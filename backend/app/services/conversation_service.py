import uuid
import json
from sqlalchemy.orm import Session
from app.models import Conversation, Message
from app.utils.logger import logger
from app.utils.errors import ConversationNotFound
from datetime import datetime
from typing import List, Dict, Any, Optional

class ConversationService:
    @staticmethod
    def create_conversation(db: Session, title: str = "New Conversation") -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        logger.info(f"Created conversation: {conversation.id}")
        return conversation
    
    @staticmethod
    def get_conversation(db: Session, conversation_id: str) -> Conversation:
        """Get conversation by ID"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ConversationNotFound(f"Conversation {conversation_id} not found")
        return conversation
    
    @staticmethod
    def add_message(
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        tokens_used: int = 0,
        reasoning_trace: Optional[List[Dict[str, Any]]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        """Add message to conversation with optional reasoning trace and tool logs"""
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            reasoning_trace=json.dumps(reasoning_trace) if reasoning_trace else None,
            tool_calls=json.dumps(tool_calls) if tool_calls else None
        )
        db.add(message)
        
        # Update conversation updated_at
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        logger.info(f"Added message {message.id} ({role}) to conversation {conversation_id}")
        return message
    
    @staticmethod
    def get_all_conversations(db: Session) -> List[Conversation]:
        """Get all conversations sorted by latest update"""
        return db.query(Conversation).order_by(
            Conversation.updated_at.desc()
        ).all()
    
    @staticmethod
    def delete_conversation(db: Session, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            db.delete(conversation)
            db.commit()
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False
    
    @staticmethod
    def get_conversation_history(db: Session, conversation_id: str) -> List[Dict[str, str]]:
        """Get message history for conversation as role/content list"""
        conversation = ConversationService.get_conversation(db, conversation_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages
        ]