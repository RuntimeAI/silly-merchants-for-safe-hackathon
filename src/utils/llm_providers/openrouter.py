from typing import Optional, Iterator, List, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .base import BaseLLMProvider
import os
import json
import logging
from datetime import datetime
import re
import time
from ..config import Config

class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        config = Config()
        self.api_key = api_key or config.get_api_key('openrouter')
        self.api_base = "https://openrouter.ai/api/v1"
        
        # Get default model config from player1 (since it's using Gemini)
        model_config = config.llm_config['models']['player1']
        self.default_model = model_config['default']
        self.backup_model = model_config.get('backup')
        self.default_max_tokens = model_config.get('max_tokens', 1024)
        self.default_temperature = model_config.get('temperature', 0.7)
        
        # Setup session with retry logic
        self.session = self._setup_session()
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get provider configuration"""
        return {
            "name": "openrouter",
            "models": {
                "gemini-pro": {
                    "id": "google/gemini-pro",
                    "context_length": 32768,
                    "supports_functions": True
                },
                "gpt-4": {
                    "id": "openai/gpt-4",
                    "context_length": 8192,
                    "supports_functions": True
                },
                "claude-2": {
                    "id": "anthropic/claude-2",
                    "context_length": 100000,
                    "supports_functions": True
                }
            }
        }
    
    def _setup_session(self):
        """Setup requests session with retry logic"""
        session = requests.Session()
        
        # Define retry strategy
        retries = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[408, 429, 500, 502, 503, 504],  # retry on these status codes
            allowed_methods=["POST"]
        )
        
        # Add retry adapter to session
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list] = None,
    ) -> str:
        """Generate text using OpenRouter"""
        try:
            # For Gemini, combine system prompt with user prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser Request: {prompt}"
            else:
                full_prompt = prompt
            
            messages = [{"role": "user", "content": full_prompt}]
            
            response = self.session.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "AI Agents Negotiation Game"
                },
                json={
                    "model": self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or self.default_max_tokens,
                    "stop": stop,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            
            # Additional JSON validation
            try:
                return json.dumps(json.loads(content))  # Normalize JSON format
            except json.JSONDecodeError:
                return json.dumps({
                    "thinking": "Error: Could not parse response",
                    "message": "I apologize, but I'm having trouble formulating my response.",
                    "transfers": []
                })
                
        except Exception as e:
            logger.error(f"OpenRouter generation error: {str(e)}")
            return json.dumps({
                "message": f"Error: {str(e)}",
                "transfers": []
            })

    def _extract_thinking_points(self, prompt: str) -> List[str]:
        """Extract key thinking points from the prompt"""
        points = []
        
        # Extract current game state
        if "Current round:" in prompt:
            round_info = re.search(r"Current round: (\d+) of \d+", prompt)
            if round_info:
                points.append(f"Round {round_info.group(1)}")
        
        # Extract coin information
        if "Your coins:" in prompt:
            coins_info = re.search(r"Your coins: (\d+)", prompt)
            if coins_info:
                points.append(f"Has {coins_info.group(1)} coins")
        
        # Extract recent actions if any
        if "Recent conversation:" in prompt:
            points.append("Analyzing recent conversations...")
        
        if "Recent transfers:" in prompt:
            points.append("Reviewing recent transfers...")
        
        # Add strategic considerations
        if "Consider forming alliances" in prompt:
            points.append("Evaluating potential alliances...")
        
        if "transfers" in prompt.lower():
            points.append("Calculating possible transfers...")
        
        return points

    def stream(self, 
              prompt: str, 
              model: str = None,
              backup_model: Optional[str] = None,
              **kwargs) -> Iterator[str]:
        model = model or self.default_model
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "AI Agents Negotiation Game"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant participating in a business negotiation game."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    **kwargs
                },
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode())
                    if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                        yield chunk["choices"][0]["delta"]["content"]
        except Exception as e:
            if backup_model:
                yield from self.stream(prompt, backup_model, None, **kwargs)
            raise e 