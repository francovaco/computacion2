## Ejercicio 1
```python
import socketserver
import os

# --- Configuración ---
HOST, PORT = "localhost", 9998
FILE_DIR = "shared_files"
MAX_PACKET_SIZE = 1024

# --- Preparación del Entorno ---
if not os.path.exists(FILE_DIR):
    os.makedirs(FILE_DIR)
    with open(os.path.join(FILE_DIR, "ejemplo.txt"), "w") as f:
        f.write("Este es un archivo de prueba.")
    with open(os.path.join(FILE_DIR, "otro_archivo.log"), "w") as f:
        f.write("Log de eventos.")

# --- Manejador del Servidor UDP ---
class FileUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data, socket = self.request
        message = data.decode('utf-8').strip()
        command_parts = message.split()
        command = command_parts[0].upper()

        if command == "LIST":
            self._handle_list(socket)
        elif command == "GET" and len(command_parts) > 1:
            filename = command_parts[1]
            self._handle_get(socket, filename)
        else:
            response = "ERROR: Comando no válido. Use LIST o GET <archivo>."
            socket.sendto(response.encode('utf-8'), self.client_address)

    def _handle_list(self, socket):
        try:
            files = os.listdir(FILE_DIR)
            if not files:
                response = "Directorio vacío."
            else:
                response = "\n".join(files)
            socket.sendto(response.encode('utf-8'), self.client_address)
        except Exception as e:
            response = f"ERROR: No se pudo listar el directorio: {e}"
            socket.sendto(response.encode('utf-8'), self.client_address)

    def _handle_get(self, socket, filename):
        filepath = os.path.join(FILE_DIR, os.path.basename(filename))

        if not os.path.isfile(filepath):
            response = "ERROR: Archivo no encontrado."
            socket.sendto(response.encode('utf-8'), self.client_address)
            return

        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            if len(content) > MAX_PACKET_SIZE:
                response = "ERROR: El archivo es demasiado grande para ser enviado por UDP."
                socket.sendto(response.encode('utf-8'), self.client_address)
            else:
                socket.sendto(content, self.client_address)
        except Exception as e:
            response = f"ERROR: No se pudo leer el archivo: {e}"
            socket.sendto(response.encode('utf-8'), self.client_address)

# --- Iniciar el Servidor ---
if __name__ == "__main__":
    with socketserver.UDPServer((HOST, PORT), FileUDPHandler) as server:
        print(f"Servidor de archivos UDP iniciado en {HOST}:{PORT}")
        print(f"Sirviendo archivos desde el directorio: '{FILE_DIR}'")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
```
## Ejecución
```bash
# Para listar los archivos
echo "LIST" | nc -u -w1 localhost 9998

# Para obtener el contenido de un archivo
echo "GET ejemplo.txt" | nc -u -w1 localhost 9998

# Para probar un archivo que no existe
echo "GET noexiste.txt" | nc -u -w1 localhost 9998
```

