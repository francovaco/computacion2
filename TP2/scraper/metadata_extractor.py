import logging
from typing import Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_metadata(html_content: str) -> Dict:
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        metadata = {
            "basic": extract_basic_meta_tags(soup),
            "open_graph": extract_open_graph(soup),
            "twitter": extract_twitter_cards(soup),
            "other": extract_other_meta_tags(soup)
        }
        
        logger.info("Metadatos extraídos exitosamente")
        return metadata
        
    except Exception as e:
        logger.error(f"Error al extraer metadatos: {e}")
        return {}


def extract_basic_meta_tags(soup: BeautifulSoup) -> Dict[str, str]:
    basic_tags = {}
    
    try:
        # Meta tags comunes
        common_names = ['description', 'keywords', 'author', 'viewport', 
                       'robots', 'generator', 'theme-color']
        
        for name in common_names:
            tag = soup.find('meta', attrs={'name': name})
            if tag and tag.get('content'):
                basic_tags[name] = tag['content'].strip()
        
        # Charset
        charset_tag = soup.find('meta', attrs={'charset': True})
        if charset_tag:
            basic_tags['charset'] = charset_tag.get('charset', '')
        
        logger.debug(f"Extraídos {len(basic_tags)} meta tags básicos")
        return basic_tags
        
    except Exception as e:
        logger.error(f"Error al extraer meta tags básicos: {e}")
        return {}


def extract_open_graph(soup: BeautifulSoup) -> Dict[str, str]:
    og_tags = {}
    
    try:
        # Buscar todos los meta tags con property que empiece con 'og:'
        for tag in soup.find_all('meta', attrs={'property': True}):
            prop = tag.get('property', '')
            if prop.startswith('og:'):
                content = tag.get('content', '').strip()
                if content:
                    # Remover el prefijo 'og:' para simplificar
                    key = prop[3:]
                    og_tags[key] = content
        
        logger.debug(f"Extraídos {len(og_tags)} tags de Open Graph")
        return og_tags
        
    except Exception as e:
        logger.error(f"Error al extraer Open Graph: {e}")
        return {}


def extract_twitter_cards(soup: BeautifulSoup) -> Dict[str, str]:
    twitter_tags = {}
    
    try:
        # Buscar todos los meta tags con name que empiece con 'twitter:'
        for tag in soup.find_all('meta', attrs={'name': True}):
            name = tag.get('name', '')
            if name.startswith('twitter:'):
                content = tag.get('content', '').strip()
                if content:
                    # Remover el prefijo 'twitter:' para simplificar
                    key = name[8:]
                    twitter_tags[key] = content
        
        logger.debug(f"Extraídos {len(twitter_tags)} tags de Twitter Cards")
        return twitter_tags
        
    except Exception as e:
        logger.error(f"Error al extraer Twitter Cards: {e}")
        return {}


def extract_other_meta_tags(soup: BeautifulSoup) -> Dict[str, str]:
    other_tags = {}
    
    try:
        # Buscar meta tags con property o name
        for tag in soup.find_all('meta'):
            name = tag.get('name') or tag.get('property')
            content = tag.get('content', '').strip()
            
            if name and content:
                # Ignorar si ya fue procesado en otras categorías
                if not (name.startswith('og:') or name.startswith('twitter:') or 
                       name in ['description', 'keywords', 'author', 'viewport', 'robots']):
                    other_tags[name] = content
        
        logger.debug(f"Extraídos {len(other_tags)} otros meta tags")
        return other_tags
        
    except Exception as e:
        logger.error(f"Error al extraer otros meta tags: {e}")
        return {}


def extract_canonical_url(soup: BeautifulSoup) -> str:
    try:
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            return canonical['href'].strip()
        return ""
    except Exception as e:
        logger.error(f"Error al extraer URL canónica: {e}")
        return ""


def extract_language(soup: BeautifulSoup) -> str:
    try:
        html_tag = soup.find('html')
        if html_tag:
            lang = html_tag.get('lang') or html_tag.get('xml:lang')
            if lang:
                return lang.strip()
        
        # Alternativa: buscar en meta tags
        lang_tag = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if lang_tag:
            return lang_tag.get('content', '').strip()
        
        return ""
    except Exception as e:
        logger.error(f"Error al extraer idioma: {e}")
        return ""


def get_all_metadata(html_content: str) -> Dict:
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        all_metadata = {
            "meta_tags": {
                "basic": extract_basic_meta_tags(soup),
                "open_graph": extract_open_graph(soup),
                "twitter": extract_twitter_cards(soup),
                "other": extract_other_meta_tags(soup)
            },
            "canonical_url": extract_canonical_url(soup),
            "language": extract_language(soup)
        }
        
        return all_metadata
        
    except Exception as e:
        logger.error(f"Error al obtener todos los metadatos: {e}")
        return {}