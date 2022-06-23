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
        output = protocol.read_message(sock)
        if output is None:
            return None
        if 'arrayF' in output:
            arrayF = output['arrayF']
            output['arrayF'] = struct.unpack('=%sf' % int(len(arrayF)//4), arrayF)
        if 'iterations' in output:
            output['iterations'] = struct.unpack('=i', output['iterations'])[0]
    return output

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
        output = connect(pack_message(job), port)
        if output is None or 'arrayF' not in output:
            if retryQueue is not None:
                retryQueue.put(job)
            workerQueue.task_done()
            continue
        job['arrayF'] = output['arrayF']
        job.pop('arrayG', None)
        job.pop('port', None)

        if 'iterations' in output:
            job['iterations'] = output['iterations']

        job['endTime'] = time.time()
        job['elapsedTime'] = job['endTime'] - job['startTime']
        
        print(f"Worker {index} completed execution in {job['elapsedTime']} seconds")

        for queue in nextQueues:
            queue.put(job)
        workerQueue.task_done()