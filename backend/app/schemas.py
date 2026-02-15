from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

# --- Odds Schemas ---
class OddsBase(BaseModel):
    bookmaker: str
    home_moneyline: Optional[int] = None
    away_moneyline: Optional[int] = None
    spread_points: Optional[float] = None
    home_spread_price: Optional[int] = None
    away_spread_price: Optional[int] = None
    total_points: Optional[float] = None
    over_price: Optional[int] = None
    under_price: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class TeamStatsBase(BaseModel):
    wins: int
    losses: int
    win_pct: float
    ppg: float
    opp_ppg: float
    plus_minus: float
    
    class Config:
        from_attributes = True

# --- Team Schemas ---
class TeamBase(BaseModel):
    id: int
    name: str
    sport: str
    conference: Optional[str] = None
    division: Optional[str] = None
    current_record: Optional[str] = None
    logo_url: Optional[str] = None
    stats: List[TeamStatsBase] = []

    class Config:
        from_attributes = True

class TeamInsightBase(BaseModel):
    team_id: int
    team_name: str
    team_abbr: str
    conference: Optional[str] = None
    division: Optional[str] = None
    current_record: Optional[str] = None
    logo_url: Optional[str] = None
    games_sampled: int = 0
    opp_points: Optional[float] = None
    opp_rebounds: Optional[float] = None
    opp_assists: Optional[float] = None
    opp_stocks: Optional[float] = None
    points_rank_most_allowed: Optional[int] = None
    rebounds_rank_most_allowed: Optional[int] = None
    assists_rank_most_allowed: Optional[int] = None
    stocks_rank_most_allowed: Optional[int] = None
    overall_easiest_rank: Optional[int] = None
    strengths: List[str] = []
    weaknesses: List[str] = []

    class Config:
        from_attributes = True

class RecommendationBase(BaseModel):
    id: int
    game_id: int
    bet_type: str
    recommended_pick: str
    confidence_score: float
    reasoning: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Game Schemas ---
class GameBase(BaseModel):
    id: int
    home_team_id: int
    away_team_id: int
    game_date: datetime
    venue: Optional[str] = None
    status: str = "Scheduled"
    home_score: int = 0
    away_score: int = 0
    quarter: Optional[str] = None
    clock: Optional[str] = None
    sport: str
    
    # Relationships
    home_team: Optional[TeamBase] = None
    away_team: Optional[TeamBase] = None
    odds: List[OddsBase] = []
    recommendations: List[RecommendationBase] = []

    class Config:
        from_attributes = True

# --- Player Schemas ---
class PlayerStatsBase(BaseModel):
    id: int
    game_date: Optional[datetime] = None
    opponent: Optional[str] = None
    points: float
    rebounds: float
    assists: float
    steals: float
    blocks: float
    minutes_played: float

    class Config:
        from_attributes = True

class PlayerBase(BaseModel):
    id: int
    name: str
    position: Optional[str] = None
    sport: str
    active_status: bool
    team_id: Optional[int] = None
    headshot_url: Optional[str] = None
    stats: List[PlayerStatsBase] = []

    class Config:
        from_attributes = True

# --- Player Props Schemas ---
class PlayerPropsBase(BaseModel):
    id: int
    player_id: Optional[int] = None
    game_id: Optional[int] = None
    prop_type: str  # 'points', 'rebounds', 'assists', 'pts+reb+ast'
    line: float
    over_odds: int
    under_odds: int
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Parlay Schemas ---
class ParlayLeg(BaseModel):
    game_id: int
    pick: str
    odds: int
    confidence: float
    player_name: Optional[str] = None
    player_headshot: Optional[str] = None
    opponent: Optional[str] = None
    matchup: Optional[str] = None

class ParlayBase(BaseModel):
    legs: List[ParlayLeg]
    combined_odds: int
    potential_payout: float  # For $100 stake
    confidence_score: float
    date_used: Optional[date] = None

# --- Auth Schemas ---
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
