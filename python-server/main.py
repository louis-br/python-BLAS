from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import asyncio
import websockets
import signal
import json
import re
import hashlib

from utils.async_wait import async_wait
from utils.sigint import sigint_decorator
from scheduler import scheduler
from worker import worker
from archiver import archiver

#scheduler = sigint_decorator(scheduler)
#worker = sigint_decorator(worker)
#archiver = sigint_decorator(archiver)

PENDING_QUEUE = Queue()
WORKER_QUEUE = Queue()
WORKER_RETRY_QUEUE = Queue()
ARCHIVER_QUEUE = Queue()
DONE_QUEUE = Queue()

def get_id(message: dict):
    hash = hashlib.sha1()
    hash.update(json.dumps(message['arrayG']).encode('ascii'))
    hash.update(json.dumps(message['algorithm']).encode('ascii'))
    hash.update(json.dumps(message['maxIterations']).encode('ascii'))
    hash.update(json.dumps(message['minError']).encode('ascii'))
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
        message = json.loads(message)
        id = get_id(message)
        await new_task(pending, message, id)

        output = await async_wait(done.get)
        message = json.dumps(output)
        await websocket.send(message)

async def listen(websocket, path):
    async for message in websocket:
        asyncio.get_event_loop().create_task(process(websocket, message, PENDING_QUEUE, DONE_QUEUE))

async def main():
    poolExecutor = ThreadPoolExecutor(max_workers=7)

    schedulers = [
        poolExecutor.submit(scheduler, PENDING_QUEUE, WORKER_QUEUE, retryQueue=WORKER_RETRY_QUEUE)
    ]
    workers = []
    archivers = []

    for i in range(3):
        workers.append(poolExecutor.submit(worker, WORKER_QUEUE, ARCHIVER_QUEUE, retryQueue=WORKER_RETRY_QUEUE, index=i))
        archivers.append(poolExecutor.submit(archiver, ARCHIVER_QUEUE, DONE_QUEUE, index=i))

    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    async with websockets.serve(listen, "127.0.0.1", 8000):
        print("Websockets listening: 127.0.0.1:8000")
        await stop

    print("Shutdown")
    PENDING_QUEUE.put("STOP")
    for work in workers:
        WORKER_QUEUE.put("STOP")
    for taskList in (("scheduler", schedulers), ("worker", workers), ("archiver", archivers)):
        for i in range(len(taskList[1])):
            print(f"Waiting for {taskList[0]} {i}")
            taskList[1][i].result()
    print("Pool shutdown")
    poolExecutor.shutdown()


if __name__ == '__main__':
    asyncio.run(main())