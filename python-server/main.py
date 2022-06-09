from multiprocessing import Queue, Process
import asyncio
import websockets
import signal
import json
import re
import hashlib

from utils.sigint import sigint_decorator
from scheduler import scheduler
from worker import worker
from archiver import archiver

scheduler = sigint_decorator(scheduler)
worker = sigint_decorator(worker)
archiver = sigint_decorator(archiver)

PENDING_QUEUE = Queue()
WORKER_QUEUE = Queue()
WORKER_RETRY_QUEUE = Queue()
ARCHIVE_QUEUE = Queue()
DONE_QUEUE = Queue()

async def async_wait(f, *args):
    return await asyncio.get_event_loop().run_in_executor(None, f, *args)

def get_id(message: str):
    arrayG = dict['arrayG']
    hash = hashlib.sha1(message.encode('ascii'))
    return hash.hexdigest()

async def new_task(queue: Queue, dict: dict, id: str) -> dict:
    dict['user'] = re.sub(r'[\W_]+', '', dict['user']).lower()
    dict['algorithm'] = dict['algorithm'] if dict['algorithm'].upper() == "CGNE" else "CGNR"
    dict['maxIterations'] = int(dict['maxIterations'])
    dict['minError'] = float(dict['minError'])
    return await async_wait(queue.put, {
        'id': id,
        'user': dict['user'],
        'algorithm': dict['algorithm'],
        'arrayG': dict['arrayG'],
        'maxIterations': dict['maxIterations'],
        'minError': dict['minError']
    })

async def process(websocket, message, pending: Queue, done: Queue):
        id = get_id(message)
        message = json.loads(message)
        await new_task(pending, message, id)

        output = await async_wait(done.get)
        message = json.dumps(output)
        await websocket.send(message)

async def listen(websocket, path):
    async for message in websocket:
        asyncio.get_event_loop().create_task(process(websocket, message, PENDING_QUEUE, DONE_QUEUE))

async def main():
    schedulerProcess =  Process(target=scheduler, args=(PENDING_QUEUE, WORKER_QUEUE), kwargs={'retryQueue': WORKER_RETRY_QUEUE})
    schedulerProcess.start()

    workers = []
    archivers = []

    for i in range(3):
        workerProcess =   Process(target=worker,   args=(WORKER_QUEUE, ARCHIVE_QUEUE), kwargs={'retryQueue': WORKER_RETRY_QUEUE, 'index': i})
        archiverProcess = Process(target=archiver, args=(ARCHIVE_QUEUE,  DONE_QUEUE),  kwargs={'index': i})
        workerProcess.start()
        archiverProcess.start()
        workers.append(workerProcess)
        archivers.append(archiverProcess)

    # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    #loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    async with websockets.serve(listen, "127.0.0.1", 8000):
        await stop

    schedulerProcess.join()
    for workerProcess in workers:
        workerProcess.join()
    for archiverProcess in archivers:
        archiverProcess.join()

if __name__ == '__main__':
    asyncio.run(main())