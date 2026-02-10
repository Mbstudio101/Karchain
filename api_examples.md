# NBA API Implementation Examples

Here is how you would implement the APIs you highlighted in your `Karchain` backend.

## 1. Using `nba_api` (Live Scoreboard)
This is the most "official" feeling library. It requires `pip install nba_api`.

```python
from nba_api.live.nba.endpoints import scoreboard

def get_live_scores():
    # Fetch today's scoreboard
    board = scoreboard.ScoreBoard()
    
    # Get the JSON data
    data = board.get_dict()
    games = data['scoreboard']['games']
    
    for game in games:
        home = game['homeTeam']['teamName']
        away = game['awayTeam']['teamName']
        score = f"{game['awayTeam']['score']} - {game['homeTeam']['score']}"
        status = game['gameStatusText']
        print(f"{away} @ {home}: {score} ({status})")

# Sample Output:
# Pistons @ Hornets: 0 - 0 (7:00 PM ET)
```

## 2. Using `NBA.net` (Direct JSON)
Simple, no library required besides `requests`.

```python
import requests
from datetime import datetime

def get_daily_json():
    # The URL pattern for daily scoreboards
    today = datetime.now().strftime("%Y%m%d")
    url = f"http://data.nba.net/10s/prod/v1/{today}/scoreboard.json"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for game in data.get('games', []):
            print(f"{game['vTeam']['triCode']} @ {game['hTeam']['triCode']}")
    else:
        print("NBA.net endpoint might be outdated or changed.")
```

> [!NOTE]
> `nba_api` is much more reliable as it's actively maintained to track changes in NBA's private endpoints. `NBA.net` URLs are known to occasionally "break" when the NBA updates their site layout.

---

### Which one would you like to try first?
I can create a test script in `backend/scripts/test_api_new.py` for either of these.
