from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.schemas import ChatRequestSchema, ChatResponseSchema
from app.services.agent_service import global_agent_service
from app.intelligence.huggingface_llm import HuggingFaceLLMService
from app.utils.logger import logger
from app.utils.errors import InvalidInput

router = APIRouter(prefix="/api/chat", tags=["chat"])
llm_service = HuggingFaceLLMService()

@router.post("/send", response_model=ChatResponseSchema)
async def send_message(
    request: ChatRequestSchema,
    db: Session = Depends(get_db)
):
    """
    Send a message to the autonomous agent.
    Performs prompt engineering, multi-step reasoning (ReAct), tool execution,
    vector memory search, and saves conversation history.
    """
    if not request.message.strip() and not request.image_base64 and not request.audio_base64:
        raise InvalidInput("Message, image, or voice input cannot be empty.")

    try:
        result = global_agent_service.process_chat_message(
            db=db,
            message=request.message,
            conversation_id=request.conversation_id,
            model=request.model,
            persona=request.persona or "assistant",
            enable_reasoning=request.enable_reasoning,
            enable_tools=request.enable_tools,
            image_base64=request.image_base64,
            audio_base64=request.audio_base64
        )

        return ChatResponseSchema(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            response=result["response"],
            reasoning_trace=result.get("reasoning_trace"),
            tool_calls=result.get("tool_calls"),
            tokens_used=result["tokens_used"],
            model=result["model"],
            timestamp=result["timestamp"]
        )

    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_message(
    request: ChatRequestSchema,
    db: Session = Depends(get_db)
):
    """
    Stream agent response and live multi-step reasoning trace using Server-Sent Events (SSE).
    """
    if not request.message.strip():
        raise InvalidInput("Message cannot be empty")

    generator = global_agent_service.stream_chat_message(
        db=db,
        message=request.message,
        conversation_id=request.conversation_id,
        model=request.model,
        persona=request.persona or "assistant"
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/generate-code")
async def generate_code(request: ChatRequestSchema, db: Session = Depends(get_db)):
    """Generate production-ready code with software engineering system prompt"""
    if not request.message.strip():
        raise InvalidInput("Prompt cannot be empty")

    try:
        system_message = (
            "You are a Senior Principal Software Architect. "
            "Generate clean, production-ready, typed, and well-documented code. "
            "Explain non-obvious design choices and format inside markdown blocks."
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": request.message}
        ]
        
        response_data = llm_service.generate_chat_completion(
            messages=messages,
            model=llm_service.settings.HF_CODER_MODEL
        )
        
        return {
            "code": response_data["content"],
            "tokens_used": response_data["tokens_used"],
            "model": response_data["model"],
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error in generate_code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))