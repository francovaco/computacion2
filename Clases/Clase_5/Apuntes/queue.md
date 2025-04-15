
# Queues en Programación Concurrente - Resumen de clase

## Tema principal
Exploramos el uso de **Queues** en programación concurrente con Python, enfocándonos en su **concepto teórico**, **implementación práctica** y **aplicaciones en comunicación entre procesos (IPC)**.

## Conceptos clave

- **Queue (cola)**: estructura FIFO utilizada para comunicar procesos entre sí de forma segura.
- **Ciclo de vida**: creación → uso → cierre → señal de fin.
- **Poison pill**: mensaje especial para indicar que un consumidor debe finalizar.
- **Bloqueo**: los procesos pueden quedarse esperando si la cola está vacía o llena (según `get()` o `put()`).

## 🛠 Implementación en Python

### Cola básica
```python
from multiprocessing import Process, Queue

def productor(q):
    q.put("Hola")

def consumidor(q):
    print(q.get())

if __name__ == "__main__":
    q = Queue()
    p1 = Process(target=productor, args=(q,))
    p2 = Process(target=consumidor, args=(q,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
```

### Comunicación múltiple con finalización
```python
def productor(q):
    for i in range(5):
        q.put(f"Mensaje {i}")
    q.put("FIN")

def consumidor(q):
    while True:
        msg = q.get()
        if msg == "FIN":
            break
        print("Procesado:", msg)
```

## Prevención de errores comunes

- Usar `Queue(maxsize)` para controlar la capacidad.
- Manejar explícitamente los finales de comunicación (`"FIN"`).
- Evitar bloqueos circulares planificando el flujo.

## Comparación con `Pipe`

| Característica        | `Queue`                    | `Pipe`                      |
|-----------------------|----------------------------|-----------------------------|
| Comunicación          | Multicanal (varios procesos) | Punto a punto               |
| Bloqueante            | Sí                          | Sí                          |
| Orden                 | FIFO                        | FIFO (básico)               |
| Seguridad             | Más robusta                | Requiere cuidado manual     |

## Buenas prácticas

- Documentar cada función con propósito y argumentos.
- Usar nombres descriptivos y constantes para mensajes especiales.
- Observar la ejecución en el sistema (`ps`, `htop`, `pstree`).
- Compartir y validar el código con docentes o compañeros.