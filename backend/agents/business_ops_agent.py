"""
Business, Industry and Operational Risk Agent - Phase 2
Specializes in analyzing business model risks, operational vulnerabilities,
and CapEx trends. Now enhanced with tool calling for competitor benchmarking.
"""

from .base_agent import BaseAgent
from tools.finance_tools import COMPETITOR_BENCHMARKING_TOOL_DEFINITION
from config import GROQ_API_KEY_3, GROQ_MODEL_3


class BusinessOpsRiskAgent(BaseAgent):
    """Agent focused on business, industry, and operational risk analysis
    with competitor benchmarking tool-calling capability."""
    
    def __init__(self):
        super().__init__(
            name="Business & Ops Analyst",
            color="yellow",
            groq_api_key=GROQ_API_KEY_3,
            groq_model=GROQ_MODEL_3,
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the "Business, Industry and Operational Risk Analyst".
Your mission is to identify business model vulnerabilities, operational risks, and industry-level threats from earnings reports.
Tone: Analytical, thorough, and risk-aware.

IMPORTANT — TOOL USAGE:
You have access to a tool called `get_competitor_benchmarking` that compares a
company's financial performance against its industry rivals. You MUST use this tool:
1. First, identify the company's stock ticker symbol from the earnings report text.
2. Identify 2-3 of its biggest publicly-traded competitors in the same industry.
3. Call `get_competitor_benchmarking` with the primary ticker and `competitor_tickers`.
4. Use the comparison data to assess whether the company is GAINING or LOSING
   market share relative to its peers. If management claims strong growth but
   competitors are growing faster, flag this as a concern.
5. If you cannot determine the ticker or competitors, explain why and proceed
   with text-only analysis."""

    @property
    def analysis_rules(self) -> str:
        return """1. ONLY use information found in the earnings report AND data retrieved via tools.
2. Cite evidence by providing a direct, short quote from the text. DO NOT use [C#] or bracketed citations.
3. Output MUST be a single, valid JSON object. No markdown, no commentary.
4. Pay special attention to the Cash Flow Statement to locate Capital Expenditure (CapEx) figures.
5. When tool data is available, include a "competitor_benchmarking" field in your output.

OUTPUT JSON SCHEMA:
{
  "operational_risk_rating": "Low/Medium/High/Critical",
  "industry_position": "Description of competitive stance and market position",
  "capex_analysis": {
    "capex_trend": "Increasing/Stable/Decreasing/Not Found",
    "risk_assessment": "Assessment of whether CapEx level poses a risk",
    "evidence": "Supporting data or quote from the report"
  },
  "competitor_benchmarking": {
    "primary_ticker": "The ticker queried",
    "competitors_compared": ["List of competitor tickers"],
    "market_share_verdict": "Gaining/Losing/Stable",
    "key_comparisons": [
      {
        "metric": "e.g. Revenue Growth",
        "company_value": "value",
        "best_competitor_value": "value",
        "assessment": "Better/Worse/Comparable"
      }
    ]
  },
  "key_business_risks": [
    {
      "risk_type": "e.g. Customer Concentration / Pricing Power / Scalability",
      "description": "Description of the risk",
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
            "confidence_score": (int, float),
        }

    @property
    def tool_definitions(self) -> list[dict]:
        """Expose the competitor benchmarking tool to Ollama for tool calling."""
        return [COMPETITOR_BENCHMARKING_TOOL_DEFINITION]

    @property
    def require_citations(self) -> bool:
        return True
    
    async def analyze(self, earnings_content: str) -> str:
        """
        Perform business, industry, and operational risk analysis using tool calling.
        
        The agent will:
        1. Read the earnings report
        2. Identify the company's ticker and its top competitors
        3. Call get_competitor_benchmarking to compare performance
        4. Produce analysis cross-referencing internal claims vs. industry reality
        
        Args:
            earnings_content: Parsed earnings report content
        
        Returns:
            Detailed business and operational risk analysis in JSON format
        """
        additional_instructions = """
Analyze the provided earnings report content. Follow these steps:

STEP 1: Identify the stock ticker from the report header and use it EXACTLY. 
         (Example: If header says 'NovaTech (NVTC)', the ticker is 'NVTC'. 
          DO NOT use 'NovaTech' or 'NOVS').
STEP 2: Identify 2-3 of its biggest publicly-traded competitors in the same industry.
STEP 3: Call the `get_competitor_benchmarking` tool with the primary ticker and
         competitor tickers to get a side-by-side performance comparison.
STEP 4: Use the comparison data to evaluate:
         - Is the company growing faster or slower than competitors?
         - Are its margins better or worse than industry peers?
         - Is it gaining or losing market share?
STEP 5: Also analyze CapEx trends, customer concentration, pricing power,
         and operational risks from the report text itself.
STEP 6: Produce your final analysis as a JSON object following the schema.

Be thorough but concise. If specific CapEx data is not found, note it explicitly.
"""
        return await self.generate_with_tools(
            earnings_content, additional_instructions, expect_json=True
        )
