"""
Base Agent Module
Abstract base class for all specialized agents in the system.
"""

import httpx
from abc import ABC, abstractmethod
from typing import Generator, Optional
import json

from config import OLLAMA_BASE_URL, OLLAMA_MODEL


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, name: str, color: str):
        """
        Initialize the base agent.
        
        Args:
            name: Display name of the agent
            color: Color identifier for UI differentiation
        """
        self.name = name
        self.color = color
        self.ollama_url = f"{OLLAMA_BASE_URL}/api/generate"
        self.model = OLLAMA_MODEL
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the agent's core identity/persona (Who are you?)."""
        pass

    @property
    def analysis_rules(self) -> str:
        """Return rules for individual analysis (e.g., JSON formatting)."""
        return ""

    def _build_prompt(self, context: str, additional_instructions: Optional[str] = None, mode: str = "analysis") -> str:
        """Build the full prompt with system instructions based on mode."""
        if mode == "analysis":
            prompt = f"{self.system_prompt}\n\nSTRICT ANALYSIS RULES:\n{self.analysis_rules}\n\n---\n\nREPORT CONTENT:\n{context}"
        else:
            prompt = f"{self.system_prompt}\n\nDISCUSSION MODE:\nYou are in the 'War Room'. Engage in a professional, punchy debate with other analysts.\n\n---\n\nREPORT CONTENT:\n{context}"
            
        if additional_instructions:
            prompt += f"\n\n{additional_instructions}"
        return prompt
    
    async def generate(self, context: str, additional_instructions: Optional[str] = None) -> str:
        """Generate a response (defaults to analysis mode)."""
        prompt = self._build_prompt(context, additional_instructions, mode="analysis")
        return await self._call_ollama(prompt)

    async def generate_discussion(self, context: str, discussion_prompt: str) -> str:
        """Generate a discussion-specific response (avoids JSON rules)."""
        prompt = self._build_prompt(context, discussion_prompt, mode="discussion")
        return await self._call_ollama(prompt, temperature=0.8) # Slightly higher temp for debate

    async def _call_ollama(self, prompt: str, temperature: float = 0.7) -> str:
        """Internal helper to call Ollama API."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
            }
        }
        
        try:
            print(f"[{self.name}] Sending request to Ollama...")
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(self.ollama_url, json=payload)
                response.raise_for_status()
                result = response.json()
                print(f"[{self.name}] Response received successfully")
                return result.get("response", "")
        except Exception as e:
            print(f"[{self.name}] ERROR: {str(e)}")
            raise

    def respond_to(self, other_agent_name: str, other_response: str, context: str) -> str:
        """
        Generate a debate-style response to another agent.
        """
        discussion_prompt = f"""
WAR ROOM DEBATE:
{other_agent_name} has just shared their perspective:
---
{other_response}
---

MISSION: Respond to {other_agent_name}. 
The user finds the chat is too "spammy". 
RULES FOR YOUR RESPONSE:
1. BE CONCISE. Do not repeat your entire analysis. 
2. BE DIRECT. Counter-argue if they are too optimistic/pessimistic.
3. BE CONVERSATIONAL. Use phrases like "I see your point on X, but...", or "Adding to your point on Y...".
4. STAY GROUNDED. Use 1 specific quote or metric from the report to back up your challenge or support.
5. NO JSON. Output plain, professional markdown text.

Respond now:"""
        return discussion_prompt
