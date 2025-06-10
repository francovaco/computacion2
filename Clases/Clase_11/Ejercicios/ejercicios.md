## Ejercicio 1
```python
import argparse
import os
import time
import random
import subprocess
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Crea procesos hijos y muestra la jerarquía.")
    parser.add_argument("--num", type=int, required=True, help="Cantidad de procesos hijos a crear.")
    parser.add_argument("--verbose", action="store_true", help="Activa salida detallada.")
    return parser.parse_args()

def main():
    args = parse_args()
    hijos = []

    if args.verbose:
        print(f"[PADRE] PID: {os.getpid()} - Creando {args.num} procesos hijos...")

    for i in range(args.num):
        pid = os.fork()
        if pid == 0:
            # Código del hijo
            duracion = random.randint(1, 5)
            if args.verbose:
                print(f"[HIJO {os.getpid()}] Dormiré por {duracion} segundos (padre: {os.getppid()})")
            time.sleep(duracion)
            if args.verbose:
                print(f"[HIJO {os.getpid()}] Terminado.")
            os._exit(0)  # Importante para evitar que el hijo siga ejecutando el resto del código
        else:
            hijos.append(pid)

    # Código del padre
    if args.verbose:
        print(f"[PADRE] Esperando que los hijos terminen...")

    for pid in hijos:
        os.waitpid(pid, 0)

    if args.verbose:
        print("[PADRE] Todos los hijos han terminado.")

    # Mostrar jerarquía de procesos
    print("\nJerarquía de procesos con pstree:")
    subprocess.run(["pstree", "-p", str(os.getpid())])

if __name__ == "__main__":
    main()
```
Desde la terminal:
```bash
python3 gestor.py --num 3 --verbose
```
Esto creará 3 procesos hijos con salida detallada. Podés observar los procesos con ps, htop, o inspeccionando /proc.

## Ejercicio 2
```python
import os
import time

def main():
    print(f"[PADRE] PID: {os.getpid()} - Creando hijo...")

    pid = os.fork()

    if pid == 0:
        # Código del hijo
        print(f"[HIJO] PID: {os.getpid()} - Terminando inmediatamente.")
        os._exit(0)  # Finaliza sin limpiar
    else:
        print(f"[PADRE] Esperando 10 segundos antes de recolectar al hijo (PID: {pid})...")
        time.sleep(10)  # Tiempo durante el cual el hijo será un zombi

        # Aquí el padre recoge al hijo
        os.waitpid(pid, 0)
        print(f"[PADRE] Proceso hijo recolectado.")

if __name__ == "__main__":
    main()
```
Mientras el padre espera los 10 segundos:
```bash
ps -o pid,ppid,state,cmd | grep zombi.py
cat /proc/[PID_DEL_HIJO]/status | grep State
```
Debes ver que el estado del hijo es Z (zombie) y que su PPID corresponde al del proceso padre.

## Ejercicio 3
```python
import os
import time

def main():
    pid = os.fork()

    if pid == 0:
        # Código del hijo
        print(f"[HIJO] PID: {os.getpid()}, PPID: {os.getppid()} - Esperando 10 segundos...")
        time.sleep(10)
        print(f"[HIJO] Luego de 10s, mi nuevo PPID es: {os.getppid()}")
    else:
        # Código del padre
        print(f"[PADRE] PID: {os.getpid()} - Terminando inmediatamente. El hijo quedará huérfano.")
        os._exit(0)

if __name__ == "__main__":
    main()
```
Mientras el hijo está en ejecución (durante los 10 segundos):
```bash
ps -o pid,ppid,state,cmd | grep huerfano.py
cat /proc/[PID_DEL_HIJO]/status | grep PPid
```
El valor de PPid debe ser 1, indicando que ha sido adoptado por init/systemd.

## Ejercicio 4
```python
import os
import time

def main():
    pid = os.fork()

    if pid == 0:
        # Código del hijo
        print(f"[HIJO] PID: {os.getpid()} ejecutará 'ls -l' usando exec().")
        os.execlp("ls", "ls", "-l")
        # Si exec() falla
        print("[HIJO] Error: exec() falló.")
        os._exit(1)
    else:
        # Código del padre
        print(f"[PADRE] PID: {os.getpid()} - Esperando que el hijo termine.")
        os.waitpid(pid, 0)
        print("[PADRE] El hijo terminó.")

if __name__ == "__main__":
    main()
```
Durante la ejecución del hijo:
```bash
ps -o pid,ppid,cmd | grep ls
```
Deberías ver que el nombre del proceso ya no es reemplazo_exec.py, sino ls.

## Ejercicio 5
```python
import os

def main():
    # Crear el pipe (retorna una tupla de file descriptors: (lectura, escritura))
    r, w = os.pipe()

    pid = os.fork()

    if pid == 0:
        # Código del hijo: escribe en el pipe
        os.close(r)  # Cierra el extremo de lectura
        mensaje = b"Hola desde el hijo!\n"
        os.write(w, mensaje)
        os.close(w)  # Cierra el extremo de escritura después de escribir
        os._exit(0)
    else:
        # Código del padre: lee del pipe
        os.close(w)  # Cierra el extremo de escritura
        recibido = os.read(r, 1024)
        os.close(r)
        print(f"[PADRE] Mensaje recibido del hijo: {recibido.decode()}")
        os.waitpid(pid, 0)

if __name__ == "__main__":
    main()
```

## Ejercicio 6
Desde la terminal:
```bash
mkfifo /tmp/mi_fifo
```
### Emisor
```python
import os

fifo_path = "/tmp/mi_fifo"

with open(fifo_path, "w") as fifo:
    print("[EMISOR] FIFO abierto para escritura.")
    while True:
        msg = input("Mensaje para enviar (Ctrl+C para salir): ")
        fifo.write(msg + "\n")
        fifo.flush()
```
### Receptor
```python
import os

fifo_path = "/tmp/mi_fifo"

with open(fifo_path, "r") as fifo:
    print("[RECEPTOR] FIFO abierto para lectura.")
    for line in fifo:
        print(f"[RECEPTOR] Mensaje recibido: {line.strip()}")
```

En una terminal:
```bash
python3 receptor.py
```
En otra terminal:
```bash
python3 emisor.py
```
Escribimos mensajes en emisor.py y vemos cómo aparecen en receptor.py