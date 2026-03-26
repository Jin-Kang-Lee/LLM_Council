"""
Deep Research Agent
Specializes in identifying information gaps and executing real web searches via DDGS.
"""

import json
import re
import asyncio
from typing import Optional
from duckduckgo_search import DDGS

from .base_agent import BaseAgent
from config import GROQ_API_KEY_1, GROQ_MODEL_1


class DeepResearchAgent(BaseAgent):
    """Agent focused on finding external information and filling data gaps."""

    def __init__(self):
        super().__init__(
            name="Deep Research Analyst",
            color="blue",
            api_key=GROQ_API_KEY_1,
            model=GROQ_MODEL_1,
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
        """Analyze content to generate a research plan (JSON with pending queries)."""
        additional_instructions = "Analyze the report and identify exactly what is missing or needs external checking. Create a research plan in the required JSON format."
        return await self.generate(earnings_content, additional_instructions)

    async def execute_searches(self, research_plan_json: str, max_results_per_query: int = 3) -> str:
        """
        Execute the planned searches using DDGS.
        Fills in 'status' and 'result' for each query and returns the enriched JSON.
        """
        plan = self._parse_json(research_plan_json)
        if not plan:
            print(f"[{self.name}] Could not parse research plan JSON — skipping searches.")
            return research_plan_json

        queries = plan.get("search_queries", [])
        capped = queries[:5]  # Cap at 5 queries to avoid rate limiting
        print(f"[{self.name}] Executing {len(capped)} search queries via DDGS...")

        for query_obj in capped:
            q = query_obj.get("query", "").strip()
            if not q:
                continue
            try:
                results = await asyncio.to_thread(self._ddgs_search, q, max_results_per_query)
                formatted = []
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    href = r.get("href", "")
                    formatted.append(f"**{title}**\n{body}\nSource: {href}")
                query_obj["status"] = "complete"
                query_obj["result"] = "\n\n".join(formatted) if formatted else "No results found."
                print(f"[{self.name}] Done: {q[:60]}...")
                await asyncio.sleep(1.5)  # Rate limit protection between queries
            except Exception as e:
                query_obj["status"] = "error"
                query_obj["result"] = f"Search failed: {str(e)}"
                print(f"[{self.name}] Search error for '{q}': {e}")

        return json.dumps(plan, indent=2)

    def _ddgs_search(self, query: str, max_results: int) -> list:
        """Synchronous DDGS call — run via asyncio.to_thread."""
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    def _parse_json(self, text: str) -> Optional[dict]:
        """Parse JSON from LLM output, handling extra prose around the object."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return None
