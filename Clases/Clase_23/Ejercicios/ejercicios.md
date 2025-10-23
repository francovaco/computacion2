## Ejercicio 1
### celery_app.py
```python
from celery import Celery

# Crear instancia de Celery
app = Celery(
    'notificaciones',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
)

# Configuración
app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='America/Argentina/Buenos_Aires',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
```

### models.py
```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Usuario:
    """Representa un usuario del sistema"""
    id: int
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    device_id: Optional[str] = None
    
    def canales_disponibles(self):
        """Retorna lista de canales disponibles para este usuario"""
        canales = []
        if self.email:
            canales.append('email')
        if self.telefono:
            canales.append('sms')
        if self.device_id:
            canales.append('push')
        return canales


@dataclass
class Notificacion:
    """Representa una notificación a enviar"""
    titulo: str
    mensaje: str
    prioridad: str = 'normal'  # alta, normal, baja
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
```

### task.py
```python
from celery_app import app
from celery import group, chord
import time
import random
from datetime import datetime
from typing import Dict, Any


@app.task(
    bind=True,
    rate_limit='100/m',  # Maximo 100 SMS por minuto
    max_retries=3,
    default_retry_delay=60
)
def enviar_sms(self, telefono: str, mensaje: str) -> Dict[str, Any]:
    """
    Envia SMS a un telefono
    
    Args:
        telefono: Numero de telefono destino
        mensaje: Contenido del SMS
    
    Returns:
        Diccionario con resultado del envio
    """
    try:
        print(f"[SMS] Enviando a {telefono}...")
        
        # Simular tiempo de envio
        time.sleep(random.uniform(0.5, 1.5))
        
        # Simular fallo aleatorio (20% de probabilidad)
        if random.random() < 0.2:
            raise Exception("Error de red en proveedor SMS")
        
        # Simular validacion de numero
        if not telefono or len(telefono) < 10:
            return {
                'canal': 'sms',
                'telefono': telefono,
                'exito': False,
                'error': 'Numero de telefono invalido',
                'timestamp': datetime.now().isoformat()
            }
        
        # Envio exitoso
        return {
            'canal': 'sms',
            'telefono': telefono,
            'exito': True,
            'mensaje_id': f"SMS-{random.randint(10000, 99999)}",
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as exc:
        # Reintentar automaticamente
        print(f"[SMS] Error enviando a {telefono}: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        else:
            return {
                'canal': 'sms',
                'telefono': telefono,
                'exito': False,
                'error': str(exc),
                'intentos': self.request.retries + 1,
                'timestamp': datetime.now().isoformat()
            }


@app.task(bind=True, max_retries=3)
def enviar_email(self, email: str, asunto: str, contenido: str) -> Dict[str, Any]:
    """
    Envia email
    
    Args:
        email: Direccion de email destino
        asunto: Asunto del email
        contenido: Cuerpo del mensaje
    
    Returns:
        Diccionario con resultado del envio
    """
    try:
        print(f"[EMAIL] Enviando a {email}...")
        
        # Simular tiempo de envio
        time.sleep(random.uniform(0.5, 2.0))
        
        # Simular fallo aleatorio (15% de probabilidad)
        if random.random() < 0.15:
            raise Exception("Error SMTP timeout")
        
        # Validacion basica de email
        if not email or '@' not in email:
            return {
                'canal': 'email',
                'email': email,
                'exito': False,
                'error': 'Email invalido',
                'timestamp': datetime.now().isoformat()
            }
        
        # Envio exitoso
        return {
            'canal': 'email',
            'email': email,
            'asunto': asunto,
            'exito': True,
            'mensaje_id': f"EMAIL-{random.randint(10000, 99999)}",
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as exc:
        print(f"[EMAIL] Error enviando a {email}: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        else:
            return {
                'canal': 'email',
                'email': email,
                'exito': False,
                'error': str(exc),
                'intentos': self.request.retries + 1,
                'timestamp': datetime.now().isoformat()
            }


@app.task(bind=True, max_retries=3)
def enviar_push(self, device_id: str, titulo: str, mensaje: str) -> Dict[str, Any]:
    """
    Envia notificacion push
    
    Args:
        device_id: ID del dispositivo destino
        titulo: Titulo de la notificacion
        mensaje: Contenido de la notificacion
    
    Returns:
        Diccionario con resultado del envio
    """
    try:
        print(f"[PUSH] Enviando a dispositivo {device_id}...")
        
        # Simular tiempo de envio
        time.sleep(random.uniform(0.3, 1.0))
        
        # Simular fallo aleatorio (10% de probabilidad)
        if random.random() < 0.1:
            raise Exception("Error en servicio FCM/APNS")
        
        # Validacion de device_id
        if not device_id or len(device_id) < 10:
            return {
                'canal': 'push',
                'device_id': device_id,
                'exito': False,
                'error': 'Device ID invalido',
                'timestamp': datetime.now().isoformat()
            }
        
        # Envio exitoso
        return {
            'canal': 'push',
            'device_id': device_id,
            'titulo': titulo,
            'exito': True,
            'mensaje_id': f"PUSH-{random.randint(10000, 99999)}",
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as exc:
        print(f"[PUSH] Error enviando a {device_id}: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=10)
        else:
            return {
                'canal': 'push',
                'device_id': device_id,
                'exito': False,
                'error': str(exc),
                'intentos': self.request.retries + 1,
                'timestamp': datetime.now().isoformat()
            }


@app.task
def registrar_resultados(resultados: list) -> Dict[str, Any]:
    """
    Callback que analiza y registra los resultados de todos los canales
    
    Args:
        resultados: Lista de resultados de cada canal
    
    Returns:
        Resumen del envio multi-canal
    """
    print("\n" + "=" * 70)
    print("REGISTRO DE RESULTADOS - NOTIFICACION MULTI-CANAL")
    print("=" * 70)
    
    # Analizar resultados
    canales_exitosos = []
    canales_fallidos = []
    
    for resultado in resultados:
        if resultado and resultado.get('exito'):
            canales_exitosos.append(resultado['canal'])
            print(f"EXITOSO - {resultado['canal'].upper()}")
            print(f"  ID: {resultado.get('mensaje_id', 'N/A')}")
            print(f"  Timestamp: {resultado['timestamp']}")
        else:
            canal = resultado.get('canal', 'desconocido') if resultado else 'desconocido'
            canales_fallidos.append(canal)
            print(f"FALLIDO - {canal.upper()}")
            if resultado:
                print(f"  Error: {resultado.get('error', 'Error desconocido')}")
                print(f"  Intentos: {resultado.get('intentos', 1)}")
    
    # Resumen
    total_canales = len(resultados)
    exitosos = len(canales_exitosos)
    fallidos = len(canales_fallidos)
    
    print("\n" + "-" * 70)
    print(f"RESUMEN:")
    print(f"  Total de canales: {total_canales}")
    print(f"  Exitosos: {exitosos} ({exitosos/total_canales*100:.1f}%)")
    print(f"  Fallidos: {fallidos} ({fallidos/total_canales*100:.1f}%)")
    print(f"  Canales exitosos: {', '.join(canales_exitosos) if canales_exitosos else 'Ninguno'}")
    print("=" * 70 + "\n")
    
    # Guardar en "base de datos" (simulado)
    registro = {
        'timestamp': datetime.now().isoformat(),
        'total_canales': total_canales,
        'exitosos': exitosos,
        'fallidos': fallidos,
        'canales_exitosos': canales_exitosos,
        'canales_fallidos': canales_fallidos,
        'detalles': resultados,
        'tasa_exito': exitosos / total_canales if total_canales > 0 else 0
    }
    
    return registro


def notificar_usuario(usuario: 'Usuario', notificacion: 'Notificacion') -> Any:
    """
    Notifica a un usuario por todos los canales disponibles
    Usa chord: group de tareas en paralelo + callback
    
    Args:
        usuario: Usuario a notificar
        notificacion: Notificacion a enviar
    
    Returns:
        AsyncResult del chord
    """
    print(f"\nNotificando a {usuario.nombre} ({usuario.id})...")
    print(f"Mensaje: {notificacion.mensaje}")
    print(f"Canales disponibles: {usuario.canales_disponibles()}")
    
    # Crear lista de tareas para cada canal disponible
    tareas = []
    
    if usuario.email:
        tareas.append(
            enviar_email.s(
                usuario.email,
                notificacion.titulo,
                notificacion.mensaje
            )
        )
    
    if usuario.telefono:
        tareas.append(
            enviar_sms.s(
                usuario.telefono,
                notificacion.mensaje
            )
        )
    
    if usuario.device_id:
        tareas.append(
            enviar_push.s(
                usuario.device_id,
                notificacion.titulo,
                notificacion.mensaje
            )
        )
    
    if not tareas:
        print("ADVERTENCIA: Usuario no tiene canales disponibles")
        return None
    
    # Crear chord: group en paralelo + callback
    callback = registrar_resultados.s()
    
    resultado = chord(tareas)(callback)
    
    print(f"Notificacion enviada. Task ID: {resultado.id}")
    print("Esperando resultados...\n")
    
    return resultado


def notificar_multiples_usuarios(usuarios: list, notificacion: 'Notificacion') -> list:
    """
    Notifica a multiples usuarios
    
    Args:
        usuarios: Lista de usuarios
        notificacion: Notificacion a enviar
    
    Returns:
        Lista de AsyncResults
    """
    resultados = []
    
    for usuario in usuarios:
        resultado = notificar_usuario(usuario, notificacion)
        if resultado:
            resultados.append(resultado)
    
    return resultados
```

### main.py
```python
from models import Usuario, Notificacion
from tasks import notificar_usuario, notificar_multiples_usuarios
import time


def demo_notificacion_simple():
    """Demo basica: notificar a un solo usuario"""
    print("\n" + "=" * 70)
    print("DEMO 1: NOTIFICACION SIMPLE")
    print("=" * 70 + "\n")
    
    # Crear usuario con todos los canales
    usuario = Usuario(
        id=1,
        nombre="Juan Perez",
        email="juan.perez@ejemplo.com",
        telefono="+5491112345678",
        device_id="device_abc123xyz456"
    )
    
    # Crear notificacion
    notificacion = Notificacion(
        titulo="Bienvenido",
        mensaje="Tu cuenta ha sido activada exitosamente",
        prioridad="alta"
    )
    
    # Enviar notificacion
    resultado = notificar_usuario(usuario, notificacion)
    
    if resultado:
        # Esperar resultado (bloqueante)
        print("Esperando finalizacion de todas las tareas...")
        resumen = resultado.get(timeout=30)
        
        print("\nRESULTADO FINAL:")
        print(f"  Tasa de exito: {resumen['tasa_exito']*100:.1f}%")
        print(f"  Canales exitosos: {resumen['exitosos']}/{resumen['total_canales']}")


def demo_multiples_usuarios():
    """Demo avanzada: notificar a multiples usuarios"""
    print("\n" + "=" * 70)
    print("DEMO 2: NOTIFICACION A MULTIPLES USUARIOS")
    print("=" * 70 + "\n")
    
    # Crear lista de usuarios con diferentes canales disponibles
    usuarios = [
        Usuario(1, "Ana Garcia", email="ana@ejemplo.com", telefono="+5491123456789"),
        Usuario(2, "Carlos Lopez", email="carlos@ejemplo.com", device_id="device_carlos"),
        Usuario(3, "Maria Rodriguez", telefono="+5491198765432", device_id="device_maria"),
        Usuario(4, "Pedro Martinez", email="pedro@ejemplo.com", telefono="+5491156781234", device_id="device_pedro"),
        Usuario(5, "Laura Fernandez", email="laura@ejemplo.com"),
    ]
    
    # Crear notificacion
    notificacion = Notificacion(
        titulo="Actualizacion del Sistema",
        mensaje="Nueva version disponible. Actualiza tu aplicacion.",
        prioridad="normal"
    )
    
    # Notificar a todos
    resultados = notificar_multiples_usuarios(usuarios, notificacion)
    
    print(f"\nNotificaciones enviadas a {len(resultados)} usuarios")
    print("Esperando finalizacion de todas las tareas...\n")
    
    # Esperar todos los resultados
    resumenes = []
    for i, resultado in enumerate(resultados, 1):
        try:
            resumen = resultado.get(timeout=30)
            resumenes.append(resumen)
            print(f"Usuario {i}: {resumen['exitosos']}/{resumen['total_canales']} canales exitosos")
        except Exception as e:
            print(f"Usuario {i}: Error obteniendo resultado - {e}")
    
    # Estadisticas globales
    if resumenes:
        total_canales = sum(r['total_canales'] for r in resumenes)
        total_exitosos = sum(r['exitosos'] for r in resumenes)
        
        print("\n" + "=" * 70)
        print("ESTADISTICAS GLOBALES")
        print("=" * 70)
        print(f"Total de notificaciones enviadas: {total_canales}")
        print(f"Total exitosas: {total_exitosos} ({total_exitosos/total_canales*100:.1f}%)")
        print("=" * 70)


def demo_solo_canales_especificos():
    """Demo: usuario con solo algunos canales"""
    print("\n" + "=" * 70)
    print("DEMO 3: USUARIO CON CANALES LIMITADOS")
    print("=" * 70 + "\n")
    
    # Usuario solo con email
    usuario = Usuario(
        id=6,
        nombre="Roberto Silva",
        email="roberto@ejemplo.com"
    )
    
    notificacion = Notificacion(
        titulo="Recordatorio",
        mensaje="Tienes una cita pendiente",
        prioridad="alta"
    )
    
    resultado = notificar_usuario(usuario, notificacion)
    
    if resultado:
        resumen = resultado.get(timeout=30)
        print("\nRESULTADO:")
        print(f"  Solo {resumen['total_canales']} canal disponible: {resumen['canales_exitosos']}")


def main():
    """Funcion principal"""
    print("\n" + "=" * 70)
    print("SISTEMA DE NOTIFICACIONES MULTI-CANAL CON CELERY")
    print("=" * 70)
    
    print("\nREQUISITOS:")
    print("1. Redis corriendo en localhost:6379")
    print("2. Celery worker ejecutandose:")
    print("   celery -A celery_app worker --loglevel=info")
    
    input("\nPresiona Enter para continuar...")
    
    # Ejecutar demos
    demos = [
        ("Notificacion simple", demo_notificacion_simple),
        ("Multiples usuarios", demo_multiples_usuarios),
        ("Canales especificos", demo_solo_canales_especificos),
    ]
    
    for i, (nombre, demo_func) in enumerate(demos, 1):
        print(f"\n\n{'='*70}")
        print(f"EJECUTANDO DEMO {i}: {nombre}")
        print('='*70)
        
        demo_func()
        
        if i < len(demos):
            input("\nPresiona Enter para continuar con la siguiente demo...")
    
    print("\n" + "=" * 70)
    print("DEMOS COMPLETADAS")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
```

### requirements.txt
```python
celery==5.3.4
redis==5.0.1
```

### Iniciar redis
```bash
# Con Docker
docker run -d -p 6379:6379 redis

# O instalar Redis localmente
```

### Iniciar celery worker
```bash
celery -A celery_app worker --loglevel=info
```

### Ejecutar programa
```bash
python main.py
```

## Ejercicio 2
### celery_app.py
```python
from celery import Celery

app = Celery(
    'video_pipeline',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
)

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    result_expires=3600,  # Resultados expiran en 1 hora
)
```

### models.py
```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json
from pathlib import Path


@dataclass
class EstadoPipeline:
    video_path: str
    etapa_actual: int = 0
    etapas_completadas: list = None
    tiempo_inicio: str = None
    tiempo_estimado_restante: float = 0
    estado: str = "iniciando"  # iniciando, procesando, completado, fallido
    error: Optional[str] = None
    
    # Resultados intermedios
    audio_path: Optional[str] = None
    transcripcion: Optional[str] = None
    subtitulos_path: Optional[str] = None
    video_comprimido_path: Optional[str] = None
    
    def __post_init__(self):
        if self.etapas_completadas is None:
            self.etapas_completadas = []
        if self.tiempo_inicio is None:
            self.tiempo_inicio = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def guardar(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def cargar(cls, filepath: str) -> 'EstadoPipeline':
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)
```

