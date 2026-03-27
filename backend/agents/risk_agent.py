"""
Financial Risk Agent - Phase 2
Specializes in analyzing liquidity, debt, and volatility factors.
Now enhanced with tool calling to fetch real-time financial data.
"""

from .base_agent import BaseAgent
from tools.finance_tools import TOOL_DEFINITIONS
from config import GROQ_API_KEY_1, GROQ_MODEL_1


class RiskAgent(BaseAgent):
    """Agent focused on financial risk analysis with tool-calling capability."""
    
    def __init__(self):
        super().__init__(
            name="Risk Analyst",
            color="red",
            groq_api_key=GROQ_API_KEY_1,
            groq_model=GROQ_MODEL_1,
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the "Financial Risk Analyst".
Your mission is to identify financial, operational, and market risks from earnings reports.
Tone: Skeptical, analytical, and data-driven.

IMPORTANT — TOOL USAGE:
You have access to a tool called `get_company_financials` that fetches real-time 
financial data for any publicly traded company. You MUST use this tool:
1. First, identify the company's stock ticker symbol from the earnings report text.
2. Call `get_company_financials` with that ticker to retrieve actual market data.
3. Use the retrieved data to VALIDATE or CHALLENGE claims made in the earnings report.
4. If a claim in the report contradicts the real data, flag it explicitly.

If you cannot determine the ticker, explain why and proceed with text-only analysis."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use information found in the earnings report AND data retrieved via tools.
2. Cite evidence by providing a direct, short quote from the text. DO NOT use [C#] or bracketed citations.
3. Output MUST be a single, valid JSON object. No markdown, no commentary.
4. When tool data is available, include a "tool_data_used" field in your output.

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
  "market_data_validation": {
    "ticker_used": "The ticker symbol queried",
    "claims_validated": [
      {
        "claim": "What management said",
        "actual_data": "What the real data shows",
        "verdict": "Confirmed/Contradicted/Inconclusive"
      }
    ]
  },
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
    def tool_definitions(self) -> list[dict]:
        """Expose the finance tools to Ollama for tool calling."""
        return TOOL_DEFINITIONS

    @property
    def require_citations(self) -> bool:
        return True
    
    async def analyze(self, earnings_content: str) -> str:
        """
        Perform risk analysis on earnings content using tool calling.
        
        The agent will:
        1. Read the earnings report
        2. Identify the company's ticker
        3. Call get_company_financials to fetch real-time data
        4. Produce a risk analysis that cross-references both sources
        
        Args:
            earnings_content: Parsed earnings report content
        
        Returns:
            Detailed risk analysis in JSON format
        """
        additional_instructions = """
Analyze the provided earnings report content. Follow these steps:

STEP 1: Identify the company being discussed. Determine its stock ticker symbol.
STEP 2: Call the `get_company_financials` tool with that ticker to fetch real-time
         financial metrics (debt, cash, ratios, margins, etc.).
STEP 3: Compare the tool's data against claims made in the earnings report.
         CRITICAL RULE — THE "actual_data" FIELD MUST ONLY CONTAIN VALUES
         THAT APPEAR VERBATIM IN THE TOOL'S JSON RESPONSE.
         - DO NOT invent, estimate, or recall numbers from your training data.
         - DO NOT write dollar values that were not explicitly returned by the tool.
         - If the tool did not return a specific metric needed for a claim, write
           "actual_data": "Not available in tool data" and set verdict to "Inconclusive".
         - Only use field values like current_ratio, total_debt, debt_to_equity,
           free_cashflow, etc. that the tool actually returned.
STEP 4: Produce your final risk analysis as a JSON object following the schema.

Focus exclusively on risk factors, financial vulnerabilities, and areas of concern.
Be thorough but concise. If you cannot find specific financial metrics, analyze
qualitative risk indicators from the language and tone of the report.
"""
        return await self.generate_with_tools(
            earnings_content, additional_instructions, expect_json=True
        )
