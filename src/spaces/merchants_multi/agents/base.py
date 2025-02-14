from typing import Optional
from ....core.base_agent import BaseAgent
from ....utils.llm_providers.openrouter import OpenRouterProvider
from ....utils.config import Config

class NegotiationAgent(BaseAgent):
    def __init__(self, name: str, model: str = None, backup_model: str = None, llm_provider = None, coins: int = 10):
        # If no specific model provided, use defaults from config
        if not model or not llm_provider:
            config = Config()
            llm_provider = llm_provider or OpenRouterProvider()
            model = model or config.llm_config['models']['player1']['default']
            backup_model = backup_model or config.llm_config['models']['player1']['backup']
        
        super().__init__(name, model, backup_model, llm_provider)
        self.coins = coins
    
    def transfer_coins(self, amount: int, recipient: 'NegotiationAgent') -> bool:
        if amount <= self.coins and amount > 0:
            self.coins -= amount
            recipient.coins += amount
            return True
        return False
    
    def get_status(self) -> str:
        return f"{self.name} has {self.coins} coins"
    
    def generate_response(self, context_prompt: str, **kwargs) -> str:
        """Override to include agent name in logging"""
        full_prompt = f"{self._role_prompt}\n\n{context_prompt}"
        return self.llm.generate(full_prompt, self.model, self.backup_model, agent_name=self.name, **kwargs) 