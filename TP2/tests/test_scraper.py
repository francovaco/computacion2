import pytest
import asyncio
from scraper.async_http import download_page, AsyncHTTPClient
from scraper.html_parser import parse_html, extract_title, extract_links
from scraper.metadata_extractor import extract_metadata


class TestAsyncHTTP:
    
    @pytest.mark.asyncio
    async def test_download_page(self):
        content = await download_page('https://example.com')
        assert content is not None
        assert len(content) > 0
        assert 'Example Domain' in content
    
    @pytest.mark.asyncio
    async def test_download_invalid_url(self):
        content = await download_page('https://this-domain-does-not-exist-12345.com', timeout=5)
        assert content is None
    
    @pytest.mark.asyncio
    async def test_download_multiple(self):
        client = AsyncHTTPClient(timeout=10)
        urls = [
            'https://example.com',
            'https://www.ietf.org',
        ]
        results = await client.fetch_multiple(urls)
        assert len(results) == len(urls)
        assert any(result is not None for result in results.values())


class TestHTMLParser:
    
    def test_parse_html_basic(self):
        html = '''
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Header 1</h1>
                <h2>Header 2</h2>
                <a href="http://example.com">Link</a>
                <img src="image.jpg" alt="Image">
            </body>
        </html>
        '''
        result = parse_html(html, 'http://test.com')
        
        assert result['title'] == 'Test Page'
        assert len(result['links']) == 1
        assert result['structure'].get('h1') == 1
        assert result['structure'].get('h2') == 1
        assert result['images_count'] == 1
    
    def test_extract_title(self):
        from bs4 import BeautifulSoup
        html = '<html><head><title>My Title</title></head></html>'
        soup = BeautifulSoup(html, 'lxml')
        title = extract_title(soup)
        assert title == 'My Title'
    
    def test_extract_links(self):
        from bs4 import BeautifulSoup
        html = '''
        <html>
            <body>
                <a href="http://example.com">Link 1</a>
                <a href="/relative">Link 2</a>
                <a href="#anchor">Link 3</a>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'lxml')
        links = extract_links(soup, 'http://test.com')
        
        assert 'http://example.com' in links
        assert 'http://test.com/relative' in links
        assert not any('#' in link for link in links)


class TestMetadataExtractor:
    
    def test_extract_metadata(self):
        html = '''
        <html>
            <head>
                <meta name="description" content="Test description">
                <meta name="keywords" content="test, keywords">
                <meta property="og:title" content="OG Title">
                <meta name="twitter:card" content="summary">
            </head>
        </html>
        '''
        metadata = extract_metadata(html)
        
        assert 'basic' in metadata
        assert 'open_graph' in metadata
        assert 'twitter' in metadata
        assert metadata['basic']['description'] == 'Test description'
        assert metadata['open_graph']['title'] == 'OG Title'
        assert metadata['twitter']['card'] == 'summary'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])