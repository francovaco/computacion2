## Ejercicio 1
### server.py
```python
import socketserver
import socket

class EchoIPv6Handler(socketserver.BaseRequestHandler):
    """
    Handler que implementa un servidor echo IPv6.
    Convierte mensajes a mayúsculas y soporta comando QUIT.
    """
    
    def handle(self):
        """
        Maneja cada conexión TCP IPv6.
        self.request es el socket TCP conectado al cliente.
        """
        print(f"Connection established with: {self.client_address}")
        
        # Bucle para manejar múltiples mensajes del mismo cliente
        while True:
            try:
                # Recibir datos (máximo 1024 bytes)
                data = self.request.recv(1024)
                
                if not data:
                    # Cliente cerró la conexión
                    print(f"Client {self.client_address} disconnected")
                    break
                
                # Decodificar el mensaje recibido
                message = data.decode('utf-8').strip()
                print(f"Received from {self.client_address}: {message}")
                
                # Verificar comando QUIT
                if message.upper() == 'QUIT':
                    print(f"QUIT command received from {self.client_address}")
                    goodbye_msg = "Goodbye!\n"
                    self.request.sendall(goodbye_msg.encode('utf-8'))
                    break
                
                # Convertir a mayúsculas y enviar respuesta
                response = message.upper() + "\n"
                self.request.sendall(response.encode('utf-8'))
                
            except ConnectionResetError:
                print(f"Connection lost with {self.client_address}")
                break
            except Exception as e:
                print(f"Error handling client {self.client_address}: {e}")
                break


class EchoServerIPv6(socketserver.TCPServer):
    """
    Servidor TCP configurado para IPv6.
    """
    address_family = socket.AF_INET6
    allow_reuse_address = True


if __name__ == "__main__":
    HOST, PORT = "::1", 8888  # Localhost IPv6
    
    # Crear servidor IPv6
    with EchoServerIPv6((HOST, PORT), EchoIPv6Handler) as server:
        print(f"Echo Server IPv6 started on [{HOST}]:{PORT}")
        print("Waiting for connections...")
        print("Clients can send messages (converted to UPPERCASE)")
        print("Send 'QUIT' to close the connection")
        print("Press Ctrl+C to stop the server")
        
        try:
            # Iniciar bucle principal del servidor
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped by user")
```

### cliente.py
```python
import socket
import sys

def run_client(host, port):
    """
    Cliente IPv6 que se conecta al servidor echo.
    Permite enviar múltiples mensajes hasta que se envíe QUIT.
    """
    try:
        # Crear socket IPv6
        client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        
        print(f"Connecting to Echo Server at [{host}]:{port}")
        
        # Conectar al servidor
        client_socket.connect((host, port))
        print("Connected successfully!")
        print("Type your messages (they will be returned in UPPERCASE)")
        print("Type 'QUIT' to exit\n")
        
        while True:
            # Leer mensaje del usuario
            message = input("Enter message: ")
            
            if not message:
                continue
            
            # Enviar mensaje al servidor
            client_socket.sendall(message.encode('utf-8'))
            
            # Recibir respuesta
            response = client_socket.recv(1024).decode('utf-8').strip()
            print(f"Server response: {response}\n")
            
            # Salir si se envió QUIT
            if message.upper() == 'QUIT':
                break
        
        # Cerrar socket
        client_socket.close()
        print("Connection closed")
        
        return 0
        
    except ConnectionRefusedError:
        print(f"Error: Connection refused. Is the server running on [{host}]:{port}?")
        return 1
    except socket.gaierror as e:
        print(f"Error: Address resolution failed: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    # Configuración del servidor
    SERVER_HOST = "::1"  # Localhost IPv6
    SERVER_PORT = 8888
    
    print("=== IPv6 Echo Client ===\n")
    exit_code = run_client(SERVER_HOST, SERVER_PORT)
    sys.exit(exit_code)
```

