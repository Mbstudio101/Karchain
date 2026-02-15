from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from .. import models, schemas
from ..dependencies import get_db
from ..date_utils import get_current_gameday
from datetime import datetime, date

router = APIRouter(
    prefix="/players",
    tags=["players"],
)

@router.get("/", response_model=List[schemas.PlayerBase])
def list_players(date: date = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get players, optionally filtered by those playing on a specific gameday."""
    from sqlalchemy import exists, or_
    
    query = db.query(models.Player).options(joinedload(models.Player.stats))
    
    if date:
        # Filter for players on teams playing today
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        
        # Subquery for teams playing on this date
        active_teams_subquery = db.query(models.Game.home_team_id).filter(
            models.Game.game_date >= start_of_day,
            models.Game.game_date <= end_of_day
        ).union(
            db.query(models.Game.away_team_id).filter(
                models.Game.game_date >= start_of_day,
                models.Game.game_date <= end_of_day
            )
        ).subquery()
        
        query = query.filter(models.Player.team_id.in_(active_teams_subquery))
    
    # Return players that have at least one recorded stat row.
    # This prevents empty cards in the frontend player directory.
    query = query.filter(exists().where(models.PlayerStats.player_id == models.Player.id))

    players = query.offset(skip).limit(limit).all()
    return players

@router.get("/team/{team_id}", response_model=List[schemas.PlayerBase])
def get_players_by_team(team_id: int, db: Session = Depends(get_db)):
    """Get all players for a specific team."""
    players = db.query(models.Player).options(
        joinedload(models.Player.stats)
    ).filter(models.Player.team_id == team_id).all()
    return players

@router.get("/top-performers", response_model=List[schemas.PlayerBase])
def get_top_performers(limit: int = 10, db: Session = Depends(get_db)):
    """Get top performers based on recent PPG."""
    # Subquery to get average points per player
    from sqlalchemy import func
    
    players = db.query(models.Player).options(
        joinedload(models.Player.stats)
    ).join(models.PlayerStats).group_by(models.Player.id).order_by(
        func.avg(models.PlayerStats.points).desc()
    ).limit(limit).all()
    
    return players

@router.get("/{player_id}/props", response_model=List[schemas.PlayerPropsBase])
def get_player_props(player_id: int, db: Session = Depends(get_db)):
    """Get all betting props for a specific player."""
    props = db.query(models.PlayerProps).filter(
        models.PlayerProps.player_id == player_id
    ).all()
    return props

@router.get("/props/all", response_model=List[schemas.PlayerPropsBase])
def get_all_props(date: date = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all player props. Defaults to all active or upcoming games."""
    query = db.query(models.PlayerProps).join(models.Game)
    
    if date:
        # If a specific date is requested, filter by it
        query = query.filter(
            models.Game.game_date >= datetime.combine(date, datetime.min.time()),
            models.Game.game_date <= datetime.combine(date, datetime.max.time())
        )
    else:
        # Otherwise show all upcoming/active games
        query = query.filter(models.Game.status.in_(["Scheduled", "Live"]))
        
    props = query.order_by(models.PlayerProps.timestamp.desc()).offset(skip).limit(limit).all()
    return props


@router.get("/{player_id}", response_model=schemas.PlayerBase)
def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get a specific player with all their stats."""
    player = db.query(models.Player).options(
        joinedload(models.Player.stats)
    ).filter(models.Player.id == player_id).first()

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
