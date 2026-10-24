from typing import Dict, Any, List, Optional
from app.adapters.base_adapter import BaseModelAdapter
from app.adapters.huggingface_adapter import HuggingFaceAdapter
from app.adapters.openai_adapter import OpenAIAdapter
from app.adapters.local_adapter import LocalFallbackAdapter

class ModelAdapterFactory:
    """
    Factory providing dynamic selection and instantiation of model adapters.
    """

    _adapters: Dict[str, BaseModelAdapter] = {}

    @classmethod
    def get_adapter(cls, provider: Optional[str] = None, model: Optional[str] = None) -> BaseModelAdapter:
        # Infer provider from model name if not specified
        if not provider and model:
            if "gpt-" in model.lower():
                provider = "openai"
            elif "/" in model:
                provider = "huggingface"
            else:
                provider = "local"
        
        provider = provider or "huggingface"

        if provider not in cls._adapters:
            if provider == "huggingface":
                cls._adapters[provider] = HuggingFaceAdapter()
            elif provider == "openai":
                cls._adapters[provider] = OpenAIAdapter()
            else:
                cls._adapters[provider] = LocalFallbackAdapter()

        return cls._adapters[provider]

    @classmethod
    def list_all_models(cls) -> List[Dict[str, str]]:
        models = []
        models.extend(HuggingFaceAdapter.MODELS)
        models.extend(OpenAIAdapter.MODELS)
        return models
