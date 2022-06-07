from multiprocessing import Queue
import matplotlib.pyplot as plt
import numpy as np
import base64
import os
import io

def create_image(path, img):
    size = int(np.sqrt(len(img)))
    img = np.reshape(img, (size, size)).transpose()
    return plt.imsave(path, img, cmap="gray")

def write_file(path, bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(bytes)

def archiver(archiveQueue: Queue, nextQueue: Queue, i, path="./images/"): #f'{id}.png'
    while True:
        job = archiveQueue.get()

        image = job.pop('arrayF', None)
        file = io.BytesIO()
        create_image(file, image)
        file = file.getvalue()
        job['image'] = base64.b64encode(file).decode('ascii')

        nextQueue.put(job)

        write_file(f'{path}{0}.png', file)
        
        print(f'Archiver {i} completed execution')
