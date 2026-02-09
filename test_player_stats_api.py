import requests
import json

def test_player_stats_api():
    url = "https://stats.nba.com/stats/leaguedashplayerstats"
    params = {
        "MeasureType": "Base",
        "PerMode": "PerGame",
        "PlusMinus": "N",
        "PaceAdjust": "N",
        "Rank": "N",
        "LeagueID": "00",
        "Season": "2024-25",
        "SeasonType": "Regular Season",
        "PORound": "0",
        "Outcome": "",
        "Location": "",
        "Month": "0",
        "SeasonSegment": "",
        "DateFrom": "",
        "DateTo": "",
        "OpponentTeamID": "0",
        "VsConference": "",
        "VsDivision": "",
        "TeamID": "0",
        "Conference": "",
        "Division": "",
        "GameSegment": "",
        "Period": "0",
        "ShotClockRange": "",
        "LastNGames": "0"
    }
    headers = {
        "Host": "stats.nba.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true",
        "Connection": "keep-alive",
        "Referer": "https://www.nba.com/",
        "Origin": "https://www.nba.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
    }

    try:
        print("Starting request...")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Successfully fetched player stats!")
            # Save a sample
            with open("player_stats_sample.json", "w") as f:
                json.dump(data, f, indent=2)
            
            # Print headers to check available fields
            if "resultSets" in data and len(data["resultSets"]) > 0:
                print("Headers:", data["resultSets"][0]["headers"])
        else:
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_player_stats_api()
