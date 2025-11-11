import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database import UserSession, Game, Prediction, get_db, init_db


class PredictionService:
    """Service for managing user predictions"""
    
    def __init__(self):
        # Initialize database tables on first run
        init_db()
    
    def get_or_create_session(self, session_id: str) -> UserSession:
        """Get existing user session or create new one"""
        db = get_db()
        try:
            user_session = db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if not user_session:
                user_session = UserSession(session_id=session_id)
                db.add(user_session)
                db.commit()
                db.refresh(user_session)
            else:
                # Update last active
                user_session.last_active = datetime.now(timezone.utc)
                db.commit()
            
            return user_session
        finally:
            db.close()
    
    def get_or_create_game(self, event_ticker: str, sport: str, 
                           home_team: str, away_team: str,
                           game_date=None, close_date=None) -> Game:
        """Get existing game or create new one"""
        db = get_db()
        try:
            game = db.query(Game).filter(
                Game.event_ticker == event_ticker
            ).first()
            
            if not game:
                game = Game(
                    event_ticker=event_ticker,
                    sport=sport,
                    home_team=home_team,
                    away_team=away_team,
                    game_date=game_date,
                    close_date=close_date
                )
                db.add(game)
                db.commit()
                db.refresh(game)
            
            return game
        finally:
            db.close()
    
    def save_prediction(self, session_id: str, event_ticker: str, sport: str,
                       home_team: str, away_team: str, predicted_winner: str,
                       confidence: float, kalshi_prob: float = None,
                       sportsbook_consensus: float = None,
                       game_date=None, close_date=None) -> Prediction:
        """Save a user prediction"""
        db = get_db()
        try:
            # Get user session within same DB session
            user_session = db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if not user_session:
                user_session = UserSession(session_id=session_id)
                db.add(user_session)
                db.flush()  # Get ID without committing
            
            # Update last active
            user_session.last_active = datetime.now(timezone.utc)
            
            # Get or create game within same DB session
            game = db.query(Game).filter(
                Game.event_ticker == event_ticker
            ).first()
            
            if not game:
                game = Game(
                    event_ticker=event_ticker,
                    sport=sport,
                    home_team=home_team,
                    away_team=away_team,
                    game_date=game_date,
                    close_date=close_date
                )
                db.add(game)
                db.flush()  # Get ID without committing
            
            # Check if prediction already exists for this session + game
            existing = db.query(Prediction).filter(
                Prediction.session_id == user_session.id,
                Prediction.game_id == game.id
            ).first()
            
            if existing:
                # Update existing prediction
                existing.predicted_winner = predicted_winner
                existing.confidence = confidence
                existing.kalshi_probability = kalshi_prob
                existing.sportsbook_consensus = sportsbook_consensus
                existing.created_at = datetime.now(timezone.utc)
            else:
                # Create new prediction
                prediction = Prediction(
                    session_id=user_session.id,
                    game_id=game.id,
                    predicted_winner=predicted_winner,
                    confidence=confidence,
                    kalshi_probability=kalshi_prob,
                    sportsbook_consensus=sportsbook_consensus
                )
                db.add(prediction)
                
                # Update user session stats (now within same session)
                user_session.total_predictions = user_session.total_predictions + 1
            
            db.commit()
            return existing if existing else prediction
        finally:
            db.close()
    
    def get_user_prediction(self, session_id: str, event_ticker: str):
        """Get user's existing prediction for a game"""
        db = get_db()
        try:
            user_session = db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if not user_session:
                return None
            
            game = db.query(Game).filter(
                Game.event_ticker == event_ticker
            ).first()
            
            if not game:
                return None
            
            prediction = db.query(Prediction).filter(
                Prediction.session_id == user_session.id,
                Prediction.game_id == game.id
            ).first()
            
            return prediction
        finally:
            db.close()
    
    def get_community_consensus(self, event_ticker: str):
        """Get community consensus for a game"""
        db = get_db()
        try:
            game = db.query(Game).filter(
                Game.event_ticker == event_ticker
            ).first()
            
            if not game:
                return None
            
            predictions = db.query(Prediction).filter(
                Prediction.game_id == game.id
            ).all()
            
            if not predictions:
                return None
            
            # Calculate consensus
            home_predictions = [p for p in predictions if p.predicted_winner == game.home_team]
            away_predictions = [p for p in predictions if p.predicted_winner == game.away_team]
            
            total = len(predictions)
            home_pct = (len(home_predictions) / total * 100) if total > 0 else 0
            away_pct = (len(away_predictions) / total * 100) if total > 0 else 0
            
            # Average confidence
            avg_confidence = sum(p.confidence for p in predictions) / total if total > 0 else 0
            
            return {
                "total_predictions": total,
                "home_team": game.home_team,
                "away_team": game.away_team,
                "home_percentage": home_pct,
                "away_percentage": away_pct,
                "average_confidence": avg_confidence,
                "home_count": len(home_predictions),
                "away_count": len(away_predictions)
            }
        finally:
            db.close()
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return str(uuid.uuid4())
