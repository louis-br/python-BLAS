from threading import Lock
from time import sleep
from queue import Queue
import hashlib
import asyncio
import websockets
import base64
import json
import csv
import math
import os

IMAGES = {}
IMAGES_LOCK = Lock()

SEND_QUEUE = Queue()

def write_file(path, bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(bytes)

def read_csv(filename):
    with open(filename, newline='') as f_input:
        return [float(row[0]) for row in csv.reader(f_input)]

def gain(g, N, S):
    for c in range(N):
        for l in range(S):
            y = 100 + (1/20) * l * math.sqrt(l)
            g[l + c*S] = g[l + c*S] * y

def get_id(message: dict):
    hash = hashlib.sha1()
    hash.update(json.dumps(message['arrayG']).encode('ascii'))
    hash.update(json.dumps(message['algorithm']).encode('ascii'))
    hash.update(json.dumps(message['maxIterations']).encode('ascii'))
    hash.update(json.dumps(message['minError']).encode('ascii'))
    return hash.hexdigest()

def new_task(user, algorithm, file, N, S, maxIterations, minError):
    g = read_csv(file)
    print(f'len: {len(g)}')
    gain(g, N, S)
    message = {
        'user': user,
        'algorithm': algorithm,
        'arrayG': g,
        'maxIterations': maxIterations,
        'minError': minError,
        'status': "sending"
    }
    id = get_id(message)
    message['id'] = id
    with IMAGES_LOCK:
        IMAGES[id] = message
    return SEND_QUEUE.put(message)

def new_download(id):
    return SEND_QUEUE.put({
        'id': id,
        'user': "user", #TODO
        'download': True
    })

def view():
    with IMAGES_LOCK:
        imageList = list(IMAGES.items())
        print('\n' * 20) #('\x1bc') #Clear screen
        for i in range(len(imageList)):
            value = imageList[i][1]
            print(
                i, '\t',
                value['user'], '\t',
                value['algorithm'], '\t',
                value['maxIterations'], '\t',
                value['minError'], '\t',
                (value['status'] if 'status' in value else "")
            )
        print("Image index: ")

def menu():
    while True:
        view()
        index = input()
        index = int(index)
        if index is not None:
            with IMAGES_LOCK:
                image = list(IMAGES.values())[index]
                new_download(image['id'])

async def async_wait(f, *args, **kwargs):
    return await asyncio.get_event_loop().run_in_executor(None, lambda: f(*args, **kwargs))

async def sender(websocket):
    while True:
        message = await async_wait(SEND_QUEUE.get)
        message = json.dumps(message)
        await websocket.send(message)

async def receiver(websocket):
    while True:
        message = await websocket.recv()
        if isinstance(message, bytes):
            write_file(f'./images/download.png', bytes)

        message = json.loads(message)
        if 'id' in message:
            with IMAGES_LOCK:
                IMAGES[message['id']] = message
            view()

async def main():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, menu)
    async with websockets.connect("ws://localhost:8000") as websocket:
        with open("input.json", encoding='utf8') as f:
            input = json.load(f)
            user = "user"
            for task in input:
                user = task['user']
                new_task(task['user'], task['algorithm'], task['file'], task['N'], task['S'], task['maxIterations'], task['minError'])
            await websocket.send(user)
            loop.run_in_executor(None, menu)
            loop.create_task(sender(websocket))
            await receiver(websocket)
                #write_file(f'./images/{message["id"]}.png', base64.b64decode(message['image']))

asyncio.run(main())