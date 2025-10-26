import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any
from aiohttp import web
from urllib.parse import urlparse

# Imports locales
from .async_http import download_page_with_metadata
from .html_parser import parse_html
from .metadata_extractor import get_all_metadata
from .task_manager import TaskManager, TaskStatus
from common.socket_client import AsyncSocketClient
from common.protocol import MSG_TYPE_SCREENSHOT, MSG_TYPE_PERFORMANCE, MSG_TYPE_IMAGE_PROCESSING

logger = logging.getLogger(__name__)


class ScrapingServer:
    def __init__(self, host: str, port: int, processing_host: str, processing_port: int):
        self.host = host
        self.port = port
        self.processing_host = processing_host
        self.processing_port = processing_port
        self.app = web.Application()
        self.task_manager = TaskManager()
        
        # Configurar rutas
        self._setup_routes()
    
    def _setup_routes(self):
        self.app.router.add_get('/', self.handle_root)
        self.app.router.add_get('/scrape', self.handle_scrape)
        self.app.router.add_get('/status/{task_id}', self.handle_status)
        self.app.router.add_get('/result/{task_id}', self.handle_result)
        self.app.router.add_get('/tasks', self.handle_tasks)
    
    async def handle_root(self, request: web.Request) -> web.Response:
        info = {
            "service": "Web Scraping Server",
            "version": "1.0.0",
            "endpoints": {
                "/scrape?url=<URL>": "Iniciar scraping de una URL (devuelve task_id)",
                "/status/<task_id>": "Consultar estado de una tarea",
                "/result/<task_id>": "Obtener resultado de una tarea completada",
                "/tasks": "Listar todas las tareas"
            }
        }
        return web.json_response(info)
    
    async def handle_scrape(self, request: web.Request) -> web.Response:
        url = request.query.get('url')
        
        if not url:
            return web.json_response(
                {"error": "Missing 'url' parameter"},
                status=400
            )
        
        # Validar URL
        if not self._is_valid_url(url):
            return web.json_response(
                {"error": "Invalid URL"},
                status=400
            )
        
        # Crear tarea
        task_id = await self.task_manager.create_task(url)
        
        # Iniciar procesamiento en background
        asyncio.create_task(self._process_scraping_task(task_id, url))
        
        # Devolver task_id inmediatamente
        return web.json_response({
            "task_id": task_id,
            "status": "pending",
            "url": url,
            "message": "Task created. Use /status/{task_id} to check progress."
        })
    
    async def handle_status(self, request: web.Request) -> web.Response:
        task_id = request.match_info.get('task_id')
        
        status = await self.task_manager.get_task_status(task_id)
        
        if not status:
            return web.json_response(
                {"error": "Task not found"},
                status=404
            )
        
        return web.json_response(status)
    
    async def handle_result(self, request: web.Request) -> web.Response:
        task_id = request.match_info.get('task_id')
        
        result = await self.task_manager.get_task_result(task_id)
        
        if not result:
            return web.json_response(
                {"error": "Task not found"},
                status=404
            )
        
        # Si la tarea no está completada
        if result.get('status') in ['pending', 'scraping', 'processing']:
            return web.json_response(
                {
                    "message": "Task not completed yet",
                    "status": result.get('status')
                },
                status=202  # Accepted
            )
        
        return web.json_response(result)
    
    async def handle_tasks(self, request: web.Request) -> web.Response:
        counts = await self.task_manager.count_tasks_by_status()
        return web.json_response({
            "total_tasks": sum(counts.values()),
            "by_status": counts
        })
    
    async def _process_scraping_task(self, task_id: str, url: str):
        try:
            logger.info(f"Iniciando procesamiento de tarea {task_id}")
            
            # Fase 1: Scraping
            await self.task_manager.update_task_status(task_id, TaskStatus.SCRAPING)
            scraping_data = await self._do_scraping(url)
            
            if not scraping_data:
                await self.task_manager.set_task_error(task_id, "Failed to scrape URL")
                return
            
            # Fase 2: Procesamiento
            await self.task_manager.update_task_status(task_id, TaskStatus.PROCESSING)
            processing_data = await self._do_processing(url, scraping_data.get('html_content', ''))
            
            # Consolidar resultado
            result = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "scraping_data": scraping_data.get('data', {}),
                "processing_data": processing_data,
                "status": "success"
            }
            
            await self.task_manager.set_task_result(task_id, result)
            logger.info(f"Tarea {task_id} completada exitosamente")
            
        except Exception as e:
            logger.error(f"Error procesando tarea {task_id}: {e}")
            await self.task_manager.set_task_error(task_id, str(e))
    
    async def _do_scraping(self, url: str) -> Dict[str, Any]:
        try:
            # Descargar página
            page_data = await download_page_with_metadata(url, timeout=30)
            
            if not page_data:
                logger.error(f"Failed to download: {url}")
                return None
            
            html_content = page_data['content']
            
            # Parsear HTML
            parsed_data = parse_html(html_content, url)
            
            # Extraer metadatos
            metadata = get_all_metadata(html_content)
            
            # Consolidar
            scraping_data = {
                "title": parsed_data.get('title', ''),
                "links": parsed_data.get('links', []),
                "meta_tags": metadata.get('meta_tags', {}),
                "structure": parsed_data.get('structure', {}),
                "images_count": parsed_data.get('images_count', 0),
                "canonical_url": metadata.get('canonical_url', ''),
                "language": metadata.get('language', '')
            }
            
            return {
                "data": scraping_data,
                "html_content": html_content
            }
            
        except Exception as e:
            logger.error(f"Error in scraping: {e}")
            return None
    
    async def _do_processing(self, url: str, html_content: str) -> Dict[str, Any]:
        processing_data = {
            "screenshot": None,
            "performance": None,
            "thumbnails": []
        }
        
        try:
            # Crear cliente socket
            client = AsyncSocketClient(self.processing_host, self.processing_port)
            
            # Screenshot
            screenshot_result = await client.send_request(
                MSG_TYPE_SCREENSHOT,
                {"url": url, "timeout": 30}
            )
            if screenshot_result and screenshot_result.get('success'):
                processing_data['screenshot'] = screenshot_result.get('screenshot')
            
            # Performance
            performance_result = await client.send_request(
                MSG_TYPE_PERFORMANCE,
                {"url": url, "timeout": 30}
            )
            if performance_result and performance_result.get('success'):
                processing_data['performance'] = performance_result.get('performance')
            
            # Image processing
            image_result = await client.send_request(
                MSG_TYPE_IMAGE_PROCESSING,
                {"url": url, "html_content": html_content, "max_images": 5}
            )
            if image_result and image_result.get('success'):
                processing_data['thumbnails'] = image_result.get('thumbnails', [])
            
            await client.close()
            
        except Exception as e:
            logger.error(f"Error in processing: {e}")
        
        return processing_data
    
    def _is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ('http', 'https')
        except Exception:
            return False
    
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Servidor de scraping iniciado en http://{self.host}:{self.port}")
    
    def run(self):
        web.run_app(self.app, host=self.host, port=self.port)


async def start_scraping_server(host: str, port: int, processing_host: str, processing_port: int):
    server = ScrapingServer(host, port, processing_host, processing_port)
    await server.start()
    
    # Mantener el servidor corriendo
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")