## Ejercicio 2
```python
import socketserver
import threading
from collections import deque

# --- Configuración del Servidor ---
HOST, PORT = "localhost", 7778
MAX_USERS_PER_ROOM = 10
HISTORY_LENGTH = 10

# --- "Base de datos" en memoria ---
# Almacena usuarios y sus credenciales. 'admin' tiene permisos especiales.
USERS = {
    "admin": {"password": "adminpass", "is_admin": True},
    "user1": {"password": "pass1", "is_admin": False},
    "user2": {"password": "pass2", "is_admin": False},
}

# Almacena las salas, sus usuarios y el historial de mensajes.
# Formato: { 'nombre_sala': {'clients': {'username': socket}, 'history': deque()} }
ROOMS = {
    "general": {
        "clients": {}, 
        "history": deque(maxlen=HISTORY_LENGTH)
    },
    "random": {
        "clients": {}, 
        "history": deque(maxlen=HISTORY_LENGTH)
    }
}
# Lock para proteger el acceso concurrente a las estructuras de datos
STATE_LOCK = threading.Lock()

# --- Manejador del Chat TCP ---
class ChatHandler(socketserver.BaseRequestHandler):
    
    def setup(self):
        self.username = None
        self.current_room = None
        self.is_admin = False

    def handle(self):
        if not self._authenticate():
            return
        
        self.request.sendall(b"Autenticacion exitosa. Bienvenido al servidor.\n")
        self.request.sendall(b"Usa /join <sala> para unirte a una sala (ej. /join general).\n")

        try:
            while True:
                message = self.request.recv(1024).decode('utf-8').strip()
                if not message:
                    break
                
                if message.startswith('/'):
                    self._handle_command(message)
                elif self.current_room:
                    self._broadcast_message(f"[{self.username}]: {message}")
                else:
                    self.request.sendall(b"Debes unirte a una sala para chatear.\n")
        except Exception:
            pass # La limpieza se hace en finish()

    def finish(self):
        if self.username and self.current_room:
            self._leave_room(silent=True)
        print(f"Conexion cerrada con {self.client_address}")

    def _authenticate(self):
        self.request.sendall(b"Usuario: ")
        username = self.request.recv(1024).decode('utf-8').strip()
        self.request.sendall(b"Contrasena: ")
        password = self.request.recv(1024).decode('utf-8').strip()

        user_data = USERS.get(username)
        if user_data and user_data["password"] == password:
            self.username = username
            self.is_admin = user_data["is_admin"]
            return True
        else:
            self.request.sendall(b"Credenciales invalidas.\n")
            return False

    def _handle_command(self, message):
        parts = message.split(' ', 2)
        command = parts[0].lower()

        if command == "/join":
            if len(parts) > 1: self._join_room(parts[1])
        elif command == "/leave":
            self._leave_room()
        elif command == "/kick":
            if self.is_admin and len(parts) > 1: self._kick_user(parts[1])
            else: self.request.sendall(b"No tienes permisos o el comando es invalido.\n")
        else:
            self.request.sendall(b"Comando desconocido.\n")

    def _join_room(self, room_name):
        if self.current_room:
            self._leave_room()
        
        with STATE_LOCK:
            if room_name not in ROOMS:
                # Opcional: crear salas dinámicamente
                ROOMS[room_name] = {"clients": {}, "history": deque(maxlen=HISTORY_LENGTH)}

            room = ROOMS[room_name]
            if len(room["clients"]) >= MAX_USERS_PER_ROOM:
                self.request.sendall(b"La sala esta llena.\n")
                return
            
            # Unir al usuario a la sala
            room["clients"][self.username] = self.request
            self.current_room = room_name

            # Enviar historial
            self.request.sendall(b"--- Inicio del historial ---\n")
            for msg in room["history"]:
                self.request.sendall(f"{msg}\n".encode('utf-8'))
            self.request.sendall(b"--- Fin del historial ---\n")

        self._broadcast_message(f"*** {self.username} se ha unido a la sala. ***")

    def _leave_room(self, silent=False):
        if not self.current_room: return

        room_name = self.current_room
        with STATE_LOCK:
            if room_name in ROOMS and self.username in ROOMS[room_name]["clients"]:
                del ROOMS[room_name]["clients"][self.username]
                self.current_room = None
        
        if not silent:
            self._broadcast_message(f"*** {self.username} ha salido de la sala. ***", room_name=room_name)
            self.request.sendall(b"Has salido de la sala.\n")

    def _kick_user(self, target_username):
        if not self.current_room: return
        
        target_socket = None
        with STATE_LOCK:
            room = ROOMS[self.current_room]
            if target_username in room["clients"]:
                target_socket = room["clients"][target_username]
                del room["clients"][target_username]
        
        if target_socket:
            self._broadcast_message(f"*** {target_username} ha sido expulsado por {self.username}. ***")
            target_socket.sendall(b"Has sido expulsado de la sala.\n")
            target_socket.close()
        else:
            self.request.sendall(b"Usuario no encontrado en la sala.\n")

    def _broadcast_message(self, message, room_name=None):
        if room_name is None:
            room_name = self.current_room
        if not room_name: return

        with STATE_LOCK:
            room = ROOMS.get(room_name)
            if not room: return
            
            room["history"].append(message)
            dead_clients = []
            for username, client_socket in room["clients"].items():
                try:
                    client_socket.sendall(f"{message}\n".encode('utf-8'))
                except:
                    dead_clients.append(username)
            # Limpiar clientes desconectados
            for username in dead_clients:
                del room["clients"][username]

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

# --- Iniciar el Servidor ---
if __name__ == "__main__":
    server = ThreadedTCPServer((HOST, PORT), ChatHandler)
    print(f"Servidor de chat mejorado iniciado en {HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando servidor...")
        server.shutdown()
        server.server_close()
```

