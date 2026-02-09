import requests
from bs4 import BeautifulSoup
import json

def main():
    url = "https://www.nba.com/stats/teams/traditional"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        # 403 is common for stats.nba.com, but www.nba.com/stats might work
        print(f"Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data = soup.find("script", id="__NEXT_DATA__")
        
        if next_data:
            data = json.loads(next_data.string)
            print("Keys:", data.keys())
            if "props" in data and "pageProps" in data["props"]:
                props = data["props"]["pageProps"]
                print("PageProps keys:", props.keys())
                # Serialize and print a small part to check for stats
                # print(json.dumps(props, indent=2)[:500])
                if "initialState" in props:
                     print("InitialState found.")
        else:
            print("__NEXT_DATA__ not found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
