# TP2 - Sistema de Scraping y Análisis Web Distribuido

## Descripción del Proyecto

Sistema distribuido de **scraping y análisis web** desarrollado en Python que utiliza programación asíncrona y paralela para extraer, analizar y procesar información de sitios web de manera eficiente.

El sistema está compuesto por **dos servidores independientes** que trabajan de forma coordinada:

- **Servidor A (Scraping Asíncrono)**: Servidor HTTP que maneja solicitudes de scraping de forma asíncrona usando `asyncio` y `aiohttp`
- **Servidor B (Procesamiento Paralelo)**: Servidor de procesamiento que ejecuta tareas CPU-intensivas usando `multiprocessing` y `socketserver`

### Características Principales

**Scraping Web Completo**
- Extracción de títulos, enlaces, metadatos (Open Graph, Twitter Cards)
- Análisis de estructura HTML (headers H1-H6)
- Conteo y procesamiento de imágenes

**Análisis de Rendimiento**
- Medición de tiempo de carga
- Cálculo de tamaño total de recursos
- Conteo de requests HTTP necesarios

**Generación de Screenshots**
- Captura visual de páginas web
- Screenshots en formato PNG codificados en base64

**Procesamiento de Imágenes**
- Descarga de imágenes principales
- Generación de thumbnails optimizados

**Sistema de Cola Asíncrono** (Bonus Track)
- Tareas con ID único
- Estados: `pending`, `scraping`, `processing`, `completed`, `failed`
- Consulta de estado y resultados en tiempo real

**Arquitectura Distribuida**
- Comunicación entre servidores via sockets TCP
- Soporte para IPv4 e IPv6
- Transparencia total para el cliente

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENTE                             │
│                    (HTTP Requests)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP GET /scrape?url=...
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SERVIDOR A - Scraping Asíncrono                │
│                      (asyncio + aiohttp)                    │
│                                                             │
│  • Recibe requests HTTP                                     │
│  • Descarga páginas web (async)                             │
│  • Extrae contenido HTML                                    │
│  • Parsea metadata                                          │
│  • Gestiona cola de tareas (task_id)                        │
│  • Coordina con Servidor B                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ TCP Socket
                         │ (Protocol: [4 bytes length][JSON payload])
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          SERVIDOR B - Procesamiento Paralelo                │
│                 (multiprocessing + socketserver)            │
│                                                             │
│  ┌──────────────────────────────────────────────────┐       │
│  │          Pool de Procesos Workers                │       │
│  ├──────────────────────────────────────────────────┤       │
│  │  Worker 1: Screenshot Generation (Selenium)      │       │
│  │  Worker 2: Performance Analysis                  │       │
│  │  Worker 3: Image Processing (Pillow)             │       │
│  │  Worker N: ...                                   │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Ejecución

1. **Cliente** envía request HTTP: `GET /scrape?url=https://example.com`
2. **Servidor A** genera un `task_id` y devuelve inmediatamente
3. **Background (Servidor A)**:
   - Descarga HTML de forma asíncrona
   - Extrae contenido (título, enlaces, metadatos)
   - Envía datos a Servidor B via socket
4. **Servidor B**:
   - Distribuye tareas al pool de procesos
   - Genera screenshot (Selenium)
   - Analiza rendimiento
   - Procesa imágenes (thumbnails)
   - Retorna resultados via socket
5. **Servidor A** consolida todo y marca tarea como `completed`
6. **Cliente** consulta:
   - `GET /status/{task_id}` → Estado actual
   - `GET /result/{task_id}` → Resultado completo

---

## Estructura del Proyecto

