import asyncio
import logging
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None

    async def start(self):
        """Initializes Playwright and opens a browser."""
        logger.info("Starting scraper...")
        self.playwright = await async_playwright().start()
        # Add arguments to make the browser less detectable as a bot
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--disable-http2",
            ]
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        # Add init script to mask webdriver property
        await self.context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.page = await self.context.new_page()
        logger.info("Scraper started.")

    async def stop(self):
        """Closes the browser and Playwright."""
        logger.info("Stopping scraper...")
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Scraper stopped.")

    async def navigate(self, url: str, wait_until: str = "domcontentloaded"):
        """Navigates to a URL with rate limiting and error handling."""
        try:
            # Rate limiting
            delay = random.uniform(2, 5)
            logger.info(f"Waiting {delay:.2f}s before navigating...")
            await asyncio.sleep(delay)

            logger.info(f"Navigating to {url}")
            await self.page.goto(url, wait_until=wait_until)
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise

    async def get_content(self):
        """Returns the page content."""
        return await self.page.content()

    async def screenshot(self, path: str):
        """Takes a screenshot."""
        await self.page.screenshot(path=path)
