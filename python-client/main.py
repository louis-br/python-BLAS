import asyncio
import websockets
import json
import csv
import math
import matplotlib.pyplot as plt
import numpy as np

def view(img):
    #size = int(math.sqrt(img.size))
    i = np.reshape(img, (60, 60)).transpose()
    return plt.imsave('test.png', i, cmap="gray")

def read_csv(filename):
    with open(filename, newline='') as f_input:
        return [float(row[0]) for row in csv.reader(f_input)] #list(map(float, row))

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

async def hello():
    async with websockets.connect("ws://localhost:8000") as websocket:
        message = new_task("User", "CGNR", "../data/G-1.csv", 794, 64, 500, 1e-4) #"Hello world"
        message = json.dumps(message)
        await websocket.send(message)
        message = await websocket.recv()
        message = json.loads(message)
        print(message)
        view(message['arrayF'])

asyncio.run(hello())