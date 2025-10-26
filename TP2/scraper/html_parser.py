import logging
from typing import Dict, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


def parse_html(html_content: str, base_url: str = None) -> Dict:
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extraer título
        title = extract_title(soup)
        
        # Extraer enlaces
        links = extract_links(soup, base_url)
        
        # Extraer estructura de headers
        structure = extract_structure(soup)
        
        # Contar imágenes
        images_count = count_images(soup)
        
        result = {
            "title": title,
            "links": links,
            "structure": structure,
            "images_count": images_count
        }
        
        logger.info(f"HTML parseado: título='{title}', {len(links)} enlaces, {images_count} imágenes")
        return result
        
    except Exception as e:
        logger.error(f"Error al parsear HTML: {e}")
        return {
            "title": None,
            "links": [],
            "structure": {},
            "images_count": 0,
            "error": str(e)
        }


def extract_title(soup: BeautifulSoup) -> str:
    try:
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Alternativa: buscar en meta tags
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '').strip()
        
        return ""
    except Exception as e:
        logger.error(f"Error al extraer título: {e}")
        return ""


def extract_links(soup: BeautifulSoup, base_url: str = None) -> List[str]:
    links = []
    try:
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            
            # Ignorar enlaces vacíos, anclas y javascript
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Resolver URL relativa a absoluta
            if base_url:
                absolute_url = urljoin(base_url, href)
            else:
                absolute_url = href
            
            # Validar que sea una URL válida
            parsed = urlparse(absolute_url)
            if parsed.scheme in ('http', 'https'):
                links.append(absolute_url)
        
        # Eliminar duplicados manteniendo orden
        links = list(dict.fromkeys(links))
        
        logger.debug(f"Extraídos {len(links)} enlaces únicos")
        return links
        
    except Exception as e:
        logger.error(f"Error al extraer enlaces: {e}")
        return []


def extract_structure(soup: BeautifulSoup) -> Dict[str, int]:
    structure = {}
    
    try:
        for level in range(1, 7):
            tag_name = f'h{level}'
            count = len(soup.find_all(tag_name))
            if count > 0:
                structure[tag_name] = count
        
        logger.debug(f"Estructura extraída: {structure}")
        return structure
        
    except Exception as e:
        logger.error(f"Error al extraer estructura: {e}")
        return {}


def count_images(soup: BeautifulSoup) -> int:
    try:
        images = soup.find_all('img')
        count = len(images)
        logger.debug(f"Encontradas {count} imágenes")
        return count
    except Exception as e:
        logger.error(f"Error al contar imágenes: {e}")
        return 0


def extract_text_content(soup: BeautifulSoup, max_length: int = 1000) -> str:
    try:
        # Eliminar scripts y estilos
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Obtener texto
        text = soup.get_text(separator=' ', strip=True)
        
        # Limpiar espacios múltiples
        text = ' '.join(text.split())
        
        # Truncar si es necesario
        if len(text) > max_length:
            text = text[:max_length] + '...'
        
        return text
    except Exception as e:
        logger.error(f"Error al extraer texto: {e}")
        return ""


def get_all_images(soup: BeautifulSoup, base_url: str = None) -> List[Dict]:
    images = []
    
    try:
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
            
            # Resolver URL
            if base_url:
                src = urljoin(base_url, src)
            
            image_info = {
                'src': src,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width'),
                'height': img.get('height')
            }
            images.append(image_info)
        
        return images
    except Exception as e:
        logger.error(f"Error al obtener imágenes: {e}")
        return []