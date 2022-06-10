import asyncio
import websockets
import base64
import json
import csv
import math
import os

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

def new_task(user, algorithm, file, N, S, maxIterations, minError):
    g = read_csv(file)
    print(f'len: {len(g)}')
    gain(g, N, S)
    return {
        'user': user,
        'algorithm': algorithm,
        'arrayG': g,
        'maxIterations': maxIterations,
        'minError': minError
    }

async def main():
    async with websockets.connect("ws://localhost:8000") as websocket:
        with open("input.json", encoding='utf8') as f:
            input = json.load(f)
            for task in input:
                message = new_task(task['user'], task['algorithm'], task['file'], task['N'], task['S'], task['maxIterations'], task['minError'])
                message = json.dumps(message)
                await websocket.send(message)
            for task in input:
                message = await websocket.recv()
                message = json.loads(message)
                write_file(f'./images/{message["id"]}.png', base64.b64decode(message['image']))

asyncio.run(main())