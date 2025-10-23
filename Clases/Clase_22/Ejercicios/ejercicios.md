## Ejercicio 1 
```python
import gzip
import shutil
import time
import random
import string
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed


def generar_contenido_aleatorio(tamaño_kb=100):
    # Generar texto repetitivo para que sea comprimible
    palabras = [''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 10))) 
                for _ in range(100)]
    
    contenido = []
    tamaño_actual = 0
    tamaño_objetivo = tamaño_kb * 1024
    
    while tamaño_actual < tamaño_objetivo:
        linea = ' '.join(random.choices(palabras, k=20)) + '\n'
        contenido.append(linea)
        tamaño_actual += len(linea)
    
    return ''.join(contenido)


def crear_archivos_prueba(num_archivos=10, tamaño_kb=100):
    carpeta = Path("archivos_prueba")
    carpeta.mkdir(exist_ok=True)
    
    archivos_creados = []
    
    print(f"Creando {num_archivos} archivos de ~{tamaño_kb}KB cada uno...")
    
    for i in range(num_archivos):
        nombre_archivo = carpeta / f"archivo_{i:02d}.txt"
        contenido = generar_contenido_aleatorio(tamaño_kb)
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        archivos_creados.append(nombre_archivo)
        print(f"  OK {nombre_archivo.name} - {nombre_archivo.stat().st_size / 1024:.1f}KB")
    
    print(f"\n{num_archivos} archivos creados\n")
    return archivos_creados


def comprimir_archivo(ruta_entrada):
    ruta_salida = ruta_entrada.with_suffix('.txt.gz')
    
    try:
        # Comprimir archivo
        with open(ruta_entrada, 'rb') as f_in:
            with gzip.open(ruta_salida, 'wb', compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Obtener tamaños
        tamaño_original = ruta_entrada.stat().st_size
        tamaño_comprimido = ruta_salida.stat().st_size
        ratio = (1 - tamaño_comprimido / tamaño_original) * 100
        
        return {
            'archivo': ruta_entrada.name,
            'tamaño_original': tamaño_original,
            'tamaño_comprimido': tamaño_comprimido,
            'ratio': ratio,
            'exito': True
        }
    
    except Exception as e:
        return {
            'archivo': ruta_entrada.name,
            'error': str(e),
            'exito': False
        }


def comprimir_secuencial(archivos):
    print("COMPRESION SECUENCIAL")
    print("=" * 50)
    
    inicio = time.time()
    resultados = []
    
    for i, archivo in enumerate(archivos, 1):
        print(f"Comprimiendo {i}/{len(archivos)}: {archivo.name}...", end=' ')
        resultado = comprimir_archivo(archivo)
        resultados.append(resultado)
        
        if resultado['exito']:
            print(f"OK ({resultado['ratio']:.1f}% reduccion)")
        else:
            print(f"Error: {resultado['error']}")
    
    duracion = time.time() - inicio
    
    print(f"\nTiempo total: {duracion:.2f}s")
    print(f"Promedio por archivo: {duracion/len(archivos):.2f}s\n")
    
    return resultados, duracion


def comprimir_paralelo(archivos, max_workers=None):
    print("COMPRESION PARALELA")
    print("=" * 50)
    
    if max_workers is None:
        import os
        max_workers = os.cpu_count()
    
    print(f"Usando {max_workers} procesos\n")
    
    inicio = time.time()
    resultados = []
    completados = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas
        future_to_archivo = {
            executor.submit(comprimir_archivo, archivo): archivo 
            for archivo in archivos
        }
        
        # Procesar según terminan
        for future in as_completed(future_to_archivo):
            archivo = future_to_archivo[future]
            completados += 1
            
            try:
                resultado = future.result()
                resultados.append(resultado)
                
                if resultado['exito']:
                    print(f"OK Comprimido {completados}/{len(archivos)}: {archivo.name} "
                          f"({resultado['ratio']:.1f}% reduccion)")
                else:
                    print(f"Error en {archivo.name}: {resultado['error']}")
                    
            except Exception as e:
                print(f"Excepcion procesando {archivo.name}: {e}")
    
    duracion = time.time() - inicio
    
    print(f"\nTiempo total: {duracion:.2f}s")
    print(f"Promedio por archivo: {duracion/len(archivos):.2f}s\n")
    
    return resultados, duracion


def calcular_estadisticas(resultados):
    exitosos = [r for r in resultados if r['exito']]
    
    if not exitosos:
        print("No hay resultados exitosos para analizar")
        return
    
    tamaño_original_total = sum(r['tamaño_original'] for r in exitosos)
    tamaño_comprimido_total = sum(r['tamaño_comprimido'] for r in exitosos)
    ratio_promedio = sum(r['ratio'] for r in exitosos) / len(exitosos)
    
    print("ESTADISTICAS DE COMPRESION")
    print("=" * 50)
    print(f"Archivos procesados: {len(exitosos)}/{len(resultados)}")
    print(f"Tamaño original total: {tamaño_original_total / 1024:.1f} KB")
    print(f"Tamaño comprimido total: {tamaño_comprimido_total / 1024:.1f} KB")
    print(f"Ratio de compresion promedio: {ratio_promedio:.1f}%")
    print(f"Espacio ahorrado: {(tamaño_original_total - tamaño_comprimido_total) / 1024:.1f} KB\n")


def limpiar_archivos(carpeta="archivos_prueba"):
    carpeta_path = Path(carpeta)
    if carpeta_path.exists():
        for archivo in carpeta_path.glob("*"):
            archivo.unlink()
        carpeta_path.rmdir()
        print(f"Archivos de prueba eliminados\n")


def main():
    print("\n" + "=" * 50)
    print("   COMPRESOR DE ARCHIVOS PARALELO")
    print("=" * 50 + "\n")
    
    # Configuración
    NUM_ARCHIVOS = 10
    TAMAÑO_KB = 200  # Archivos más grandes para ver diferencia
    
    # Crear archivos de prueba
    archivos = crear_archivos_prueba(NUM_ARCHIVOS, TAMAÑO_KB)
    
    # Compresión secuencial
    resultados_seq, tiempo_seq = comprimir_secuencial(archivos)
    calcular_estadisticas(resultados_seq)
    
    # Limpiar archivos .gz de la prueba secuencial
    for archivo in archivos:
        gz_file = archivo.with_suffix('.txt.gz')
        if gz_file.exists():
            gz_file.unlink()
    
    # Compresión paralela
    resultados_par, tiempo_par = comprimir_paralelo(archivos, max_workers=4)
    calcular_estadisticas(resultados_par)
    
    # Comparación final
    print("COMPARACION DE RENDIMIENTO")
    print("=" * 50)
    print(f"Tiempo secuencial: {tiempo_seq:.2f}s")
    print(f"Tiempo paralelo: {tiempo_par:.2f}s")
    
    if tiempo_par < tiempo_seq:
        speedup = tiempo_seq / tiempo_par
        print(f"Speedup: {speedup:.2f}x")
        mejora = ((tiempo_seq - tiempo_par) / tiempo_seq) * 100
        print(f"Mejora: {mejora:.1f}% mas rapido")
    else:
        print("La version paralela fue mas lenta (overhead de procesos)")
    
    print("\n" + "=" * 50)
    
    # Preguntar si quiere limpiar
    respuesta = input("\nEliminar archivos de prueba? (s/n): ").lower()
    if respuesta == 's':
        limpiar_archivos()
    else:
        print("Archivos guardados en carpeta 'archivos_prueba'\n")


if __name__ == "__main__":
    main()
```