## Ejercicio 2
### server.py
```python
import socketserver
import socket
import threading

class ChatHandler(socketserver.BaseRequestHandler):
    """
    Handler para el sistema de chat IPv6.
    Cada cliente es manejado en un hilo separado.
    """
    
    # Variable de clase para almacenar clientes conectados
    # Formato: {username: socket}
    clients = {}
    clients_lock = threading.Lock()
    
    def setup(self):
        """Se ejecuta antes de handle() - inicialización"""
        self.username = None
        print(f"New connection from {self.client_address}")
    
    def handle(self):
        """Maneja la comunicación con un cliente específico"""
        try:
            # Solicitar nombre de usuario
            self.request.sendall(b"Enter your username: ")
            username_data = self.request.recv(1024)
            
            if not username_data:
                return
            
            self.username = username_data.decode('utf-8').strip()
            
            # Verificar que el nombre no esté vacío
            if not self.username:
                self.request.sendall(b"Invalid username. Disconnecting.\n")
                return
            
            # Registrar cliente
            with self.clients_lock:
                # Verificar si el nombre ya existe
                if self.username in self.clients:
                    self.request.sendall(b"Username already taken. Disconnecting.\n")
                    return
                
                self.clients[self.username] = self.request
            
            print(f"User '{self.username}' joined the chat")
            
            # Notificar a otros clientes
            self.broadcast_message(f"*** {self.username} joined the chat ***", exclude_self=True)
            
            # Mensaje de bienvenida
            welcome_msg = f"Welcome to the chat, {self.username}!\n"
            welcome_msg += f"Connected users: {len(self.clients)}\n"
            self.request.sendall(welcome_msg.encode('utf-8'))
            
            # Bucle principal de chat
            while True:
                data = self.request.recv(1024)
                
                if not data:
                    break
                
                message = data.decode('utf-8').strip()
                
                if not message:
                    continue
                
                # Formatear y transmitir mensaje
                full_message = f"[{self.username}]: {message}"
                print(full_message)
                self.broadcast_message(full_message, exclude_self=True)
                    
        except ConnectionResetError:
            print(f"Connection lost with {self.username}")
        except Exception as e:
            print(f"Error in handler for {self.username}: {e}")
        
    def finish(self):
        """Se ejecuta después de handle() - limpieza"""
        if self.username:
            # Remover cliente de la lista
            with self.clients_lock:
                self.clients.pop(self.username, None)
            
            # Notificar salida
            leave_msg = f"*** {self.username} left the chat ***"
            self.broadcast_message(leave_msg, exclude_self=True)
            print(f"User '{self.username}' disconnected")
    
    def broadcast_message(self, message, exclude_self=False):
        """Envía un mensaje a todos los clientes conectados"""
        with self.clients_lock:
            dead_clients = []
            
            for username, client_socket in self.clients.items():
                # Excluir al remitente si se especifica
                if exclude_self and username == self.username:
                    continue
                
                try:
                    client_socket.sendall(f"{message}\n".encode('utf-8'))
                except:
                    # Cliente desconectado, marcar para eliminación
                    dead_clients.append(username)
            
            # Limpiar clientes desconectados
            for username in dead_clients:
                self.clients.pop(username, None)
                print(f"Removed dead client: {username}")


class ThreadedChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    Servidor de chat IPv6 que crea un hilo para cada conexión.
    Hereda de ThreadingMixIn para funcionalidad concurrente.
    """
    address_family = socket.AF_INET6
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    HOST, PORT = "::1", 9999
    
    # Crear servidor concurrente
    server = ThreadedChatServer((HOST, PORT), ChatHandler)
    
    print(f"Chat Server IPv6 started on [{HOST}]:{PORT}")
    print(f"Active threads: {threading.active_count()}")
    print("Waiting for clients to connect...")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\nClosing server... Active threads: {threading.active_count()}")
        server.shutdown()
        server.server_close()
```

### cliente.py
```python
import socket
import threading
import sys

class ChatClient:
    """
    Cliente de chat IPv6 con threading para enviar y recibir mensajes simultáneamente.
    """
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
    
    def receive_messages(self):
        """
        Hilo que recibe mensajes del servidor continuamente.
        """
        while self.running:
            try:
                # Recibir mensaje del servidor
                data = self.socket.recv(1024)
                
                if not data:
                    print("\nConnection closed by server")
                    self.running = False
                    break
                
                message = data.decode('utf-8').strip()
                
                # Mostrar mensaje
                print(f"\n{message}")
                print("You: ", end="", flush=True)
                
            except ConnectionResetError:
                print("\nConnection lost")
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f"\nError receiving message: {e}")
                break
    
    def send_messages(self):
        """
        Hilo principal que envía mensajes al servidor.
        """
        print("You: ", end="", flush=True)
        
        while self.running:
            try:
                # Leer mensaje del usuario
                message = input()
                
                if not self.running:
                    break
                
                if not message:
                    print("You: ", end="", flush=True)
                    continue
                
                # Enviar mensaje al servidor
                self.socket.sendall(message.encode('utf-8'))
                print("You: ", end="", flush=True)
                
            except EOFError:
                break
            except Exception as e:
                if self.running:
                    print(f"\nError sending message: {e}")
                break
    
    def connect(self):
        """
        Conecta al servidor de chat y solicita nombre de usuario.
        """
        try:
            # Crear socket IPv6
            self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            
            print(f"Connecting to chat server at [{self.host}]:{self.port}")
            
            # Conectar al servidor
            self.socket.connect((self.host, self.port))
            print("Connected successfully!\n")
            
            # Recibir solicitud de nombre de usuario
            prompt = self.socket.recv(1024).decode('utf-8')
            print(prompt, end="", flush=True)
            
            # Enviar nombre de usuario
            username = input()
            self.socket.sendall(username.encode('utf-8'))
            
            # Recibir mensaje de bienvenida o error
            welcome = self.socket.recv(1024).decode('utf-8')
            print(welcome)
            
            # Verificar si la conexión fue aceptada
            if "Disconnecting" in welcome:
                self.socket.close()
                return False
            
            self.running = True
            
            # Iniciar hilo para recibir mensajes
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
            # Enviar mensajes en el hilo principal
            self.send_messages()
            
            return True
            
        except ConnectionRefusedError:
            print(f"Error: Connection refused. Is the server running on [{self.host}]:{self.port}?")
            return False
        except socket.gaierror as e:
            print(f"Error: Address resolution failed: {e}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            self.disconnect()
    
    def disconnect(self):
        """
        Cierra la conexión limpiamente.
        """
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("\nDisconnected from chat server")


if __name__ == "__main__":
    # Configuración del servidor
    SERVER_HOST = "::1"  # Localhost IPv6
    SERVER_PORT = 9999
    
    print("=== IPv6 Chat Client ===\n")
    
    client = ChatClient(SERVER_HOST, SERVER_PORT)
    
    try:
        client.connect()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        client.disconnect()
    
    sys.exit(0)
```

