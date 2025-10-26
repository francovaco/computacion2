import base64
import logging
from io import BytesIO
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


def generate_screenshot(url: str, timeout: int = 30) -> Optional[str]:
    driver = None
    try:
        logger.info(f"Generando screenshot para: {url}")
        
        # Configurar opciones de Chrome en modo headless
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        
        # Inicializar el driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        # Cargar la página
        driver.get(url)
        
        # Tomar screenshot
        screenshot_bytes = driver.get_screenshot_as_png()
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        logger.info(f"Screenshot generado exitosamente para: {url}")
        return screenshot_base64
        
    except TimeoutException:
        logger.error(f"Timeout al cargar la página: {url}")
        return None
    except WebDriverException as e:
        logger.error(f"Error de WebDriver al generar screenshot: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al generar screenshot: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error al cerrar driver: {e}")


def generate_screenshot_with_dimensions(url: str, width: int = 1920, height: int = 1080, timeout: int = 30) -> Optional[str]:
    driver = None
    try:
        logger.info(f"Generando screenshot personalizado para: {url} ({width}x{height})")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--window-size={width},{height}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        driver.get(url)
        screenshot_bytes = driver.get_screenshot_as_png()
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        logger.info(f"Screenshot personalizado generado exitosamente")
        return screenshot_base64
        
    except Exception as e:
        logger.error(f"Error al generar screenshot personalizado: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error al cerrar driver: {e}")