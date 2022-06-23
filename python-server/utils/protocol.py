import socket
import struct

def write_message(sock: socket.socket, message: dict[str, bytes]):
    maxFields = len(message)
    maxFields = struct.pack("=i", maxFields)
    sock.sendall(maxFields)
    for k, v in message.items():
        fieldName = bytes(k, "ascii")
        packed = struct.pack("=i%dsi" % (len(fieldName),), len(fieldName), fieldName, len(v))
        sock.sendall(packed)
        sock.sendall(v)

def recv_all(sock: socket.socket, size: int) -> bytes:
    b = b''
    bytesRead = 0
    offset = 0
    while (size > bytesRead):
        result = sock.recv(size - bytesRead) #min(size - bytesRead, 4096)
        if (len(result) == 0):
            return None
        b += result
        bytesRead = len(b)
    return b

def unpack_recv(sock: socket.socket, format: str) -> tuple:
    size = struct.calcsize(format)
    value = recv_all(sock, size)
    if value is None:
        return None
    return struct.unpack(format, value)[0]

def read_message(sock: socket.socket) -> dict[str, bytes]:
    message = {}
    maxFields = unpack_recv(sock, "=i")
    if maxFields is None:
        return None
    for i in range(maxFields):
        fieldNameSize = unpack_recv(sock, "=i")
        if fieldNameSize is None:
            return None
        fieldName = unpack_recv(sock, "=%ds" % fieldNameSize)
        fieldSize = unpack_recv(sock, "=i")
        if fieldName is None or fieldNameSize is None:
            return None
        message[fieldName.decode('ascii')] = recv_all(sock, fieldSize)
    return message