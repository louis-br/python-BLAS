from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
import requests
import signal
import json
import math
import csv
import os

INPUT_FILE = os.getenv("INPUT", "input.json")
USER = os.getenv("USER", "user")
IMAGES_PATH = os.getenv("IMAGES_PATH", "./images")

def read_csv(filename):
    with open(filename, newline='') as f_input:
        return [float(row[0]) for row in csv.reader(f_input)]

def gain(g, N, S):
    for c in range(N):
        for l in range(S):
            y = 100 + (1/20) * l * math.sqrt(l)
            g[l + c*S] = g[l + c*S] * y

def generate_name(task):
    return f"{Path(task['file']).stem}_{task['algorithm']}_err{task['minError']:.0E}_max{task['maxIterations']}{'_g' if 'gain' in task else ''}"

def new_task(task):
    name = task['name'] if 'name' in task else generate_name(task)
    g = read_csv(task['file'])
    if 'gain' in task and task['gain']:
        gain(g, task['N'], task['S'])
    message = {
        'name': name,
        'user': task['user'],
        'algorithm': task['algorithm'],
        'arrayG': g,
        'maxIterations': task['maxIterations'],
        'minError': task['minError']
    }
    message = json.dumps(message)
    print(requests.post("http://localhost:8000/tasks", data=message).content, task)

def download_file(url, path):
    response = requests.get(url).content
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(response)

def main():
    url = "http://localhost:8000/"
    with ThreadPoolExecutor() as executor:
        with open(INPUT_FILE, encoding='utf8') as f:
            tasks = json.load(f)
            for task in tasks:
                executor.submit(new_task, task)
    print("Done")

    with ThreadPoolExecutor(max_workers=1) as executor:
        inputFuture = None
        while True:
            tasks = requests.get(f"{url}tasks/{USER}")
            tasks = tasks.json()
            if not 'data' in tasks:
                continue
            tasks = tasks['data']
            print('\n' * 20, "\x1bc")
            print("c: Clear local images folder")
            for i in range(len(tasks)):
                task = tasks[i]
                print(f"{i}:", task['name'] if 'name' in task else task)
            print("Select image: ")
            if inputFuture is None or inputFuture.done():
                inputFuture = executor.submit(input)
            try:
                key = inputFuture.result(timeout=1)
                if key == "c":
                    import shutil
                    shutil.rmtree(IMAGES_PATH, ignore_errors=True)
                    print('\n' * 20, "\x1bc")
                    print("Cleared")
                    input()
                    continue
                try:
                    index = int(key)
                    print(index)
                except ValueError:
                    input()
                    pass
                if index < 0 or index >= len(tasks):
                    continue
                task = tasks[index]
                id = task['id']
                print('\n' * 20, "\x1bc")
                print(task)
                print()
                filename = task['name'] if 'name' in task else id
                print(f"Downloading image: {filename}.png")
                download_file(f"{url}tasks/{USER}/{id}.png", os.path.join(IMAGES_PATH, f"{filename}.png"))
                download_file(f"{url}tasks/{USER}/{id}.json", os.path.join(IMAGES_PATH, f"{filename}.json"))
                print(f"Downloaded image: {filename}.png")
                input()
            except TimeoutError:
                pass

signal.signal(signal.SIGINT, lambda signum, frame: os._exit(0))
main()