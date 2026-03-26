"""
Base Agent Module
Abstract base class for all specialized agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Optional
from groq import AsyncGroq


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, color: str, api_key: str, model: str):
        self.name = name
        self.color = color
        self.api_key = api_key
        self.model = model

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the agent's core identity/persona (Who are you?)."""
        pass

    @property
    def discussion_persona(self) -> str:
        """Return this agent's unique war room voice. Override in war room agents."""
        return ""

    @property
    def analysis_rules(self) -> str:
        """Return rules for individual analysis (e.g., JSON formatting)."""
        return ""

    def _build_analysis_prompt(self, context: str, additional_instructions: Optional[str] = None) -> str:
        """Build the full prompt for analysis mode."""
        prompt = f"{self.system_prompt}\n\nSTRICT ANALYSIS RULES:\n{self.analysis_rules}\n\n---\n\nREPORT CONTENT:\n{context}"
        if additional_instructions:
            prompt += f"\n\n{additional_instructions}"
        return prompt

    async def generate(self, context: str, additional_instructions: Optional[str] = None) -> str:
        """Generate an analysis response."""
        prompt = self._build_analysis_prompt(context, additional_instructions)
        return await self._call_groq(prompt)

    async def write_position_paper(self, analysis_json: str) -> str:
        """
        Distill the agent's JSON analysis into a concise war room opening position.
        3 bullets max — one strong claim each, backed by a specific number or quote.
        This is what other agents see, not the raw JSON.
        """
        prompt = f"""{self.system_prompt}

{self.discussion_persona}

Your deep analysis is complete. Here are your findings:
---
{analysis_json}
---

Write your WAR ROOM OPENING POSITION.
- Exactly 3 bullet points
- Each bullet = one sharp, specific claim you will defend in the debate
- Lead with your strongest finding
- Each bullet must cite one number, ratio, or direct quote from the report as evidence
- Be direct and opinionated — this is your stake in the ground before debate opens

No JSON. No preamble. Just the 3 bullets."""
        return await self._call_groq(prompt, temperature=0.7)

    async def generate_discussion(
        self,
        position_papers: dict,
        thread: list,
        turn_instruction: str,
        research_findings: str = "",
    ) -> str:
        """
        Generate a war room response using the proper chat messages array.

        Args:
            position_papers: {"Agent Name": "position paper text", ...} for all 3 agents
            thread:          full conversation so far [{"agent": ..., "content": ...}, ...]
            turn_instruction: what this agent should do right now
            research_findings: DDGS results to include as external context
        """
        messages = [
            {"role": "system", "content": f"{self.system_prompt}\n\n{self.discussion_persona}"},
        ]

        if research_findings:
            messages.append({
                "role": "user",
                "content": f"EXTERNAL RESEARCH FINDINGS (from web search):\n{research_findings}"
            })

        papers_text = "\n\n".join([
            f"**{agent}**:\n{paper}"
            for agent, paper in position_papers.items()
        ])
        messages.append({"role": "user", "content": f"OPENING POSITIONS:\n{papers_text}"})

        # Add full conversation thread — own messages as "assistant", others as "user"
        for msg in thread:
            role = "assistant" if msg["agent"] == self.name else "user"
            messages.append({"role": role, "content": f"[{msg['agent']}]: {msg['content']}"})

        messages.append({"role": "user", "content": turn_instruction})

        return await self._call_groq_messages(messages)

    def respond_to(self, other_agent_name: str, other_response: str) -> str:
        """Return the turn instruction for responding to another agent."""
        return f"[{other_agent_name}] just said:\n---\n{other_response}\n---\nYour turn. Stay in character. Be concise."

    async def _call_groq(self, prompt: str, temperature: float = 0.7) -> str:
        """Single-turn completion — used for analysis and position papers."""
        try:
            print(f"[{self.name}] Sending request to Groq ({self.model})...")
            client = AsyncGroq(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=8192,
            )
            print(f"[{self.name}] Response received successfully")
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"[{self.name}] ERROR: {str(e)}")
            raise

    async def _call_groq_messages(self, messages: list, temperature: float = 0.9) -> str:
        """Multi-turn chat completion — used for war room discussion."""
        try:
            print(f"[{self.name}] War room turn — Groq ({self.model})...")
            client = AsyncGroq(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=600,  # Keep debate responses tight
            )
            print(f"[{self.name}] Response received successfully")
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"[{self.name}] ERROR: {str(e)}")
            raise
