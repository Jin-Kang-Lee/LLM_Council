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
            color="purple"
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the "Governance & Compliance Analyst". 
Your mission is to identify governance, legal, and compliance risks that affect creditworthiness.
Tone: Audit-friendly, objective, and highly risk-averse."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use information found in the earnings report. 
2. If evidence for a category is missing, explicitly list it in 'non_disclosures'.
3. DO NOT hallucinate or guess. 
4. Cite evidence by providing a direct, short quote from the text. DO NOT use [C#] or bracketed citations.
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
    
    async def analyze(self, earnings_content: str) -> str:
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
        return await self.generate(earnings_content, additional_instructions, expect_json=True)
