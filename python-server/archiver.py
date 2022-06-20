from queue import Queue
import matplotlib.pyplot as plt
import numpy as np
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

def archiver(archiveQueue: Queue, nextQueue: Queue=None, imagesPath="./results/images/", dataPath="./results/metadata/", index=0):
    while True:
        job = archiveQueue.get()

        if job == "STOP":
            archiveQueue.task_done()
            return

        elapsed = time.perf_counter()

        image = job.pop('arrayF', None)

        file = io.BytesIO()
        create_image(file, image)
        file = file.getvalue()

        #job['image'] = base64.b64encode(file).decode('ascii')

        write_file(f"{imagesPath}{job['user']}/{job['id']}.png", file)
        write_file(f"{dataPath}{job['user']}/{job['id']}.json", json.dumps(job), 'w')
        
        if nextQueue is not None:
            nextQueue.put(job)

        elapsed = time.perf_counter() - elapsed
        print(f'Archiver {index} completed execution in {elapsed} seconds')
        archiveQueue.task_done()
