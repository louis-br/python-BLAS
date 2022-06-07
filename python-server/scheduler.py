from multiprocessing import Queue

def scheduler(pendingQueue: Queue, nextQueue: Queue):
    while True:
        next = pendingQueue.get()

        alg = next['algorithm']
        print(f'Scheduling: {alg}')
        
        nextQueue.put(next)