## Ejercicio 3
### server.py
```python
import socketserver
import socket
import os

class FileServerHandler(socketserver.BaseRequestHandler):
    """
    Handler que implementa un servidor de archivos IPv6.
    Soporta comandos: LIST, GET <filename>, QUIT
    """
    
    # Directorio base donde se encuentran los archivos
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CHUNK_SIZE = 8192
    
    def handle(self):
        """
        Maneja cada conexión TCP IPv6.
        """
        print(f"Connection established with: {self.client_address}")
        
        # Enviar mensaje de bienvenida
        welcome = "File Server IPv6\n"
        welcome += "Commands: LIST, GET <filename>, QUIT\n"
        self.request.sendall(welcome.encode('utf-8'))
        
        # Bucle para manejar múltiples comandos
        while True:
            try:
                # Recibir comando
                data = self.request.recv(1024)
                
                if not data:
                    print(f"Client {self.client_address} disconnected")
                    break
                
                command = data.decode('utf-8').strip()
                print(f"Received from {self.client_address}: {command}")
                
                # Parsear comando
                parts = command.split(maxsplit=1)
                cmd = parts[0].upper()
                
                if cmd == 'QUIT':
                    print(f"QUIT command received from {self.client_address}")
                    self.request.sendall(b"OK:Goodbye\n")
                    break
                
                elif cmd == 'LIST':
                    self.handle_list()
                
                elif cmd == 'GET':
                    if len(parts) < 2:
                        self.send_error("Usage: GET <filename>")
                    else:
                        filename = parts[1]
                        self.handle_get(filename)
                
                else:
                    self.send_error(f"Unknown command: {cmd}")
                
            except ConnectionResetError:
                print(f"Connection lost with {self.client_address}")
                break
            except Exception as e:
                print(f"Error handling client {self.client_address}: {e}")
                self.send_error(f"Internal server error: {e}")
                break
    
    def handle_list(self):
        """
        Maneja el comando LIST - lista archivos en el directorio actual.
        """
        try:
            # Listar archivos en el directorio base
            files = [f for f in os.listdir(self.BASE_DIR) 
                    if os.path.isfile(os.path.join(self.BASE_DIR, f))]
            
            if not files:
                response = "OK:No files available\n"
            else:
                # Formatear lista de archivos con tamaños
                file_list = []
                for filename in sorted(files):
                    filepath = os.path.join(self.BASE_DIR, filename)
                    size = os.path.getsize(filepath)
                    file_list.append(f"{filename} ({size} bytes)")
                
                response = "OK:Files available:\n" + "\n".join(file_list) + "\n"
            
            self.request.sendall(response.encode('utf-8'))
            print(f"Sent file list to {self.client_address}")
            
        except Exception as e:
            self.send_error(f"Error listing files: {e}")
    
    def handle_get(self, filename):
        """
        Maneja el comando GET - envía un archivo al cliente.
        """
        try:
            # Validar nombre de archivo (seguridad contra path traversal)
            if '..' in filename or '/' in filename or '\\' in filename:
                self.send_error("Invalid filename: Path traversal not allowed")
                return
            
            # Construir ruta completa del archivo
            filepath = os.path.join(self.BASE_DIR, filename)
            
            # Verificar que el archivo esté dentro del directorio base
            if not filepath.startswith(self.BASE_DIR):
                self.send_error("File not in allowed directory")
                return
            
            # Verificar que el archivo existe
            if not os.path.exists(filepath):
                self.send_error(f"File does not exist: {filename}")
                return
            
            # Verificar que es un archivo (no directorio)
            if not os.path.isfile(filepath):
                self.send_error(f"Not a file: {filename}")
                return
            
            # Obtener tamaño del archivo
            file_size = os.path.getsize(filepath)
            
            # Enviar respuesta de éxito con tamaño
            header = f"OK:{file_size}\n"
            self.request.sendall(header.encode('utf-8'))
            
            print(f"Sending file '{filename}' ({file_size} bytes) to {self.client_address}")
            
            # Enviar archivo en chunks
            bytes_sent = 0
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    self.request.sendall(chunk)
                    bytes_sent += len(chunk)
            
            print(f"File '{filename}' sent successfully ({bytes_sent} bytes)")
            
        except Exception as e:
            self.send_error(f"Error sending file: {e}")
    
    def send_error(self, message):
        """
        Envía un mensaje de error al cliente.
        """
        error_msg = f"ERROR:{message}\n"
        self.request.sendall(error_msg.encode('utf-8'))
        print(f"Error sent to {self.client_address}: {message}")


class FileServerIPv6(socketserver.TCPServer):
    """
    Servidor TCP configurado para IPv6.
    """
    address_family = socket.AF_INET6
    allow_reuse_address = True


if __name__ == "__main__":
    HOST, PORT = "::1", 8000
    
    # Crear servidor IPv6
    with FileServerIPv6((HOST, PORT), FileServerHandler) as server:
        print(f"File Server IPv6 started on [{HOST}]:{PORT}")
        print(f"Serving files from: {FileServerHandler.BASE_DIR}")
        print("Waiting for connections...")
        print("Press Ctrl+C to stop the server\n")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped by user")
```

