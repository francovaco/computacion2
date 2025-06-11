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

## Ejercicio 7
```python
import multiprocessing
import os
import time
from datetime import datetime

LOG_FILE = "log_procesos.txt"

def escribir_log(lock, identificador):
    for _ in range(3):
        with lock:
            with open(LOG_FILE, "a") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] Proceso {identificador} (PID: {os.getpid()}) escribiendo al log.\n")
                print(f"[{timestamp}] Proceso {identificador} escribió en el log.")
        time.sleep(1)

def main():
    lock = multiprocessing.Lock()
    procesos = []

    for i in range(4):
        p = multiprocessing.Process(target=escribir_log, args=(lock, f"P{i+1}"))
        procesos.append(p)
        p.start()

    for p in procesos:
        p.join()

    print("Todos los procesos han terminado. Revisa el archivo log_procesos.txt.")

if __name__ == "__main__":
    main()
```

## Ejercicio 8
Sin sincronización (con condición de carrera)
```python
import multiprocessing

def incrementar_sin_lock(contador):
    for _ in range(100_000):
        contador.value += 1  # No es atómico

if __name__ == "__main__":
    contador = multiprocessing.Value('i', 0)  # 'i' = entero con signo
    p1 = multiprocessing.Process(target=incrementar_sin_lock, args=(contador,))
    p2 = multiprocessing.Process(target=incrementar_sin_lock, args=(contador,))

    p1.start()
    p2.start()
    p1.join()
    p2.join()

    print(f"Valor final sin Lock: {contador.value} (esperado: 200000)")
```
Resultado esperado:
Probablemente menor a 200000.
Variará entre ejecuciones debido a la condición de carrera.

Con sincronización (sin condición de carrera)
```python
import multiprocessing

def incrementar_con_lock(contador, lock):
    for _ in range(100_000):
        with lock:
            contador.value += 1

if __name__ == "__main__":
    contador = multiprocessing.Value('i', 0)
    lock = multiprocessing.Lock()
    p1 = multiprocessing.Process(target=incrementar_con_lock, args=(contador, lock))
    p2 = multiprocessing.Process(target=incrementar_con_lock, args=(contador, lock))

    p1.start()
    p2.start()
    p1.join()
    p2.join()

    print(f"Valor final con Lock: {contador.value} (esperado: 200000)")
```
Resultado esperado:
Siempre exactamente 200000.
El Lock garantiza que no se pierdan actualizaciones.

## Ejercicio 9
```python
import multiprocessing
import time
import os
import random

def zona_critica(sem: multiprocessing.Semaphore, identificador: str):
    print(f"[{identificador}] PID {os.getpid()} intentando entrar a la zona crítica.")
    with sem:
        print(f"[{identificador}] ✨ Entró a la zona crítica.")
        time.sleep(random.uniform(1, 3))  # Simula trabajo en zona crítica
        print(f"[{identificador}] Saliendo de la zona crítica.")

if __name__ == "__main__":
    sem = multiprocessing.Semaphore(3)  # Solo 3 procesos a la vez
    procesos = []

    for i in range(10):
        p = multiprocessing.Process(target=zona_critica, args=(sem, f"P{i+1}"))
        procesos.append(p)
        p.start()

    for p in procesos:
        p.join()

    print("Todos los procesos han terminado.")
```

## Ejercicio 10
```python
import multiprocessing
import time
import random

class CuentaBancaria:
    def __init__(self, saldo_inicial, lock):
        self.saldo = multiprocessing.Value('i', saldo_inicial)
        self.lock = lock

    def depositar(self, monto):
        with self.lock:
            self._modificar_saldo(monto)

    def retirar(self, monto):
        with self.lock:
            self._modificar_saldo(-monto)

    def _modificar_saldo(self, monto):
        with self.lock:
            saldo_anterior = self.saldo.value
            time.sleep(random.uniform(0.1, 0.3))  # Simula latencia
            self.saldo.value = saldo_anterior + monto
            print(f"[{multiprocessing.current_process().name}] Nuevo saldo: {self.saldo.value}")

def tarea(cuenta: CuentaBancaria):
    for _ in range(3):
        if random.choice([True, False]):
            cuenta.depositar(50)
        else:
            cuenta.retirar(30)
        time.sleep(random.uniform(0.2, 0.5))

if __name__ == "__main__":
    rlock = multiprocessing.RLock()
    cuenta = CuentaBancaria(saldo_inicial=100, lock=rlock)

    procesos = []
    for i in range(4):
        p = multiprocessing.Process(target=tarea, args=(cuenta,), name=f"Cliente-{i+1}")
        procesos.append(p)
        p.start()

    for p in procesos:
        p.join()

    print(f"Saldo final: {cuenta.saldo.value}")
```

