## Ejercicio 6
```python
from multiprocessing import Process, Value, Lock
import time

# Función que simula la actualización del cronómetro
def actualizar_cronometro(cronometro, lock, id_proceso):
    while True:
        time.sleep(1)  # Actualiza cada segundo
        with lock:
            cronometro.value = time.time()  # Guardar el tiempo actual
        print(f"Proceso {id_proceso} actualizado: {cronometro.value}")

# Función que simula la lectura del cronómetro y chequeo de incoherencias
def leer_cronometro(cronometro, lock):
    last_value = cronometro.value
    while True:
        time.sleep(0.5)  # Lee cada 0.5 segundos
        with lock:
            current_value = cronometro.value  # Leer el valor actual
        print(f"Lectura actual: {current_value}")
        
        # Comprobar incoherencia temporal (más de 1 segundo de diferencia)
        if current_value - last_value > 1:
            print(f"Incoherencia detectada: salto de {current_value - last_value} segundos.")
        last_value = current_value

if __name__ == "__main__":
    lock = Lock()  # Lock para sincronización del acceso al valor compartido
    cronometro = Value('d', time.time())  # Inicializamos el valor de cronómetro con el tiempo actual

    # Crear y arrancar 3 procesos que actualizan el cronómetro
    procesos_actualizadores = [Process(target=actualizar_cronometro, args=(cronometro, lock, i)) for i in range(3)]
    for p in procesos_actualizadores:
        p.start()

    # Crear y arrancar el proceso que lee el cronómetro y verifica incoherencias
    proceso_lector = Process(target=leer_cronometro, args=(cronometro, lock))
    proceso_lector.start()

    # Esperar a que todos los procesos terminen (en este caso, no terminarán nunca debido al loop)
    for p in procesos_actualizadores:
        p.join()
    proceso_lector.join()
```

## Ejercicio 7
```python
import time
import requests
from multiprocessing import Process, Queue, Lock
import os

# Función del worker para descargar las URLs
def worker(queue, results, lock):
    while not queue.empty():
        url = queue.get()
        start_time = time.time()  # Tiempo antes de la descarga
        try:
            response = requests.get(url)  # Descargar la URL
            end_time = time.time()  # Tiempo después de la descarga
            download_time = end_time - start_time  # Duración de la descarga
            pid = os.getpid()  # Obtener el PID del proceso
            # Almacenar el resultado
            with lock:
                results.append((pid, url, download_time))
        except Exception as e:
            print(f"Error descargando {url}: {e}")

# Función del proceso maestro para repartir las URLs y generar el reporte
def master(urls, k):
    queue = Queue()  # Cola para repartir las URLs entre los workers
    results = []  # Lista para almacenar los resultados
    lock = Lock()  # Lock para sincronizar el acceso a la lista de resultados

    # Colocar las URLs en la cola
    for url in urls:
        queue.put(url)

    # Crear y lanzar los procesos worker
    workers = []
    for _ in range(k):
        worker_process = Process(target=worker, args=(queue, results, lock))
        workers.append(worker_process)
        worker_process.start()

    # Esperar a que todos los procesos worker terminen
    for wp in workers:
        wp.join()

    # Generar el reporte ordenado por tiempo de descarga
    results.sort(key=lambda x: x[2])  # Ordenar por duración (tercer elemento de la tupla)
    
    # Imprimir el reporte
    print("\nReporte de descargas:")
    for pid, url, download_time in results:
        print(f"PID: {pid} | URL: {url} | Tiempo de descarga: {download_time:.2f} segundos")

if __name__ == "__main__":
    # Lista de URLs a descargar
    urls = [
        "http://example.com",
        "http://example.org",
        "http://example.net",
        "http://example.edu",
        "http://example.co"
    ]

    # Número de workers
    k = 3

    # Ejecutar el proceso maestro
    master(urls, k)
```

