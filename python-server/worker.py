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
        f = protocol.read_message(sock)['arrayF']
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

def worker(workerQueue: Queue, nextQueue: Queue, retryQueue: Queue=None, index=0):
    while True:
        job = workerQueue.get()

        if job == "STOP":
            workerQueue.task_done()
            return
        
        elapsed = time.perf_counter()

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
        
        elapsed = time.perf_counter() - elapsed
        print(f"Worker {index} completed execution in {elapsed} seconds")

        nextQueue.put(job)
        workerQueue.task_done()