from fastapi import APIRouter
from app.config import get_settings
from app.intelligence.huggingface_llm import HuggingFaceLLMService
from app.tools.registry import global_tool_registry
from app.memory.memory_manager import global_memory_manager

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """System health check and agent capabilities discovery"""
    settings = get_settings()
    llm = HuggingFaceLLMService()
    
    return {
        "status": "healthy",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "models": {
            "default": settings.HF_DEFAULT_MODEL,
            "coder": settings.HF_CODER_MODEL,
            "reasoning": settings.HF_REASONING_MODEL,
            "embedding": settings.HF_EMBEDDING_MODEL,
            "vision": settings.HF_VISION_MODEL,
            "audio": settings.HF_AUDIO_MODEL,
            "available_models": llm.AVAILABLE_MODELS
        },
        "capabilities": {
            "hugging_face_router": bool(settings.HF_TOKEN),
            "multi_step_reasoning": True,
            "tools_enabled": len(global_tool_registry.list_tools()),
            "vector_memory": True,
            "multi_agent_team": True,
            "autonomous_workflows": True,
            "voice_and_vision": True
        }
    }