### cliente.py
```python
import socket
import sys
import os

class FileClient:
    """
    Cliente de servidor de archivos IPv6.
    Permite listar y descargar archivos.
    """
    
    CHUNK_SIZE = 8192
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
    
    def connect(self):
        """
        Conecta al servidor de archivos.
        """
        try:
            # Crear socket IPv6
            self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            
            print(f"Connecting to file server at [{self.host}]:{self.port}")
            
            # Conectar al servidor
            self.socket.connect((self.host, self.port))
            print("Connected successfully!\n")
            
            # Recibir mensaje de bienvenida
            welcome = self.socket.recv(1024).decode('utf-8')
            print(welcome)
            
            return True
            
        except ConnectionRefusedError:
            print(f"Error: Connection refused. Is the server running on [{self.host}]:{self.port}?")
            return False
        except socket.gaierror as e:
            print(f"Error: Address resolution failed: {e}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def send_command(self, command):
        """
        Envía un comando al servidor.
        """
        try:
            self.socket.sendall(command.encode('utf-8'))
        except Exception as e:
            print(f"Error sending command: {e}")
            raise
    
    def receive_response(self):
        """
        Recibe la primera línea de respuesta del servidor.
        Retorna (status, data) donde status es 'OK' o 'ERROR'
        """
        try:
            # Recibir primera línea de respuesta
            response = b""
            while b"\n" not in response:
                chunk = self.socket.recv(1024)
                if not chunk:
                    raise ConnectionError("Server closed connection")
                response += chunk
            
            # Separar primera línea del resto
            first_line = response.split(b"\n", 1)[0].decode('utf-8')
            
            # Parsear respuesta: "OK:data" o "ERROR:message"
            if ':' in first_line:
                status, data = first_line.split(':', 1)
                return status.strip(), data.strip()
            else:
                return 'ERROR', 'Invalid response format'
                
        except Exception as e:
            print(f"Error receiving response: {e}")
            raise
    
    def list_files(self):
        """
        Lista los archivos disponibles en el servidor.
        """
        print("Requesting file list...")
        self.send_command("LIST\n")
        
        # Recibir respuesta completa
        response = b""
        while True:
            chunk = self.socket.recv(1024)
            if not chunk:
                break
            response += chunk
            # Si recibimos un salto de línea doble o un prompt, terminamos
            if b"\n\n" in response or response.endswith(b"\n"):
                break
        
        # Decodificar y mostrar
        response_text = response.decode('utf-8')
        
        if response_text.startswith('OK:'):
            # Extraer contenido después de "OK:"
            content = response_text.split(':', 1)[1].strip()
            print(f"\n{content}\n")
        elif response_text.startswith('ERROR:'):
            error_msg = response_text.split(':', 1)[1].strip()
            print(f"\nError: {error_msg}\n")
        else:
            print(f"\n{response_text}\n")
    
    def download_file(self, filename, save_as=None):
        """
        Descarga un archivo del servidor.
        """
        if save_as is None:
            save_as = filename
        
        print(f"Requesting file: {filename}")
        self.send_command(f"GET {filename}\n")
        
        # Recibir respuesta
        status, data = self.receive_response()
        
        if status == 'ERROR':
            print(f"\nError: {data}\n")
            return False
        
        if status == 'OK':
            try:
                file_size = int(data)
                print(f"File size: {file_size} bytes")
                print(f"Downloading to: {save_as}")
                
                # Recibir archivo en chunks
                bytes_received = 0
                with open(save_as, 'wb') as f:
                    while bytes_received < file_size:
                        remaining = file_size - bytes_received
                        chunk_size = min(self.CHUNK_SIZE, remaining)
                        chunk = self.socket.recv(chunk_size)
                        
                        if not chunk:
                            raise ConnectionError("Connection lost during download")
                        
                        f.write(chunk)
                        bytes_received += len(chunk)
                        
                        # Mostrar progreso
                        progress = (bytes_received / file_size) * 100
                        print(f"\rProgress: {progress:.1f}% ({bytes_received}/{file_size} bytes)", end='', flush=True)
                
                print(f"\n\nFile downloaded successfully: {save_as}\n")
                return True
                
            except ValueError:
                print(f"\nError: Invalid file size received: {data}\n")
                return False
            except Exception as e:
                print(f"\nError during download: {e}\n")
                return False
        
        return False
    
    def quit(self):
        """
        Envía comando QUIT y cierra la conexión.
        """
        try:
            self.send_command("QUIT\n")
            response = self.socket.recv(1024).decode('utf-8')
            print(response)
        except:
            pass
        finally:
            self.disconnect()
    
    def disconnect(self):
        """
        Cierra la conexión.
        """
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("Disconnected from server")
    
    def interactive_mode(self):
        """
        Modo interactivo para el cliente.
        """
        print("\n=== Interactive Mode ===")
        print("Commands:")
        print("  list           - List available files")
        print("  get <filename> - Download a file")
        print("  quit           - Exit\n")
        
        while True:
            try:
                command = input("file-client> ").strip()
                
                if not command:
                    continue
                
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                
                if cmd == 'quit':
                    self.quit()
                    break
                
                elif cmd == 'list':
                    self.list_files()
                
                elif cmd == 'get':
                    if len(parts) < 2:
                        print("Usage: get <filename>\n")
                    else:
                        filename = parts[1]
                        self.download_file(filename)
                
                else:
                    print(f"Unknown command: {cmd}\n")
                
            except KeyboardInterrupt:
                print("\n")
                self.quit()
                break
            except Exception as e:
                print(f"Error: {e}\n")
                break


if __name__ == "__main__":
    # Configuración del servidor
    SERVER_HOST = "::1"  # Localhost IPv6
    SERVER_PORT = 8000
    
    print("=== IPv6 File Client ===\n")
    
    client = FileClient(SERVER_HOST, SERVER_PORT)
    
    if client.connect():
        client.interactive_mode()
    
    sys.exit(0)
```

