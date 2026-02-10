"""
Diagnostic script to capture authentication tokens and discover protected API endpoints.
This script intercepts network requests to find auth headers used by the sites.
"""
import asyncio
from playwright.async_api import async_playwright
import json

class APIInterceptor:
    def __init__(self):
        self.captured_requests = []
        self.auth_tokens = {}
        
    async def capture_bettingpros_auth(self):
        """Navigate BettingPros logged-in pages to capture auth tokens."""
        print("=== BettingPros Auth Token Discovery ===")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visible for login
            context = await browser.new_context()
            page = await context.new_page()
            
            # Intercept all API requests
            async def handle_request(request):
                if 'api.bettingpros.com' in request.url:
                    headers = request.headers
                    self.captured_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': dict(headers)
                    })
                    # Look for auth tokens
                    for key, value in headers.items():
                        if any(auth in key.lower() for auth in ['auth', 'token', 'bearer', 'cookie', 'session']):
                            self.auth_tokens[key] = value
                            print(f"Found auth header: {key} = {value[:50]}...")
            
            page.on('request', handle_request)
            
            # Navigate to pages that require auth
            print("Navigating to BettingPros...")
            await page.goto('https://www.bettingpros.com/nba/props/')
            await asyncio.sleep(3)
            
            # Try to access projection pages
            await page.goto('https://www.bettingpros.com/nba/projections/')
            await asyncio.sleep(3)
            
            # Defense vs Position
            await page.goto('https://www.bettingpros.com/nba/defense-vs-position/')
            await asyncio.sleep(3)
            
            await browser.close()
        
        print(f"\nCaptured {len(self.captured_requests)} API requests")
        print(f"Auth tokens found: {list(self.auth_tokens.keys())}")
        return self.captured_requests
    
    async def discover_fanduel_api(self):
        """Discover FanDuel API endpoints by intercepting network requests."""
        print("\n=== FanDuel API Discovery ===")
        fanduel_apis = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            async def handle_request(request):
                url = request.url
                # Look for API endpoints
                if any(api in url for api in ['api.', '/api/', 'sportsbook-api', 'sbapi', 'content-api']):
                    if 'fanduel' in url or 'sportsbook' in url:
                        fanduel_apis.append({
                            'url': url,
                            'method': request.method,
                            'headers': dict(request.headers)
                        })
                        print(f"Found FanDuel API: {url[:100]}")
            
            page.on('request', handle_request)
            
            try:
                await page.goto('https://sportsbook.fanduel.com/navigation/nba', timeout=30000)
                await asyncio.sleep(5)
                
                # Click on a game to trigger more API calls
                game_links = await page.query_selector_all('a[href*="/basketball/nba"]')
                if game_links:
                    await game_links[0].click()
                    await asyncio.sleep(3)
            except Exception as e:
                print(f"Navigation error: {e}")
            
            await browser.close()
        
        print(f"\nDiscovered {len(fanduel_apis)} FanDuel API endpoints")
        
        # Save discovered APIs
        with open('/Users/marvens/Desktop/Karchain/backend/scrapers/fanduel_api_discovery.json', 'w') as f:
            json.dump(fanduel_apis, f, indent=2)
        
        return fanduel_apis

async def main():
    interceptor = APIInterceptor()
    
    # Discover FanDuel APIs first (doesn't require login)
    fd_apis = await interceptor.discover_fanduel_api()
    
    # Capture BettingPros auth (may require manual login)
    bp_requests = await interceptor.capture_bettingpros_auth()
    
    # Save all findings
    findings = {
        'fanduel_apis': fd_apis,
        'bettingpros_requests': bp_requests,
        'auth_tokens': interceptor.auth_tokens
    }
    
    with open('/Users/marvens/Desktop/Karchain/backend/scrapers/api_discovery_results.json', 'w') as f:
        json.dump(findings, f, indent=2)
    
    print("\n=== Discovery Complete ===")
    print(f"Results saved to api_discovery_results.json")

if __name__ == "__main__":
    asyncio.run(main())
