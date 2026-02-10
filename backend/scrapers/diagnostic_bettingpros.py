import asyncio
import json
import re
from playwright.async_api import async_playwright

async def extract_data(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        # Monitor network requests
        async def handle_request(request):
            if "api.bettingpros.com" in request.url:
                print(f"API Request: {request.url}")
                print(f"Headers: {request.headers}")
        
        page.on("request", handle_request)
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        # Scroll to trigger more requests
        await page.mouse.wheel(0, 2000)
        await asyncio.sleep(2)
        
        await browser.close()

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.bettingpros.com/nba/odds/spread/"
    asyncio.run(extract_data(url))

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.bettingpros.com/nba/odds/spread/"
    asyncio.run(extract_data(url))
