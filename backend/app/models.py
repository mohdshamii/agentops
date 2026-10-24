from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), index=True)
    role = Column(String)  # "user", "assistant", "system", "tool"
    content = Column(Text)
    reasoning_trace = Column(Text, nullable=True)  # JSON-encoded multi-step reasoning steps
    tool_calls = Column(Text, nullable=True)       # JSON-encoded tool calls and results
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

class MemoryItem(Base):
    __tablename__ = "memories"
    
    id = Column(String, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    category = Column(String, default="general")  # "user_fact", "preference", "agent_experience", "system"
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkflowExecution(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String, default="pending")  # "pending", "running", "completed", "failed"
    plan_json = Column(Text, default="[]")       # List of plan steps
    results_json = Column(Text, default="[]")    # Step results
    final_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ToolExecutionLog(Base):
    __tablename__ = "tool_logs"
    
    id = Column(String, primary_key=True, index=True)
    tool_name = Column(String, nullable=False, index=True)
    input_params = Column(Text, default="{}")
    output_result = Column(Text, default="")
    status = Column(String, default="success")  # "success", "error"
    duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)