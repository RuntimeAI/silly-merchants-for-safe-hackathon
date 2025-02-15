from typing import Optional, Dict, Any
from ....utils.llm_providers.openrouter import OpenRouterProvider
from ....utils.config import Config
import logging
from src.utils.logger import GameLogger
from src.utils.llm_providers.fallback import FallbackProvider

logger = logging.getLogger(__name__)

class NegotiationAgent:
    def __init__(self, name: str):
        config = Config()
        model_config = config.llm_config['models']['player1']  # Default to player1 config
        
        self.name = name
        self.coins = 10  # Starting coins
        self.round = 1
        
        # Initialize logger
        self.logger = GameLogger(f"agent_{name}")
        
        # Initialize LLM provider
        self.model = model_config['default']
        self.backup_model = model_config['backup']
        self.llm_provider = FallbackProvider()
        
        self.logger.info(f"Agent {name} initialized with {self.coins} coins")
    
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
        """Generate response using LLM"""
        try:
            response = self.llm_provider.generate(
                model=self.model,
                prompt=prompt,
                temperature=temperature
            )
            return response
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            # Try backup model
            try:
                self.logger.info(f"Trying backup model {self.backup_model}")
                response = self.llm_provider.generate(
                    model=self.backup_model,
                    prompt=prompt,
                    temperature=temperature
                )
                return response
            except Exception as e:
                self.logger.error(f"Backup model failed: {str(e)}")
                raise

    def get_player_statuses(self) -> Dict[str, int]:
        """Get current player statuses"""
        return {"coins": self.coins} 