## Ejercicio 8
```python
import os
import time
from multiprocessing import Process, Lock
import math

# Función para comprobar si un número es primo
def es_primo(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

# Función que calcula los primos en un rango y escribe los resultados en un archivo
def calcular_primos(rango_inicio, rango_fin, lock, archivo):
    primos_en_rango = []
    for numero in range(rango_inicio, rango_fin):
        if es_primo(numero):
            primos_en_rango.append(numero)
    
    # Escribir los resultados en el archivo de manera sincronizada
    with lock:
        with open(archivo, 'a') as f:
            for primo in primos_en_rango:
                f.write(f"{primo}\n")

# Función para ejecutar el cálculo en paralelo
def ejecutar_paralelo(N, archivo):
    lock = Lock()  # Lock para sincronizar el acceso al archivo
    procesos = []
    rango_maximo = 100000  # Limite superior del cálculo
    rango_por_proceso = rango_maximo // N

    # Crear y lanzar los procesos
    for i in range(N):
        inicio = i * rango_por_proceso
        fin = (i + 1) * rango_por_proceso if i < N - 1 else rango_maximo
        p = Process(target=calcular_primos, args=(inicio, fin, lock, archivo))
        procesos.append(p)
        p.start()

    # Esperar a que todos los procesos terminen
    for p in procesos:
        p.join()

# Función para ejecutar la versión secuencial
def ejecutar_secuencial(archivo):
    primos_en_rango = []
    rango_maximo = 100000
    for numero in range(rango_maximo):
        if es_primo(numero):
            primos_en_rango.append(numero)
    
    # Escribir los resultados en el archivo
    with open(archivo, 'w') as f:
        for primo in primos_en_rango:
            f.write(f"{primo}\n")

# Medir el tiempo de ejecución y calcular el speed-up
def medir_speedup(N, archivo):
    # Ejecutar la versión secuencial
    start_time = time.time()
    ejecutar_secuencial(archivo)
    secuencial_time = time.time() - start_time

    # Ejecutar la versión paralelizada
    start_time = time.time()
    ejecutar_paralelo(N, archivo)
    paralelo_time = time.time() - start_time

    # Calcular el speed-up
    speedup = secuencial_time / paralelo_time

    print(f"Tiempo secuencial: {secuencial_time:.2f} segundos")
    print(f"Tiempo paralelo: {paralelo_time:.2f} segundos")
    print(f"Speed-up: {speedup:.2f}")

if __name__ == "__main__":
    archivo = "primos.txt"
    N = 8  # Número de procesos paralelizados
    medir_speedup(N, archivo)
```

## Ejercicio 9
```python
import time
import random
from multiprocessing import Process, Value, Lock
from math import exp

# Parámetros del banco
balance_inicial = 10000  # Balance inicial en el banco
n_cajeros = 5  # Número de cajeros
n_transacciones = 100  # Número de transacciones por cajero

# Función para realizar transacciones (retiros y depósitos)
def realizar_transacciones(cajero_id, balance, lock, contabilidad_contencion):
    for _ in range(n_transacciones):
        # Randomizar tipo de transacción (depósito o retiro)
        transaccion_tipo = random.choice(['deposito', 'retiro'])
        monto = random.randint(1, 500)
        
        # Intentar realizar la transacción con back-off exponencial
        intento = 0
        while True:
            if lock.acquire(timeout=0.1):  # Intento de obtener el lock
                try:
                    if transaccion_tipo == 'deposito':
                        balance.value += monto
                        print(f"Cajero {cajero_id}: Depositado {monto}. Balance: {balance.value}")
                    else:
                        if balance.value >= monto:
                            balance.value -= monto
                            print(f"Cajero {cajero_id}: Retirado {monto}. Balance: {balance.value}")
                        else:
                            print(f"Cajero {cajero_id}: Fondos insuficientes para retiro.")
                finally:
                    lock.release()
                break  # Salir del bucle si se realizó la transacción con éxito
            else:
                # Incrementar el contador de contención y aplicar back-off exponencial
                intento += 1
                contabilidad_contencion.value += 1
                backoff_time = exp(intento)  # Back-off exponencial
                print(f"Cajero {cajero_id}: Reintentando transacción. Intento {intento}...")
                time.sleep(backoff_time)  # Esperar antes de reintentar

# Función para iniciar los cajeros y registrar las métricas
def simulacion_banco():
    # Balance compartido entre los cajeros
    balance = Value('d', balance_inicial)
    lock = Lock()
    contabilidad_contencion = Value('i', 0)  # Contador de intentos fallidos
    
    # Crear los procesos de los cajeros
    procesos = []
    for i in range(n_cajeros):
        p = Process(target=realizar_transacciones, args=(i, balance, lock, contabilidad_contencion))
        procesos.append(p)
        p.start()

    # Esperar a que todos los procesos terminen
    for p in procesos:
        p.join()
    
    # Reportar métricas de contención
    print(f"\nMétricas de contención: Intentos fallidos para adquirir el Lock: {contabilidad_contencion.value}")

if __name__ == "__main__":
    simulacion_banco()
```

