from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list] = None,
    ) -> str:
        """Generate text using the LLM"""
        pass

    @staticmethod
    @abstractmethod
    def get_config() -> Dict[str, Any]:
        """Get provider configuration"""
        pass 