### utils.py
```python
import time
import random
from pathlib import Path


def simular_procesamiento(duracion_segundos: float, nombre_etapa: str):
    inicio = time.time()
    print(f"[{nombre_etapa}] Iniciando procesamiento...")
    
    while time.time() - inicio < duracion_segundos:
        elapsed = time.time() - inicio
        progreso = (elapsed / duracion_segundos) * 100
        print(f"[{nombre_etapa}] Progreso: {progreso:.1f}%", end='\r')
        time.sleep(0.5)
    
    print(f"\n[{nombre_etapa}] Completado")


def estimar_tiempo_restante(etapa_actual: int, total_etapas: int, tiempo_transcurrido: float) -> float:
    if etapa_actual == 0:
        return 0
    
    tiempo_por_etapa = tiempo_transcurrido / etapa_actual
    etapas_restantes = total_etapas - etapa_actual
    
    return tiempo_por_etapa * etapas_restantes


def validar_archivo_video(video_path: str) -> bool:
    path = Path(video_path)
    return path.exists() and path.is_file()


def crear_directorio_salida(video_path: str) -> Path:
    video_file = Path(video_path)
    output_dir = video_file.parent / f"{video_file.stem}_procesamiento"
    output_dir.mkdir(exist_ok=True)
    return output_dir
```

### tasks.py
```python
from celery_app import app
from celery import chain
from models import EstadoPipeline
from utils import (
    simular_procesamiento, 
    estimar_tiempo_restante,
    validar_archivo_video,
    crear_directorio_salida
)
import time
import random
from pathlib import Path
from datetime import datetime


# Tiempos estimados por etapa (en segundos)
TIEMPOS_ETAPA = {
    'extraer_audio': 10,
    'transcribir': 15,
    'generar_subtitulos': 8,
    'comprimir_video': 20
}

TOTAL_ETAPAS = 4


@app.task(
    bind=True,
    name='tasks.extraer_audio',
    max_retries=3,
    time_limit=300,
    soft_time_limit=270
)
def extraer_audio(self, video_path: str) -> dict:
    inicio = time.time()
    etapa = 1
    
    try:
        # Actualizar estado inicial
        self.update_state(
            state='PROGRESS',
            meta={
                'step': etapa,
                'total': TOTAL_ETAPAS,
                'etapa': 'extraer_audio',
                'progreso_etapa': 0,
                'mensaje': 'Iniciando extraccion de audio...'
            }
        )
        
        # Validar archivo de entrada
        if not validar_archivo_video(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")
        
        # Crear directorio de salida
        output_dir = crear_directorio_salida(video_path)
        audio_path = str(output_dir / "audio.wav")
        
        # Simular extracción de audio con actualizaciones de progreso
        duracion = TIEMPOS_ETAPA['extraer_audio']
        inicio_etapa = time.time()
        
        while time.time() - inicio_etapa < duracion:
            elapsed = time.time() - inicio_etapa
            progreso = (elapsed / duracion) * 100
            
            tiempo_restante = estimar_tiempo_restante(
                etapa, 
                TOTAL_ETAPAS,
                time.time() - inicio
            )
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'step': etapa,
                    'total': TOTAL_ETAPAS,
                    'etapa': 'extraer_audio',
                    'progreso_etapa': min(progreso, 100),
                    'mensaje': f'Extrayendo audio del video...',
                    'tiempo_transcurrido': time.time() - inicio,
                    'tiempo_estimado_restante': tiempo_restante
                }
            )
            
            time.sleep(1)
        
        # Simular posible fallo (5% probabilidad)
        if random.random() < 0.05:
            raise Exception("Error al extraer audio: codec no soportado")
        
        # Guardar estado del pipeline
        estado = EstadoPipeline(
            video_path=video_path,
            etapa_actual=1,
            etapas_completadas=['extraer_audio'],
            audio_path=audio_path,
            estado='procesando'
        )
        estado_path = output_dir / "estado_pipeline.json"
        estado.guardar(str(estado_path))
        
        resultado = {
            'video_path': video_path,
            'audio_path': audio_path,
            'output_dir': str(output_dir),
            'estado_path': str(estado_path),
            'duracion': time.time() - inicio,
            'etapa_completada': 'extraer_audio'
        }
        
        print(f"\n[ETAPA 1/4] Audio extraido: {audio_path}")
        return resultado
    
    except Exception as exc:
        print(f"\n[ERROR] Fallo en extraccion de audio: {exc}")
        
        # Guardar estado de error
        try:
            output_dir = crear_directorio_salida(video_path)
            estado = EstadoPipeline(
                video_path=video_path,
                etapa_actual=1,
                estado='fallido',
                error=str(exc)
            )
            estado.guardar(str(output_dir / "estado_pipeline.json"))
        except:
            pass
        
        # Reintentar si no hemos excedido max_retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        
        raise


@app.task(
    bind=True,
    name='tasks.transcribir',
    max_retries=3,
    time_limit=600,
    soft_time_limit=570
)
def transcribir(self, datos_previos: dict) -> dict:
    inicio = time.time()
    etapa = 2
    audio_path = datos_previos['audio_path']
    output_dir = Path(datos_previos['output_dir'])
    
    try:
        self.update_state(
            state='PROGRESS',
            meta={
                'step': etapa,
                'total': TOTAL_ETAPAS,
                'etapa': 'transcribir',
                'progreso_etapa': 0,
                'mensaje': 'Iniciando transcripcion de audio...'
            }
        )
        
        # Simular transcripción con progreso
        duracion = TIEMPOS_ETAPA['transcribir']
        inicio_etapa = time.time()
        
        transcripcion_parcial = ""
        palabras = ["Hola", "este", "es", "un", "video", "de", "prueba", 
                   "para", "el", "sistema", "de", "procesamiento"]
        
        while time.time() - inicio_etapa < duracion:
            elapsed = time.time() - inicio_etapa
            progreso = (elapsed / duracion) * 100
            
            # Agregar palabras gradualmente
            indice_palabra = int((progreso / 100) * len(palabras))
            transcripcion_parcial = " ".join(palabras[:indice_palabra])
            
            tiempo_restante = estimar_tiempo_restante(
                etapa,
                TOTAL_ETAPAS,
                time.time() - inicio
            )
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'step': etapa,
                    'total': TOTAL_ETAPAS,
                    'etapa': 'transcribir',
                    'progreso_etapa': min(progreso, 100),
                    'mensaje': f'Transcribiendo: "{transcripcion_parcial}..."',
                    'tiempo_transcurrido': time.time() - inicio,
                    'tiempo_estimado_restante': tiempo_restante
                }
            )
            
            time.sleep(1)
        
        # Simular posible fallo (3% probabilidad)
        if random.random() < 0.03:
            raise Exception("Error en API de transcripción: timeout")
        
        transcripcion_completa = " ".join(palabras)
        transcripcion_path = output_dir / "transcripcion.txt"
        
        with open(transcripcion_path, 'w', encoding='utf-8') as f:
            f.write(transcripcion_completa)
        
        # Actualizar estado
        estado = EstadoPipeline.cargar(str(datos_previos['estado_path']))
        estado.etapa_actual = 2
        estado.etapas_completadas.append('transcribir')
        estado.transcripcion = str(transcripcion_path)
        estado.guardar(str(datos_previos['estado_path']))
        
        resultado = {
            **datos_previos,
            'transcripcion': transcripcion_completa,
            'transcripcion_path': str(transcripcion_path),
            'duracion': time.time() - inicio,
            'etapa_completada': 'transcribir'
        }
        
        print(f"\n[ETAPA 2/4] Transcripcion completada: {len(palabras)} palabras")
        return resultado
    
    except Exception as exc:
        print(f"\n[ERROR] Fallo en transcripcion: {exc}")
        
        # Actualizar estado de error
        try:
            estado = EstadoPipeline.cargar(str(datos_previos['estado_path']))
            estado.estado = 'fallido'
            estado.error = str(exc)
            estado.guardar(str(datos_previos['estado_path']))
        except:
            pass
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        
        raise


@app.task(
    bind=True,
    name='tasks.generar_subtitulos',
    max_retries=3,
    time_limit=300
)
def generar_subtitulos(self, datos_previos: dict) -> dict:
    inicio = time.time()
    etapa = 3
    transcripcion = datos_previos['transcripcion']
    output_dir = Path(datos_previos['output_dir'])
    
    try:
        self.update_state(
            state='PROGRESS',
            meta={
                'step': etapa,
                'total': TOTAL_ETAPAS,
                'etapa': 'generar_subtitulos',
                'progreso_etapa': 0,
                'mensaje': 'Generando archivo de subtitulos...'
            }
        )
        
        # Simular generación de subtítulos
        duracion = TIEMPOS_ETAPA['generar_subtitulos']
        inicio_etapa = time.time()
        
        while time.time() - inicio_etapa < duracion:
            elapsed = time.time() - inicio_etapa
            progreso = (elapsed / duracion) * 100
            
            tiempo_restante = estimar_tiempo_restante(
                etapa,
                TOTAL_ETAPAS,
                time.time() - inicio
            )
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'step': etapa,
                    'total': TOTAL_ETAPAS,
                    'etapa': 'generar_subtitulos',
                    'progreso_etapa': min(progreso, 100),
                    'mensaje': 'Sincronizando subtitulos con video...',
                    'tiempo_transcurrido': time.time() - inicio,
                    'tiempo_estimado_restante': tiempo_restante
                }
            )
            
            time.sleep(0.8)
        
        # Generar archivo SRT
        subtitulos_path = output_dir / "subtitulos.srt"
        palabras = transcripcion.split()
        
        with open(subtitulos_path, 'w', encoding='utf-8') as f:
            for i, palabra in enumerate(palabras, 1):
                inicio_time = i * 2
                fin_time = inicio_time + 2
                
                f.write(f"{i}\n")
                f.write(f"00:00:{inicio_time:02d},000 --> 00:00:{fin_time:02d},000\n")
                f.write(f"{palabra}\n\n")
        
        # Actualizar estado
        estado = EstadoPipeline.cargar(str(datos_previos['estado_path']))
        estado.etapa_actual = 3
        estado.etapas_completadas.append('generar_subtitulos')
        estado.subtitulos_path = str(subtitulos_path)
        estado.guardar(str(datos_previos['estado_path']))
        
        resultado = {
            **datos_previos,
            'subtitulos_path': str(subtitulos_path),
            'duracion': time.time() - inicio,
            'etapa_completada': 'generar_subtitulos'
        }
        
        print(f"\n[ETAPA 3/4] Subtitulos generados: {subtitulos_path}")
        return resultado
    
    except Exception as exc:
        print(f"\n[ERROR] Fallo en generacion de subtitulos: {exc}")
        
        try:
            estado = EstadoPipeline.cargar(str(datos_previos['estado_path']))
            estado.estado = 'fallido'
            estado.error = str(exc)
            estado.guardar(str(datos_previos['estado_path']))
        except:
            pass
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=20)
        
        raise


@app.task(
    bind=True,
    name='tasks.comprimir_video',
    max_retries=2,
    time_limit=900,
    soft_time_limit=870
)
def comprimir_video(self, datos_previos: dict) -> dict:
    inicio = time.time()
    etapa = 4
    video_path = datos_previos['video_path']
    subtitulos_path = datos_previos['subtitulos_path']
    output_dir = Path(datos_previos['output_dir'])
    
    try:
        self.update_state(
            state='PROGRESS',
            meta={
                'step': etapa,
                'total': TOTAL_ETAPAS,
                'etapa': 'comprimir_video',
                'progreso_etapa': 0,
                'mensaje': 'Comprimiendo video final...'
            }
        )
        
        # Simular compresión con progreso detallado
        duracion = TIEMPOS_ETAPA['comprimir_video']
        inicio_etapa = time.time()
        
        video_comprimido_path = output_dir / "video_final.mp4"
        
        while time.time() - inicio_etapa < duracion:
            elapsed = time.time() - inicio_etapa
            progreso = (elapsed / duracion) * 100
            
            # Estimar tamaño del archivo
            tamaño_estimado = int((progreso / 100) * 1024 * 10)  # 10 MB final
            
            tiempo_restante = estimar_tiempo_restante(
                etapa,
                TOTAL_ETAPAS,
                time.time() - inicio
            )
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'step': etapa,
                    'total': TOTAL_ETAPAS,
                    'etapa': 'comprimir_video',
                    'progreso_etapa': min(progreso, 100),
                    'mensaje': f'Comprimiendo... {tamaño_estimado} KB procesados',
                    'tiempo_transcurrido': time.time() - inicio,
                    'tiempo_estimado_restante': tiempo_restante
                }
            )
            
            time.sleep(1)
        
        # Simular creación del archivo final
        with open(video_comprimido_path, 'w') as f:
            f.write("VIDEO_COMPRIMIDO_PLACEHOLDER")
        
        # Actualizar estado final
        estado = EstadoPipeline.cargar(str(datos_previos['estado_path']))
        estado.etapa_actual = 4
        estado.etapas_completadas.append('comprimir_video')
        estado.video_comprimido_path = str(video_comprimido_path)
        estado.estado = 'completado'
        estado.guardar(str(datos_previos['estado_path']))
        
        tiempo_total = time.time() - inicio
        
        resultado = {
            **datos_previos,
            'video_comprimido_path': str(video_comprimido_path),
            'duracion': tiempo_total,
            'etapa_completada': 'comprimir_video',
            'pipeline_completado': True,
            'tiempo_total_pipeline': tiempo_total
        }
        
        print(f"\n[ETAPA 4/4] Video comprimido: {video_comprimido_path}")
        print(f"\nPIPELINE COMPLETADO en {tiempo_total:.1f}s")
        return resultado
    
    except Exception as exc:
        print(f"\n[ERROR] Fallo en compresion de video: {exc}")
        
        try:
            estado = EstadoPipeline.cargar(str(datos_previos['estado_path']))
            estado.estado = 'fallido'
            estado.error = str(exc)
            estado.guardar(str(datos_previos['estado_path']))
        except:
            pass
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=120)
        
        raise


def crear_pipeline(video_path: str):
    pipeline = chain(
        extraer_audio.s(video_path),
        transcribir.s(),
        generar_subtitulos.s(),
        comprimir_video.s()
    )
    
    return pipeline


def reanudar_pipeline(estado_path: str):
    estado = EstadoPipeline.cargar(estado_path)
    
    print(f"\nReanudando pipeline desde etapa {estado.etapa_actual + 1}")
    print(f"Etapas completadas: {estado.etapas_completadas}")
    
    # Construir datos previos
    datos_previos = {
        'video_path': estado.video_path,
        'audio_path': estado.audio_path,
        'output_dir': str(Path(estado_path).parent),
        'estado_path': estado_path
    }
    
    if estado.transcripcion:
        with open(estado.transcripcion, 'r') as f:
            datos_previos['transcripcion'] = f.read()
        datos_previos['transcripcion_path'] = estado.transcripcion
    
    if estado.subtitulos_path:
        datos_previos['subtitulos_path'] = estado.subtitulos_path
    
    # Crear chain desde la etapa siguiente
    if estado.etapa_actual == 1:
        pipeline = chain(
            transcribir.s(datos_previos),
            generar_subtitulos.s(),
            comprimir_video.s()
        )
    elif estado.etapa_actual == 2:
        pipeline = chain(
            generar_subtitulos.s(datos_previos),
            comprimir_video.s()
        )
    elif estado.etapa_actual == 3:
        pipeline = comprimir_video.s(datos_previos)
    else:
        print("Pipeline ya esta completado")
        return None
    
    return pipeline
```

