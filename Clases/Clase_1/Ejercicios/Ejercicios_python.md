## Ejercicios de Python con argparse

```python
# 1. Uso básico de argparse
import argparse
parser = argparse.ArgumentParser(description="Procesador de archivos con número de líneas limitadas")
parser.add_argument("-i", "--input", required=True, help="Archivo de entrada")
parser.add_argument("-o", "--output", required=True, help="Archivo de salida")
parser.add_argument("-n", "--num_lines", required=True, type=int, help="Número de líneas a procesar")
args = parser.parse_args()
print(f"Procesando {args.num_lines} líneas del archivo {args.input} y guardando en {args.output}")

# 2. Validación de argumentos

def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("El número de líneas debe ser un entero positivo.")
    return ivalue

parser.add_argument("-n", "--num_lines", type=check_positive, help="Número de líneas a procesar (debe ser positivo)")

# 3. Uso de argumentos opcionales
parser.add_argument("--verbose", action="store_true", help="Muestra mensajes detallados de procesamiento")
if args.verbose:
    print("Modo detallado activado.")

# 4. Argumentos posicionales y opciones restringidas
parser.add_argument("archivo", help="Archivo de entrada (argumento posicional)")
parser.add_argument("--modo", choices=["rapido", "lento"], help="Modo de ejecución (opcional)")

# 5. Mostrar ayuda del script
# Ejecutar en terminal:
# python script.py --help
```