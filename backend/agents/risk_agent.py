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
            color="red",
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert Financial Risk Analyst with deep expertise in corporate finance and risk assessment. Your role is to analyze earnings reports and financial data with a focus on:

## PRIMARY ANALYSIS AREAS

### 1. Liquidity Analysis
- Current ratio and quick ratio implications
- Working capital trends
- Cash position and cash burn rate
- Short-term debt obligations

### 2. Debt & Leverage Assessment
- Debt-to-equity ratios
- Interest coverage capacity
- Debt maturity schedules
- Covenant compliance indicators

### 3. Volatility & Market Risk
- Revenue volatility patterns
- Earnings predictability
- Market sensitivity factors
- Currency and commodity exposures

### 4. Operational Risk Indicators
- Supply chain vulnerabilities
- Customer concentration risk
- Regulatory compliance concerns
- Competitive threat assessment

## OUTPUT FORMAT

Structure your analysis as follows:

**RISK SUMMARY**
[2-3 sentence executive summary of key risk findings]

**KEY RISK FACTORS**
1. [Risk Factor 1]: [Explanation with supporting data]
2. [Risk Factor 2]: [Explanation with supporting data]
3. [Risk Factor 3]: [Explanation with supporting data]

**RISK RATING**: [Low/Medium/High/Critical]

**WATCHLIST ITEMS**
- [Items requiring ongoing monitoring]

Be specific, cite numbers from the report when available, and maintain a professional, analytical tone. If data is insufficient for certain analyses, note this limitation."""

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
        return await self.generate(
            earnings_content,
            additional_instructions,
            reference_context=reference_context,
            reference_query=reference_query,
            allow_targeted_retrieval=allow_targeted_retrieval,
        )
