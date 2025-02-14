from abc import ABC, abstractmethod
from typing import Dict, Any
from ..utils.llm_providers import BaseLLMProvider

class BaseAgent(ABC):
    def __init__(self, name: str, model: str, backup_model: str, llm_provider: BaseLLMProvider):
        self.name = name
        self.model = model
        self.backup_model = backup_model
        self.llm = llm_provider
        self._role_prompt = self._get_role_prompt()
    
    @abstractmethod
    def _get_role_prompt(self) -> str:
        """Define the agent's base role, personality, and expertise"""
        pass
    
    def generate_response(self, context_prompt: str, system_prompt: str = None, **kwargs) -> str:
        """Generate response by combining role prompt with context-specific prompt"""
        full_prompt = f"{self._role_prompt}\n\n{context_prompt}"
        return self.llm.generate(
            full_prompt, 
            self.model, 
            self.backup_model, 
            system_prompt=system_prompt,
            **kwargs
        )

    @abstractmethod
    def process(self, *args, **kwargs):
        """Process the agent's main action"""
        pass 