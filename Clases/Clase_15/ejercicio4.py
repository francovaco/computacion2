import socket

def recv_all(sock):
    chunks = []
    while True:
        b = sock.recv(64 * 1024)  # 64 KiB por iteración
        if not b:
            break
        chunks.append(b)
    return b"".join(chunks)

def main():
    HOST, PORT = "127.0.0.1", 9003
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        data = recv_all(s)
        print(f"Recibidos {len(data)} bytes")

if __name__ == "__main__":
    main()