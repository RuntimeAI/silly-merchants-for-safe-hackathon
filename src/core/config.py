from typing import Dict, Any
from pydantic import BaseModel
import os

class GameConfig(BaseModel):
    """Configuration for the Silly Merchants game"""
    max_rounds: int = 5
    initial_balance: float = 1000.0
    trading_fee: float = 0.01
    min_trade_amount: float = 1.0
    
    class Config:
        arbitrary_types_allowed = True 

    def _load_llm_config(self) -> Dict[str, Any]:
        """Load LLM configuration"""
        return {
            "default_provider": "gemini",
            "providers": {
                "openrouter": {
                    # ... existing OpenRouter config ...
                },
                "gemini": {
                    "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
                    "location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
                    "models": {
                        "player1": {
                            "default": "gemini-pro",
                            "backup": "gemini-pro"
                        },
                        "player2": {
                            "default": "gemini-pro",
                            "backup": "gemini-pro"
                        },
                        "coordinator": {
                            "default": "gemini-pro",
                            "backup": "gemini-pro"
                        }
                    }
                }
            }
        } 