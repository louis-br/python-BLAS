from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from fastapi import BackgroundTasks, HTTPException, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, constr
from enum import Enum
import hashlib
import json
import os

from scheduler import scheduler
from worker import worker
from archiver import archiver

PENDING_QUEUE = Queue()
WORKER_QUEUE = Queue()
WORKER_RETRY_QUEUE = Queue()
ARCHIVER_QUEUE = Queue()
DONE_QUEUE = Queue()

NUM_WORKERS = os.getenv("WORKERS", None)
if NUM_WORKERS is None:
    NUM_WORKERS = 10
    print(f"\033[93m\nWORKERS environment variable not set, defaulting to: {NUM_WORKERS}\nPlease run with: WORKERS=10 uvicorn main:app\n\033[0m")
else:
    NUM_WORKERS = int(NUM_WORKERS)

WORKERS = {}
THREAD_POOL = ThreadPoolExecutor(max_workers=NUM_WORKERS)

RESULTS_PATH = "./results/"
METADATA_PATH = os.path.join(RESULTS_PATH, "metadata/")
IMAGES_PATH = os.path.join(RESULTS_PATH, "images/")

app = FastAPI()

@app.on_event("startup")
def startWorkers():
    schedulers = [
        THREAD_POOL.submit(scheduler, PENDING_QUEUE, WORKER_QUEUE, retryQueue=WORKER_RETRY_QUEUE)
    ]

    workers = []
    archivers = []
    for i in range(NUM_WORKERS):
        workers.append(THREAD_POOL.submit(worker, WORKER_QUEUE, ARCHIVER_QUEUE, retryQueue=WORKER_RETRY_QUEUE, index=i))
        archivers.append(THREAD_POOL.submit(archiver, ARCHIVER_QUEUE, DONE_QUEUE, imagesPath=IMAGES_PATH, dataPath=METADATA_PATH))

    WORKERS['schedulers'] = schedulers
    WORKERS['workers'] = workers
    WORKERS['archivers'] = archivers

@app.on_event("shutdown")
def stopWorkers():
    PENDING_QUEUE.put("STOP")
    for worker in range(NUM_WORKERS):
        WORKER_QUEUE.put("STOP")
    for taskList in (("scheduler", WORKERS['schedulers']), ("worker", WORKERS['workers']), ("archiver", WORKERS['archivers'])):
        for i in range(len(taskList[1])):
            print(f"Waiting for {taskList[0]} {i}")
            taskList[1][i].result()
    print("Pool shutdown")
    THREAD_POOL.shutdown()

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

def new_task(task: Task):
    id = get_id(task)
    PENDING_QUEUE.put({
        'id': id,
        'user': task.user,
        'algorithm': task.algorithm,
        'arrayG': task.arrayG,
        'maxIterations': task.maxIterations,
        'minError': task.minError
    })

@app.post("/tasks")
async def post_task(task: Task, background_tasks: BackgroundTasks):
    background_tasks.add_task(new_task, task)
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
                task = json.load(f)
                if not 'id' in task:
                    continue
                tasks.append(task)
    return {"status": "success", "data": tasks}

@app.get("/tasks/{user}/{id}.png")
async def get_png_image(user: str, id: str):
    print("user", user, "id", id)
    return RedirectResponse(f"/tasks/images/{user}/{id}.png")

@app.get("/tasks/{user}/{id}.json")
async def get_json_metadata(user: str, id: str):
    print("user", user, "id", id)
    return RedirectResponse(f"/tasks/metadata/{user}/{id}.json")

app.mount("/tasks", StaticFiles(directory=RESULTS_PATH), name="tasks-static")

@app.get("/")
async def root():
    return RedirectResponse("/docs")

if __name__ == '__main__':
    print("Please run with: WORKERS=10 uvicorn main:app")