```
TP2/
├── README.md                      # Este archivo
├── .gitignore                     # Archivos ignorados por Git
├── requirements.txt               # Dependencias Python
│
├── server_scraping.py            # Entry point Servidor A
├── server_processing.py          # Entry point Servidor B
├── client.py                     # Cliente de prueba
│
├── common/                       # Módulos compartidos
│   ├── __init__.py
│   ├── protocol.py               # Protocolo de comunicación socket
│   ├── serialization.py          # Serialización JSON/base64
│   └── socket_client.py          # Cliente socket asíncrono
│
├── scraper/                      # Módulo Servidor A
│   ├── __init__.py
│   ├── async_server.py           # Servidor HTTP asyncio + cola
│   ├── async_http.py             # Cliente HTTP asíncrono (aiohttp)
│   ├── html_parser.py            # Parser HTML (BeautifulSoup)
│   ├── metadata_extractor.py     # Extractor de metadatos
│   └── task_manager.py           # Gestor de tareas (Bonus)
│
├── processor/                    # Módulo Servidor B
│   ├── __init__.py
│   ├── processing_server.py      # Servidor socketserver + multiprocessing
│   ├── screenshot.py             # Generación de screenshots (Selenium)
│   ├── performance.py            # Análisis de rendimiento
│   └── image_processor.py        # Procesamiento de imágenes (Pillow)
│
└── tests/                        # Tests unitarios e integración
    ├── __init__.py
    ├── test_scraper.py           # Tests módulo scraper
    ├── test_processor.py         # Tests módulo processor
    └── test_integration.py       # Tests de integración
```

---

## Instalación

### Requisitos Previos

- **Python 3.8+** (recomendado 3.10+)
- **Google Chrome** instalado (para screenshots con Selenium)
- **pip** actualizado
- **macOS, Linux o Windows**

### Paso 1: Clonar o Descargar el Proyecto

```bash
# Si usas Git
git clone https://github.com/francovaco/computacion2.git
cd TP2

# O simplemente crea la carpeta y copia los archivos
mkdir TP2
cd TP2
```

### Paso 2: Crear Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### Paso 3: Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar todas las dependencias
pip install -r requirements.txt

# Verificar instalación
pip list
```

### Paso 4: Dar Permisos de Ejecución (macOS/Linux)

```bash
chmod +x server_scraping.py
chmod +x server_processing.py
chmod +x client.py
```

### Paso 5: Verificar ChromeDriver

El proyecto usa `webdriver-manager` que descarga automáticamente ChromeDriver. Solo asegúrate de tener Chrome instalado:

```bash
# Verificar Chrome en macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

# En Linux
google-chrome --version

# En Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --version
```

---

## Ejecución del Sistema

### Importante: Orden de Inicio

**SIEMPRE iniciar primero el Servidor B, luego el Servidor A**

### Terminal 1: Iniciar Servidor B (Procesamiento)

```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar servidor de procesamiento
python server_processing.py -i localhost -p 9000

# Con opciones adicionales:
python server_processing.py -i localhost -p 9000 -n 8 -v
# -n 8  : 8 procesos workers
# -v    : modo verbose (más logs)
```

**Salida esperada:**
```
============================================================
SERVIDOR DE PROCESAMIENTO DISTRIBUIDO
============================================================
Host: localhost
Puerto: 9000
Procesos: 8
============================================================
[2024-11-10 15:30:00] INFO Iniciando servidor de procesamiento en localhost:9000
[2024-11-10 15:30:00] INFO Pool de procesos: 8 workers
[2024-11-10 15:30:00] INFO Servidor de procesamiento escuchando en localhost:9000
```

### Terminal 2: Iniciar Servidor A (Scraping)

```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar servidor de scraping
python server_scraping.py -i localhost -p 8000 -ph localhost -pp 9000

# Con opciones adicionales:
python server_scraping.py -i localhost -p 8000 -ph localhost -pp 9000 -w 8 -v
# -ph localhost : host del servidor de procesamiento
# -pp 9000      : puerto del servidor de procesamiento
# -w 8          : 8 workers asíncronos
# -v            : modo verbose
```

**Salida esperada:**
```
============================================================
SERVIDOR DE SCRAPING WEB ASÍNCRONO
============================================================
Host: localhost
Puerto: 8000
Workers: 4
Servidor de procesamiento: localhost:9000
============================================================
Iniciando servidor...
[2024-11-10 15:30:00] INFO Servidor de scraping iniciado en http://localhost:8000
```

---

## Ejemplos de Uso

### Opción 1: Cliente de Python

```bash
# Terminal 3
source venv/bin/activate

