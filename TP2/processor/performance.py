import logging
import time
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


def analyze_performance(url: str, timeout: int = 30) -> Optional[Dict]:
    driver = None
    try:
        logger.info(f"Analizando rendimiento para: {url}")
        
        # Configurar Chrome headless
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        # Medir tiempo de carga
        start_time = time.time()
        driver.get(url)
        load_time = (time.time() - start_time) * 1000  # Convertir a milisegundos
        
        # Obtener métricas de rendimiento usando Navigation Timing API
        navigation_timing = driver.execute_script("""
            var timing = window.performance.timing;
            return {
                'loadTime': timing.loadEventEnd - timing.navigationStart,
                'domContentLoaded': timing.domContentLoadedEventEnd - timing.navigationStart,
                'responseTime': timing.responseEnd - timing.requestStart,
                'domInteractive': timing.domInteractive - timing.navigationStart
            };
        """)
        
        # Obtener información de recursos
        resources = driver.execute_script("""
            var resources = window.performance.getEntriesByType('resource');
            var totalSize = 0;
            var resourceTypes = {};
            
            resources.forEach(function(resource) {
                if (resource.transferSize) {
                    totalSize += resource.transferSize;
                }
                var type = resource.initiatorType || 'other';
                resourceTypes[type] = (resourceTypes[type] || 0) + 1;
            });
            
            return {
                'numRequests': resources.length,
                'totalSize': totalSize,
                'resourceTypes': resourceTypes
            };
        """)
        
        # Contar elementos de la página
        try:
            num_images = len(driver.find_elements(By.TAG_NAME, "img"))
            num_scripts = len(driver.find_elements(By.TAG_NAME, "script"))
            num_stylesheets = len(driver.find_elements(By.TAG_NAME, "link"))
        except Exception:
            num_images = num_scripts = num_stylesheets = 0
        
        performance_data = {
            "load_time_ms": int(navigation_timing.get('loadTime', load_time)),
            "dom_content_loaded_ms": navigation_timing.get('domContentLoaded', 0),
            "response_time_ms": navigation_timing.get('responseTime', 0),
            "dom_interactive_ms": navigation_timing.get('domInteractive', 0),
            "total_size_kb": int(resources.get('totalSize', 0) / 1024),
            "num_requests": resources.get('numRequests', 0),
            "resource_types": resources.get('resourceTypes', {}),
            "num_images": num_images,
            "num_scripts": num_scripts,
            "num_stylesheets": num_stylesheets
        }
        
        logger.info(f"Análisis de rendimiento completado: {load_time:.2f}ms, {performance_data['num_requests']} requests")
        return performance_data
        
    except TimeoutException:
        logger.error(f"Timeout al analizar rendimiento: {url}")
        return {
            "load_time_ms": timeout * 1000,
            "error": "timeout",
            "num_requests": 0,
            "total_size_kb": 0
        }
    except WebDriverException as e:
        logger.error(f"Error de WebDriver al analizar rendimiento: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al analizar rendimiento: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error al cerrar driver: {e}")


def get_simple_performance(url: str, timeout: int = 30) -> Optional[Dict]:
    import requests
    from urllib.parse import urljoin, urlparse
    from bs4 import BeautifulSoup
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        load_time = (time.time() - start_time) * 1000
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Contar recursos
        images = soup.find_all('img')
        scripts = soup.find_all('script')
        stylesheets = soup.find_all('link', rel='stylesheet')
        
        return {
            "load_time_ms": int(load_time),
            "total_size_kb": int(len(response.content) / 1024),
            "num_requests": len(images) + len(scripts) + len(stylesheets) + 1,  # +1 por el HTML
            "num_images": len(images),
            "num_scripts": len(scripts),
            "num_stylesheets": len(stylesheets),
            "status_code": response.status_code
        }
        
    except Exception as e:
        logger.error(f"Error en análisis simple de rendimiento: {e}")
        return None