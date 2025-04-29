
# Resumen Completo: Señales en Sistemas Operativos (UNIX/POSIX) y Python

## ¿Qué son las señales?

Una **señal** es una notificación enviada a un proceso para informarle de un evento asincrónico. Las señales permiten a los procesos:
- Manejar eventos inesperados (como división por cero).
- Interrumpirse mutuamente (por ejemplo, desde el teclado con `Ctrl+C`).
- Sincronizar acciones entre procesos concurrentes.

---

## Tipos de señales

### Por origen:
- **Síncronas**: generadas por errores durante la ejecución del proceso, como `SIGFPE` (división por cero).
- **Asíncronas**: generadas por el sistema operativo o por otros procesos (`SIGINT`, `SIGTERM`, etc).

### Por diseño:
- **Estándar**: como `SIGINT`, `SIGTERM`, `SIGKILL`.
- **Tiempo real (POSIX.1b)**: `SIGRTMIN` a `SIGRTMAX`, permiten **datos adjuntos** y **cola de señales**.

---

## Señales comunes en UNIX

| Señal      | Número | Descripción                          |
|------------|--------|--------------------------------------|
| SIGINT     | 2      | Interrupción desde teclado (Ctrl+C)  |
| SIGTERM    | 15     | Solicitud de terminación             |
| SIGKILL    | 9      | Terminación inmediata (no atrapable) |
| SIGSTOP    | 19     | Pausa del proceso                    |
| SIGCONT    | 18     | Continuar proceso pausado            |
| SIGUSR1    | 10     | Uso definido por el usuario 1        |
| SIGUSR2    | 12     | Uso definido por el usuario 2        |
| SIGCHLD    | 17     | El hijo terminó                      |

---

## Señales que no se pueden manejar

- `SIGKILL` y `SIGSTOP` **no pueden ser atrapadas ni ignoradas**, ya que están diseñadas por el sistema para controlar estrictamente los procesos.
- Estas señales **no pueden ser interceptadas** por `signal.signal()` ni por `sigaction()`.
- Se usan generalmente para asegurar que un proceso termine (KILL) o se detenga (STOP) sin posibilidad de intervención del propio proceso.

---

## Señales en Python (módulo `signal`)

### Funciones principales

```python
import signal
import os

# Registrar un manejador de señal
signal.signal(signal.SIGINT, handler)

# Enviar señal al mismo proceso
signal.raise_signal(signal.SIGUSR1)

# Enviar señal a otro proceso
os.kill(pid, signal.SIGUSR1)

# Suspender el proceso hasta recibir una señal
signal.pause()

# Obtener el PID del proceso actual o del padre
os.getpid()
os.getppid()
```

### Ejemplo básico

```python
import signal
import time

def handler(signum, frame):
    print(f"Señal recibida: {signum}")

signal.signal(signal.SIGINT, handler)

print("Esperando SIGINT (Ctrl+C)...")
signal.pause()
```

---

## Señales y multihilo en Python

- **Solo el hilo principal del proceso** puede registrar manejadores de señal mediante `signal.signal()`.
- Si otro hilo intenta hacerlo, Python lanza una excepción `ValueError`.
- Para comunicar la recepción de una señal al resto de los hilos, se recomienda usar:
  - `threading.Event()`
  - Variables globales protegidas por locks
- Las señales dirigidas al proceso (como `SIGTERM`) pueden ser recibidas por cualquier hilo, pero **sólo el hilo principal** puede ejecutar el handler.
- Las **señales dirigidas a un hilo específico** son parte de POSIX pero no están expuestas directamente en Python.

---

## Seguridad en los signal handlers

- En contexto de señales, **no todas las funciones son seguras** para usar (async-signal-safe).
- **Evitar funciones como**:
  - `print()`
  - `malloc()`
  - `exit()`
  - funciones que realicen asignaciones dinámicas o IO de alto nivel
- **Sí se puede usar** dentro de un handler:
  - `write()` (bajo nivel, syscall directa)
  - `signal()` (registrar otra señal)
  - `_exit()` (terminación inmediata)

### Recomendación de diseño

- **Usar el handler solo para marcar un evento**, y manejar la lógica en el código principal del proceso.
- Ejemplo:

```python
import signal

flag = False

def handler(sig, frame):
    global flag
    flag = True  # Marcar recepción

signal.signal(signal.SIGUSR1, handler)
```

---

## Comparación con otros mecanismos IPC

| Mecanismo           | Comunicación     | Soporta datos complejos | Comentario                            |
|---------------------|------------------|--------------------------|----------------------------------------|
| Señales             | Notificación     | No                       | Útiles para eventos simples            |
| Pipes               | Unidireccional   | Si                       | Mejor para transferencia de datos     |
| Memoria compartida  | Compartido       | Si                       | Rápida, requiere sincronización        |

---

## Diferencias entre funciones

- `signal.raise_signal(sig)` → Señal enviada **al proceso actual**.
- `os.kill(pid, sig)` → Señal enviada **a cualquier proceso** (incluso el mismo).
- `sigqueue(pid, sig, value)` en C → Permite enviar **datos** junto con la señal.
- `sigaction()` en C → Define el comportamiento avanzado al recibir una señal.

---

## Ejemplo con `fork()` y señales

```python
import os
import signal
import time

def child_handler(signum, frame):
    os.write(1, b"Hijo: Señal recibida, comenzando tarea...
")

pid = os.fork()

if pid == 0:
    # Proceso hijo
    signal.signal(signal.SIGUSR1, child_handler)
    os.write(1, b"Hijo: Esperando señal SIGUSR1...
")
    signal.pause()
else:
    # Proceso padre
    time.sleep(2)
    os.write(1, b"Padre: Enviando señal al hijo...
")
    os.kill(pid, signal.SIGUSR1)
```