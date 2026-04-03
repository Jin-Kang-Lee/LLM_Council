"""
Governance & Compliance Agent
Specializes in analyzing governance, legal, and regulatory risks.
"""

from .base_agent import BaseAgent
from tools.finance_tools import INSIDER_TRADING_TOOL_DEFINITION


class GovernanceAgent(BaseAgent):
    """Agent focused on governance, compliance, and legal risk analysis."""

    def __init__(self):
        super().__init__(
            name="Governance Analyst",
            color="purple",
            tools=[INSIDER_TRADING_TOOL_DEFINITION],
        )

    @property
    def domain_scope(self) -> str:
        return (
            "board structure, executive compensation, audit quality, legal proceedings, "
            "regulatory compliance, related-party transactions, insider trading, "
            "disclosure gaps, accounting policy changes"
        )

    @property
    def system_prompt(self) -> str:
        return """You are the "Governance & Compliance Analyst".
Your mission is to identify governance, legal, and compliance risks that affect creditworthiness.
Tone: Audit-friendly, objective, and highly risk-averse."""

    @property
    def analysis_rules(self) -> str:
        return """OUTPUT RULES:
1. Output MUST be a single valid JSON object. No markdown, no commentary, no code fences.
2. Use ONLY information from the grounded conclusions provided — do NOT invent or guess.
3. If something is not disclosed, write "Not disclosed" — do not leave fields empty.
4. You MUST use exactly these field names — do not rename or add fields.

FILL IN THIS EXACT JSON TEMPLATE:
{
  "governance_risk_level": "<Low|Medium|High>",
  "compliance_risk_level": "<Low|Medium|High>",
  "key_findings": [
    {
      "issue": "<description of the risk or finding>",
      "category": "<Governance|Legal|Compliance|Accounting>",
      "severity": "<Low|Medium|High>",
      "evidence": "<specific quote or figure from the report>",
      "impact": "<why this affects creditworthiness>"
    }
  ],
  "non_disclosures": ["<expected item not found in report>"],
  "confidence_score": <0.0-1.0>,
  "limitations": "<short summary of data gaps>"
}"""

    @property
    def json_schema(self) -> dict:
        return {
            "governance_risk_level": str,
            "compliance_risk_level": str,
            "key_findings": [
                {
                    "issue": str,
                    "category": str,
                    "severity": str,
                    "evidence": str,
                    "impact": str,
                }
            ],
            "non_disclosures": [str],
            "confidence_score": (int, float),
            "limitations": str,
        }

    @property
    def discussion_persona(self) -> str:
        return """WAR ROOM MODE — You are the auditor in the room.

Your voice: dry, exact, pedantic — deliberately so. You separate "risk" from "disclosure gap" from "regulatory breach".
You care about what wasn't in the report as much as what was. You don't speculate."""

    def respond_to(self, other_agent_name: str, other_response: str) -> str:
        return (
            f"[{other_agent_name}] just said:\n---\n{other_response[:1200]}\n---\n\n"
            "YOUR TURN as the Governance Analyst — mandatory rules:\n"
            "1. Stay in your lane: disclosure gaps, regulatory compliance, board structure, "
            "audit quality, related-party transactions, legal proceedings. "
            "Do NOT drift into financial risk or operational metrics.\n"
            "2. Identify ONE specific governance or compliance angle the thread has ignored or got wrong. Quote it.\n"
            "3. Cite a specific disclosure gap or regulatory requirement FROM THE REPORT (not invented).\n"
            "4. Add ONE governance angle not yet raised.\n"
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
Focus exclusively on governance, compliance, legal risks, and accounting quality.
Ground all findings in evidence from the report. If something is not disclosed, say so explicitly.
"""
        return await self.generate_staged(
            earnings_content,
            additional_instructions,
            expect_json=True,
        )
