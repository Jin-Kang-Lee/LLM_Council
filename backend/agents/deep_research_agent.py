"""
Deep Research Agent
Specializes in identifying information gaps and searching for external verification.
"""

from .base_agent import BaseAgent
from typing import Optional

class DeepResearchAgent(BaseAgent):
    """Agent focused on finding external information and filling data gaps."""
    
    def __init__(self):
        super().__init__(
            name="Deep Research Analyst",
            color="blue"
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are the "Deep Research Analyst".
Your mission is to look beyond the provided earnings report and identify critical information that is missing, undisclosed, or requires external verification.

SCOPE:
- Competitor benchmarks and market share
- Regulatory filings beyond the current report (e.g., pending lawsuits)
- Macroeconomic context affecting the specific industry
- Unanswered questions from the analyst call

STRICT RULES:
1. IDENTIFY specific questions that need answering.
2. FORMULATE precise search queries for each question.
3. PROVIDE a "Thinking Trace" explaining why this information is crucial.
4. Output MUST be a single, valid JSON object.

OUTPUT JSON SCHEMA:
{
  "thinking_trace": "A detailed paragraph explaining your research strategy and why certain gaps are critical.",
  "search_queries": [
    {
      "topic": "The broad area of research",
      "query": "The exact search string to use",
      "rationale": "Why this specific query will fix a data gap",
      "status": "pending",
      "result": null
    }
  ],
  "confidence_gap": "Description of the biggest unknown"
}"""

    @property
    def analysis_rules(self) -> str:
        return "Return ONLY the JSON object. Do not perform actual searches yet; just plan them."

    async def analyze(self, earnings_content: str) -> str:
        """Analyze content to generate research plan."""
        additional_instructions = "Analyze the report and identify exactly what is missing or needs external checking. Create a research plan in the required JSON format."
        return await self.generate(earnings_content, additional_instructions)
