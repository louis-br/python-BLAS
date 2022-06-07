from multiprocessing import Queue, Process
import asyncio
import websockets
import signal
import json

from scheduler import scheduler
from worker import worker
from archiver import archiver

PENDING_QUEUE = Queue()
WORKER_QUEUE = Queue()
ARCHIVE_QUEUE = Queue()
DONE_QUEUE = Queue()

async def async_wait(f, *args):
    return await asyncio.get_event_loop().run_in_executor(None, f, *args)

async def new_task(queue: Queue, dict: dict) -> dict:
    return await async_wait(queue.put, {
        'user': dict['user'],
        'algorithm': dict['algorithm'],
        'arrayG': dict['arrayG'],
        'maxIterations': dict['maxIterations'],
        'minError': dict['minError']
    })

async def process(websocket, message, pending: Queue, done: Queue):
        message = json.loads(message)
        await new_task(PENDING_QUEUE, message)

        output = await async_wait(DONE_QUEUE.get)
        message = json.dumps(output)
        await websocket.send(message)

#https://docs.python.org/3/library/asyncio-task.html#running-in-threads
async def listen(websocket, path):
    async for message in websocket:
        asyncio.get_event_loop().create_task(process(websocket, message, PENDING_QUEUE, DONE_QUEUE))

async def main():
    schedulerProcess =  Process(target=scheduler, args=(PENDING_QUEUE, WORKER_QUEUE))
    schedulerProcess.start()

    workers = []
    archivers = []

    for i in range(3):
        workerProcess = Process(target=worker, args=(WORKER_QUEUE,  ARCHIVE_QUEUE, i))
        archiverProcess = Process(target=archiver, args=(ARCHIVE_QUEUE,  DONE_QUEUE, i))
        workerProcess.start()
        archiverProcess.start()
        workers.append(workerProcess)
        archivers.append(archiverProcess)

    # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    #loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    #loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    async with websockets.serve(listen, "127.0.0.1", 8000):
        await stop

    schedulerProcess.join()
    for workerProcess in workers:
        workerProcess.join()
    for archiverProcess in archivers:
        archiverProcess.join()

if __name__ == '__main__':
    asyncio.run(main())