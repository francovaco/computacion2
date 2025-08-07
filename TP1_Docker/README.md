# Sistema Concurrente de Análisis Biométrico con Cadena de Bloques Local

Este sistema simula una prueba de esfuerzo generando datos biométricos (frecuencia cardíaca, presión arterial y nivel de oxígeno) en tiempo real. Cada señal es procesada en paralelo por distintos procesos que calculan estadísticas como media y desviación estándar. Los resultados se verifican y almacenan en una cadena de bloques local que garantiza la integridad de los datos.

### Archivos generados por el sistema:
- `blockchain.json`: contiene la cadena de bloques con los datos procesados y verificados.
- `reporte.txt`: informe con estadísticas generales y verificación de la integridad de la cadena.

---

## Requerimientos

- Python **3.9 o superior**
- Librerías necesarias:
  - `numpy` 
  - Módulos estándar: `multiprocessing`, `datetime`, `hashlib`, `random`, `json`, `os`, `time`

---

## Instalación

1. Crear un entorno virtual (opcional pero recomendado):

```bash
python3 -m venv venv
source venv/bin/activate     # En Linux/macOS
venv\Scripts\activate        # En Windows
```

2. Instalar las dependencias con el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Ejecución del sistema principal

Para iniciar el sistema principal, ejecutá:

```bash
python main.py
```

Esto realizará automáticamente:

- La generación de 60 muestras de datos (1 por segundo).
- El análisis concurrente por tres procesos separados.
- La verificación de los resultados.
- La construcción de bloques con sus respectivos hashes.
- El guardado de los bloques en `blockchain.json`.

Durante la ejecución, se mostrará información por consola indicando si el bloque incluye una alerta:

```
[1] Hash: a1b2c3d4... Alerta: False
[2] Hash: e5f6g7h8... Alerta: True
```

---

## Verificación de la cadena

Una vez finalizado `main.py`, podés ejecutar el verificador de integridad con:

```bash
python verificar_cadena.py
```

Este script:

- Recorre la cadena de bloques y recalcula los hashes.
- Verifica que no haya bloques corruptos.
- Cuenta la cantidad de alertas detectadas.
- Calcula los promedios generales de frecuencia, presión y oxígeno.

### Archivo generado:

- `reporte.txt`: informe con el total de bloques, número de alertas, posibles bloques corruptos y estadísticas globales.

---

## Ejemplo de uso completo

```bash
python main.py
python verificar_cadena.py
cat reporte.txt
```

---

## Ejecución del código en Docker

Crear la imagen de Docker:

```bash
docker build -t analisis-biometrico .
```

Ejecutar main:

```bash
docker run --rm -v $(pwd):/app analisis-biometrico
```

Ejecutar el verificador:

```bash
docker run --rm -v $(pwd):/app analisis-biometrico python verificar_cadena.py
```

---

### Franco Vaccarezza 63179