"""
Financial Risk Agent - Phase 2
Specializes in analyzing liquidity, debt, and volatility factors.
"""

from .base_agent import BaseAgent


class RiskAgent(BaseAgent):
    """Agent focused on financial risk analysis."""
    
    def __init__(self):
        super().__init__(
            name="Risk Analyst",
            color="red"
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the "Financial Risk Analyst".
Your mission is to identify financial, operational, and market risks from earnings reports.
Tone: Skeptical, analytical, and data-driven."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use information found in the earnings report.
2. Cite evidence with chunk IDs from reference context using [C#] format.
3. Output MUST be a single, valid JSON object. No markdown, no commentary.

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

    @property
    def json_schema(self) -> dict:
        return {
            "overall_risk_rating": str,
            "liquidity_score": (int, float),
            "key_risk_factors": [
                {
                    "factor": str,
                    "impact": str,
                    "severity": str,
                    "evidence": str,
                }
            ],
            "watchlist": [str],
            "confidence_score": (int, float),
        }

    @property
    def require_citations(self) -> bool:
        return True
    
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
        return await self.generate(earnings_content, additional_instructions, expect_json=True)
