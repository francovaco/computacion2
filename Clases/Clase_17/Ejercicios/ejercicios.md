## Ejercicio 1
```python
import http.server
import socketserver
import os
from functools import partial

# --- Configuración ---
PORT = 8000
DIRECTORY = "sitio_web" 

# --- Preparación del Entorno ---
# Crea el directorio y un archivo de ejemplo si no existen.
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)
    with open(os.path.join(DIRECTORY, "index.html"), "w") as f:
        f.write("<h1>Servidor de Archivos</h1><p>Página de inicio.</p>")

# --- Implementación del Servidor ---
# Se crea una clase manejadora que apunta al directorio especificado.
Handler = partial(http.server.SimpleHTTPRequestHandler, directory=DIRECTORY)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Servidor ejecutándose en http://localhost:{PORT}")
    print(f"Sirviendo archivos del directorio: '{DIRECTORY}'")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        httpd.shutdown()
```

## Ejercicio 2
```python
import http.server
import json

# --- "Base de datos" en memoria ---
users = {
    1: {"nombre": "Ada Lovelace", "email": "ada@example.com"},
    2: {"nombre": "Grace Hopper", "email": "grace@example.com"}
}
next_user_id = 3

# --- Manejador de la API ---
class APIHandler(http.server.BaseHTTPRequestHandler):
    
    def _send_response(self, status_code, data, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()
        if data:
            self.wfile.write(json.dumps(data).encode('utf-8'))

    def _get_request_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        return json.loads(body) if body else {}

    def do_GET(self):
        path_parts = self.path.strip('/').split('/')
        
        if path_parts == ['users']:
            # GET /users -> Listar todos los usuarios
            self._send_response(200, list(users.values()))
        elif len(path_parts) == 2 and path_parts[0] == 'users':
            # GET /users/{id} -> Obtener un usuario
            try:
                user_id = int(path_parts[1])
                user = users.get(user_id)
                if user:
                    self._send_response(200, user)
                else:
                    self._send_response(404, {"error": "Usuario no encontrado"})
            except ValueError:
                self._send_response(400, {"error": "ID de usuario inválido"})
        else:
            self._send_response(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        if self.path == '/users':
            # POST /users -> Crear un nuevo usuario
            try:
                data = self._get_request_body()
                global next_user_id
                users[next_user_id] = data
                response = {"id": next_user_id, **data}
                next_user_id += 1
                self._send_response(201, response)
            except (json.JSONDecodeError, KeyError):
                self._send_response(400, {"error": "Datos JSON inválidos"})
        else:
            self._send_response(404, {"error": "Ruta no encontrada"})

    def do_PUT(self):
        path_parts = self.path.strip('/').split('/')
        if len(path_parts) == 2 and path_parts[0] == 'users':
            # PUT /users/{id} -> Actualizar un usuario
            try:
                user_id = int(path_parts[1])
                if user_id in users:
                    data = self._get_request_body()
                    users[user_id].update(data)
                    self._send_response(200, users[user_id])
                else:
                    self._send_response(404, {"error": "Usuario no encontrado"})
            except (ValueError, json.JSONDecodeError):
                self._send_response(400, {"error": "ID o datos inválidos"})
        else:
            self._send_response(404, {"error": "Ruta no encontrada"})
            
    def do_DELETE(self):
        path_parts = self.path.strip('/').split('/')
        if len(path_parts) == 2 and path_parts[0] == 'users':
            # DELETE /users/{id} -> Eliminar un usuario
            try:
                user_id = int(path_parts[1])
                if user_id in users:
                    del users[user_id]
                    self.send_response(204) # Sin contenido
                    self.end_headers()
                else:
                    self._send_response(404, {"error": "Usuario no encontrado"})
            except ValueError:
                self._send_response(400, {"error": "ID de usuario inválido"})
        else:
            self._send_response(404, {"error": "Ruta no encontrada"})

# --- Iniciar el Servidor ---
if __name__ == "__main__":
    PORT = 8080
    with http.server.ThreadingHTTPServer(("", PORT), APIHandler) as httpd:
        print(f"Servidor API REST ejecutándose en http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
```

