from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, constr
from enum import Enum

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import hashlib
import time
import json
import os

from scheduler import scheduler
from worker import worker
from archiver import archiver

from config.models import MODELS

SCHEDULER_QUEUES = {model: Queue() for model in MODELS}
SCHEDULER_QUEUES['stop'] = Queue()
SCHEDULER_QUEUES['retry'] = Queue()

#PENDING_QUEUE = Queue()
WORKER_QUEUE = Queue()
WORKER_RETRY_QUEUE = SCHEDULER_QUEUES['retry']
WORKER_DONE_QUEUE = Queue()
ARCHIVER_QUEUE = Queue()
#DONE_QUEUE = Queue()

NUM_WORKERS = os.getenv("WORKERS", None)
if NUM_WORKERS is None:
    NUM_WORKERS = 10
    print(f"\033[93m\nWORKERS environment variable not set, defaulting to: {NUM_WORKERS}\nPlease run with: WORKERS=10 uvicorn main:app\n\033[0m")
else:
    NUM_WORKERS = int(NUM_WORKERS)

WORKERS = {}
THREAD_POOL = ThreadPoolExecutor(max_workers=NUM_WORKERS + 2)

RESULTS_PATH = "./results/"
METADATA_PATH = os.path.join(RESULTS_PATH, "metadata/")
IMAGES_PATH = os.path.join(RESULTS_PATH, "images/")

for path in [RESULTS_PATH, METADATA_PATH, IMAGES_PATH]:
    os.makedirs(path, exist_ok=True)

app = FastAPI()

@app.on_event("startup")
def start_workers():
    schedulers = [THREAD_POOL.submit(scheduler, NUM_WORKERS, SCHEDULER_QUEUES, workerQueue=WORKER_QUEUE, workerDoneQueue=WORKER_DONE_QUEUE)]
    workers = []
    archivers = []

    for i in range(NUM_WORKERS):
        workers.append(THREAD_POOL.submit(worker, WORKER_QUEUE, nextQueues=[ARCHIVER_QUEUE, WORKER_DONE_QUEUE], retryQueue=WORKER_RETRY_QUEUE, index=i))
    archivers.append(THREAD_POOL.submit(archiver, ARCHIVER_QUEUE, nextQueue=None, imagesPath=IMAGES_PATH, dataPath=METADATA_PATH))

    WORKERS['schedulers'] = schedulers
    WORKERS['workers'] = workers
    WORKERS['archivers'] = archivers

def stop_tasks(name: str, list: list, queue: Queue):
    for i in range(len(list)):
        queue.put("STOP")
    for i in range(len(list)):
        print(f"Waiting for {name}: {i+1}/{len(list)}")
        list[i].result()

@app.on_event("shutdown")
def stop_workers():
    stop_tasks("scheduler", WORKERS['schedulers'],  SCHEDULER_QUEUES['stop'] )
    stop_tasks("worker",    WORKERS['workers'],     WORKER_QUEUE  )
    stop_tasks("archiver",  WORKERS['archivers'],   ARCHIVER_QUEUE)

    print("Pool shutdown")
    THREAD_POOL.shutdown()

    if os.getenv("CLEAR", None) == "1":
        import shutil
        shutil.rmtree(IMAGES_PATH, ignore_errors=True)
        shutil.rmtree(METADATA_PATH, ignore_errors=True)

class AlgorithmEnum(str, Enum):
    CGNE = "CGNE"
    CGNR = "CGNR"

class Task(BaseModel):
    user: constr(to_lower=True, strip_whitespace=True)
    algorithm: AlgorithmEnum
    arrayG: list[float]
    maxIterations: int
    minError: float

def get_id(task: Task) -> str:
    hash = hashlib.sha1()
    for item in [task.arrayG, task.algorithm, task.maxIterations, task.minError]:
        hash.update(json.dumps(item).encode('ascii'))
    return hash.hexdigest()

def new_task(task: Task, size):
    id = get_id(task)
    if size not in SCHEDULER_QUEUES:
        print("Attempt to add a new task but size is no longer available. ")
        return
    SCHEDULER_QUEUES[size].put({
        'id': id,
        'user': task.user,
        'algorithm': task.algorithm,
        'arrayG': task.arrayG,
        'queueTime': time.time(),
        'size': size,
        'maxIterations': task.maxIterations,
        'minError': task.minError
    })

@app.post("/tasks")
async def post_task(task: Task, background_tasks: BackgroundTasks):
    size = len(task.arrayG)
    if size not in SCHEDULER_QUEUES:
        return {"status": "error", "message": f"No model available for size: {size}"}
    background_tasks.add_task(new_task, task, size)
    return {"status": "success"}

@app.get("/tasks/{user}")
def list_tasks(user: constr(to_lower=True, strip_whitespace=True)):
    tasks = []
    userPath = os.path.join(METADATA_PATH, user)
    if os.path.exists(userPath):  
        for filename in os.listdir(userPath):
            filePath = os.path.join(userPath, filename)
            if not os.path.isfile(filePath):
                continue
            with open(filePath, 'r') as f:
                try:
                    task = json.load(f)
                    if 'id' not in task:
                        continue
                    tasks.append(task)
                except json.decoder.JSONDecodeError:
                    pass
    return {"status": "success", "data": tasks}

@app.get("/tasks/{user}/{id}.png")
async def get_png_image(user: str, id: str):
    return RedirectResponse(f"/tasks/images/{user}/{id}.png")

@app.get("/tasks/{user}/{id}.json")
async def get_json_metadata(user: str, id: str):
    return RedirectResponse(f"/tasks/metadata/{user}/{id}.json")

app.mount("/tasks", StaticFiles(directory=RESULTS_PATH), name="tasks-static")

@app.get("/")
async def root():
    return RedirectResponse("/docs")

if __name__ == '__main__':
    print("Please run with: WORKERS=10 uvicorn main:app")