from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class MessageSchema(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    reasoning_trace: Optional[Any] = None
    tool_calls: Optional[Any] = None
    tokens_used: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationSchema(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = []

    class Config:
        from_attributes = True

class ChatRequestSchema(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    persona: Optional[str] = "assistant"
    enable_reasoning: bool = True
    enable_tools: bool = True
    image_base64: Optional[str] = None
    audio_base64: Optional[str] = None

class ChatResponseSchema(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    reasoning_trace: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tokens_used: int = 0
    model: str = "meta-llama/Llama-3.2-3B-Instruct"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ToolRunRequest(BaseModel):
    tool_name: str
    params: Dict[str, Any] = {}

class ToolRunResponse(BaseModel):
    tool_name: str
    status: str
    result: Any
    duration_ms: float = 0.0

class MemoryCreateRequest(BaseModel):
    content: str
    category: str = "general"
    metadata: Dict[str, Any] = {}

class MemorySearchRequest(BaseModel):
    query: str
    top_k: int = 4

class MemoryItemSchema(BaseModel):
    id: str
    content: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowCreateRequest(BaseModel):
    title: str
    goal: str
    max_steps: int = 5

class WorkflowResponse(BaseModel):
    id: str
    title: str
    goal: str
    status: str
    plan: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []
    final_output: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MultiAgentRequest(BaseModel):
    task: str
    conversation_id: Optional[str] = None
    agent_roles: List[str] = ["supervisor", "researcher", "coder", "data_analyst", "reviewer"]

class VisionAnalysisRequest(BaseModel):
    prompt: Optional[str] = "Describe what you see in this image in detail and identify key objects."
    image_base64: Optional[str] = None
    image_url: Optional[str] = None

class VoiceTranscriptionRequest(BaseModel):
    audio_base64: str
