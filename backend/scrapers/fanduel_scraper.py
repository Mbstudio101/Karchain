import asyncio
from playwright.async_api import async_playwright
import logging
import os
import time
from datetime import datetime
from app.database import SessionLocal
from app.models import Team, Game, BettingOdds, Player, PlayerProps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FanDuelScraper:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def start(self):
        self.playwright = await async_playwright().start()
        
        # More diverse user agents
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]
        import random
        ua = random.choice(user_agents)
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
                "--ignore-certificate-errors",
                "--ignore-certificate-errors-spki-list",
                f"--user-agent={ua}"
            ]
        )
        
        # Load state if exists
        storage_state = "fanduel_state.json" if os.path.exists("fanduel_state.json") else None
        
        self.context = await self.browser.new_context(
            user_agent=ua,
            viewport={"width": 1440 + random.randint(0, 100), "height": 900 + random.randint(0, 100)},
            ignore_https_errors=True,
            storage_state=storage_state,
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "cross-site",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        # Add stealth scripts to the page
        await self.context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.page = await self.context.new_page()
        logger.info(f"Browser launched with UA: {ua}")

    async def handle_captcha(self, page):
        """Detect and solve 'Press & Hold' captcha across all frames with randomized interaction."""
        try:
            import random
            # Check main page and all frames
            for frame in page.frames:
                try:
                    # Look for the Press & Hold button
                    btn = frame.get_by_text("Press & Hold", exact=False).first
                    if await btn.is_visible(timeout=3000):
                        logger.info(f"Captcha 'Press & Hold' button found. Solving...")
                        box = await btn.bounding_box()
                        if box:
                            # Move to center with small random offset
                            offset_x = random.randint(-5, 5)
                            offset_y = random.randint(-5, 5)
                            
                            await btn.hover()
                            await page.mouse.move(box['x'] + box['width']/2 + offset_x, box['y'] + box['height']/2 + offset_y)
                            await page.mouse.down()
                            
                            # Randomized hold time between 8 and 11 seconds
                            hold_time = random.uniform(8.5, 11.0)
                            logger.info(f"Holding for {hold_time:.2f} seconds...")
                            await asyncio.sleep(hold_time)
                            
                            await page.mouse.up()
                            
                            # Wait for the captcha to disappear or navigation
                            try:
                                await page.wait_for_function("() => !document.body.innerText.includes('Press & Hold')", timeout=10000)
                                logger.info("Captcha disappeared.")
                            except:
                                logger.info("Timed out waiting for captcha to disappear, but continuing...")
                            
                            await asyncio.sleep(3)
                            return True
                except:
                    continue
            return False
        except Exception as e:
            logger.debug(f"Captcha handler error: {e}")
            return False

    async def scrape_nba_odds(self):
        """
        Navigates to NBA page and scrapes odds using ARIA labels.
        """
        url = "https://ma.sportsbook.fanduel.com/navigation/nba"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to {url} (Attempt {attempt + 1}/{max_retries})...")
                await self.page.goto(url, timeout=60000, wait_until="domcontentloaded")
                
                # Check for captcha
                await self.handle_captcha(self.page)
                
                # Wait for content
                try:
                    await self.page.wait_for_selector('a[href*="/basketball/nba/"]', timeout=30000)
                    logger.info("NBA page loaded successfully.")
                    break
                except:
                    logger.warning(f"Attempt {attempt + 1} failed to find game links.")
                    if attempt == max_retries - 1:
                        await self.page.screenshot(path="fanduel_final_fail.png")
                        return []
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Navigation error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1: return []
                await asyncio.sleep(5)

        # Save success state
        await self.context.storage_state(path="fanduel_state.json")

        # Find all game links - some might not have "More wagers" text but still lead to props
        # Usually direct game links contain /basketball/nba/team1-v-team2
        links = await self.page.locator('a[href*="/basketball/nba/"]').all()
        
        # Deduplicate and prioritize "More wagers" or direct links
        unique_games = {}
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if not href or "/players/" in href: continue
            
            # Normalize href
            full_url = f"https://sportsbook.fanduel.com{href}" if href.startswith("/") else href
            
            # If we see "More wagers", it's the gold standard link
            if "More wagers" in text or full_url not in unique_games:
                unique_games[full_url] = text

        logger.info(f"Identified {len(unique_games)} unique games to scrape.")
        
        odds_data = []
        for href, text in unique_games.items():
            try:
                # Extract team names from URL slug
                # Use a more robust split for different URL formats
                slug = href.split("/")[-1]
                # Split at the ID (usually start with digit)
                slug_clean = re.split(r'-\d+$', slug)[0]
                
                parts = []
                if "-@-" in slug_clean:
                    parts = slug_clean.split("-@-")
                elif "-at-" in slug_clean:
                    parts = slug_clean.split("-at-")
                elif "-v-" in slug_clean:
                    parts = slug_clean.split("-v-")
                
                if len(parts) != 2:
                    logger.warning(f"Could not parse teams from slug: {slug_clean}")
                    continue
                    
                away_slug = parts[0].replace("-", " ").title()
                home_slug = parts[1].replace("-", " ").title()
                
                # 1. Deep Dive for Player Props [NEW]
                # href is already the full URL if normalized correctly in the previous step
                await self.scrape_game_props(href, home_slug, away_slug)
                
            except Exception as e:
                logger.error(f"Error processing game {href}: {e}")
                continue

        return odds_data

    async def scrape_game_props(self, url: str, home_team: str, away_team: str):
        """Navigate to game detail and scrape player props."""
        page = await self.context.new_page()
        try:
            logger.info(f"Deep scraping: {url}")
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Check for captcha
            await self.handle_captcha(page)
            
            tabs = [
                ("points", "player-points", "Player Points"),
                ("threes", "player-threes", "Player Threes"),
                ("rebounds", "player-rebounds", "Player Rebounds"),
                ("assists", "player-assists", "Player Assists"),
                ("combos", "player-combos", "Player Combos"),
                ("defense", "player-defense", "Player Defense"),
                ("first_basket", "first-basket", "First Basket"),
                ("double_result", "double-result", "Double Result"),
                ("odd_even", "odd-even", "Odd/Even")
            ]
            
            for prop_type, tab_id, tab_name in tabs:
                # 1. Try to find the Horizontal Tab first
                selectors = [
                    f'[data-testid="{tab_id}"]',
                    f'[data-testid="tab-{tab_name}"]',
                    f'div[role="tab"]:has-text("{tab_name}")',
                    f'a:has-text("{tab_name}")'
                ]
                
                tab_found = False
                for sel in selectors:
                    try:
                        loc = page.locator(sel).first
                        if await loc.is_visible(timeout=2000):
                            await loc.scroll_into_view_if_needed()
                            await loc.click()
                            tab_found = True
                            break
                    except:
                        continue

                # 2. If no tab, it might be a vertical Accordion (ArrowAction)
                # User provided snippet: div[aria-label="First Basket"][data-testid="ArrowAction"]
                if not tab_found:
                    accordion_selector = f'div[data-testid="ArrowAction"][aria-label*="{tab_name}"]'
                    try:
                        accordion = page.locator(accordion_selector).first
                        if await accordion.is_visible(timeout=2000):
                            expanded = await accordion.get_attribute("aria-expanded")
                            if expanded == "false":
                                await accordion.scroll_into_view_if_needed()
                                await accordion.click()
                                await asyncio.sleep(1)
                            tab_found = True
                    except Exception as e:
                        logger.debug(f"Accordion check failed for {tab_name}: {e}")

                if not tab_found:
                    logger.warning(f"Market {tab_name} not found as Tab or Accordion for {away_team} @ {home_team}")
                    continue

                try:
                    logger.info(f"Scraping {tab_name} market...")
                    await asyncio.sleep(2)
                    
                    # Scroll to load content
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)
                    
                    # Extract props
                    buttons = await page.locator('div[role="button"][aria-label]:not([aria-label*="Tab "])').all()
                    
                    extracted_count = 0
                    current_milestone = None
                    
                    for btn in buttons:
                        aria = await btn.get_attribute("aria-label")
                        if not aria or "ArrowAction" in aria: continue # Skip accordion buttons themselves
                        
                        # 1. Detect milestone headers
                        if "+" in aria and "," not in aria:
                            current_milestone = aria.strip()
                            continue

                        parsed = self._parse_player_prop(aria, prop_type, context_line=current_milestone)
                        if parsed:
                            self.save_player_prop(parsed, home_team, away_team)
                            extracted_count += 1
                    
                    logger.info(f"Extracted {extracted_count} props for {tab_name}")
                            
                except Exception as e:
                    logger.warning(f"Error extracting {tab_name}: {e}")
                    
        finally:
            await page.close()

    def _parse_player_prop(self, text, prop_type, context_line=None):
        """
        Parse variations:
        1. 'Lebron James Over 24.5 -110'
        2. 'To Score 20+ Points, Lebron James, -150'
        3. 'Points + Rebounds + Assists Over 35.5, Nikola Jokic, -115'
        4. Contextual: 'Brandon Miller, -4000' with context '1+ Made Threes'
        """
        import re
        text = text.replace("(", "").replace(")", "").strip()
        
        # 1. Comma Separated Format
        if "," in text:
            parts = [p.strip() for p in text.split(",")]
            
            # Contextual Handle: "Player Name, -110"
            if len(parts) == 2 and context_line:
                player_name = parts[0]
                price_match = re.search(r"([\+\-]?\d+)", parts[1])
                line_match = re.search(r"(\d+)\+", context_line)
                if price_match and line_match:
                    return {
                        "name": player_name,
                        "side": "over",
                        "line": float(line_match.group(1)) - 0.5,
                        "price": int(price_match.group(1)),
                        "type": prop_type
                    }

            if len(parts) >= 3:
                market = parts[0]
                player_name = parts[1]
                # Price is usually the 3rd part, e.g. "-110 Odds" or just "-110"
                price_match = re.search(r"([\+\-]?\d+)", parts[2])
                if not price_match: return None
                price = int(price_match.group(1))
                
                # Check for Milestone line: "To Score 20+ Points"
                ms_line = re.search(r"(\d+)\+", market)
                if ms_line:
                    return {
                        "name": player_name,
                        "side": "over",
                        "line": float(ms_line.group(1)) - 0.5,
                        "price": price,
                        "type": prop_type
                    }
                
                # Check for Over/Under in market string: "Points + Assists Over 12.5"
                ou_line = re.search(r"(Over|Under)\s+([\d\.]+)", market)
                if ou_line:
                    return {
                        "name": player_name,
                        "side": ou_line.group(1).lower(),
                        "line": float(ou_line.group(2)),
                        "price": price,
                        "type": prop_type
                    }

        # 2. Space Separated Format (Standard)
        # e.g., "Lebron James Over 24.5 -110"
        ou_match = re.search(r"^(.*?)\s+(Over|Under)\s+([\d\.]+)(?:\s+\w+)?\s+([\+\-]?\d+)$", text)
        if ou_match:
            return {
                "name": ou_match.group(1).strip(),
                "side": ou_match.group(2).lower(),
                "line": float(ou_match.group(3)),
                "price": int(ou_match.group(4)),
                "type": prop_type
            }
            
        # 3. Selection Based Odds (First Basket, Double Result, Odd/Even)
        # e.g., "Tobias Harris, +450", "Odd, -110", "Celtics/Celtics, +200"
        if "," in text:
            parts = [p.strip() for p in text.split(",")]
            if len(parts) == 2:
                name = parts[0]
                price_match = re.search(r"([\+\-]?\d+)", parts[1])
                if price_match:
                    return {
                        "name": name,
                        "side": "selection",
                        "line": 0.0,
                        "price": int(price_match.group(1)),
                        "type": prop_type
                    }

        return None

    def save_player_prop(self, data, home_team_name, away_team_name):
        db = SessionLocal()
        try:
            # 1. Find Game
            today = datetime.utcnow().date()
            game = db.query(Game).join(Team, Game.home_team_id == Team.id).filter(
                Team.name.ilike(f"%{home_team_name}%"),
                Game.game_date >= today
            ).first()
            if not game: return

            # 2. Find Player (or create)
            player = db.query(Player).filter(Player.name.ilike(f"%{data['name']}%")).first()
            if not player:
                # We don't have team_id easily here without more mapping, but we can assign later
                player = Player(name=data['name'], sport="NBA", active_status=True)
                db.add(player)
                db.commit()
                db.refresh(player)

            # 3. Save/Update Prop
            prop = db.query(PlayerProps).filter(
                PlayerProps.player_id == player.id,
                PlayerProps.game_id == game.id,
                PlayerProps.prop_type == data['type'],
                PlayerProps.line == data['line']
            ).first()

            if not prop:
                prop = PlayerProps(
                    player_id=player.id,
                    game_id=game.id,
                    prop_type=data['type'],
                    line=data['line'],
                    over_odds=0,
                    under_odds=0
                )
                db.add(prop)

            if data['side'] == 'over':
                prop.over_odds = data['price']
            else:
                prop.under_odds = data['price']
            
            prop.timestamp = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            logger.error(f"Error saving player prop: {e}")
            db.rollback()
        finally:
            db.close()

    def save_odds(self, data, status="Scheduled"):
        session = SessionLocal()
        try:
            # 1. Get or Create Teams
            home_team = session.query(Team).filter(Team.name.ilike(f"%{data['home_team']}%")).first()
            if not home_team:
                home_team = Team(name=data['home_team'], sport="NBA")
                session.add(home_team)
                session.commit()
                session.refresh(home_team)
            
            away_team = session.query(Team).filter(Team.name.ilike(f"%{data['away_team']}%")).first()
            if not away_team:
                away_team = Team(name=data['away_team'], sport="NBA")
                session.add(away_team)
                session.commit()
                session.refresh(away_team)
            
            # 2. Find or Create Game
            today = datetime.utcnow().date()
            game = session.query(Game).filter(
                Game.home_team_id == home_team.id,
                Game.away_team_id == away_team.id,
                Game.game_date >= today 
            ).first()
            
            if not game:
                game = Game(
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    game_date=datetime.utcnow(), 
                    sport="NBA",
                    status=status
                )
                session.add(game)
                session.commit()
                session.refresh(game)
            else:
                # Let ESPN handle status. We only create as Scheduled if new.
                pass
                
            # 3. Save Odds
            def clean_price(p):
                if not p: return None
                try:
                    return int(p.replace("+", ""))
                except:
                    return None
            
            def clean_spread(s):
                if not s: return None
                try:
                    return float(s)
                except:
                    return None

            odds_entry = BettingOdds(
                game_id=game.id,
                bookmaker="FanDuel",
                home_moneyline=clean_price(data['home_moneyline']),
                away_moneyline=clean_price(data['away_moneyline']),
                spread_points=clean_spread(data['home_spread']),
                home_spread_price=clean_price(data['home_spread_price']),
                away_spread_price=clean_price(data['away_spread_price']),
                total_points=clean_spread(data['total_over']),
                over_price=clean_price(data['over_price']),
                under_price=clean_price(data['under_price']),
                timestamp=datetime.utcnow()
            )
            
            session.add(odds_entry)
            session.commit()
            logger.info(f"Saved odds for game {game.id}")

        except Exception as e:
            logger.error(f"Error saving odds to DB: {e}")
            session.rollback()
        finally:
            session.close()

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def main():
    scraper = FanDuelScraper(headless=True)
    try:
        await scraper.start()
        await scraper.scrape_nba_odds()
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