## Ejercicio 11
```python
import os
import signal
import time

def handler(sig, frame):
    print(f"\n Señal recibida: {signal.Signals(sig).name} (PID: {os.getpid()})")

if __name__ == "__main__":
    print(f"[PROCESO] PID: {os.getpid()}")
    print("[PROCESO] Esperando señal SIGUSR1...")

    signal.signal(signal.SIGUSR1, handler)

    # Espera pasiva usando bucle infinito (alternativamente, usar signal.pause())
    while True:
        time.sleep(1)
```
Ejecutar en una terminal:
```bash
python3 manejador_senal.py
```
Desde otra terminal:
```bash
kill -SIGUSR1 [pid]
```
El proceso debería imprimir un mensaje como este:
```bash
Señal recibida: SIGUSR1 (PID: 12345)
```

## Ejercicio 12
### Generafor.py
```python
import argparse
import random

def main():
    parser = argparse.ArgumentParser(description="Generador de números aleatorios")
    parser.add_argument("--n", type=int, required=True, help="Cantidad de números a generar")
    args = parser.parse_args()

    for _ in range(args.n):
        print(random.randint(0, 100))  # Rango fijo: 0 a 100

if __name__ == "__main__":
    main()
```

### Filtro.py
```python
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Filtro de números mayores que un umbral")
    parser.add_argument("--min", type=int, required=True, help="Valor mínimo para filtrar")
    args = parser.parse_args()

    for line in sys.stdin:
        try:
            num = int(line.strip())
            if num > args.min:
                print(num)
        except ValueError:
            continue  # Ignora líneas no numéricas

if __name__ == "__main__":
    main()
```
Desde una terminal:
```bash
python3 generador.py --n 100 | python3 filtro.py --min 50
```
Esto imprimirá únicamente los números mayores a 50 generados aleatoriamente.

## Ejercicio 13
```python
import os
import time

def crear_hijo(nombre):
    pid = os.fork()
    if pid == 0:
        print(f"[HIJO {nombre}] PID: {os.getpid()}, PPID: {os.getppid()}")
        time.sleep(5)
        os._exit(0)

if __name__ == "__main__":
    print(f"[PADRE] PID: {os.getpid()}")
    crear_hijo("A")
    crear_hijo("B")
    os.wait()
    os.wait()
    print("[PADRE] Ambos hijos han terminado.")
```
En una terminal:
```bash
python3 jerarquia_procesos.py
```
En otra terminal:
```bash
pstree -p | grep -A 5 [PID_DEL_PADRE]
```
Ejemplo de la salida esperada:
1234 python3 jerarquia_procesos.py
 ├─1235 [HIJO A]
 └─1236 [HIJO B]

## Ejercicio 14
### Dormir.py
```python
import time
import os
import signal
import sys

def handler(sig, frame):
    print(f"\n🛑 Señal {sig} recibida. Terminando proceso {os.getpid()}...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handler)

print(f"[PYTHON] PID: {os.getpid()} - Durmiendo por 10 segundos...")
time.sleep(10)
print("[PYTHON] Finalizado normalmente.")
```

### Lanzador.sh
```bash
echo "[BASH] Ejecutando dormir.py en segundo plano..."
python3 dormir.py &
PID=$!
echo "[BASH] PID del proceso Python: $PID"
echo "[BASH] Use 'ps' o 'kill -SIGTERM $PID' desde otra terminal para interactuar."
wait $PID
echo "[BASH] El proceso ha finalizado."
```
En una terminal:
```bash
bash lanzador.sh
```
En otra terminal verificamos el proceso:
```bash
ps -p [PID]
```
Terminar el proceso manualmente:
```bash
kill -SIGTERM [PID]
```
Observamos que el script Python captura la señal y finaliza limpiamente.

