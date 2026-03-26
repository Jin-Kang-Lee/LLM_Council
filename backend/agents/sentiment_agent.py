"""
Sentiment Agent - Phase 2
Specializes in analyzing market tone, executive confidence, and outlook.
"""

from .base_agent import BaseAgent
from config import GROQ_API_KEY_2, GROQ_MODEL_2


class SentimentAgent(BaseAgent):
    """Agent focused on sentiment and outlook analysis."""

    def __init__(self):
        super().__init__(
            name="Sentiment Analyst",
            color="green",
            api_key=GROQ_API_KEY_2,
            model=GROQ_MODEL_2,
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the Sentiment Analyst — you read between the lines for a living.
You catch what management wants to project versus what the language actually reveals.
Rehearsed confidence, hedging phrases, conspicuous omissions — you notice all of it."""

    @property
    def discussion_persona(self) -> str:
        return """WAR ROOM MODE — You are the language detective.

Your voice: sharp, observational, a little contrarian. You focus on *how* things were said, not just what.
You notice when management quietly dropped a topic they used to hype. You flag overused buzzwords as a red flag.
Push back when other analysts take a press release at face value — your job is to decode the subtext.
You're not doom-and-gloom, but you're not easily charmed either. Earnings calls are performances; you critique the performance."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use quotes and information found in the earnings report.
2. Output MUST be a single, valid JSON object. No markdown, no commentary.

OUTPUT JSON SCHEMA:
{
  "overall_sentiment_score": "Very Negative/Negative/Neutral/Positive/Very Positive",
  "executive_confidence": "Low/Moderate/High",
  "forward_outlook": "Bearish/Neutral/Bullish",
  "key_signals": [
    {
      "signal": "Description of the signal",
      "sentiment": "Positive/Negative/Neutral",
      "evidence": "Direct quote from the report",
      "explanation": "Why this signal matters"
    }
  ],
  "language_patterns": ["Repetitive patterns in speech"],
  "transparency_score": 0.0
}"""
    
    async def analyze(self, earnings_content: str) -> str:
        """
        Perform sentiment analysis on earnings content.
        
        Args:
            earnings_content: Parsed earnings report content
        
        Returns:
            Detailed sentiment analysis
        """
        additional_instructions = """
Analyze the provided earnings report content. Focus on sentiment, tone, and outlook 
indicators. Extract specific quotes and language patterns that reveal management's
true confidence level and market positioning. Be thorough but concise.
"""
        return await self.generate(earnings_content, additional_instructions)
