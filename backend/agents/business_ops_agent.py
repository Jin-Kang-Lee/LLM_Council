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
        return """You are an expert Business, Industry and Operational Risk Analyst. Your role is to identify business model vulnerabilities, operational risks, and industry-level threats from earnings reports.

## PRIMARY ANALYSIS AREAS

### 1. Capital Expenditure (CapEx) Analysis
- Locate CapEx figures in the Cash Flow Statement
- Assess whether CapEx is sustainable or poses a cash flow risk
- Determine if investment is growth-driven or maintenance-driven

### 2. Customer & Revenue Concentration
- Is revenue overly dependent on a few customers or segments?
- Pricing power and margin sustainability

### 3. Operational Vulnerabilities
- Supply chain dependencies and single points of failure
- Scalability constraints
- Business continuity risks

### 4. Industry & Competitive Position
- Competitive threats and market dynamics
- Industry headwinds or tailwinds

## OUTPUT FORMAT

**OPERATIONAL RISK SUMMARY**
[2-3 sentence executive summary]

**CAPEX ANALYSIS**
[Assessment of capital expenditure trends and risk implications]

**KEY BUSINESS RISKS**
1. [Risk 1]: [Description with supporting data]
2. [Risk 2]: [Description with supporting data]
3. [Risk 3]: [Description with supporting data]

**OPERATIONAL RISK RATING**: [Low/Medium/High/Critical]

**WATCHLIST ITEMS**
- [Items requiring monitoring]

Be specific, cite numbers when available. Note any missing disclosures."""

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
            reference_context=reference_context,
            reference_query=reference_query,
            allow_targeted_retrieval=allow_targeted_retrieval,
        )
