import requests
import json
from datetime import datetime

# API Base URL
BASE_URL = "http://127.0.0.1:8000"

def test_daily_reset():
    print("--- Testing Daily Reset Logic ---")
    
    # 1. Verify Games Filtering
    print("\n1. Games Filtering (Today/Feb 10):")
    r_games = requests.get(f"{BASE_URL}/games/")
    games_today = r_games.json()
    print(f"Default games count (local todayish): {len(games_today)}")
    
    r_games_future = requests.get(f"{BASE_URL}/games/", params={"date": "2026-02-12"})
    games_future = r_games_future.json()
    print(f"Games on Feb 12: {len(games_future)}")

    # 2. Verify Recommendations Filtering
    print("\n2. Recommendations Filtering:")
    r_recs = requests.get(f"{BASE_URL}/recommendations/")
    recs_today = r_recs.json()
    print(f"Default recommendations count: {len(recs_today)}")
    
    # 3. Verify Genius Picks Filtering
    print("\n3. Genius Picks Filtering:")
    r_genius = requests.get(f"{BASE_URL}/recommendations/genius-picks/")
    genius_today = r_genius.json().get("picks", [])
    print(f"Default genius picks count: {len(genius_today)}")
    
    r_genius_future = requests.get(f"{BASE_URL}/recommendations/genius-picks/", params={"date": "2026-02-12"})
    genius_future = r_genius_future.json().get("picks", [])
    print(f"Genius picks on Feb 12: {len(genius_future)}")

    # 4. Verify Recommendation Generation (Target Active Only)
    print("\n4. Triggering Generation (Optimized):")
    r_gen = requests.post(f"{BASE_URL}/recommendations/generate")
    new_recs = r_gen.json()
    print(f"Generated {len(new_recs)} recommendations for active/upcoming games.")

if __name__ == "__main__":
    try:
        test_daily_reset()
    except Exception as e:
        print(f"Error: {e}")
