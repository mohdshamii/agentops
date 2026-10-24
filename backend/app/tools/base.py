from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseTool(ABC):
    """
    Abstract Base Class for all Agent Tools.
    Every tool must define a name, description, parameters schema, and execute method.
    """
    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Executes the tool logic with provided keyword arguments"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Returns tool schema definition for LLM tool injection"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

    def format_description_for_prompt(self) -> str:
        """Formats the tool into a clean string for system prompt injection"""
        params_str = ", ".join([f"{k}: {v.get('type', 'any')} ({v.get('description', '')})" for k, v in self.parameters.get("properties", {}).items()])
        return f"- **{self.name}**: {self.description}\n  Parameters: {{{params_str}}}"
