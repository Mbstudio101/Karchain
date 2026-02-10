import asyncio
import aiohttp
import json
from datetime import datetime

async def test_rockets_clippers():
    """Test the BettingPros API for Rockets vs Clippers game"""
    
    # API details from the scraper
    api_url = "https://api.bettingpros.com/v3"
    headers = {
        "x-api-key": "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh",
        "referer": "https://www.bettingpros.com/",
    }
    
    # Get today's games from the API
    today = datetime.now().strftime("%Y-%m-%d")
    
    async with aiohttp.ClientSession() as session:
        # Get NBA events for today
        events_url = f"{api_url}/events"
        params = {
            "sport": "nba",
            "date": today,
            "include": "scores"
        }
        
        try:
            async with session.get(events_url, headers=headers, params=params) as response:
                events_data = await response.json()
                
            print(f"🔍 Searching for Rockets vs Clippers game on {today}")
            print(f"📊 Total events found: {len(events_data.get('events', []))}")
            
            # Find the Rockets vs Clippers game
            target_game = None
            for event in events_data.get('events', []):
                home_team = event.get('home', {}).get('name', '') if isinstance(event.get('home'), dict) else ''
                away_team = event.get('away', {}).get('name', '') if isinstance(event.get('away'), dict) else ''
                
                if ('Rockets' in home_team and 'Clippers' in away_team) or ('Rockets' in away_team and 'Clippers' in home_team):
                    target_game = event
                    print(f"🎯 Found game: {home_team} vs {away_team}")
                    print(f"🆔 Event ID: {event.get('id')}")
                    break
            
            if not target_game:
                print("❌ Rockets vs Clippers game not found in today's events")
                return
                
            event_id = target_game['id']
            
            # Check market status
            markets_url = f"{api_url}/markets"
            params = {
                "eventId": event_id,
                "include": "selections"
            }
            
            async with session.get(markets_url, headers=headers, params=params) as response:
                markets_data = await response.json()
                
            print(f"\n📈 Market Status for Event {event_id}:")
            print(f"Total markets: {len(markets_data.get('markets', []))}")
            
            # Check specific markets
            for market in markets_data.get('markets', []):
                market_name = market.get('name', '').lower()
                market_id = market.get('id')
                
                if any(keyword in market_name for keyword in ['moneyline', 'spread', 'total']):
                    print(f"\n🎯 {market_name.upper()} Market (ID: {market_id}):")
                    print(f"Status: {market.get('status', 'unknown')}")
                    
                    # Check selections
                    selections = market.get('selections', [])
                    print(f"Selections: {len(selections)}")
                    
                    for sel in selections:
                        sel_label = sel.get('label', '')
                        books = sel.get('books', [])
                        print(f"  - {sel_label}: {len(books)} bookmakers")
                        
                        # Check FanDuel specifically
                        fd_book = next((b for b in books if isinstance(b, dict) and b.get("id") == 10), None)
                        if fd_book:
                            lines = fd_book.get('lines', [])
                            if lines:
                                line = lines[0]
                                print(f"    FanDuel: {line.get('line', 'N/A')} @ {line.get('cost', 'N/A')}")
                        else:
                            # Check consensus
                            consensus = next((b for b in books if isinstance(b, dict) and b.get("id") == 0), None)
                            if consensus and consensus.get('lines'):
                                line = consensus['lines'][0]
                                print(f"    Consensus: {line.get('line', 'N/A')} @ {line.get('cost', 'N/A')}")
                            else:
                                print(f"    ❌ No lines available")
                                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rockets_clippers())