import os
from openai import OpenAI
from typing import Dict, Optional

# Using OpenAI blueprint for python_openai integration
# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user

class OpenAIService:
    """Service for generating AI-powered market insights using OpenAI."""
    
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
    
    def generate_market_brief(self, market_data: Dict) -> str:
        """
        Generate an AI-powered market brief for a Kalshi NFL market.
        
        Args:
            market_data: Dictionary containing market information
            
        Returns:
            AI-generated market brief as a string
        """
        ticker = market_data.get("ticker", "Unknown")
        title = market_data.get("title", "Unknown Market")
        subtitle = market_data.get("subtitle", "")
        yes_bid = market_data.get("yes_bid", 0)
        no_bid = market_data.get("no_bid", 0)
        volume = market_data.get("volume", 0)
        open_interest = market_data.get("open_interest", 0)
        close_time = market_data.get("close_time", "Unknown")
        
        prompt = f"""You are a sports betting market analyst. Analyze this NFL prediction market from Kalshi and provide a concise, insightful brief.

Market: {title}
{subtitle if subtitle else ''}

Current Market Data:
- Yes Bid: {yes_bid}¢ (implies {yes_bid}% probability)
- No Bid: {no_bid}¢ (implies {100 - yes_bid}% probability)
- Trading Volume: ${volume}
- Open Interest: {open_interest} contracts
- Market Closes: {close_time}

Provide a brief analysis (3-4 sentences) covering:
1. What this market is asking and its current implied probability
2. Key factors that could influence the outcome
3. Any notable aspects of the current pricing or trading activity

Keep it concise, informative, and focused on actionable insights for traders."""

        try:
            # Using gpt-5 model - a reasoning model that uses hidden reasoning tokens
            # Need higher max_completion_tokens since reasoning consumes tokens too
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert sports betting analyst specializing in NFL prediction markets. Provide clear, concise analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=5000,  # Increased from 500 to account for reasoning tokens
                reasoning_effort="low"  # Use low effort for simple analysis tasks
            )
            
            # Debug logging for response analysis
            choice = response.choices[0]
            print(f"[DEBUG] OpenAI Response Details:")
            print(f"  - finish_reason: {choice.finish_reason}")
            print(f"  - content: {choice.message.content}")
            print(f"  - refusal: {getattr(choice.message, 'refusal', None)}")
            print(f"  - usage: {response.usage}")
            
            # Check for refusal
            if hasattr(choice.message, 'refusal') and choice.message.refusal:
                return f"Unable to generate market brief: Model refused - {choice.message.refusal}"
            
            # Check finish reason
            if choice.finish_reason == "length":
                return "Unable to generate market brief: Response was cut off (token limit). Try viewing a different market."
            
            # Get content
            content = choice.message.content
            
            if content:
                return content
            else:
                # Provide detailed debugging info if content is empty
                debug_info = f"finish_reason={choice.finish_reason}, has_refusal={hasattr(choice.message, 'refusal')}"
                return f"Unable to generate market brief: No content returned ({debug_info})"
        
        except Exception as e:
            print(f"[ERROR] OpenAI API Exception: {type(e).__name__}: {str(e)}")
            return f"Unable to generate market brief: {type(e).__name__}: {str(e)}"
    
    def generate_quick_insight(self, title: str, probability: float, volume: int) -> str:
        """
        Generate a quick one-liner insight about a market.
        
        Args:
            title: Market title
            probability: Current probability (0-1)
            volume: Trading volume
            
        Returns:
            Quick insight string
        """
        try:
            prompt = f"""Give a single sentence insight about this NFL betting market:
Market: {title}
Current Probability: {probability*100:.1f}%
Volume: ${volume}

Provide ONE concise sentence highlighting what's interesting about this market."""

            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=100
            )
            
            content = response.choices[0].message.content
            return content if content else f"Market trading at {probability*100:.1f}% probability with ${volume} volume"
        
        except Exception as e:
            return f"Market trading at {probability*100:.1f}% probability with ${volume} volume"