## Ejercicio 4
### server.py
```python
import socketserver
import socket
import threading
import time
import os
from datetime import datetime

class ConnectionStats:
    """
    Clase para almacenar estadísticas de conexiones.
    """
    def __init__(self):
        self.ipv4_connections = 0
        self.ipv6_connections = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0
        self.connection_times = []  # Lista de tiempos de conexión
        self.lock = threading.Lock()
    
    def add_connection(self, protocol, duration, bytes_sent, bytes_received):
        """
        Registra una conexión completada.
        """
        with self.lock:
            if protocol == 'IPv4':
                self.ipv4_connections += 1
            else:
                self.ipv6_connections += 1
            
            self.total_bytes_sent += bytes_sent
            self.total_bytes_received += bytes_received
            self.connection_times.append(duration)
    
    def get_average_connection_time(self):
        """
        Calcula el tiempo promedio de conexión.
        """
        with self.lock:
            if not self.connection_times:
                return 0.0
            return sum(self.connection_times) / len(self.connection_times)
    
    def get_total_connections(self):
        """
        Retorna el total de conexiones.
        """
        with self.lock:
            return self.ipv4_connections + self.ipv6_connections
    
    def generate_report(self, filename='log.txt'):
        """
        Genera un reporte con las estadísticas recopiladas.
        """
        with self.lock:
            report = []
            report.append("=" * 60)
            report.append("DUAL STACK SERVER - STATISTICS REPORT")
            report.append("=" * 60)
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            report.append("CONNECTION STATISTICS:")
            report.append(f"  Total connections: {self.get_total_connections()}")
            report.append(f"  IPv4 connections: {self.ipv4_connections}")
            report.append(f"  IPv6 connections: {self.ipv6_connections}")
            report.append("")
            report.append("DATA TRANSFER:")
            report.append(f"  Total bytes sent: {self.total_bytes_sent}")
            report.append(f"  Total bytes received: {self.total_bytes_received}")
            report.append(f"  Total bytes transferred: {self.total_bytes_sent + self.total_bytes_received}")
            report.append("")
            report.append("TIMING:")
            report.append(f"  Average connection time: {self.get_average_connection_time():.4f} seconds")
            
            if self.connection_times:
                report.append(f"  Shortest connection: {min(self.connection_times):.4f} seconds")
                report.append(f"  Longest connection: {max(self.connection_times):.4f} seconds")
            
            report.append("=" * 60)
            
            # Guardar en archivo
            report_text = "\n".join(report)
            
            try:
                log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                with open(log_path, 'w') as f:
                    f.write(report_text)
                print(f"\nReport saved to: {log_path}")
            except Exception as e:
                print(f"\nError saving report: {e}")
            
            # También imprimir en consola
            print("\n" + report_text)


# Instancia global de estadísticas
stats = ConnectionStats()


class DualStackHandler(socketserver.BaseRequestHandler):
    """
    Handler que maneja conexiones IPv4 e IPv6 y recopila estadísticas.
    """
    
    def handle(self):
        """
        Maneja cada conexión y recopila estadísticas.
        """
        # Detectar protocolo
        client_ip = self.client_address[0]
        if ':' in client_ip:
            protocol = 'IPv6'
        else:
            protocol = 'IPv4'
        
        # Tiempo de inicio
        start_time = time.time()
        bytes_sent = 0
        bytes_received = 0
        
        print(f"[{protocol}] Connection from: {self.client_address}")
        
        try:
            # Enviar mensaje de conexión exitosa
            welcome_msg = f"Connection successful!\nProtocol: {protocol}\nServer: Dual Stack Server\n"
            self.request.sendall(welcome_msg.encode('utf-8'))
            bytes_sent += len(welcome_msg.encode('utf-8'))
            
            # Mantener conexión abierta y recibir datos
            while True:
                data = self.request.recv(1024)
                
                if not data:
                    break
                
                bytes_received += len(data)
                
                # Echo de los datos recibidos
                message = data.decode('utf-8').strip()
                print(f"[{protocol}] Received from {self.client_address}: {message}")
                
                # Responder
                response = f"Echo [{protocol}]: {message}\n"
                self.request.sendall(response.encode('utf-8'))
                bytes_sent += len(response.encode('utf-8'))
        
        except ConnectionResetError:
            print(f"[{protocol}] Connection lost with {self.client_address}")
        except Exception as e:
            print(f"[{protocol}] Error handling {self.client_address}: {e}")
        finally:
            # Calcular duración de la conexión
            end_time = time.time()
            duration = end_time - start_time
            
            # Registrar estadísticas
            stats.add_connection(protocol, duration, bytes_sent, bytes_received)
            
            print(f"[{protocol}] Connection closed: {self.client_address}")
            print(f"  Duration: {duration:.4f}s, Sent: {bytes_sent}B, Received: {bytes_received}B")


class ServerIPv4(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    Servidor TCP IPv4 con threading.
    """
    address_family = socket.AF_INET
    allow_reuse_address = True
    daemon_threads = True


class ServerIPv6(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    Servidor TCP IPv6 con threading.
    """
    address_family = socket.AF_INET6
    allow_reuse_address = True
    daemon_threads = True


def start_server(server_class, host, port, handler):
    """
    Inicia un servidor en un hilo separado.
    """
    try:
        server = server_class((host, port), handler)
        protocol = "IPv4" if server.address_family == socket.AF_INET else "IPv6"
        print(f"[{protocol}] Server started on {host}:{port}")
        
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        
        return server, thread
    except Exception as e:
        protocol = "IPv4" if server_class.address_family == socket.AF_INET else "IPv6"
        print(f"[{protocol}] Error starting server: {e}")
        return None, None


if __name__ == "__main__":
    PORT = 7777
    servers = []
    
    print("=" * 60)
    print("DUAL STACK SERVER - IPv4 and IPv6")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"Active threads: {threading.active_count()}")
    print()
    
    # Iniciar servidor IPv4
    srv4, thread4 = start_server(ServerIPv4, "127.0.0.1", PORT, DualStackHandler)
    if srv4:
        servers.append(srv4)
    
    # Iniciar servidor IPv6
    srv6, thread6 = start_server(ServerIPv6, "::1", PORT, DualStackHandler)
    if srv6:
        servers.append(srv6)
    
    if not servers:
        print("Error: No servers could be started")
        exit(1)
    
    print("\nServers running. Press Ctrl+C to stop and generate report.\n")
    
    try:
        # Mantener el programa principal activo
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping servers...")
        
        # Detener todos los servidores
        for server in servers:
            server.shutdown()
            server.server_close()
        
        # Generar reporte
        stats.generate_report()
        
        print("\nServers stopped.")
```

