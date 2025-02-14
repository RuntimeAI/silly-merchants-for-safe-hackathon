from typing import Optional, Dict
from ....utils.llm_providers.openrouter import OpenRouterProvider
from ....utils.config import Config
import logging

logger = logging.getLogger(__name__)

class NegotiationAgent:
    def __init__(self, name: str, model: str = None, backup_model: str = None, llm_provider = None):
        self.name = name
        self.coins = 10  # Starting coins
        self.llm_provider = llm_provider
        self.model = model
        self.backup_model = backup_model
        self.round = 1  # Add round tracking
        self._role_prompt = self._get_role_prompt()
    
    def _get_role_prompt(self) -> str:
        """Override this method to provide role-specific prompt"""
        raise NotImplementedError
    
    def transfer_coins(self, amount: int, recipient: 'NegotiationAgent') -> bool:
        if amount <= self.coins and amount > 0:
            self.coins -= amount
            recipient.coins += amount
            return True
        return False
    
    def get_status(self) -> str:
        return f"{self.name} has {self.coins} coins"
    
    def generate_response(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate response using LLM provider"""
        try:
            # Pass only the prompt and temperature, not the model names
            return self.llm_provider.generate(
                prompt=prompt,
                system_prompt=self._get_role_prompt(),
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Error generating response for {self.name}: {str(e)}")
            raise 

    def get_player_statuses(self) -> Dict[str, int]:
        """Get current player statuses"""
        return {
            "Marco Polo": self.coins,  # This is simplified, should get from game state
            "Trader Joe": 10  # This is simplified, should get from game state
        } 