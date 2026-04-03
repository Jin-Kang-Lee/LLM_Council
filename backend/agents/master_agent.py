"""
Master Agent - Phase 4
Consolidates all analyses into a unified earnings report (JSON).
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
        return """You are the "Senior Investment Analyst" responsible for synthesizing multiple expert analyses into a single, cohesive investment report.
Your role: resolve analyst disagreements with reasoned judgment, surface the most critical findings, and deliver clear, actionable conclusions.
Tone: authoritative, balanced, evidence-driven."""

    @property
    def analysis_rules(self) -> str:
        return """OUTPUT RULES:
1. Output MUST be a single valid JSON object. No markdown, no commentary, no code fences.
2. Use ONLY information from the analyses and discussion provided — do NOT invent figures.
3. If data is missing or unclear, use the best available evidence and note uncertainty.
4. You MUST use exactly these field names — do not rename or add fields.

FILL IN THIS EXACT JSON TEMPLATE:
{
  "executive_summary": "<3-4 sentence summary of the key takeaway for decision-makers>",
  "risk_assessment": {
    "summary": "<synthesized summary of key risk findings>",
    "primary_risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
    "risk_level": "<Low|Medium|High|Critical>"
  },
  "sentiment_outlook": {
    "summary": "<synthesized sentiment and forward outlook>",
    "management_confidence": "<Low|Medium|High>",
    "market_outlook": "<Bearish|Neutral|Bullish>"
  },
  "governance_compliance": {
    "summary": "<synthesized governance and compliance assessment>",
    "governance_risk": "<Low|Medium|High>",
    "compliance_status": "<description of compliance status>",
    "confidence_score": <0.0-1.0>
  },
  "points_of_agreement": ["<agreed finding 1>", "<agreed finding 2>"],
  "points_of_contentions": [
    {
      "issue": "<description of the contention>",
      "resolution": "<how you resolve or weigh the disagreement>"
    }
  ],
  "key_metrics": [
    {
      "metric": "<metric name>",
      "finding": "<value or finding>",
      "implication": "<what this means for investors>"
    }
  ],
  "investment_considerations": {
    "strengths": ["<strength 1>", "<strength 2>"],
    "concerns": ["<concern 1>", "<concern 2>"]
  },
  "final_recommendation": {
    "recommendation": "<Underperform|Neutral|Outperform>",
    "confidence_level": "<Low|Medium|High>"
  },
  "discussion_summary": "<1-2 sentence summary of the key debate points and consensus reached>"
}"""

    @property
    def json_schema(self) -> dict:
        return {
            "executive_summary": str,
            "risk_assessment": {
                "summary": str,
                "primary_risks": [str],
                "risk_level": str,
            },
            "sentiment_outlook": {
                "summary": str,
                "management_confidence": str,
                "market_outlook": str,
            },
            "governance_compliance": {
                "summary": str,
                "governance_risk": str,
                "compliance_status": str,
                "confidence_score": (int, float),
            },
            "points_of_agreement": [str],
            "points_of_contentions": [
                {
                    "issue": str,
                    "resolution": str,
                }
            ],
            "key_metrics": [
                {
                    "metric": str,
                    "finding": str,
                    "implication": str,
                }
            ],
            "investment_considerations": {
                "strengths": [str],
                "concerns": [str],
            },
            "final_recommendation": {
                "recommendation": str,
                "confidence_level": str,
            },
            "discussion_summary": str,
        }

    async def consolidate(
        self,
        original_content: str,
        risk_analysis: str,
        business_ops_analysis: str,
        governance_analysis: str,
        research_analysis: str,
        discussion_transcript: str,
    ) -> str:
        """Generate the final consolidated report as JSON."""
        context = f"""ORIGINAL EARNINGS CONTENT:
{original_content}

---

RISK ANALYST'S ASSESSMENT:
{risk_analysis}

---

BUSINESS & OPS ANALYST'S ASSESSMENT:
{business_ops_analysis}

---

GOVERNANCE & COMPLIANCE ASSESSMENT:
{governance_analysis}

---

ANALYST DISCUSSION TRANSCRIPT:
{discussion_transcript}
"""

        prompt = (
            f"{self.system_prompt}\n\n"
            f"{self.analysis_rules}\n\n"
            "TASK — SYNTHESIS:\n"
            "Review all analyses and the discussion transcript above.\n"
            "Synthesize findings into the JSON template. Resolve any disagreements with reasoned judgment.\n"
            "CRITICAL: Copy the field names from the template EXACTLY — do not rename, add, or remove any field.\n"
            "Every field must be grounded in the provided analyses — do not invent figures.\n\n"
            f"{context}"
        )

        return await self._generate_with_retry(prompt)
