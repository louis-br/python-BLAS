from multiprocessing import Queue, Process
import asyncio
import sched
import websockets
import signal
import json
import random
import time

from scheduler import scheduler
from worker import worker

PENDING_QUEUE = Queue()
WORKER_QUEUE = Queue()
DONE_QUEUE = Queue()

def new_task(queue: Queue, dict: dict) -> dict:
    queue.put({
        'user': dict['user'],
        'algorithm': dict['algorithm'],
        'arrayG': dict['arrayG'],
        'maxIterations': dict['maxIterations'],
        'minError': dict['minError']
    })

#https://docs.python.org/3/library/asyncio-task.html#running-in-threads
async def listen(websocket, path):
    print(f'new {PENDING_QUEUE}, {DONE_QUEUE}')
    async for message in websocket:
        message = json.loads(message)
        new_task(PENDING_QUEUE, message)
        #print(message)
        output = DONE_QUEUE.get()
        message = json.dumps(output)
        await websocket.send(message)

async def main():
    schedulerProcess =  Process(target=scheduler,   args=(PENDING_QUEUE, WORKER_QUEUE))
    workerProcess =     Process(target=worker,      args=(WORKER_QUEUE,  DONE_QUEUE  ))

    schedulerProcess.start()
    workerProcess.start()

     # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with websockets.serve(listen, "127.0.0.1", 8000):
        await stop

    schedulerProcess.join()
    workerProcess.join()

if __name__ == '__main__':
    asyncio.run(main())