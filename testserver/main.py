from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import socket
import shutil
import struct
import time
import matplotlib.pyplot as plt
import numpy as np

app = FastAPI()


@app.post("/csvfile")
async def root(file: UploadFile = File(...)):
    with open(f'{file.filename}', "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"file_name": file.filename}

@app.get("/process")
async def process():
    g = np.genfromtxt("../testserver/G-1.csv", dtype=np.float32, delimiter=",")
    print(g[10000], g[10001])
    struct.pack("i", g.size)

    field = "arrayG"
    field = bytes(field, "ascii")
    struct.pack("iisi", 1, len(field), field, g.size)

    def field(name, valueSize):
        name = bytes(name, "ascii")
        return struct.pack("=i%dsi" % (len(name),), len(name), name, valueSize)

    field("arrayG", g.size)

    def connect_host(sock):
        sock.connect(("localhost", 3145))

    def send(sock, g):
        sock.sendall(struct.pack("=i", 1))
        sock.sendall(field("arrayG", len(g)))
        sock.sendall(g)
        return sock.recv(3600*4, socket.MSG_WAITALL)

    def connect(g):
        g = g.tobytes()
        elapsed = time.perf_counter()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
           connect_host(sock)
           f = send(sock, g)
        elapsed = time.perf_counter() - elapsed
        print(f"Completed Execution in {elapsed} seconds")
        return f

    img = connect(g)

    img = np.frombuffer(img, dtype=np.float32)

    def view(img):
        i = img.reshape(60, 60).transpose()
        plt.imsave('test.png', i, cmap="gray")


    view(img)

    def iterfile():
        with open("../testserver/test.png", mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="image/png")