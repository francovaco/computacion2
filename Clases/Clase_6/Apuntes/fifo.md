# Resumen de FIFOs en Unix/Linux

## 1. ¿Qué son los FIFOs?

Los *FIFOs* (First-In, First-Out), también conocidos como *named pipes*, son archivos especiales utilizados para la comunicación entre procesos (IPC) en sistemas Unix/Linux. A diferencia de los *pipes anónimos*, los FIFOs:

- Son persistentes (se representan como archivos en el sistema de archivos).
- Permiten comunicación entre procesos **no emparentados**.
- Son adecuados para arquitecturas modulares y desacopladas.

## 2. Características principales

- Comunicación **unidireccional** o **bidireccional** (usando dos FIFOs).
- Semántica de **cola**: lo que se escribe primero, se lee primero.
- Se crean con `mkfifo` o `os.mkfifo()` (en Python).
- Persisten en disco hasta que son eliminados.
- Cada proceso tiene su propio descriptor de archivo y cursor de lectura.

## 3. Operaciones básicas

### Crear un FIFO:
```bash
mkfifo /tmp/mi_fifo
```

### Escritura y lectura en Python:
```python
# escribir_fifo.py
with open('/tmp/mi_fifo', 'w') as fifo:
    fifo.write('Hola mundo\n')
```

```python
# leer_fifo.py
with open('/tmp/mi_fifo', 'r') as fifo:
    print(fifo.readline())
```

> Si no hay lector, el escritor se bloquea (y viceversa), salvo que se usen flags `O_NONBLOCK`.

## 4. Cuestiones técnicas clave

- **Bloqueo:** lectores se bloquean si no hay datos; escritores si no hay lectores.
- **Buffer interno:** FIFO implementado como cola circular en espacio de kernel.
- **Tamaño del buffer:** configurable vía `/proc/sys/fs/pipe-max-size`.
- **Cursor independiente:** cada proceso mantiene su propia posición de lectura.
- **Uso de `select()`/`poll()`:** permite monitorear múltiples FIFOs sin espera activa.

## 5. Buenas prácticas

- Verificar si el FIFO existe antes de crearlo:
```python
if not os.path.exists('/tmp/mi_fifo'):
    os.mkfifo('/tmp/mi_fifo')
```

- Limpiar recursos al finalizar:
```python
os.unlink('/tmp/mi_fifo')
```

- Controlar permisos con `umask` para evitar accesos no autorizados.
- Validar que haya lectores antes de escribir, si es crítico.
- Utilizar múltiples FIFOs para lograr comunicación bidireccional clara.

## 6. Conclusión

Los FIFOs son una solución simple y eficaz para la comunicación entre procesos en sistemas Unix/Linux. Su diseño basado en archivos y su semántica de cola permiten:

- Diseñar sistemas modulares y concurrentes.
- Construir herramientas como chats, loggers o multiplexores simples.
- Comprender fundamentos clave de IPC sin necesidad de herramientas más complejas como sockets o memoria compartida.