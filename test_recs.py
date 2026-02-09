import requests
import time
import sys

def test_recs():
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

    # Generate Recommendations
    print("Generating recommendations...")
    r = requests.post(f"{base_url}/recommendations/generate")
    if r.status_code == 200:
        recs = r.json()
        print(f"Generated {len(recs)} recommendations.")
        for rec in recs:
            print(f"- {rec['bet_type']} on {rec['recommended_pick']}: {rec['reasoning']}")
    else:
        print(f"Failed to generate recommendations: {r.status_code} {r.text}")

    # Fetch Recommendations
    print("Fetching all recommendations...")
    r = requests.get(f"{base_url}/recommendations/")
    print(f"Found {len(r.json())} total recommendations.")

if __name__ == "__main__":
    test_recs()