### cliente.py
```python
import socket
import sys
import time

class DualStackClient:
    """
    Cliente que puede conectarse vía IPv4 o IPv6 al servidor dual stack.
    """
    
    def __init__(self, host, port, use_ipv6=False):
        self.host = host
        self.port = port
        self.use_ipv6 = use_ipv6
        self.socket = None
    
    def connect(self):
        """
        Conecta al servidor usando IPv4 o IPv6.
        """
        try:
            # Determinar familia de direcciones
            if self.use_ipv6:
                family = socket.AF_INET6
                protocol = "IPv6"
            else:
                family = socket.AF_INET
                protocol = "IPv4"
            
            # Crear socket
            self.socket = socket.socket(family, socket.SOCK_STREAM)
            
            print(f"Connecting to server at {self.host}:{self.port} using {protocol}...")
            
            # Conectar al servidor
            self.socket.connect((self.host, self.port))
            print("Connected successfully!\n")
            
            # Recibir mensaje de bienvenida
            welcome = self.socket.recv(1024).decode('utf-8')
            print("Server response:")
            print(welcome)
            
            return True
            
        except ConnectionRefusedError:
            print(f"Error: Connection refused. Is the server running on {self.host}:{self.port}?")
            return False
        except socket.gaierror as e:
            print(f"Error: Address resolution failed: {e}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def send_message(self, message):
        """
        Envía un mensaje al servidor.
        """
        try:
            self.socket.sendall(message.encode('utf-8'))
            
            # Recibir respuesta
            response = self.socket.recv(1024).decode('utf-8').strip()
            print(f"Server: {response}\n")
            
        except Exception as e:
            print(f"Error sending message: {e}")
            raise
    
    def interactive_mode(self):
        """
        Modo interactivo para enviar mensajes.
        """
        print("=== Interactive Mode ===")
        print("Type messages to send to server")
        print("Press Ctrl+C or type 'quit' to exit\n")
        
        try:
            while True:
                message = input("You: ").strip()
                
                if not message:
                    continue
                
                if message.lower() == 'quit':
                    break
                
                self.send_message(message)
                
        except KeyboardInterrupt:
            print("\n")
        except Exception as e:
            print(f"Error: {e}")
    
    def disconnect(self):
        """
        Cierra la conexión.
        """
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("Disconnected from server")


def main():
    """
    Función principal que maneja argumentos y ejecuta el cliente.
    """
    PORT = 7777
    
    print("=== DUAL STACK CLIENT ===\n")
    
    # Preguntar al usuario qué protocolo usar
    print("Select protocol:")
    print("1. IPv4")
    print("2. IPv6")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        host = "127.0.0.1"
        use_ipv6 = False
        protocol_name = "IPv4"
    elif choice == '2':
        host = "::1"
        use_ipv6 = True
        protocol_name = "IPv6"
    else:
        print("Invalid choice. Using IPv4 by default.")
        host = "127.0.0.1"
        use_ipv6 = False
        protocol_name = "IPv4"
    
    print(f"\nUsing {protocol_name}\n")
    
    # Crear y conectar cliente
    client = DualStackClient(host, PORT, use_ipv6)
    
    if client.connect():
        # Modo interactivo
        client.interactive_mode()
    
    # Desconectar
    client.disconnect()
    
    sys.exit(0)


if __name__ == "__main__":
    main()
```

