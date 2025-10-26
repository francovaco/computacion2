import argparse
import logging
import multiprocessing as mp
from processor.processing_server import start_processing_server


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Servidor de Procesamiento Distribuido',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s -i 0.0.0.0 -p 9000
  %(prog)s -i localhost -p 9000 -n 4
  %(prog)s -i :: -p 9000 -n 8  # IPv6
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
        '-n', '--processes',
        type=int,
        default=None,
        help=f'Número de procesos en el pool (default: {mp.cpu_count()})'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Modo verbose (más logs)'
    )
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    # Configurar logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("SERVIDOR DE PROCESAMIENTO DISTRIBUIDO")
    logger.info("=" * 60)
    logger.info(f"Host: {args.ip}")
    logger.info(f"Puerto: {args.port}")
    logger.info(f"Procesos: {args.processes or mp.cpu_count()}")
    logger.info("=" * 60)
    
    try:
        # Iniciar servidor
        start_processing_server(
            host=args.ip,
            port=args.port,
            num_processes=args.processes
        )
    except KeyboardInterrupt:
        logger.info("\nServidor detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())