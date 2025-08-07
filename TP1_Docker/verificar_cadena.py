import json
import hashlib

BLOCKCHAIN_FILE = "blockchain.json"
REPORTE_FILE = "reporte.txt"

def cargar_blockchain():
    try:
        with open(BLOCKCHAIN_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: El archivo blockchain.json no existe.")
        return []
    except json.JSONDecodeError:
        print("Error: El archivo blockchain.json está corrupto.")
        return []

def verificar_integridad(bloques):
    corruptos = []
    prev_hash = "0" * 64

    for i, bloque in enumerate(bloques):
        datos = bloque["datos"]
        timestamp = bloque["timestamp"]
        esperado = hashlib.sha256((json.dumps(datos, sort_keys=True) + timestamp + prev_hash).encode()).hexdigest()
        
        if bloque["hash"] != esperado or bloque["prev_hash"] != prev_hash:
            corruptos.append(i)

        prev_hash = bloque["hash"]
    
    return corruptos

def generar_reporte(bloques, corruptos):
    total = len(bloques)
    alertas = sum(1 for b in bloques if b.get("alerta", False))

    suma_frec = 0
    suma_pres = 0
    suma_oxi = 0

    for b in bloques:
        suma_frec += b["datos"]["frecuencia"]["media"]
        suma_pres += b["datos"]["presion"]["media"]
        suma_oxi += b["datos"]["oxigeno"]["media"]

    promedio_frec = suma_frec / total if total else 0
    promedio_pres = suma_pres / total if total else 0
    promedio_oxi = suma_oxi / total if total else 0

    with open(REPORTE_FILE, "w") as f:
        f.write("REPORTE FINAL\n")
        f.write("====================\n")
        f.write(f"Bloques totales: {total}\n")
        f.write(f"Bloques con alerta: {alertas}\n")
        f.write(f"Bloques corruptos: {len(corruptos)}\n")
        if corruptos:
            f.write(f"Índices corruptos: {corruptos}\n")
        f.write("\nPROMEDIOS GENERALES\n")
        f.write(f"Frecuencia: {promedio_frec:.2f}\n")
        f.write(f"Presión: {promedio_pres:.2f}\n")
        f.write(f"Oxígeno: {promedio_oxi:.2f}\n")

    print("Reporte generado en reporte.txt")

def main():
    bloques = cargar_blockchain()
    if not bloques:
        return

    corruptos = verificar_integridad(bloques)
    if corruptos:
        print(f"Se detectaron bloques corruptos en los índices: {corruptos}")
    else:
        print("Cadena íntegra. No se detectaron corrupciones.")

    generar_reporte(bloques, corruptos)

if __name__ == "__main__":
    main()
