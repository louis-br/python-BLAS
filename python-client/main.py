from concurrent.futures import ThreadPoolExecutor, TimeoutError
import requests
import signal
import json
import math
import csv
import os

def read_csv(filename):
    with open(filename, newline='') as f_input:
        return [float(row[0]) for row in csv.reader(f_input)]

def gain(g, N, S):
    for c in range(N):
        for l in range(S):
            y = 100 + (1/20) * l * math.sqrt(l)
            g[l + c*S] = g[l + c*S] * y

def new_task(task):
    g = read_csv(task['file'])
    if 'gain' in task and task['gain']:
        gain(g, task['N'], task['S'])
    message = {
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
        with open("input.json", encoding='utf8') as f:
            tasks = json.load(f)
            for task in tasks:
                executor.submit(new_task, task)
    print("Done")

    with ThreadPoolExecutor(max_workers=1) as executor:
        inputFuture = None
        while True:
            tasks = requests.get(f"{url}tasks/user")
            tasks = tasks.json()
            if not 'data' in tasks:
                continue
            tasks = tasks['data']
            print('\n' * 20, "\x1bc")
            for i in range(len(tasks)):
                print(f"{i}:", tasks[i])
            print("Select image: ")
            if inputFuture is None or inputFuture.done():
                inputFuture = executor.submit(input)
            try:
                index = int(inputFuture.result(timeout=1))
                id = tasks[index]['id']
                print('\n' * 20, "\x1bc")
                print(f"Downloading image: {id}.png")
                download_file(f"{url}tasks/user/{id}.png", f"images/{id}.png")
                download_file(f"{url}tasks/user/{id}.json", f"images/{id}.json")
                print(f"Downloaded image: {id}.png")
                input()
            except TimeoutError:
                pass

signal.signal(signal.SIGINT, lambda signum, frame: os._exit(0))
main()