## Ejercicio 3
```python
import http.server
import socketserver
from urllib.parse import parse_qs
import html

# --- Manejador del Formulario ---
class FormHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Sirve el formulario HTML en la ruta raíz
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Contenido del formulario HTML
            form_html = """
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Formulario</title>
            </head>
            <body>
                <h1>Formulario de Registro</h1>
                <form action="/submit" method="post">
                    <label for="nombre">Nombre:</label><br>
                    <input type="text" id="nombre" name="nombre" required><br><br>
                    
                    <label for="email">Email:</label><br>
                    <input type="email" id="email" name="email" required><br><br>
                    
                    <label for="tema">Tema de Interés:</label><br>
                    <select id="tema" name="tema">
                        <option value="tecnologia">Tecnología</option>
                        <option value="ciencia">Ciencia</option>
                        <option value="arte">Arte</option>
                    </select><br><br>
                    
                    <input type="checkbox" id="suscripcion" name="suscripcion" value="si">
                    <label for="suscripcion">Acepto suscribirme al boletín informativo</label><br><br>
                    
                    <input type="submit" value="Enviar Datos">
                </form>
            </body>
            </html>
            """
            self.wfile.write(form_html.encode('utf-8'))
        else:
            self.send_error(404, "Página no encontrada")

    def do_POST(self):
        # Procesa los datos enviados al endpoint /submit
        if self.path == '/submit':
            # Leer el cuerpo de la solicitud
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Decodificar y parsear los datos del formulario
            form_data = parse_qs(post_data.decode('utf-8'))
            
            # Extraer y limpiar los datos para mostrarlos de forma segura
            nombre = html.escape(form_data.get('nombre', [''])[0])
            email = html.escape(form_data.get('email', [''])[0])
            tema = html.escape(form_data.get('tema', [''])[0])
            suscripcion = "Sí" if 'suscripcion' in form_data else "No"
            
            # Enviar la página de confirmación
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            response_html = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head><title>Confirmación</title></head>
            <body>
                <h1>Datos Recibidos Correctamente</h1>
                <p><strong>Nombre:</strong> {nombre}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Tema de Interés:</strong> {tema}</p>
                <p><strong>Suscripción al boletín:</strong> {suscripcion}</p>
                <br>
                <a href="/">Volver al formulario</a>
            </body>
            </html>
            """
            self.wfile.write(response_html.encode('utf-8'))
        else:
            self.send_error(404, "Página no encontrada")

# --- Iniciar el Servidor ---
if __name__ == "__main__":
    PORT = 8000
    with socketserver.TCPServer(("", PORT), FormHandler) as httpd:
        print(f"Servidor de formularios ejecutándose en http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
```

## Ejercicio 4
```python
import http.server
import socketserver
import os
import cgi
import html
from http import HTTPStatus

# --- Configuración ---
PORT = 8000
UPLOAD_DIR = "uploads"

# --- Preparación del Entorno ---
# Crear el directorio para los archivos subidos si no existe
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- Manejador del Servidor ---
class UploadHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Ruta para mostrar el formulario de subida
        if self.path == '/upload':
            self._serve_upload_form()
        # Ruta para listar los archivos subidos
        elif self.path == '/files':
            self._serve_file_list()
        # Ruta para descargar un archivo específico
        elif self.path.startswith('/files/'):
            self._serve_downloadable_file()
        else:
            # Redirigir la ruta raíz al formulario de subida
            if self.path == '/':
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                self.send_header('Location', '/upload')
                self.end_headers()
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Página no encontrada")

    def do_POST(self):
        # Ruta que procesa la subida del archivo
        if self.path == '/upload':
            self._process_upload()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Página no encontrada")

    def _serve_upload_form(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        form_html = """
        <!DOCTYPE html><html><head><title>Subir Archivo</title></head>
        <body>
            <h1>Formulario para Subir Archivos</h1>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <label for="file_to_upload">Selecciona un archivo:</label>
                <input type="file" name="file_to_upload" id="file_to_upload" required>
                <br><br>
                <input type="submit" value="Subir Archivo" name="submit">
            </form>
            <hr>
            <a href="/files">Ver archivos subidos</a>
        </body></html>
        """
        self.wfile.write(form_html.encode('utf-8'))

    def _serve_file_list(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        try:
            files = os.listdir(UPLOAD_DIR)
            list_html = "<h1>Archivos Subidos</h1><ul>"
            if not files:
                list_html += "<li>No hay archivos todavía.</li>"
            else:
                for filename in files:
                    escaped_name = html.escape(filename)
                    list_html += f'<li><a href="/files/{escaped_name}">{escaped_name}</a></li>'
            list_html += "</ul><br><a href='/upload'>Subir otro archivo</a>"
            self.wfile.write(list_html.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "El directorio de subidas no existe.")
    
    def _serve_downloadable_file(self):
        # Extraer el nombre del archivo de la ruta
        filename = os.path.basename(self.path)
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Validar que el archivo exista y no sea un intento de salir del directorio
        if not os.path.isfile(filepath):
            self.send_error(HTTPStatus.NOT_FOUND, "Archivo no encontrado")
            return

        try:
            with open(filepath, 'rb') as f:
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                fs = os.fstat(f.fileno())
                self.send_header('Content-Length', str(fs.st_size))
                self.end_headers()
                self.wfile.write(f.read())
        except IOError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "No se pudo leer el archivo")

    def _process_upload(self):
        # Utilizar cgi.FieldStorage para parsear el formulario multipart/form-data
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}
        )

        if 'file_to_upload' not in form:
            self._send_simple_response("El formulario no contenía un archivo.", status=HTTPStatus.BAD_REQUEST)
            return

        file_item = form['file_to_upload']

        if not file_item.filename:
            self._send_simple_response("No se seleccionó ningún archivo.", status=HTTPStatus.BAD_REQUEST)
            return

        # Prevenir path traversal attacks
        filename = os.path.basename(file_item.filename)
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Guardar el archivo en el disco
        with open(filepath, 'wb') as f:
            f.write(file_item.file.read())
        
        self._send_simple_response(f"Archivo '{html.escape(filename)}' subido con éxito.<br><a href='/files'>Ver lista de archivos</a>")

    def _send_simple_response(self, message, status=HTTPStatus.OK):
        self.send_response(status)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        response_html = f"<!DOCTYPE html><html><body><p>{message}</p></body></html>"
        self.wfile.write(response_html.encode('utf-8'))


# --- Iniciar el Servidor ---
if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), UploadHandler) as httpd:
        print(f"Servidor de subida de archivos en http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
```

