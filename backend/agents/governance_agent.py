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
            tools=[INSIDER_TRADING_TOOL_DEFINITION]
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert Governance & Compliance Analyst. Your role is to analyze earnings reports for governance, legal, regulatory, and accounting quality risks.

## PRIMARY ANALYSIS AREAS

### 1. Corporate Governance
- Board structure and independence
- Ownership concentration and related-party transactions
- Management changes and control risks

### 2. Legal & Regulatory Exposure
- Litigation and regulatory investigations
- Fines, sanctions, or enforcement actions
- Licensing issues or compliance orders

### 3. Compliance Risk
- AML/KYC control weaknesses
- Regulatory compliance gaps
- Auditor findings or management disclosures

### 4. Accounting & Disclosure Quality
- Audit opinion quality (qualified, adverse, going concern)
- Restatements or revisions
- Disclosure gaps and missing information

## OUTPUT FORMAT

**GOVERNANCE SUMMARY**
[2-3 sentence executive summary]

**KEY FINDINGS**
1. [Finding 1 — Category: Governance/Legal/Compliance/Accounting]: [Description with evidence]
2. [Finding 2]: [Description with evidence]
3. [Finding 3]: [Description with evidence]

**GOVERNANCE RISK LEVEL**: [Low/Medium/High]
**COMPLIANCE RISK LEVEL**: [Low/Medium/High]

**NON-DISCLOSURES**
- [Expected items not found in the report]

Be precise. Only state what is disclosed. If something is not in the report, say "Not disclosed" — do not guess."""

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
        """
        Perform governance and compliance analysis on earnings content.
        
        Args:
            earnings_content: Parsed earnings report content
        
        Returns:
            Detailed governance analysis in JSON format
        """
        additional_instructions = """
Analyze the provided earnings report content. Focus exclusively on governance,
compliance, legal risks, and accounting quality. Ground all findings in evidence from the report.
"""
        return await self.generate(
            earnings_content,
            additional_instructions,
            reference_context=reference_context,
            reference_query=reference_query,
            allow_targeted_retrieval=allow_targeted_retrieval,
        )
