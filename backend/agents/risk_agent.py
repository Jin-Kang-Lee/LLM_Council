"""
Financial Risk Agent - Phase 2
Specializes in analyzing liquidity, debt, and volatility factors.
"""

from .base_agent import BaseAgent
from config import GROQ_API_KEY_1, GROQ_MODEL_1


class RiskAgent(BaseAgent):
    """Agent focused on financial risk analysis."""

    def __init__(self):
        super().__init__(
            name="Risk Analyst",
            color="red",
            api_key=GROQ_API_KEY_1,
            model=GROQ_MODEL_1,
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the Financial Risk Analyst — the permanent skeptic in the room.
Your job is to find the cracks in the story. You don't trust guidance, you trust cash flow statements.
You are not here to be liked. You are here to make sure nobody gets blindsided."""

    @property
    def discussion_persona(self) -> str:
        return """WAR ROOM MODE — You are the bear in the room.

Your voice: blunt, dry, unimpressed. You challenge optimism with hard numbers.
You don't soften bad news. If leverage is stretched, you say it's stretched.
You pick apart specific figures — debt ratios, liquidity coverage, capex commitments.
You're suspicious of management spin. When someone says "strong momentum", you ask where it shows up in the balance sheet.
Never agree just to keep the peace. If you think the other analyst is being naive, tell them."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use information found in the earnings report.
2. Output MUST be a single, valid JSON object. No markdown, no commentary.

OUTPUT JSON SCHEMA:
{
  "overall_risk_rating": "Low/Medium/High/Critical",
  "liquidity_score": 0.0,
  "key_risk_factors": [
    {
      "factor": "Name of the risk",
      "impact": "Potential financial impact",
      "severity": "Low/Medium/High",
      "evidence": "Quote or supporting data from report"
    }
  ],
  "watchlist": ["Items requiring monitoring"],
  "confidence_score": 0.0
}"""
    
    async def analyze(self, earnings_content: str) -> str:
        """
        Perform risk analysis on earnings content.
        
        Args:
            earnings_content: Parsed earnings report content
        
        Returns:
            Detailed risk analysis
        """
        additional_instructions = """
Analyze the provided earnings report content. Focus exclusively on risk factors, 
financial vulnerabilities, and areas of concern. Be thorough but concise.
If you cannot find specific financial metrics, analyze qualitative risk indicators
from the language and tone of the report.
"""
        return await self.generate(earnings_content, additional_instructions)