## Ejercicio 15
```bash
echo "PID  PPID  NOMBRE              ESTADO"
echo "----------------------------------------"

declare -A estados

for pid in /proc/[0-9]*; do
    if [ -f "$pid/status" ]; then
        PID=$(basename "$pid")
        PPID=$(grep "^PPid:" "$pid/status" | awk '{print $2}')
        NAME=$(grep "^Name:" "$pid/status" | awk '{print $2}')
        STATE=$(grep "^State:" "$pid/status" | awk '{print $2}')
        
        printf "%-5s %-5s %-18s %-2s\n" "$PID" "$PPID" "$NAME" "$STATE"

        # Contar estado
        ((estados[$STATE]++))
    fi
done

echo ""
echo "Resumen de estados de procesos:"
for estado in "${!estados[@]}"; do
    echo "Estado $estado: ${estados[$estado]} proceso(s)"
done
```
Damos permisos de ejecución:
```bash
chmod +x analisis_procesos.sh
```
Lo ejecutamos:
```bash
./analisis_procesos.sh
```
Ejemplo de salida esperada:
PID   PPID  NOMBRE              ESTADO
----------------------------------------
1     0     systemd             S
321   1     bash                S
456   321   python3             R
789   1     kthreadd            S
...

Resumen de estados de procesos:
Estado S: 132 proceso(s)
Estado R: 4 proceso(s)
Estado Z: 1 proceso(s)

Estados comunes:
| Código | Significado               |
| ------ | ------------------------- |
| R      | Ejecutando                |
| S      | En espera (interrumpible) |
| D      | Espera ininterrumpible    |
| Z      | Zombi                     |
| T      | Detenido (trazado)        |
| X      | Muerto (terminado)        |

## Ejercicio 16
```python
import os
import time
import random

def hijo(tiempo, nombre):
    print(f"[{nombre}] PID: {os.getpid()} - Dormiré {tiempo}s")
    time.sleep(tiempo)
    print(f"[{nombre}] Finalizando.")
    os._exit(0)

if __name__ == "__main__":
    hijos = {}
    orden_terminacion = []

    for i in range(3):
        duracion = random.randint(1, 5)
        pid = os.fork()
        if pid == 0:
            hijo(duracion, f"Hijo-{i+1}")
        else:
            hijos[pid] = f"Hijo-{i+1}"

    while hijos:
        pid_terminado, _ = os.waitpid(-1, 0)
        nombre = hijos.pop(pid_terminado)
        orden_terminacion.append(nombre)
        print(f"[PADRE] Recolectado {nombre} (PID: {pid_terminado})")

    print("\n Orden de terminación de los hijos:")
    for i, nombre in enumerate(orden_terminacion, 1):
        print(f"{i}. {nombre}")
```
Ejemplo de salida esperada:
[Hijo-1] PID: 1234 - Dormiré 3s
[Hijo-2] PID: 1235 - Dormiré 1s
[Hijo-3] PID: 1236 - Dormiré 5s
[PADRE] Recolectado Hijo-2 (PID: 1235)
[PADRE] Recolectado Hijo-1 (PID: 1234)
[PADRE] Recolectado Hijo-3 (PID: 1236)

Orden de terminación de los hijos:
1. Hijo-2
2. Hijo-1
3. Hijo-3

## Ejercicio 17
Crear FIFO
```bash
mkfifo /tmp/fifo_lector_escritor
```
### Escritor.sh
```bash
FIFO="/tmp/fifo_lector_escritor"
echo "[ESCRITOR] Escribiendo en FIFO cada segundo..."

i=1
while true; do
    echo "Mensaje $i desde escritor" > "$FIFO"
    echo "[ESCRITOR] Enviado: Mensaje $i"
    ((i++))
    sleep 1
done
```

### Lector.sh
```bash
FIFO="/tmp/fifo_lector_escritor"
echo "[LECTOR] Esperando mensajes en FIFO..."

while true; do
    if read linea < "$FIFO"; then
        echo "[LECTOR] Recibido: $linea"
    fi
done
```
En la terminal:
```bash
bash lector.sh
```
En otrs terminal:
```bash
bash escritor.sh
```
Comportamiento esperado:
| Orden                | Resultado                                                              |
| -------------------- | ---------------------------------------------------------------------- |
| **Lector primero**   | Se bloquea esperando que el escritor escriba.                          |
| **Escritor primero** | Se bloquea esperando que alguien lea (hasta que el lector se conecte). |

