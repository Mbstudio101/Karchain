import requests
import time
import subprocess
import sys

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    print("Waiting for API to start...")
    for i in range(10):
        try:
            r = requests.get(f"{base_url}/health")
            if r.status_code == 200:
                print("API is up!")
                break
        except:
            time.sleep(1)
    else:
        print("API failed to start within 10 seconds.")
        sys.exit(1)

    # Test Root
    r = requests.get(f"{base_url}/")
    print(f"Root: {r.json()}")

    # Test Games
    r = requests.get(f"{base_url}/games")
    print(f"Games status: {r.status_code}")
    games = r.json()
    print(f"Found {len(games)} games.")
    
    if games:
        game_id = games[0]['id']
        # Test specific game
        r = requests.get(f"{base_url}/games/{game_id}")
        print(f"Game {game_id}: {r.json()['sport']}")
        
        # Test Odds
        r = requests.get(f"{base_url}/games/{game_id}/odds")
        print(f"Game odds: {len(r.json())}")

    # Test Teams
    r = requests.get(f"{base_url}/teams")
    print(f"Teams status: {r.status_code}")
    print(f"Found {len(r.json())} teams.")

if __name__ == "__main__":
    test_api()
