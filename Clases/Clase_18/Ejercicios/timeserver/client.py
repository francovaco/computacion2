import socket
import sys

def send_time_request(host, port):
    """
    Envía una petición 'time' al servidor UDP y muestra la respuesta.
    """
    try:
        # Crear socket UDP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Configurar timeout para no esperar indefinidamente
        client_socket.settimeout(5.0)
        
        # Mensaje a enviar
        message = "time"
        
        print(f"Connecting to UDP server at {host}:{port}")
        print(f"Sending: {message}")
        
        # Enviar mensaje al servidor
        client_socket.sendto(message.encode('utf-8'), (host, port))
        
        # Recibir respuesta
        data, server_address = client_socket.recvfrom(1024)
        response = data.decode('utf-8')
        
        print(f"Response from server: {response}")
        
        # Cerrar socket
        client_socket.close()
        
        return 0
        
    except socket.timeout:
        print("Error: Connection timeout. Server did not respond.")
        return 1
    except ConnectionRefusedError:
        print(f"Error: Connection refused. Is the server running on {host}:{port}?")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    # Configuración del servidor
    # En Docker, usar el nombre del servicio como host
    SERVER_HOST = "udp-server"
    SERVER_PORT = 9876
    
    print("=== UDP Time Client ===")
    exit_code = send_time_request(SERVER_HOST, SERVER_PORT)
    sys.exit(exit_code)