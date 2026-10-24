import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.schemas import ConversationSchema, MessageSchema
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

def _format_conversation(conv) -> Dict[str, Any]:
    messages = []
    for m in conv.messages:
        r_trace = None
        t_calls = None
        if m.reasoning_trace:
            try:
                r_trace = json.loads(m.reasoning_trace)
            except Exception:
                r_trace = m.reasoning_trace
        if m.tool_calls:
            try:
                t_calls = json.loads(m.tool_calls)
            except Exception:
                t_calls = m.tool_calls

        messages.append({
            "id": m.id,
            "conversation_id": m.conversation_id,
            "role": m.role,
            "content": m.content,
            "reasoning_trace": r_trace,
            "tool_calls": t_calls,
            "tokens_used": m.tokens_used,
            "created_at": m.created_at
        })

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": messages
    }

@router.get("/")
async def get_conversations(db: Session = Depends(get_db)):
    """Get all conversations sorted by last update"""
    convs = ConversationService.get_all_conversations(db)
    return [_format_conversation(c) for c in convs]

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get specific conversation with all messages and reasoning traces"""
    conv = ConversationService.get_conversation(db, conversation_id)
    return _format_conversation(conv)

@router.post("/create")
async def create_conversation(db: Session = Depends(get_db)):
    """Create a new empty conversation"""
    conversation = ConversationService.create_conversation(db)
    return _format_conversation(conversation)

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and associated message logs"""
    deleted = ConversationService.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}