### main.py
```python
from tasks import crear_pipeline, reanudar_pipeline
from pathlib import Path
import time


def crear_video_prueba():
    video_dir = Path("videos_prueba")
    video_dir.mkdir(exist_ok=True)
    
    video_path = video_dir / "video_test.mp4"
    
    with open(video_path, 'w') as f:
        f.write("VIDEO_PLACEHOLDER_DATA")
    
    print(f"Video de prueba creado: {video_path}")
    return str(video_path)


def monitorear_progreso(resultado):
    print("\nMonitoreando progreso del pipeline...")
    print("=" * 70)
    
    ultima_etapa = None
    
    while not resultado.ready():
        info = resultado.info
        
        if isinstance(info, dict):
            etapa = info.get('etapa', 'desconocido')
            progreso = info.get('progreso_etapa', 0)
            mensaje = info.get('mensaje', '')
            step = info.get('step', 0)
            total = info.get('total', 4)
            tiempo_restante = info.get('tiempo_estimado_restante', 0)
            
            if etapa != ultima_etapa:
                print(f"\n[ETAPA {step}/{total}] {etapa.upper()}")
                ultima_etapa = etapa
            
            print(f"  Progreso: {progreso:5.1f}% | {mensaje}", end='\r')
            
            if tiempo_restante > 0:
                mins, secs = divmod(int(tiempo_restante), 60)
                print(f" | Tiempo restante: {mins}m {secs}s", end='')
        
        time.sleep(0.5)
    
    print("\n" + "=" * 70)


def demo_pipeline_completo():
    print("\n" + "=" * 70)
    print("DEMO: PIPELINE COMPLETO")
    print("=" * 70 + "\n")
    
    # Crear video de prueba
    video_path = crear_video_prueba()
    
    # Crear y ejecutar pipeline
    print(f"\nIniciando pipeline para: {video_path}")
    pipeline = crear_pipeline(video_path)
    resultado = pipeline.apply_async()
    
    print(f"Pipeline iniciado. Task ID: {resultado.id}")
    
    # Monitorear progreso
    monitorear_progreso(resultado)
    
    # Obtener resultado final
    try:
        resultado_final = resultado.get(timeout=300)
        
        print("\nRESULTADO FINAL:")
        print(f"  Video original: {resultado_final['video_path']}")
        print(f"  Audio extraido: {resultado_final['audio_path']}")
        print(f"  Transcripcion: {resultado_final['transcripcion_path']}")
        print(f"  Subtitulos: {resultado_final['subtitulos_path']}")
        print(f"  Video final: {resultado_final['video_comprimido_path']}")
        print(f"  Tiempo total: {resultado_final['tiempo_total_pipeline']:.1f}s")
        
    except Exception as e:
        print(f"\nERROR: Pipeline fallo - {e}")
        
        # Mostrar información del estado para posible reanudación
        video_dir = Path(video_path).parent
        output_dir = video_dir / f"{Path(video_path).stem}_procesamiento"
        estado_path = output_dir / "estado_pipeline.json"
        
        if estado_path.exists():
            print(f"\nEstado guardado en: {estado_path}")
            print("Puedes reanudar con: reanudar_pipeline('{estado_path}')")


def demo_reanudar_pipeline():
    print("\n" + "=" * 70)
    print("DEMO: REANUDAR PIPELINE")
    print("=" * 70 + "\n")
    
    # Buscar archivos de estado
    estados = list(Path(".").rglob("estado_pipeline.json"))
    
    if not estados:
        print("No se encontraron pipelines para reanudar")
        print("Ejecuta primero demo_pipeline_completo()")
        return
    
    estado_path = str(estados[0])
    print(f"Reanudando desde: {estado_path}\n")
    
    # Reanudar pipeline
    pipeline = reanudar_pipeline(estado_path)
    
    if pipeline:
        resultado = pipeline.apply_async()
        monitorear_progreso(resultado)
        
        try:
            resultado_final = resultado.get(timeout=300)
            print("\nPIPELINE REANUDADO Y COMPLETADO")
        except Exception as e:
            print(f"\nERROR al reanudar: {e}")


def main():
    print("\n" + "=" * 70)
    print("PIPELINE DE PROCESAMIENTO DE VIDEO CON CELERY")
    print("=" * 70)
    
    print("\nREQUISITOS:")
    print("1. Redis corriendo en localhost:6379")
    print("2. Celery worker ejecutandose:")
    print("   celery -A celery_app worker --loglevel=info")
    
    input("\nPresiona Enter para continuar...")
    
    demo_pipeline_completo()
    
    print("\n" + "=" * 70)
    print("DEMOS COMPLETADAS")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
```

### requirements.txt
```python
celery==5.3.4
redis==5.0.1
```

### Iniciar redis
```bash
# Con Docker
docker run -d -p 6379:6379 redis

# O instalar Redis localmente
```

### Iniciar celery worker
```bash
celery -A celery_app worker --loglevel=info
```

### Ejecutar programa
```bash
python main.py
```

### Para monitoreo visual (opcional):
```bash
   pip install flower
   celery -A celery_app flower
   # Abrir http://localhost:5555
```

## Ejercicio 3 
### celery_app.py
```python
from celery import Celery
from kombu import Queue

app = Celery(
    'scraper_distribuido',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
)

# Configurar colas con prioridades
app.conf.task_queues = (
    Queue('urgent', routing_key='urgent', priority=10),
    Queue('normal', routing_key='normal', priority=5),
    Queue('low', routing_key='low', priority=1),
)

# Configuración de routing por defecto
app.conf.task_default_queue = 'normal'
app.conf.task_default_routing_key = 'normal'

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        'tasks.scrape_url_urgent': {'queue': 'urgent'},
        'tasks.scrape_url_normal': {'queue': 'normal'},
        'tasks.scrape_url_low': {'queue': 'low'},
    }
)
```

### rate_limiter.py
```python
import redis
import time
from urllib.parse import urlparse
from datetime import datetime, timedelta


class DomainRateLimiter:
    
    def __init__(self, redis_client=None, max_requests=10, window_seconds=60):
        self.redis = redis_client or redis.Redis(
            host='localhost', 
            port=6379, 
            db=2,
            decode_responses=True
        )
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def get_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or parsed.path.split('/')[0]
    
    def can_request(self, url: str) -> bool:
        domain = self.get_domain(url)
        key = f"rate_limit:{domain}"
        
        now = time.time()
        window_start = now - self.window_seconds
        
        # Limpiar requests antiguos
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Contar requests en ventana actual
        current_requests = self.redis.zcard(key)
        
        return current_requests < self.max_requests
    
    def record_request(self, url: str):
        domain = self.get_domain(url)
        key = f"rate_limit:{domain}"
        
        now = time.time()
        
        # Agregar timestamp actual
        self.redis.zadd(key, {str(now): now})
        
        # Expirar key después de ventana
        self.redis.expire(key, self.window_seconds * 2)
    
    def wait_time(self, url: str) -> float:
        domain = self.get_domain(url)
        key = f"rate_limit:{domain}"
        
        now = time.time()
        window_start = now - self.window_seconds
        
        # Obtener requests en ventana
        requests = self.redis.zrangebyscore(
            key, 
            window_start, 
            now,
            withscores=True
        )
        
        if len(requests) < self.max_requests:
            return 0
        
        # Calcular cuándo expira el request más antiguo
        oldest_request = float(requests[0][1])
        wait_until = oldest_request + self.window_seconds
        wait_seconds = max(0, wait_until - now)
        
        return wait_seconds
    
    def get_stats(self, url: str) -> dict:
        domain = self.get_domain(url)
        key = f"rate_limit:{domain}"
        
        now = time.time()
        window_start = now - self.window_seconds
        
        self.redis.zremrangebyscore(key, 0, window_start)
        current_requests = self.redis.zcard(key)
        
        return {
            'domain': domain,
            'current_requests': current_requests,
            'max_requests': self.max_requests,
            'remaining': self.max_requests - current_requests,
            'window_seconds': self.window_seconds
        }
```

### stats.py
```python
import redis
import json
from datetime import datetime
from typing import Dict, List


class ScraperStats:
    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis(
            host='localhost',
            port=6379,
            db=3,
            decode_responses=True
        )
    
    def increment(self, metric: str, amount: int = 1):
        self.redis.incrby(f"stats:{metric}", amount)
    
    def record_success(self, url: str, duration: float, queue: str):
        self.increment('total_success')
        self.increment(f'queue:{queue}:success')
        
        # Guardar detalle
        data = {
            'url': url,
            'duration': duration,
            'queue': queue,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        self.redis.lpush('recent_scrapes', json.dumps(data))
        self.redis.ltrim('recent_scrapes', 0, 99)  # Mantener últimos 100
    
    def record_failure(self, url: str, error: str, queue: str):
        self.increment('total_failures')
        self.increment(f'queue:{queue}:failures')
        
        data = {
            'url': url,
            'error': error,
            'queue': queue,
            'timestamp': datetime.now().isoformat(),
            'status': 'failure'
        }
        self.redis.lpush('recent_scrapes', json.dumps(data))
        self.redis.ltrim('recent_scrapes', 0, 99)
    
    def record_retry(self, url: str, old_queue: str, new_queue: str):
        self.increment('total_retries')
        self.increment(f'priority_changes:{old_queue}_to_{new_queue}')
    
    def get_summary(self) -> Dict:
        keys = self.redis.keys('stats:*')
        stats = {}
        
        for key in keys:
            metric = key.replace('stats:', '')
            value = int(self.redis.get(key) or 0)
            stats[metric] = value
        
        # Calcular tasas
        total = stats.get('total_success', 0) + stats.get('total_failures', 0)
        if total > 0:
            stats['success_rate'] = (stats.get('total_success', 0) / total) * 100
        else:
            stats['success_rate'] = 0
        
        return stats
    
    def get_recent_scrapes(self, limit: int = 20) -> List[Dict]:
        items = self.redis.lrange('recent_scrapes', 0, limit - 1)
        return [json.loads(item) for item in items]
    
    def reset(self):
        keys = self.redis.keys('stats:*')
        if keys:
            self.redis.delete(*keys)
        self.redis.delete('recent_scrapes')
```

### tasks.py
```python
from celery_app import app
from rate_limiter import DomainRateLimiter
from stats import ScraperStats
import requests
import time
import random
from urllib.parse import urlparse
from bs4 import BeautifulSoup


# Inicializar utilidades
rate_limiter = DomainRateLimiter(max_requests=10, window_seconds=60)
stats = ScraperStats()


# Dominios de alta prioridad
DOMINIOS_URGENTES = [
    'importante.com',
    'critico.com',
    'urgente.com',
    'prioritario.com'
]

# Dominios de prioridad normal
DOMINIOS_NORMALES = [
    'ejemplo.com',
    'sitio.com',
    'pagina.com'
]


def clasificar_dominio(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    
    if any(d in domain for d in DOMINIOS_URGENTES):
        return 'urgent'
    elif any(d in domain for d in DOMINIOS_NORMALES):
        return 'normal'
    else:
        return 'low'


@app.task(
    bind=True,
    name='tasks.scrape_url_urgent',
    queue='urgent',
    max_retries=3,
    time_limit=60
)
def scrape_url_urgent(self, url: str, retry_count: int = 0) -> dict:
    return _scrape_url(self, url, 'urgent', retry_count)


@app.task(
    bind=True,
    name='tasks.scrape_url_normal',
    queue='normal',
    max_retries=3,
    time_limit=90
)
def scrape_url_normal(self, url: str, retry_count: int = 0) -> dict:
    return _scrape_url(self, url, 'normal', retry_count)


@app.task(
    bind=True,
    name='tasks.scrape_url_low',
    queue='low',
    max_retries=2,
    time_limit=120
)
def scrape_url_low(self, url: str, retry_count: int = 0) -> dict:
    return _scrape_url(self, url, 'low', retry_count)


def _scrape_url(task, url: str, queue: str, retry_count: int) -> dict:
    inicio = time.time()
    
    try:
        print(f"\n[{queue.upper()}] Scraping: {url}")
        
        # Verificar rate limit
        if not rate_limiter.can_request(url):
            wait_time = rate_limiter.wait_time(url)
            print(f"  Rate limit alcanzado. Esperando {wait_time:.1f}s...")
            
            # Esperar y reintentar
            raise task.retry(countdown=int(wait_time) + 1)
        
        # Registrar request
        rate_limiter.record_request(url)
        
        # Obtener stats del dominio
        domain_stats = rate_limiter.get_stats(url)
        print(f"  Domain: {domain_stats['domain']}")
        print(f"  Requests: {domain_stats['current_requests']}/{domain_stats['max_requests']}")
        
        # Simular scraping
        time.sleep(random.uniform(0.5, 2.0))
        
        # Simular diferentes respuestas según prioridad
        fallo_prob = {
            'urgent': 0.05,   # 5% de fallos
            'normal': 0.15,   # 15% de fallos
            'low': 0.25       # 25% de fallos
        }
        
        if random.random() < fallo_prob.get(queue, 0.15):
            raise Exception(f"Error HTTP: {random.choice([500, 502, 503, 504])}")
        
        # Scraping exitoso
        response_data = {
            'url': url,
            'status_code': 200,
            'title': f"Pagina de {urlparse(url).netloc}",
            'content_length': random.randint(1000, 50000),
            'links_found': random.randint(10, 100),
            'images_found': random.randint(5, 50),
            'queue': queue,
            'retry_count': retry_count,
            'duration': time.time() - inicio
        }
        
        # Registrar éxito
        stats.record_success(url, response_data['duration'], queue)
        
        print(f"  EXITOSO - {response_data['content_length']} bytes")
        print(f"  Links: {response_data['links_found']}, Imagenes: {response_data['images_found']}")
        
        return response_data
    
    except Exception as exc:
        duracion = time.time() - inicio
        print(f"  FALLO - {exc}")
        
        # Si no hemos excedido reintentos, bajar prioridad y reintentar
        if task.request.retries < task.max_retries:
            # Determinar nueva cola (bajar prioridad)
            nueva_cola = {
                'urgent': 'normal',
                'normal': 'low',
                'low': 'low'
            }.get(queue, 'low')
            
            if nueva_cola != queue:
                print(f"  Bajando prioridad: {queue} -> {nueva_cola}")
                stats.record_retry(url, queue, nueva_cola)
                
                # Reenviar a nueva cola
                if nueva_cola == 'normal':
                    scrape_url_normal.apply_async(
                        args=[url, retry_count + 1],
                        countdown=5
                    )
                elif nueva_cola == 'low':
                    scrape_url_low.apply_async(
                        args=[url, retry_count + 1],
                        countdown=10
                    )
            
            # Registrar fallo
            stats.record_failure(url, str(exc), queue)
            
            # Reintentar en misma cola con countdown
            countdown = 2 ** task.request.retries  # Backoff exponencial
            raise task.retry(exc=exc, countdown=countdown)
        
        else:
            # Ya no hay más reintentos
            stats.record_failure(url, str(exc), queue)
            
            return {
                'url': url,
                'status_code': 0,
                'error': str(exc),
                'queue': queue,
                'retry_count': retry_count,
                'duration': duracion,
                'success': False
            }


def clasificar_y_enviar(url: str):
    cola = clasificar_dominio(url)
    
    print(f"Clasificando URL: {url}")
    print(f"  Cola asignada: {cola}")
    
    if cola == 'urgent':
        return scrape_url_urgent.apply_async(args=[url])
    elif cola == 'normal':
        return scrape_url_normal.apply_async(args=[url])
    else:
        return scrape_url_low.apply_async(args=[url])
```

