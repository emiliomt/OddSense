import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# PostgreSQL SSL configuration for Neon/Replit
# Append SSL mode to URL if not already present
if "?" not in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL + "?sslmode=require"
elif "sslmode" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL + "&sslmode=require"

engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserSession(Base):
    """Anonymous user session tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_active = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_predictions = Column(Integer, default=0)
    
    predictions = relationship("Prediction", back_populates="user_session")


class Game(Base):
    """Store game information for tracking outcomes"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    event_ticker = Column(String, unique=True, index=True, nullable=False)
    sport = Column(String, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    game_date = Column(DateTime, nullable=True)
    close_date = Column(DateTime, nullable=True)
    
    # Game outcome (filled after game completes)
    is_completed = Column(Boolean, default=False)
    winner = Column(String, nullable=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    predictions = relationship("Prediction", back_populates="game")


class Prediction(Base):
    """User predictions for games"""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    
    # Prediction details
    predicted_winner = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)  # 0-100 slider value
    
    # Context at time of prediction
    kalshi_probability = Column(Float, nullable=True)
    sportsbook_consensus = Column(Float, nullable=True)
    
    # Outcome tracking (filled after game completes)
    is_correct = Column(Boolean, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user_session = relationship("UserSession", back_populates="predictions")
    game = relationship("Game", back_populates="predictions")


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, let caller manage
