from multiprocessing import Queue

def scheduler(pendingQueue: Queue, workerQueue: Queue):
    while True:
        next = pendingQueue.get()
        alg = next['algorithm']
        print(f'scheduling: {alg}')
        workerQueue.put(next)