# Scrapear una URL
python client.py http://localhost:8000 https://example.com

# Scrapear múltiples URLs concurrentemente
python client.py http://localhost:8000 --multiple \
  https://example.com \
  https://python.org \
  https://github.com

# Con verbose
python client.py http://localhost:8000 https://python.org -v
```

**Salida del cliente:**
```
============================================================
Scraping URL: https://example.com
============================================================

Task ID: 12345678-abcd-ef12-3456-789abcdef012
Estado inicial: pending

Esperando resultado...

Estado actual: scraping
Estado actual: processing
Estado actual: completed

============================================================
RESULTADO
============================================================

{
  "url": "https://example.com",
  "timestamp": "2024-11-10T15:30:15.123456",
  "scraping_data": {
    "title": "Example Domain",
    "links": ["https://www.iana.org/domains/example"],
    "meta_tags": {
      "basic": {
        "viewport": "width=device-width, initial-scale=1"
      }
    },
    "structure": {
      "h1": 1
    },
    "images_count": 0
  },
  "processing_data": {
    "screenshot": "iVBORw0KGgo...(base64)...",
    "performance": {
      "load_time_ms": 250,
      "total_size_kb": 1256,
      "num_requests": 2
    },
    "thumbnails": []
  },
  "status": "success"
}

============================================================
RESUMEN
============================================================
Título: Example Domain
Enlaces encontrados: 1
Imágenes: 0
Estructura: {'h1': 1}

Rendimiento:
  - Tiempo de carga: 250 ms
  - Tamaño total: 1256 KB
  - Requests: 2
  - Screenshot: Sí
  - Thumbnails: 0
```

### Opción 2: Usando curl

```bash
# 1. Iniciar scraping (devuelve task_id)
curl "http://localhost:8000/scrape?url=https://example.com"

# Respuesta:
# {
#   "task_id": "abc-123-def-456",
#   "status": "pending",
#   "url": "https://example.com",
#   "message": "Task created. Use /status/{task_id} to check progress."
# }

# 2. Consultar estado
curl "http://localhost:8000/status/abc-123-def-456"

# Respuesta:
# {
#   "task_id": "abc-123-def-456",
#   "status": "processing",
#   "url": "https://example.com",
#   "created_at": "2024-11-10T15:30:00",
#   "updated_at": "2024-11-10T15:30:05"
# }

# 3. Obtener resultado (cuando status = completed)
curl "http://localhost:8000/result/abc-123-def-456"

# 4. Ver estadísticas generales
curl "http://localhost:8000/tasks"

# Respuesta:
# {
#   "total_tasks": 15,
#   "by_status": {
#     "pending": 2,
#     "scraping": 1,
#     "processing": 3,
#     "completed": 8,
#     "failed": 1
#   }
# }
```

### Opción 3: Navegador Web

Abre tu navegador favorito:

1. **Información del servicio:**  
   `http://localhost:8000/`

2. **Iniciar scraping:**  
   `http://localhost:8000/scrape?url=https://example.com`
   
   Copia el `task_id` de la respuesta

3. **Consultar estado:**  
   `http://localhost:8000/status/<task_id>`

4. **Obtener resultado:**  
   `http://localhost:8000/result/<task_id>`

5. **Ver estadísticas:**  
   `http://localhost:8000/tasks`

---

## Formato de Respuesta

### Respuesta Completa Exitosa

