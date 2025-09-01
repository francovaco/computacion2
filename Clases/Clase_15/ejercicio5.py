import socket
import time

HOST, PORT = "127.0.0.1", 9004

def try_connect(max_retries=5, base_backoff=1):
    for attempt in range(1, max_retries + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)  # segundos
                s.connect((HOST, PORT))
                s.sendall(b"ping\n")
                print("Esperando respuesta del servidor...")
                try:
                    data = s.recv(1024)
                    if data:
                        return data
                    else:
                        print("No se recibió respuesta del servidor.")
                        return None
                except socket.timeout:
                    print("Tiempo de espera agotado sin respuesta del servidor.")
                    return None
        except (socket.timeout, ConnectionRefusedError) as e:
            sleep_s = base_backoff * attempt
            print(f"Intento {attempt} falló ({e}). Reintento en {sleep_s:.1f}s...")
            time.sleep(sleep_s)
    raise TimeoutError("Servidor no disponible tras varios reintentos")

if __name__ == "__main__":
    print(try_connect())