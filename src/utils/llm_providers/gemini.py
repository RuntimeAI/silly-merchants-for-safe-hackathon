from typing import Optional, Dict, Any
import logging
import google.generativeai as genai
import json
import os
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini Studio Provider"""
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini provider with API key"""
        try:
            # Get API key from environment if not provided
            api_key = api_key or os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("No Gemini API key found in environment")
            
            # Configure the Gemini API
            genai.configure(api_key=api_key)
            
            # Initialize both models
            self.default_model = genai.GenerativeModel('gemini-2.0-flash')
            self.backup_model = genai.GenerativeModel('gemini-2.0-flash-lite-preview-02-05')
            logger.info("Initialized Gemini Flash providers")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini provider: {str(e)}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list] = None,
        use_backup: bool = False,
        **kwargs
    ) -> str:
        """Generate text using Gemini"""
        try:
            logger.info(f"Starting Gemini generation with temperature: {temperature}")
            
            # Select model
            model = self.backup_model if use_backup else self.default_model
            model_name = "Flash Lite" if use_backup else "Flash"
            logger.info(f"Using {model_name} model")
            
            # Format the prompt with system prompt if provided
            formatted_prompt = prompt
            if system_prompt:
                formatted_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            logger.info(f"Formatted prompt: {formatted_prompt}")
            
            # Generate response
            try:
                logger.info("Sending message to Gemini...")
                response = model.generate_content(
                    formatted_prompt,
                    generation_config={
                        "temperature": float(temperature),
                        "max_output_tokens": max_tokens if max_tokens else 1024,
                        "stop_sequences": stop if stop else [],
                        "candidate_count": 1
                    }
                )
                logger.info("Message sent successfully")
                
                text = response.text
                logger.info(f"Raw response: {text}")
                
                # Clean up and validate response
                return self._process_response(text, prompt)

            except Exception as e:
                if not use_backup:
                    logger.warning(f"Primary model failed, trying backup model: {str(e)}")
                    return self.generate(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stop=stop,
                        use_backup=True
                    )
                raise

        except Exception as e:
            logger.error(f"Error in generate method: {str(e)}")
            raise

    def _process_response(self, text: str, prompt: str) -> str:
        """Process and validate the response"""
        # Clean up markdown code blocks if present
        if "```json" in text:
            logger.info("Cleaning up markdown code blocks")
            text = text.split("```json")[-1]
            text = text.split("```")[0]
            text = text.strip()
            logger.info(f"Cleaned response: {text}")
        
        # Validate JSON if that's what we're expecting
        if '"message"' in prompt and '"transfers"' in prompt:
            logger.info("Validating JSON response")
            try:
                json_obj = json.loads(text)
                normalized = json.dumps(json_obj)
                logger.info(f"Valid JSON response: {normalized}")
                return normalized
            except json.JSONDecodeError as e:
                logger.error(f"JSON validation failed: {str(e)}")
                logger.error(f"Invalid JSON text: {text}")
                fallback = json.dumps({
                    "message": "Error: Could not generate valid JSON response",
                    "transfers": []
                })
                logger.info(f"Using fallback JSON: {fallback}")
                return fallback
        
        return text

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get provider configuration"""
        return {
            "name": "gemini",
            "models": {
                "gemini-2.0-flash": {
                    "context_length": 32768,
                    "supports_functions": True,
                    "supports_vision": False
                },
                "gemini-2.0-flash-lite-preview-02-05": {
                    "context_length": 32768,
                    "supports_functions": True,
                    "supports_vision": False
                }
            }
        } 