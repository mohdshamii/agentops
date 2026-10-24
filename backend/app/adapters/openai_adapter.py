import os
import requests
import re
from typing import List, Dict, Any, Generator, Optional
from app.adapters.base_adapter import BaseModelAdapter
from app.config import get_settings
from app.utils.logger import logger

class OpenAIAdapter(BaseModelAdapter):
    """
    Modular Adapter for OpenAI and OpenAI-compatible API providers.
    """

    MODELS = [
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"}
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        target_model = model or "gpt-4o"
        if not self.api_key:
            from app.adapters.local_adapter import LocalFallbackAdapter
            return LocalFallbackAdapter().generate(messages, model=target_model, temperature=temperature, max_tokens=max_tokens)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            res = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                    "model": target_model,
                    "adapter": "openai"
                }
        except Exception as e:
            logger.error(f"OpenAIAdapter failed: {str(e)}")

        from app.adapters.local_adapter import LocalFallbackAdapter
        return LocalFallbackAdapter().generate(messages, model=target_model, temperature=temperature, max_tokens=max_tokens)

    def stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Generator[str, None, None]:
        res = self.generate(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        text = res.get("content", "")
        for word in re.split(r'(\s+)', text):
            if word:
                yield word

    def get_supported_models(self) -> List[Dict[str, str]]:
        return self.MODELS
