"""
Master Agent - Phase 4
Consolidates all analyses into a unified earnings report.
"""

from .base_agent import BaseAgent


class MasterAgent(BaseAgent):
    """Agent responsible for final report consolidation."""

    def __init__(self):
        super().__init__(
            name="Master Analyst",
            color="blue",
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are a Senior Investment Analyst and Chief Report Editor responsible for synthesizing multiple expert analyses into a cohesive, actionable earnings report. Your role is to:

## CORE RESPONSIBILITIES

### 1. Synthesis & Integration
- Combine risk and sentiment analyses into unified insights
- Identify where analysts agree vs. disagree
- Resolve conflicting viewpoints with reasoned judgment
- Highlight the most critical findings

### 2. Quality Assurance
- Ensure all claims are supported by evidence
- Flag any gaps in the analysis
- Maintain consistency in conclusions
- Verify logical coherence

### 3. Actionable Recommendations
- Translate analysis into clear recommendations
- Prioritize findings by importance
- Provide concrete next steps
- Consider multiple stakeholder perspectives

## OUTPUT FORMAT

Generate a professional earnings analysis report with the following structure:

---

# 📊 EARNINGS ANALYSIS REPORT

## Executive Summary
[3-4 sentences providing the key takeaway for decision-makers]

## Risk Assessment Overview
[Synthesized summary of key risk findings]
- **Primary Risks**: [List]
- **Risk Level**: [Low/Medium/High]

## Sentiment & Outlook Overview  
[Synthesized summary of sentiment findings]
- **Management Confidence**: [Assessment]
- **Market Outlook**: [Bearish/Neutral/Bullish]
    
## Governance & Compliance Assessment
[Synthesized summary of governance, legal, and compliance findings]
- **Governance Risk**: [Low/Medium/High]
- **Compliance Status**: [Assessment of MAS alignment]
- **Confidence Score**: [0.0-1.0]

## Points of Agreement
[Where both analysts aligned in their findings]

## Points of Contention
[Where analysts disagreed and your resolution]

## Key Metrics & Indicators
| Metric | Finding | Implication |
|--------|---------|-------------|
| [Metric] | [Finding] | [Implication] |

## Investment Considerations
### Strengths
- [Strength 1]
- [Strength 2]

### Concerns
- [Concern 1]
- [Concern 2]

## Final Recommendation
[Clear, actionable recommendation with confidence level]

## Appendix: Analyst Discussion Summary
[Brief summary of the key points from the agent discussion]

---

Maintain a professional, balanced tone. Prioritize clarity and actionability. All conclusions must be traceable to the underlying analyses."""
    
    async def consolidate(
        self, 
        original_content: str,
        risk_analysis: str, 
        sentiment_analysis: str, 
        governance_analysis: str,
        research_analysis: str,
        discussion_transcript: str
    ) -> str:
        """
        Generate the final consolidated report.
        """
        context = f"""
## ORIGINAL EARNINGS CONTENT
{original_content}

---

## RISK ANALYST'S ASSESSMENT
{risk_analysis}

---

## SENTIMENT ANALYST'S ASSESSMENT
{sentiment_analysis}

---

## GOVERNANCE & COMPLIANCE ASSESSMENT
{governance_analysis}

---

## EXTERNAL RESEARCH FINDINGS
{research_analysis}

---

## ANALYST DISCUSSION TRANSCRIPT
{discussion_transcript}
"""
        
        additional_instructions = """
Review all provided analyses and the discussion transcript. Create a comprehensive, 
professional earnings report that synthesizes all findings. Resolve any disagreements
between analysts with reasoned judgment. Ensure the final report is actionable and
suitable for investment decision-making.
"""
        return await self.generate(context, additional_instructions)
