import playwright.async_api as pw
import logging
import base64
import time
import random
from urllib.parse import urlparse, urljoin
import validators
from typing import Dict, Any, List
import asyncio
from src.utils.url_validator import get_url_without_fragment, is_same_page_link
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class CloudflareDetectedException(Exception):
    """Exception raised when Cloudflare protection is detected"""
    pass

class WebCrawler:
    def __init__(self):
        self.browser = None
        self.base_url = ""
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]

    async def __aenter__(self):
        logger.info("Initializing WebCrawler")
        playwright = await pw.async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
                '--disable-features=IsolateOrigins',
                '--disable-features=BlockInsecurePrivateNetworkRequests'
            ]
        )
        logger.info("Browser launched successfully")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()

    async def _setup_page(self) -> pw.Page:
        """Configure page with anti-detection measures"""
        page = await self.browser.new_page()
        
        # Set random user agent
        user_agent = random.choice(self.user_agents)
        await page.set_extra_http_headers({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Emulate human-like viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Override automation flags
        await page.evaluate("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return page

    async def _handle_cloudflare(self, page: pw.Page, url: str) -> bool:
        """Handle Cloudflare and similar protection pages"""
        try:
            # Check for common protection page indicators
            protection_selectors = [
                "iframe[src*='challenges.cloudflare.com']",
                "#challenge-running",
                "#challenge-form",
                "input[name='cf_captcha']"
            ]
            
            for selector in protection_selectors:
                if await page.query_selector(selector):
                    logger.warning(f"Protection page detected at {url}")
                    
                    # Wait a bit and try human-like interactions
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Simulate random mouse movements
                    for _ in range(3):
                        x = random.randint(100, 700)
                        y = random.randint(100, 500)
                        await page.mouse.move(x, y)
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                    # Wait for protection check to complete
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error handling protection page: {str(e)}")
            return False
            
    async def capture_screenshot(self, page: pw.Page, url: str) -> tuple[str, str]:
        """Capture full-page screenshot including scrolled content"""
        logger.info(f"Capturing full-page screenshot of {url}")
        try:
            # Set a large viewport to handle most content
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = "reports/screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate filename from URL and timestamp
            domain = urlparse(url).netloc.replace('www.', '')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{domain}_{timestamp}.jpg"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Try networkidle first, fall back to domcontentloaded
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
            except Exception as e:
                logger.warning(f"NetworkIdle timeout, falling back to domcontentloaded: {str(e)}")
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    # Give a short grace period for additional content
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Failed to load page even with fallback: {str(e)}")
                    raise
            
            # Get full page dimensions
            dimensions = await page.evaluate("""() => {
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
            await page.set_viewport_size({
                "width": dimensions["width"],
                "height": dimensions["height"]
            })
            
            # Try to load lazy content with timeout
            try:
                await asyncio.wait_for(
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
                    }"""),
                    timeout=10.0  # 10 seconds timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout during lazy loading scroll, continuing with capture")
            
            # Take the screenshot of whatever content we have
            screenshot = await page.screenshot(
                full_page=True,
                type='jpeg',
                quality=80,
                path=filepath
            )
            
            await page.close()
            logger.info(f"Full-page screenshot saved to {filepath}")
            
            return base64.b64encode(screenshot).decode(), filepath
            
        except Exception as e:
            logger.error(f"Error capturing full-page screenshot: {str(e)}")
            raise
        finally:
            try:
                await page.close()
            except:
                pass
            
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
    
    async def _detect_cloudflare(self, page: pw.Page) -> bool:
        """Detect if page is showing Cloudflare security check"""
        try:
            # Common Cloudflare challenge indicators
            cloudflare_indicators = [
                "//h1[contains(text(), 'Verify you are human')]",
                "//iframe[contains(@src, 'challenges.cloudflare.com')]",
                "//*[contains(text(), 'needs to review the security of your connection')]",
                "//input[@name='cf_captcha']",
                "//*[@id='challenge-running']",
                "//*[@class='cf-browser-verification']"
            ]
            
            for indicator in cloudflare_indicators:
                if await page.locator(indicator).count() > 0:
                    return True
                    
            # Check page title and content
            title = await page.title()
            if any(phrase in title.lower() for phrase in ['security check', 'cloudflare', 'ddos protection']):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking for Cloudflare: {str(e)}")
            return False

    async def extract_content(self, url: str) -> Dict[str, Any]:
        logger.info(f"Extracting content from {url}")
        start_time = time.time()
        
        try:
            validated_url = self.validate_url(url)
            page = await self._setup_page()
            
            try:
                await page.goto(validated_url, wait_until='networkidle', timeout=30000)
            except Exception as e:
                logger.warning(f"NetworkIdle timeout, falling back to domcontentloaded: {str(e)}")
                await page.goto(validated_url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(2)  # Grace period
            
            # Check for Cloudflare
            if await self._detect_cloudflare(page):
                error_msg = (
                    f"Cloudflare security check detected at {validated_url}. "
                    "Unable to proceed with automated analysis. "
                    "This website requires human verification."
                )
                logger.error(error_msg)
                raise CloudflareDetectedException(error_msg)
            
            # Handle any protection pages
            if await self._handle_cloudflare(page, validated_url):
                # Re-extract content after passing protection
                await page.reload()
                await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Extract text content
            visible_text = await page.evaluate("""
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
            raw_links = await page.query_selector_all('a')
            valid_links = []
            section_links = {}  # Track same-page sections
            for link in raw_links:
                href = await link.get_attribute('href')
                if not href:
                    continue
                    
                try:
                    if href.startswith('#'):
                        # Handle pure anchor links
                        section_id = href[1:]
                        section_element = await page.query_selector(f'#{section_id}')
                        if section_element:
                            section_links[href] = await section_element.text_content()
                        continue
                        
                    full_url = href if href.startswith(('http://', 'https://')) else urljoin(validated_url, href)
                    
                    if is_same_page_link(full_url, validated_url):
                        # Handle full URLs with fragments
                        fragment = urlparse(full_url).fragment
                        if fragment:
                            section_element = await page.query_selector(f'#{fragment}')
                            if section_element:
                                section_links[f'#{fragment}'] = await section_element.text_content()
                        continue
                        
                    if validators.url(full_url):
                        valid_links.append(full_url)
                    
                except Exception as e:
                    logger.warning(f"Skipping invalid link {href}: {str(e)}")
            
            screenshot_b64, screenshot_path = await self.capture_screenshot(page, validated_url)
            
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
            
        except CloudflareDetectedException:
            raise  # Re-raise to be handled by calling code
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            raise
        finally:
            if 'page' in locals():
                await page.close() 