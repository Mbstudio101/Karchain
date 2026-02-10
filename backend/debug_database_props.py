
import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import PlayerProps
from datetime import datetime, timedelta

# Check today's props in database
today = datetime.utcnow().date()
tomorrow = today + timedelta(days=1)

db = SessionLocal()
try:
    # Check all Lakers props for today
    lakers_props = db.query(PlayerProps).filter(
        PlayerProps.team.ilike("%lakers%"),
        PlayerProps.created_date >= today,
        PlayerProps.created_date < tomorrow
    ).all()
    
    print(f"Lakers props in database for today: {len(lakers_props)}")
    
    # Check for LeBron specifically
    lebron_props = db.query(PlayerProps).filter(
        PlayerProps.player_name.ilike("%lebron%"),
        PlayerProps.created_date >= today,
        PlayerProps.created_date < tomorrow
    ).all()
    
    print(f"LeBron James props in database for today: {len(lebron_props)}")
    
    if lebron_props:
        for prop in lebron_props:
            print(f"  - {prop.prop_type}: {prop.line} (Over: {prop.over_odds}, Under: {prop.under_odds})")
    
    # Check for Luka
    luka_props = db.query(PlayerProps).filter(
        PlayerProps.player_name.ilike("%luka%"),
        PlayerProps.created_date >= today,
        PlayerProps.created_date < tomorrow
    ).all()
    
    print(f"Luka Dončić props in database for today: {len(luka_props)}")
    
    if luka_props:
        for prop in luka_props:
            print(f"  - {prop.prop_type}: {prop.line} (Over: {prop.over_odds}, Under: {prop.under_odds})")
    
    # Check all Dallas props
    dallas_props = db.query(PlayerProps).filter(
        PlayerProps.team.ilike("%dallas%") | PlayerProps.team.ilike("%mavericks%"),
        PlayerProps.created_date >= today,
        PlayerProps.created_date < tomorrow
    ).all()
    
    print(f"Dallas Mavericks props in database for today: {len(dallas_props)}")
    
    # Show first few Dallas players
    if dallas_props:
        dallas_players = set([prop.player_name for prop in dallas_props])
        print(f"  Dallas players with props: {list(dallas_players)[:5]}")
    
finally:
    db.close()