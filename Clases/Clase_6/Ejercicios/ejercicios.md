### Ejercicio 1 — Lectura diferida
**Objetivo**: Comprender el bloqueo de lectura en un FIFO.
**lector_fifo.py**:
```python
import os

fifo_path = "/tmp/test_fifo"

if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)
    print(f"FIFO creado en {fifo_path}")

print("Esperando datos en el FIFO...")
with open(fifo_path, "r") as fifo:
    while True:
        linea = fifo.readline()
        if not linea:
            break  
        print("Leído:", linea.strip())
```
**escritor_fifo.py**:
```python
import os
import time

fifo_path = "/tmp/test_fifo"

if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)
    print(f"FIFO creado en {fifo_path}")

print("Escribiendo datos al FIFO...")
with open(fifo_path, "w") as fifo:
    fifo.write("Primera línea\n")
    time.sleep(1)
    fifo.write("Segunda línea\n")
    time.sleep(1)
    fifo.write("Tercera línea\n")
print("Escritura finalizada.")
```
### Pregunta 1: ¿Qué se observa en el lector mientras espera?

El lector queda **bloqueado** en la línea `open(fifo_path, "r")` o en `readline()` hasta que el escritor comience a enviar datos.  
No imprime nada hasta que recibe al menos una línea.

### Pregunta 2: ¿Qué ocurre si se escriben múltiples líneas desde el escritor?
 
Cada línea escrita es **recibida secuencialmente** por el lector.  
El lector imprime cada línea apenas se recibe, respetando el **orden de llegada (FIFO)**.

### Ejercicio 2 — FIFO como buffer entre procesos
**Objetivo**: Simular un flujo de datos continuo entre dos procesos.
**escritor_fifo.py**:
```python
import os
import time

FIFO_PATH = "/tmp/fifo_buffer"

def productor():
    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)

    with open(FIFO_PATH, "w") as fifo:
        for i in range(1, 101):
            fifo.write(f"{i}\n")
            fifo.flush()  # Asegura que los datos se escriban inmediatamente
            print(f"Productor: Escribió {i}")
            time.sleep(0.1)

if __name__ == "__main__":
    productor()
```
**lector_fifo.py**:
```python
import os
import time
from datetime import datetime

FIFO_PATH = "/tmp/fifo_buffer"

def consumidor():
    if not os.path.exists(FIFO_PATH):
        print("El FIFO no existe. Asegúrate de que el productor lo haya creado.")
        return

    ultimo_numero = 0

    with open(FIFO_PATH, "r") as fifo:
        while True:
            data = fifo.readline().strip()
            if data:
                numero = int(data)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"Consumidor: Leyó {numero} a las {timestamp}")

                # Verificar si hay números faltantes
                if numero != ultimo_numero + 1 and ultimo_numero != 0:
                    print(f"Advertencia: Número faltante detectado entre {ultimo_numero} y {numero}")
                
                ultimo_numero = numero
            else:
                time.sleep(0.1)  # Esperar si no hay datos nuevos

if __name__ == "__main__":
    consumidor()
```

### Ejercicio 3 — FIFO + archivos
**Objetivo**: Usar un FIFO como entrada para un proceso que guarda datos en un archivo.
**escritor_fifo.py**:
```python
import os

FIFO_PATH = "/tmp/fifo_to_file"

def escritor():
    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)

    print("Escribe líneas para enviarlas al FIFO. Escribe 'exit' para salir.")
    with open(FIFO_PATH, "w") as fifo:
        while True:
            linea = input("> ")
            if linea.strip().lower() == "exit":
                print("Cerrando escritor...")
                break
            fifo.write(linea + "\n")
            fifo.flush()  # Asegura que los datos se envíen inmediatamente

if __name__ == "__main__":
    escritor()
```
**lector_fifo.py**:
```python
import os

FIFO_PATH = "/tmp/fifo_to_file"
OUTPUT_FILE = "output.txt"

def lector():
    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)

    print(f"Escuchando el FIFO en {FIFO_PATH} y guardando en {OUTPUT_FILE}...")
    with open(FIFO_PATH, "r") as fifo, open(OUTPUT_FILE, "a") as output_file:
        while True:
            linea = fifo.readline().strip()
            if not linea:
                continue
            print(f"Lector: Recibido '{linea}'")
            output_file.write(linea + "\n")
            output_file.flush()  # Asegura que los datos se guarden inmediatamente

if __name__ == "__main__":
    lector()
```

### Ejercicio 4 — Múltiples productores
**Objetivo**: Estudiar el comportamiento de múltiples escritores sobre un mismo FIFO.
**escritor_fifo.py**:
```python
import os
import time
import sys

FIFO_PATH = "/tmp/fifo_multi"

def productor(id_productor):
    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)

    with open(FIFO_PATH, "w") as fifo:
        for i in range(10):  # Cada productor enviará 10 mensajes
            mensaje = f"Soy productor {id_productor}, mensaje {i + 1}"
            fifo.write(mensaje + "\n")
            fifo.flush()  # Asegura que los datos se envíen inmediatamente
            print(f"Productor {id_productor}: Escribió '{mensaje}'")
            time.sleep(1)  # Simula un intervalo entre mensajes

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 productor.py <id_productor>")
        sys.exit(1)

    id_productor = sys.argv[1]
    productor(id_productor)
```

