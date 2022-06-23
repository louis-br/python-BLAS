from queue import Queue
import matplotlib.pyplot as plt
import numpy as np
import datetime
import json
import time
import os
import io

def timestamp_to_iso(timestamp: float):
    return datetime.datetime.fromtimestamp(timestamp).isoformat()

def get_img_size(img):
    return int(np.sqrt(len(img)))

def create_image(path, img, size):
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

        size = get_img_size(image)

        file = io.BytesIO()
        create_image(file, image, size)
        file = file.getvalue()

        if 'startTime' in job and 'endTime' in job:
            job['startDate'] = timestamp_to_iso(job['startTime'])
            job['endDate'] = timestamp_to_iso(job['endTime'])

        job['imageSize'] = f'{size}x{size}px'

        write_file(f"{imagesPath}{job['user']}/{job['id']}.png", file)
        write_file(f"{dataPath}{job['user']}/{job['id']}.json", json.dumps(job), 'w')
        
        if nextQueue is not None:
            nextQueue.put(job)

        elapsed = time.perf_counter() - elapsed
        print(f'Archiver {index} completed execution in {elapsed} seconds')
        archiveQueue.task_done()