## Ejercicio 2
```python
import dns.resolver
import time
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed


def generar_emails_prueba(cantidad=100):
    # Dominios reales con registros MX
    dominios_validos = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'icloud.com', 'protonmail.com', 'aol.com', 'zoho.com',
        'mail.com', 'yandex.com', 'gmx.com', 'fastmail.com'
    ]
    # Dominios que probablemente no existen
    dominios_invalidos = [
        'noexiste12345.com', 'fake-domain-xyz.net', 'invalid-email-test.org',
        'este-dominio-no-existe.com', 'fake-company-2024.io', 
        'no-real-domain-here.co', 'invalid-test-domain.info',
        'fake-email-provider.com', 'nonexistent-site.net'
    ]
    # Dominios que existen pero sin MX (serán no verificables)
    dominios_sin_mx = [
        'example.com', 'example.org', 'example.net',
        'localhost.local', 'test.local', 'internal.local'
    ]
    
    emails = []
    nombres = ['juan', 'maria', 'pedro', 'ana', 'carlos', 'laura', 'diego', 'sofia']
    
    # Generar emails mezclados
    for i in range(cantidad):
        nombre = random.choice(nombres)
        numero = random.randint(1, 999)
        
        # 50% válidos, 30% inválidos, 20% sin MX
        rand = random.random()
        if rand < 0.5:
            dominio = random.choice(dominios_validos)
            categoria = 'valido'
        elif rand < 0.8:
            dominio = random.choice(dominios_invalidos)
            categoria = 'invalido'
        else:
            dominio = random.choice(dominios_sin_mx)
            categoria = 'sin_mx'
        
        email = f"{nombre}{numero}@{dominio}"
        emails.append({'email': email, 'categoria_real': categoria})
    
    return emails


def verificar_email(email_data, timeout=5):
    email = email_data['email']
    inicio = time.time()
    
    try:
        # Validación básica de formato
        if '@' not in email or email.count('@') != 1:
            return {
                'email': email,
                'estado': 'invalido',
                'razon': 'formato_invalido',
                'tiempo': time.time() - inicio
            }
        
        # Extraer dominio
        dominio = email.split('@')[1]
        
        if not dominio:
            return {
                'email': email,
                'estado': 'invalido',
                'razon': 'dominio_vacio',
                'tiempo': time.time() - inicio
            }
        
        # Configurar resolver con timeout
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        
        # Intentar resolver registros MX
        try:
            respuesta = resolver.resolve(dominio, 'MX')
            mx_records = [str(r.exchange) for r in respuesta]
            
            return {
                'email': email,
                'estado': 'valido',
                'razon': f'{len(mx_records)} servidores MX encontrados',
                'tiempo': time.time() - inicio,
                'mx_servers': mx_records[:3]  # Primeros 3
            }
        
        except dns.resolver.NoAnswer:
            # El dominio existe pero no tiene registros MX
            return {
                'email': email,
                'estado': 'no_verificable',
                'razon': 'dominio_sin_mx',
                'tiempo': time.time() - inicio
            }
        
        except dns.resolver.NXDOMAIN:
            # El dominio no existe
            return {
                'email': email,
                'estado': 'invalido',
                'razon': 'dominio_no_existe',
                'tiempo': time.time() - inicio
            }
        
        except dns.resolver.Timeout:
            return {
                'email': email,
                'estado': 'no_verificable',
                'razon': 'timeout_dns',
                'tiempo': time.time() - inicio
            }
    
    except Exception as e:
        return {
            'email': email,
            'estado': 'no_verificable',
            'razon': f'error: {type(e).__name__}',
            'tiempo': time.time() - inicio
        }


def validar_secuencial(emails_data, timeout=5):
    print("\nVALIDACION SECUENCIAL")
    print("=" * 70)
    
    inicio = time.time()
    resultados = []
    
    for i, email_data in enumerate(emails_data, 1):
        print(f"Verificando {i}/{len(emails_data)}: {email_data['email'][:40]}...", end=' ')
        
        resultado = verificar_email(email_data, timeout)
        resultados.append(resultado)
        
        print(f"{resultado['estado']} ({resultado['tiempo']:.2f}s)")
    
    duracion = time.time() - inicio
    
    print(f"\nTiempo total: {duracion:.2f}s")
    print(f"Promedio por email: {duracion/len(emails_data):.2f}s\n")
    
    return resultados, duracion


def validar_concurrente(emails_data, max_workers=20, timeout=5):
    print("\nVALIDACION CONCURRENTE")
    print("=" * 70)
    print(f"Usando {max_workers} threads\n")
    
    inicio = time.time()
    resultados = []
    completados = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas
        future_to_email = {
            executor.submit(verificar_email, email_data, timeout): email_data
            for email_data in emails_data
        }
        
        # Procesar según terminan con timeout global
        try:
            for future in as_completed(future_to_email, timeout=len(emails_data) * timeout):
                email_data = future_to_email[future]
                completados += 1
                
                try:
                    # Timeout individual por tarea
                    resultado = future.result(timeout=timeout)
                    resultados.append(resultado)
                    
                    # Mostrar progreso cada 10 emails
                    if completados % 10 == 0 or completados == len(emails_data):
                        print(f"Progreso: {completados}/{len(emails_data)} emails verificados")
                    
                except TimeoutError:
                    # Timeout en la verificación individual
                    resultados.append({
                        'email': email_data['email'],
                        'estado': 'no_verificable',
                        'razon': 'timeout_operacion',
                        'tiempo': timeout
                    })
                    print(f"Timeout en: {email_data['email']}")
                
                except Exception as e:
                    # Error inesperado
                    resultados.append({
                        'email': email_data['email'],
                        'estado': 'no_verificable',
                        'razon': f'error_excepcion: {type(e).__name__}',
                        'tiempo': 0
                    })
                    print(f"Error en: {email_data['email']} - {e}")
        
        except TimeoutError:
            print(f"\nTimeout global alcanzado. Procesados: {completados}/{len(emails_data)}")
    
    duracion = time.time() - inicio
    
    print(f"\nTiempo total: {duracion:.2f}s")
    print(f"Promedio por email: {duracion/len(emails_data):.2f}s\n")
    
    return resultados, duracion


def clasificar_resultados(resultados):
    print("\nESTADISTICAS DE VALIDACION")
    print("=" * 70)
    
    # Clasificar por estado
    validos = [r for r in resultados if r['estado'] == 'valido']
    invalidos = [r for r in resultados if r['estado'] == 'invalido']
    no_verificables = [r for r in resultados if r['estado'] == 'no_verificable']
    
    total = len(resultados)
    
    print(f"Total de emails procesados: {total}")
    print(f"\nClasificacion:")
    print(f"  Validos:         {len(validos):3d} ({len(validos)/total*100:5.1f}%)")
    print(f"  Invalidos:       {len(invalidos):3d} ({len(invalidos)/total*100:5.1f}%)")
    print(f"  No verificables: {len(no_verificables):3d} ({len(no_verificables)/total*100:5.1f}%)")
    
    # Estadísticas de tiempo
    tiempos = [r['tiempo'] for r in resultados]
    if tiempos:
        print(f"\nTiempos de verificacion:")
        print(f"  Promedio: {sum(tiempos)/len(tiempos):.3f}s")
        print(f"  Minimo:   {min(tiempos):.3f}s")
        print(f"  Maximo:   {max(tiempos):.3f}s")
    
    # Razones de no verificables
    if no_verificables:
        print(f"\nRazones de no verificables:")
        razones = {}
        for r in no_verificables:
            razon = r.get('razon', 'desconocido')
            razones[razon] = razones.get(razon, 0) + 1
        
        for razon, cantidad in sorted(razones.items(), key=lambda x: x[1], reverse=True):
            print(f"  {razon}: {cantidad}")
    
    # Ejemplos de emails válidos
    if validos:
        print(f"\nEjemplos de emails validos:")
        for r in validos[:5]:
            mx_info = f" (MX: {r.get('mx_servers', ['N/A'])[0]})" if 'mx_servers' in r else ""
            print(f"  {r['email']}{mx_info}")
    
    # Ejemplos de emails inválidos
    if invalidos:
        print(f"\nEjemplos de emails invalidos:")
        for r in invalidos[:5]:
            print(f"  {r['email']} - {r.get('razon', 'N/A')}")
    
    print()
    
    return {
        'validos': validos,
        'invalidos': invalidos,
        'no_verificables': no_verificables
    }


def main():
    print("\n" + "=" * 70)
    print("   VALIDADOR DE EMAILS CONCURRENTE")
    print("=" * 70)
    
    # Configuración
    NUM_EMAILS = 100
    MAX_WORKERS = 20
    TIMEOUT = 5
    
    # Generar emails de prueba
    print(f"\nGenerando {NUM_EMAILS} emails de prueba...")
    emails_data = generar_emails_prueba(NUM_EMAILS)
    print(f"Emails generados: {NUM_EMAILS}")
    print(f"  ~ 50% con dominios validos")
    print(f"  ~ 30% con dominios invalidos")
    print(f"  ~ 20% con dominios sin MX")
    
    # Validación secuencial (solo muestra de 10 para comparación)
    print("\n" + "=" * 70)
    print("COMPARACION: Procesando muestra de 10 emails")
    print("=" * 70)
    
    muestra = emails_data[:10]
    resultados_seq, tiempo_seq = validar_secuencial(muestra, TIMEOUT)
    
    # Validación concurrente (todos los emails)
    print("\n" + "=" * 70)
    print(f"VALIDACION COMPLETA: Procesando {NUM_EMAILS} emails")
    print("=" * 70)
    
    resultados_con, tiempo_con = validar_concurrente(
        emails_data, 
        max_workers=MAX_WORKERS,
        timeout=TIMEOUT
    )
    
    # Clasificar y mostrar resultados
    clasificacion = clasificar_resultados(resultados_con)
    
    # Comparación de rendimiento (extrapolado)
    print("\nCOMPARACION DE RENDIMIENTO")
    print("=" * 70)
    
    tiempo_seq_estimado = (tiempo_seq / len(muestra)) * NUM_EMAILS
    
    print(f"Tiempo secuencial (estimado): {tiempo_seq_estimado:.2f}s")
    print(f"Tiempo concurrente (real):    {tiempo_con:.2f}s")
    
    if tiempo_con < tiempo_seq_estimado:
        speedup = tiempo_seq_estimado / tiempo_con
        print(f"Speedup: {speedup:.2f}x")
        mejora = ((tiempo_seq_estimado - tiempo_con) / tiempo_seq_estimado) * 100
        print(f"Mejora: {mejora:.1f}% mas rapido")
    
    print("\n" + "=" * 70)
    
    # Opción de exportar resultados
    respuesta = input("\nExportar resultados a archivo? (s/n): ").lower()
    if respuesta == 's':
        exportar_resultados(resultados_con, clasificacion)


def exportar_resultados(resultados, clasificacion):
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Archivo con todos los resultados
    with open(f'validacion_emails_{timestamp}.txt', 'w', encoding='utf-8') as f:
        f.write("RESULTADOS DE VALIDACION DE EMAILS\n")
        f.write("=" * 70 + "\n\n")
        
        for r in resultados:
            f.write(f"Email: {r['email']}\n")
            f.write(f"Estado: {r['estado']}\n")
            f.write(f"Razon: {r.get('razon', 'N/A')}\n")
            f.write(f"Tiempo: {r['tiempo']:.3f}s\n")
            if 'mx_servers' in r:
                f.write(f"MX Servers: {', '.join(r['mx_servers'])}\n")
            f.write("-" * 70 + "\n")
    
    # Archivo solo con válidos
    with open(f'emails_validos_{timestamp}.txt', 'w', encoding='utf-8') as f:
        for r in clasificacion['validos']:
            f.write(f"{r['email']}\n")
    
    print(f"\nArchivos exportados:")
    print(f"  - validacion_emails_{timestamp}.txt")
    print(f"  - emails_validos_{timestamp}.txt")


if __name__ == "__main__":
    main()
```