## Ejercicio 5
```python
import http.server
import json
import base64
import time
from datetime import datetime

# --- "Base de datos" en memoria ---
users_data = {
    1: {"nombre": "Ada Lovelace", "email": "ada@example.com"},
    2: {"nombre": "Grace Hopper", "email": "grace@example.com"}
}
next_user_id = 3

# --- Configuración de Seguridad ---
# Usuarios y roles para la autenticación
API_USERS = {
    "writer": {"password": "writepassword123", "role": "write"},
    "reader": {"password": "readpassword456", "role": "read"}
}

# --- Rate Limiting ---
RATE_LIMIT_REQUESTS = 20  # Máximo 20 peticiones
RATE_LIMIT_WINDOW = 60    # por cada 60 segundos
request_timestamps = {}   # Almacena: { 'ip': [timestamp1, timestamp2, ...] }

# --- Manejador de la API con Seguridad ---
class SecureAPIHandler(http.server.BaseHTTPRequestHandler):
    
    def _log_request(self):
        """Imprime un log de cada solicitud en la consola."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {self.client_address[0]} - {self.command} {self.path}")

    def _check_rate_limit(self):
        """Verifica si el cliente ha excedido el límite de solicitudes."""
        client_ip = self.client_address[0]
        current_time = time.time()
        
        # Filtrar timestamps que ya no están en la ventana de tiempo
        if client_ip in request_timestamps:
            request_timestamps[client_ip] = [
                ts for ts in request_timestamps[client_ip] 
                if current_time - ts < RATE_LIMIT_WINDOW
            ]
        else:
            request_timestamps[client_ip] = []
        
        # Comprobar si se ha superado el límite
        if len(request_timestamps[client_ip]) >= RATE_LIMIT_REQUESTS:
            self.send_error(429, "Too Many Requests")
            return False
        
        request_timestamps[client_ip].append(current_time)
        return True

    def _authenticate(self):
        """Verifica las credenciales de Autenticación Básica HTTP."""
        auth_header = self.headers.get('Authorization')
        if auth_header is None:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="API"')
            self.end_headers()
            return None # No autenticado

        # El header es "Basic <credenciales_en_base64>"
        auth_type, credentials_b64 = auth_header.split()
        if auth_type.lower() != 'basic':
            self.send_error(401, "Esquema de autenticación no soportado.")
            return None

        # Decodificar credenciales
        try:
            credentials = base64.b64decode(credentials_b64).decode('utf-8')
            username, password = credentials.split(':', 1)
        except:
            self.send_error(400, "Credenciales mal formadas.")
            return None
        
        # Validar usuario y contraseña
        user = API_USERS.get(username)
        if user and user['password'] == password:
            return user['role'] # Autenticación exitosa, devuelve el rol

        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="API"')
        self.end_headers()
        return None # Contraseña incorrecta
    
    def _handle_request(self, required_role='read'):
        """Método central para gestionar logging, rate limiting y autenticación."""
        self._log_request()
        
        if not self._check_rate_limit():
            return None # Detener si se excede el límite
        
        user_role = self._authenticate()
        if user_role is None:
            return None # Detener si la autenticación falla
            
        # Verificar permisos (rol)
        if required_role == 'write' and user_role != 'write':
            self.send_error(403, "Permiso denegado: se requiere rol de escritura.")
            return None
        
        return user_role # Devolver el rol si todo es correcto

    # --- Implementación de métodos HTTP ---
    def do_GET(self):
        if not self._handle_request(required_role='read'):
            return
        # El resto del código es idéntico al del Ejercicio 2
        path_parts = self.path.strip('/').split('/')
        if path_parts == ['users']:
            self._send_json_response(200, list(users_data.values()))
        elif len(path_parts) == 2 and path_parts[0] == 'users':
            try:
                user_id = int(path_parts[1])
                user = users_data.get(user_id)
                if user: self._send_json_response(200, user)
                else: self._send_json_response(404, {"error": "Usuario no encontrado"})
            except ValueError: self._send_json_response(400, {"error": "ID de usuario inválido"})
        else: self._send_json_response(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        if not self._handle_request(required_role='write'):
            return
        # El resto del código es idéntico al del Ejercicio 2
        global next_user_id
        if self.path == '/users':
            try:
                data = self._get_request_body()
                users_data[next_user_id] = data
                response = {"id": next_user_id, **data}
                next_user_id += 1
                self._send_json_response(201, response)
            except (json.JSONDecodeError, KeyError): self._send_json_response(400, {"error": "Datos inválidos"})
        else: self._send_json_response(404, {"error": "Ruta no encontrada"})

    def do_PUT(self):
        if not self._handle_request(required_role='write'):
            return
        # El resto del código es idéntico al del Ejercicio 2
        path_parts = self.path.strip('/').split('/')
        if len(path_parts) == 2 and path_parts[0] == 'users':
            try:
                user_id = int(path_parts[1])
                if user_id in users_data:
                    data = self._get_request_body()
                    users_data[user_id].update(data)
                    self._send_json_response(200, users_data[user_id])
                else: self._send_json_response(404, {"error": "Usuario no encontrado"})
            except (ValueError, json.JSONDecodeError): self._send_json_response(400, {"error": "ID o datos inválidos"})
        else: self._send_json_response(404, {"error": "Ruta no encontrada"})

    def do_DELETE(self):
        if not self._handle_request(required_role='write'):
            return
        # El resto del código es idéntico al del Ejercicio 2
        path_parts = self.path.strip('/').split('/')
        if len(path_parts) == 2 and path_parts[0] == 'users':
            try:
                user_id = int(path_parts[1])
                if user_id in users_data:
                    del users_data[user_id]
                    self.send_response(204)
                    self.end_headers()
                else: self._send_json_response(404, {"error": "Usuario no encontrado"})
            except ValueError: self._send_json_response(400, {"error": "ID de usuario inválido"})
        else: self._send_json_response(404, {"error": "Ruta no encontrada"})

    # --- Funciones auxiliares (del Ejercicio 2) ---
    def _send_json_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _get_request_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length))

# --- Iniciar el Servidor ---
if __name__ == "__main__":
    PORT = 8080
    with http.server.ThreadingHTTPServer(("", PORT), SecureAPIHandler) as httpd:
        print(f"Servidor API Seguro ejecutándose en http://localhost:{PORT}")
        try: httpd.serve_forever()
        except KeyboardInterrupt: print("\nServidor detenido.")
```

