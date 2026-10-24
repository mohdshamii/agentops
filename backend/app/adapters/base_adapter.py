from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional

class BaseModelAdapter(ABC):
    """
    Abstract Model Adapter interface.
    Enables modular switching between Hugging Face, OpenAI, and local engines.
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a complete text completion."""
        pass

    @abstractmethod
    def stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream completion tokens as a generator."""
        pass

    @abstractmethod
    def get_supported_models(self) -> List[Dict[str, str]]:
        """Return list of supported model configurations."""
        pass
