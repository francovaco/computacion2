#  Resumen de Pipes – Computación II

##  Contexto

Estudiante: 3er año Ing. en Informática – Universidad de Mendoza  
Asignatura: Computación II  
Objetivo: Comprender y aplicar **pipes** para comunicación entre procesos en Python.

---

##  Estructura y objetivos de aprendizaje

1. **Fundamentos conceptuales de los pipes**
2. **Implementación interna y ciclo de vida**
3. **Implementación práctica en Python**
4. **Ejemplos de comunicación y pipelines**
5. **Ejercicios prácticos**
6. **Prevención de errores comunes**

---

## 1.  Fundamentos conceptuales

- Un **pipe** permite la **comunicación unidireccional** entre procesos.
- Se comporta como un **archivo temporal en memoria**, gestionado por el kernel.
- Sirve para enviar datos desde un proceso a otro, sin usar archivos intermedios.
- Utilizado comúnmente para conectar procesos como filtros:  
  `comando1 | comando2`

---

## 2.  Implementación interna y ciclo de vida

- `os.pipe()` crea el pipe → devuelve `(r, w)` (read y write descriptors).
- El buffer del pipe tiene un tamaño limitado (usualmente 4–64 KB).
- Si se llena, `write()` se bloquea.  
  Si está vacío, `read()` se bloquea.
- Cierre adecuado de extremos es esencial:
  - Proceso que **escribe**: cierra `r`.
  - Proceso que **lee**: cierra `w`.
- El sistema libera recursos al cerrar ambos extremos.

---

## 3.  Pipes en Python con `os`

###  Código base: comunicación padre → hijo

```python
import os

r, w = os.pipe()
pid = os.fork()

if pid > 0:
    os.close(r)
    os.write(w, b"Hola desde el padre")
    os.close(w)
    os.wait()
else:
    os.close(w)
    mensaje = os.read(r, 1024)
    print("Hijo recibió:", mensaje.decode())
    os.close(r)
```

- `os.write()` y `os.read()` trabajan con **bytes** → usar `.encode()` y `.decode()`.

---

## 4.  Ejemplos prácticos

###  Comunicación unidireccional

Padre escribe → hijo lee.

###  Pipeline (Padre → Hijo como filtro)

Padre lee archivo y escribe línea por línea al pipe.  
Hijo filtra las que contengan `"hola"`.

```python
with open("archivo.txt", "r") as f:
    for linea in f:
        os.write(w, linea.encode())

# Hijo
if "hola" in linea.lower():
    print("Hijo:", linea)
```

###  Comunicación bidireccional

Usar **dos pipes**:

```python
r1, w1 = os.pipe()  # Padre → Hijo
r2, w2 = os.pipe()  # Hijo → Padre
```

Cada proceso cierra los extremos que no usa. Se puede simular un diálogo.

---

## 5.  Ejercicios prácticos propuestos

###  Ejercicio 1: Filtrar líneas largas
- Padre: lee archivo y manda líneas.
- Hijo: imprime las que tienen más de 20 caracteres.

###  Ejercicio 2: Comunicación bidireccional con transformación
- Padre envía texto → hijo responde en mayúsculas.

###  Ejercicio 3: Mini pipeline de 3 procesos
- Padre → Proceso 1 (a mayúsculas) → Proceso 2 (filtra `"ERROR"`).

---

## 6.  Prevención de errores comunes

-  **No cerrar extremos** → bloqueos (deadlocks).
-  Escribir sin lector → excepción o `SIGPIPE`.
-  Siempre cerrar los descriptores no usados.
-  Usar `os.wait()` para evitar procesos huérfanos.
-  Documentar cada parte del código.

---

##  Puestas en común (checkpoints)

En cada sección hicimos pausas para:
- Verificar comprensión con preguntas.
- Compartir avances con el profesor.
- Confirmar correcta implementación y cierre de descriptores.

---

##  Recordatorios finales

-  No avanzar sin comprender bien `os.pipe()` y `os.fork()`.
-  Compartí al menos un ejercicio funcional con tu profesor.
-  Documentá tu código con claridad.
-  No avanzar a temas como *sockets o programación asíncrona* sin dominar primero **pipes**.
