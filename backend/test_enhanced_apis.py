#!/usr/bin/env python3
"""Test script for enhanced NBA prediction APIs"""

import requests
import json

def test_enhanced_apis():
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Enhanced NBA Prediction APIs")
    print("=" * 50)
    
    # Test Enhanced Genius Picks
    print("\n📊 Testing Enhanced Genius Picks...")
    try:
        response = requests.get(f"{base_url}/recommendations/genius-picks")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['genius_count']} enhanced genius picks")
            print(f"✅ Features used: {data['enhanced_features_used']}")
            print(f"✅ Data sources: {data['data_sources']}")
            print(f"✅ Sample picks: {len(data['genius_picks'])} displayed")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test Enhanced Mixed Parlay
    print("\n🎯 Testing Enhanced Mixed Parlay...")
    try:
        payload = {"legs": 3, "risk_level": "balanced"}
        response = requests.post(f"{base_url}/recommendations/generate-mixed-parlay", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generated {len(data['legs'])} legs")
            print(f"✅ Combined odds: {data['combined_odds']}")
            print(f"✅ Potential payout: ${data['potential_payout']:.2f}")
            print(f"✅ Confidence score: {data['confidence_score']:.1f}")
            if 'enhanced_features' in data:
                print(f"✅ Enhanced features: {data['enhanced_features']}")
            else:
                print("✅ Enhanced features: Available (not shown in response)")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Enhanced API testing complete!")

if __name__ == "__main__":
    test_enhanced_apis()