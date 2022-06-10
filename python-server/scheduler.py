from queue import Queue
import queue
import subprocess
import socket

MODELS = {
    50816: {'path': '../utils/data/H-1.float', 'rows': 50816, 'columns': 3600},
    27904: {'path': '../utils/data/H-2.float', 'rows': 27904, 'columns': 900},
}

def get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def create_blas_process(executable, port, path, rows, columns):
    return subprocess.Popen([
        executable,
        '--port', str(port),
        '--file', str(path),
        '--rows', str(rows),
        '--columns', str(columns)
        ])

def scheduler(pendingQueue: Queue, nextQueue: Queue, retryQueue=None, blasExecutable="../blas/out/blas"):
    blasProcesses = {}
    while True:
        next = None
        currentQueue = None
        if retryQueue is not None and not retryQueue.empty():
            try:
                next = retryQueue.get_nowait()
                currentQueue = retryQueue
            except queue.Empty:
                pass
        if next is None:
            try:
                next = pendingQueue.get(timeout=1)
                currentQueue = pendingQueue
            except queue.Empty:
                continue

        if next == "STOP":
            nextQueue.put(next)
            currentQueue.task_done()
            return

        size = len(next['arrayG'])

        if size not in blasProcesses:
            if size in MODELS:
                model = MODELS[size]
            else:
                print(f'No model available for size: {size}')
                currentQueue.task_done()
                continue

            port = get_free_port()
            blasProcesses[size] = {
                'process': create_blas_process(blasExecutable, port, model['path'], model['rows'], model['columns']),
                'port': port
            }
                    
        process = blasProcesses[size]
        next['port'] = process['port']

        print(f"Scheduling: {next['algorithm']}")
        
        nextQueue.put(next)
        currentQueue.task_done()