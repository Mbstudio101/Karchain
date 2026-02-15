from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case, exists, select
from typing import List, Optional
from datetime import date, datetime, timedelta
from .. import models, schemas
from ..dependencies import get_db
from ..date_utils import get_client_timezone, get_current_gameday, get_gameday_range, game_datetime_to_gameday

router = APIRouter(
    prefix="/games",
    tags=["games"]
)


def _sync_espn_for_date(target_date: date):
    """
    Run ESPN sync for a specific date in a background-safe way.
    Uses its own DB session (espn_sync creates one internally).
    """
    try:
        from scrapers.espn_sync import sync_espn_data
        date_str = target_date.strftime("%Y%m%d")
        sync_espn_data(date_str)
    except Exception as e:
        print(f"ESPN Sync failed for {target_date}: {e}")


def _sync_espn_today_and_tomorrow(timezone_name: str = "America/New_York"):
    """Sync today and tomorrow to catch upcoming games."""
    today = get_current_gameday(timezone_name)
    _sync_espn_for_date(today)
    _sync_espn_for_date(today + timedelta(days=1))


@router.get("/", response_model=List[schemas.GameBase])
def read_games(
    request: Request,
    date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Returns games for a gameday, with real-time ESPN score sync.
    Defaults to today's gameday (Eastern time, 5 AM cutoff).
    """
    client_tz = get_client_timezone(request)
    if date is None:
        date = get_current_gameday(client_tz)

    # 1. Sync with ESPN for real-time scores (today + tomorrow)
    _sync_espn_today_and_tomorrow(client_tz)

    # The ESPN sync uses its own session, so we need to expire
    # our session's cache to see the updated scores
    db.expire_all()

    # 2. Auto-correct stale games (>12 hours old still marked Live/Scheduled)
    now = datetime.utcnow()
    stale_threshold = now - timedelta(hours=12)
    stale_games = db.query(models.Game).filter(
        models.Game.status.in_(["Live", "Scheduled"]),
        models.Game.game_date < stale_threshold
    ).all()
    if stale_games:
        for game in stale_games:
            game.status = "Final"
        db.commit()

    # 3. Query games using the UTC-aware gameday range
    #    A 7:30 PM ET game on Feb 10 = 00:30 UTC Feb 11,
    #    so we use get_gameday_range() which accounts for this.
    start_utc, end_utc = get_gameday_range(date, client_tz)

    has_odds = exists(
        select(models.BettingOdds.id).where(
            models.BettingOdds.game_id == models.Game.id
        )
    )

    games = db.query(models.Game).options(
        joinedload(models.Game.home_team).joinedload(models.Team.stats),
        joinedload(models.Game.away_team).joinedload(models.Team.stats),
        joinedload(models.Game.odds),
        joinedload(models.Game.recommendations)
    ).filter(
        models.Game.game_date >= start_utc,
        models.Game.game_date < end_utc,
        has_odds  # Only return games that have betting odds
    ).order_by(
        models.Game.game_date.asc()
    ).offset(skip).limit(limit).all()

    return games


@router.get("/available-dates", response_model=List[date])
def get_available_game_dates(request: Request, db: Session = Depends(get_db)):
    """Get all dates that have games in the database."""
    # Query all game dates
    # We use a raw query for efficiency to just get distinct dates
    dates = db.query(models.Game.game_date).all()
    client_tz = get_client_timezone(request)
    
    # Extract unique dates (converting datetime to date)
    unique_dates = set()
    for d in dates:
        if isinstance(d[0], datetime):
            unique_dates.add(game_datetime_to_gameday(d[0], client_tz))
        else:
            unique_dates.add(d[0])
            
    return sorted(list(unique_dates))


@router.get("/{game_id}", response_model=schemas.GameBase)
def read_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Trigger a targeted ESPN sync for this game's date
    _sync_espn_for_date(game.game_date.date() if isinstance(game.game_date, datetime) else game.game_date)

    # Expire cache so we see updated scores from the sync
    db.expire_all()

    return db.query(models.Game).options(
        joinedload(models.Game.home_team).joinedload(models.Team.stats),
        joinedload(models.Game.away_team).joinedload(models.Team.stats),
        joinedload(models.Game.odds),
        joinedload(models.Game.recommendations)
    ).filter(models.Game.id == game_id).first()


@router.get("/{game_id}/tracker")
def read_game_tracker(game_id: int, db: Session = Depends(get_db)):
    """Fetches real-time play-by-play data from ESPN for a specific game."""
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

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
            if game.home_team.name.lower() in name and game.away_team.name.lower() in name:
                espn_event_id = event.get("id")
                break

        if not espn_event_id:
            return {"plays": [], "message": "ESPN Event ID not found for this matchup"}

        summary_url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={espn_event_id}"
        resp = requests.get(summary_url, timeout=10)
        resp.raise_for_status()
        summary_data = resp.json()

        plays = summary_data.get("plays", [])
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
            "plays": formatted_plays[::-1]
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
