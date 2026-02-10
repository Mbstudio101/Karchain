
import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import PlayerProps, Player, Team
from datetime import datetime, timedelta
from sqlalchemy import or_

# Check today's props in database
today = datetime.utcnow().date()
tomorrow = today + timedelta(days=1)

db = SessionLocal()
try:
    # Check for LeBron specifically
    lebron_props = db.query(PlayerProps).join(Player).filter(
        Player.name.ilike("%lebron%"),
        PlayerProps.timestamp >= today,
        PlayerProps.timestamp < tomorrow
    ).all()
    
    print(f"LeBron James props in database for today: {len(lebron_props)}")
    
    if lebron_props:
        for prop in lebron_props:
            print(f"  - {prop.prop_type}: {prop.line} (Over: {prop.over_odds}, Under: {prop.under_odds})")
    
    # Check for Luka
    luka_props = db.query(PlayerProps).join(Player).filter(
        Player.name.ilike("%luka%"),
        PlayerProps.timestamp >= today,
        PlayerProps.timestamp < tomorrow
    ).all()
    
    print(f"Luka Dončić props in database for today: {len(luka_props)}")
    
    if luka_props:
        for prop in luka_props:
            print(f"  - {prop.prop_type}: {prop.line} (Over: {prop.over_odds}, Under: {prop.under_odds})")
    
    # Check all Lakers props for today (via team relationship)
    lakers_props = db.query(PlayerProps).join(Player).join(Team).filter(
        or_(Team.name.ilike("%lakers%"), Team.name.ilike("%lal%")),
        PlayerProps.timestamp >= today,
        PlayerProps.timestamp < tomorrow
    ).all()
    
    print(f"Lakers props in database for today: {len(lakers_props)}")
    
    # Check all Dallas props
    dallas_props = db.query(PlayerProps).join(Player).join(Team).filter(
        or_(Team.name.ilike("%dallas%"), Team.name.ilike("%mavericks%"), Team.name.ilike("%dal%")),
        PlayerProps.timestamp >= today,
        PlayerProps.timestamp < tomorrow
    ).all()
    
    print(f"Dallas Mavericks props in database for today: {len(dallas_props)}")
    
    # Show first few Dallas players
    if dallas_props:
        dallas_players = set([prop.player.name for prop in dallas_props])
        print(f"  Dallas players with props: {list(dallas_players)[:10]}")
    
    # Show first few Lakers players
    if lakers_props:
        lakers_players = set([prop.player.name for prop in lakers_props])
        print(f"  Lakers players with props: {list(lakers_players)[:10]}")
    
finally:
    db.close()