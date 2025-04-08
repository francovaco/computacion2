# 7 Ejercicios Prácticos sobre Pipes

### Ejercicio 1: Eco Simple

```python 
import os

r, w = os.pipe()
r2, w2 = os.pipe()

pid = os.fork()

if pid == 0:
    os.close(w)
    os.close(r2)
    msg = os.read(r, 1024).decode()
    os.close(r)
    os.write(w2, msg.encode())
    os.close(w2)
else:
    os.close(r)
    os.close(w2)
    mensaje = "Hola desde el padre"
    os.write(w, mensaje.encode())
    os.close(w)
    respuesta = os.read(r2, 1024).decode()
    os.close(r2)
    print(f"Padre recibió: {respuesta}")
```

### Ejercicio 2: Contador de Palabras
```python
import os

r, w = os.pipe()
r2, w2 = os.pipe()
pid = os.fork()

if pid == 0:
    os.close(w)
    os.close(r2)
    while True:
        linea = os.read(r, 1024).decode()
        if not linea:
            break
        cantidad = len(linea.split())
        os.write(w2, f"{cantidad}\n".encode())
    os.close(r)
    os.close(w2)
else:
    os.close(r)
    os.close(w2)
    lineas = ["Hola mundo", "Los pipes son útiles", "Python y procesos"]
    for l in lineas:
        os.write(w, f"{l}\n".encode())
    os.close(w)
    for _ in lineas:
        print("Palabras:", os.read(r2, 1024).decode().strip())
    os.close(r2)
```

### Ejercicio 3: Pipeline de Filtrado
```python
import os, random

def generar():
    for _ in range(10):
        print(random.randint(1, 100))

def filtrar():
    import sys
    for line in sys.stdin:
        n = int(line.strip())
        if n % 2 == 0:
            print(n)

def cuadrado():
    import sys
    for line in sys.stdin:
        n = int(line.strip())
        print(n * n)

os.pipe(), os.pipe()
```

### Ejercicio 4: Simulador de Shell
```python
import subprocess

cmd1 = input("Comando 1: ").split()
cmd2 = input("Comando 2: ").split()

p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)
p1.stdout.close()
output = p2.communicate()[0]
print(output.decode())
```

### Ejercicio 5: Chat Bidireccional
```python
import os

r1, w1 = os.pipe()
r2, w2 = os.pipe()

pid = os.fork()

if pid == 0:
    os.close(w1)
    os.close(r2)
    for _ in range(3):
        msg = os.read(r1, 1024).decode()
        print(f"Hijo recibió: {msg}")
        os.write(w2, f"Eco: {msg}".encode())
    os.close(r1)
    os.close(w2)
else:
    os.close(r1)
    os.close(w2)
    for i in range(3):
        mensaje = f"Mensaje {i}"
        os.write(w1, mensaje.encode())
        respuesta = os.read(r2, 1024).decode()
        print(f"Padre recibió: {respuesta}")
    os.close(w1)
    os.close(r2)
```

### Ejercicio 6: Servidor de Operaciones Matemáticas
```python
import os

r, w = os.pipe()
r2, w2 = os.pipe()

pid = os.fork()

if pid == 0:
    os.close(w)
    os.close(r2)
    while True:
        op = os.read(r, 1024).decode()
        if not op:
            break
        try:
            resultado = str(eval(op))
        except Exception as e:
            resultado = f"Error: {e}"
        os.write(w2, f"{resultado}\n".encode())
    os.close(r)
    os.close(w2)
else:
    os.close(r)
    os.close(w2)
    operaciones = ["5 + 3", "10 / 2", "4 ** 2", "7 +"]
    for o in operaciones:
        os.write(w, f"{o}\n".encode())
    os.close(w)
    for _ in operaciones:
        print("Resultado:", os.read(r2, 1024).decode().strip())
    os.close(r2)
```

### Ejercicio 7: Sistema de Procesamiento de Transacciones
```python
import os
import json
import random
import time

rgv, wgv = os.pipe()
rvv, wvr = os.pipe()

pid_validador = os.fork()

if pid_validador == 0:
    os.close(wgv)
    os.close(rvv)
    while True:
        data = os.read(rgv, 1024).decode()
        if not data:
            break
        try:
            trans = json.loads(data)
            if 'id' in trans and 'tipo' in trans and 'monto' in trans:
                os.write(wvr, json.dumps(trans).encode())
        except json.JSONDecodeError:
            continue
    os.close(rgv)
    os.close(wvr)
else:
    pid_registrador = os.fork()
    if pid_registrador == 0:
        os.close(wvr)
        os.close(rgv)
        stats = {'total': 0, 'depositos': 0, 'retiros': 0}
        while True:
            data = os.read(rvv, 1024).decode()
            if not data:
                break
            trans = json.loads(data)
            stats['total'] += trans['monto']
            if trans['tipo'] == 'deposito':
                stats['depositos'] += 1
            elif trans['tipo'] == 'retiro':
                stats['retiros'] += 1
        print("Estadísticas finales:", stats)
        os.close(rvv)
    else:
        os.close(rgv)
        os.close(wvr)
        tipos = ['deposito', 'retiro']
        for i in range(10):
            trans = {
                'id': i,
                'tipo': random.choice(tipos),
                'monto': random.randint(10, 500)
            }
            os.write(wgv, json.dumps(trans).encode())
            time.sleep(0.1)
        os.close(wgv)
        os.close(rvv)
```