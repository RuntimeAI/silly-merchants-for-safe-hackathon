from typing import Optional, Dict, Any
import logging
import os
from .gemini import GeminiProvider
from .openrouter import OpenRouterProvider
from .base import BaseLLMProvider
from pathlib import Path

logger = logging.getLogger(__name__)

class FallbackProvider(BaseLLMProvider):
    """Provider that falls back to OpenRouter if Gemini fails"""
    
    def __init__(self):
        """Initialize provider"""
        try:
            self.provider = GeminiProvider()  # Will use env variable
            logger.info("Initialized Gemini Studio provider")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini provider: {str(e)}")
            raise

    def generate(self, *args, **kwargs) -> str:
        """Generate text using Gemini"""
        try:
            logger.info("Attempting generation with Gemini provider")
            return self.provider.generate(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in FallbackProvider generate: {str(e)}")
            logger.error(f"Args: {args}")
            logger.error(f"Kwargs: {kwargs}")
            raise

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get provider configuration"""
        return GeminiProvider.get_config() 