## Ejercicio 3
```python
import time
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict


def es_primo_simple(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def criba_eratostenes_rango(inicio, fin):
    if fin <= 2:
        return []
    
    # Ajustar inicio al primer número impar >= inicio
    if inicio <= 2:
        primos = [2]
        inicio = 3
    else:
        primos = []
        if inicio % 2 == 0:
            inicio += 1
    
    # Crear array booleano para números impares en el rango
    # Solo necesitamos verificar impares (optimización)
    tamaño = (fin - inicio) // 2 + 1
    es_primo_arr = [True] * tamaño
    
    # Función helper para convertir índice a número
    def idx_a_num(idx):
        return inicio + idx * 2
    
    def num_a_idx(num):
        return (num - inicio) // 2
    
    # Necesitamos primos hasta sqrt(fin) para cribar
    limite_criba = int(math.sqrt(fin)) + 1
    
    # Generar primos base hasta el límite
    primos_base = []
    for i in range(3, limite_criba, 2):
        if es_primo_simple(i):
            primos_base.append(i)
    
    # Cribar el rango usando los primos base
    for primo in primos_base:
        # Encontrar el primer múltiplo de primo >= inicio
        primer_multiplo = ((inicio + primo - 1) // primo) * primo
        if primer_multiplo % 2 == 0:
            primer_multiplo += primo
        
        # Marcar todos los múltiplos impares como no primos
        if primer_multiplo >= inicio:
            idx_inicio = num_a_idx(primer_multiplo)
            for idx in range(idx_inicio, tamaño, primo):
                es_primo_arr[idx] = False
    
    # Recolectar números primos
    for idx in range(tamaño):
        if es_primo_arr[idx]:
            primos.append(idx_a_num(idx))
    
    return primos


def encontrar_primos_simple(inicio, fin):
    return [n for n in range(inicio, fin) if es_primo_simple(n)]


def procesar_chunk(chunk_data):
    chunk_id, inicio, fin, usar_criba = chunk_data
    
    inicio_tiempo = time.time()
    
    # Usar algoritmo según configuración
    if usar_criba:
        primos = criba_eratostenes_rango(inicio, fin)
    else:
        primos = encontrar_primos_simple(inicio, fin)
    
    tiempo = time.time() - inicio_tiempo
    
    return {
        'chunk_id': chunk_id,
        'inicio': inicio,
        'fin': fin,
        'cantidad_primos': len(primos),
        'primos': primos,  # Guardamos los primos para validación
        'tiempo': tiempo,
        'numeros_procesados': fin - inicio
    }


def calcular_primos_secuencial(rango_inicio, rango_fin, tamaño_chunk, usar_criba=True):
    print("\nCALCULO SECUENCIAL")
    print("=" * 70)
    
    inicio = time.time()
    
    # Dividir en chunks
    chunks = []
    for i, start in enumerate(range(rango_inicio, rango_fin, tamaño_chunk)):
        end = min(start + tamaño_chunk, rango_fin)
        chunks.append((i, start, end, usar_criba))
    
    print(f"Procesando {len(chunks)} chunks secuencialmente...")
    print(f"Algoritmo: {'Criba de Eratostenes' if usar_criba else 'Verificacion simple'}\n")
    
    # Procesar chunks
    resultados = []
    for i, chunk in enumerate(chunks, 1):
        if i % 10 == 0 or i == len(chunks):
            print(f"Procesando chunk {i}/{len(chunks)}...", end='\r')
        resultado = procesar_chunk(chunk)
        resultados.append(resultado)
    
    duracion = time.time() - inicio
    
    print(f"\nTiempo total: {duracion:.2f}s")
    print(f"Promedio por chunk: {duracion/len(chunks):.3f}s\n")
    
    return resultados, duracion


def calcular_primos_paralelo(rango_inicio, rango_fin, tamaño_chunk, max_workers=None, usar_criba=True):
    print("\nCALCULO PARALELO")
    print("=" * 70)
    
    if max_workers is None:
        import os
        max_workers = os.cpu_count()
    
    print(f"Usando {max_workers} procesos")
    
    inicio = time.time()
    
    # Dividir en chunks
    chunks = []
    for i, start in enumerate(range(rango_inicio, rango_fin, tamaño_chunk)):
        end = min(start + tamaño_chunk, rango_fin)
        chunks.append((i, start, end, usar_criba))
    
    print(f"Procesando {len(chunks)} chunks en paralelo...")
    print(f"Algoritmo: {'Criba de Eratostenes' if usar_criba else 'Verificacion simple'}\n")
    
    resultados = []
    completados = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todos los chunks
        future_to_chunk = {
            executor.submit(procesar_chunk, chunk): chunk
            for chunk in chunks
        }
        
        # Procesar según terminan
        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            completados += 1
            
            try:
                resultado = future.result()
                resultados.append(resultado)
                
                # Mostrar progreso
                if completados % 10 == 0 or completados == len(chunks):
                    print(f"Progreso: {completados}/{len(chunks)} chunks completados", end='\r')
            
            except Exception as e:
                print(f"\nError procesando chunk {chunk[0]}: {e}")
    
    print()  # Nueva línea después del progreso
    
    duracion = time.time() - inicio
    
    print(f"\nTiempo total: {duracion:.2f}s")
    print(f"Promedio por chunk: {duracion/len(chunks):.3f}s\n")
    
    return resultados, duracion


def analizar_resultados(resultados, rango_inicio, rango_fin):
    print("\nESTADISTICAS")
    print("=" * 70)
    
    # Consolidar todos los primos
    todos_los_primos = []
    for r in sorted(resultados, key=lambda x: x['chunk_id']):
        todos_los_primos.extend(r['primos'])
    
    # Estadísticas generales
    total_primos = len(todos_los_primos)
    total_numeros = rango_fin - rango_inicio
    porcentaje = (total_primos / total_numeros) * 100
    
    print(f"Rango analizado: {rango_inicio:,} a {rango_fin:,}")
    print(f"Total de numeros: {total_numeros:,}")
    print(f"Primos encontrados: {total_primos:,} ({porcentaje:.2f}%)")
    
    # Estadísticas de chunks
    tiempos_chunks = [r['tiempo'] for r in resultados]
    primos_por_chunk = [r['cantidad_primos'] for r in resultados]
    
    print(f"\nEstadisticas de chunks:")
    print(f"  Chunks procesados: {len(resultados)}")
    print(f"  Tiempo promedio por chunk: {sum(tiempos_chunks)/len(tiempos_chunks):.3f}s")
    print(f"  Chunk mas rapido: {min(tiempos_chunks):.3f}s")
    print(f"  Chunk mas lento: {max(tiempos_chunks):.3f}s")
    print(f"  Primos por chunk (promedio): {sum(primos_por_chunk)/len(primos_por_chunk):.1f}")
    
    # Primeros y últimos primos
    if total_primos > 0:
        print(f"\nPrimeros 10 primos encontrados:")
        print(f"  {todos_los_primos[:10]}")
        
        print(f"\nUltimos 10 primos encontrados:")
        print(f"  {todos_los_primos[-10:]}")
        
        # Algunos primos famosos
        primos_famosos = {
            104729: "Primo 10,000",
            1299709: "Primo 100,000"
        }
        
        encontrados = [p for p in primos_famosos.keys() if p in todos_los_primos]
        if encontrados:
            print(f"\nPrimos famosos encontrados:")
            for p in encontrados:
                print(f"  {p:,} - {primos_famosos[p]}")
    
    print()
    
    return todos_los_primos


def comparar_algoritmos(rango_inicio, rango_fin, tamaño_chunk):
    print("\nCOMPARACION DE ALGORITMOS")
    print("=" * 70)
    
    muestra_fin = min(rango_inicio + 100000, rango_fin)  # Muestra de 100k
    
    print(f"Comparando algoritmos en rango {rango_inicio:,} a {muestra_fin:,}\n")
    
    # Algoritmo simple
    print("1. Verificacion simple (secuencial):")
    inicio = time.time()
    primos_simple = encontrar_primos_simple(rango_inicio, muestra_fin)
    tiempo_simple = time.time() - inicio
    print(f"   Tiempo: {tiempo_simple:.2f}s")
    print(f"   Primos encontrados: {len(primos_simple):,}")
    
    # Criba de Eratóstenes
    print("\n2. Criba de Eratostenes (secuencial):")
    inicio = time.time()
    primos_criba = criba_eratostenes_rango(rango_inicio, muestra_fin)
    tiempo_criba = time.time() - inicio
    print(f"   Tiempo: {tiempo_criba:.2f}s")
    print(f"   Primos encontrados: {len(primos_criba):,}")
    
    # Verificar que dan los mismos resultados
    if sorted(primos_simple) == sorted(primos_criba):
        print("\n   Verificacion: Ambos algoritmos dan el mismo resultado")
        speedup = tiempo_simple / tiempo_criba
        print(f"   Speedup de Criba: {speedup:.2f}x mas rapido")
    else:
        print("\n   ERROR: Los algoritmos dan resultados diferentes!")
    
    print()


def main():
    print("\n" + "=" * 70)
    print("   CALCULADORA DE NUMEROS PRIMOS DISTRIBUIDA")
    print("=" * 70)
    
    # Configuración
    RANGO_INICIO = 1
    RANGO_FIN = 1_000_000
    TAMAÑO_CHUNK = 10_000  # 100 chunks de 10,000 números
    MAX_WORKERS = None  # Usa cpu_count()
    
    print(f"\nConfiguracion:")
    print(f"  Rango: {RANGO_INICIO:,} a {RANGO_FIN:,}")
    print(f"  Tamaño de chunk: {TAMAÑO_CHUNK:,} numeros")
    print(f"  Chunks totales: {(RANGO_FIN - RANGO_INICIO) // TAMAÑO_CHUNK}")
    
    # Comparar algoritmos primero (opcional)
    respuesta = input("\nComparar algoritmos primero? (s/n): ").lower()
    if respuesta == 's':
        comparar_algoritmos(RANGO_INICIO, RANGO_FIN, TAMAÑO_CHUNK)
    
    # Cálculo secuencial (muestra pequeña)
    print("\n" + "=" * 70)
    print("MUESTRA SECUENCIAL (primeros 100,000 numeros)")
    print("=" * 70)
    
    muestra_fin = min(RANGO_INICIO + 100_000, RANGO_FIN)
    resultados_seq, tiempo_seq = calcular_primos_secuencial(
        RANGO_INICIO, 
        muestra_fin,
        TAMAÑO_CHUNK,
        usar_criba=True
    )
    analizar_resultados(resultados_seq, RANGO_INICIO, muestra_fin)
    
    # Cálculo paralelo (rango completo)
    print("\n" + "=" * 70)
    print("CALCULO COMPLETO EN PARALELO")
    print("=" * 70)
    
    resultados_par, tiempo_par = calcular_primos_paralelo(
        RANGO_INICIO,
        RANGO_FIN,
        TAMAÑO_CHUNK,
        max_workers=MAX_WORKERS,
        usar_criba=True
    )
    todos_los_primos = analizar_resultados(resultados_par, RANGO_INICIO, RANGO_FIN)
    
    # Comparación de rendimiento
    print("\nCOMPARACION DE RENDIMIENTO")
    print("=" * 70)
    
    # Extrapolar tiempo secuencial
    tiempo_seq_estimado = (tiempo_seq / (muestra_fin - RANGO_INICIO)) * (RANGO_FIN - RANGO_INICIO)
    
    print(f"Tiempo secuencial (estimado): {tiempo_seq_estimado:.2f}s ({tiempo_seq_estimado/60:.1f} min)")
    print(f"Tiempo paralelo (real):       {tiempo_par:.2f}s ({tiempo_par/60:.1f} min)")
    
    if tiempo_par < tiempo_seq_estimado:
        speedup = tiempo_seq_estimado / tiempo_par
        print(f"\nSpeedup: {speedup:.2f}x")
        mejora = ((tiempo_seq_estimado - tiempo_par) / tiempo_seq_estimado) * 100
        print(f"Mejora: {mejora:.1f}% mas rapido")
        tiempo_ahorrado = tiempo_seq_estimado - tiempo_par
        print(f"Tiempo ahorrado: {tiempo_ahorrado:.1f}s ({tiempo_ahorrado/60:.1f} min)")
    
    print("\n" + "=" * 70)
    
    # Opción de guardar resultados
    respuesta = input("\nGuardar lista de primos en archivo? (s/n): ").lower()
    if respuesta == 's':
        guardar_primos(todos_los_primos, RANGO_INICIO, RANGO_FIN)


def guardar_primos(primos, rango_inicio, rango_fin):
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f'primos_{rango_inicio}_{rango_fin}_{timestamp}.txt'
    
    with open(nombre_archivo, 'w') as f:
        f.write(f"Numeros primos de {rango_inicio:,} a {rango_fin:,}\n")
        f.write(f"Total: {len(primos):,} primos\n")
        f.write("=" * 70 + "\n\n")
        
        # Escribir 10 primos por línea
        for i in range(0, len(primos), 10):
            linea = ', '.join(str(p) for p in primos[i:i+10])
            f.write(linea + '\n')
    
    print(f"\nPrimos guardados en: {nombre_archivo}")
    print(f"Total de primos: {len(primos):,}")


if __name__ == "__main__":
    main()
```

