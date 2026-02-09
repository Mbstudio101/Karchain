from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class BettingOdds(Base):
    __tablename__ = "betting_odds"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, index=True) # FanDuel Game ID
    team_id = Column(Integer, ForeignKey("teams.id"))
    bookmaker = Column(String, default="FanDuel")
    
    # Moneyline
    moneyline = Column(Integer) # e.g. -150, +130
    
    # Spread
    spread_points = Column(Float) # e.g. -5.5
    spread_price = Column(Integer) # e.g. -110
    
    # Over/Under
    total_points = Column(Float) # e.g. 215.5
    over_price = Column(Integer) # e.g. -110
    under_price = Column(Integer) # e.g. -110
    
    timestamp = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team")
