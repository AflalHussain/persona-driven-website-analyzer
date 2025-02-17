from urllib.parse import urlparse, urljoin, urlunsplit
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

def is_same_page_link(url1: str, url2: str) -> bool:
    """Check if two URLs point to the same page (ignoring hash/fragment)"""
    try:
        parsed1 = urlparse(url1)
        parsed2 = urlparse(url2)

        # Normalize paths by stripping trailing slashes
        path1 = parsed1.path.rstrip('/')
        path2 = parsed2.path.rstrip('/')
        
        # Compare everything except fragment
        return (parsed1.scheme == parsed2.scheme and
                parsed1.netloc == parsed2.netloc and
                path1== path2 and
                parsed1.params == parsed2.params and
                parsed1.query == parsed2.query)
    except Exception as e:
        logger.error(f"Error comparing URLs {url1} and {url2}: {str(e)}")
        return False

def get_url_without_fragment(url: str) -> str:
    """Remove fragment/hash from URL"""
    try:
        parsed = urlparse(url)
        return urlunsplit((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.query,
            ''  # Empty fragment
        ))
    except Exception as e:
        logger.error(f"Error cleaning URL {url}: {str(e)}")
        return url 