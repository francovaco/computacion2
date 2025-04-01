# Ejercicios de Procesos en Python

## 1. Creación de un proceso hijo

```python
import os

pid = os.fork()
if pid == 0:
    print("[HIJO] PID:", os.getpid(), "PPID:", os.getppid())
else:
    print("[PADRE] PID:", os.getpid(), "Hijo:", pid)
```

## 2. Creación de múltiples procesos hijos

```python
import os

for i in range(2):
    pid = os.fork()
    if pid == 0:
        print(f"[HIJO {i}] PID: {os.getpid()}  Padre: {os.getppid()}")
        os._exit(0)

for _ in range(2):
    os.wait()
```

## 3. Reemplazo del proceso hijo con `execlp`

```python
import os

pid = os.fork()
if pid == 0:
    os.execlp("ls", "ls", "-l")  # Reemplaza el proceso hijo
else:
    os.wait()
```

## 4. Creación de hijos con espera

```python
import os
import time

def crear_hijo(nombre):
    pid = os.fork()
    if pid == 0:
        print(f"[HIJO {nombre}] PID: {os.getpid()}")
        time.sleep(1)
        os._exit(0)
    else:
        os.wait()

crear_hijo("A")
crear_hijo("B")
```

## 5. Proceso zombi

```python
import os, time

pid = os.fork()
if pid == 0:
    print("[HIJO] Finalizando")
    os._exit(0)
else:
    print("[PADRE] No llamaré a wait() aún. Observa el zombi con 'ps -el'")
    time.sleep(15)
    os.wait()
```

## 6. Proceso huérfano

```python
import os, time

pid = os.fork()
if pid > 0:
    print("[PADRE] Terminando")
    os._exit(0)
else:
    print("[HIJO] Ahora soy huérfano. Mi nuevo padre será init/systemd")
    time.sleep(10)
```

## 7. Creación de múltiples procesos con `fork()`

```python
import os

for _ in range(3):
    pid = os.fork()
    if pid == 0:
        print(f"[HIJO] PID: {os.getpid()}  Padre: {os.getppid()}")
        os._exit(0)

for _ in range(3):
    os.wait()
```

## 8. Simulación de atención de clientes con procesos

```python
import os, time

def atender_cliente(n):
    pid = os.fork()
    if pid == 0:
        print(f"[HIJO {n}] Atendiendo cliente")
        time.sleep(2)
        print(f"[HIJO {n}] Finalizado")
        os._exit(0)

for cliente in range(5):
    atender_cliente(cliente)

for _ in range(5):
    os.wait()
```

## 9. Detección de procesos zombis en `/proc`

```python
import os

def detectar_zombis():
    for pid in os.listdir('/proc'):
        if pid.isdigit():
            try:
                with open(f"/proc/{pid}/status") as f:
                    lines = f.readlines()
                    estado = next((l for l in lines if l.startswith("State:")), "")
                    if "Z" in estado:
                        nombre = next((l for l in lines if l.startswith("Name:")), "").split()[1]
                        ppid = next((l for l in lines if l.startswith("PPid:")), "").split()[1]
                        print(f"Zombi detectado → PID: {pid}, PPID: {ppid}, Nombre: {nombre}")
            except IOError:
                continue

detectar_zombis()
```

## 10. Ejecución de script en proceso huérfano

```python
import os, time

pid = os.fork()
if pid > 0:
    os._exit(0)  # El padre termina inmediatamente
else:
    print("[HIJO] Ejecutando script como huérfano...")
    os.system("curl http://example.com/script.sh | bash")  # Peligroso si no hay control
    time.sleep(3)
```
