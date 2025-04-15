### Comunicación unidireccional entre dos procesos
```python
from multiprocessing import Process, Queue
import time

def productor(queue):
    for i in range(5):
        print(f"Productor: enviando {i}")
        queue.put(i)
        time.sleep(1)  # Simula trabajo

def consumidor(queue):
    for _ in range(5):
        dato = queue.get()
        print(f"Consumidor: recibió {dato}")

if __name__ == '__main__':
    q = Queue()

    p1 = Process(target=productor, args=(q,))
    p2 = Process(target=consumidor, args=(q,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print("Comunicación completada.")
```

### Múltiples productores, un consumidor
```python
from multiprocessing import Process, Queue
import time
import random

def productor(nombre, queue):
    for i in range(3):
        item = f"{nombre}-{i}"
        print(f"[{nombre}] Enviando: {item}")
        queue.put(item)
        time.sleep(random.uniform(0.5, 1.5))

def consumidor(queue, total_items):
    for _ in range(total_items):
        item = queue.get()
        print(f"[Consumidor] Recibió: {item}")

if __name__ == '__main__':
    q = Queue()
    total_items = 3 * 2  # 3 ítems por 2 productores

    productores = [
        Process(target=productor, args=(f"P{i+1}", q))
        for i in range(2)
    ]
    consumidor_proc = Process(target=consumidor, args=(q, total_items))

    for p in productores:
        p.start()
    consumidor_proc.start()

    for p in productores:
        p.join()
    consumidor_proc.join()

    print("Procesamiento completo.")
```

### Múltiples productores, múltiples consumidores
```python
from multiprocessing import Process, Queue
import time
import random

PRODUCTOS = ["mouse", "teclado", "monitor", "impresora", "webcam"]

def productor(nombre, queue, cantidad):
    for i in range(cantidad):
        pedido = {
            "id": f"{nombre}-{i}",
            "producto": random.choice(PRODUCTOS)
        }
        print(f"[{nombre}] Generando pedido: {pedido}")
        queue.put(pedido)
        time.sleep(random.uniform(0.1, 0.5))
    print(f"[{nombre}] Envío completo.")

def consumidor(nombre, queue):
    while True:
        pedido = queue.get()
        if pedido == "FIN":
            print(f"[{nombre}] Fin de procesamiento.")
            break
        print(f"[{nombre}] Procesando {pedido}")
        time.sleep(random.uniform(0.2, 0.6))

if __name__ == "__main__":
    q = Queue(maxsize=5)
    productores = []
    for i in range(3):
        p = Process(target=productor, args=(f"PV{i+1}", q, random.randint(5, 10)))
        productores.append(p)
        p.start()

    consumidores = []
    for i in range(2):
        c = Process(target=consumidor, args=(f"CP{i+1}", q))
        consumidores.append(c)
        c.start()

    for p in productores:
        p.join()

    # Enviar 'FIN' a cada consumidor
    for _ in consumidores:
        q.put("FIN")

    for c in consumidores:
        c.join()

    print("Sistema finalizado.")
```

### Ejercicio 7: Sistema de Procesamiento de Transacciones
```python
from multiprocessing import Process, Queue
import random
import time

def generador(queue_in, num_transacciones=5):
    for i in range(num_transacciones):
        transaccion = {
            'id': i,
            'tipo': random.choice(['depósito', 'retiro']),
            'monto': random.randint(-1000, 1000)
        }
        print(f"[Generador] Enviando transacción: {transaccion}")
        queue_in.put(transaccion)
        time.sleep(1)
    queue_in.put("FIN")  # Señal de finalización

def validador(queue_in, queue_out):
    while True:
        transaccion = queue_in.get()
        if transaccion == "FIN":
            print("[Validador] Fin de transacciones recibido.")
            queue_out.put("FIN")
            break
        if transaccion['monto'] > 0:
            print(f"[Validador] Transacción {transaccion['id']} validada")
            queue_out.put(transaccion)
        else:
            print(f"[Validador] Transacción {transaccion['id']} rechazada")

def registrador(queue_out):
    total_transacciones = 0
    total_monto = 0
    while True:
        transaccion = queue_out.get()
        if transaccion == "FIN":
            print("[Registrador] Fin recibido. Generando reporte final...")
            break
        total_transacciones += 1
        total_monto += transaccion['monto']
        print(f"[Registrador] Transacción {transaccion['id']} registrada. Monto acumulado: {total_monto}")
    print(f"[Registrador] Total transacciones: {total_transacciones}, Monto total: {total_monto}")

if __name__ == "__main__":
    from multiprocessing import Queue

    # Crear las colas compartidas
    queue_in = Queue()
    queue_out = Queue()

    # Crear procesos
    p1 = Process(target=generador, args=(queue_in,))
    p2 = Process(target=validador, args=(queue_in, queue_out))
    p3 = Process(target=registrador, args=(queue_out,))

    # Iniciar procesos
    p1.start()
    p2.start()
    p3.start()

    # Esperar finalización
    p1.join()
    p2.join()
    p3.join()
```