## Ejercicio 4
```python
import psutil
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from datetime import datetime
import signal
import sys


# Event global para señalizar detención
detenerse = threading.Event()

# Diccionario compartido para almacenar resultados (thread-safe con lock)
resultados_lock = threading.Lock()
resultados = {
    'cpu': [],
    'memoria': [],
    'disco': []
}


def monitorear_cpu(intervalo=5):
    print("[CPU Monitor] Iniciado")
    
    while not detenerse.is_set():
        try:
            # Obtener porcentaje de CPU (promedio de 1 segundo)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Obtener uso por core
            cpu_per_core = psutil.cpu_percent(interval=0, percpu=True)
            
            # Obtener frecuencia (si está disponible)
            try:
                freq = psutil.cpu_freq()
                freq_actual = freq.current if freq else None
            except:
                freq_actual = None
            
            # Timestamp
            timestamp = datetime.now()
            
            # Guardar datos (con lock para thread-safety)
            with resultados_lock:
                resultados['cpu'].append({
                    'timestamp': timestamp,
                    'porcentaje': cpu_percent,
                    'por_core': cpu_per_core,
                    'frecuencia_mhz': freq_actual
                })
            
            # Esperar antes de la próxima lectura
            # Usamos wait() en lugar de sleep() para responder a detenerse
            if not detenerse.wait(intervalo - 1):  # -1 porque cpu_percent ya tomó 1s
                continue
            else:
                break
                
        except Exception as e:
            print(f"[CPU Monitor] Error: {e}")
            if not detenerse.wait(intervalo):
                continue
            else:
                break
    
    print("[CPU Monitor] Detenido")


def monitorear_memoria(intervalo=5):
    print("[Memoria Monitor] Iniciado")
    
    while not detenerse.is_set():
        try:
            # Obtener información de memoria virtual (RAM)
            mem = psutil.virtual_memory()
            
            # Obtener información de swap
            swap = psutil.swap_memory()
            
            # Timestamp
            timestamp = datetime.now()
            
            # Guardar datos
            with resultados_lock:
                resultados['memoria'].append({
                    'timestamp': timestamp,
                    'total_gb': mem.total / (1024**3),
                    'usado_gb': mem.used / (1024**3),
                    'disponible_gb': mem.available / (1024**3),
                    'porcentaje': mem.percent,
                    'swap_usado_gb': swap.used / (1024**3),
                    'swap_porcentaje': swap.percent
                })
            
            # Esperar
            if detenerse.wait(intervalo):
                break
                
        except Exception as e:
            print(f"[Memoria Monitor] Error: {e}")
            if detenerse.wait(intervalo):
                break
    
    print("[Memoria Monitor] Detenido")


def monitorear_disco(intervalo=5):
    print("[Disco Monitor] Iniciado")
    
    # Obtener punto de montaje principal
    # En Windows: "C:\", en Unix: "/"
    punto_montaje = "/" if sys.platform != "win32" else "C:\\"
    
    while not detenerse.is_set():
        try:
            # Obtener información de disco
            disco = psutil.disk_usage(punto_montaje)
            
            # Obtener I/O de disco (lecturas/escrituras)
            try:
                io = psutil.disk_io_counters()
                read_mb = io.read_bytes / (1024**2) if io else None
                write_mb = io.write_bytes / (1024**2) if io else None
            except:
                read_mb = None
                write_mb = None
            
            # Timestamp
            timestamp = datetime.now()
            
            # Guardar datos
            with resultados_lock:
                resultados['disco'].append({
                    'timestamp': timestamp,
                    'total_gb': disco.total / (1024**3),
                    'usado_gb': disco.used / (1024**3),
                    'libre_gb': disco.free / (1024**3),
                    'porcentaje': disco.percent,
                    'read_mb_total': read_mb,
                    'write_mb_total': write_mb,
                    'punto_montaje': punto_montaje
                })
            
            # Esperar
            if detenerse.wait(intervalo):
                break
                
        except Exception as e:
            print(f"[Disco Monitor] Error: {e}")
            if detenerse.wait(intervalo):
                break
    
    print("[Disco Monitor] Detenido")


def calcular_promedios():
    with resultados_lock:
        # CPU
        if resultados['cpu']:
            cpu_promedio = sum(r['porcentaje'] for r in resultados['cpu']) / len(resultados['cpu'])
            cpu_max = max(r['porcentaje'] for r in resultados['cpu'])
            cpu_min = min(r['porcentaje'] for r in resultados['cpu'])
            cpu_lecturas = len(resultados['cpu'])
        else:
            cpu_promedio = cpu_max = cpu_min = cpu_lecturas = 0
        
        # Memoria
        if resultados['memoria']:
            mem_promedio = sum(r['porcentaje'] for r in resultados['memoria']) / len(resultados['memoria'])
            mem_max = max(r['porcentaje'] for r in resultados['memoria'])
            mem_min = min(r['porcentaje'] for r in resultados['memoria'])
            mem_lecturas = len(resultados['memoria'])
            mem_usado_promedio = sum(r['usado_gb'] for r in resultados['memoria']) / len(resultados['memoria'])
        else:
            mem_promedio = mem_max = mem_min = mem_lecturas = mem_usado_promedio = 0
        
        # Disco
        if resultados['disco']:
            disco_promedio = sum(r['porcentaje'] for r in resultados['disco']) / len(resultados['disco'])
            disco_max = max(r['porcentaje'] for r in resultados['disco'])
            disco_min = min(r['porcentaje'] for r in resultados['disco'])
            disco_lecturas = len(resultados['disco'])
            disco_usado_promedio = sum(r['usado_gb'] for r in resultados['disco']) / len(resultados['disco'])
        else:
            disco_promedio = disco_max = disco_min = disco_lecturas = disco_usado_promedio = 0
    
    return {
        'cpu': {
            'promedio': cpu_promedio,
            'max': cpu_max,
            'min': cpu_min,
            'lecturas': cpu_lecturas
        },
        'memoria': {
            'promedio': mem_promedio,
            'max': mem_max,
            'min': mem_min,
            'lecturas': mem_lecturas,
            'usado_gb': mem_usado_promedio
        },
        'disco': {
            'promedio': disco_promedio,
            'max': disco_max,
            'min': disco_min,
            'lecturas': disco_lecturas,
            'usado_gb': disco_usado_promedio
        }
    }


def mostrar_reporte(promedios):
    print("\n" + "=" * 70)
    print(f"REPORTE DE RECURSOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # CPU
    cpu = promedios['cpu']
    print(f"\nCPU:")
    print(f"  Uso promedio: {cpu['promedio']:5.1f}%")
    print(f"  Uso minimo:   {cpu['min']:5.1f}%")
    print(f"  Uso maximo:   {cpu['max']:5.1f}%")
    print(f"  Lecturas:     {cpu['lecturas']}")
    
    # Barra de progreso visual
    barra_cpu = '█' * int(cpu['promedio'] / 10) + '░' * (10 - int(cpu['promedio'] / 10))
    print(f"  [{barra_cpu}] {cpu['promedio']:.1f}%")
    
    # Memoria
    mem = promedios['memoria']
    print(f"\nMemoria RAM:")
    print(f"  Uso promedio: {mem['promedio']:5.1f}% ({mem['usado_gb']:.2f} GB)")
    print(f"  Uso minimo:   {mem['min']:5.1f}%")
    print(f"  Uso maximo:   {mem['max']:5.1f}%")
    print(f"  Lecturas:     {mem['lecturas']}")
    
    barra_mem = '█' * int(mem['promedio'] / 10) + '░' * (10 - int(mem['promedio'] / 10))
    print(f"  [{barra_mem}] {mem['promedio']:.1f}%")
    
    # Disco
    disco = promedios['disco']
    print(f"\nDisco:")
    print(f"  Uso promedio: {disco['promedio']:5.1f}% ({disco['usado_gb']:.2f} GB)")
    print(f"  Uso minimo:   {disco['min']:5.1f}%")
    print(f"  Uso maximo:   {disco['max']:5.1f}%")
    print(f"  Lecturas:     {disco['lecturas']}")
    
    barra_disco = '█' * int(disco['promedio'] / 10) + '░' * (10 - int(disco['promedio'] / 10))
    print(f"  [{barra_disco}] {disco['promedio']:.1f}%")
    
    print("\n" + "=" * 70)


def mostrar_info_sistema():
    print("\nINFORMACION DEL SISTEMA")
    print("=" * 70)
    
    # CPU
    print(f"CPU:")
    print(f"  Cores fisicos: {psutil.cpu_count(logical=False)}")
    print(f"  Cores logicos: {psutil.cpu_count(logical=True)}")
    
    # Memoria
    mem = psutil.virtual_memory()
    print(f"\nMemoria RAM:")
    print(f"  Total: {mem.total / (1024**3):.2f} GB")
    
    # Disco
    punto_montaje = "/" if sys.platform != "win32" else "C:\\"
    disco = psutil.disk_usage(punto_montaje)
    print(f"\nDisco ({punto_montaje}):")
    print(f"  Total: {disco.total / (1024**3):.2f} GB")
    print(f"  Usado: {disco.used / (1024**3):.2f} GB")
    print(f"  Libre: {disco.free / (1024**3):.2f} GB")
    
    print("=" * 70 + "\n")


def limpiar_datos_antiguos(limite_lecturas=100):
    with resultados_lock:
        for clave in resultados:
            if len(resultados[clave]) > limite_lecturas:
                resultados[clave] = resultados[clave][-limite_lecturas:]


def exportar_datos(nombre_archivo=None):
    if nombre_archivo is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"monitor_recursos_{timestamp}.csv"
    
    with resultados_lock:
        with open(nombre_archivo, 'w') as f:
            # Cabecera
            f.write("Timestamp,Tipo,Metrica,Valor\n")
            
            # CPU
            for r in resultados['cpu']:
                ts = r['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{ts},CPU,Porcentaje,{r['porcentaje']}\n")
            
            # Memoria
            for r in resultados['memoria']:
                ts = r['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{ts},Memoria,Porcentaje,{r['porcentaje']}\n")
                f.write(f"{ts},Memoria,Usado_GB,{r['usado_gb']}\n")
            
            # Disco
            for r in resultados['disco']:
                ts = r['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{ts},Disco,Porcentaje,{r['porcentaje']}\n")
                f.write(f"{ts},Disco,Usado_GB,{r['usado_gb']}\n")
    
    print(f"\nDatos exportados a: {nombre_archivo}")


def signal_handler(sig, frame):
    print("\n\n[Sistema] Señal de interrupcion recibida (Ctrl+C)")
    print("[Sistema] Deteniendo monitores...")
    detenerse.set()


def main():
    print("\n" + "=" * 70)
    print("   MONITOR DE RECURSOS DEL SISTEMA")
    print("=" * 70)
    
    # Configurar manejador de señales para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Mostrar información del sistema
    mostrar_info_sistema()
    
    # Configuración
    INTERVALO_MONITOREO = 5  # segundos entre lecturas
    INTERVALO_REPORTE = 30   # segundos entre reportes
    MAX_WORKERS = 3          # 3 threads: CPU, Memoria, Disco
    
    print(f"Configuracion:")
    print(f"  Intervalo de monitoreo: {INTERVALO_MONITOREO}s")
    print(f"  Intervalo de reporte:   {INTERVALO_REPORTE}s")
    print(f"  Workers (threads):      {MAX_WORKERS}")
    print(f"\nPresiona Ctrl+C para detener el monitoreo\n")
    
    input("Presiona Enter para iniciar el monitoreo...")
    print()
    
    # Iniciar ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="Monitor") as executor:
        # Enviar las tres funciones de monitoreo
        future_cpu = executor.submit(monitorear_cpu, INTERVALO_MONITOREO)
        future_mem = executor.submit(monitorear_memoria, INTERVALO_MONITOREO)
        future_disco = executor.submit(monitorear_disco, INTERVALO_MONITOREO)
        
        print("[Sistema] Monitores iniciados\n")
        
        # Loop principal: mostrar reportes cada INTERVALO_REPORTE segundos
        try:
            contador_reportes = 0
            while not detenerse.is_set():
                # Esperar intervalo de reporte
                if detenerse.wait(INTERVALO_REPORTE):
                    break
                
                # Calcular y mostrar promedios
                contador_reportes += 1
                promedios = calcular_promedios()
                mostrar_reporte(promedios)
                
                # Limpiar datos antiguos cada 5 reportes
                if contador_reportes % 5 == 0:
                    limpiar_datos_antiguos()
                    print("[Sistema] Datos antiguos limpiados")
        
        except KeyboardInterrupt:
            # Esto no debería ejecutarse si signal_handler funciona
            print("\n[Sistema] Interrupcion detectada")
            detenerse.set()
        
        finally:
            # Asegurar que los threads se detengan
            print("\n[Sistema] Esperando que los monitores terminen...")
            detenerse.set()
            
            # Los futures se completarán cuando los threads terminen
            # El context manager esperará automáticamente
    
    # Mostrar reporte final
    print("\n[Sistema] Todos los monitores detenidos")
    print("\nGenerando reporte final...")
    promedios_finales = calcular_promedios()
    mostrar_reporte(promedios_finales)
    
    # Preguntar si quiere exportar
    try:
        respuesta = input("\nExportar datos a CSV? (s/n): ").lower()
        if respuesta == 's':
            exportar_datos()
    except:
        pass
    
    print("\n[Sistema] Monitor finalizado correctamente\n")


if __name__ == "__main__":
    main()
```

