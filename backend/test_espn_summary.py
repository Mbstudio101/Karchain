import requests
import json

game_id = "401810614" # Pacers at Raptors
url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
print(f"Fetching from {url}...")

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    # Check for plays
    plays = data.get("plays", [])
    print(f"Found {len(plays)} plays.")
    
    if plays:
        print("\nLatest 5 Plays:")
        for play in plays[-5:]:
            clock = play.get("clock", {}).get("displayValue", "??")
            text = play.get("text", "No description")
            print(f"[{clock}] {text}")

    # Check for boxscore
    boxscore = data.get("boxscore", {})
    teams = boxscore.get("teams", [])
    print(f"\nFound boxscore for {len(teams)} teams.")
    for team in teams:
        team_name = team.get("team", {}).get("displayName")
        score = team.get("team", {}).get("score")
        print(f"Team: {team_name} | Score: {score}")

except Exception as e:
    print(f"Error: {e}")