### dashboard.py
```python
from flask import Flask, render_template_string, jsonify
from stats import ScraperStats
import json

app_flask = Flask(__name__)
stats_dashboard = ScraperStats()


TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Scraper Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #3498db;
        }
        .stat-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        .recent-table {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        th {
            background-color: #34495e;
            color: white;
        }
        .success { color: #27ae60; }
        .failure { color: #e74c3c; }
        .queue-urgent { background-color: #e74c3c; color: white; padding: 3px 8px; border-radius: 3px; }
        .queue-normal { background-color: #f39c12; color: white; padding: 3px 8px; border-radius: 3px; }
        .queue-low { background-color: #95a5a6; color: white; padding: 3px 8px; border-radius: 3px; }
    </style>
    <script>
        function updateDashboard() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-success').textContent = data.summary.total_success || 0;
                    document.getElementById('total-failures').textContent = data.summary.total_failures || 0;
                    document.getElementById('success-rate').textContent = 
                        (data.summary.success_rate || 0).toFixed(1) + '%';
                    document.getElementById('total-retries').textContent = data.summary.total_retries || 0;
                    
                    // Actualizar tabla
                    const tbody = document.getElementById('recent-tbody');
                    tbody.innerHTML = '';
                    
                    data.recent.forEach(item => {
                        const row = tbody.insertRow();
                        row.innerHTML = `
                            <td class="${item.status}">${item.status.toUpperCase()}</td>
                            <td><span class="queue-${item.queue}">${item.queue}</span></td>
                            <td><small>${item.url}</small></td>
                            <td><small>${new Date(item.timestamp).toLocaleTimeString()}</small></td>
                        `;
                    });
                });
        }
        
        // Actualizar cada 2 segundos
        setInterval(updateDashboard, 2000);
        updateDashboard();
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Scraper Dashboard - Tiempo Real</h1>
            <p>Monitoreo de scraping distribuido con colas de prioridad</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="total-success">0</div>
                <div class="stat-label">Scrapes Exitosos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-failures">0</div>
                <div class="stat-label">Scrapes Fallidos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="success-rate">0%</div>
                <div class="stat-label">Tasa de Exito</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-retries">0</div>
                <div class="stat-label">Reintentos</div>
            </div>
        </div>
        
        <div class="recent-table">
            <h2>Actividad Reciente</h2>
            <table>
                <thead>
                    <tr>
                        <th>Estado</th>
                        <th>Cola</th>
                        <th>URL</th>
                        <th>Hora</th>
                    </tr>
                </thead>
                <tbody id="recent-tbody">
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""


@app_flask.route('/')
def dashboard():
    return render_template_string(TEMPLATE_HTML)


@app_flask.route('/api/stats')
def api_stats():
    summary = stats_dashboard.get_summary()
    recent = stats_dashboard.get_recent_scrapes(20)
    
    return jsonify({
        'summary': summary,
        'recent': recent
    })


def run_dashboard(port=5000):
    print(f"\nDashboard disponible en: http://localhost:{port}")
    app_flask.run(port=port, debug=False)
```

### main.py
```python
from tasks import clasificar_y_enviar, stats
from rate_limiter import DomainRateLimiter
import time
import threading


def generar_urls_prueba():
    urls = []
    
    # URLs urgentes
    for i in range(20):
        urls.append(f"https://importante.com/pagina{i}")
        urls.append(f"https://critico.com/datos{i}")
    
    # URLs normales
    for i in range(30):
        urls.append(f"https://ejemplo.com/articulo{i}")
        urls.append(f"https://sitio.com/contenido{i}")
    
    # URLs de baja prioridad
    for i in range(50):
        urls.append(f"https://blog-personal.net/post{i}")
        urls.append(f"https://sitio-aleatorio.org/pagina{i}")
    
    return urls


def demo_scraping_basico():
    print("\n" + "=" * 70)
    print("DEMO: SCRAPING CON CLASIFICACION AUTOMATICA")
    print("=" * 70 + "\n")
    
    # Resetear estadísticas
    stats.reset()
    
    # Generar URLs
    urls = generar_urls_prueba()[:20]  # Solo 20 para demo
    
    print(f"Enviando {len(urls)} URLs a las colas...")
    
    # Enviar a colas
    resultados = []
    for url in urls:
        resultado = clasificar_y_enviar(url)
        resultados.append(resultado)
        time.sleep(0.1)  # Pequeña pausa
    
    print(f"\n{len(urls)} tareas enviadas")
    print("Esperando resultados...")
    
    # Esperar resultados
    completados = 0
    for resultado in resultados:
        try:
            data = resultado.get(timeout=30)
            completados += 1
            if completados % 5 == 0:
                print(f"  Completados: {completados}/{len(urls)}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Mostrar estadísticas
    print("\n" + "=" * 70)
    print("ESTADISTICAS FINALES")
    print("=" * 70)
    
    summary = stats.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")


def demo_rate_limiting():
    print("\n" + "=" * 70)
    print("DEMO: RATE LIMITING POR DOMINIO")
    print("=" * 70 + "\n")
    
    limiter = DomainRateLimiter(max_requests=5, window_seconds=10)
    
    print("Configuracion: Max 5 requests por 10 segundos")
    print("Dominio de prueba: ejemplo.com\n")
    
    # Enviar 10 URLs del mismo dominio
    urls = [f"https://ejemplo.com/pagina{i}" for i in range(10)]
    
    for i, url in enumerate(urls, 1):
        if limiter.can_request(url):
            limiter.record_request(url)
            print(f"Request {i}: PERMITIDO")
            clasificar_y_enviar(url)
        else:
            wait = limiter.wait_time(url)
            print(f"Request {i}: BLOQUEADO (esperar {wait:.1f}s)")
        
        # Mostrar stats
        stats_dom = limiter.get_stats(url)
        print(f"  Stats: {stats_dom['current_requests']}/{stats_dom['max_requests']}")
        print()
        
        time.sleep(1)


def main():
    print("\n" + "=" * 70)
    print("WEB SCRAPER DISTRIBUIDO CON COLAS DE PRIORIDAD")
    print("=" * 70)
    
    print("\nREQUISITOS:")
    print("1. Redis corriendo en localhost:6379")
    print("2. Celery workers para cada cola:")
    print("   celery -A celery_app worker -Q urgent --loglevel=info -n urgent@%%h")
    print("   celery -A celery_app worker -Q normal --loglevel=info -n normal@%%h")
    print("   celery -A celery_app worker -Q low --loglevel=info -n low@%%h")
    print("3. Dashboard (opcional):")
    print("   python dashboard.py")
    
    input("\nPresiona Enter para continuar...")
    
    # Ejecutar demos
    demo_scraping_basico()
    
    input("\nPresiona Enter para demo de rate limiting...")
    demo_rate_limiting()
    
    print("\n" + "=" * 70)
    print("DEMOS COMPLETADAS")
    print("=" * 70)
    print("\nPara ver estadisticas en tiempo real:")
    print("  python -c 'from dashboard import run_dashboard; run_dashboard()'")
    print("  Abrir: http://localhost:5000")
    print()


if __name__ == "__main__":
    main()
```

### requirements.txt
```python
celery==5.3.4
redis==5.0.1
requests==2.31.0
beautifulsoup4==4.12.2
flask==3.0.0
kombu==5.3.4
```

### Iniciar Redis:
```bash
   docker run -d -p 6379:6379 redis
```

### Iniciar Workers (3 terminales diferentes):
```bash
   Terminal 1 - Worker URGENT:
   celery -A celery_app worker -Q urgent --loglevel=info -n urgent@%h
   
   Terminal 2 - Worker NORMAL:
   celery -A celery_app worker -Q normal --loglevel=info -n normal@%h
   
   Terminal 3 - Worker LOW:
   celery -A celery_app worker -Q low --loglevel=info -n low@%h
```
### Ejecutar programa principal:
```bash
   python main.py
```

### Iniciar Dashboard (opcional, terminal 4):
```bash
   python -c "from dashboard import run_dashboard; run_dashboard()"
   # Abrir http://localhost:5000
```

## Ejercicio 4
### celery_app.py
```python
from celery import Celery
from celery.schedules import crontab

app = Celery(
    'reportes_programados',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
)

# Configuración de tareas periódicas con Celery Beat
app.conf.beat_schedule = {
    # Reporte diario de ventas - cada día a las 8 AM
    'reporte-diario-ventas': {
        'task': 'tasks.generar_reporte_ventas',
        'schedule': crontab(hour=8, minute=0),
        'kwargs': {'tipo': 'diario'}
    },
    
    # Reporte semanal de usuarios activos - cada lunes a las 9 AM
    'reporte-semanal-usuarios': {
        'task': 'tasks.generar_reporte_usuarios',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # 1 = lunes
        'kwargs': {'tipo': 'semanal'}
    },
    
    # Reporte mensual financiero - día 1 de cada mes a las 10 AM
    'reporte-mensual-financiero': {
        'task': 'tasks.generar_reporte_financiero',
        'schedule': crontab(hour=10, minute=0, day_of_month=1),
        'kwargs': {'tipo': 'mensual'}
    },
    
    # Reporte de inventario - cada 6 horas
    'reporte-inventario-6h': {
        'task': 'tasks.generar_reporte_inventario',
        'schedule': crontab(minute=0, hour='*/6'),  # 0:00, 6:00, 12:00, 18:00
        'kwargs': {'tipo': 'periodico'}
    },
    
    # Limpieza de reportes antiguos - cada día a las 2 AM
    'limpieza-reportes-antiguos': {
        'task': 'tasks.limpiar_reportes_antiguos',
        'schedule': crontab(hour=2, minute=0),
        'kwargs': {'dias_antiguedad': 30}
    },
}

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='America/Argentina/Buenos_Aires',
    enable_utc=False,
    task_track_started=True,
    task_acks_late=True,
)
```

### database.py
```python
import random
from datetime import datetime, timedelta
from typing import List, Dict


class Database:
    
    @staticmethod
    def obtener_ventas_diarias() -> List[Dict]:
        ventas = []
        num_ventas = random.randint(50, 150)
        
        for i in range(num_ventas):
            ventas.append({
                'id': i + 1,
                'producto': random.choice([
                    'Laptop', 'Mouse', 'Teclado', 'Monitor', 
                    'Auriculares', 'Webcam', 'SSD', 'RAM'
                ]),
                'cantidad': random.randint(1, 5),
                'precio_unitario': round(random.uniform(20, 1500), 2),
                'cliente': f"Cliente_{random.randint(1, 100)}",
                'fecha': datetime.now().isoformat(),
                'vendedor': random.choice(['Juan', 'Maria', 'Pedro', 'Ana'])
            })
            
            ventas[-1]['total'] = round(
                ventas[-1]['cantidad'] * ventas[-1]['precio_unitario'], 2
            )
        
        return ventas
    
    @staticmethod
    def obtener_usuarios_activos_semana() -> List[Dict]:
        usuarios = []
        num_usuarios = random.randint(200, 500)
        
        for i in range(num_usuarios):
            usuarios.append({
                'id': i + 1,
                'nombre': f"Usuario_{i+1}",
                'email': f"usuario{i+1}@ejemplo.com",
                'sesiones': random.randint(1, 50),
                'tiempo_total_minutos': random.randint(10, 500),
                'ultima_actividad': (
                    datetime.now() - timedelta(days=random.randint(0, 6))
                ).isoformat(),
                'dispositivo': random.choice(['Desktop', 'Mobile', 'Tablet'])
            })
        
        return usuarios
    
    @staticmethod
    def obtener_datos_financieros_mes() -> Dict:
        ingresos = round(random.uniform(50000, 150000), 2)
        gastos = round(ingresos * random.uniform(0.6, 0.8), 2)
        
        return {
            'mes': datetime.now().strftime('%B %Y'),
            'ingresos_brutos': ingresos,
            'gastos_operativos': gastos,
            'utilidad_neta': round(ingresos - gastos, 2),
            'margen_utilidad': round(((ingresos - gastos) / ingresos) * 100, 2),
            'transacciones': random.randint(1000, 5000),
            'clientes_nuevos': random.randint(50, 200),
            'tasa_conversion': round(random.uniform(2, 8), 2),
            'ticket_promedio': round(ingresos / random.randint(1000, 5000), 2),
            'categorias': {
                'Hardware': round(ingresos * 0.4, 2),
                'Software': round(ingresos * 0.3, 2),
                'Servicios': round(ingresos * 0.2, 2),
                'Otros': round(ingresos * 0.1, 2)
            }
        }
    
    @staticmethod
    def obtener_inventario() -> List[Dict]:
        productos = [
            'Laptop', 'Mouse', 'Teclado', 'Monitor', 'Auriculares',
            'Webcam', 'SSD', 'RAM', 'GPU', 'CPU', 'Motherboard'
        ]
        
        inventario = []
        for i, producto in enumerate(productos, 1):
            stock = random.randint(0, 100)
            stock_minimo = 10
            
            inventario.append({
                'id': i,
                'producto': producto,
                'stock_actual': stock,
                'stock_minimo': stock_minimo,
                'estado': 'CRITICO' if stock < stock_minimo else 'OK',
                'precio': round(random.uniform(50, 2000), 2),
                'proveedor': f"Proveedor_{random.randint(1, 5)}"
            })
        
        return inventario
```

### pdf_generator.py
```python
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
from pathlib import Path
import io


class PDFGenerator:
    def __init__(self, output_path: str, titulo: str):
        self.output_path = output_path
        self.titulo = titulo
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        self.story = []
        self.styles = getSampleStyleSheet()
        self._crear_estilos_personalizados()
    
    def _crear_estilos_personalizados(self):
        self.styles.add(ParagraphStyle(
            name='TituloPersonalizado',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubtituloPersonalizado',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=12
        ))
    
    def agregar_titulo(self):
        titulo = Paragraph(self.titulo, self.styles['TituloPersonalizado'])
        self.story.append(titulo)
        
        fecha = Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['Normal']
        )
        self.story.append(fecha)
        self.story.append(Spacer(1, 0.3 * inch))
    
    def agregar_seccion(self, titulo: str, contenido: str = None):
        titulo_seccion = Paragraph(titulo, self.styles['SubtituloPersonalizado'])
        self.story.append(titulo_seccion)
        
        if contenido:
            texto = Paragraph(contenido, self.styles['Normal'])
            self.story.append(texto)
        
        self.story.append(Spacer(1, 0.2 * inch))
    
    def agregar_tabla(self, datos: list, encabezados: list):
        # Preparar datos
        tabla_datos = [encabezados] + datos
        
        # Crear tabla
        tabla = Table(tabla_datos)
        
        # Estilo de tabla
        estilo = TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Contenido
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ])
        
        tabla.setStyle(estilo)
        self.story.append(tabla)
        self.story.append(Spacer(1, 0.3 * inch))
    
    def agregar_resumen(self, datos: dict):
        resumen_texto = "<br/>".join([
            f"<b>{clave}:</b> {valor}" 
            for clave, valor in datos.items()
        ])
        
        resumen = Paragraph(resumen_texto, self.styles['Normal'])
        self.story.append(resumen)
        self.story.append(Spacer(1, 0.2 * inch))
    
    def generar(self):
        self.doc.build(self.story)
        print(f"PDF generado: {self.output_path}")
```

### email_sender.py
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime


class EmailSender:
    def __init__(self, smtp_host='localhost', smtp_port=25):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
    
    def enviar_reporte(
        self, 
        destinatarios: list,
        asunto: str,
        cuerpo: str,
        archivo_adjunto: str = None
    ):
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = 'reportes@empresa.com'
        msg['To'] = ', '.join(destinatarios)
        msg['Subject'] = asunto
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Agregar cuerpo
        msg.attach(MIMEText(cuerpo, 'html'))
        
        # Agregar adjunto si existe
        if archivo_adjunto and Path(archivo_adjunto).exists():
            with open(archivo_adjunto, 'rb') as f:
                adjunto = MIMEApplication(f.read(), _subtype='pdf')
                adjunto.add_header(
                    'Content-Disposition', 
                    'attachment', 
                    filename=Path(archivo_adjunto).name
                )
                msg.attach(adjunto)
        
        # Simular envío (en producción usar SMTP real)
        print(f"\nEmail simulado:")
        print(f"  Para: {', '.join(destinatarios)}")
        print(f"  Asunto: {asunto}")
        print(f"  Adjunto: {Path(archivo_adjunto).name if archivo_adjunto else 'Ninguno'}")
        print(f"  Tamaño: {len(msg.as_string())} bytes")
        
        return True
