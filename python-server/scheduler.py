from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from threading import Timer
from signal import SIGINT
from queue import Queue
import queue
import subprocess
import socket

from config.models import MODELS
from monitor import monitor

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

def process_finished_tasks(workerDoneQueue: Queue, busy: dict[int, int]):
    try:
        while workerDoneQueue.qsize() > 0:
            task = workerDoneQueue.get_nowait()
            size = task['size']
            if size not in busy:
                continue
            busy[size] -= 1
            if busy[size] <= 0:
                del busy[size]
    except queue.Empty:
        pass

def fill_task_list(taskList: list, workers: int, queues: dict) -> bool:
    taskList.reverse()
    times = {key: queue['time'] for key, queue in queues.items()}
    while len(taskList) < workers and len(times) > 0:
        key = min(times, key=times.get)
        queueDict = queues[key] if key in queues else None
        q: Queue = queueDict['queue'] if queueDict else None
        if not q or q.qsize() == 0 or not queueDict['enabled']:
            times.pop(key, None)
            continue
        try:
            task = q.get_nowait()
            q.task_done()
            if task == "STOP":
                return False
            time = task['queueTime']
            times[key] = time
            queueDict['time'] = time
            taskList.append(task)
        except queue.Empty:
            times.pop(key, None)
    taskList.reverse()
    return True

def wait_for_tasks(timeout: float, taskQueue: Queue, queues: list[dict]):
    executor = ThreadPoolExecutor(max_workers=sum([len(q) for q in queues]))
    futures = []
    for dict in queues:
        for queue in dict.values():
            if queue == taskQueue or not queue['enabled']:
                continue
            futures.append(executor.submit(lambda queue, done, t: done.put(queue.get(timeout=t)), queue['queue'], taskQueue, timeout))
    wait(futures, timeout=timeout, return_when=FIRST_COMPLETED)
    executor.shutdown(wait=False, cancel_futures=True)

def increment_dict(dict: dict, key, increment: int):
    if increment == 0:
        return
    dict[key] = dict[key] + increment if key in dict else increment

def set_queues_enabled(queuesDict: list[dict], key: int, enabled: bool):
    for queueDict in queuesDict:
        if key in queueDict:
            queueDict[key]['enabled'] = enabled

def scheduler(maxWorkers: int, pendingQueues: dict, workerQueue: Queue, workerDoneQueue: Queue, blasExecutable: str="../blas/out/blas"):
    workers = maxWorkers
    pendingQueues = {
        key: {'time': 0, 'enabled': True, 'queue': value} for key, value in pendingQueues.items()
    }
    retryQueues = {
        key: {'time': 0, 'enabled': True, 'queue': Queue()} for key in pendingQueues
    }
    processes = {}
    busy = {}
    taskList = []
    while True:
        upcoming = {}
        wait_for_tasks(1.0, pendingQueues['retry']['queue'], [retryQueues, pendingQueues])

        process_finished_tasks(workerDoneQueue, busy)
        
        if not fill_task_list(taskList, workers, queues=retryQueues): 
            return
        if not fill_task_list(taskList, workers, queues=pendingQueues): 
            return

        pending = 0
        for queue in [retryQueues, pendingQueues]:
            for size, value in queue.items():
                if size in MODELS:
                    qsize = value['queue'].qsize()
                    increment_dict(upcoming, size, qsize)
                    pending += qsize
        for task in taskList:
            size = task['size']
            increment_dict(upcoming, size, 1)
            pending += 1

        limits = monitor(busy, upcoming)
        workers = max(0, min(sum(busy.values()) - limits['cpu'], maxWorkers))
        for size, value in limits['memory'].items():
            if value > 0:
                upcoming.pop(size, None)
                set_queues_enabled([pendingQueues, retryQueues], size, False)

        print(f'Scheduler tasks: {len(taskList)}, workers: {workers}, busy: {busy}, pending:{pending}, limits: {limits}')

        for size in upcoming:
            set_queues_enabled([pendingQueues, retryQueues], size, True)

        for size, process in processes.items():
            if process['process'].poll() is not None:
                processes.pop(size, None)

        for i in range(min(workers, len(taskList))):
            task = taskList.pop()
            size = task['size']
            if size not in upcoming:
                if size in retryQueues:
                    retryQueues[size]['queue'].put(task)
                continue
            if size not in processes:
                model = MODELS[size]
                create_process(processes, size, blasExecutable, get_free_port(), model['path'], model['rows'], model['columns'])
            task['port'] = processes[size]['port']
            increment_dict(busy, size, 1)
            workerQueue.put(task)

        for size in list(processes.keys()):
            if size not in busy:
                stop_process(processes, size)