from urllib.parse import urlparse, urljoin
import validators
import logging

logger = logging.getLogger(__name__)

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid"""
    try:
        return validators.url(url)
    except Exception as e:
        logger.error(f"Error validating URL {url}: {str(e)}")
        return False

def normalize_url(url: str, base_url: str = None) -> str:
    """Normalize a URL by adding protocol if missing and handling relative URLs"""
    try:
        if url.startswith('/') and base_url:
            url = urljoin(base_url, url)
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        return url
    except Exception as e:
        logger.error(f"Error normalizing URL {url}: {str(e)}")
        raise ValueError(f"Invalid URL: {url}")

def get_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception as e:
        logger.error(f"Error extracting domain from URL {url}: {str(e)}")
        return "" 