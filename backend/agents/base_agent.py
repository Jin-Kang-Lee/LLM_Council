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
        """Return the agent's system prompt."""
        pass
    
    def _build_prompt(self, context: str, additional_instructions: Optional[str] = None) -> str:
        """Build the full prompt with system instructions."""
        prompt = f"{self.system_prompt}\n\n---\n\n{context}"
        if additional_instructions:
            prompt += f"\n\n{additional_instructions}"
        return prompt
    
    async def generate(self, context: str, additional_instructions: Optional[str] = None) -> str:
        """
        Generate a response using Ollama.
        
        Args:
            context: The main context/content to analyze
            additional_instructions: Optional additional instructions
        
        Returns:
            Generated response string
        """
        prompt = self._build_prompt(context, additional_instructions)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        try:
            print(f"[{self.name}] Sending request to Ollama...")
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout
                response = await client.post(self.ollama_url, json=payload)
                response.raise_for_status()
                result = response.json()
                print(f"[{self.name}] Response received successfully")
                return result.get("response", "")
        except httpx.TimeoutException:
            print(f"[{self.name}] ERROR: Ollama request timed out")
            raise Exception(f"Ollama request timed out for {self.name}")
        except httpx.ConnectError:
            print(f"[{self.name}] ERROR: Cannot connect to Ollama at {self.ollama_url}")
            raise Exception(f"Cannot connect to Ollama. Is it running at {OLLAMA_BASE_URL}?")
        except Exception as e:
            print(f"[{self.name}] ERROR: {str(e)}")
            raise
    
    async def generate_stream(self, context: str, additional_instructions: Optional[str] = None) -> Generator[str, None, None]:
        """
        Generate a streaming response using Ollama.
        
        Args:
            context: The main context/content to analyze
            additional_instructions: Optional additional instructions
        
        Yields:
            Response chunks as they arrive
        """
        prompt = self._build_prompt(context, additional_instructions)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", self.ollama_url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
    
    def respond_to(self, other_agent_name: str, other_response: str, context: str) -> str:
        """
        Generate a response to another agent's analysis.
        
        Args:
            other_agent_name: Name of the other agent
            other_response: The other agent's analysis
            context: Original context/content
        
        Returns:
            Response addressing the other agent's points
        """
        discussion_prompt = f"""
You are in a discussion with {other_agent_name}. They have provided the following analysis:

---
{other_response}
---

Based on your expertise and the original content, provide your response. You may:
- Support their findings with additional evidence
- Challenge points you disagree with
- Add perspectives they may have missed
- Synthesize both viewpoints where appropriate

Keep your response focused and professional. Reference specific data points when possible.
"""
        return discussion_prompt