## Ejercicio 18
```python
import os
import time

def main():
    r, w = os.pipe()
    pid = os.fork()

    if pid == 0:
        # Hijo: cierra extremo de escritura y lee
        os.close(w)
        print(f"[HIJO] PID: {os.getpid()} - leyendo del pipe...")
        time.sleep(5)
        os._exit(0)
    else:
        # Padre: cierra extremo de lectura y escribe
        os.close(r)
        print(f"[PADRE] PID: {os.getpid()} - escribiendo en el pipe...")
        os.write(w, b"mensaje desde el padre\n")
        time.sleep(5)
        os.wait()
        print("[PADRE] Hijo finalizado.")

if __name__ == "__main__":
    main()
```
En una terminal:
```bash
python3 pipe_lsof.py
```
Mientras se ejecuta, desde otra terminal identificar el PID del proceso padre o hijo (por ejemplo con ps).
Observar los descriptores abiertos:
```bash
lsof -p [PID]
```
Ejemplo de salida esperada:
Buscar líneas con tipo PIPE.
El FD (File Descriptor) puede ser r, w, 3u, 4u, etc.
Ejemplo:
python3  12345  usuario  3w  FIFO  ...  pipe:[123456]
Esto indica que el proceso tiene un pipe anónimo abierto.

## Ejercicio 19
### escribir_sin_lock.py
```python
import os
import time
from multiprocessing import Process

LOG_FILE = "log_sin_lock.txt"

def escribir(proceso_id):
    for i in range(5):
        with open(LOG_FILE, "a") as f:
            f.write(f"[{proceso_id}] Línea {i}\n")
        time.sleep(0.1)

if __name__ == "__main__":
    procesos = []
    for i in range(4):
        p = Process(target=escribir, args=(f"P{i+1}",))
        procesos.append(p)
        p.start()

    for p in procesos:
        p.join()
```
El archivo log_sin_lock.txt puede mostrar líneas mezcladas o incompletas debido a la escritura simultánea sin exclusión mutua.

### escribir_con_lock.py
```python
import os
import time
from multiprocessing import Process, Lock

LOG_FILE = "log_con_lock.txt"

def escribir(proceso_id, lock):
    for i in range(5):
        with lock:
            with open(LOG_FILE, "a") as f:
                f.write(f"[{proceso_id}] Línea {i}\n")
        time.sleep(0.1)

if __name__ == "__main__":
    lock = Lock()
    procesos = []
    for i in range(4):
        p = Process(target=escribir, args=(f"P{i+1}", lock))
        procesos.append(p)
        p.start()

    for p in procesos:
        p.join()
```
El archivo log_con_lock.txt muestra un log ordenado y coherente, sin líneas partidas o solapadas.
Comparación:
| Versión    | Salida        | Riesgo |
| ---------- | ------------- | ------ |
| Sin Lock   | Inconsistente | Alta   |
| Con `Lock` | Consistente   | Baja   |

## Ejercicio 20
### Receptor.py
```python
import signal
import os
import time

def handler_usr1(signum, frame):
    print(f"[RECEPTOR] Recibí SIGUSR1 (PID: {os.getpid()}) - 🟡 ¡Acción A!")

def handler_usr2(signum, frame):
    print(f"[RECEPTOR] Recibí SIGUSR2 (PID: {os.getpid()}) - 🔵 ¡Acción B!")

if __name__ == "__main__":
    print(f"[RECEPTOR] Esperando señales... PID: {os.getpid()}")

    signal.signal(signal.SIGUSR1, handler_usr1)
    signal.signal(signal.SIGUSR2, handler_usr2)

    # Espera pasiva infinita
    while True:
        signal.pause()
```

### Emisor.py
```python
import os
import time
import signal
import argparse

def main():
    parser = argparse.ArgumentParser(description="Envía señales a otro proceso.")
    parser.add_argument("pid", type=int, help="PID del proceso receptor")
    args = parser.parse_args()

    for i in range(5):
        sig = signal.SIGUSR1 if i % 2 == 0 else signal.SIGUSR2
        os.kill(args.pid, sig)
        print(f"[EMISOR] Enviada {signal.Signals(sig).name} al PID {args.pid}")
        time.sleep(2)

if __name__ == "__main__":
    main()
```
En una terminal ejecutar el receptor:
```bash
python3 receptor.py
```
En otra terminal y con el PID de receptor ejecutamos:
```bash
python3 emisor.py [PID_DEL_RECEPTOR]
```
Salida esperada:
El receptor imprime mensajes diferentes según si recibe SIGUSR1 o SIGUSR2.
El emisor alterna entre ambas señales cada 2 segundos.