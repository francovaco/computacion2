# Creación de Procesos en Python

## Ejercicio 1: Creación de procesos hijos con diferentes tiempos de espera

```python
import os
import time

def create_child(wait_time, message):
    pid = os.fork()
    if pid == 0:
        time.sleep(wait_time)
        print(f"{message}, mi PID es {os.getpid()}, el PID de mi padre es: {os.getppid()}")
        os.wait(0)

if __name__ == "__main__":
    create_child(0, "soy el hijo 1")
    create_child(3, "soy el hijo 2")

    #time.sleep(1)
    os.wait() #el padre espera a su hijo
    os.wait() #el padre espera a su hijo
    #os.waitpid(pid,options)
    print(f"soy el padre, mi PID es {os.getpid()}")
```

## Ejercicio 2: Creación de procesos en cascada

```python
import os
import time

def crear_cascada(nivel, max_niveles):
    if nivel < max_niveles:
        pid = os.fork()
        if pid == 0:
            print(f"[HIJO {nivel}] PID: {os.getpid()}, PPID: {os.getppid()}")
            time.sleep(1)
            crear_cascada(nivel + 1, max_niveles)
            os._exit(0)
        else:
            os.wait()
            print(f"[PADRE {nivel}] PID: {os.getpid()} - Hijo {pid} terminó")

if __name__ == "__main__":
    print(f"[INICIO] PID: {os.getpid()}")
    crear_cascada(1, 5)
```
### Otra opción

```python
import os
import time

def create_child(child_number):
    child_number += 1 
    pid = os.fork()
    
    if pid == 0:  
        print(f"Soy el hijo {child_number}, mi PID es {os.getpid()}, el PID de mi padre es: {os.getppid()}")
        if child_number < 5:
            create_child(child_number)
        os._exit(0)

if __name__ == "__main__":
    os.system('clear')
    create_child(0)
    print(f"Soy el padre, mi PID es {os.getpid()}")
```

## BOMBA FORK

### Python
```python
import os

while True:
    os.fork()
```
### Terminal
```bash
:(){ :|:& };:
```