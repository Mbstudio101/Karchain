import asyncio
import aiohttp
import json
from datetime import datetime

async def check_today_games():
    """Check what games are available today from BettingPros"""
    
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
                
            print(f"📅 Today's NBA Games ({today}):")
            print(f"📊 Total events found: {len(events_data.get('events', []))}")
            
            # List all games
            for i, event in enumerate(events_data.get('events', [])):
                home_team = event.get('home', {}).get('name', '') if isinstance(event.get('home'), dict) else 'Unknown'
                away_team = event.get('away', {}).get('name', '') if isinstance(event.get('away'), dict) else 'Unknown'
                event_id = event.get('id', 'Unknown')
                
                print(f"\n{i+1}. {away_team} @ {home_team}")
                print(f"   Event ID: {event_id}")
                print(f"   Start Time: {event.get('start', 'Unknown')}")
                
                # Check if this is Rockets or Clippers
                if 'Rockets' in home_team or 'Rockets' in away_team:
                    print("   🔥 ROCKETS GAME 🔥")
                if 'Clippers' in home_team or 'Clippers' in away_team:
                    print("   ✂️ CLIPPERS GAME ✂️")
                            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_today_games())