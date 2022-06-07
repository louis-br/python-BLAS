from multiprocessing import Queue
import time
import socket
import protocol
import struct

def connect(msg):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", 3145))
        protocol.write_message(sock, msg)
        f = protocol.read_message(sock)['arrayF']
        f = struct.unpack('=%sf' % int(len(f)//4), f)
    return f

def pack_message(msg):
    arrayG = msg['arrayG']
    return {
        'algorithmIndex': struct.pack('=i', msg['algorithm'] == "CGNR"),
        'arrayG': struct.pack('=%sf' % len(arrayG), *(arrayG)), #TODO
        'maxIterations': struct.pack('=i', msg['maxIterations']),
        'minError': struct.pack('=f', msg['minError'])
    }

def worker(workerQueue: Queue, nextQueue: Queue, i):
    while True:
        job = workerQueue.get()

        if job == 'STOP':
            return
        elapsed = time.perf_counter()
        job['arrayF'] = connect(pack_message(job))
        job.pop('arrayG', None)
        elapsed = time.perf_counter() - elapsed
        print(f"Worker {i} completed execution in {elapsed} seconds")
        
        nextQueue.put(job)