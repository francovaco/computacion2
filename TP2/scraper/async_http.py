import asyncio
import logging
from typing import Optional, Dict
import aiohttp
from aiohttp import ClientTimeout, ClientError

logger = logging.getLogger(__name__)

# Configuración por defecto
DEFAULT_TIMEOUT = 30
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


class AsyncHTTPClient:
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = ClientTimeout(total=timeout)
        self.headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def fetch(self, url: str) -> Optional[Dict]:
        try:
            logger.info(f"Descargando: {url}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=self.headers, allow_redirects=True) as response:
                    # Verificar status
                    if response.status != 200:
                        logger.warning(f"Status code {response.status} para {url}")
                    
                    # Leer contenido
                    content = await response.text()
                    
                    result = {
                        'content': content,
                        'status': response.status,
                        'headers': dict(response.headers),
                        'url': str(response.url),  # URL final después de redirects
                        'content_type': response.headers.get('Content-Type', '')
                    }
                    
                    logger.info(f"Descarga exitosa: {url} ({len(content)} bytes)")
                    return result
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout al descargar {url}")
            return None
        except ClientError as e:
            logger.error(f"Error de cliente al descargar {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al descargar {url}: {e}")
            return None
    
    async def fetch_multiple(self, urls: list) -> Dict[str, Optional[Dict]]:
        tasks = [self.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Excepción al descargar {url}: {result}")
                output[url] = None
            else:
                output[url] = result
        
        return output


async def download_page(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    client = AsyncHTTPClient(timeout=timeout)
    result = await client.fetch(url)
    
    if result:
        return result['content']
    return None


async def download_page_with_metadata(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[Dict]:
    client = AsyncHTTPClient(timeout=timeout)
    return await client.fetch(url)