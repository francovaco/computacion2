import socket

HOST, PORT = "127.0.0.1", 9006

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.sendto(b"ping\n", (HOST, PORT))
    data, addr = s.recvfrom(2048)
    print(f"< {data!r} desde {addr}")