## Ejercicio 5
### server.py
```python
import socketserver
import socket
import math
import re
import ast
import operator

class CalculatorHandler(socketserver.BaseRequestHandler):
    """
    Handler que implementa una calculadora remota con IPv6.
    Evalúa expresiones matemáticas de forma segura.
    """
    
    # Operadores permitidos
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    # Funciones matemáticas permitidas del módulo math
    ALLOWED_FUNCTIONS = {
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'ceil': math.ceil,
        'floor': math.floor,
        'abs': abs,
        'pow': pow,
    }
    
    # Constantes matemáticas permitidas
    ALLOWED_CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
    }
    
    def handle(self):
        """
        Maneja cada conexión TCP IPv6.
        """
        print(f"Connection established with: {self.client_address}")
        
        # Enviar mensaje de bienvenida
        welcome = "Remote Calculator Server IPv6\n"
        welcome += "Enter mathematical expressions to evaluate\n"
        welcome += "Supported: +, -, *, /, //, %, **\n"
        welcome += "Functions: sqrt, sin, cos, tan, log, exp, etc.\n"
        welcome += "Constants: pi, e\n"
        welcome += "Type 'quit' to exit\n"
        self.request.sendall(welcome.encode('utf-8'))
        
        # Bucle para manejar múltiples expresiones
        while True:
            try:
                # Recibir expresión
                data = self.request.recv(1024)
                
                if not data:
                    print(f"Client {self.client_address} disconnected")
                    break
                
                expression = data.decode('utf-8').strip()
                print(f"Received from {self.client_address}: {expression}")
                
                # Verificar comando quit
                if expression.lower() == 'quit':
                    print(f"QUIT command received from {self.client_address}")
                    self.request.sendall(b"Goodbye!\n")
                    break
                
                # Evaluar expresión
                result = self.evaluate_expression(expression)
                
                # Enviar respuesta
                self.request.sendall(result.encode('utf-8'))
                
            except ConnectionResetError:
                print(f"Connection lost with {self.client_address}")
                break
            except Exception as e:
                print(f"Error handling client {self.client_address}: {e}")
                break
    
    def evaluate_expression(self, expression):
        """
        Evalúa una expresión matemática de forma segura.
        Retorna una cadena con el resultado o error.
        """
        try:
            # Validación básica: verificar caracteres permitidos
            if not self.is_safe_expression(expression):
                return "ERROR: Invalid characters in expression\n"
            
            # Reemplazar constantes
            expression = self.replace_constants(expression)
            
            # Parsear la expresión
            tree = ast.parse(expression, mode='eval')
            
            # Evaluar la expresión de forma segura
            result = self.safe_eval(tree.body)
            
            # Formatear resultado
            if isinstance(result, float):
                # Redondear si es muy cercano a un entero
                if abs(result - round(result)) < 1e-10:
                    result = int(round(result))
                else:
                    result = round(result, 10)  # Limitar decimales
            
            return f"RESULTADO: {result}\n"
            
        except ZeroDivisionError:
            return "ERROR: División por cero\n"
        except ValueError as e:
            return f"ERROR: Valor inválido - {str(e)}\n"
        except TypeError as e:
            return f"ERROR: Tipo inválido - {str(e)}\n"
        except SyntaxError:
            return "ERROR: Sintaxis inválida\n"
        except Exception as e:
            return f"ERROR: {str(e)}\n"
    
    def is_safe_expression(self, expression):
        """
        Verifica que la expresión solo contenga caracteres seguros.
        """
        # Permitir: números, operadores, paréntesis, espacios, letras (para funciones)
        pattern = r'^[0-9+\-*/().,\s%a-zA-Z_]+$'
        return bool(re.match(pattern, expression))
    
    def replace_constants(self, expression):
        """
        Reemplaza constantes matemáticas por sus valores.
        """
        for name, value in self.ALLOWED_CONSTANTS.items():
            # Reemplazar solo palabras completas
            expression = re.sub(r'\b' + name + r'\b', str(value), expression)
        return expression
    
    def safe_eval(self, node):
        """
        Evalúa un nodo AST de forma segura.
        Solo permite operaciones y funciones matemáticas predefinidas.
        """
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python 3.7 y anteriores
            return node.n
        elif isinstance(node, ast.BinOp):
            # Operación binaria: +, -, *, /, etc.
            op_type = type(node.op)
            if op_type not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Operator not allowed: {op_type.__name__}")
            
            left = self.safe_eval(node.left)
            right = self.safe_eval(node.right)
            op_func = self.ALLOWED_OPERATORS[op_type]
            
            return op_func(left, right)
        
        elif isinstance(node, ast.UnaryOp):
            # Operación unaria: -, +
            op_type = type(node.op)
            if op_type not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Operator not allowed: {op_type.__name__}")
            
            operand = self.safe_eval(node.operand)
            op_func = self.ALLOWED_OPERATORS[op_type]
            
            return op_func(operand)
        
        elif isinstance(node, ast.Call):
            # Llamada a función: sqrt(), sin(), etc.
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls allowed")
            
            func_name = node.func.id
            if func_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"Function not allowed: {func_name}")
            
            # Evaluar argumentos
            args = [self.safe_eval(arg) for arg in node.args]
            
            # Ejecutar función
            func = self.ALLOWED_FUNCTIONS[func_name]
            return func(*args)
        
        elif isinstance(node, ast.Name):
            # Variables/constantes (ya reemplazadas)
            raise ValueError(f"Variable not allowed: {node.id}")
        
        else:
            raise ValueError(f"Expression type not allowed: {type(node).__name__}")


class CalculatorServerIPv6(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    Servidor TCP IPv6 con threading para calculadora remota.
    """
    address_family = socket.AF_INET6
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    HOST, PORT = "::1", 5555
    
    # Crear servidor IPv6
    with CalculatorServerIPv6((HOST, PORT), CalculatorHandler) as server:
        print(f"Calculator Server IPv6 started on [{HOST}]:{PORT}")
        print("Waiting for connections...")
        print("Press Ctrl+C to stop the server\n")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped by user")
```

