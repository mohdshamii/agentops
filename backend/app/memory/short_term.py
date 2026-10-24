from typing import List, Dict, Any, Optional
from app.utils.logger import logger

class ShortTermMemory:
    """
    Manages short-term conversation context, token budget estimation,
    sliding window pruning, and working memory scratchpad.
    """

    def __init__(self, max_turns: int = 10, max_tokens: int = 2048):
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.scratchpad: Dict[str, Any] = {}

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimator: approximately 1.3 tokens per word"""
        if not text:
            return 0
        return int(len(text.split()) * 1.3) + 1

    def get_pruned_context(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = ""
    ) -> List[Dict[str, str]]:
        """
        Applies sliding window pruning to ensure conversation context fits
        within token budget without dropping system instructions.
        """
        system_tokens = self.estimate_tokens(system_prompt)
        available_budget = max(self.max_tokens - system_tokens - 200, 500)

        pruned: List[Dict[str, str]] = []
        accumulated_tokens = 0

        # Traverse backwards from latest message to preserve recency
        for msg in reversed(messages[-self.max_turns:]):
            msg_tokens = self.estimate_tokens(msg.get("content", ""))
            if accumulated_tokens + msg_tokens > available_budget:
                logger.info("Context limit reached; truncating older messages in short-term buffer")
                break
            pruned.insert(0, msg)
            accumulated_tokens += msg_tokens

        return pruned

    def summarize_older_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Summarizes earlier dialogue when context gets too long.
        """
        if len(messages) <= 4:
            return ""

        summary_lines = []
        for m in messages[:-4]:
            role = m.get("role", "unknown").capitalize()
            content = m.get("content", "")[:100]
            summary_lines.append(f"- {role}: {content}...")

        return "Earlier context summary:\n" + "\n".join(summary_lines)

    # Scratchpad operations for active multi-step reasoning
    def set_scratchpad(self, key: str, value: Any) -> None:
        self.scratchpad[key] = value

    def get_scratchpad(self, key: str, default: Any = None) -> Any:
        return self.scratchpad.get(key, default)

    def clear_scratchpad(self) -> None:
        self.scratchpad.clear()
