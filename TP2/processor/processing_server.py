import socketserver
import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Dict, Any
import sys
import os

# Importar módulos comunes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.protocol import (
    receive_message_sync, send_message_sync,
    MSG_TYPE_SCREENSHOT, MSG_TYPE_PERFORMANCE, MSG_TYPE_IMAGE_PROCESSING,
    MSG_TYPE_RESPONSE, MSG_TYPE_ERROR
)
from processor.screenshot import generate_screenshot
from processor.performance import analyze_performance
from processor.image_processor import process_images

logger = logging.getLogger(__name__)

# Pool global de procesos
process_pool: ProcessPoolExecutor = None


def process_screenshot_task(data: Dict[str, Any]) -> Dict[str, Any]:
    url = data.get('url')
    timeout = data.get('timeout', 30)
    
    screenshot = generate_screenshot(url, timeout)
    
    return {
        "screenshot": screenshot,
        "success": screenshot is not None
    }


def process_performance_task(data: Dict[str, Any]) -> Dict[str, Any]:
    url = data.get('url')
    timeout = data.get('timeout', 30)
    
    performance_data = analyze_performance(url, timeout)
    
    return {
        "performance": performance_data,
        "success": performance_data is not None
    }


def process_images_task(data: Dict[str, Any]) -> Dict[str, Any]:
    url = data.get('url')
    html_content = data.get('html_content', '')
    max_images = data.get('max_images', 5)
    
    thumbnails = process_images(url, html_content, max_images)
    
    return {
        "thumbnails": thumbnails,
        "count": len(thumbnails),
        "success": True
    }


class ProcessingRequestHandler(socketserver.BaseRequestHandler):
    
    def handle(self):
        """Maneja una conexión entrante."""
        client_address = self.client_address
        logger.info(f"Nueva conexión desde {client_address}")
        
        try:
            # Recibir mensaje
            message = receive_message_sync(self.request)
            msg_type = message.msg_type
            data = message.data
            
            logger.info(f"Recibido mensaje de tipo: {msg_type}")
            
            # Procesar según el tipo
            result = self.process_task(msg_type, data)
            
            # Enviar respuesta
            send_message_sync(self.request, MSG_TYPE_RESPONSE, result)
            logger.info(f"Respuesta enviada a {client_address}")
            
        except Exception as e:
            logger.error(f"Error al procesar request: {e}")
            try:
                error_data = {"error": str(e), "success": False}
                send_message_sync(self.request, MSG_TYPE_ERROR, error_data)
            except Exception:
                pass
    
    def process_task(self, msg_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        global process_pool
        
        # Seleccionar función según tipo
        task_functions = {
            MSG_TYPE_SCREENSHOT: process_screenshot_task,
            MSG_TYPE_PERFORMANCE: process_performance_task,
            MSG_TYPE_IMAGE_PROCESSING: process_images_task
        }
        
        task_function = task_functions.get(msg_type)
        if not task_function:
            logger.error(f"Tipo de tarea desconocido: {msg_type}")
            return {"error": f"Unknown task type: {msg_type}", "success": False}
        
        try:
            # Ejecutar en el pool con timeout
            timeout = data.get('timeout', 30) + 10  # +10 segundos de margen
            future = process_pool.submit(task_function, data)
            result = future.result(timeout=timeout)
            
            logger.info(f"Tarea {msg_type} completada exitosamente")
            return result
            
        except FuturesTimeoutError:
            logger.error(f"Timeout al procesar tarea {msg_type}")
            return {"error": "Task timeout", "success": False}
        except Exception as e:
            logger.error(f"Error al ejecutar tarea {msg_type}: {e}")
            return {"error": str(e), "success": False}


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_processing_server(host: str, port: int, num_processes: int = None):
    global process_pool
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Determinar número de procesos
    if num_processes is None:
        num_processes = mp.cpu_count()
    
    logger.info(f"Iniciando servidor de procesamiento en {host}:{port}")
    logger.info(f"Pool de procesos: {num_processes} workers")
    
    # Crear pool de procesos
    process_pool = ProcessPoolExecutor(max_workers=num_processes)
    
    try:
        # Crear y arrancar servidor
        server = ThreadedTCPServer((host, port), ProcessingRequestHandler)
        logger.info(f"Servidor de procesamiento escuchando en {host}:{port}")
        
        # Ejecutar servidor
        server.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Servidor interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error en el servidor: {e}")
    finally:
        # Cleanup
        logger.info("Cerrando servidor de procesamiento...")
        if process_pool:
            process_pool.shutdown(wait=True)
        logger.info("Servidor cerrado")