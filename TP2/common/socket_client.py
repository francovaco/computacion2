import asyncio
import logging
from typing import Dict, Any, Optional
from .protocol import send_message_async, receive_message_async, MSG_TYPE_ERROR

logger = logging.getLogger(__name__)


class AsyncSocketClient:
    
    def __init__(self, host: str, port: int, max_retries: int = 3, timeout: float = 30.0):
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.timeout = timeout
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
    
    async def connect(self) -> bool:
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Intentando conectar a {self.host}:{self.port} (intento {attempt + 1}/{self.max_retries})")
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=self.timeout
                )
                logger.info(f"Conectado exitosamente a {self.host}:{self.port}")
                return True
            except asyncio.TimeoutError:
                logger.warning(f"Timeout al conectar (intento {attempt + 1}/{self.max_retries})")
            except ConnectionRefusedError:
                logger.warning(f"Conexión rechazada (intento {attempt + 1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"Error al conectar: {e}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(1)  # Esperar antes de reintentar
        
        logger.error(f"No se pudo conectar después de {self.max_retries} intentos")
        return False
    
    async def send_request(self, msg_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.writer or not self.reader:
            if not await self.connect():
                return None
        
        try:
            # Enviar solicitud
            logger.debug(f"Enviando solicitud de tipo: {msg_type}")
            await asyncio.wait_for(
                send_message_async(self.writer, msg_type, data),
                timeout=self.timeout
            )
            
            # Recibir respuesta
            logger.debug("Esperando respuesta del servidor de procesamiento")
            response = await asyncio.wait_for(
                receive_message_async(self.reader),
                timeout=self.timeout
            )
            
            if response.msg_type == MSG_TYPE_ERROR:
                logger.error(f"Error del servidor de procesamiento: {response.data}")
                return None
            
            logger.debug(f"Respuesta recibida exitosamente: {response.msg_type}")
            return response.data
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout al comunicarse con servidor de procesamiento")
            await self.close()
            return None
        except ConnectionError as e:
            logger.error(f"Error de conexión: {e}")
            await self.close()
            return None
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            await self.close()
            return None
    
    async def close(self):
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
                logger.info("Conexión cerrada")
            except Exception as e:
                logger.error(f"Error al cerrar conexión: {e}")
            finally:
                self.writer = None
                self.reader = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()