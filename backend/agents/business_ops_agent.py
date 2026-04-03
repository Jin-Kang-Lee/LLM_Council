"""
Business, Industry and Operational Risk Agent - Phase 2
Specializes in analyzing business model risks, operational vulnerabilities, and CapEx trends.
"""

from .base_agent import BaseAgent


class BusinessOpsRiskAgent(BaseAgent):
    """Agent focused on business, industry, and operational risk analysis."""
    
    def __init__(self):
        super().__init__(
            name="Business & Ops Analyst",
            color="yellow"
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the "Business, Industry and Operational Risk Analyst".
Your mission is to identify business model vulnerabilities, operational risks, and industry-level threats from earnings reports.
Tone: Analytical, thorough, and risk-aware."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use information found in the earnings report and any provided REFERENCE CONTEXT. Do not use outside knowledge.
2. DO NOT hallucinate or guess. If information is missing, say "Not Found" and list it under non_disclosures.
3. Evidence must include a short direct quote. If REFERENCE CONTEXT is provided, the quote MUST be verbatim from that context and include a [C#] chunk citation.
4. Output MUST be a single, valid JSON object. No markdown, no commentary.
5. Pay special attention to the Cash Flow Statement to locate Capital Expenditure (CapEx) figures.

OUTPUT JSON SCHEMA:
{
  "operational_risk_rating": "Low/Medium/High/Critical",
  "industry_position": "Description of competitive stance and market position",
  "capex_analysis": {
    "capex_trend": "Increasing/Stable/Decreasing/Not Found",
    "risk_assessment": "Assessment of whether CapEx level poses a risk to cash flow or signals necessary investment",
    "evidence": "Supporting data or quote from the report"
  },
  "key_business_risks": [
    {
      "risk_type": "e.g. Customer Concentration / Pricing Power / Scalability / Single Point of Failure / Business Continuity",
      "description": "Description of the risk",
      "severity": "Low/Medium/High",
      "evidence": "Quote or supporting data from report"
    }
  ],
  "watchlist": ["Items requiring monitoring"],
  "non_disclosures": ["Expected items not found in report"],
  "confidence_score": 0.0,
  "limitations": "Short summary of data gaps"
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
        Perform business, industry, and operational risk analysis on earnings content.
        
        Args:
            earnings_content: Parsed earnings report content
        
        Returns:
            Detailed business and operational risk analysis in JSON format
        """
        additional_instructions = """
Analyze the provided earnings report content. Focus on business model risks,
operational vulnerabilities, and industry-level threats.

Specifically:
1. Locate the Cash Flow Statement data and extract Capital Expenditure (CapEx) figures.
   Assess whether the CapEx level is sustainable, poses a risk to working capital,
   or represents necessary growth/maintenance investment.
2. Evaluate customer concentration risk - is revenue overly dependent on few customers?
3. Assess pricing power - can the company maintain or increase margins?
4. Identify single points of failure in operations or supply chain.
5. Evaluate business continuity risks and scalability constraints.

Be thorough but concise. If specific CapEx data is not found, note it explicitly.
List any missing expected disclosures in non_disclosures and summarize data gaps in limitations.
"""
        return await self.generate(
            earnings_content,
            additional_instructions,
            expect_json=True,
            reference_context=reference_context,
            reference_query=reference_query,
            allow_targeted_retrieval=allow_targeted_retrieval,
        )
