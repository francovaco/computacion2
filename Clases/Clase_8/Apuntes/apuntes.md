# Apunte de Multiprocessing en Python

## ¿Por qué usar `multiprocessing`?

Python tiene una limitación llamada **GIL (Global Interpreter Lock)** que impide ejecutar múltiples hilos verdaderamente en paralelo para tareas que consumen CPU.  
El módulo `multiprocessing` evita esta limitación creando **procesos independientes**, cada uno con su propio intérprete y espacio de memoria.

---

## Procesos vs Hilos

| Característica     | Hilos                      | Procesos                    |
|--------------------|----------------------------|-----------------------------|
| Memoria            | Compartida                 | Independiente               |
| Seguridad          | Baja (riesgo de colisiones)| Alta (aislados)             |
| Recursos           | Menos consumo              | Más consumo                 |
| Paralelismo real   | No (por el GIL)            | Sí                          |

---

## Crear y controlar procesos

### Clase `Process`

```python
from multiprocessing import Process

def tarea():
    print("Hola desde un proceso hijo")

p = Process(target=tarea)
p.start()   # crea y lanza el proceso
p.join()    # espera a que termine
```

- `.start()` inicia el proceso.
- `.join()` bloquea el padre hasta que termine el hijo.
- `.run()` se ejecuta directamente, **sin crear proceso nuevo**.

> Si se omite `join()`, el proceso puede quedar ejecutándose en segundo plano.

---

## Comunicación entre procesos (IPC)

Los procesos **no comparten memoria**, por lo tanto deben comunicarse por mecanismos de IPC:

### 1. `Queue`

Cola segura entre procesos, basada en `multiprocessing.Queue`.

- Apta para **muchos productores y consumidores**.
- Evita condiciones de carrera.
- Bloquea por defecto si se intenta leer sin datos.

```python
from multiprocessing import Process, Queue

def productor(q):
    q.put("dato")

def consumidor(q):
    print(q.get())

q = Queue()
Process(target=productor, args=(q,)).start()
Process(target=consumidor, args=(q,)).start()
```

### 2. `Pipe`

Conecta **exactamente dos procesos**.

- Menos escalable.
- Más rápido en casos simples.

```python
from multiprocessing import Pipe

a, b = Pipe()
a.send("mensaje")
print(b.recv())
```

---

## Compartir estado: `Value` y `Array`

Para compartir variables entre procesos:

- `Value('d', 0.0)` — comparte un valor escalar.
- `Array('i', [0]*5)` — comparte un arreglo.

### Protección con `Lock`

El acceso a estos objetos **debe sincronizarse** para evitar condiciones de carrera.

```python
from multiprocessing import Value, Lock

val = Value('i', 0)
lock = Lock()

with lock:
    val.value += 1
```

---

## Pool de procesos

`Pool` administra un grupo fijo de procesos trabajadores.

- Más eficiente que crear procesos manualmente.
- Simplifica el paralelismo de funciones.

```python
from multiprocessing import Pool

def cuadrado(x):
    return x * x

with Pool(4) as pool:
    resultados = pool.map(cuadrado, range(10))
```

### Variantes:

- `apply()` → ejecuta una función con un argumento.
- `map()` → paraleliza una función sobre una lista.
- `map_async()` → versión no bloqueante de `map()`.

---

## Medición de rendimiento

- **Speed-up**: compara el tiempo de una versión secuencial vs paralela.
- **Contención**: se produce cuando muchos procesos compiten por un recurso (ej. un `Lock`).
- **Back-off exponencial**: estrategia para reintentar tras una contención.

---

## IPC avanzado

### Manager

`multiprocessing.Manager()` permite compartir estructuras más complejas entre procesos:

```python
from multiprocessing import Manager

m = Manager()
lista_compartida = m.list()
```

---

## Conceptos clave

- **Condición de carrera**: ocurre cuando dos procesos acceden a una variable al mismo tiempo sin sincronización.
- **Sección crítica**: parte del código que accede a recursos compartidos y debe protegerse.
- **Deadlock**: bloqueo mutuo cuando dos o más procesos esperan indefinidamente por un recurso.
