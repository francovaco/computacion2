import asyncio
import aiohttp
import argparse
import json
import time
from typing import Optional


class ScrapingClient:
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    async def scrape_url(self, url: str) -> Optional[dict]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/scrape",
                    params={"url": url}
                ) as response:
                    return await response.json()
            except Exception as e:
                print(f"Error al solicitar scraping: {e}")
                return None
    
    async def get_status(self, task_id: str) -> Optional[dict]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/status/{task_id}"
                ) as response:
                    return await response.json()
            except Exception as e:
                print(f"Error al obtener estado: {e}")
                return None
    
    async def get_result(self, task_id: str) -> Optional[dict]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/result/{task_id}"
                ) as response:
                    return await response.json()
            except Exception as e:
                print(f"Error al obtener resultado: {e}")
                return None
    
    async def wait_for_completion(self, task_id: str, max_wait: int = 60, poll_interval: float = 2.0) -> Optional[dict]:
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = await self.get_status(task_id)
            
            if not status:
                return None
            
            current_status = status.get('status')
            print(f"Estado actual: {current_status}")
            
            if current_status == 'completed':
                return await self.get_result(task_id)
            elif current_status == 'failed':
                result = await self.get_result(task_id)
                print(f"Tarea falló: {result.get('error', 'Unknown error')}")
                return result
            
            await asyncio.sleep(poll_interval)
        
        print(f"Timeout esperando la tarea {task_id}")
        return None
    
    async def scrape_and_wait(self, url: str, max_wait: int = 60) -> Optional[dict]:
        print(f"\n{'='*60}")
        print(f"Scraping URL: {url}")
        print(f"{'='*60}\n")
        
        # Solicitar scraping
        response = await self.scrape_url(url)
        
        if not response:
            print("Error al iniciar scraping")
            return None
        
        task_id = response.get('task_id')
        print(f"Task ID: {task_id}")
        print(f"Estado inicial: {response.get('status')}\n")
        
        # Esperar resultado
        print("Esperando resultado...\n")
        result = await self.wait_for_completion(task_id, max_wait)
        
        return result


async def test_scraping(server_url: str, test_url: str):
    client = ScrapingClient(server_url)
    
    # Scrape y esperar resultado
    result = await client.scrape_and_wait(test_url)
    
    if result:
        print(f"\n{'='*60}")
        print("RESULTADO")
        print(f"{'='*60}\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Mostrar resumen
        if result.get('scraping_data'):
            scraping = result['scraping_data']
            print(f"\n{'='*60}")
            print("RESUMEN")
            print(f"{'='*60}")
            print(f"Título: {scraping.get('title', 'N/A')}")
            print(f"Enlaces encontrados: {len(scraping.get('links', []))}")
            print(f"Imágenes: {scraping.get('images_count', 0)}")
            print(f"Estructura: {scraping.get('structure', {})}")
            
            if result.get('processing_data'):
                proc = result['processing_data']
                if proc.get('performance'):
                    perf = proc['performance']
                    print(f"\nRendimiento:")
                    print(f"  - Tiempo de carga: {perf.get('load_time_ms', 'N/A')} ms")
                    print(f"  - Tamaño total: {perf.get('total_size_kb', 'N/A')} KB")
                    print(f"  - Requests: {perf.get('num_requests', 'N/A')}")
                
                print(f"  - Screenshot: {'✓' if proc.get('screenshot') else '✗'}")
                print(f"  - Thumbnails: {len(proc.get('thumbnails', []))}")
    else:
        print("\nNo se pudo obtener resultado")


async def test_multiple_urls(server_url: str, urls: list):
    client = ScrapingClient(server_url)
    
    print(f"\n{'='*60}")
    print(f"PRUEBA CON MÚLTIPLES URLs ({len(urls)} URLs)")
    print(f"{'='*60}\n")
    
    # Enviar todas las solicitudes
    tasks = []
    for url in urls:
        response = await client.scrape_url(url)
        if response:
            task_id = response.get('task_id')
            print(f"✓ Enviado: {url} (task_id: {task_id})")
            tasks.append(task_id)
        else:
            print(f"✗ Error: {url}")
    
    print(f"\nEsperando {len(tasks)} tareas...\n")
    
    # Esperar todas las tareas
    for i, task_id in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] Esperando tarea {task_id}...")
        result = await client.wait_for_completion(task_id, max_wait=90)
        if result:
            print(f"  ✓ Completada")
        else:
            print(f"  ✗ Falló o timeout")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Cliente de prueba para el sistema de scraping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s http://localhost:8000 https://example.com
  %(prog)s http://localhost:8000 https://python.org --verbose
  %(prog)s http://localhost:8000 --multiple https://example.com https://python.org https://github.com
        """
    )
    
    parser.add_argument(
        'server_url',
        help='URL del servidor de scraping (ej: http://localhost:8000)'
    )
    
    parser.add_argument(
        'url',
        nargs='?',
        default='https://example.com',
        help='URL a scrapear (default: https://example.com)'
    )
    
    parser.add_argument(
        '--multiple', '-m',
        nargs='+',
        help='Múltiples URLs para probar concurrentemente'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verbose'
    )
    
    return parser.parse_args()


async def main_async():
    args = parse_arguments()
    
    if args.multiple:
        # Probar con múltiples URLs
        await test_multiple_urls(args.server_url, args.multiple)
    else:
        # Probar con una sola URL
        await test_scraping(args.server_url, args.url)


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())