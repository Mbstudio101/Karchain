from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime, timedelta
from .. import models, schemas
from ..dependencies import get_db
from ..date_utils import get_current_gameday
from scrapers.espn_sync import sync_upcoming_games

router = APIRouter(
    prefix="/games",
    tags=["games"]
)

@router.get("/", response_model=List[schemas.GameBase])
def read_games(
    date: date = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Returns games, but also performs a real-time sync with ESPN and a safety auto-correct.
    Filter by 'date' (YYYY-MM-DD). Defaults to today if not provided.
    """
    # Use today's date (adjusted for late night NBA games)
    if date is None:
        date = get_current_gameday()
        
    # 1. Sync with ESPN for real-time scores and official status (next 3 days)
    try:
        sync_upcoming_games(3)
    except Exception as e:
        print(f"ESPN Sync failed: {e}")

    # 2. Lazy Auto-Correct fallback (12 hours)
    now = datetime.utcnow()
    stale_threshold = now - timedelta(hours=12)
    
    # Identify stale games
    stale_games = db.query(models.Game).filter(
        models.Game.status.in_(["Live", "Scheduled"]),
        models.Game.game_date < stale_threshold
    ).all()
    
    if stale_games:
        for game in stale_games:
            game.status = "Final"
        db.commit()
    
    # 3. Return games for the specific date
    start_of_day = datetime.combine(date, datetime.min.time())
    end_of_day = datetime.combine(date, datetime.max.time())
    
    games = db.query(models.Game).filter(
        models.Game.game_date >= start_of_day,
        models.Game.game_date <= end_of_day
    ).order_by(models.Game.game_date.desc()).offset(skip).limit(limit).all()
    
    return games

from sqlalchemy.orm import Session, joinedload

# ... existing imports ...

@router.get("/{game_id}", response_model=schemas.GameBase)
def read_game(game_id: int, db: Session = Depends(get_db)):
    # 1. Fetch game basic info
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    # 2. Trigger a targeted ESPN sync for this game's date
    try:
        from scrapers.espn_sync import sync_espn_data
        game_date_str = game.game_date.strftime("%Y%m%d")
        sync_espn_data(game_date_str)
        # Refresh game object after sync
        db.refresh(game)
    except Exception as e:
        print(f"Targeted ESPN Sync failed: {e}")

    # 3. Return full game details with relations
    return db.query(models.Game).options(
        joinedload(models.Game.home_team).joinedload(models.Team.stats),
        joinedload(models.Game.away_team).joinedload(models.Team.stats),
        joinedload(models.Game.odds)
    ).filter(models.Game.id == game_id).first()

@router.get("/{game_id}/tracker")
def read_game_tracker(game_id: int, db: Session = Depends(get_db)):
    """
    Fetches real-time play-by-play data from ESPN for a specific game.
    """
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    # 1. We need the ESPN Event ID. 
    # Since we might not have it stored directly, we fetch the scoreboard for that date
    # and find the event matching our teams.
    import requests
    from scrapers.espn_sync import ESPN_SCOREBOARD_URL
    
    date_str = game.game_date.strftime("%Y%m%d")
    try:
        sb_response = requests.get(f"{ESPN_SCOREBOARD_URL}?dates={date_str}", timeout=10)
        sb_response.raise_for_status()
        sb_data = sb_response.json()
        
        espn_event_id = None
        for event in sb_data.get("events", []):
            name = event.get("name", "").lower()
            # Loose match team names
            if game.home_team.name.lower() in name and game.away_team.name.lower() in name:
                espn_event_id = event.get("id")
                break
                
        if not espn_event_id:
            # Fallback: if we just synced this game, it might be the only one or we use teams
            # In a production app, we'd store espn_id in the Game model.
            return {"plays": [], "message": "ESPN Event ID not found for this matchup"}

        # 2. Fetch Detail Summary
        summary_url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={espn_event_id}"
        resp = requests.get(summary_url, timeout=10)
        resp.raise_for_status()
        summary_data = resp.json()
        
        plays = summary_data.get("plays", [])
        # Return last 20 plays
        formatted_plays = []
        for p in plays[-20:]:
            formatted_plays.append({
                "id": p.get("id"),
                "clock": p.get("clock", {}).get("displayValue"),
                "text": p.get("text"),
                "type": p.get("type", {}).get("text"),
                "scoreValue": p.get("scoreValue")
            })
            
        return {
            "game_id": game_id,
            "espn_id": espn_event_id,
            "status": summary_data.get("header", {}).get("competitions", [{}])[0].get("status", {}).get("type", {}).get("description"),
            "plays": formatted_plays[::-1] # Newest first
        }

    except Exception as e:
        print(f"Tracker Fetch failed: {e}")
        return {"plays": [], "error": str(e)}

@router.get("/{game_id}/odds", response_model=List[schemas.OddsBase])
def read_game_odds(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.odds
