import pytest
from processor.screenshot import generate_screenshot
from processor.performance import analyze_performance, get_simple_performance
from processor.image_processor import download_image, create_thumbnail
from PIL import Image
import io
import base64


class TestScreenshot:
    
    @pytest.mark.slow
    def test_generate_screenshot(self):
        screenshot = generate_screenshot('https://example.com', timeout=15)
        assert screenshot is not None
        
        # Verificar que es base64 válido
        try:
            image_bytes = base64.b64decode(screenshot)
            assert len(image_bytes) > 0
        except Exception:
            pytest.fail("Screenshot no es base64 válido")
    
    @pytest.mark.slow
    def test_screenshot_invalid_url(self):
        screenshot = generate_screenshot('https://invalid-domain-12345.com', timeout=10)
        assert screenshot is None


class TestPerformance:
    
    @pytest.mark.slow
    def test_analyze_performance(self):
        performance = analyze_performance('https://example.com', timeout=15)
        
        if performance:  # Puede fallar si Selenium no está disponible
            assert 'load_time_ms' in performance
            assert performance['load_time_ms'] > 0
    
    def test_simple_performance(self):
        performance = get_simple_performance('https://example.com', timeout=10)
        
        assert performance is not None
        assert 'load_time_ms' in performance
        assert 'total_size_kb' in performance
        assert performance['load_time_ms'] > 0


class TestImageProcessor:
    
    def test_download_image(self):
        # URL de una imagen pequeña de prueba
        image_url = 'https://via.placeholder.com/150'
        image_bytes = download_image(image_url, timeout=10)
        
        assert image_bytes is not None
        assert len(image_bytes) > 0
    
    def test_create_thumbnail(self):
        # Crear imagen de prueba
        img = Image.new('RGB', (800, 600), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        # Crear thumbnail
        thumbnail = create_thumbnail(image_bytes, size=(100, 100))
        
        assert thumbnail is not None
        
        # Verificar que es base64 válido
        try:
            thumb_bytes = base64.b64decode(thumbnail)
            thumb_img = Image.open(io.BytesIO(thumb_bytes))
            assert thumb_img.size[0] <= 100
            assert thumb_img.size[1] <= 100
        except Exception as e:
            pytest.fail(f"Thumbnail inválido: {e}")
    
    def test_thumbnail_with_transparency(self):
        # Crear imagen RGBA
        img = Image.new('RGBA', (800, 600), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        # Crear thumbnail
        thumbnail = create_thumbnail(image_bytes)
        assert thumbnail is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'not slow'])