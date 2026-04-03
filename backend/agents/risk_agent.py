"""
Financial Risk Agent - Phase 2
Specializes in analyzing liquidity, debt, and volatility factors.
"""

from .base_agent import BaseAgent
from tools.finance_tools import FINANCE_TOOL_DEFINITION


class RiskAgent(BaseAgent):
    """Agent focused on financial risk analysis."""

    def __init__(self):
        super().__init__(
            name="Risk Analyst",
            color="red",
            tools=[FINANCE_TOOL_DEFINITION],
        )

    @property
    def domain_scope(self) -> str:
        return (
            "liquidity, debt levels, leverage ratios, cash flow, interest coverage, "
            "credit risk, capital structure, financial covenants, net debt"
        )

    @property
    def system_prompt(self) -> str:
        return """You are the "Financial Risk Analyst".
Your mission is to identify financial, operational, and market risks from earnings reports.
Tone: Skeptical, analytical, and data-driven."""

    @property
    def analysis_rules(self) -> str:
        return """OUTPUT RULES:
1. Output MUST be a single valid JSON object. No markdown, no commentary, no code fences.
2. Use ONLY information from the grounded conclusions provided — do NOT invent figures.
3. You MUST use exactly these field names — do not rename or add fields.

FILL IN THIS EXACT JSON TEMPLATE:
{
  "overall_risk_rating": "<Low|Medium|High|Critical>",
  "liquidity_score": <0.0-1.0>,
  "key_risk_factors": [
    {
      "factor": "<name of the risk>",
      "impact": "<potential financial impact>",
      "severity": "<Low|Medium|High>",
      "evidence": "<specific quote or figure from the report>"
    }
  ],
  "watchlist": ["<item requiring monitoring>"],
  "confidence_score": <0.0-1.0>
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
    def discussion_persona(self) -> str:
        return """WAR ROOM MODE — You are the bear in the room.

Your voice: blunt, dry, unimpressed. You challenge optimism with hard numbers.
You pick apart specific figures — debt ratios, liquidity coverage, capex commitments.
You're suspicious of management spin. Never agree just to keep the peace."""

    def respond_to(self, other_agent_name: str, other_response: str) -> str:
        return (
            f"[{other_agent_name}] just said:\n---\n{other_response[:1200]}\n---\n\n"
            "YOUR TURN as the Risk Analyst — mandatory rules:\n"
            "1. Stay in your lane: liquidity, leverage, cash flow, debt ratios, credit risk. "
            "Do NOT drift into governance or compliance — that is not your job.\n"
            "2. Identify ONE specific financial claim above you DISAGREE with or think is incomplete. Quote it.\n"
            "3. Back your challenge with a specific number or ratio FROM THE REPORT (not invented).\n"
            "4. Add ONE financial risk angle not yet raised in the thread.\n"
            "5. Do NOT repeat points already made. 3-5 sentences max per point."
        )

    async def analyze(
        self,
        earnings_content: str,
        reference_context: str | None = None,
        reference_query: str | None = None,
        allow_targeted_retrieval: bool = True,
    ) -> str:
        additional_instructions = """
Focus exclusively on risk factors, financial vulnerabilities, and areas of concern.
If a metric is missing from the report, note it explicitly — do not invent figures.
"""
        return await self.generate_staged(
            earnings_content,
            additional_instructions,
            expect_json=True,
        )
