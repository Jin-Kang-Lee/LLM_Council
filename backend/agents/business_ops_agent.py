"""
Business, Industry and Operational Risk Agent - Phase 2
Specializes in analyzing business model risks, operational vulnerabilities, and CapEx trends.
"""

from .base_agent import BaseAgent
from tools.finance_tools import COMPETITOR_BENCHMARKING_TOOL_DEFINITION


class BusinessOpsRiskAgent(BaseAgent):
    """Agent focused on business, industry, and operational risk analysis."""

    def __init__(self):
        super().__init__(
            name="Business & Ops Analyst",
            color="yellow",
            tools=[COMPETITOR_BENCHMARKING_TOOL_DEFINITION],
        )

    @property
    def domain_scope(self) -> str:
        return (
            "CapEx, operational margins, customer concentration, supply chain, "
            "pricing power, scalability, market position, competitive dynamics, "
            "industry headwinds, business model risks"
        )

    @property
    def system_prompt(self) -> str:
        return """You are the "Business, Industry and Operational Risk Analyst".
Your mission is to identify business model vulnerabilities, operational risks, and industry-level threats from earnings reports.
Tone: Analytical, thorough, and risk-aware."""

    @property
    def analysis_rules(self) -> str:
        return """OUTPUT RULES:
1. Output MUST be a single valid JSON object. No markdown, no commentary, no code fences.
2. Use ONLY information from the grounded conclusions provided — do NOT invent figures.
3. If data is missing, write "Not Found" in the relevant field.
4. You MUST use exactly these field names — do not rename or add fields.

FILL IN THIS EXACT JSON TEMPLATE:
{
  "operational_risk_rating": "<Low|Medium|High|Critical>",
  "industry_position": "<description of competitive stance and market position>",
  "capex_analysis": {
    "capex_trend": "<Increasing|Stable|Decreasing|Not Found>",
    "risk_assessment": "<whether CapEx poses a risk to cash flow or signals necessary investment>",
    "evidence": "<specific figure or quote from the report>"
  },
  "key_business_risks": [
    {
      "risk_type": "<e.g. Customer Concentration|Pricing Power|Scalability|Single Point of Failure>",
      "description": "<description of the risk>",
      "severity": "<Low|Medium|High>",
      "evidence": "<specific quote or figure from the report>"
    }
  ],
  "watchlist": ["<item requiring monitoring>"],
  "non_disclosures": ["<expected item not found in report>"],
  "confidence_score": <0.0-1.0>,
  "limitations": "<short summary of data gaps>"
}"""

    @property
    def json_schema(self) -> dict:
        return {
            "operational_risk_rating": str,
            "industry_position": str,
            "capex_analysis": {
                "capex_trend": str,
                "risk_assessment": str,
                "evidence": str,
            },
            "key_business_risks": [
                {
                    "risk_type": str,
                    "description": str,
                    "severity": str,
                    "evidence": str,
                }
            ],
            "watchlist": [str],
            "non_disclosures": [str],
            "confidence_score": (int, float),
            "limitations": str,
        }

    @property
    def discussion_persona(self) -> str:
        return """WAR ROOM MODE — You are the operator in the room.

Your voice: direct, pragmatic, commercially grounded. You see the business behind the numbers.
You challenge both doom-sayers and optimists with operational reality.
Never agree just to keep the peace."""

    def respond_to(self, other_agent_name: str, other_response: str) -> str:
        return (
            f"[{other_agent_name}] just said:\n---\n{other_response[:1200]}\n---\n\n"
            "YOUR TURN as the Business & Ops Analyst — mandatory rules:\n"
            "1. Stay in your lane: CapEx, operational margins, customer concentration, "
            "supply chain, scalability, pricing power. Do NOT drift into pure financial risk or governance.\n"
            "2. Identify ONE specific operational claim above you DISAGREE with or think is incomplete. Quote it.\n"
            "3. Back your challenge with a specific operational metric FROM THE REPORT (not invented).\n"
            "4. Add ONE operational angle not yet raised in the thread.\n"
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
Focus on business model risks, operational vulnerabilities, and industry-level threats.
Pay special attention to CapEx figures, customer concentration, pricing power, and supply chain risks.
If specific data is not found in the report, note it explicitly — do not invent figures.
"""
        return await self.generate_staged(
            earnings_content,
            additional_instructions,
            expect_json=True,
        )
