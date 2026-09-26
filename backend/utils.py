"""
Utility functions for the chatbot backend
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation state and history"""
    
    def __init__(self):
        """Initialize conversation manager"""
        self.conversations: Dict[str, Dict[str, Any]] = {}
    
    def create_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Create a new conversation"""
        self.conversations[conversation_id] = {
            "created_at": datetime.utcnow(),
            "messages": [],
            "user_context": {},
            "status": "active"
        }
        return self.conversations[conversation_id]
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to conversation"""
        if conversation_id not in self.conversations:
            self.create_conversation(conversation_id)
        
        self.conversations[conversation_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_messages(self, conversation_id: str) -> list:
        """Get all messages from a conversation"""
        conv = self.get_conversation(conversation_id)
        return conv["messages"] if conv else []
    
    def clear_messages(self, conversation_id: str) -> None:
        """Clear all messages from a conversation"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["messages"] = []
    
    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    def get_all_conversations(self) -> Dict[str, Dict[str, Any]]:
        """Get all conversations"""
        return self.conversations


class ApprovalManager:
    """Manages human-in-the-loop approvals"""
    
    def __init__(self):
        """Initialize approval manager"""
        self.approvals: Dict[str, Dict[str, Any]] = {}
    
    def create_approval(self, conversation_id: str, action_type: str, message: str) -> None:
        """Create a new approval request"""
        self.approvals[conversation_id] = {
            "action_type": action_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending"
        }
    
    def get_approval(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get approval status"""
        return self.approvals.get(conversation_id)
    
    def approve(self, conversation_id: str) -> None:
        """Approve an action"""
        if conversation_id in self.approvals:
            self.approvals[conversation_id]["status"] = "approved"
            self.approvals[conversation_id]["approved_at"] = datetime.utcnow().isoformat()
    
    def reject(self, conversation_id: str) -> None:
        """Reject an action"""
        if conversation_id in self.approvals:
            self.approvals[conversation_id]["status"] = "rejected"
            self.approvals[conversation_id]["rejected_at"] = datetime.utcnow().isoformat()
    
    def get_pending(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending approvals"""
        return {
            cid: approval 
            for cid, approval in self.approvals.items() 
            if approval["status"] == "pending"
        }


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO format string"""
    return dt.isoformat() if isinstance(dt, datetime) else str(dt)


def extract_entities(text: str) -> Dict[str, Any]:
    """Extract entities from text (simple implementation)"""
    entities = {
        "has_email": "@" in text,
        "has_phone": any(char.isdigit() for char in text),
        "has_currency": "$" in text or "amount" in text.lower(),
        "text_length": len(text),
        "word_count": len(text.split())
    }
    return entities


def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove multiple spaces
    text = " ".join(text.split())
    
    # Limit length
    if len(text) > settings.max_input_length:
        text = text[:settings.max_input_length]
    
    return text


def log_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log an event"""
    logger.info(f"Event: {event_type} - Details: {details}")
