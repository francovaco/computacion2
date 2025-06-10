# Resumen: Hilos y Concurrencia con `threading` en Python

## Introducción
La concurrencia permite que distintas partes de un programa se ejecuten simultáneamente. Los hilos (`threads`) son la unidad más pequeña de ejecución y permiten realizar tareas concurrentes dentro de un proceso.

## Capítulo 1: Fundamentos de los Hilos

### ¿Qué es un Hilo?
- Unidad de ejecución gestionada por el sistema operativo.
- Comparte memoria con otros hilos del mismo proceso.

### Características Clave
- Compartición de memoria.
- Ejecución concurrente o paralela.
- Ligereza comparado con procesos.

### Ventajas
- Mejora del rendimiento y la responsividad.
- Eficiencia de recursos.

### Desafíos
- Necesidad de sincronización.
- Complejidad en diseño y depuración.
- Riesgo de *race conditions* y *deadlocks*.

## Capítulo 2: Hilos vs Procesos

| Aspecto             | Hilos                         | Procesos                      |
|---------------------|-------------------------------|-------------------------------|
| Memoria             | Compartida                    | Aislada                       |
| Comunicación        | Memoria compartida directa    | IPC                           |
| Coste de creación   | Bajo                          | Alto                          |
| Paralelismo real    | Limitado por el GIL           | Sí, con `multiprocessing`     |

## Capítulo 3: Tipos de Hilos

### Hilos a Nivel de Usuario
- Gestionados en espacio de usuario.
- Rápidos, pero no aprovechan múltiples núcleos.

### Hilos a Nivel de Kernel
- Gestionados por el SO.
- Permiten paralelismo real.

### Python (`threading`)
- Usa hilos del sistema (nivel de kernel).
- Limitados por el **GIL**.

## Capítulo 4: El Módulo `threading` de Python

### Clases y Métodos Importantes
- `Thread`, `Lock`, `RLock`, `Semaphore`, `Event`, `Condition`, `Barrier`.

## Capítulo 5: El GIL en CPython

- Solo un hilo puede ejecutar bytecode Python a la vez.
- Limita paralelismo real en tareas CPU-bound.
- Es irrelevante para I/O-bound o bibliotecas que liberan el GIL.
- Alternativas: `multiprocessing`, `asyncio`, extensiones en C.

## Capítulo 6: Comparativa Final

| Modelo          | Ideal para       | Paralelismo | GIL       |
|----------------|------------------|-------------|-----------|
| `threading`    | I/O-bound        | No          | Sí        |
| `multiprocessing` | CPU-bound     | Sí          | No        |
| `asyncio`      | I/O intensivo    | No (cooperativo) | No (monohilo) |

## Capítulo 7: Ejercicios Avanzados

- **Web Crawler multihilo** con `Lock`.
- **Sistema de procesamiento de tareas** con `Queue`, `Lock`, `JoinableQueue`.

## Conclusiones

- Los hilos son eficientes para I/O, pero deben usarse con sincronización cuidadosa.
- Para CPU-bound, usar `multiprocessing`.
- El GIL limita el paralelismo real, pero no impide la concurrencia útil.

> Dominar los hilos es saber cuándo y cómo usarlos… o cuándo evitarlos.

