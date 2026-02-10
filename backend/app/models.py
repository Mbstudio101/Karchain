from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Date, JSON, Index
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

# Import NBA official stats models
from .models_nba_official import NBAOfficialPlayerStats, NBAOfficialTeamStats

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    sport = Column(String)
    conference = Column(String, nullable=True)
    division = Column(String, nullable=True)
    current_record = Column(String, nullable=True)

    players = relationship("Player", back_populates="team")
    home_games = relationship("Game", back_populates="home_team", foreign_keys="Game.home_team_id")
    away_games = relationship("Game", back_populates="away_team", foreign_keys="Game.away_team_id")
    stats = relationship("TeamStats", back_populates="team")
    logo_url = Column(String, nullable=True)  # Team logo URL

class TeamStats(Base):
    __tablename__ = "team_stats"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    season = Column(String)
    wins = Column(Integer)
    losses = Column(Integer)
    win_pct = Column(Float)
    ppg = Column(Float)
    opp_ppg = Column(Float)
    plus_minus = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="stats")

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    position = Column(String)
    sport = Column(String)
    active_status = Column(Boolean, default=True)

    team = relationship("Team", back_populates="players")
    stats = relationship("PlayerStats", back_populates="player")
    injuries = relationship("Injury", back_populates="player")
    props = relationship("PlayerProps", back_populates="player")
    headshot_url = Column(String, nullable=True)  # Player headshot URL

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    game_date = Column(DateTime)
    status = Column(String, default="Scheduled")  # Scheduled, Live, Final, Postponed
    home_score = Column(Integer, default=0)
    away_score = Column(Integer, default=0)
    quarter = Column(String, nullable=True)  # e.g. "Q1", "Halftime", "Final"
    clock = Column(String, nullable=True)    # e.g. "10:45"
    venue = Column(String, nullable=True)
    sport = Column(String)

    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    odds = relationship("BettingOdds", back_populates="game")
    recommendations = relationship("Recommendation", back_populates="game")

class PlayerStats(Base):
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    game_id = Column(Integer, ForeignKey("games.id"), nullable=True) # Optional link to game
    game_date = Column(Date)
    opponent = Column(String)
    points = Column(Float, default=0)
    rebounds = Column(Float, default=0)
    assists = Column(Float, default=0)
    steals = Column(Float, default=0)
    blocks = Column(Float, default=0)
    minutes_played = Column(Float, default=0)
    fg_percentage = Column(Float, nullable=True)
    three_pt_percentage = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    player = relationship("Player", back_populates="stats")

class PlayerProps(Base):
    """Player prop bets - points/rebounds/assists over/unders."""
    __tablename__ = "player_props"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    game_id = Column(Integer, ForeignKey("games.id"), nullable=True)
    prop_type = Column(String)  # 'points', 'rebounds', 'assists', 'pts+reb', 'pts+ast', etc.
    line = Column(Float)  # The over/under line (e.g., 24.5)
    over_odds = Column(Integer)  # American odds for over (e.g., -110)
    under_odds = Column(Integer)  # American odds for under (e.g., -110)
    
    # BettingPros Analyzer Data
    star_rating = Column(Float, nullable=True)  # 1-5 star rating from BettingPros
    bp_ev = Column(Float, nullable=True)  # BettingPros calculated expected value
    performance_pct = Column(Float, nullable=True)  # Hit rate over last 15 games
    recommended_side = Column(String, nullable=True)  # 'over' or 'under'
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    player = relationship("Player", back_populates="props")


class Injury(Base):
    __tablename__ = "injuries"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    injury_type = Column(String)
    status = Column(String) # Out, Questionable, Probable
    updated_date = Column(DateTime, default=datetime.utcnow)

    player = relationship("Player", back_populates="injuries")

class BettingOdds(Base):
    __tablename__ = "betting_odds"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    bookmaker = Column(String, default="FanDuel")
    
    # Moneyline
    home_moneyline = Column(Integer, nullable=True)
    away_moneyline = Column(Integer, nullable=True)
    
    # Spread
    spread_points = Column(Float, nullable=True)
    home_spread_price = Column(Integer, nullable=True)
    away_spread_price = Column(Integer, nullable=True)
    
    # Over/Under
    total_points = Column(Float, nullable=True)
    over_price = Column(Integer, nullable=True)
    under_price = Column(Integer, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="odds")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    bet_type = Column(String)
    recommended_pick = Column(String)
    confidence_score = Column(Float)
    reasoning = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="recommendations")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TeamDefenseStats(Base):
    """
    Advanced defensive metrics for teams.
    Used to adjust player props based on matchup difficulty.
    """
    __tablename__ = "team_defense_stats"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    season = Column(String)
    
    # Defense vs Position (DvP) Rankings (1-30, 1=Best Defense)
    # Stored as JSON or separate columns? Separate columns for easier querying.
    pg_points_rank = Column(Integer, nullable=True)
    sg_points_rank = Column(Integer, nullable=True)
    sf_points_rank = Column(Integer, nullable=True)
    pf_points_rank = Column(Integer, nullable=True)
    c_points_rank = Column(Integer, nullable=True)
    
    # Allowed Stats per game
    allowed_points = Column(Float, nullable=True)
    allowed_rebounds = Column(Float, nullable=True)
    allowed_assists = Column(Float, nullable=True)
    allowed_three_pointers = Column(Float, nullable=True)
    
    def_rating = Column(Float, nullable=True) # Defensive Rating (Points allowed per 100 poss)
    pace = Column(Float, nullable=True)       # Pace (Possessions per 48 min)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team")

class MLModelMetadata(Base):
    """Metadata for trained Machine Learning models."""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String)     # e.g., "xgboost_spread_v1"
    model_type = Column(String)     # e.g., "classifier", "regressor"
    version = Column(String)
    accuracy = Column(Float, nullable=True)
    mae = Column(Float, nullable=True) # Mean Absolute Error
    filepath = Column(String)       # Path to the serialized model file
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)

class PredictionOutcome(Base):
    """
    Tracks the actual result of predictions/recommendations.
    Used for model performance monitoring and self-improvement.
    """
    __tablename__ = "prediction_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    
    # Prediction details
    predicted_pick = Column(String)  # e.g., "MIA Heat -9.5"
    predicted_confidence = Column(Float)
    bet_type = Column(String)  # 'spread', 'total', 'moneyline', 'prop'
    
    # Actual result
    actual_result = Column(String)  # 'win', 'loss', 'push', 'pending'
    actual_score_home = Column(Integer, nullable=True)
    actual_score_away = Column(Integer, nullable=True)
    
    # Model tracking
    model_used = Column(String, nullable=True)  # 'xgboost', 'pythagorean', 'heuristic'
    feature_snapshot = Column(String, nullable=True)  # JSON of features used
    
    # Performance metrics
    profit_loss = Column(Float, default=0.0)  # Profit/loss amount (positive for win)
    odds_at_bet = Column(Integer, nullable=True)  # American odds when bet was placed
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    recommendation = relationship("Recommendation")
    game = relationship("Game")