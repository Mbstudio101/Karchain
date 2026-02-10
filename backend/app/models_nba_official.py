#!/usr/bin/env python3
"""
Database model for NBA Official Season Stats

This model stores season-long player statistics from the official NBA API,
including advanced metrics like hustle stats and defensive ratings.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class NBAOfficialPlayerStats(Base):
    """
    Season-long player statistics from NBA.com official API.
    Includes traditional, advanced, hustle, and defensive metrics.
    """
    __tablename__ = "nba_official_player_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, nullable=False, index=True)
    player_name = Column(String, nullable=False, index=True)
    team_id = Column(Integer, nullable=False, index=True)
    team_abbreviation = Column(String, nullable=False, index=True)
    season = Column(String, nullable=False, index=True)
    season_type = Column(String, nullable=False, default="Regular Season")
    
    # Basic stats
    games_played = Column(Integer, default=0)
    minutes_played = Column(Float, default=0.0)
    age = Column(Float, nullable=True)
    position = Column(String, nullable=True)
    
    # Traditional stats
    points = Column(Float, default=0.0)
    rebounds = Column(Float, default=0.0)
    assists = Column(Float, default=0.0)
    steals = Column(Float, default=0.0)
    blocks = Column(Float, default=0.0)
    turnovers = Column(Float, default=0.0)
    
    # Shooting stats
    field_goals_made = Column(Float, default=0.0)
    field_goals_attempted = Column(Float, default=0.0)
    field_goal_percentage = Column(Float, default=0.0)
    three_points_made = Column(Float, default=0.0)
    three_points_attempted = Column(Float, default=0.0)
    three_point_percentage = Column(Float, default=0.0)
    free_throws_made = Column(Float, default=0.0)
    free_throws_attempted = Column(Float, default=0.0)
    free_throw_percentage = Column(Float, default=0.0)
    
    # Advanced stats
    plus_minus = Column(Float, default=0.0)
    efficiency = Column(Float, nullable=True)
    usage_rate = Column(Float, nullable=True)
    true_shooting_percentage = Column(Float, nullable=True)
    
    # Hustle stats (from leaguehustlestatsplayer endpoint)
    contested_shots = Column(Float, default=0.0)
    contested_shots_2pt = Column(Float, default=0.0)
    contested_shots_3pt = Column(Float, default=0.0)
    deflections = Column(Float, default=0.0)
    charges_drawn = Column(Float, default=0.0)
    screen_assists = Column(Float, default=0.0)
    screen_assist_points = Column(Float, default=0.0)
    loose_balls_recovered = Column(Float, default=0.0)
    off_loose_balls_recovered = Column(Float, default=0.0)
    def_loose_balls_recovered = Column(Float, default=0.0)
    box_outs = Column(Float, default=0.0)
    off_box_outs = Column(Float, default=0.0)
    def_box_outs = Column(Float, default=0.0)
    box_out_team_rebounds = Column(Float, default=0.0)
    box_out_player_rebounds = Column(Float, default=0.0)
    
    # Defense stats (from leaguedashptdefend endpoint)
    defense_frequency = Column(Float, default=0.0)
    defense_fgm = Column(Float, default=0.0)
    defense_fga = Column(Float, default=0.0)
    defense_fg_percentage = Column(Float, default=0.0)
    defense_fg_percentage_diff = Column(Float, default=0.0)  # vs normal FG%
    
    # Raw data for future use
    raw_data = Column(JSON, nullable=True)
    
    # Metadata
    stat_type = Column(String, nullable=False, default="official")  # official, hustle, defense, etc.
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Create composite indexes for efficient queries
    __table_args__ = (
        Index('idx_nba_player_season', 'player_id', 'season'),
        Index('idx_nba_player_team_season', 'team_id', 'season'),
        Index('idx_nba_player_stat_type_season', 'stat_type', 'season'),
    )

class NBAOfficialTeamStats(Base):
    """
    Season-long team statistics from NBA.com official API.
    Includes traditional, advanced, and team-specific metrics.
    """
    __tablename__ = "nba_official_team_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, nullable=False, index=True)
    team_name = Column(String, nullable=False, index=True)
    team_abbreviation = Column(String, nullable=False, index=True)
    season = Column(String, nullable=False, index=True)
    season_type = Column(String, nullable=False, default="Regular Season")
    
    # Basic stats
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_percentage = Column(Float, default=0.0)
    
    # Traditional stats (per game)
    points_per_game = Column(Float, default=0.0)
    rebounds_per_game = Column(Float, default=0.0)
    assists_per_game = Column(Float, default=0.0)
    steals_per_game = Column(Float, default=0.0)
    blocks_per_game = Column(Float, default=0.0)
    turnovers_per_game = Column(Float, default=0.0)
    
    # Shooting stats
    field_goal_percentage = Column(Float, default=0.0)
    three_point_percentage = Column(Float, default=0.0)
    free_throw_percentage = Column(Float, default=0.0)
    
    # Advanced stats
    offensive_rating = Column(Float, nullable=True)
    defensive_rating = Column(Float, nullable=True)
    net_rating = Column(Float, nullable=True)
    pace = Column(Float, nullable=True)
    
    # Hustle stats (team version)
    team_contested_shots = Column(Float, default=0.0)
    team_deflections = Column(Float, default=0.0)
    team_charges_drawn = Column(Float, default=0.0)
    team_screen_assists = Column(Float, default=0.0)
    team_loose_balls_recovered = Column(Float, default=0.0)
    team_box_outs = Column(Float, default=0.0)
    
    # Defense vs Position (DvP) rankings (1-30, 1=best defense)
    dvp_pg_points = Column(Integer, nullable=True)
    dvp_sg_points = Column(Integer, nullable=True)
    dvp_sf_points = Column(Integer, nullable=True)
    dvp_pf_points = Column(Integer, nullable=True)
    dvp_c_points = Column(Integer, nullable=True)
    
    # Raw data for future use
    raw_data = Column(JSON, nullable=True)
    
    # Metadata
    stat_type = Column(String, nullable=False, default="official")
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Create composite indexes for efficient queries
    __table_args__ = (
        Index('idx_nba_team_season', 'team_id', 'season'),
        Index('idx_nba_team_stat_type_season', 'stat_type', 'season'),
    )