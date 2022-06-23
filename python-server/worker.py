from queue import Queue
from utils import protocol
import time
import socket
import struct

def connect(msg, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect(("localhost", port))
        except socket.error as err:
            print(f'socket error: {err}')
            return None
        protocol.write_message(sock, msg)
        f = protocol.read_message(sock)
        if f is None or 'arrayF' not in f:
            return None
        f = f['arrayF']
        f = struct.unpack('=%sf' % int(len(f)//4), f)
    return f

def pack_message(msg):
    arrayG = msg['arrayG']
    return {
        'algorithmIndex': struct.pack('=i', msg['algorithm'] == "CGNR"),
        'arrayG': struct.pack('=%sf' % len(arrayG), *(arrayG)),
        'maxIterations': struct.pack('=i', msg['maxIterations']),
        'minError': struct.pack('=f', msg['minError'])
    }

def worker(workerQueue: Queue, nextQueues: list[Queue], retryQueue: Queue=None, index=0):
    while True:
        job = workerQueue.get()

        if job == "STOP":
            workerQueue.task_done()
            return
        
        job['startTime'] = time.time()

        port = job['port']
        arrayF = connect(pack_message(job), port)
        if arrayF is None:
            if retryQueue is not None:
                retryQueue.put(job)
            workerQueue.task_done()
            continue
        job['arrayF'] = arrayF
        job.pop('arrayG', None)
        job.pop('port', None)

        job['endTime'] = time.time()
        job['elapsedTime'] = job['endTime'] - job['startTime']
        
        print(f"Worker {index} completed execution in {job['elapsedTime']} seconds")

        for queue in nextQueues:
            queue.put(job)
        workerQueue.task_done()