## Ejercicio 6
```python
import http.server
import socketserver
import json
import time
from collections import deque

# --- "Base de datos" del Chat en Memoria ---
MAX_MESSAGES = 50
# Usamos deque para eliminar eficientemente los mensajes más antiguos
messages = deque(maxlen=MAX_MESSAGES)

# --- Manejador del Servidor de Chat ---
class ChatHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Servir la página principal del chat
        if self.path == '/':
            self._serve_chat_client()
        # API para obtener todos los mensajes
        elif self.path == '/messages':
            self._send_json(list(messages))
        # API para obtener mensajes desde un timestamp específico (polling)
        elif self.path.startswith('/messages/since/'):
            try:
                since_ts = float(self.path.split('/')[-1])
                new_messages = [msg for msg in messages if msg['timestamp'] > since_ts]
                self._send_json(new_messages)
            except (ValueError, IndexError):
                self.send_error(400, "Timestamp inválido")
        else:
            self.send_error(404, "Página no encontrada")

    def do_POST(self):
        # API para enviar un nuevo mensaje
        if self.path == '/messages':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                
                if 'user' not in data or 'text' not in data:
                    self.send_error(400, "El mensaje debe contener 'user' y 'text'")
                    return

                new_message = {
                    'user': data['user'],
                    'text': data['text'],
                    'timestamp': time.time()
                }
                messages.append(new_message)
                
                self.send_response(201) # Created
                self.end_headers()
            except json.JSONDecodeError:
                self.send_error(400, "JSON mal formado")
        else:
            self.send_error(404, "Página no encontrada")

    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _serve_chat_client(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Página HTML con el cliente de chat en JavaScript
        client_html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Chat Simple</title>
            <style>
                body { font-family: sans-serif; max-width: 800px; margin: auto; padding: 20px; }
                #chatbox { height: 400px; border: 1px solid #ccc; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
                .message { margin-bottom: 5px; }
                .user { font-weight: bold; }
                #controls { display: flex; }
                #controls input { flex-grow: 1; padding: 8px; }
                #controls button { padding: 8px; }
            </style>
        </head>
        <body>
            <h1>Chat Simple con Polling</h1>
            <div id="chatbox"></div>
            <div id="controls">
                <input type="text" id="userInput" placeholder="Tu nombre">
                <input type="text" id="textInput" placeholder="Escribe un mensaje...">
                <button id="sendButton">Enviar</button>
            </div>

            <script>
                const chatbox = document.getElementById('chatbox');
                const userInput = document.getElementById('userInput');
                const textInput = document.getElementById('textInput');
                const sendButton = document.getElementById('sendButton');

                let lastTimestamp = 0;

                // Función para obtener y mostrar mensajes
                async function fetchMessages() {
                    try {
                        const response = await fetch(`/messages/since/${lastTimestamp}`);
                        if (!response.ok) throw new Error('Error en la red');
                        
                        const newMessages = await response.json();
                        
                        if (newMessages.length > 0) {
                            newMessages.forEach(msg => {
                                const msgElement = document.createElement('div');
                                msgElement.classList.add('message');
                                msgElement.innerHTML = `<span class="user">${escapeHTML(msg.user)}:</span> ${escapeHTML(msg.text)}`;
                                chatbox.appendChild(msgElement);
                                // Actualizar el timestamp al del último mensaje recibido
                                lastTimestamp = msg.timestamp;
                            });
                            // Auto-scroll al final
                            chatbox.scrollTop = chatbox.scrollHeight;
                        }
                    } catch (error) {
                        console.error('Error al obtener mensajes:', error);
                    }
                }

                // Función para enviar un mensaje
                async function sendMessage() {
                    const user = userInput.value.trim();
                    const text = textInput.value.trim();

                    if (!user || !text) {
                        alert('Por favor, ingresa tu nombre y un mensaje.');
                        return;
                    }

                    try {
                        await fetch('/messages', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user, text })
                        });
                        textInput.value = ''; // Limpiar el input
                        textInput.focus();
                        // No necesitamos esperar a la siguiente ronda, podemos llamar a fetchMessages inmediatamente
                        fetchMessages(); 
                    } catch (error) {
                        console.error('Error al enviar mensaje:', error);
                    }
                }
                
                // Función para escapar HTML y prevenir XSS
                function escapeHTML(str) {
                    return str.replace(/[&<>"']/g, function(match) {
                        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[match];
                    });
                }

                // Event Listeners
                sendButton.addEventListener('click', sendMessage);
                textInput.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                });

                // Iniciar el polling
                setInterval(fetchMessages, 2000); // Polling cada 2 segundos
                fetchMessages(); // Carga inicial
            </script>
        </body>
        </html>
        """
        self.wfile.write(client_html.encode('utf-8'))

# --- Iniciar el Servidor ---
if __name__ == "__main__":
    PORT = 8080
    with socketserver.TCPServer(("", PORT), ChatHandler) as httpd:
        print(f"Servidor de Chat ejecutándose en http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
```