from typing import Optional, Iterator
import requests
from .base import BaseLLMProvider
import os
import json

class DeepseekProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_base = "https://api.deepseek.com/v1"
        self.default_model = "deepseek/deepseek-r1"  # Updated default model
    
    def generate(self, 
                prompt: str, 
                model: str = None,
                backup_model: Optional[str] = None,
                **kwargs) -> str:
        model = model or self.default_model
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant participating in a business negotiation game."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,  # Added for more strategic responses
                    "max_tokens": 1000,   # Increased for detailed responses
                    **kwargs
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if backup_model:
                return self.generate(prompt, backup_model, None, **kwargs)
            raise e

    def stream(self, 
              prompt: str, 
              model: str = None,
              backup_model: Optional[str] = None,
              **kwargs) -> Iterator[str]:
        model = model or self.default_model
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
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