```

### task.py
```python
from celery_app import app
from database import Database
from pdf_generator import PDFGenerator
from email_sender import EmailSender
from pathlib import Path
from datetime import datetime
import time


# Directorios de salida
REPORTES_DIR = Path("reportes")
REPORTES_DIR.mkdir(exist_ok=True)


@app.task(
    bind=True,
    name='tasks.generar_reporte_ventas',
    max_retries=3,
    default_retry_delay=3600  # 1 hora = 3600 segundos
)
def generar_reporte_ventas(self, tipo='diario'):
    try:
        print(f"\n{'='*70}")
        print(f"GENERANDO REPORTE DE VENTAS - {tipo.upper()}")
        print(f"{'='*70}\n")
        
        inicio = time.time()
        
        # 1. Consultar base de datos
        print("[1/4] Consultando base de datos...")
        db = Database()
        ventas = db.obtener_ventas_diarias()
        time.sleep(1)  # Simular consulta
        print(f"  {len(ventas)} ventas obtenidas")
        
        # 2. Generar PDF
        print("[2/4] Generando PDF...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"reporte_ventas_{tipo}_{timestamp}.pdf"
        pdf_path = REPORTES_DIR / pdf_filename
        
        pdf = PDFGenerator(str(pdf_path), f"Reporte de Ventas - {tipo.title()}")
        pdf.agregar_titulo()
        
        # Calcular métricas
        total_ventas = sum(v['total'] for v in ventas)
        ticket_promedio = total_ventas / len(ventas) if ventas else 0
        
        # Resumen
        pdf.agregar_seccion("Resumen Ejecutivo")
        pdf.agregar_resumen({
            'Total de Ventas': f"${total_ventas:,.2f}",
            'Número de Transacciones': len(ventas),
            'Ticket Promedio': f"${ticket_promedio:,.2f}",
            'Producto Más Vendido': max(ventas, key=lambda x: x['cantidad'])['producto'] if ventas else 'N/A'
        })
        
        # Tabla de ventas (primeras 20)
        pdf.agregar_seccion("Detalle de Ventas (Muestra)")
        datos_tabla = [
            [v['producto'], v['cantidad'], f"${v['precio_unitario']:.2f}", 
             f"${v['total']:.2f}", v['vendedor']]
            for v in ventas[:20]
        ]
        pdf.agregar_tabla(
            datos_tabla,
            ['Producto', 'Cant.', 'Precio Unit.', 'Total', 'Vendedor']
        )
        
        pdf.generar()
        print(f"  PDF guardado: {pdf_path}")
        
        # 3. Enviar email
        print("[3/4] Enviando email...")
        email_sender = EmailSender()
        
        destinatarios = ['gerencia@empresa.com', 'ventas@empresa.com']
        asunto = f"Reporte de Ventas {tipo.title()} - {datetime.now().strftime('%d/%m/%Y')}"
        cuerpo = f"""
        <html>
        <body>
            <h2>Reporte de Ventas {tipo.title()}</h2>
            <p>Se ha generado el reporte automático de ventas.</p>
            <h3>Resumen:</h3>
            <ul>
                <li><b>Total de Ventas:</b> ${total_ventas:,.2f}</li>
                <li><b>Transacciones:</b> {len(ventas)}</li>
                <li><b>Ticket Promedio:</b> ${ticket_promedio:,.2f}</li>
            </ul>
            <p>Encuentra el reporte detallado en el archivo adjunto.</p>
            <p><i>Este es un email automático generado por el sistema.</i></p>
        </body>
        </html>
        """
        
        email_sender.enviar_reporte(destinatarios, asunto, cuerpo, str(pdf_path))
        print("  Email enviado correctamente")
        
        # 4. Registrar resultado
        print("[4/4] Registrando resultado...")
        duracion = time.time() - inicio
        
        resultado = {
            'tipo': tipo,
            'pdf_path': str(pdf_path),
            'total_ventas': total_ventas,
            'num_transacciones': len(ventas),
            'timestamp': datetime.now().isoformat(),
            'duracion_segundos': round(duracion, 2),
            'exito': True
        }
        
        print(f"\nREPORTE COMPLETADO en {duracion:.1f}s")
        print(f"{'='*70}\n")
        
        return resultado
    
    except Exception as exc:
        print(f"\nERROR generando reporte: {exc}")
        
        # Reintentar si no hemos excedido max_retries
        if self.request.retries < self.max_retries:
            print(f"Reintentando en 1 hora... (intento {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=exc)
        
        return {
            'tipo': tipo,
            'exito': False,
            'error': str(exc),
            'timestamp': datetime.now().isoformat()
        }


@app.task(
    bind=True,
    name='tasks.generar_reporte_usuarios',
    max_retries=3,
    default_retry_delay=3600
)
def generar_reporte_usuarios(self, tipo='semanal'):
    try:
        print(f"\n{'='*70}")
        print(f"GENERANDO REPORTE DE USUARIOS - {tipo.upper()}")
        print(f"{'='*70}\n")
        
        inicio = time.time()
        
        # 1. Consultar BD
        print("[1/4] Consultando usuarios activos...")
        db = Database()
        usuarios = db.obtener_usuarios_activos_semana()
        time.sleep(1)
        print(f"  {len(usuarios)} usuarios activos")
        
        # 2. Generar PDF
        print("[2/4] Generando PDF...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"reporte_usuarios_{tipo}_{timestamp}.pdf"
        pdf_path = REPORTES_DIR / pdf_filename
        
        pdf = PDFGenerator(str(pdf_path), f"Reporte de Usuarios Activos - {tipo.title()}")
        pdf.agregar_titulo()
        
        # Métricas
        total_sesiones = sum(u['sesiones'] for u in usuarios)
        tiempo_total = sum(u['tiempo_total_minutos'] for u in usuarios)
        promedio_sesiones = total_sesiones / len(usuarios) if usuarios else 0
        
        # Resumen
        pdf.agregar_seccion("Resumen Ejecutivo")
        pdf.agregar_resumen({
            'Usuarios Activos': len(usuarios),
            'Total de Sesiones': total_sesiones,
            'Tiempo Total (horas)': round(tiempo_total / 60, 2),
            'Promedio Sesiones por Usuario': round(promedio_sesiones, 2),
            'Dispositivo Más Usado': max(
                set(u['dispositivo'] for u in usuarios),
                key=lambda d: sum(1 for u in usuarios if u['dispositivo'] == d)
            ) if usuarios else 'N/A'
        })
        
        # Tabla de usuarios top (primeros 20)
        pdf.agregar_seccion("Top Usuarios Activos")
        usuarios_ordenados = sorted(usuarios, key=lambda x: x['sesiones'], reverse=True)[:20]
        datos_tabla = [
            [u['nombre'], u['sesiones'], round(u['tiempo_total_minutos']/60, 1), u['dispositivo']]
            for u in usuarios_ordenados
        ]
        pdf.agregar_tabla(
            datos_tabla,
            ['Usuario', 'Sesiones', 'Horas', 'Dispositivo']
        )
        
        pdf.generar()
        print(f"  PDF guardado: {pdf_path}")
        
        # 3. Enviar email
        print("[3/4] Enviando email...")
        email_sender = EmailSender()
        
        destinatarios = ['marketing@empresa.com', 'producto@empresa.com']
        asunto = f"Reporte de Usuarios Activos {tipo.title()} - {datetime.now().strftime('%d/%m/%Y')}"
        cuerpo = f"""
        <html>
        <body>
            <h2>Reporte de Usuarios Activos {tipo.title()}</h2>
            <h3>Métricas Clave:</h3>
            <ul>
                <li><b>Usuarios Activos:</b> {len(usuarios)}</li>
                <li><b>Total Sesiones:</b> {total_sesiones}</li>
                <li><b>Tiempo Total:</b> {round(tiempo_total/60, 1)} horas</li>
            </ul>
            <p>Reporte completo en archivo adjunto.</p>
        </body>
        </html>
        """
        
        email_sender.enviar_reporte(destinatarios, asunto, cuerpo, str(pdf_path))
        print("  Email enviado")
        
        duracion = time.time() - inicio
        
        print(f"\nREPORTE COMPLETADO en {duracion:.1f}s")
        print(f"{'='*70}\n")
        
        return {
            'tipo': tipo,
            'pdf_path': str(pdf_path),
            'utilidad_neta': datos_financieros['utilidad_neta'],
            'timestamp': datetime.now().isoformat(),
            'exito': True
        }
    
    except Exception as exc:
        print(f"\nERROR: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {'tipo': tipo, 'exito': False, 'error': str(exc)}


@app.task(
    bind=True,
    name='tasks.generar_reporte_inventario',
    max_retries=3,
    default_retry_delay=3600
)
def generar_reporte_inventario(self, tipo='periodico'):
    try:
        print(f"\nGenerando reporte de inventario...")
        
        db = Database()
        inventario = db.obtener_inventario()
        
        # Verificar productos críticos
        productos_criticos = [p for p in inventario if p['estado'] == 'CRITICO']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"reporte_inventario_{timestamp}.pdf"
        pdf_path = REPORTES_DIR / pdf_filename
        
        pdf = PDFGenerator(str(pdf_path), "Reporte de Inventario")
        pdf.agregar_titulo()
        
        # Alertas
        if productos_criticos:
            pdf.agregar_seccion(
                "ALERTA: Productos con Stock Crítico",
                f"{len(productos_criticos)} productos necesitan reabastecimiento urgente"
            )
            
            datos_criticos = [
                [p['producto'], p['stock_actual'], p['stock_minimo'], p['proveedor']]
                for p in productos_criticos
            ]
            pdf.agregar_tabla(
                datos_criticos,
                ['Producto', 'Stock Actual', 'Mínimo', 'Proveedor']
            )
        
        # Inventario completo
        pdf.agregar_seccion("Inventario Completo")
        datos_inventario = [
            [p['producto'], p['stock_actual'], p['estado'], f"${p['precio']:.2f}"]
            for p in inventario
        ]
        pdf.agregar_tabla(
            datos_inventario,
            ['Producto', 'Stock', 'Estado', 'Precio']
        )
        
        pdf.generar()
        
        # Solo enviar email si hay productos críticos
        if productos_criticos:
            email_sender = EmailSender()
            destinatarios = ['inventario@empresa.com', 'compras@empresa.com']
            asunto = f"ALERTA: {len(productos_criticos)} productos con stock crítico"
            cuerpo = f"""
            <html>
            <body>
                <h2 style="color: red">Alerta de Inventario</h2>
                <p>Los siguientes productos necesitan reabastecimiento:</p>
                <ul>
                    {''.join([f"<li><b>{p['producto']}</b>: {p['stock_actual']} unidades</li>" for p in productos_criticos])}
                </ul>
                <p>Reporte completo adjunto.</p>
            </body>
            </html>
            """
            email_sender.enviar_reporte(destinatarios, asunto, cuerpo, str(pdf_path))
        
        print(f"Reporte de inventario completado: {pdf_path}")
        
        return {
            'tipo': tipo,
            'pdf_path': str(pdf_path),
            'productos_criticos': len(productos_criticos),
            'timestamp': datetime.now().isoformat(),
            'exito': True
        }
    
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {'tipo': tipo, 'exito': False, 'error': str(exc)}


@app.task(name='tasks.limpiar_reportes_antiguos')
def limpiar_reportes_antiguos(dias_antiguedad=30):
    try:
        print(f"\nLimpiando reportes con más de {dias_antiguedad} días...")
        
        from datetime import timedelta
        limite = datetime.now() - timedelta(days=dias_antiguedad)
        
        archivos_eliminados = 0
        for archivo in REPORTES_DIR.glob("*.pdf"):
            fecha_creacion = datetime.fromtimestamp(archivo.stat().st_ctime)
            
            if fecha_creacion < limite:
                archivo.unlink()
                archivos_eliminados += 1
        
        print(f"Limpieza completada: {archivos_eliminados} archivos eliminados")
        
        return {
            'archivos_eliminados': archivos_eliminados,
            'timestamp': datetime.now().isoformat(),
            'exito': True
        }
    
    except Exception as exc:
        print(f"Error en limpieza: {exc}")
        return {'exito': False, 'error': str(exc)}
```

### main.py
```python
from tasks import (
    generar_reporte_ventas,
    generar_reporte_usuarios,
    generar_reporte_financiero,
    generar_reporte_inventario,
    limpiar_reportes_antiguos
)
import time


def ejecutar_reporte_manual(tipo_reporte):
    print(f"\n{'='*70}")
    print(f"EJECUCION MANUAL DE REPORTE")
    print(f"{'='*70}\n")
    
    tareas = {
        '1': ('Ventas Diario', generar_reporte_ventas, {'tipo': 'diario'}),
        '2': ('Usuarios Semanal', generar_reporte_usuarios, {'tipo': 'semanal'}),
        '3': ('Financiero Mensual', generar_reporte_financiero, {'tipo': 'mensual'}),
        '4': ('Inventario', generar_reporte_inventario, {'tipo': 'periodico'}),
        '5': ('Limpieza', limpiar_reportes_antiguos, {'dias_antiguedad': 30}),
    }
    
    if tipo_reporte in tareas:
        nombre, tarea, kwargs = tareas[tipo_reporte]
        print(f"Ejecutando: {nombre}")
        
        # Ejecutar tarea de forma asíncrona
        resultado = tarea.apply_async(kwargs=kwargs)
        
        print(f"Tarea enviada. Task ID: {resultado.id}")
        print("Esperando resultado...\n")
        
        # Esperar resultado
        try:
            data = resultado.get(timeout=120)
            
            print("\nRESULTADO:")
            for key, value in data.items():
                print(f"  {key}: {value}")
            
            if data.get('exito'):
                print("\nREPORTE GENERADO EXITOSAMENTE")
            else:
                print("\nERROR EN LA GENERACION")
        
        except Exception as e:
            print(f"\nERROR: {e}")
    else:
        print("Tipo de reporte no válido")


def demo_reportes_programados():
    print("\n" + "=" * 70)
    print("SISTEMA DE REPORTES PROGRAMADOS")
    print("=" * 70)
    
    print("\nREPORTES CONFIGURADOS:")
    print("-" * 70)
    
    schedules = {
        'Reporte Diario de Ventas': 'Todos los días a las 8:00 AM',
        'Reporte Semanal de Usuarios': 'Cada lunes a las 9:00 AM',
        'Reporte Mensual Financiero': 'Día 1 de cada mes a las 10:00 AM',
        'Reporte de Inventario': 'Cada 6 horas (0:00, 6:00, 12:00, 18:00)',
        'Limpieza de Reportes': 'Todos los días a las 2:00 AM'
    }
    
    for nombre, horario in schedules.items():
        print(f"\n{nombre}:")
        print(f"  Horario: {horario}")
    
    print("\n" + "=" * 70)


def demo_ejecucion_inmediata():
    print("\n" + "=" * 70)
    print("DEMO: EJECUCION INMEDIATA DE TODOS LOS REPORTES")
    print("=" * 70 + "\n")
    
    print("Ejecutando todos los reportes de forma asíncrona...")
    
    # Ejecutar todas las tareas
    resultados = {
        'ventas': generar_reporte_ventas.apply_async(kwargs={'tipo': 'diario'}),
        'usuarios': generar_reporte_usuarios.apply_async(kwargs={'tipo': 'semanal'}),
        'financiero': generar_reporte_financiero.apply_async(kwargs={'tipo': 'mensual'}),
        'inventario': generar_reporte_inventario.apply_async(kwargs={'tipo': 'periodico'}),
    }
    
    print(f"\n{len(resultados)} tareas enviadas")
    print("Esperando completación...\n")
    
    # Esperar todos los resultados
    for nombre, resultado in resultados.items():
        try:
            data = resultado.get(timeout=120)
            estado = "EXITOSO" if data.get('exito') else "FALLIDO"
            print(f"{nombre.title():15} - {estado}")
            if data.get('pdf_path'):
                print(f"                  PDF: {data['pdf_path']}")
        except Exception as e:
            print(f"{nombre.title():15} - ERROR: {e}")
    
    print("\n" + "=" * 70)


def main():
    print("\n" + "=" * 70)
    print("SISTEMA DE REPORTES PROGRAMADOS CON CELERY BEAT")
    print("=" * 70)
    
    print("\nREQUISITOS:")
    print("1. Redis corriendo en localhost:6379")
    print("2. Celery worker ejecutándose:")
    print("   celery -A celery_app worker --loglevel=info")
    print("3. Celery beat ejecutándose:")
    print("   celery -A celery_app beat --loglevel=info")
    print("\nNOTA: Beat generará reportes según el schedule configurado")
    
    input("\nPresiona Enter para continuar...")
    
    while True:
        print("\n" + "=" * 70)
        print("MENU DE OPCIONES")
        print("=" * 70)
        print("1. Ver schedule de reportes programados")
        print("2. Ejecutar reporte de ventas (manual)")
        print("3. Ejecutar reporte de usuarios (manual)")
        print("4. Ejecutar reporte financiero (manual)")
        print("5. Ejecutar reporte de inventario (manual)")
        print("6. Ejecutar todos los reportes inmediatamente")
        print("7. Limpiar reportes antiguos")
        print("0. Salir")
        
        opcion = input("\nSelecciona una opción: ")
        
        if opcion == '0':
            print("\nSaliendo...")
            break
        elif opcion == '1':
            demo_reportes_programados()
        elif opcion == '6':
            demo_ejecucion_inmediata()
        elif opcion == '7':
            resultado = limpiar_reportes_antiguos.delay()
            print(f"\nLimpieza iniciada. Task ID: {resultado.id}")
        elif opcion in ['2', '3', '4', '5']:
            ejecutar_reporte_manual(opcion)
        else:
            print("Opción no válida")
        
        input("\nPresiona Enter para continuar...")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
```

### requirements.txt
```python
celery==5.3.4
redis==5.0.1
reportlab==4.0.7
```

### Iniciar servicios:

   Terminal 1 - Redis:
   ```bash
   docker run -d -p 6379:6379 redis
   ```

   Terminal 2 - Celery Worker:
   ```bash
   celery -A celery_app worker --loglevel=info
   ```

   Terminal 3 - Celery Beat (Scheduler):
   ```bash
   celery -A celery_app beat --loglevel=info
   ```

   Terminal 4 - Programa Principal:
   ```bash
   python main.py
   ```

## Ejercicio 5
### celery_app.py
```python
from celery import Celery
from celery.schedules import crontab

app = Celery(
    'cache_distribuido',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
)

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    # Verificar cada 10 minutos si hay que actualizar cache
    'verificar-cache-10min': {
        'task': 'tasks.verificar_y_actualizar_cache',
        'schedule': 600.0,  # 10 minutos en segundos
    },
    
    # Verificar invalidación cada 2 minutos (más frecuente)
    'verificar-invalidacion-2min': {
        'task': 'tasks.verificar_invalidacion_forzada',
        'schedule': 120.0,  # 2 minutos
    },
    
    # Limpiar caches expirados cada hora
    'limpiar-caches-1h': {
        'task': 'tasks.limpiar_caches_expirados',
        'schedule': 3600.0,  # 1 hora
    },
}

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
)
```

### cache_manager.py
```python
import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis(
            host='localhost',
            port=6379,
            db=4,
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[Dict]:
        try:
            # Obtener datos del cache
            cache_data = self.redis.get(f"cache:{key}")
            
            if not cache_data:
                logger.info(f"CACHE MISS: {key}")
                return None
            
            data = json.loads(cache_data)
            
            # Verificar si está siendo actualizado
            is_updating = self.redis.get(f"cache:{key}:updating")
            
            # Obtener TTL restante
            ttl = self.redis.ttl(f"cache:{key}")
            
            logger.info(f"CACHE HIT: {key} (TTL: {ttl}s, Updating: {bool(is_updating)})")
            
            return {
                'data': data['value'],
                'cached_at': data['cached_at'],
                'version': data.get('version', 1),
                'is_stale': bool(is_updating),
                'ttl_seconds': ttl if ttl > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo cache {key}: {e}")
            return None
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = 600, 
        version: int = None
    ) -> bool:
        try:
            cache_data = {
                'value': value,
                'cached_at': datetime.now().isoformat(),
                'version': version or self._get_next_version(key)
            }
            
            # Guardar en Redis con TTL
            self.redis.setex(
                f"cache:{key}",
                ttl,
                json.dumps(cache_data)
            )
            
            # Guardar metadata adicional
            self.redis.setex(
                f"cache:{key}:metadata",
                ttl + 3600,  # Mantener metadata más tiempo
                json.dumps({
                    'key': key,
                    'ttl': ttl,
                    'created_at': datetime.now().isoformat(),
                    'version': cache_data['version']
                })
            )
            
            # Limpiar flag de actualización
            self.redis.delete(f"cache:{key}:updating")
            
            logger.info(f"CACHE SET: {key} (TTL: {ttl}s, Version: {cache_data['version']})")
            
            return True
        
        except Exception as e:
            logger.error(f"Error guardando cache {key}: {e}")
            return False
    
    def invalidate(self, key: str) -> bool:
        try:
            self.redis.delete(f"cache:{key}")
            self.redis.delete(f"cache:{key}:metadata")
            self.redis.delete(f"cache:{key}:updating")
            self.redis.delete(f"cache:{key}:source_hash")
            
            logger.warning(f"CACHE INVALIDATED: {key}")
            return True
        
        except Exception as e:
            logger.error(f"Error invalidando cache {key}: {e}")
            return False
    
    def mark_as_updating(self, key: str, ttl: int = 300) -> bool:
        try:
            self.redis.setex(
                f"cache:{key}:updating",
                ttl,
                "1"
            )
            logger.info(f"CACHE MARKED AS UPDATING: {key}")
            return True
        
        except Exception as e:
            logger.error(f"Error marcando cache {key}: {e}")
            return False
    
    def is_updating(self, key: str) -> bool:
        return bool(self.redis.get(f"cache:{key}:updating"))
    
    def get_source_hash(self, key: str) -> Optional[str]:
        return self.redis.get(f"cache:{key}:source_hash")
    
    def set_source_hash(self, key: str, hash_value: str, ttl: int = 86400):
        self.redis.setex(
            f"cache:{key}:source_hash",
            ttl,
            hash_value
        )
        logger.debug(f"SOURCE HASH SET: {key} = {hash_value[:8]}...")
    
    def _get_next_version(self, key: str) -> int:
        version_key = f"cache:{key}:version"
        return int(self.redis.incr(version_key))
    
    def get_all_cache_keys(self) -> list:
        return [
            k.decode('utf-8').replace('cache:', '') 
            for k in self.redis.keys('cache:*')
            if not k.decode('utf-8').endswith((':metadata', ':updating', ':source_hash', ':version'))
        ]
    
    def get_cache_stats(self) -> Dict:
        keys = self.get_all_cache_keys()
        
        total_memory = 0
        updating_count = 0
        
        for key in keys:
            # Tamaño en memoria
            memory = self.redis.memory_usage(f"cache:{key}")
            if memory:
                total_memory += memory
            
            # Verificar si está actualizando
            if self.is_updating(key):
                updating_count += 1
        
        return {
            'total_keys': len(keys),
            'updating_count': updating_count,
            'total_memory_bytes': total_memory,
            'total_memory_mb': round(total_memory / (1024 * 1024), 2)
        }
```

### data_source.py
```python
import random
import time
import hashlib
import json
from datetime import datetime


class DataSource:
    
    def __init__(self):
        self.version = 1
        self.last_change = datetime.now()
    
    def get_expensive_data(self, delay_seconds: float = 5.0) -> Dict:
        print(f"\nConsultando fuente de datos... (tardará {delay_seconds}s)")
        
        # Simular procesamiento costoso
        for i in range(int(delay_seconds)):
            time.sleep(1)
            print(f"  Progreso: {((i+1)/delay_seconds)*100:.0f}%", end='\r')
        
        print("\n  Consulta completada")
        
        # Generar datos de ejemplo
        data = {
            'timestamp': datetime.now().isoformat(),
            'version': self.version,
            'metrics': {
                'users_online': random.randint(1000, 5000),
                'requests_per_second': random.randint(100, 1000),
                'error_rate': round(random.uniform(0.1, 5.0), 2),
                'avg_response_time_ms': random.randint(50, 500),
                'database_connections': random.randint(10, 100),
                'cache_hit_rate': round(random.uniform(70, 95), 2)
            },
            'summary': {
                'total_revenue': round(random.uniform(10000, 50000), 2),
                'total_orders': random.randint(100, 1000),
                'active_campaigns': random.randint(5, 20)
            }
        }
        
        return data
    
    def calculate_hash(self, data: Dict) -> str:
        # Serializar datos de forma determinística
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def simulate_change(self):
        self.version += 1
        self.last_change = datetime.now()
        print(f"\nFUENTE DE DATOS CAMBIO (nueva versión: {self.version})")
    
    def needs_update(self, cached_version: int) -> bool:
        return self.version > cached_version
```

### tasks.py
```python
from celery_app import app
from cache_manager import CacheManager
from data_source import DataSource
import time
from datetime import datetime

# Instancias globales
cache = CacheManager()
data_source = DataSource()


@app.task(
    bind=True,
    name='tasks.calcular_datos_costosos',
    max_retries=3,
    time_limit=300
)
def calcular_datos_costosos(self, cache_key: str = 'main_data', force: bool = False):
    try:
        print(f"\n{'='*70}")
        print(f"CALCULANDO DATOS COSTOSOS - {cache_key}")
        print(f"{'='*70}\n")
        
        inicio = time.time()
        
        # Marcar cache como actualizándose
        cache.mark_as_updating(cache_key)
        
        # Obtener datos de la fuente
        print("[1/3] Consultando fuente de datos...")
        datos = data_source.get_expensive_data(delay_seconds=5)
        
        # Calcular hash de los datos
        print("[2/3] Calculando hash...")
        datos_hash = data_source.calculate_hash(datos)
        
        # Verificar si cambió vs cache anterior
        hash_anterior = cache.get_source_hash(cache_key)
        
        if not force and hash_anterior == datos_hash:
            print("  Los datos NO cambiaron, manteniendo cache actual")
            cache.redis.delete(f"cache:{cache_key}:updating")
            return {
                'cache_key': cache_key,
                'changed': False,
                'duration': time.time() - inicio
            }
        
        print("  Datos nuevos o modificados detectados")
        
        # Guardar en cache
        print("[3/3] Guardando en cache...")
        cache.set(cache_key, datos, ttl=600)  # 10 minutos
        cache.set_source_hash(cache_key, datos_hash)
        
        duracion = time.time() - inicio
        
        print(f"\nCACHE ACTUALIZADO en {duracion:.1f}s")
        print(f"{'='*70}\n")
        
        return {
            'cache_key': cache_key,
            'changed': True,
            'version': datos['version'],
            'duration': duracion,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as exc:
        print(f"\nERROR calculando datos: {exc}")
        
        # Limpiar flag de actualización en caso de error
        cache.redis.delete(f"cache:{cache_key}:updating")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        
        return {
            'cache_key': cache_key,
            'error': str(exc),
            'timestamp': datetime.now().isoformat()
        }


@app.task(name='tasks.verificar_y_actualizar_cache')
def verificar_y_actualizar_cache():
    print(f"\n{'='*70}")
    print(f"VERIFICACION PERIODICA DE CACHE - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*70}\n")
    
    cache_key = 'main_data'
    
    # Verificar si cache existe
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        print("Cache no existe, iniciando cálculo...")
        calcular_datos_costosos.delay(cache_key)
        return {'action': 'inicializar', 'reason': 'cache_vacio'}
    
    # Verificar TTL
    ttl_restante = cached_data['ttl_seconds']
    print(f"TTL restante: {ttl_restante}s")
    
    if ttl_restante < 120:  # Menos de 2 minutos
        print("TTL bajo, refrescando cache preventivamente...")
        calcular_datos_costosos.delay(cache_key)
        return {'action': 'refrescar', 'reason': 'ttl_bajo', 'ttl': ttl_restante}
    
    # Verificar si está ya actualizándose
    if cache.is_updating(cache_key):
        print("Cache ya se está actualizando, omitiendo...")
        return {'action': 'omitir', 'reason': 'actualizando'}
    
    print("Cache válido, no requiere actualización")
    return {'action': 'mantener', 'ttl': ttl_restante}


@app.task(name='tasks.verificar_invalidacion_forzada')
def verificar_invalidacion_forzada():
    cache_key = 'main_data'
    
    # Obtener versión actual del cache
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        return {'action': 'ninguna', 'reason': 'cache_vacio'}
    
    cached_version = cached_data.get('version', 0)
    
    # Verificar si la fuente cambió
    if data_source.needs_update(cached_version):
        print(f"\nCAMBIO DETECTADO en fuente de datos")
        print(f"  Version cache: {cached_version}")
        print(f"  Version fuente: {data_source.version}")
        print("  Invalidando y recalculando...\n")
        
        cache.invalidate(cache_key)
        calcular_datos_costosos.delay(cache_key, force=True)
        
        return {
            'action': 'invalidar_y_recalcular',
            'cached_version': cached_version,
            'source_version': data_source.version
        }
    
    return {'action': 'ninguna', 'reason': 'sin_cambios'}


@app.task(name='tasks.limpiar_caches_expirados')
def limpiar_caches_expirados():
    print("\nLimpiando caches expirados...")
    
    todas_las_claves = cache.get_all_cache_keys()
    claves_eliminadas = 0
    
    for key in todas_las_claves:
        ttl = cache.redis.ttl(f"cache:{key}")
        
        # Si TTL es -2, la clave no existe (ya expiró)
        # Si TTL es -1, no tiene expiración (error)
        if ttl < 0:
            cache.invalidate(key)
            claves_eliminadas += 1
    
    print(f"Limpieza completada: {claves_eliminadas} caches eliminados")
    
    return {
        'claves_revisadas': len(todas_las_claves),
        'claves_eliminadas': claves_eliminadas,
        'timestamp': datetime.now().isoformat()
    }
```

### api.py
```python
from flask import Flask, jsonify, request
from cache_manager import CacheManager
from tasks import calcular_datos_costosos, data_source
import time

app_flask = Flask(__name__)
cache_api = CacheManager()


@app_flask.route('/api/data')
def get_data():
    inicio = time.time()
    
    cache_key = request.args.get('key', 'main_data')
    
    # Intentar obtener de cache
    cached = cache_api.get(cache_key)
    
    if cached:
        response = {
            'data': cached['data'],
            'metadata': {
                'cached_at': cached['cached_at'],
                'version': cached['version'],
                'is_stale': cached['is_stale'],
                'ttl_seconds': cached['ttl_seconds'],
                'source': 'cache',
                'response_time_ms': round((time.time() - inicio) * 1000, 2)
            }
        }
        
        if cached['is_stale']:
            response['warning'] = 'Datos en actualización, mostrando versión anterior'
        
        return jsonify(response)
    
    # Cache miss - calcular y retornar
    print(f"Cache miss para {cache_key}, calculando...")
    
    # Disparar cálculo asíncrono
    task = calcular_datos_costosos.delay(cache_key)
    
    # Esperar resultado (para demo, en producción devolver 202 Accepted)
    result = task.get(timeout=30)
    
    # Obtener datos recién calculados
    cached = cache_api.get(cache_key)
    
    return jsonify({
        'data': cached['data'] if cached else None,
        'metadata': {
            'source': 'calculated',
            'calculation_time_s': result.get('duration', 0),
            'response_time_ms': round((time.time() - inicio) * 1000, 2)
        }
    })


@app_flask.route('/api/cache/stats')
def cache_stats():
    stats = cache_api.get_cache_stats()
    keys = cache_api.get_all_cache_keys()
    
    cache_info = []
    for key in keys:
        cached = cache_api.get(key)
        if cached:
            cache_info.append({
                'key': key,
                'version': cached['version'],
                'ttl_seconds': cached['ttl_seconds'],
                'is_stale': cached['is_stale'],
                'cached_at': cached['cached_at']
            })
    
    return jsonify({
        'stats': stats,
        'caches': cache_info
    })


@app_flask.route('/api/cache/invalidate', methods=['POST'])
def invalidate_cache():
    cache_key = request.json.get('key', 'main_data')
    
    cache_api.invalidate(cache_key)
    calcular_datos_costosos.delay(cache_key, force=True)
    
    return jsonify({
        'message': f'Cache {cache_key} invalidado y recalculando',
        'status': 'success'
    })


@app_flask.route('/api/source/change', methods=['POST'])
def simulate_source_change():
    data_source.simulate_change()
    
    return jsonify({
        'message': 'Cambio simulado en fuente de datos',
        'new_version': data_source.version
    })


def run_api(port=5000):
    print(f"\nAPI disponible en: http://localhost:{port}")
    print(f"Endpoints:")
    print(f"  GET  /api/data - Obtener datos cacheados")
    print(f"  GET  /api/cache/stats - Estadísticas del cache")
    print(f"  POST /api/cache/invalidate - Invalidar cache")
    print(f"  POST /api/source/change - Simular cambio en fuente\n")
    
    app_flask.run(port=port, debug=False)
```

### main.py
```python
from tasks import calcular_datos_costosos, cache, data_source
import time
import threading


def demo_cache_basico():
    print("\n" + "=" * 70)
    print("DEMO: FUNCIONAMIENTO BASICO DEL CACHE")
    print("=" * 70 + "\n")
    
    cache_key = 'demo_data'
    
    # Primera consulta - cache miss
    print("1. Primera consulta (cache miss)...")
    cached = cache.get(cache_key)
    print(f"   Resultado: {cached}\n")
    
    # Calcular y guardar
    print("2. Calculando datos...")
    resultado = calcular_datos_costosos.apply_async(args=[cache_key])
    data = resultado.get(timeout=30)
    print(f"   Calculado en {data['duration']:.1f}s\n")
    
    # Segunda consulta - cache hit
    print("3. Segunda consulta (cache hit)...")
    cached = cache.get(cache_key)
    if cached:
        print(f"   Datos obtenidos instantáneamente")
        print(f"   TTL restante: {cached['ttl_seconds']}s")
        print(f"   Version: {cached['version']}\n")
    
    # Limpiar
    cache.invalidate(cache_key)


def demo_actualizacion_automatica():
    print("\n" + "=" * 70)
    print("DEMO: ACTUALIZACION AUTOMATICA")
    print("=" * 70 + "\n")
    
    cache_key = 'auto_update_data'
    
    # Inicializar cache
    print("1. Inicializando cache...")
    resultado = calcular_datos_costosos.apply_async(args=[cache_key])
    resultado.get(timeout=30)
    
    # Simular cambio en fuente
    print("\n2. Simulando cambio en fuente de datos...")
    data_source.simulate_change()
    
    # Verificar que cache detecta cambio
    print("\n3. Esperando detección de cambio...")
    time.sleep(2)
    
    # Obtener datos (debería mostrar warning)
    cached = cache.get(cache_key)
    if cached:
        if cached['is_stale']:
            print("   ADVERTENCIA: Datos en actualización")
        print(f"   Version actual: {cached['version']}")
        print(f"   Version fuente: {data_source.version}")
    
    # Limpiar
    cache.invalidate(cache_key)


def demo_servir_datos_viejos():
    print("\n" + "=" * 70)
    print("DEMO: SERVIR DATOS VIEJOS DURANTE ACTUALIZACION")
    print("=" * 70 + "\n")
    
    cache_key = 'stale_data'
    
    # Inicializar
    print("1. Inicializando cache...")
    resultado = calcular_datos_costosos.apply_async(args=[cache_key])
    resultado.get(timeout=30)
    
    # Obtener datos iniciales
    cached_v1 = cache.get(cache_key)
    print(f"   Version inicial: {cached_v1['version']}")
    
    # Iniciar actualización en background
    print("\n2. Iniciando actualización en background...")
    cache.mark_as_updating(cache_key)
    
    # Simular actualización lenta (no esperar resultado)
    calcular_datos_costosos.apply_async(args=[cache_key, True])
    
    # Mientras actualiza, obtener datos
    print("\n3. Obteniendo datos durante actualización...")
    cached_stale = cache.get(cache_key)
    
    if cached_stale:
        print(f"   Datos disponibles: SI")
        print(f"   Marca de stale: {cached_stale['is_stale']}")
        print(f"   Version: {cached_stale['version']}")
        print("   -> Usuario ve datos viejos con warning")
    
    time.sleep(6)  # Esperar que termine
    
    # Verificar actualización
    cached_new = cache.get(cache_key)
    if cached_new:
        print(f"\n4. Después de actualización:")
        print(f"   Marca de stale: {cached_new['is_stale']}")
        print(f"   Version: {cached_new['version']}")
    
    cache.invalidate(cache_key)


def main():
    print("\n" + "=" * 70)
    print("SISTEMA DE CACHE DISTRIBUIDO CON INVALIDACION")
    print("=" * 70)
    
    print("\nREQUISITOS:")
    print("1. Redis corriendo en localhost:6379")
    print("2. Celery worker:")
    print("   celery -A celery_app worker --loglevel=info")
    print("3. Celery beat:")
    print("   celery -A celery_app beat --loglevel=info")
    print("4. API Flask (opcional):")
    print("   python -c 'from api import run_api; run_api()'")
    
    input("\nPresiona Enter para continuar...")
    
    while True:
        print("\n" + "=" * 70)
        print("MENU DE DEMOS")
        print("=" * 70)
        print("1. Demo: Funcionamiento básico del cache")
        print("2. Demo: Actualización automática")
        print("3. Demo: Servir datos viejos durante actualización")
        print("4. Ver estadísticas del cache")
        print("5. Simular cambio en fuente de datos")
        print("6. Invalidar cache manualmente")
        print("0. Salir")
        
        opcion = input("\nSelecciona una opción: ")
        
        if opcion == '0':
            break
        elif opcion == '1':
            demo_cache_basico()
        elif opcion == '2':
            demo_actualizacion_automatica()
        elif opcion == '3':
            demo_servir_datos_viejos()
        elif opcion == '4':
            stats = cache.get_cache_stats()
            print("\nESTADISTICAS DEL CACHE:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        elif opcion == '5':
            data_source.simulate_change()
            print(f"\nFuente cambiada a version {data_source.version}")
        elif opcion == '6':
            cache.invalidate('main_data')
            print("\nCache 'main_data' invalidado")
        
        input("\nPresiona Enter para continuar...")


if __name__ == "__main__":
    main()
```

### requirements.txt
```python
celery==5.3.4
redis==5.0.1
flask==3.0.0
```

### Iniciar servicios:
  
  Terminal 1 - Redis:
  ```bash
  docker run -d -p 6379:6379 redis
  ```

  Terminal 2 - Celery Worker:
  ```bash
  celery -A celery_app worker --loglevel=info
  ```

  Terminal 3 - Celery Beat:
  ```bash
  celery -A celery_app beat --loglevel=info
  ```

  Terminal 4 - Programa Principal:
  ```bash
  python main.py
  ```

  Terminal 5 - API Flask (opcional):
  ```bash
  python -c "from api import run_api; run_api()"
  ```

## Ejercicio 6
### celery_app.py
```python
from celery import Celery

app = Celery(
    'ml_workflow',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
)

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    result_expires=7200,  # Resultados expiran en 2 horas
)
```

### metrics.py
```python
import redis
import json
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsStore:
    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis(
            host='localhost',
            port=6379,
            db=5,
            decode_responses=True
        )
    
    def save_step_metrics(self, workflow_id: str, step: str, metrics: Dict):
        key = f"workflow:{workflow_id}:step:{step}"
        
        data = {
            'step': step,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        self.redis.setex(key, 7200, json.dumps(data))
        
        # También agregar a lista de pasos
        self.redis.lpush(f"workflow:{workflow_id}:steps", step)
        
        logger.info(f"Métricas guardadas: {workflow_id} / {step}")
    
    def get_step_metrics(self, workflow_id: str, step: str) -> Dict:
        key = f"workflow:{workflow_id}:step:{step}"
        data = self.redis.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    def get_workflow_summary(self, workflow_id: str) -> Dict:
        steps = self.redis.lrange(f"workflow:{workflow_id}:steps", 0, -1)
        
        summary = {
            'workflow_id': workflow_id,
            'total_steps': len(steps),
            'steps': {}
        }
        
        for step in steps:
            metrics = self.get_step_metrics(workflow_id, step)
            if metrics:
                summary['steps'][step] = metrics
        
        return summary
    
    def clear_workflow(self, workflow_id: str):
        keys = self.redis.keys(f"workflow:{workflow_id}:*")
        if keys:
            self.redis.delete(*keys)
```

### models.py
```python
import random
import time
from typing import Dict, List, Tuple
import numpy as np


class MLModelSimulator:
    MODELS = {
        'linear': {'train_time': 2, 'accuracy_range': (0.70, 0.80)},
        'rf': {'train_time': 4, 'accuracy_range': (0.80, 0.88)},
        'xgboost': {'train_time': 5, 'accuracy_range': (0.85, 0.92)},
        'neural_net': {'train_time': 8, 'accuracy_range': (0.82, 0.91)},
        'svm': {'train_time': 3, 'accuracy_range': (0.75, 0.85)},
    }
    
    @staticmethod
    def generate_dataset(rows: int = 1000) -> Dict:
        return {
            'features': np.random.randn(rows, 10).tolist(),
            'labels': np.random.randint(0, 2, rows).tolist(),
            'rows': rows,
            'columns': 10
        }
    
    @staticmethod
    def train_model(model_type: str, dataset: Dict) -> Dict:
        if model_type not in MLModelSimulator.MODELS:
            raise ValueError(f"Modelo desconocido: {model_type}")
        
        config = MLModelSimulator.MODELS[model_type]
        
        # Simular entrenamiento
        train_time = config['train_time']
        for i in range(train_time):
            time.sleep(1)
            progress = ((i + 1) / train_time) * 100
            print(f"  Entrenando {model_type}: {progress:.0f}%", end='\r')
        
        print()
        
        # Generar métricas
        acc_min, acc_max = config['accuracy_range']
        accuracy = random.uniform(acc_min, acc_max)
        
        return {
            'model_type': model_type,
            'accuracy': round(accuracy, 4),
            'precision': round(accuracy * random.uniform(0.95, 1.05), 4),
            'recall': round(accuracy * random.uniform(0.95, 1.05), 4),
            'f1_score': round(accuracy * random.uniform(0.97, 1.03), 4),
            'train_time_seconds': train_time,
            'dataset_size': dataset['rows']
        }
    
    @staticmethod
    def evaluate_model(model_result: Dict, test_data: Dict) -> Dict:
        time.sleep(1)  # Simular evaluación
        
        # Degradar un poco las métricas (overfitting simulado)
        degradation = random.uniform(0.92, 0.98)
        
        return {
            **model_result,
            'test_accuracy': round(model_result['accuracy'] * degradation, 4),
            'test_f1_score': round(model_result['f1_score'] * degradation, 4),
            'evaluated': True
        }
```

### tasks.py
```python
from celery_app import app
from models import MLModelSimulator
from metrics import MetricsStore
import time
import random
from datetime import datetime

metrics_store = MetricsStore()


@app.task(
    bind=True,
    name='tasks.preparar_datos_fuente1',
    max_retries=2
)
def preparar_datos_fuente1(self, workflow_id: str):
    try:
        print(f"\n[FUENTE 1] Obteniendo datos de API...")
        time.sleep(2)
        
        # Simular fallo ocasional
        if random.random() < 0.1:
            raise Exception("Error de red en API")
        
        dataset = MLModelSimulator.generate_dataset(rows=3000)
        
        metrics_store.save_step_metrics(workflow_id, 'preparacion_fuente1', {
            'rows': dataset['rows'],
            'source': 'API externa',
            'duration': 2.0
        })
        
        print(f"[FUENTE 1] {dataset['rows']} filas obtenidas")
        
        return {
            'source': 'fuente1',
            'data': dataset,
            'workflow_id': workflow_id
        }
    
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=5)
        raise


@app.task(name='tasks.preparar_datos_fuente2')
def preparar_datos_fuente2(workflow_id: str):
    print(f"\n[FUENTE 2] Consultando base de datos...")
    time.sleep(3)
    
    dataset = MLModelSimulator.generate_dataset(rows=2500)
    
    metrics_store.save_step_metrics(workflow_id, 'preparacion_fuente2', {
        'rows': dataset['rows'],
        'source': 'PostgreSQL',
        'duration': 3.0
    })
    
    print(f"[FUENTE 2] {dataset['rows']} filas obtenidas")
    
    return {
        'source': 'fuente2',
        'data': dataset,
        'workflow_id': workflow_id
    }


@app.task(name='tasks.preparar_datos_fuente3')
def preparar_datos_fuente3(workflow_id: str):
    print(f"\n[FUENTE 3] Leyendo archivos CSV...")
    time.sleep(2)
    
    dataset = MLModelSimulator.generate_dataset(rows=2000)
    
    metrics_store.save_step_metrics(workflow_id, 'preparacion_fuente3', {
        'rows': dataset['rows'],
        'source': 'CSV files',
        'duration': 2.0
    })
    
    print(f"[FUENTE 3] {dataset['rows']} filas obtenidas")
    
    return {
        'source': 'fuente3',
        'data': dataset,
        'workflow_id': workflow_id
    }


@app.task(name='tasks.combinar_datasets')
def combinar_datasets(datasets: List[Dict]):
    print(f"\n[COMBINAR] Fusionando {len(datasets)} datasets...")
    time.sleep(2)
    
    workflow_id = datasets[0]['workflow_id']
    
    # Combinar datos
    total_rows = sum(d['data']['rows'] for d in datasets)
    
    # Crear dataset combinado
    combined = {
        'features': [],
        'labels': [],
        'rows': total_rows,
        'columns': 10,
        'sources': [d['source'] for d in datasets]
    }
    
    for dataset in datasets:
        combined['features'].extend(dataset['data']['features'])
        combined['labels'].extend(dataset['data']['labels'])
    
    # Dividir en train/test
    split_idx = int(total_rows * 0.8)
    
    train_data = {
        'features': combined['features'][:split_idx],
        'labels': combined['labels'][:split_idx],
        'rows': split_idx,
        'columns': 10
    }
    
    test_data = {
        'features': combined['features'][split_idx:],
        'labels': combined['labels'][split_idx:],
        'rows': total_rows - split_idx,
        'columns': 10
    }
    
    metrics_store.save_step_metrics(workflow_id, 'combinacion', {
        'total_rows': total_rows,
        'train_rows': train_data['rows'],
        'test_rows': test_data['rows'],
        'sources_count': len(datasets),
        'duration': 2.0
    })
    
    print(f"[COMBINAR] Dataset combinado: {total_rows} filas")
    print(f"[COMBINAR] Train: {train_data['rows']}, Test: {test_data['rows']}")
    
    return {
        'train_data': train_data,
        'test_data': test_data,
        'workflow_id': workflow_id
    }


@app.task(
    bind=True,
    name='tasks.entrenar_modelo',
    time_limit=300
)
def entrenar_modelo(self, combined_data: Dict, model_type: str):
    print(f"\n[ENTRENAR] Modelo: {model_type}")
    
    workflow_id = combined_data['workflow_id']
    train_data = combined_data['train_data']
    
    inicio = time.time()
    
    # Entrenar modelo
    model_result = MLModelSimulator.train_model(model_type, train_data)
    
    duracion = time.time() - inicio
    
    metrics_store.save_step_metrics(
        workflow_id, 
        f'entrenamiento_{model_type}', 
        {
            **model_result,
            'duration': round(duracion, 2)
        }
    )
    
    print(f"[ENTRENAR] {model_type} completado - Accuracy: {model_result['accuracy']:.4f}")
    
    return {
        **model_result,
        'test_data': combined_data['test_data'],
        'workflow_id': workflow_id
    }


@app.task(name='tasks.evaluar_modelo')
def evaluar_modelo(model_result: Dict):
    model_type = model_result['model_type']
    print(f"\n[EVALUAR] Modelo: {model_type}")
    
    workflow_id = model_result['workflow_id']
    test_data = model_result['test_data']
    
    # Evaluar
    evaluated = MLModelSimulator.evaluate_model(model_result, test_data)
    
    metrics_store.save_step_metrics(
        workflow_id,
        f'evaluacion_{model_type}',
        {
            'model_type': model_type,
            'train_accuracy': evaluated['accuracy'],
            'test_accuracy': evaluated['test_accuracy'],
            'test_f1_score': evaluated['test_f1_score']
        }
    )
    
    print(f"[EVALUAR] {model_type} - Test Accuracy: {evaluated['test_accuracy']:.4f}")
    
    return evaluated


@app.task(name='tasks.seleccionar_mejor_modelo')
def seleccionar_mejor_modelo(evaluated_models: List[Dict]):
    print(f"\n[SELECCIONAR] Comparando {len(evaluated_models)} modelos...")
    
    workflow_id = evaluated_models[0]['workflow_id']
    
    # Encontrar mejor modelo por test_accuracy
    mejor_modelo = max(evaluated_models, key=lambda m: m['test_accuracy'])
    
    # Ranking de modelos
    ranking = sorted(
        evaluated_models,
        key=lambda m: m['test_accuracy'],
        reverse=True
    )
    
    print(f"\n[SELECCIONAR] Ranking de modelos:")
    for i, modelo in enumerate(ranking, 1):
        print(f"  {i}. {modelo['model_type']:15} - Test Acc: {modelo['test_accuracy']:.4f}")
    
    print(f"\n[SELECCIONAR] Mejor modelo: {mejor_modelo['model_type']}")
    print(f"              Test Accuracy: {mejor_modelo['test_accuracy']:.4f}")
    
    metrics_store.save_step_metrics(
        workflow_id,
        'seleccion_mejor_modelo',
        {
            'mejor_modelo': mejor_modelo['model_type'],
            'test_accuracy': mejor_modelo['test_accuracy'],
            'ranking': [
                {'model': m['model_type'], 'accuracy': m['test_accuracy']}
                for m in ranking
            ]
        }
    )
    
    return {
        'mejor_modelo': mejor_modelo,
        'ranking': ranking,
        'workflow_id': workflow_id
    }


@app.task(name='tasks.desplegar_modelo')
def desplegar_modelo(seleccion_result: Dict):
    print(f"\n[DESPLEGAR] Iniciando despliegue...")
    
    workflow_id = seleccion_result['workflow_id']
    mejor_modelo = seleccion_result['mejor_modelo']
    
    # Simular despliegue
    print(f"[DESPLEGAR] Empaquetando modelo {mejor_modelo['model_type']}...")
    time.sleep(2)
    
    print(f"[DESPLEGAR] Subiendo a servidor de producción...")
    time.sleep(2)
    
    print(f"[DESPLEGAR] Actualizando endpoint de API...")
    time.sleep(1)
    
    print(f"[DESPLEGAR] Verificando health check...")
    time.sleep(1)
    
    deployment_info = {
        'modelo': mejor_modelo['model_type'],
        'version': f"v{int(time.time())}",
        'accuracy': mejor_modelo['test_accuracy'],
        'deployed_at': datetime.now().isoformat(),
        'endpoint': f"https://api.empresa.com/ml/{mejor_modelo['model_type']}"
    }
    
    metrics_store.save_step_metrics(
        workflow_id,
        'despliegue',
        deployment_info
    )
    
    print(f"\n[DESPLEGAR] Modelo desplegado exitosamente!")
    print(f"[DESPLEGAR] Endpoint: {deployment_info['endpoint']}")
    print(f"[DESPLEGAR] Versión: {deployment_info['version']}")
    
    return {
        'deployment': deployment_info,
        'workflow_id': workflow_id,
        'success': True
    }
```

### workflow.py
```python
from celery import chain, group, chord
from tasks import (
    preparar_datos_fuente1,
    preparar_datos_fuente2,
    preparar_datos_fuente3,
    combinar_datasets,
    entrenar_modelo,
    evaluar_modelo,
    seleccionar_mejor_modelo,
    desplegar_modelo
)
import uuid


def crear_workflow_ml(workflow_id: str = None):
    if workflow_id is None:
        workflow_id = str(uuid.uuid4())
    
    print(f"\nCreando workflow ML con ID: {workflow_id}")
    
    # Paso 1: Preparar datos en paralelo (GROUP)
    preparacion = group(
        preparar_datos_fuente1.s(workflow_id),
        preparar_datos_fuente2.s(workflow_id),
        preparar_datos_fuente3.s(workflow_id),
    )
    
    # Paso 2: Combinar datasets
    combinacion = combinar_datasets.s()
    
    # Paso 3: Entrenar modelos en paralelo (GROUP)
    # Los modelos reciben el dataset combinado
    modelos = ['linear', 'rf', 'xgboost', 'neural_net', 'svm']
    
    # Nota: group con signature parcial
    entrenamiento = group(
        entrenar_modelo.s(model_type=modelo)
        for modelo in modelos
    )
    
    # Paso 4: Evaluar cada modelo (automático con chain en group)
    evaluacion = group(
        evaluar_modelo.s()
        for _ in modelos
    )
    
    # Paso 5: Seleccionar mejor modelo (CHORD)
    # Chord ejecuta las tareas en paralelo y luego el callback
    seleccion_y_despliegue = chord(
        evaluacion
    )(seleccionar_mejor_modelo.s())
    
    # Paso 6: Desplegar
    despliegue = desplegar_modelo.s()
    
    # Construir workflow completo con CHAIN
    workflow = chain(
        preparacion,      # Group: 3 fuentes en paralelo
        combinacion,      # Combina resultados
        entrenamiento,    # Group: 5 modelos en paralelo
        seleccion_y_despliegue,  # Chord: evalúa y selecciona mejor
        despliegue        # Despliega a producción
    )
    
    return workflow, workflow_id


def crear_workflow_simplificado(workflow_id: str = None):
    if workflow_id is None:
        workflow_id = str(uuid.uuid4())
    
    # Solo 2 fuentes y 2 modelos
    preparacion = group(
        preparar_datos_fuente1.s(workflow_id),
        preparar_datos_fuente2.s(workflow_id),
    )
    
    combinacion = combinar_datasets.s()
    
    entrenamiento_y_evaluacion = chord(
        group(
            chain(entrenar_modelo.s(model_type='rf'), evaluar_modelo.s()),
            chain(entrenar_modelo.s(model_type='xgboost'), evaluar_modelo.s()),
        )
    )(seleccionar_mejor_modelo.s())
    
    despliegue = desplegar_modelo.s()
    
    workflow = chain(
        preparacion,
        combinacion,
        entrenamiento_y_evaluacion,
        despliegue
    )
    
    return workflow, workflow_id
```

### main.py
```python
from workflow import crear_workflow_ml, crear_workflow_simplificado
from metrics import MetricsStore
import time
from celery.result import AsyncResult
from celery_app import app as celery_app


def ejecutar_workflow_completo():
    print("\n" + "=" * 70)
    print("EJECUTANDO WORKFLOW COMPLETO DE ML")
    print("=" * 70)
    
    # Crear workflow
    workflow, workflow_id = crear_workflow_ml()
    
    print(f"\nWorkflow ID: {workflow_id}")
    print("\nEstructura del workflow:")
    print("  1. Preparar datos (3 fuentes en paralelo)")
    print("  2. Combinar datasets")
    print("  3. Entrenar modelos (5 modelos en paralelo)")
    print("  4. Evaluar modelos")
    print("  5. Seleccionar mejor modelo")
    print("  6. Desplegar a producción")
    
    input("\nPresiona Enter para iniciar...")
    
    # Ejecutar workflow
    inicio = time.time()
    resultado = workflow.apply_async()
    
    print(f"\nWorkflow iniciado. Task ID: {resultado.id}")
    print("Esperando completación...")
    print("(Puedes cancelar con Ctrl+C)\n")
    
    try:
        # Monitorear progreso
        while not resultado.ready():
            print(".", end="", flush=True)
            time.sleep(2)
        
        # Obtener resultado final
        resultado_final = resultado.get(timeout=300)
        
        duracion = time.time() - inicio
        
        print("\n\n" + "=" * 70)
        print("WORKFLOW COMPLETADO")
        print("=" * 70)
        print(f"\nTiempo total: {duracion:.1f}s ({duracion/60:.1f} minutos)")
        
        if resultado_final.get('success'):
            deployment = resultado_final['deployment']
            print(f"\nModelo desplegado:")
            print(f"  Tipo: {deployment['modelo']}")
            print(f"  Versión: {deployment['version']}")
            print(f"  Accuracy: {deployment['accuracy']:.4f}")
            print(f"  Endpoint: {deployment['endpoint']}")
        
        # Mostrar métricas
        mostrar_metricas_workflow(workflow_id)
        
        return resultado_final
    
    except KeyboardInterrupt:
        print("\n\nCANCELANDO WORKFLOW...")
        cancelar_workflow(resultado.id)
        return None


def ejecutar_workflow_simplificado():
    print("\n" + "=" * 70)
    print("EJECUTANDO WORKFLOW SIMPLIFICADO")
    print("=" * 70)
    
    workflow, workflow_id = crear_workflow_simplificado()
    
    print(f"\nWorkflow ID: {workflow_id}")
    print("(Solo 2 fuentes y 2 modelos para prueba rápida)\n")
    
    inicio = time.time()
    resultado = workflow.apply_async()
    
    print(f"Workflow iniciado. Task ID: {resultado.id}\n")
    
    try:
        resultado_final = resultado.get(timeout=120)
        duracion = time.time() - inicio
        
        print(f"\nWorkflow completado en {duracion:.1f}s")
        
        mostrar_metricas_workflow(workflow_id)
        
        return resultado_final
    
    except KeyboardInterrupt:
        print("\nCancelando...")
        cancelar_workflow(resultado.id)
        return None


def cancelar_workflow(task_id: str):
    print(f"Intentando cancelar workflow {task_id}...")
    
    # Revocar tarea
    celery_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
    
    print("Workflow cancelado")
    print("NOTA: Algunas tareas ya iniciadas pueden completarse")


def mostrar_metricas_workflow(workflow_id: str):
    print("\n" + "=" * 70)
    print("METRICAS DEL WORKFLOW")
    print("=" * 70)
    
    metrics_store = MetricsStore()
    summary = metrics_store.get_workflow_summary(workflow_id)
    
    if not summary['steps']:
        print("\nNo hay métricas disponibles")
        return
    
    print(f"\nWorkflow ID: {workflow_id}")
    print(f"Total de pasos: {summary['total_steps']}")
    
    # Agrupar por tipo
    preparacion_steps = [k for k in summary['steps'] if 'preparacion' in k]
    entrenamiento_steps = [k for k in summary['steps'] if 'entrenamiento' in k]
    evaluacion_steps = [k for k in summary['steps'] if 'evaluacion' in k]
    
    if preparacion_steps:
        print("\n--- PREPARACION DE DATOS ---")
        total_rows = 0
        for step in preparacion_steps:
            metrics = summary['steps'][step]['metrics']
            print(f"  {step}: {metrics.get('rows', 0)} filas desde {metrics.get('source', 'N/A')}")
            total_rows += metrics.get('rows', 0)
        print(f"  TOTAL: {total_rows} filas")
    
    if 'combinacion' in summary['steps']:
        print("\n--- COMBINACION ---")
        metrics = summary['steps']['combinacion']['metrics']
        print(f"  Train: {metrics['train_rows']} filas")
        print(f"  Test: {metrics['test_rows']} filas")
    
    if entrenamiento_steps:
        print("\n--- ENTRENAMIENTO ---")
        for step in sorted(entrenamiento_steps):
            metrics = summary['steps'][step]['metrics']
            print(f"  {metrics['model_type']:15} - Accuracy: {metrics['accuracy']:.4f}")
    
    if evaluacion_steps:
        print("\n--- EVALUACION ---")
        for step in sorted(evaluacion_steps):
            metrics = summary['steps'][step]['metrics']
            print(f"  {metrics['model_type']:15} - Test Acc: {metrics['test_accuracy']:.4f}")
    
    if 'seleccion_mejor_modelo' in summary['steps']:
        print("\n--- SELECCION ---")
        metrics = summary['steps']['seleccion_mejor_modelo']['metrics']
        print(f"  Mejor modelo: {metrics['mejor_modelo']}")
        print(f"  Test Accuracy: {metrics['test_accuracy']:.4f}")
    
    if 'despliegue' in summary['steps']:
        print("\n--- DESPLIEGUE ---")
        metrics = summary['steps']['despliegue']['metrics']
        print(f"  Modelo: {metrics['modelo']}")
        print(f"  Versión: {metrics['version']}")
        print(f"  Endpoint: {metrics['endpoint']}")
    
    print("\n" + "=" * 70)


def main():
    print("\n" + "=" * 70)
    print("WORKFLOW COMPLEJO DE ML CON CELERY CANVAS")
    print("=" * 70)
    
    print("\nREQUISITOS:")
    print("1. Redis corriendo en localhost:6379")
    print("2. Celery worker con concurrencia:")
    print("   celery -A celery_app worker --loglevel=info --concurrency=8")
    
    input("\nPresiona Enter para continuar...")
    
    while True:
        print("\n" + "=" * 70)
        print("MENU DE OPCIONES")
        print("=" * 70)
        print("1. Ejecutar workflow completo (5 modelos)")
        print("2. Ejecutar workflow simplificado (2 modelos)")
        print("3. Ver métricas de workflow anterior")
        print("4. Limpiar métricas")
        print("0. Salir")
        
        opcion = input("\nSelecciona una opción: ")
        
        if opcion == '0':
            break
        elif opcion == '1':
            ejecutar_workflow_completo()
        elif opcion == '2':
            ejecutar_workflow_simplificado()
        elif opcion == '3':
            workflow_id = input("Workflow ID: ")
            mostrar_metricas_workflow(workflow_id)
        elif opcion == '4':
            metrics_store = MetricsStore()
            workflow_id = input("Workflow ID a limpiar: ")
            metrics_store.clear_workflow(workflow_id)
            print(f"Métricas de {workflow_id} eliminadas")
        else:
            print("Opción no válida")
        
        input("\nPresiona Enter para continuar...")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
```

### requirements.txt
```python
celery==5.3.4
redis==5.0.1
numpy==1.24.3
```

### Iniciar servicios:
Redis
```bash
docker run -d -p 6379:6379 redis
```
Worker con alta concurrencia
```bash
celery -A celery_app worker --loglevel=info --concurrency=8
```
Programa
```bash
python main.py
```