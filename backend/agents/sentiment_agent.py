"""
Sentiment Agent - Phase 2
Specializes in analyzing market tone, executive confidence, and outlook.
"""

from .base_agent import BaseAgent


class SentimentAgent(BaseAgent):
    """Agent focused on sentiment and outlook analysis."""
    
    def __init__(self):
        super().__init__(
            name="Sentiment Analyst",
            color="green"
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the "Sentiment Analyst".
Your mission is to analyze executive tone, market positioning, and guidance outlook.
Tone: Bullish but critical, sensitive to nuances in language."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use quotes and information found in the earnings report.
2. Cite evidence with chunk IDs from reference context using [C#] format.
3. Output MUST be a single, valid JSON object. No markdown, no commentary.

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

    @property
    def json_schema(self) -> dict:
        return {
            "overall_sentiment_score": str,
            "executive_confidence": str,
            "forward_outlook": str,
            "key_signals": [
                {
                    "signal": str,
                    "sentiment": str,
                    "evidence": str,
                    "explanation": str,
                }
            ],
            "language_patterns": [str],
            "transparency_score": (int, float),
        }

    @property
    def require_citations(self) -> bool:
        return True
    
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
        return await self.generate(earnings_content, additional_instructions, expect_json=True)
