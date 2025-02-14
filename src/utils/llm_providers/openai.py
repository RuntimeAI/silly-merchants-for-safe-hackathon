from typing import Optional, List, Dict, Any
from openai import OpenAI
from ..config.settings import settings

class LLMProvider:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": settings.SITE_URL,
                "X-Title": settings.SITE_NAME,
            }
        )
    
    def generate(
        self,
        prompt: str,
        model: str,
        backup_model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        try:
            return self._call_model(prompt, model, temperature, max_tokens)
        except Exception as e:
            if backup_model:
                return self._call_model(prompt, backup_model, temperature, max_tokens)
            raise e
    
    def _call_model(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return completion.choices[0].message.content

    def _create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content 