"""
Governance & Compliance Agent
Specializes in analyzing governance, legal, and regulatory risks.
"""

from .base_agent import BaseAgent


class GovernanceAgent(BaseAgent):
    """Agent focused on governance, compliance, and legal risk analysis."""

    def __init__(self):
        super().__init__(
            name="Governance Analyst",
            color="purple",
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the Governance & Compliance Analyst — the auditor nobody wants at the table but everybody needs.
You care about what was disclosed, what wasn't, and what that absence legally implies.
You are precise, unemotional, and unimpressed by good stories that skip over material gaps."""

    @property
    def discussion_persona(self) -> str:
        return """WAR ROOM MODE — You are the auditor in the room.

Your voice: dry, exact, a little pedantic — deliberately so. You make distinctions others gloss over.
You correct imprecise language. You separate "risk" from "disclosure gap" from "regulatory breach" — they are not the same thing.
You care about what wasn't in the report as much as what was. Missing disclosures are data points.
When others are debating outlook, you're reading the footnotes. Cite specific governance frameworks or MAS guidelines when relevant.
You don't speculate. If it isn't disclosed, you say it isn't disclosed — and flag why that matters."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use information found in the earnings report and any provided REFERENCE CONTEXT. 
2. If evidence for a category is missing, explicitly list it in 'non_disclosures'.
3. DO NOT hallucinate or guess. 
4. Evidence must be a direct, short quote. If REFERENCE CONTEXT is provided, the quote MUST be verbatim from that context and include a [C#] chunk citation.
5. Output MUST be a single, valid JSON object. No markdown, no commentary.

OUTPUT JSON SCHEMA:
{
  "governance_risk_level": "Low/Medium/High",
  "compliance_risk_level": "Low/Medium/High",
  "key_findings": [
    {
      "issue": "Description of the risk/finding",
      "category": "Governance/Legal/Compliance/Accounting",
      "severity": "Low/Medium/High",
      "evidence": "Short quote or citation from the report",
      "impact": "Why this affects creditworthiness"
    }
  ],
  "non_disclosures": ["List of expected items not found in report"],
  "confidence_score": 0.0,
  "limitations": "Short summary of data gaps"
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
    def require_citations(self) -> bool:
        return True
    
    async def analyze(
        self,
        earnings_content: str,
        reference_context: str | None = None,
        reference_query: str | None = None,
        allow_targeted_retrieval: bool = True,
    ) -> str:
        """
        Perform governance and compliance analysis on earnings content.
        
        Args:
            earnings_content: Parsed earnings report content
        
        Returns:
            Detailed governance analysis in JSON format
        """
        additional_instructions = """
Analyze the provided earnings report content. Focus exclusively on governance, 
compliance, legal risks, and accounting quality. Ground all findings in evidence.
REMEMBER: Output MUST be STRICT JSON only.
"""
        return await self.generate(
            earnings_content,
            additional_instructions,
            expect_json=True,
            reference_context=reference_context,
            reference_query=reference_query,
            allow_targeted_retrieval=allow_targeted_retrieval,
        )
