import requests
import json

def test_game_log_api():
    url = "https://stats.nba.com/stats/leaguegamelog"
    params = {
        "Counter": "1000",
        "DateFrom": "",
        "DateTo": "",
        "Direction": "DESC",
        "LeagueID": "00",
        "PlayerOrTeam": "P",
        "Season": "2024-25",
        "SeasonType": "Regular Season",
        "Sorter": "DATE"
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
            print("Successfully fetched game logs!")
            # Save a sample
            with open("game_log_sample.json", "w") as f:
                json.dump(data, f, indent=2)
            
            if "resultSets" in data and len(data["resultSets"]) > 0:
                print("Headers:", data["resultSets"][0]["headers"])
                print(f"Total rows: {len(data['resultSets'][0]['rowSet'])}")
        else:
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_game_log_api()
