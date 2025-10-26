import argparse
import asyncio
import logging
from scraper.async_server import start_scraping_server


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Servidor de Scraping Web Asíncrono',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s -i 0.0.0.0 -p 8000 --processing-host localhost --processing-port 9000
  %(prog)s -i localhost -p 8080 -ph 127.0.0.1 -pp 9000 -w 8
  %(prog)s -i :: -p 8000 -ph :: -pp 9000  # IPv6
  
Endpoints disponibles:
  GET /scrape?url=<URL>       - Iniciar scraping (devuelve task_id)
  GET /status/<task_id>       - Consultar estado de tarea
  GET /result/<task_id>       - Obtener resultado de tarea
  GET /tasks                  - Listar estadísticas de tareas
        """
    )
    
    parser.add_argument(
        '-i', '--ip',
        required=True,
        help='Dirección de escucha (soporta IPv4/IPv6)'
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        required=True,
        help='Puerto de escucha'
    )
    
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=4,
        help='Número de workers asíncronos (default: 4)'
    )
    
    parser.add_argument(
        '--processing-host', '-ph',
        default='localhost',
        help='Host del servidor de procesamiento (default: localhost)'
    )
    
    parser.add_argument(
        '--processing-port', '-pp',
        type=int,
        default=9000,
        help='Puerto del servidor de procesamiento (default: 9000)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Modo verbose (más logs)'
    )
    
    return parser.parse_args()


async def main_async(args):
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("SERVIDOR DE SCRAPING WEB ASÍNCRONO")
    logger.info("=" * 60)
    logger.info(f"Host: {args.ip}")
    logger.info(f"Puerto: {args.port}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Servidor de procesamiento: {args.processing_host}:{args.processing_port}")
    logger.info("=" * 60)
    logger.info("Iniciando servidor...")
    
    try:
        await start_scraping_server(
            host=args.ip,
            port=args.port,
            processing_host=args.processing_host,
            processing_port=args.processing_port
        )
    except KeyboardInterrupt:
        logger.info("\nServidor detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        raise


def main():
    args = parse_arguments()
    
    # Configurar logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    try:
        # Ejecutar servidor asíncrono
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())