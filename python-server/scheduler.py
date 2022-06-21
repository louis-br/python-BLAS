from queue import Queue
from config.models import MODELS
from monitor import monitor
from signal import SIGINT
from threading import Timer
import queue
import subprocess
import socket

def get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def create_process(processes: dict[int, dict], size: int, executable: str, port: int, path: str, rows: int, columns: int):
    processes[size] = {
        'process': subprocess.Popen([
            executable,
            '--port', str(port),
            '--file', str(path),
            '--rows', str(rows),
            '--columns', str(columns)
        ]),
        'port': port
    }

def stop_process(processes: dict, size: int):
    process = processes.pop(size, None)
    if process is None:
        return
    process: subprocess.Popen = process['process']
    process.send_signal(SIGINT)
    Timer(10.0, process.kill).start()

def process_finished_tasks(workerDoneQueue: Queue, doneQueue: Queue, busyModels: dict[int, int], latency: list=[]):
    try:
        for task in iter(workerDoneQueue.get_nowait, None):
            if task is None:
                break
            size = task['size']
            if size not in busyModels:
                continue
            busyModels[size] -= 1
            if busyModels[size] <= 0:
                del busyModels[size]
            doneQueue.put(task)
    except queue.Empty:
        pass

def fill_task_list(taskList: list, workers: int, queues: list[Queue]=[], timeout: float=1.0) -> bool: #, processes: dict={}
    taskList.reverse()
    queuesSize = len(queues)
    for i in range(queuesSize):
        q = queues[i]
        while len(taskList) < workers:
            try:
                task = q.get(timeout=1) if i == queuesSize - 1 else q.get_nowait()
                q.task_done()
                if task is None:
                    continue
                if task == "STOP":
                    return False
                size = task['size']
                if size not in MODELS:
                    print(f'No model available for size: {size}')
                    continue
                taskList.append(task)
            except queue.Empty:
                break
    taskList.reverse()
    return True

def scheduler(maxWorkers: int, pendingQueue: Queue, workerQueue: Queue, doneQueue: Queue, retryQueue: Queue, workerDoneQueue: Queue, blasExecutable: str="../blas/out/blas"):
    processes = {}
    busyModels = {}
    taskList = []
    workers = maxWorkers
    while True:
        upcoming = {}
        process_finished_tasks(workerDoneQueue, doneQueue, busyModels)
        
        if not fill_task_list(taskList, workers, queues=[retryQueue, pendingQueue], timeout=1.0):
            return

        for task in taskList:
            size = task['size']
            if size not in processes:
                upcoming[size] = 0
            if size in upcoming:
                upcoming[size] += 1

        limits = monitor(busyModels.keys(), upcoming.keys())
        workers = min(sum(busyModels.values()) - limits['cpu'], maxWorkers)
        print(f"workers: {workers}")
        for size, value in limits['memory'].items():
            if value > 0:
                upcoming.pop(size, None)

        #if len(taskList) > 0:
        print(f'Scheduler workers: {workers}, limits: {limits}, busy: {busyModels}')

        for size in upcoming:
            if size not in processes:
                model = MODELS[size]
                create_process(processes, size, blasExecutable, get_free_port(), model['path'], model['rows'], model['columns'])

        for i in range(min(workers, len(taskList))):
            task = taskList.pop()
            size = task['size']
            if size not in upcoming:
                retryQueue.put(task)
                continue
            if size not in processes:
                continue
            task['port'] = processes[size]['port']
            busyModels[size] = busyModels[size] + 1 if size in busyModels else 1
            workerQueue.put(task)

        for size in list(processes.keys()):
            if size not in busyModels:
                stop_process(processes, size)