## Ejercicio 3
```python
import socketserver
import threading
import socket
from urllib.parse import urlparse
from datetime import datetime

# --- Configuración del Proxy ---
HOST, PORT = "localhost", 8888
CACHE_MAX_SIZE = 50
BLACKLIST = {"example.com", "blocked-site.org"} # Sitios a bloquear

# --- "Base de datos" en memoria para la caché ---
# Formato: { 'url_completa': b'respuesta_http_completa' }
CACHE = {}
CACHE_LOCK = threading.Lock()

# --- Manejador del Proxy TCP ---
class ProxyHandler(socketserver.BaseRequestHandler):

    def handle(self):
        try:
            # 1. Recibir la petición inicial del cliente (navegador)
            request_data = self.request.recv(4096)
            if not request_data:
                return

            self._log(f"Peticion recibida de {self.client_address}")

            # 2. Parsear la primera línea para obtener método, URL y host
            first_line = request_data.decode('utf-8', errors='ignore').split('\n')[0]
            method, full_url, _ = first_line.split()
            
            # Solo manejamos peticiones GET para este ejemplo
            if method.upper() != 'GET':
                self._send_error(501, "Not Implemented", "Solo se soportan peticiones GET.")
                return

            parsed_url = urlparse(full_url)
            dest_host = parsed_url.hostname
            dest_port = parsed_url.port or 80

            # 3. Filtrado de URLs (Blacklist)
            if dest_host in BLACKLIST:
                self._log(f"BLOQUEADO: Peticion a {dest_host}")
                self._send_error(403, "Forbidden", f"El sitio {dest_host} está bloqueado.")
                return

            # 4. Revisar la Caché
            with CACHE_LOCK:
                cached_response = CACHE.get(full_url)
            
            if cached_response:
                self._log(f"CACHE HIT: Sirviendo {full_url} desde la cache.")
                self.request.sendall(cached_response)
                return
            
            self._log(f"CACHE MISS: Peticion para {full_url}")

            # 5. Si no está en caché, reenviar la petición al servidor destino
            response_from_server = self._forward_request(dest_host, dest_port, request_data)

            if response_from_server:
                # 6. Devolver la respuesta al cliente original
                self.request.sendall(response_from_server)
                
                # 7. Guardar en caché si hay espacio
                with CACHE_LOCK:
                    if len(CACHE) < CACHE_MAX_SIZE:
                        self._log(f"CACHE SET: Guardando {full_url} en cache.")
                        CACHE[full_url] = response_from_server

        except Exception as e:
            self._log(f"Error al manejar la peticion: {e}")

    def _forward_request(self, host, port, request_data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.connect((host, port))
                server_socket.sendall(request_data)
                
                self._log(f"Peticion reenviada a {host}:{port}")
                
                # Recibir la respuesta completa del servidor destino
                response = b""
                while True:
                    chunk = server_socket.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                
                self._log(f"Respuesta recibida de {host}")
                return response
        except Exception as e:
            self._log(f"Error al conectar con el servidor destino {host}: {e}")
            self._send_error(502, "Bad Gateway", "No se pudo conectar al servidor de destino.")
            return None

    def _log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [PROXY] {message}")
        
    def _send_error(self, code, title, message):
        error_response = (
            f"HTTP/1.1 {code} {title}\r\n"
            f"Content-Type: text/html\r\n"
            f"Connection: close\r\n\r\n"
            f"<html><body><h1>{code} {title}</h1><p>{message}</p></body></html>"
        ).encode('utf-8')
        self.request.sendall(error_response)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

# --- Iniciar el Servidor ---
if __name__ == "__main__":
    server = ThreadedTCPServer((HOST, PORT), ProxyHandler)
    print(f"Proxy HTTP iniciado en {HOST}:{PORT}")
    print(f"Sitios bloqueados: {BLACKLIST}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando proxy...")
        server.shutdown()
        server.server_close()
```