### cliente.py
```python
import socket
import sys

class CalculatorClient:
    """
    Cliente de calculadora remota IPv6.
    Permite enviar expresiones matemáticas y recibir resultados.
    """
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
    
    def connect(self):
        """
        Conecta al servidor de calculadora.
        """
        try:
            # Crear socket IPv6
            self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            
            print(f"Connecting to calculator server at [{self.host}]:{self.port}")
            
            # Conectar al servidor
            self.socket.connect((self.host, self.port))
            print("Connected successfully!\n")
            
            # Recibir mensaje de bienvenida
            welcome = self.socket.recv(2048).decode('utf-8')
            print(welcome)
            
            return True
            
        except ConnectionRefusedError:
            print(f"Error: Connection refused. Is the server running on [{self.host}]:{self.port}?")
            return False
        except socket.gaierror as e:
            print(f"Error: Address resolution failed: {e}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def send_expression(self, expression):
        """
        Envía una expresión matemática al servidor y recibe el resultado.
        """
        try:
            # Enviar expresión
            self.socket.sendall(expression.encode('utf-8'))
            
            # Recibir respuesta
            response = self.socket.recv(1024).decode('utf-8').strip()
            return response
            
        except Exception as e:
            return f"Error sending expression: {e}"
    
    def interactive_mode(self):
        """
        Modo interactivo para ingresar expresiones matemáticas.
        """
        print("=== Interactive Calculator ===")
        print("Enter mathematical expressions")
        print("Examples:")
        print("  2 + 2")
        print("  sqrt(16)")
        print("  sin(pi/2)")
        print("  10 / 0")
        print("Type 'quit' to exit\n")
        
        while True:
            try:
                # Leer expresión del usuario
                expression = input("Expression: ").strip()
                
                if not expression:
                    continue
                
                # Enviar expresión
                result = self.send_expression(expression)
                print(result)
                
                # Salir si se envió quit
                if expression.lower() == 'quit':
                    break
                
                print()  # Línea en blanco para separar
                
            except KeyboardInterrupt:
                print("\n")
                self.send_expression("quit")
                break
            except Exception as e:
                print(f"Error: {e}\n")
                break
    
    def disconnect(self):
        """
        Cierra la conexión.
        """
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("Disconnected from server")


if __name__ == "__main__":
    # Configuración del servidor
    SERVER_HOST = "::1"  # Localhost IPv6
    SERVER_PORT = 5555
    
    print("=== IPv6 Calculator Client ===\n")
    
    client = CalculatorClient(SERVER_HOST, SERVER_PORT)
    
    if client.connect():
        client.interactive_mode()
    
    client.disconnect()
    
    sys.exit(0)
```