import requests
import json
import time

API_URL = "https://api.bettingpros.com/v3"
HEADERS = {
    "x-api-key": "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh",
    "referer": "https://www.bettingpros.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

MARKET_IDS = [
    129, 128, 127, 169, 170, 171, 174, 172, 132, 133, 135, 131, 130, 156, 364, 
    157, 151, 162, 147, 160, 152, 142, 136, 335, 336, 337, 338, 137, 138, 139, 
    140, 141, 144, 148, 149, 146, 143, 247, 145, 150, 163, 166, 153, 158, 154, 
    159, 161, 155, 164, 167, 168, 165, 248, 250, 252, 251, 249, 134, 350, 351, 
    352, 353, 354, 355, 356, 357, 358, 359, 363
]

def get_market_sample(market_id):
    try:
        url = f"{API_URL}/props"
        params = {
            "sport": "NBA",
            "market_id": market_id,
            "limit": 1
        }
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            data = response.json()
            props = data.get("props", [])
            if props:
                prop = props[0]
                return {
                    "name": prop.get("name"),
                    "prop_type": prop.get("prop_type"),
                    "market_name": prop.get("market_name")
                }
    except Exception as e:
        print(f"Error fetching market {market_id}: {e}")
    return None

print("Mapping Market IDs...")
for market_id in MARKET_IDS:
    sample = get_market_sample(market_id)
    if sample:
        print(f"Market {market_id}: {sample}")
    else:
        print(f"Market {market_id}: No data found")
    time.sleep(0.2)
