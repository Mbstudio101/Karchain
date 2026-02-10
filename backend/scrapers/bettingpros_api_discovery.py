"""
BettingPros API Discovery Script
Probes the known API structure to find additional useful endpoints.
"""
import requests
import json

API_URL = "https://api.bettingpros.com/v3"
HEADERS = {
    "x-api-key": "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh",
    "referer": "https://www.bettingpros.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def probe_endpoint(endpoint, params=None, description=""):
    """Probe an endpoint and report what we find."""
    url = f"{API_URL}/{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        print(f"\n{'='*60}")
        print(f"ENDPOINT: {endpoint}")
        print(f"DESCRIPTION: {description}")
        print(f"STATUS: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"KEYS: {list(data.keys()) if isinstance(data, dict) else 'list/array'}")
            # Show a sample of the data
            print(f"SAMPLE: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"ERROR: {response.text[:200]}")
    except Exception as e:
        print(f"FAILED: {e}")

# --- Known Endpoints ---
print("\n\n*** KNOWN WORKING ENDPOINTS ***")
probe_endpoint("events", {"sport": "NBA", "date": "2026-02-09"}, "Game events for a specific date")
probe_endpoint("books", None, "List of available sportsbooks")
probe_endpoint("markets/offer-counts", {"sport": "NBA"}, "Count of offers per market type")

# --- Exploring New Endpoints (Based on Site Structure) ---
print("\n\n*** EXPLORING POTENTIAL NEW ENDPOINTS ***")

# Consensus / Picks
probe_endpoint("consensus", {"sport": "NBA"}, "Consensus picks")
probe_endpoint("picks", {"sport": "NBA"}, "Expert picks")
probe_endpoint("picks/consensus", {"sport": "NBA"}, "Consensus picks (alt)")
probe_endpoint("selections/consensus", {"sport": "NBA"}, "Selection consensus")

# Projections
probe_endpoint("projections", {"sport": "NBA"}, "Player/team projections")
probe_endpoint("projections/players", {"sport": "NBA"}, "Player projections")

# Defense vs Position
probe_endpoint("defense-vs-position", {"sport": "NBA"}, "Defense vs Position stats")
probe_endpoint("stats/defense-vs-position", {"sport": "NBA"}, "DvP stats (alt)")
probe_endpoint("dvp", {"sport": "NBA"}, "DvP stats (short)")

# Player Stats / Analysis
probe_endpoint("players", {"sport": "NBA"}, "Player list/stats")
probe_endpoint("player-stats", {"sport": "NBA"}, "Player statistics")
probe_endpoint("streaks", {"sport": "NBA"}, "Player/team streaks")

# Teams
probe_endpoint("teams", {"sport": "NBA"}, "Team list")
probe_endpoint("team-stats", {"sport": "NBA"}, "Team statistics")

# Ratings / Rankings
probe_endpoint("ratings", {"sport": "NBA"}, "Bet ratings")
probe_endpoint("rankings", {"sport": "NBA"}, "Power rankings")
probe_endpoint("power-rankings", {"sport": "NBA"}, "Power rankings (alt)")

# Accuracy / Leaderboard
probe_endpoint("accuracy", {"sport": "NBA"}, "Expert accuracy")
probe_endpoint("leaderboard", {"sport": "NBA"}, "Betting leaderboard")
probe_endpoint("experts", {"sport": "NBA"}, "Expert list")

# Best Bets / Featured
probe_endpoint("best-bets", {"sport": "NBA"}, "Best bets")
probe_endpoint("featured", {"sport": "NBA"}, "Featured bets")
probe_endpoint("top-picks", {"sport": "NBA"}, "Top picks")

# Matchups / Games Analysis
probe_endpoint("matchups", {"sport": "NBA"}, "Game matchups")
probe_endpoint("games", {"sport": "NBA"}, "Games (alt)")

# Trends
probe_endpoint("trends", {"sport": "NBA"}, "Betting trends")
probe_endpoint("line-movements", {"sport": "NBA"}, "Line movements")

# Props specific
probe_endpoint("props", {"sport": "NBA"}, "Prop bets overview")
probe_endpoint("prop-analyzer", {"sport": "NBA"}, "Prop bet analyzer data")

print("\n\n*** DISCOVERY COMPLETE ***")
