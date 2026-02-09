import requests
import json
from datetime import datetime

base_url = "http://127.0.0.1:8000/games/"

# 1. Test Default (Today - 2026-02-08)
print("Testing Default (Today)...")
r_today = requests.get(base_url)
games_today = r_today.json()
print(f"Found {len(games_today)} games for today.")
for g in games_today:
    print(f"  Game ID: {g['id']} | Date: {g['game_date']} | Status: {g['status']}")

# 2. Test Feb 10 (contains Feb 9 local night games)
print("\nTesting Feb 10 (Next Local Gameday)...")
r_feb10 = requests.get(base_url, params={"date": "2026-02-10"})
games_feb10 = r_feb10.json()
print(f"Found {len(games_feb10)} games for Feb 10.")
for g in games_feb10:
    print(f"  Game ID: {g['id']} | Date: {g['game_date']} | Status: {g['status']}")

# 3. Test Far Future (2026-02-12)
print("\nTesting Far Future (2026-02-12)...")
r_future = requests.get(base_url, params={"date": "2026-02-12"})
games_future = r_future.json()
print(f"Found {len(games_future)} games.")
for g in games_future:
    print(f"  Game ID: {g['id']} | Date: {g['game_date']} | Status: {g['status']}")