**lector_fifo.py**:
```python
import os

FIFO_PATH = "/tmp/fifo_multi"

def lector():
    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)

    print(f"Escuchando mensajes en {FIFO_PATH}...")
    with open(FIFO_PATH, "r") as fifo:
        while True:
            mensaje = fifo.readline().strip()
            if mensaje:
                print(f"Lector: Recibido '{mensaje}'")

if __name__ == "__main__":
    lector()
```
### Reflexión: ¿Qué pasa si todos escriben al mismo tiempo? ¿Hay mezcla de líneas? ¿Es atómico?

¿Qué pasa si todos escriben al mismo tiempo?

Los mensajes se almacenan en el FIFO en el orden en que llegan. Si varios productores escriben simultáneamente, el sistema operativo gestiona el acceso al FIFO para evitar conflictos.

¿Hay mezcla de líneas?

No debería haber mezcla de líneas, ya que las operaciones de escritura en un FIFO son atómicas si el tamaño del mensaje es menor que el tamaño del buffer del FIFO (generalmente 4 KB en sistemas Unix/Linux).

¿Es atómico?

Sí, las escrituras al FIFO son atómicas siempre que el tamaño del mensaje sea menor que el tamaño del buffer.

### Ejercicio 5 — FIFO con apertura condicional
**Objetivo**: Usar `os.open()` y manejar errores.
**lector_fifo.py**:
```python
import os
import time
import errno

FIFO_PATH = "/tmp/fifo_condicional"

def lector():
    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)

    intentos = 5
    for intento in range(intentos):
        try:
            print(f"Intentando abrir el FIFO (intento {intento + 1}/{intentos})...")
            fifo_fd = os.open(FIFO_PATH, os.O_RDONLY | os.O_NONBLOCK)
            print("FIFO abierto exitosamente. Leyendo datos...")
            
            with os.fdopen(fifo_fd, "r") as fifo:
                while True:
                    linea = fifo.readline().strip()
                    if linea:
                        print(f"Lector: Recibido '{linea}'")
                    else:
                        time.sleep(0.5)  # Esperar si no hay datos nuevos
            break
        except OSError as e:
            if e.errno == errno.ENXIO:  # No hay escritores en el FIFO
                print("No hay escritores en el FIFO. Reintentando...")
                time.sleep(1)
            else:
                raise
    else:
        print("No se pudo abrir el FIFO después de varios intentos. Saliendo.")

if __name__ == "__main__":
    lector()
```

**escritor_fifo.py**:
```python
import os
import time

FIFO_PATH = "/tmp/fifo_condicional"

def escritor():
    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)

    print("Escribiendo datos al FIFO...")
    with open(FIFO_PATH, "w") as fifo:
        for i in range(5):
            mensaje = f"Mensaje {i + 1}"
            fifo.write(mensaje + "\n")
            fifo.flush()  # Asegura que los datos se envíen inmediatamente
            print(f"Escritor: Enviado '{mensaje}'")
            time.sleep(1)
    print("Escritura finalizada.")

if __name__ == "__main__":
    escritor()
```

### Ejercicio 6 — Chat asincrónico con doble FIFO
**Objetivo**: Crear una estructura de comunicación bidireccional entre dos usuarios.
**usuario_a.py**:
```python
import os
import time
from datetime import datetime

FIFO_WRITE = "/tmp/chat_a"
FIFO_READ = "/tmp/chat_b"

def crear_fifo(path):
    if not os.path.exists(path):
        os.mkfifo(path)

def usuario_a():
    crear_fifo(FIFO_WRITE)
    crear_fifo(FIFO_READ)

    print("Chat iniciado. Escribe '/exit' para salir.")
    try:
        with open(FIFO_WRITE, "w") as fifo_write, open(FIFO_READ, "r") as fifo_read:
            while True:
                # Leer mensajes del otro usuario
                if os.path.exists(FIFO_READ):
                    mensaje_recibido = fifo_read.readline().strip()
                    if mensaje_recibido:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Usuario B: {mensaje_recibido}")

                # Enviar mensajes
                mensaje = input("> ")
                if mensaje.strip().lower() == "/exit":
                    print("Saliendo del chat...")
                    break
                fifo_write.write(mensaje + "\n")
                fifo_write.flush()
    except KeyboardInterrupt:
        print("\nChat terminado.")

if __name__ == "__main__":
    usuario_a()
```

