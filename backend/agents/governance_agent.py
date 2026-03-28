"""
Governance & Compliance Agent
Specializes in analyzing governance, legal, and regulatory risks.
Now enhanced with tool calling to fetch insider trading data.
"""

from .base_agent import BaseAgent
from tools.finance_tools import INSIDER_TRADING_TOOL_DEFINITION
from config import GROQ_API_KEY_3, GROQ_MODEL_3


class GovernanceAgent(BaseAgent):
    """Agent focused on governance, compliance, and legal risk analysis
    with insider-trading tool-calling capability."""
    
    def __init__(self):
        super().__init__(
            name="Governance Analyst",
            color="purple",
            groq_api_key=GROQ_API_KEY_3,
            groq_model=GROQ_MODEL_3,
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the "Governance & Compliance Analyst". 
Your mission is to identify governance, legal, and compliance risks that affect creditworthiness.
Tone: Audit-friendly, objective, and highly risk-averse.

IMPORTANT — TOOL USAGE:
You have access to a tool called `get_insider_trading` that fetches recent SEC Form 4
insider trading data for any publicly traded company. You MUST use this tool:
1. First, identify the company's stock ticker symbol from the earnings report text.
2. Call `get_insider_trading` with that ticker to retrieve recent insider buy/sell activity.
3. Compare insider behaviour against management's stated outlook:
   - If management is very optimistic but executives are SELLING, flag this as a major red flag.
   - If management is cautious but executives are BUYING, note this as a positive signal.
4. If you cannot determine the ticker, explain why and proceed with text-only analysis."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use information found in the earnings report AND data retrieved via tools.
2. If evidence for a category is missing, explicitly list it in 'non_disclosures'.
3. DO NOT hallucinate or guess. 
4. Cite evidence by providing a direct, short quote from the text. DO NOT use [C#] or bracketed citations.
5. Output MUST be a single, valid JSON object. No markdown, no commentary.
6. When tool data is available, include an "insider_trading_check" field in your output.

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
  "insider_trading_check": {
    "ticker_used": "The ticker symbol queried",
    "total_recent_buys": 0,
    "total_recent_sells": 0,
    "net_insider_sentiment": "Bullish/Bearish/Neutral",
    "alignment_with_management_tone": "Aligned/Contradictory/Inconclusive",
    "red_flags": ["List of specific concerns, e.g. CEO sold $10M before earnings call"]
  },
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
    def tool_definitions(self) -> list[dict]:
        """Expose the insider trading tool to Ollama for tool calling."""
        return [INSIDER_TRADING_TOOL_DEFINITION]

    @property
    def require_citations(self) -> bool:
        return True
    
    async def analyze(self, earnings_content: str) -> str:
        """
        Perform governance and compliance analysis on earnings content
        using tool calling to fetch insider trading data.
        
        The agent will:
        1. Read the earnings report
        2. Identify the company's ticker
        3. Call get_insider_trading to fetch recent insider activity
        4. Produce a governance analysis that cross-references both sources
        
        Args:
            earnings_content: Parsed earnings report content
        
        Returns:
            Detailed governance analysis in JSON format
        """
        additional_instructions = """
Analyze the provided earnings report content. Follow these steps:

STEP 1: Identify the stock ticker from the report header and use it EXACTLY. 
         (Example: If header says 'NovaTech (NVTC)', the ticker is 'NVTC'. 
          DO NOT use 'NovaTech' or 'NOVS').
STEP 2: Call the `get_insider_trading` tool with that ticker to fetch recent
         insider buy/sell transactions by executives and board members.
STEP 3: Compare insider trading behaviour against management's stated outlook.
         If executives are aggressively selling while the report paints a rosy picture,
         flag this as a MAJOR governance red flag.
STEP 4: Produce your final governance analysis as a JSON object following the schema.

Focus exclusively on governance, compliance, legal risks, and accounting quality.
Ground all findings in evidence.
REMEMBER: Output MUST be STRICT JSON only.
"""
        return await self.generate_with_tools(
            earnings_content, additional_instructions, expect_json=True
        )
