import logging
import requests
from io import BytesIO
from typing import List, Optional
from PIL import Image
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import base64

logger = logging.getLogger(__name__)

# Constantes
THUMBNAIL_SIZE = (200, 200)
MAX_IMAGES_TO_PROCESS = 5
IMAGE_TIMEOUT = 10


def download_image(url: str, timeout: int = IMAGE_TIMEOUT) -> Optional[bytes]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=timeout, headers=headers, stream=True)
        response.raise_for_status()
        
        # Verificar que sea una imagen
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"URL no es una imagen: {url} (content-type: {content_type})")
            return None
        
        return response.content
        
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout al descargar imagen: {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error al descargar imagen {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al descargar imagen: {e}")
        return None


def create_thumbnail(image_bytes: bytes, size: tuple = THUMBNAIL_SIZE) -> Optional[str]:
    try:
        # Abrir imagen
        image = Image.open(BytesIO(image_bytes))
        
        # Convertir a RGB si es necesario (para PNG con transparencia)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Crear thumbnail manteniendo aspect ratio
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convertir a base64
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=85, optimize=True)
        buffer.seek(0)
        thumbnail_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return thumbnail_base64
        
    except Exception as e:
        logger.error(f"Error al crear thumbnail: {e}")
        return None


def extract_image_urls(html_content: str, base_url: str, max_images: int = MAX_IMAGES_TO_PROCESS) -> List[str]:
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        image_urls = []
        
        # Buscar todas las imágenes
        for img in soup.find_all('img', limit=max_images * 2):  # Buscar más por si algunas fallan
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                # Resolver URL relativa
                absolute_url = urljoin(base_url, src)
                
                # Filtrar URLs inválidas o muy pequeñas
                parsed = urlparse(absolute_url)
                if parsed.scheme in ('http', 'https'):
                    image_urls.append(absolute_url)
            
            if len(image_urls) >= max_images:
                break
        
        logger.info(f"Extraídas {len(image_urls)} URLs de imágenes de {base_url}")
        return image_urls
        
    except Exception as e:
        logger.error(f"Error al extraer URLs de imágenes: {e}")
        return []


def process_images(url: str, html_content: str, max_images: int = MAX_IMAGES_TO_PROCESS) -> List[str]:
    thumbnails = []
    
    try:
        # Extraer URLs de imágenes
        image_urls = extract_image_urls(html_content, url, max_images)
        
        if not image_urls:
            logger.info(f"No se encontraron imágenes en: {url}")
            return thumbnails
        
        # Procesar cada imagen
        for img_url in image_urls[:max_images]:
            logger.debug(f"Procesando imagen: {img_url}")
            
            # Descargar imagen
            image_bytes = download_image(img_url)
            if not image_bytes:
                continue
            
            # Crear thumbnail
            thumbnail = create_thumbnail(image_bytes)
            if thumbnail:
                thumbnails.append(thumbnail)
            
            # Límite alcanzado
            if len(thumbnails) >= max_images:
                break
        
        logger.info(f"Procesadas {len(thumbnails)} imágenes exitosamente")
        return thumbnails
        
    except Exception as e:
        logger.error(f"Error al procesar imágenes: {e}")
        return thumbnails


def get_image_info(image_bytes: bytes) -> Optional[dict]:
    try:
        image = Image.open(BytesIO(image_bytes))
        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height
        }
    except Exception as e:
        logger.error(f"Error al obtener info de imagen: {e}")
        return None