# Resumen: Dominando la Concurrencia en Python con `multiprocessing`

## Introducción
La concurrencia es esencial en sistemas modernos para mejorar rendimiento y responsividad. Sin embargo, introduce problemas como *condiciones de carrera* al compartir recursos. La solución: **exclusión mutua** y sincronización usando primitivas como `Lock`, `Semaphore`, `Condition`, entre otras.

## 1. Lock
- **¿Qué es?** Primitiva básica para asegurar que solo un proceso acceda a una sección crítica.
- **Uso típico:** Contadores, archivos compartidos.
- **Recomendación:** Usar con `with lock:` para evitar *deadlocks*.
- **Ejemplo:** Incremento seguro de un contador.

## 2. RLock (Reentrant Lock)
- **¿Qué es?** Lock que puede ser adquirido varias veces por el mismo proceso.
- **Ideal para:** Funciones recursivas o llamadas anidadas sincronizadas.
- **Advertencia:** Indica posible diseño complejo.

## 3. Semaphore
- **¿Qué es?** Permite que hasta *N* procesos entren a una sección crítica.
- **Uso típico:** Control de acceso a recursos limitados (BD, buffer).
- **No tiene propiedad:** Cuidado con `release()` extra.

## 4. BoundedSemaphore
- **Diferencia clave:** Lanza error si `release()` excede el límite inicial.
- **Uso:** Detección temprana de errores de lógica.

## 5. Condition
- **¿Qué es?** Permite que procesos esperen hasta que se cumpla una condición.
- **Métodos:** `wait()`, `notify()`, `notify_all()`.
- **Uso típico:** Productor-consumidor avanzado, barreras reutilizables.
- **Importante:** Usar `wait()` dentro de un bucle `while`.

## 6. Event
- **¿Qué es?** Bandera booleana compartida entre procesos.
- **Métodos:** `set()`, `clear()`, `wait()`.
- **Uso:** Señales simples como inicio, parada, alerta.

## 7. Barrier
- **¿Qué es?** Punto de sincronización: todos los procesos deben llegar antes de continuar.
- **Ideal para:** Algoritmos en fases, pruebas de concurrencia.
- **Cuidado:** Si uno falla, todos los que esperan lanzan `BrokenBarrierError`.

## 8. Queue
- **¿Qué es?** Estructura FIFO segura para múltiples procesos.
- **Uso:** Comunicación, distribución de tareas, logging centralizado.
- **Variante:** `JoinableQueue` permite saber cuándo todas las tareas fueron completadas.

## 9. Value
- **¿Qué es?** Variable compartida simple (entero, float, etc.).
- **Uso típico:** Contadores, flags, estados.
- **Atención:** No es atómico; usar `Lock` para `+=`.

## 10. Array
- **¿Qué es?** Arreglo de memoria compartida.
- **Uso:** Estructuras como matrices, buffers.
- **Sincronización:** Usar `get_lock()` o `Lock` externo para modificar.

## Recomendaciones Generales
- **Usar siempre `Lock`** para evitar condiciones de carrera.
- **Combinar primitivas** según la necesidad del patrón concurrente.
- **Evitar `print()` desde múltiples procesos sin control.**
- **Diseño claro y modular** es clave en sistemas concurrentes.