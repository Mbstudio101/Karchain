import asyncio
import aiohttp
import json
from datetime import datetime

async def debug_api_response():
    """Debug the actual API response structure"""
    
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
                
            print(f"📅 Raw API Response for {today}:")
            print(f"Response type: {type(events_data)}")
            print(f"Response keys: {list(events_data.keys()) if isinstance(events_data, dict) else 'Not a dict'}")
            
            if isinstance(events_data, dict):
                print(f"\n📊 Total events: {len(events_data.get('events', []))}")
                
                # Show first event structure
                if events_data.get('events'):
                    first_event = events_data['events'][0]
                    print(f"\n🎯 First event structure:")
                    print(f"Event keys: {list(first_event.keys())}")
                    
                    # Check home/away structure
                    if 'home' in first_event:
                        home_data = first_event['home']
                        print(f"\n🏠 Home team data:")
                        print(f"Type: {type(home_data)}")
                        if isinstance(home_data, dict):
                            print(f"Keys: {list(home_data.keys())}")
                            print(f"Name: {home_data.get('name', 'No name')}")
                        else:
                            print(f"Data: {home_data}")
                    
                    if 'away' in first_event:
                        away_data = first_event['away']
                        print(f"\n✈️ Away team data:")
                        print(f"Type: {type(away_data)}")
                        if isinstance(away_data, dict):
                            print(f"Keys: {list(away_data.keys())}")
                            print(f"Name: {away_data.get('name', 'No name')}")
                        else:
                            print(f"Data: {away_data}")
                            
            else:
                print(f"Response data: {events_data}")
                            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_response())