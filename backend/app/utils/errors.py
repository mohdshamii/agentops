from fastapi import HTTPException

class AppBaseException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class InvalidInput(AppBaseException):
    def __init__(self, detail: str = "Invalid input provided"):
        super().__init__(status_code=400, detail=detail)

class ConversationNotFound(AppBaseException):
    def __init__(self, detail: str = "Conversation not found"):
        super().__init__(status_code=404, detail=detail)

class ToolExecutionError(AppBaseException):
    def __init__(self, detail: str = "Failed to execute tool"):
        super().__init__(status_code=500, detail=detail)

class LLMServiceException(AppBaseException):
    def __init__(self, detail: str = "LLM inference failure"):
        super().__init__(status_code=502, detail=detail)

class MemoryException(AppBaseException):
    def __init__(self, detail: str = "Memory operation failed"):
        super().__init__(status_code=500, detail=detail)

# Backward compatibility alias
OpenAIException = LLMServiceException
