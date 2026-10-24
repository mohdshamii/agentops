import requests
import json
import re
from typing import List, Dict, Any, Generator, Optional
from app.adapters.base_adapter import BaseModelAdapter
from app.config import get_settings
from app.utils.logger import logger

class HuggingFaceAdapter(BaseModelAdapter):
    """
    Modular Adapter for Hugging Face Inference API and Serverless Router.
    """

    MODELS = [
        {"id": "meta-llama/Llama-3.2-3B-Instruct", "name": "LLaMA 3.2 (3B)", "provider": "huggingface"},
        {"id": "mistralai/Mistral-7B-Instruct-v0.3", "name": "Mistral 7B v0.3", "provider": "huggingface"},
        {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen 2.5 (72B)", "provider": "huggingface"},
        {"id": "Qwen/Qwen2.5-Coder-32B-Instruct", "name": "Qwen 2.5 Coder (32B)", "provider": "huggingface"},
        {"id": "deepseek-ai/DeepSeek-R1", "name": "DeepSeek R1", "provider": "huggingface"}
    ]

    def __init__(self, token: Optional[str] = None):
        self.settings = get_settings()
        self.token = token or self.settings.HF_TOKEN
        self.router_url = f"{self.settings.HF_ROUTER_BASE_URL}/chat/completions"
        self.default_model = self.settings.HF_DEFAULT_MODEL

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        target_model = model or self.default_model

        if self.token:
            try:
                payload = {
                    "model": target_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                res = requests.post(self.router_url, headers=self._headers(), json=payload, timeout=40)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", len(content.split()) * 2)
                    return {
                        "content": content,
                        "tokens_used": tokens,
                        "model": target_model,
                        "adapter": "huggingface"
                    }
            except Exception as e:
                logger.warning(f"HuggingFaceAdapter remote call failed: {str(e)}")

        # Fallback local generation if remote is unavailable
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
        result = self.generate(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        text = result.get("content", "")
        chunks = re.split(r'(\s+)', text)
        for chunk in chunks:
            if chunk:
                yield chunk

    def get_supported_models(self) -> List[Dict[str, str]]:
        return self.MODELS