## Eejrcicio 5
```python
import queue
import hashlib
import requests
import time
import logging
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse


class DownloadQueue:
    # Niveles de prioridad
    PRIORIDAD_ALTA = 0
    PRIORIDAD_MEDIA = 1
    PRIORIDAD_BAJA = 2
    
    def __init__(self, max_workers=5, carpeta_destino="descargas", max_reintentos=3):
        self.queue = queue.PriorityQueue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Downloader")
        self.carpeta_destino = Path(carpeta_destino)
        self.carpeta_destino.mkdir(exist_ok=True)
        self.max_reintentos = max_reintentos
        
        # Control de estado
        self.activo = False
        self.lock = threading.Lock()
        self.contador_tareas = 0
        
        # Estadísticas
        self.stats = {
            'exitosas': 0,
            'fallidas': 0,
            'total_bytes': 0,
            'reintentos': 0
        }
        
        # Configurar logging
        self._configurar_logging()
        
        self.logger.info("DownloadQueue inicializado con %d workers", max_workers)
    
    def _configurar_logging(self):
        # Crear logger
        self.logger = logging.getLogger('DownloadQueue')
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicación de handlers
        if self.logger.handlers:
            return
        
        # Handler para archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fh = logging.FileHandler(f'download_queue_{timestamp}.log', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Handler para consola
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    def add_download(self, url, prioridad=PRIORIDAD_MEDIA, nombre_archivo=None):
        with self.lock:
            self.contador_tareas += 1
            tarea_id = self.contador_tareas
        
        # Crear item de descarga
        item = {
            'id': tarea_id,
            'url': url,
            'prioridad': prioridad,
            'nombre_archivo': nombre_archivo,
            'intentos': 0
        }
        
        # PriorityQueue ordena por el primer elemento de la tupla
        # Usamos (prioridad, id) para ordenar por prioridad y luego por orden de llegada
        self.queue.put((prioridad, tarea_id, item))
        
        prioridad_str = ['ALTA', 'MEDIA', 'BAJA'][prioridad]
        self.logger.info(f"Descarga añadida [ID:{tarea_id}] [Prioridad:{prioridad_str}] {url}")
    
    def _generar_nombre_archivo(self, url, contenido=None):
        # Obtener extensión de la URL
        parsed = urlparse(url)
        path = parsed.path
        extension = Path(path).suffix or '.bin'
        
        # Generar hash MD5
        if contenido:
            # Hash del contenido
            hash_md5 = hashlib.md5(contenido).hexdigest()[:12]
        else:
            # Hash de la URL si no hay contenido
            hash_md5 = hashlib.md5(url.encode()).hexdigest()[:12]
        
        return f"{hash_md5}{extension}"
    
    def _descargar_con_reintentos(self, item):
        url = item['url']
        tarea_id = item['id']
        
        for intento in range(1, self.max_reintentos + 1):
            try:
                self.logger.debug(f"[ID:{tarea_id}] Intento {intento}/{self.max_reintentos}: {url}")
                
                # Realizar descarga
                inicio = time.time()
                response = requests.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Leer contenido
                contenido = response.content
                tamaño = len(contenido)
                duracion = time.time() - inicio
                
                # Generar nombre de archivo
                if item['nombre_archivo']:
                    nombre_archivo = item['nombre_archivo']
                else:
                    nombre_archivo = self._generar_nombre_archivo(url, contenido)
                
                # Guardar archivo
                ruta_completa = self.carpeta_destino / nombre_archivo
                with open(ruta_completa, 'wb') as f:
                    f.write(contenido)
                
                # Actualizar estadísticas
                with self.lock:
                    self.stats['exitosas'] += 1
                    self.stats['total_bytes'] += tamaño
                    if intento > 1:
                        self.stats['reintentos'] += (intento - 1)
                
                self.logger.info(
                    f"[ID:{tarea_id}] Descarga exitosa: {nombre_archivo} "
                    f"({tamaño/1024:.1f}KB en {duracion:.2f}s)"
                )
                
                return {
                    'id': tarea_id,
                    'url': url,
                    'exito': True,
                    'archivo': nombre_archivo,
                    'ruta': str(ruta_completa),
                    'tamaño': tamaño,
                    'duracion': duracion,
                    'intentos': intento
                }
            
            except requests.exceptions.RequestException as e:
                # Error de red/HTTP
                self.logger.warning(f"[ID:{tarea_id}] Intento {intento} fallido: {type(e).__name__} - {e}")
                
                if intento < self.max_reintentos:
                    # Backoff exponencial: 2^intento segundos
                    espera = 2 ** intento
                    self.logger.debug(f"[ID:{tarea_id}] Esperando {espera}s antes de reintentar...")
                    time.sleep(espera)
                else:
                    # Último intento fallido
                    with self.lock:
                        self.stats['fallidas'] += 1
                    
                    self.logger.error(f"[ID:{tarea_id}] Descarga fallida después de {intento} intentos: {url}")
                    
                    return {
                        'id': tarea_id,
                        'url': url,
                        'exito': False,
                        'error': str(e),
                        'intentos': intento
                    }
            
            except Exception as e:
                # Error inesperado
                with self.lock:
                    self.stats['fallidas'] += 1
                
                self.logger.error(f"[ID:{tarea_id}] Error inesperado: {type(e).__name__} - {e}")
                
                return {
                    'id': tarea_id,
                    'url': url,
                    'exito': False,
                    'error': f"Error inesperado: {str(e)}",
                    'intentos': intento
                }
    
    def procesar(self, timeout=None):
        self.activo = True
        self.logger.info("Iniciando procesamiento de descargas...")
        
        resultados = []
        futures = []
        
        inicio = time.time()
        
        try:
            # Procesar mientras haya items en la cola
            while not self.queue.empty():
                try:
                    # Obtener item (sin bloquear)
                    prioridad, tarea_id, item = self.queue.get_nowait()
                    
                    # Enviar a thread pool
                    future = self.executor.submit(self._descargar_con_reintentos, item)
                    futures.append(future)
                    
                except queue.Empty:
                    break
            
            # Esperar a que todas las descargas terminen
            for future in as_completed(futures, timeout=timeout):
                try:
                    resultado = future.result()
                    resultados.append(resultado)
                except Exception as e:
                    self.logger.error(f"Error obteniendo resultado: {e}")
        
        finally:
            self.activo = False
            duracion_total = time.time() - inicio
            
            self.logger.info(f"Procesamiento completado en {duracion_total:.2f}s")
            self._mostrar_estadisticas()
        
        return resultados
    
    def procesar_continuo(self, intervalo_check=1):
        self.activo = True
        self.logger.info("Iniciando procesamiento continuo...")
        
        try:
            while self.activo:
                if not self.queue.empty():
                    try:
                        prioridad, tarea_id, item = self.queue.get_nowait()
                        
                        # Procesar inmediatamente en el pool
                        future = self.executor.submit(self._descargar_con_reintentos, item)
                        
                    except queue.Empty:
                        pass
                
                time.sleep(intervalo_check)
        
        except KeyboardInterrupt:
            self.logger.info("Procesamiento continuo interrumpido")
        
        finally:
            self.activo = False
    
    def detener(self):
        self.logger.info("Deteniendo procesamiento...")
        self.activo = False
    
    def _mostrar_estadisticas(self):
        with self.lock:
            stats = self.stats.copy()
        
        total = stats['exitosas'] + stats['fallidas']
        
        self.logger.info("=" * 70)
        self.logger.info("ESTADISTICAS DE DESCARGAS")
        self.logger.info("=" * 70)
        self.logger.info(f"Total procesadas: {total}")
        self.logger.info(f"  Exitosas: {stats['exitosas']} ({stats['exitosas']/total*100:.1f}%)" if total > 0 else "  Exitosas: 0")
        self.logger.info(f"  Fallidas: {stats['fallidas']} ({stats['fallidas']/total*100:.1f}%)" if total > 0 else "  Fallidas: 0")
        self.logger.info(f"Total descargado: {stats['total_bytes']/1024/1024:.2f} MB")
        self.logger.info(f"Reintentos totales: {stats['reintentos']}")
        self.logger.info("=" * 70)
    
    def obtener_estadisticas(self):
        with self.lock:
            return self.stats.copy()
    
    def tamaño_cola(self):
        return self.queue.qsize()
    
    def shutdown(self, wait=True):
        self.logger.info("Cerrando DownloadQueue...")
        self.activo = False
        self.executor.shutdown(wait=wait)
        self.logger.info("DownloadQueue cerrado")


def demo_basica():
    print("\n" + "=" * 70)
    print("   DEMO: SISTEMA DE DESCARGA CON COLA DE PRIORIDAD")
    print("=" * 70 + "\n")
    
    # Crear downloader
    downloader = DownloadQueue(max_workers=3, max_reintentos=3)
    
    # URLs de prueba (imágenes pequeñas de placeholder)
    urls_test = [
        # Prioridad ALTA (0)
        ("https://via.placeholder.com/150/FF0000", DownloadQueue.PRIORIDAD_ALTA, "imagen_alta_1.png"),
        ("https://via.placeholder.com/150/00FF00", DownloadQueue.PRIORIDAD_ALTA, "imagen_alta_2.png"),
        
        # Prioridad MEDIA (1)
        ("https://via.placeholder.com/150/0000FF", DownloadQueue.PRIORIDAD_MEDIA, "imagen_media_1.png"),
        ("https://via.placeholder.com/150/FFFF00", DownloadQueue.PRIORIDAD_MEDIA, "imagen_media_2.png"),
        
        # Prioridad BAJA (2)
        ("https://via.placeholder.com/150/FF00FF", DownloadQueue.PRIORIDAD_BAJA, "imagen_baja_1.png"),
        ("https://via.placeholder.com/150/00FFFF", DownloadQueue.PRIORIDAD_BAJA, "imagen_baja_2.png"),
        
        # URL que fallará (para probar reintentos)
        ("https://httpstat.us/500", DownloadQueue.PRIORIDAD_MEDIA, None),
        ("https://this-domain-does-not-exist-12345.com/file.zip", DownloadQueue.PRIORIDAD_BAJA, None),
    ]
    
    # Añadir descargas
    print("Añadiendo descargas a la cola...\n")
    for url, prioridad, nombre in urls_test:
        downloader.add_download(url, prioridad, nombre)
    
    print(f"\nDescargas en cola: {downloader.tamaño_cola()}")
    input("\nPresiona Enter para iniciar el procesamiento...")
    
    # Procesar
    resultados = downloader.procesar(timeout=120)
    
    # Mostrar resultados
    print("\n" + "=" * 70)
    print("RESULTADOS DETALLADOS")
    print("=" * 70)
    
    for r in resultados:
        if r['exito']:
            print(f"\nOK  [ID:{r['id']}] {r['archivo']}")
            print(f"    URL: {r['url']}")
            print(f"    Tamaño: {r['tamaño']/1024:.1f}KB")
            print(f"    Tiempo: {r['duracion']:.2f}s")
            print(f"    Intentos: {r['intentos']}")
        else:
            print(f"\nFALLO [ID:{r['id']}]")
            print(f"    URL: {r['url']}")
            print(f"    Error: {r['error']}")
            print(f"    Intentos: {r['intentos']}")
    
    # Cerrar
    downloader.shutdown()
    
    print("\n" + "=" * 70)
    print(f"Archivos guardados en: {downloader.carpeta_destino.absolute()}")
    print("=" * 70 + "\n")


def demo_avanzada():
    print("\n" + "=" * 70)
    print("   DEMO AVANZADA: DESCARGA DE RECURSOS WEB")
    print("=" * 70 + "\n")
    
    downloader = DownloadQueue(max_workers=5, carpeta_destino="recursos_web", max_reintentos=3)
    
    # Simular diferentes tipos de recursos con prioridades
    recursos = {
        'criticos': [
            "https://via.placeholder.com/800/FF0000",
            "https://via.placeholder.com/800/00FF00",
        ],
        'importantes': [
            "https://via.placeholder.com/600/0000FF",
            "https://via.placeholder.com/600/FFFF00",
            "https://via.placeholder.com/600/FF00FF",
        ],
        'opcionales': [
            "https://via.placeholder.com/400/00FFFF",
            "https://via.placeholder.com/400/888888",
            "https://via.placeholder.com/400/AAAAAA",
        ]
    }
    
    # Añadir recursos críticos (prioridad alta)
    print("Añadiendo recursos criticos (prioridad ALTA)...")
    for url in recursos['criticos']:
        downloader.add_download(url, DownloadQueue.PRIORIDAD_ALTA)
    
    # Añadir recursos importantes (prioridad media)
    print("Añadiendo recursos importantes (prioridad MEDIA)...")
    for url in recursos['importantes']:
        downloader.add_download(url, DownloadQueue.PRIORIDAD_MEDIA)
    
    # Añadir recursos opcionales (prioridad baja)
    print("Añadiendo recursos opcionales (prioridad BAJA)...")
    for url in recursos['opcionales']:
        downloader.add_download(url, DownloadQueue.PRIORIDAD_BAJA)
    
    print(f"\nTotal en cola: {downloader.tamaño_cola()} descargas")
    input("\nPresiona Enter para comenzar...")
    
    # Procesar
    resultados = downloader.procesar()
    
    # Análisis de resultados
    exitosas = [r for r in resultados if r['exito']]
    fallidas = [r for r in resultados if not r['exito']]
    
    print("\n" + "=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    print(f"Exitosas: {len(exitosas)}/{len(resultados)}")
    print(f"Fallidas: {len(fallidas)}/{len(resultados)}")
    
    if exitosas:
        tamaño_total = sum(r['tamaño'] for r in exitosas)
        tiempo_total = sum(r['duracion'] for r in exitosas)
        print(f"Descargado: {tamaño_total/1024:.1f}KB")
        print(f"Tiempo total: {tiempo_total:.2f}s")
        print(f"Velocidad promedio: {tamaño_total/tiempo_total/1024:.1f}KB/s")
    
    downloader.shutdown()


def main():
    print("\nSISTEMA DE DESCARGA CON COLA DE PRIORIDAD")
    print("1. Demo basica")
    print("2. Demo avanzada")
    print("3. Salir")
    
    opcion = input("\nSelecciona una opcion: ")
    
    if opcion == "1":
        demo_basica()
    elif opcion == "2":
        demo_avanzada()
    else:
        print("Saliendo...")


if __name__ == "__main__":
    main()
```

