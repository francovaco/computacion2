import pytest
import asyncio
import aiohttp


# Configuración
SCRAPING_SERVER = 'http://localhost:8000'
TEST_URL = 'https://example.com'


class TestIntegration:
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_scraping_workflow(self):
        async with aiohttp.ClientSession() as session:
            # 1. Iniciar scraping
            async with session.get(
                f'{SCRAPING_SERVER}/scrape',
                params={'url': TEST_URL}
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert 'task_id' in data
                task_id = data['task_id']
            
            # 2. Verificar estado
            await asyncio.sleep(1)
            async with session.get(
                f'{SCRAPING_SERVER}/status/{task_id}'
            ) as resp:
                assert resp.status == 200
                status = await resp.json()
                assert status['status'] in ['pending', 'scraping', 'processing', 'completed']
            
            # 3. Esperar completación
            max_attempts = 30
            for _ in range(max_attempts):
                async with session.get(
                    f'{SCRAPING_SERVER}/status/{task_id}'
                ) as resp:
                    status = await resp.json()
                    if status['status'] == 'completed':
                        break
                    await asyncio.sleep(2)
            
            # 4. Obtener resultado
            async with session.get(
                f'{SCRAPING_SERVER}/result/{task_id}'
            ) as resp:
                result = await resp.json()
                
                # Verificar estructura
                assert 'scraping_data' in result
                assert 'processing_data' in result
                assert result['status'] == 'success'
                
                # Verificar datos de scraping
                scraping = result['scraping_data']
                assert 'title' in scraping
                assert 'links' in scraping
                assert 'meta_tags' in scraping
                
                # Verificar datos de procesamiento
                processing = result['processing_data']
                assert 'screenshot' in processing
                assert 'performance' in processing
                assert 'thumbnails' in processing
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_url(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{SCRAPING_SERVER}/scrape',
                params={'url': 'not-a-valid-url'}
            ) as resp:
                assert resp.status == 400
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_missing_url_parameter(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{SCRAPING_SERVER}/scrape') as resp:
                assert resp.status == 400
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_nonexistent_task(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{SCRAPING_SERVER}/status/nonexistent-task-id'
            ) as resp:
                assert resp.status == 404
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_requests(self):
        urls = [
            'https://example.com',
            'https://www.ietf.org',
            'https://httpbin.org',
        ]
        
        async with aiohttp.ClientSession() as session:
            # Enviar múltiples requests
            tasks = []
            for url in urls:
                async with session.get(
                    f'{SCRAPING_SERVER}/scrape',
                    params={'url': url}
                ) as resp:
                    data = await resp.json()
                    tasks.append(data['task_id'])
            
            assert len(tasks) == len(urls)
            
            # Verificar que todas las tareas están en el sistema
            for task_id in tasks:
                async with session.get(
                    f'{SCRAPING_SERVER}/status/{task_id}'
                ) as resp:
                    assert resp.status == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])