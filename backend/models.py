"""
Pydantic models for the chatbot application
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Message model"""
    content: str = Field(..., min_length=1, description="Message content")
    role: UserRole = Field(default=UserRole.USER, description="Message role")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class Conversation(BaseModel):
    """Conversation model"""
    id: str = Field(..., description="Unique conversation ID")
    title: Optional[str] = Field(default=None, description="Conversation title")
    messages: List[Message] = Field(default_factory=list, description="Conversation messages")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    message_id: Optional[str] = Field(default=None, description="Message ID")


class GraphState(BaseModel):
    """LangGraph state model"""
    messages: List[Message] = Field(default_factory=list, description="Message history")
    current_node: Optional[str] = Field(default=None, description="Current node in graph")
    context: Optional[dict] = Field(default=None, description="Execution context")
