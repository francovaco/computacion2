import socket

HOST, PORT = "127.0.0.1", 9007

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(5)
    retries = 3
    for i in range(1, retries + 1):
        try:
            s.sendto(b"TIME", (HOST, PORT))
            data, _ = s.recvfrom(2048)
            print("Respuesta:", data.decode())
            break
        except socket.timeout:
            print(f"Timeout intento {i}; reintentando...")
    else:
        print("Sin respuesta tras reintentos")