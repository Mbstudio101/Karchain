#!/usr/bin/env python3
"""
Diagnostic script to check BettingPros API response structure
"""
import requests
import json
from datetime import datetime

def test_bettingpros_api():
    """Test the BettingPros API to see actual response structure"""
    
    headers = {
        "x-api-key": "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh",
        "referer": "https://www.bettingpros.com/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Get today's events
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    print("=== Testing BettingPros API ===")
    print(f"Date: {today_str}")
    
    # Get events
    events_url = "https://api.bettingpros.com/v3/events"
    events_params = {
        "sport": "NBA", 
        "date": today_str,
        "lineups": "true"
    }
    
    try:
        events_response = requests.get(events_url, headers=headers, params=events_params, timeout=15)
        events_data = events_response.json()
        
        print(f"Events found: {len(events_data.get('events', []))}")
        
        if events_data.get('events'):
            # Take first event
            event = events_data['events'][0]
            event_id = event['id']
            home_team = event.get('home', 'Unknown')
            away_team = event.get('away', 'Unknown')
            
            print(f"\n=== Event Details ===")
            print(f"Event ID: {event_id}")
            print(f"Home: {home_team}")
            print(f"Away: {away_team}")
            
            # Test moneyline market
            print(f"\n=== Testing Moneyline Market ===")
            ml_url = "https://api.bettingpros.com/v3/offers"
            ml_params = {
                "sport": "NBA",
                "market_id": 127,  # moneyline
                "event_id": event_id,
                "live": "false"
            }
            
            ml_response = requests.get(ml_url, headers=headers, params=ml_params, timeout=15)
            ml_data = ml_response.json()
            
            print(f"Moneyline offers: {len(ml_data.get('offers', []))}")
            
            if ml_data.get('offers'):
                offer = ml_data['offers'][0]
                print(f"First offer structure:")
                print(json.dumps(offer, indent=2))
                
                # Check selections
                selections = offer.get('selections', [])
                for i, sel in enumerate(selections):
                    print(f"\nSelection {i+1}:")
                    print(f"  Label: '{sel.get('label', 'N/A')}'")
                    print(f"  Books: {len(sel.get('books', []))}")
                    if sel.get('books'):
                        book = sel['books'][0]
                        print(f"  First book ID: {book.get('id')}")
                        if book.get('lines'):
                            line = book['lines'][0]
                            print(f"  Line: {line.get('line')}")
                            print(f"  Cost: {line.get('cost')}")
            
            # Test spread market
            print(f"\n=== Testing Spread Market ===")
            spread_params = {
                "sport": "NBA",
                "market_id": 129,  # spread
                "event_id": event_id,
                "live": "false"
            }
            
            spread_response = requests.get(ml_url, headers=headers, params=spread_params, timeout=15)
            spread_data = spread_response.json()
            
            print(f"Spread offers: {len(spread_data.get('offers', []))}")
            
            if spread_data.get('offers'):
                offer = spread_data['offers'][0]
                selections = offer.get('selections', [])
                for i, sel in enumerate(selections):
                    print(f"Selection {i+1}: Label='{sel.get('label', 'N/A')}'")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bettingpros_api()