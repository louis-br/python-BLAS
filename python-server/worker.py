from multiprocessing import Queue
import time
import socket
import protocol
import ctypes
import struct

def connect(g):
    #g = g.tobytes()
    g = struct.pack('=%sf' % len(g), *g) #TODO
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", 3145))
        protocol.write_message(sock, {'arrayG': g})
        f = protocol.read_message(sock)['arrayF']
        print(f'f: {(len(f)//4)}')
        f = struct.unpack('=%sf' % int(len(f)//4), f)
    return f

def worker(workerQueue: Queue, doneQueue: Queue):
    while True:
        job = workerQueue.get()
        if job == 'STOP':
            return
        elapsed = time.perf_counter()
        arrayG = job.pop('arrayG', None)
        if arrayG != None:
            job['arrayF'] = connect(arrayG)
        else:
            print("arrayG is None")
        elapsed = time.perf_counter() - elapsed
        print(f"Worker completed execution in {elapsed} seconds")
        doneQueue.put(job)