## Ejercicio 6
```python
import time
import re
import random
import string
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict, Counter
from functools import reduce as func_reduce

def map_phase(archivo_path):
    conteo = defaultdict(int)
    
    try:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Limpiar y tokenizar
        # Convertir a minúsculas y extraer solo palabras
        palabras = re.findall(r'\b[a-záéíóúñ]+\b', contenido.lower())
        
        # Contar palabras
        for palabra in palabras:
            if len(palabra) >= 3:  # Filtrar palabras muy cortas
                conteo[palabra] += 1
        
        return {
            'archivo': archivo_path.name,
            'conteo': dict(conteo),
            'total_palabras': len(palabras),
            'palabras_unicas': len(conteo)
        }
    
    except Exception as e:
        print(f"Error procesando {archivo_path}: {e}")
        return {
            'archivo': archivo_path.name,
            'conteo': {},
            'total_palabras': 0,
            'palabras_unicas': 0,
            'error': str(e)
        }


def map_phase_optimizado(archivo_path):
    try:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Tokenizar y limpiar
        palabras = re.findall(r'\b[a-záéíóúñ]+\b', contenido.lower())
        palabras = [p for p in palabras if len(p) >= 3]
        
        # Counter es muy eficiente para conteo
        conteo = Counter(palabras)
        
        return {
            'archivo': archivo_path.name,
            'conteo': dict(conteo),
            'total_palabras': len(palabras),
            'palabras_unicas': len(conteo)
        }
    
    except Exception as e:
        return {
            'archivo': archivo_path.name,
            'conteo': {},
            'total_palabras': 0,
            'palabras_unicas': 0,
            'error': str(e)
        }

def shuffle_phase(resultados_map):
    agrupado = defaultdict(list)
    
    for resultado in resultados_map:
        if 'error' not in resultado:
            for palabra, cuenta in resultado['conteo'].items():
                agrupado[palabra].append(cuenta)
    
    return dict(agrupado)

def reduce_phase(conteos_parciales):
    conteo_final = defaultdict(int)
    
    for conteo in conteos_parciales:
        if isinstance(conteo, dict) and 'conteo' in conteo:
            # Si viene de map_phase (tiene estructura completa)
            for palabra, cuenta in conteo['conteo'].items():
                conteo_final[palabra] += cuenta
        elif isinstance(conteo, dict):
            # Si es un dict simple
            for palabra, cuenta in conteo.items():
                conteo_final[palabra] += cuenta
    
    return dict(conteo_final)


def reduce_phase_paralelo(agrupado, num_workers=None):
    def reduce_chunk(items):
        resultado = {}
        for palabra, cuentas in items:
            resultado[palabra] = sum(cuentas)
        return resultado
    
    # Dividir en chunks
    items = list(agrupado.items())
    chunk_size = max(1, len(items) // (num_workers or 4))
    chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
    
    # Reducir chunks en paralelo
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        resultados_parciales = executor.map(reduce_chunk, chunks)
    
    # Combinar resultados
    conteo_final = {}
    for resultado in resultados_parciales:
        conteo_final.update(resultado)
    
    return conteo_final

def mapreduce_secuencial(archivos):
    print("\nMAPREDUCE SECUENCIAL")
    print("=" * 70)
    
    inicio = time.time()
    
    # MAP
    print("Fase MAP...")
    resultados_map = []
    for i, archivo in enumerate(archivos, 1):
        print(f"  Procesando {i}/{len(archivos)}: {archivo.name}", end='\r')
        resultado = map_phase(archivo)
        resultados_map.append(resultado)
    print()
    
    # SHUFFLE
    print("Fase SHUFFLE...")
    agrupado = shuffle_phase(resultados_map)
    
    # REDUCE
    print("Fase REDUCE...")
    conteo_final = reduce_phase(resultados_map)
    
    duracion = time.time() - inicio
    
    print(f"\nTiempo total: {duracion:.2f}s\n")
    
    return conteo_final, duracion, resultados_map


def mapreduce_paralelo(archivos, max_workers=None, reduce_paralelo=False):
    print("\nMAPREDUCE PARALELO")
    print("=" * 70)
    
    if max_workers is None:
        import os
        max_workers = os.cpu_count()
    
    print(f"Usando {max_workers} procesos\n")
    
    inicio = time.time()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # FASE MAP (paralela)
        print("Fase MAP (paralela)...")
        resultados_map = list(executor.map(map_phase_optimizado, archivos))
        print(f"  {len(archivos)} archivos procesados")
        
        # FASE SHUFFLE
        print("Fase SHUFFLE...")
        agrupado = shuffle_phase(resultados_map)
        print(f"  {len(agrupado)} palabras unicas encontradas")
        
        # FASE REDUCE
        if reduce_paralelo and len(agrupado) > 1000:
            print("Fase REDUCE (paralela)...")
            conteo_final = reduce_phase_paralelo(agrupado, max_workers)
        else:
            print("Fase REDUCE (secuencial)...")
            conteo_final = reduce_phase(resultados_map)
    
    duracion = time.time() - inicio
    
    print(f"\nTiempo total: {duracion:.2f}s\n")
    
    return conteo_final, duracion, resultados_map

def generar_archivos_prueba(num_archivos=10, palabras_por_archivo=10000, carpeta="textos_prueba"):
    carpeta_path = Path(carpeta)
    carpeta_path.mkdir(exist_ok=True)
    
    print(f"\nGenerando {num_archivos} archivos de prueba...")
    
    # Vocabulario base (para que haya palabras repetidas)
    vocabulario = [
        'python', 'programacion', 'codigo', 'desarrollo', 'software',
        'algoritmo', 'funcion', 'clase', 'objeto', 'variable',
        'datos', 'proceso', 'sistema', 'aplicacion', 'programa',
        'computadora', 'servidor', 'cliente', 'red', 'internet',
        'base', 'archivo', 'texto', 'numero', 'string',
        'lista', 'diccionario', 'tupla', 'conjunto', 'array',
        'procesamiento', 'paralelo', 'concurrente', 'thread', 'proceso',
        'memoria', 'disco', 'cpu', 'cache', 'buffer',
        'optimizacion', 'rendimiento', 'velocidad', 'eficiencia', 'escalabilidad'
    ]
    
    archivos_creados = []
    
    for i in range(num_archivos):
        nombre_archivo = carpeta_path / f"texto_{i:03d}.txt"
        
        # Generar contenido
        palabras = []
        for _ in range(palabras_por_archivo):
            # 70% del vocabulario, 30% palabras aleatorias
            if random.random() < 0.7:
                palabra = random.choice(vocabulario)
            else:
                longitud = random.randint(4, 10)
                palabra = ''.join(random.choices(string.ascii_lowercase, k=longitud))
            
            palabras.append(palabra)
        
        # Escribir archivo (con formato de párrafos)
        contenido = []
        for j in range(0, len(palabras), 20):
            parrafo = ' '.join(palabras[j:j+20])
            contenido.append(parrafo.capitalize() + '.')
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(contenido))
        
        archivos_creados.append(nombre_archivo)
        
        tamaño_kb = nombre_archivo.stat().st_size / 1024
        print(f"  {nombre_archivo.name} - {tamaño_kb:.1f}KB")
    
    print(f"\n{num_archivos} archivos creados en '{carpeta}'\n")
    
    return archivos_creados


def analizar_resultados(conteo_final, resultados_map, top_n=20):
    print("\nANALISIS DE RESULTADOS")
    print("=" * 70)
    
    # Estadísticas generales
    total_palabras = sum(r['total_palabras'] for r in resultados_map if 'error' not in r)
    palabras_unicas = len(conteo_final)
    
    print(f"Total de palabras procesadas: {total_palabras:,}")
    print(f"Palabras unicas encontradas: {palabras_unicas:,}")
    
    # Estadísticas por archivo
    print(f"\nEstadisticas por archivo:")
    palabras_por_archivo = [r['total_palabras'] for r in resultados_map if 'error' not in r]
    if palabras_por_archivo:
        print(f"  Promedio: {sum(palabras_por_archivo)/len(palabras_por_archivo):.0f} palabras/archivo")
        print(f"  Minimo: {min(palabras_por_archivo):,} palabras")
        print(f"  Maximo: {max(palabras_por_archivo):,} palabras")
    
    # Top palabras más frecuentes
    print(f"\nTop {top_n} palabras mas frecuentes:")
    top_palabras = sorted(conteo_final.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    for i, (palabra, cuenta) in enumerate(top_palabras, 1):
        porcentaje = (cuenta / total_palabras) * 100
        barra = '█' * int(porcentaje * 2)
        print(f"  {i:2d}. {palabra:20s} {cuenta:6,} ({porcentaje:5.2f}%) {barra}")
    
    # Distribución de frecuencias
    print(f"\nDistribucion de frecuencias:")
    rangos = [
        (1, 1, "Palabras que aparecen 1 vez"),
        (2, 10, "Palabras que aparecen 2-10 veces"),
        (11, 100, "Palabras que aparecen 11-100 veces"),
        (101, 1000, "Palabras que aparecen 101-1000 veces"),
        (1001, float('inf'), "Palabras que aparecen >1000 veces"),
    ]
    
    for min_val, max_val, desc in rangos:
        cantidad = sum(1 for c in conteo_final.values() if min_val <= c <= max_val)
        if cantidad > 0:
            print(f"  {desc}: {cantidad:,}")
    
    print()


def exportar_resultados(conteo_final, nombre_archivo="wordcount_resultados.txt"):
    # Ordenar por frecuencia
    palabras_ordenadas = sorted(conteo_final.items(), key=lambda x: x[1], reverse=True)
    
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        f.write("RESULTADOS MAPREDUCE - CONTEO DE PALABRAS\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total de palabras unicas: {len(conteo_final):,}\n")
        f.write(f"Suma total de frecuencias: {sum(conteo_final.values()):,}\n\n")
        f.write("RANKING DE PALABRAS\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Rank':<6} {'Palabra':<20} {'Frecuencia':>12}\n")
        f.write("-" * 70 + "\n")
        
        for i, (palabra, cuenta) in enumerate(palabras_ordenadas, 1):
            f.write(f"{i:<6} {palabra:<20} {cuenta:>12,}\n")
    
    print(f"\nResultados exportados a: {nombre_archivo}")


def limpiar_archivos(carpeta="textos_prueba"):
    carpeta_path = Path(carpeta)
    if carpeta_path.exists():
        for archivo in carpeta_path.glob("*.txt"):
            archivo.unlink()
        carpeta_path.rmdir()
        print(f"\nArchivos de prueba eliminados")

def main():
    print("\n" + "=" * 70)
    print("   SISTEMA MAPREDUCE - CONTEO DE PALABRAS")
    print("=" * 70)
    
    # Configuración
    NUM_ARCHIVOS = 10
    PALABRAS_POR_ARCHIVO = 10000
    MAX_WORKERS = None  # Usa cpu_count()
    
    # Generar archivos de prueba
    carpeta = "textos_prueba"
    archivos = generar_archivos_prueba(NUM_ARCHIVOS, PALABRAS_POR_ARCHIVO, carpeta)
    
    input("Presiona Enter para iniciar el procesamiento...")
    
    # MapReduce SECUENCIAL (solo muestra de 3 archivos)
    print("\n" + "=" * 70)
    print("COMPARACION: Procesando muestra de 3 archivos")
    print("=" * 70)
    
    muestra = archivos[:3]
    conteo_seq, tiempo_seq, res_seq = mapreduce_secuencial(muestra)
    
    # MapReduce PARALELO (todos los archivos)
    print("\n" + "=" * 70)
    print("PROCESAMIENTO COMPLETO EN PARALELO")
    print("=" * 70)
    
    conteo_par, tiempo_par, res_par = mapreduce_paralelo(
        archivos,
        max_workers=MAX_WORKERS,
        reduce_paralelo=True
    )
    
    # Analizar resultados
    analizar_resultados(conteo_par, res_par, top_n=30)
    
    # Comparación de rendimiento
    print("\nCOMPARACION DE RENDIMIENTO")
    print("=" * 70)
    
    tiempo_seq_estimado = (tiempo_seq / len(muestra)) * len(archivos)
    
    print(f"Tiempo secuencial (estimado): {tiempo_seq_estimado:.2f}s")
    print(f"Tiempo paralelo (real):       {tiempo_par:.2f}s")
    
    if tiempo_par < tiempo_seq_estimado:
        speedup = tiempo_seq_estimado / tiempo_par
        print(f"\nSpeedup: {speedup:.2f}x")
        mejora = ((tiempo_seq_estimado - tiempo_par) / tiempo_seq_estimado) * 100
        print(f"Mejora: {mejora:.1f}% mas rapido")
    
    print("\n" + "=" * 70)
    
    # Opciones
    respuesta = input("\nExportar resultados a archivo? (s/n): ").lower()
    if respuesta == 's':
        exportar_resultados(conteo_par)
    
    respuesta = input("Eliminar archivos de prueba? (s/n): ").lower()
    if respuesta == 's':
        limpiar_archivos(carpeta)
    else:
        print(f"\nArchivos guardados en: {Path(carpeta).absolute()}")
    
    print()


if __name__ == "__main__":
    main()
```