## Ejercicio 4
```python
import socketserver
import http.server
import threading
import json
import time
from collections import defaultdict, deque

# --- Configuración ---
UDP_HOST, UDP_PORT = "localhost", 9990
HTTP_HOST, HTTP_PORT = "localhost", 9991
PERSISTENCE_FILE = "metrics_data.json"
PERSISTENCE_INTERVAL = 300 # Guardar cada 5 minutos

# --- "Base de datos" en memoria y su Lock ---
# Formato: { 'nombre_metrica': deque([(timestamp, valor), ...]) }
METRICS = defaultdict(lambda: deque(maxlen=100))
METRICS_LOCK = threading.Lock()

# --- Componente 1: Recolector UDP ---
class UDPMetricsHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip().decode('utf-8')
        try:
            metric, value_str, ts_str = data.split(':')
            value, timestamp = float(value_str), float(ts_str)
            
            with METRICS_LOCK:
                METRICS[metric].append((timestamp, value))
            print(f"[UDP] Métrica recibida: {metric}={value}")
        except ValueError:
            print(f"[UDP] Error: Mensaje mal formado recibido: {data}")

# --- Componente 2 & 3: API HTTP y Dashboard ---
class HTTPMetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self._serve_dashboard()
        elif self.path == '/api/metrics':
            self._serve_api_metrics()
        else:
            self.send_error(404, "Not Found")

    def _serve_dashboard(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        dashboard_html = """
        <!DOCTYPE html><html><head><title>Dashboard de Metricas</title>
        <style>body{font-family: monospace; padding: 20px;} pre{background-color: #f0f0f0; padding: 1em;}</style>
        </head><body><h1>Metricas del Sistema</h1><pre id="metrics-data">Cargando...</pre>
        <script>
            async function fetchMetrics() {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                document.getElementById('metrics-data').textContent = JSON.stringify(data, null, 2);
            }
            setInterval(fetchMetrics, 3000); // Actualizar cada 3 segundos
            fetchMetrics(); // Carga inicial
        </script></body></html>
        """
        self.wfile.write(dashboard_html.encode('utf-8'))
        
    def _serve_api_metrics(self):
        output_data = {}
        with METRICS_LOCK:
            # Agregaciones (ej. últimos 60 seg)
            current_time = time.time()
            for metric, values in METRICS.items():
                recent_values = [v for ts, v in values if current_time - ts <= 60]
                if recent_values:
                    output_data[metric] = {
                        "current_value": values[-1][1],
                        "last_60s": {
                            "count": len(recent_values),
                            "avg": sum(recent_values) / len(recent_values),
                            "max": max(recent_values),
                            "min": min(recent_values)
                        }
                    }
        
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(output_data).encode('utf-8'))

# --- Componente 4: Persistencia ---
def persist_metrics():
    while True:
        time.sleep(PERSISTENCE_INTERVAL)
        with METRICS_LOCK:
            # Convertir deques a listas para que sea serializable en JSON
            persist_data = {k: list(v) for k, v in METRICS.items()}
        
        with open(PERSISTENCE_FILE, 'w') as f:
            json.dump(persist_data, f)
        print(f"[PERSISTENCE] Métricas guardadas en {PERSISTENCE_FILE}")

def load_metrics():
    try:
        with open(PERSISTENCE_FILE, 'r') as f:
            loaded_data = json.load(f)
            with METRICS_LOCK:
                for metric, values in loaded_data.items():
                    METRICS[metric].extend(values)
            print(f"[PERSISTENCE] Métricas cargadas de {PERSISTENCE_FILE}")
    except FileNotFoundError:
        print("[PERSISTENCE] No se encontró archivo de persistencia, iniciando en blanco.")

# --- Función Principal para Iniciar Servidores ---
def main():
    load_metrics() # Cargar datos al inicio

    # Iniciar servidor UDP en un hilo
    udp_server = socketserver.UDPServer((UDP_HOST, UDP_PORT), UDPMetricsHandler)
    udp_thread = threading.Thread(target=udp_server.serve_forever)
    udp_thread.daemon = True
    udp_thread.start()
    print(f"Servidor recolector UDP escuchando en {UDP_HOST}:{UDP_PORT}")

    # Iniciar servidor HTTP en otro hilo
    http_server = socketserver.ThreadingTCPServer((HTTP_HOST, HTTP_PORT), HTTPMetricsHandler)
    http_thread = threading.Thread(target=http_server.serve_forever)
    http_thread.daemon = True
    http_thread.start()
    print(f"Servidor API/Dashboard HTTP disponible en http://{HTTP_HOST}:{HTTP_PORT}")
    
    # Iniciar hilo de persistencia
    persistence_thread = threading.Thread(target=persist_metrics)
    persistence_thread.daemon = True
    persistence_thread.start()
    print(f"Persistencia activada cada {PERSISTENCE_INTERVAL} segundos.")

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\nCerrando servidores...")
        udp_server.shutdown()
        http_server.shutdown()

if __name__ == "__main__":
    main()
```
## Ejecución
```bash
# Simular métrica de uso de CPU
echo "cpu_usage:55.2:$(date +%s.%N)" | nc -u -w0 localhost 9990

# Simular uso de memoria
echo "memory_usage:78.9:$(date +%s.%N)" | nc -u -w0 localhost 9990

# Envía varias métricas de CPU para ver las agregaciones
echo "cpu_usage:60.1:$(date +%s.%N)" | nc -u -w0 localhost 9990
echo "cpu_usage:40.5:$(date +%s.%N)" | nc -u -w0 localhost 9990
```