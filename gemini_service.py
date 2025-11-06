import os
import logging
from typing import Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for generating AI-powered game summaries and insights using Google Gemini."""
    
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
    
    def generate_game_summary(
        self,
        away_team: str,
        home_team: str,
        kalshi_prob: Optional[float] = None,
        sportsbook_prob: Optional[float] = None,
        game_date: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate an AI-powered game summary with player insights.
        
        Args:
            away_team: Name of the away team
            home_team: Name of the home team
            kalshi_prob: Kalshi prediction market probability for the favored team
            sportsbook_prob: Sportsbook consensus probability
            game_date: Game date if available
            
        Returns:
            Generated summary text or None if generation fails
        """
        if not self.client:
            return None
        
        try:
            # Build context for the prompt
            context_parts = [f"NFL matchup: {away_team} at {home_team}"]
            
            if game_date:
                context_parts.append(f"Game date: {game_date}")
            
            if kalshi_prob is not None:
                context_parts.append(f"Prediction market probability: {kalshi_prob*100:.0f}%")
            
            if sportsbook_prob is not None:
                context_parts.append(f"Sportsbook consensus: {sportsbook_prob*100:.0f}%")
            
            context = "\n".join(context_parts)
            
            # Create a detailed prompt for game analysis
            prompt = f"""You are an expert NFL analyst. Generate a concise game preview for this matchup:

{context}

Provide a 3-4 sentence summary that includes:
1. Key storylines and what makes this game interesting
2. 2-3 star players to watch from each team (name specific players and their positions)
3. Recent performance trends or notable stats for the key players
4. One tactical matchup or factor that could decide the game

Keep it engaging, informative, and focused on actionable insights for someone considering a bet or trade on this game. Use specific player names and recent stats when possible."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                logger.warning(f"Empty response from Gemini for {away_team} vs {home_team}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating game summary: {e}")
            return None
