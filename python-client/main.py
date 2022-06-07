import asyncio
import websockets
import base64
import json
import csv
import math
import os
#import matplotlib.pyplot as plt

#def view(img):
#    #size = int(math.sqrt(img.size))
#    i = np.reshape(img, (60, 60)).transpose()
#    return plt.imsave('test.png', i, cmap="gray")

def write_file(path, bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(bytes)

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

async def main():
    async with websockets.connect("ws://localhost:8000") as websocket:
        for i in range(3):
            message = new_task("User", "CGNR", "../data/G-1.csv", 794, 64, 500, 1e-4)
            message = json.dumps(message)
            await websocket.send(message)
        for i in range(3):
            message = await websocket.recv()
        message = json.loads(message)
        write_file(f'./images/{0}.png', base64.b64decode(message['image']))

asyncio.run(main())