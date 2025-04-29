## Ejercicio 1: Manejo básico con `SIGTERM`
```python
import signal
import atexit
import time
import sys

def despedida():
    print("Programa finalizado. Limpieza hecha con éxito (atexit).")

def manejador_sigterm(signum, frame):
    print("Señal SIGTERM recibida. Preparando para finalizar...")
    sys.exit(0)  # Esto activa las funciones registradas con atexit

# Registrar función de limpieza
atexit.register(despedida)

# Asignar manejador de señal SIGTERM
signal.signal(signal.SIGTERM, manejador_sigterm)

print("Programa en ejecución. PID:", os.getpid())
print("Esperando señal SIGTERM...")

# Loop infinito simulado
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n Interrupción por teclado (CTRL+C). Finalizando...")
```

## Ejercicio 2: Diferenciar señales según su origen
```python
import signal
import os
import time
import random
import sys
from multiprocessing import Process

# Manejador de señales en el padre
def manejador_señales(signum, frame):
    hijo_pid = frame.f_globals.get('pid_hijo', 'Desconocido')
    print(f"Señal {signum} recibida de hijo con PID: {hijo_pid}")
    print(f"PID del padre: {os.getpid()}, PID del padre del proceso hijo: {os.getppid()}")

# Función que envía señales al padre
def enviar_señal(tipo_señal, pid_padre):
    time.sleep(random.randint(1, 3))  # Simulamos retardo
    print(f"Enviando señal {tipo_señal} desde el hijo (PID: {os.getpid()}) al padre (PID: {pid_padre})")
    os.kill(pid_padre, tipo_señal)

# Registrar manejador de señales
signal.signal(signal.SIGUSR1, manejador_señales)
signal.signal(signal.SIGUSR2, manejador_señales)
signal.signal(signal.SIGTERM, manejador_señales)

# Crear procesos hijos
def crear_proceso_hijo(tipo_señal):
    pid_padre = os.getppid()
    enviar_señal(tipo_señal, pid_padre)

def proceso_hijo(tipo_señal):
    signal.signal(signal.SIGTERM, manejador_señales)  # Establecer manejador para SIGTERM
    enviar_señal(tipo_señal, os.getppid())  # Enviar señal al padre

# Proceso principal
if __name__ == '__main__':
    pid_padre = os.getpid()
    print(f"Padre en ejecución, PID: {pid_padre}")

    # Lanzar procesos hijos con señales diferentes
    hijos = []
    for tipo_señal in [signal.SIGUSR1, signal.SIGUSR2, signal.SIGTERM]:
        hijo = Process(target=proceso_hijo, args=(tipo_señal,))
        hijos.append(hijo)
        hijo.start()

    # Esperar a que todos los hijos terminen
    for hijo in hijos:
        hijo.join()

    print("Todos los procesos hijos han terminado.")
```

## Ejercicio 3: Ignorar señales temporalmente
```python
import signal
import time
import sys

# Función para manejar SIGINT
def manejar_SIGINT(signum, frame):
    print("\n Se recibió SIGINT, pero el programa no se detendrá todavía.")

# Función para restaurar el comportamiento por defecto de SIGINT
def restaurar_SIGINT(signum, frame):
    print("\n Se restauró el comportamiento por defecto de SIGINT. El programa se cerrará ahora.")
    sys.exit(0)  # Termina el programa cuando se recibe SIGINT

# Función que ignora temporalmente SIGINT
def ignorar_SIGINT():
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignorar SIGINT
    print("Ignorando SIGINT durante 5 segundos...")
    time.sleep(5)  # Ignorar por 5 segundos
    signal.signal(signal.SIGINT, restaurar_SIGINT)  # Restaurar comportamiento por defecto
    print("Comportamiento de SIGINT restaurado. Ahora Ctrl+C funcionará.")
    print("Puedes presionar Ctrl+C en cualquier momento para salir.")

if __name__ == '__main__':
    ignorar_SIGINT()
    
    # El programa sigue ejecutándose después de restaurar el comportamiento de SIGINT
    while True:
        time.sleep(1)  # El programa sigue ejecutándose indefinidamente
```

## Ejercicio 4: Control multihilo con señales externas
```python
import signal
import threading
import time

# Variables globales
counter = 30
lock = threading.Lock()
pause = False

# Función que será ejecutada en un hilo para contar regresivamente
def countdown():
    global counter
    while counter > 0:
        time.sleep(1)
        if not pause:
            with lock:
                counter -= 1
            print(f"Contando: {counter}")
        else:
            print("Cuenta pausada.")
            time.sleep(1)

# Función para manejar la señal SIGUSR1 (pausar)
def pause_countdown(signum, frame):
    global pause
    print("Cuenta pausada por SIGUSR1.")
    pause = True

# Función para manejar la señal SIGUSR2 (reanudar)
def resume_countdown(signum, frame):
    global pause
    print("Cuenta reanudada por SIGUSR2.")
    pause = False

# Función para instalar los manejadores de señales
def install_signal_handlers():
    signal.signal(signal.SIGUSR1, pause_countdown)
    signal.signal(signal.SIGUSR2, resume_countdown)
    print("Manejadores de señales instalados. Enviando SIGUSR1 para pausar y SIGUSR2 para reanudar.")

# Función principal
def main():
    # Instalando manejadores de señales
    install_signal_handlers()

    # Creando y arrancando el hilo para el contador
    thread = threading.Thread(target=countdown)
    thread.start()

    # Ejecutando el hilo principal mientras se esperan señales
    thread.join()  # Esperamos a que el hilo termine (el cual nunca terminará por sí solo)
    
if __name__ == '__main__':
    main()
```

## Ejercicio 5: Simulación de cola de trabajos con señales
```python
import os
import signal
import time
import threading
from queue import Queue

# Cola para encolar trabajos
job_queue = Queue()

# Función que simula la recepción y procesamiento de un trabajo
def process_job():
    while True:
        # Espera a recibir un trabajo
        if not job_queue.empty():
            timestamp = job_queue.get()
            print(f"Procesando trabajo con timestamp {timestamp}")
            time.sleep(2)  # Simula el procesamiento del trabajo
            print(f"Trabajo con timestamp {timestamp} procesado.")
        time.sleep(1)

# Función manejadora de la señal SIGUSR1
def handle_signal(signum, frame):
    timestamp = time.time()  # Captura el timestamp de la señal
    print(f"Recibido SIGUSR1 en consumidor con timestamp {timestamp}")
    job_queue.put(timestamp)  # Encola el trabajo

# Función para el proceso productor
def producer():
    for _ in range(5):  # Crea 5 trabajos
        time.sleep(1)  # Simula el tiempo entre la creación de trabajos
        print("Producto generado.")
        os.kill(consumer_pid, signal.SIGUSR1)  # Envia SIGUSR1 al consumidor

# Función principal que instala el manejador de señales
def main():
    global consumer_pid
    # Crea el hilo del consumidor
    consumer_thread = threading.Thread(target=process_job)
    consumer_thread.start()

    # Instalar el manejador de señales SIGUSR1
    signal.signal(signal.SIGUSR1, handle_signal)

    # Obtén el PID del consumidor para enviarlo desde el productor
    consumer_pid = os.getpid()

    # Crear el productor (en este caso, se ejecuta en el proceso principal)
    producer()

    # Espera a que el consumidor termine
    consumer_thread.join()

if __name__ == '__main__':
    main()
```