from asyncore import write
from multiprocessing import Queue
import matplotlib.pyplot as plt
import numpy as np
import base64
import json
import time
import os
import io

def create_image(path, img):
    size = int(np.sqrt(len(img)))
    img = np.reshape(img, (size, size)).transpose()
    return plt.imsave(path, img, cmap="gray")

def write_file(path, data, mode='wb'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode) as f:
        f.write(data)

def archiver(archiveQueue: Queue, nextQueue: Queue, imagesPath="./results/images/", dataPath="./results/metadata/", index=0): #f'{id}.png'
    while True:
        job = archiveQueue.get()

        elapsed = time.perf_counter()

        image = job.pop('arrayF', None)

        file = io.BytesIO()
        create_image(file, image)
        file = file.getvalue()

        copy = job.copy()

        job['image'] = base64.b64encode(file).decode('ascii')

        nextQueue.put(job)

        write_file(f'{imagesPath}{copy["id"]}.png', file)
        write_file(f'{dataPath}{copy["id"]}.json', json.dumps(copy), 'w')
        
        elapsed = time.perf_counter() - elapsed
        print(f'Archiver {index} completed execution in {elapsed} seconds')