**usuario_b.py**:
```python
import os
import time
from datetime import datetime

FIFO_WRITE = "/tmp/chat_b"
FIFO_READ = "/tmp/chat_a"

def crear_fifo(path):
    if not os.path.exists(path):
        os.mkfifo(path)

def usuario_b():
    crear_fifo(FIFO_WRITE)
    crear_fifo(FIFO_READ)

    print("Chat iniciado. Escribe '/exit' para salir.")
    try:
        with open(FIFO_WRITE, "w") as fifo_write, open(FIFO_READ, "r") as fifo_read:
            while True:
                # Leer mensajes del otro usuario
                if os.path.exists(FIFO_READ):
                    mensaje_recibido = fifo_read.readline().strip()
                    if mensaje_recibido:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Usuario A: {mensaje_recibido}")

                # Enviar mensajes
                mensaje = input("> ")
                if mensaje.strip().lower() == "/exit":
                    print("Saliendo del chat...")
                    break
                fifo_write.write(mensaje + "\n")
                fifo_write.flush()
    except KeyboardInterrupt:
        print("\nChat terminado.")

if __name__ == "__main__":
    usuario_b()
```

### Ejercicio 7 — Monitor de temperatura simulado
**Objetivo**: Simular un sensor que envía datos por FIFO y un visualizador que los muestra.
**simulador.py**:
```python
import os
import time
import random

FIFO_PATH = "/tmp/temperatura_fifo"

def crear_fifo(path):
    if not os.path.exists(path):
        os.mkfifo(path)

def simulador():
    crear_fifo(FIFO_PATH)
    print("Simulador de temperatura iniciado. Enviando datos al FIFO...")
    try:
        with open(FIFO_PATH, "w") as fifo:
            while True:
                temperatura = round(random.uniform(20, 30), 2)
                fifo.write(f"{temperatura}\n")
                fifo.flush()  # Asegura que los datos se envíen inmediatamente
                print(f"Simulador: Enviada temperatura {temperatura}°C")
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nSimulador detenido.")

if __name__ == "__main__":
    simulador()
```

**monitor.py**:
```python
import os
import time
from datetime import datetime

FIFO_PATH = "/tmp/temperatura_fifo"
LOG_FILE = "temperatura_log.txt"

def crear_fifo(path):
    if not os.path.exists(path):
        os.mkfifo(path)

def monitor():
    crear_fifo(FIFO_PATH)
    print("Monitor de temperatura iniciado. Leyendo datos del FIFO...")
    try:
        with open(FIFO_PATH, "r") as fifo, open(LOG_FILE, "a") as log:
            while True:
                linea = fifo.readline().strip()
                if linea:
                    temperatura = float(linea)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"[{timestamp}] Temperatura: {temperatura}°C\n"
                    log.write(log_entry)
                    log.flush()  # Asegura que los datos se guarden inmediatamente
                    print(f"Monitor: {log_entry.strip()}")
                    if temperatura > 28:
                        print(f"ALERTA: Temperatura alta detectada ({temperatura}°C)")
    except KeyboardInterrupt:
        print("\nMonitor detenido.")

if __name__ == "__main__":
    monitor()
```

### Reflexionar no solo sobre el funcionamiento técnico, sino sobre cómo estas estructuras permiten modelar arquitecturas de software robustas, modulares y concurrentes.
Las estructuras como los FIFOs permiten modelar arquitecturas de software robustas, modulares y concurrentes debido a:
1. Modularidad
Cada componente tiene una responsabilidad clara: producir, consumir o procesar datos.
Ejemplo: En el Ejercicio 7, el simulador genera datos y el monitor los procesa, facilitando el mantenimiento.
2. Comunicación eficiente
Los FIFOs permiten comunicación directa entre procesos sin necesidad de archivos temporales o bases de datos.
Ejemplo: En el Ejercicio 6, los usuarios se comunican bidireccionalmente en tiempo real.
3. Escalabilidad
Es fácil agregar más productores o consumidores sin modificar la arquitectura.
Ejemplo: En el Ejercicio 4, múltiples productores escriben en un mismo FIFO sin conflictos.
4. Robustez
El manejo de errores asegura que los procesos no fallen abruptamente.
Ejemplo: En el Ejercicio 5, el lector reintenta abrir el FIFO si no hay escritores.
5. Concurrencia
Los FIFOs permiten que los procesos trabajen en paralelo, mejorando la eficiencia.
Ejemplo: En el Ejercicio 2, el productor y el consumidor operan simultáneamente.
6. Extensibilidad
Estas arquitecturas son fácilmente ampliables.
Ejemplo: En el Ejercicio 7, se podría agregar un sistema de notificaciones para alertas críticas.
7. Inspiración para sistemas distribuidos
Aunque los FIFOs son locales, el diseño puede extenderse a sistemas distribuidos usando sockets o colas de mensajes.
Conclusión
Estas estructuras no solo resuelven problemas técnicos, sino que fomentan buenas prácticas de diseño como la modularidad, la separación de responsabilidades y la escalabilidad, esenciales para sistemas concurrentes y robustos.