```json
{
  "url": "https://python.org",
  "timestamp": "2024-11-10T15:45:30.123456",
  "scraping_data": {
    "title": "Welcome to Python.org",
    "links": [
      "https://www.python.org/about/",
      "https://www.python.org/downloads/",
      "https://docs.python.org/3/"
    ],
    "meta_tags": {
      "basic": {
        "description": "The official home of the Python Programming Language",
        "keywords": "Python programming language object oriented web free",
        "viewport": "width=device-width, initial-scale=1.0"
      },
      "open_graph": {
        "title": "Welcome to Python.org",
        "type": "website",
        "url": "https://www.python.org/",
        "image": "https://www.python.org/static/opengraph-icon-200x200.png"
      },
      "twitter": {
        "card": "summary",
        "site": "@ThePSF",
        "title": "Python.org"
      }
    },
    "structure": {
      "h1": 1,
      "h2": 4,
      "h3": 8
    },
    "images_count": 15,
    "canonical_url": "https://www.python.org/",
    "language": "en"
  },
  "processing_data": {
    "screenshot": "iVBORw0KGgoAAAANSUhEUgAA...(base64 muy largo)...",
    "performance": {
      "load_time_ms": 1250,
      "dom_content_loaded_ms": 850,
      "response_time_ms": 320,
      "dom_interactive_ms": 780,
      "total_size_kb": 2048,
      "num_requests": 45,
      "resource_types": {
        "script": 12,
        "css": 3,
        "img": 15,
        "fetch": 8
      },
      "num_images": 15,
      "num_scripts": 12,
      "num_stylesheets": 3
    },
    "thumbnails": [
      "/9j/4AAQSkZJRgABAQAAAQ...(base64 thumbnail 1)...",
      "/9j/4AAQSkZJRgABAQAAAQ...(base64 thumbnail 2)...",
      "/9j/4AAQSkZJRgABAQAAAQ...(base64 thumbnail 3)..."
    ]
  },
  "status": "success"
}
```

### Estados de Tarea

| Estado | Descripción |
|--------|-------------|
| `pending` | Tarea creada, esperando procesamiento |
| `scraping` | Descargando y analizando HTML |
| `processing` | Ejecutando tareas en Servidor B |
| `completed` | Tarea completada exitosamente |
| `failed` | Tarea falló (ver campo `error`) |

---

## Testing

### Tests Unitarios

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar todos los tests
pytest tests/ -v

# Solo tests rápidos (sin Selenium)
pytest tests/ -v -m "not slow"

# Tests con cobertura
pytest tests/ --cov=scraper --cov=processor --cov=common --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Tests de Integración

**Requiere que ambos servidores estén corriendo**

```bash
# Terminal 1: Servidor B
python server_processing.py -i localhost -p 9000

# Terminal 2: Servidor A
python server_scraping.py -i localhost -p 8000 -ph localhost -pp 9000

# Terminal 3: Tests
pytest tests/test_integration.py -v -m integration
```

### Tests Individuales

```bash
# Tests del scraper
pytest tests/test_scraper.py -v

# Tests del processor
pytest tests/test_processor.py -v

# Un test específico
pytest tests/test_scraper.py::TestHTMLParser::test_parse_html_basic -v
```

---

## Troubleshooting

### Problema: `ModuleNotFoundError: No module named 'aiohttp'`

**Solución:**
```bash
# Verificar que el entorno virtual esté activado
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Problema: `Connection refused` al comunicarse con Servidor B

**Solución:**
1. Verificar que el Servidor B esté corriendo
2. Verificar que los puertos coincidan
3. Verificar que no haya firewall bloqueando

```bash
# Ver qué procesos usan los puertos
lsof -i :8000
lsof -i :9000

# Verificar conectividad
telnet localhost 9000
```

### Problema: `Address already in use`

**Solución:**
```bash
# Ver qué proceso usa el puerto
lsof -i :8000  # o :9000

# Matar el proceso
kill -9 <PID>

# O usar otros puertos
python server_scraping.py -i localhost -p 8080 -ph localhost -pp 9001
python server_processing.py -i localhost -p 9001
```

### Problema: ChromeDriver no funciona

**Solución:**
```bash
# Verificar Chrome instalado
google-chrome --version  # Linux
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version  # macOS

# Reinstalar webdriver-manager
pip uninstall selenium webdriver-manager
pip install selenium webdriver-manager

# O instalar manualmente ChromeDriver
brew install chromedriver  # macOS
```

### Problema: Timeouts al generar screenshots

**Solución:**
- Aumentar timeout en el código: `screenshot.py` → `generate_screenshot(url, timeout=60)`
- Verificar conexión a internet
- Probar con URLs más simples primero

### Problema: `ImportError` en tests

**Solución:**
```bash
# Ejecutar desde el directorio raíz TP2/
cd /ruta/a/TP2

# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ejecutar tests
pytest tests/ -v
```

---

## Opciones de Línea de Comandos

### Servidor de Scraping (`server_scraping.py`)

```
usage: server_scraping.py [-h] -i IP -p PORT [-w WORKERS] 
                          [--processing-host PH] [--processing-port PP] [-v]

Opciones:
  -h, --help            Muestra ayuda
  -i, --ip IP           Dirección de escucha (IPv4/IPv6)
  -p, --port PORT       Puerto de escucha
  -w, --workers N       Número de workers async (default: 4)
  --processing-host PH  Host del servidor de procesamiento (default: localhost)
  --processing-port PP  Puerto del servidor de procesamiento (default: 9000)
  -v, --verbose         Modo verbose

Ejemplos:
  server_scraping.py -i 0.0.0.0 -p 8000 --processing-host localhost --processing-port 9000
  server_scraping.py -i localhost -p 8080 -ph 127.0.0.1 -pp 9000 -w 8
  server_scraping.py -i :: -p 8000 -ph :: -pp 9000  # IPv6
```

### Servidor de Procesamiento (`server_processing.py`)

```
usage: server_processing.py [-h] -i IP -p PORT [-n PROCESSES] [-v]

Opciones:
  -h, --help            Muestra ayuda
  -i, --ip IP           Dirección de escucha (IPv4/IPv6)
  -p, --port PORT       Puerto de escucha
  -n, --processes N     Número de procesos en el pool (default: CPU count)
  -v, --verbose         Modo verbose

Ejemplos:
  server_processing.py -i 0.0.0.0 -p 9000
  server_processing.py -i localhost -p 9000 -n 4
  server_processing.py -i :: -p 9000 -n 8  # IPv6
```

### Cliente (`client.py`)

```
usage: client.py [-h] [--multiple URL [URL ...]] [-v] server_url [url]

Argumentos:
  server_url            URL del servidor (ej: http://localhost:8000)
  url                   URL a scrapear (default: https://example.com)

Opciones:
  -h, --help            Muestra ayuda
  --multiple, -m        Múltiples URLs para probar concurrentemente
  -v, --verbose         Modo verbose

Ejemplos:
  client.py http://localhost:8000 https://example.com
  client.py http://localhost:8000 https://python.org --verbose
  client.py http://localhost:8000 --multiple https://example.com https://python.org
```

---

## Consideraciones de Seguridad

- No usar en producción sin medidas adicionales de seguridad
- Implementar rate limiting para evitar abuso
- Validar y sanitizar todas las URLs de entrada
- Considerar timeout limits para evitar DoS
- No scrapear sitios que lo prohíban en robots.txt

---

## Tecnologías Utilizadas

| Tecnología | Uso |
|------------|-----|
| **asyncio** | Programación asíncrona en Servidor A |
| **aiohttp** | Cliente y servidor HTTP asíncrono |
| **multiprocessing** | Procesamiento paralelo en Servidor B |
| **socketserver** | Servidor TCP para Servidor B |
| **BeautifulSoup4** | Parsing de HTML |
| **lxml** | Parser HTML rápido |
| **Selenium** | Generación de screenshots |
| **Pillow** | Procesamiento de imágenes |
| **pytest** | Testing unitario e integración |

---

## Conceptos Implementados

- **Programación Asíncrona** (asyncio, async/await)
- **Programación Paralela** (multiprocessing, ProcessPoolExecutor)
- **Comunicación por Sockets** (TCP client-server)
- **Protocolos de Comunicación** (length-prefixed messages)
- **Web Scraping** (extracción de datos HTML)
- **Serialización** (JSON, base64)
- **Arquitectura Distribuida** (múltiples servidores coordinados)
- **Sistema de Colas** (task management con estados)
- **Manejo de Errores** robusto
- **Testing** (unitario, integración)

---

## Autor

**Franco Vaccarezza**  
Ingeniería informática legajo:63179
