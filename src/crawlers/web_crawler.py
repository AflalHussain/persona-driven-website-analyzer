import playwright.sync_api as pw
import logging
import base64
import time
from urllib.parse import urlparse, urljoin
import validators
from typing import Dict, Any, List
from src.utils.url_validator import get_url_without_fragment, is_same_page_link
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self):
        logger.info("Initializing WebCrawler")
        self.browser = pw.sync_playwright().start().chromium.launch(headless=True)
        self.base_url = ""
        logger.info("Browser launched successfully")
    
    def capture_screenshot(self, url: str) -> tuple[str, str]:
        """Capture full-page screenshot including scrolled content"""
        logger.info(f"Capturing full-page screenshot of {url}")
        try:
            page = self.browser.new_page()
            
            # Set a large viewport to handle most content
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = "reports/screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate filename from URL and timestamp
            domain = urlparse(url).netloc.replace('www.', '')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{domain}_{timestamp}.jpg"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Navigate to URL and wait for content to load
            page.goto(url, wait_until='networkidle')
            
            # Get full page dimensions
            dimensions = page.evaluate("""() => {
                return {
                    width: Math.max(
                        document.documentElement.scrollWidth,
                        document.body.scrollWidth,
                        document.documentElement.clientWidth
                    ),
                    height: Math.max(
                        document.documentElement.scrollHeight,
                        document.body.scrollHeight,
                        document.documentElement.clientHeight
                    )
                }
            }""")
            
            # Update viewport and scroll to capture everything
            page.set_viewport_size({
                "width": dimensions["width"],
                "height": dimensions["height"]
            })
            
            # Ensure all lazy-loaded content is loaded
            page.evaluate("""() => {
                const scrollStep = 100;
                const delay = 100;
                
                return new Promise((resolve) => {
                    let lastOffset = window.pageYOffset;
                    
                    function scrollDown() {
                        window.scrollBy(0, scrollStep);
                        
                        if (window.pageYOffset !== lastOffset) {
                            lastOffset = window.pageYOffset;
                            setTimeout(scrollDown, delay);
                        } else {
                            window.scrollTo(0, 0);
                            resolve();
                        }
                    }
                    
                    scrollDown();
                });
            }""")
            
            # Take the screenshot
            screenshot = page.screenshot(
                full_page=True,
                type='jpeg',
                quality=80,  # Reduce file size while maintaining quality
                path=filepath  # Save to file
            )
            
            page.close()
            logger.info(f"Full-page screenshot saved to {filepath}")
            
            # Return both base64 for Claude and filepath for reference
            return base64.b64encode(screenshot).decode(), filepath
            
        except Exception as e:
            logger.error(f"Error capturing full-page screenshot: {str(e)}")
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
        max_retries = 3
        current_try = 0
        
        while current_try < max_retries:
            try:
                validated_url = self.validate_url(url)
                base_url = get_url_without_fragment(validated_url)
                logger.info(f"Validated URL: {validated_url}")
                
                page = self.browser.new_page()
                
                # Set shorter timeout and different wait strategy
                page.set_default_navigation_timeout(45000)  # 45 seconds
                
                # Try different load states if networkidle fails
                try:
                    page.goto(validated_url, wait_until='domcontentloaded', timeout=30000)
                    # Wait a bit more for content to load
                    page.wait_for_load_state('networkidle', timeout=15000)
                except Exception as e:
                    logger.warning(f"NetworkIdle timeout, falling back to domcontentloaded: {str(e)}")
                    # Continue with available content
                
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
                
                # Extract and validate links, handling same-page links
                raw_links = page.query_selector_all('a')
                valid_links = []
                section_links = {}  # Track same-page sections
                for link in raw_links:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                        
                    try:
                        if href.startswith('#'):
                            # Handle pure anchor links
                            section_id = href[1:]
                            section_element = page.query_selector(f'#{section_id}')
                            if section_element:
                                section_links[href] = section_element.text_content()
                            continue
                            
                        full_url = href if href.startswith(('http://', 'https://')) else urljoin(base_url, href)
                        
                        if is_same_page_link(full_url, base_url):
                            # Handle full URLs with fragments
                            fragment = urlparse(full_url).fragment
                            if fragment:
                                section_element = page.query_selector(f'#{fragment}')
                                if section_element:
                                    section_links[f'#{fragment}'] = section_element.text_content()
                            continue
                            
                        if validators.url(full_url):
                            valid_links.append(full_url)
                            
                    except Exception as e:
                        logger.warning(f"Skipping invalid link {href}: {str(e)}")
                
                screenshot_b64, screenshot_path = self.capture_screenshot(validated_url)
                page.close()
                
                execution_time = time.time() - start_time
                logger.info(f"Content extraction completed in {execution_time:.2f} seconds")
                
                return {
                    'url': validated_url,
                    'text_content': visible_text,
                    'links': valid_links,
                    'screenshot': screenshot_b64,
                    'screenshot_path': screenshot_path,  # Add screenshot path
                    'section_links': section_links  # Add section content
                }
                
            except Exception as e:
                current_try += 1
                logger.warning(f"Attempt {current_try} failed: {str(e)}")
                if current_try >= max_retries:
                    logger.error(f"Error extracting content after {max_retries} attempts: {str(e)}")
                    raise
                time.sleep(2 ** current_try)  # Exponential backoff
                
            finally:
                try:
                    page.close()
                except:
                    pass

    def __del__(self):
        try:
            self.browser.close()
        except:
            pass 