## Ejercicio 10
```python
import time
import random
import multiprocessing
import matplotlib.pyplot as plt

# Número de enteros a transferir
N = 10**6

# Función para medir el rendimiento de Pipe
def benchmark_pipe():
    parent_conn, child_conn = multiprocessing.Pipe()
    
    def child_process():
        data = child_conn.recv()  # Recibe los datos
        child_conn.close()
        return data
    
    # Generar datos aleatorios en el proceso principal
    data = [random.randint(1, 1000) for _ in range(N)]
    
    # Medir tiempo de transferencia
    start_time = time.time()
    parent_conn.send(data)  # Envía los datos
    result = child_process()  # Recibe los datos
    end_time = time.time()
    
    return end_time - start_time

# Función para medir el rendimiento de Queue
def benchmark_queue():
    queue = multiprocessing.Queue()
    
    def child_process():
        data = queue.get()  # Recibe los datos
        return data
    
    # Generar datos aleatorios en el proceso principal
    data = [random.randint(1, 1000) for _ in range(N)]
    
    # Medir tiempo de transferencia
    start_time = time.time()
    queue.put(data)  # Envía los datos
    result = child_process()  # Recibe los datos
    end_time = time.time()
    
    return end_time - start_time

# Función para medir el rendimiento de Manager().list
def benchmark_manager_list():
    with multiprocessing.Manager() as manager:
        shared_list = manager.list()
    
        def child_process():
            return list(shared_list)
        
        # Generar datos aleatorios en el proceso principal
        data = [random.randint(1, 1000) for _ in range(N)]
    
        # Medir tiempo de transferencia
        start_time = time.time()
        shared_list.extend(data)  # Envía los datos
        result = child_process()  # Recibe los datos
        end_time = time.time()
    
        return end_time - start_time

# Función principal para ejecutar los benchmarks y graficar resultados
def run_benchmark():
    # Ejecutar benchmarks
    pipe_time = benchmark_pipe()
    queue_time = benchmark_queue()
    manager_list_time = benchmark_manager_list()

    # Guardar los tiempos para graficar
    methods = ['Pipe', 'Queue', 'Manager().list']
    times = [pipe_time, queue_time, manager_list_time]

    # Graficar los resultados
    plt.bar(methods, times, color='skyblue')
    plt.ylabel('Tiempo de transferencia (segundos)')
    plt.title('Comparación de Métodos IPC')
    plt.show()

    # Imprimir los resultados
    print(f"Tiempo con Pipe: {pipe_time:.6f} segundos")
    print(f"Tiempo con Queue: {queue_time:.6f} segundos")
    print(f"Tiempo con Manager().list: {manager_list_time:.6f} segundos")

if __name__ == '__main__':
    run_benchmark()
```