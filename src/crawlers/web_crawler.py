import playwright.sync_api as pw
import logging
import base64
import time
from urllib.parse import urlparse, urljoin
import validators
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self):
        logger.info("Initializing WebCrawler")
        self.browser = pw.sync_playwright().start().chromium.launch(headless=True)
        self.base_url = ""
        logger.info("Browser launched successfully")
    
    def capture_screenshot(self, url: str) -> str:
        logger.info(f"Capturing screenshot of {url}")
        try:
            page = self.browser.new_page()
            page.goto(url)
            screenshot = page.screenshot()
            page.close()
            logger.info("Screenshot captured successfully")
            return base64.b64encode(screenshot).decode()
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            raise
            
    def validate_url(self, url: str) -> str:
        """Validate and normalize URL"""
        logger.debug(f"Validating URL: {url}")
        
        try:
            if url.startswith('/'):
                url = urljoin(self.base_url, url)
                logger.info(f"Converted relative URL to absolute: {url}")
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                logger.info(f"Added https protocol to URL: {url}")
            
            if not validators.url(url):
                raise ValueError(f"Invalid URL format: {url}")
            
            return url
            
        except Exception as e:
            logger.error(f"URL validation error: {str(e)}")
            raise ValueError(f"Invalid URL: {url}")
    
    def extract_content(self, url: str) -> Dict[str, Any]:
        logger.info(f"Extracting content from {url}")
        start_time = time.time()
        
        try:
            validated_url = self.validate_url(url)
            logger.info(f"Validated URL: {validated_url}")
            
            page = self.browser.new_page()
            page.goto(validated_url, wait_until='networkidle')
            
            # Extract text content
            visible_text = page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('body *'))
                        .filter(element => {
                            const style = window.getComputedStyle(element);
                            return style.display !== 'none' && style.visibility !== 'hidden';
                        })
                        .map(element => element.textContent)
                        .join('\\n');
                }
            """)
            
            # Extract and validate links
            raw_links = [link.get_attribute('href') for link in page.query_selector_all('a')]
            valid_links = []
            for link in raw_links:
                if link:
                    try:
                        if link.startswith('/'):
                            full_link = urljoin(validated_url, link)
                        else:
                            full_link = link if link.startswith(('http://', 'https://')) else urljoin(validated_url, link)
                        
                        if validators.url(full_link):
                            valid_links.append(full_link)
                    except Exception as e:
                        logger.warning(f"Skipping invalid link {link}: {str(e)}")
            
            screenshot = self.capture_screenshot(validated_url)
            
            page.close()
            
            execution_time = time.time() - start_time
            logger.info(f"Content extraction completed in {execution_time:.2f} seconds")
            
            return {
                'url': validated_url,
                'text_content': visible_text,
                'links': valid_links,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            raise

    def __del__(self):
        try:
            self.browser.close()
        except:
            pass 