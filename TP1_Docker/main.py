import multiprocessing
import time
import json
import random
import hashlib
import os
from datetime import datetime
import numpy as np

BLOCKCHAIN_FILE = "blockchain.json"
TOTAL_MUESTRAS = 60
VENTANA = 30

# Generador de datos biométricos
def generar_datos():
    """Genera datos biométricos aleatorios para simular sensores médicos"""
    return {
        "timestamp": datetime.now().isoformat(timespec='seconds'),
        "frecuencia": random.randint(60, 220),                     # Frecuencia cardíaca
        "presion": [random.randint(110, 220), random.randint(70, 110)],  # Presión sistólica y diastólica
        "oxigeno": random.randint(85, 105)                         # Saturación de oxígeno
    }

# Análisis por tipo de señal
def analizador(tipo, conn, queue):
    """
    Analiza una señal biométrica específica usando ventana deslizante
    - tipo: tipo de señal a analizar (frecuencia, presion, oxigeno)
    - conn: conexión para recibir datos del proceso principal
    - queue: cola para enviar resultados al verificador
    """
    ventana = []  # Ventana deslizante para calcular promedios
    try:
        for _ in range(TOTAL_MUESTRAS):
            datos = conn.recv()
            timestamp = datos["timestamp"]

            if tipo == "frecuencia":
                valor = datos["frecuencia"]
            elif tipo == "presion":
                valor = datos["presion"][0]
            elif tipo == "oxigeno":
                valor = datos["oxigeno"]
            else:
                continue

            # Mantiene el tamaño de la ventana deslizante
            ventana.append(valor)
            if len(ventana) > VENTANA:
                ventana.pop(0)  # Elimina el valor más antiguo

            media = float(np.mean(ventana))
            desv = float(np.std(ventana))

            resultado = {
                "tipo": tipo,
                "timestamp": timestamp,
                "media": media,
                "desv": desv
            }

            queue.put(resultado)
    finally:
        conn.close()  # Cierra la conexión al terminar

# Verificación y construcción de bloques
def verificador(queue_frec, queue_pres, queue_oxi):
    """
    Recolecta resultados de análisis y construye bloques del blockchain
    - Espera resultados de los 3 procesos analizadores
    - Detecta alertas médicas basadas en umbrales
    - Construye y almacena bloques en el blockchain
    """
    blockchain = []
    prev_hash = "0" * 64

    if os.path.exists(BLOCKCHAIN_FILE):
        os.remove(BLOCKCHAIN_FILE)

    for i in range(TOTAL_MUESTRAS):
        resultados = {}
        while len(resultados) < 3:
            for q in [queue_frec, queue_pres, queue_oxi]:
                if not q.empty():
                    r = q.get()
                    resultados[r["tipo"]] = r

        timestamp = resultados["frecuencia"]["timestamp"]
        
        # Detección de alertas
        alerta = (
            resultados["frecuencia"]["media"] >= 200 or  # Taquicardia severa
            not (90 <= resultados["oxigeno"]["media"] <= 100) or  # Hipoxemia
            resultados["presion"]["media"] >= 200  # Hipertensión severa
        )

        # Estructura de datos para el bloque
        datos = {
            "frecuencia": resultados["frecuencia"],
            "presion": resultados["presion"],
            "oxigeno": resultados["oxigeno"]
        }

        # Creación del hash del bloque (datos + timestamp + hash anterior)
        bloque_str = json.dumps(datos, sort_keys=True) + timestamp + prev_hash
        bloque_hash = hashlib.sha256(bloque_str.encode()).hexdigest()

        # Estructura completa del bloque
        bloque = {
            "timestamp": timestamp,
            "datos": datos,
            "alerta": alerta,
            "prev_hash": prev_hash,
            "hash": bloque_hash
        }

        blockchain.append(bloque)
        prev_hash = bloque_hash

        with open(BLOCKCHAIN_FILE, "w") as f:
            json.dump(blockchain, f, indent=4)

        print(f"[{i+1}] Hash: {bloque_hash[:10]}... Alerta: {alerta}")

# Función principal
def main():
    parent_conns = []
    child_conns = []
    queues = []

    # Crea pipes y colas para 3 procesos analizadores
    for _ in range(3):
        parent_conn, child_conn = multiprocessing.Pipe()
        queue = multiprocessing.Queue()
        parent_conns.append(parent_conn)
        child_conns.append(child_conn)
        queues.append(queue)

    # Inicia procesos analizadores para cada tipo de señal
    procesos = []
    for tipo, conn, queue in zip(["frecuencia", "presion", "oxigeno"], child_conns, queues):
        p = multiprocessing.Process(target=analizador, args=(tipo, conn, queue))
        procesos.append(p)
        p.start()

    # Inicia proceso verificador que construye el blockchain
    p_verificador = multiprocessing.Process(target=verificador, args=tuple(queues))
    p_verificador.start()

    try:
        for _ in range(TOTAL_MUESTRAS):
            datos = generar_datos()
            for conn in parent_conns:
                conn.send(datos)
            time.sleep(1)
    finally:
        for conn in parent_conns:
            conn.close()

    for p in procesos:
        p.join()

    p_verificador.join()
    print("Análisis finalizado.")

if __name__ == "__main__":
    main()