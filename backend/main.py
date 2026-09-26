"""
FastAPI Backend for Mortgage Chatbot Application
Handles chat requests and manages LangGraph workflows
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import uuid
from datetime import datetime

from config.settings import settings

# Import the workflow whether the module is loaded as ``backend.main`` or
# directly by Uvicorn from the backend directory.
try:
    from .graph import get_chatbot_graph, reset_graph
except ImportError:
    from graph import get_chatbot_graph, reset_graph

# Configure logging
logging.basicConfig(level=getattr(logging, settings.api_log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=f"{settings.app_name} API",
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/api/docs" if settings.api_docs_enabled else None,
    openapi_url="/api/openapi.json" if settings.api_docs_enabled else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models
# ============================================================================

class Message(BaseModel):
    """Chat message model"""
    content: str = Field(..., min_length=1, max_length=settings.max_input_length, description="Message content")
    user: str = Field(default="user", description="Message sender")
    timestamp: Optional[str] = Field(default=None, description="Message timestamp")


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=settings.max_input_length, description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional user context")


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    action_required: bool = Field(default=False, description="Whether human approval is needed")
    action_type: str = Field(default="none", description="Type of action required")
    nodes_executed: List[str] = Field(default_factory=list, description="Nodes executed in workflow")
    customer_details: Optional[Dict[str, Any]] = Field(default=None, description="Customer details extracted")


class CustomerDetailsModel(BaseModel):
    """Customer details model"""
    account_number: Optional[str] = Field(default=None, description="Customer account number")
    reason_for_contact: Optional[str] = Field(default=None, description="Reason for contact")
    contact_date: Optional[str] = Field(default=None, description="Contact date")
    previous_interactions: List[Dict[str, Any]] = Field(default_factory=list, description="Previous interactions")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Customer preferences")


class InteractionRecord(BaseModel):
    """Interaction record model"""
    timestamp: str = Field(..., description="Interaction timestamp")
    message: str = Field(..., description="User message")
    response: str = Field(..., description="Bot response")
    intent: str = Field(..., description="Detected intent")


class ConversationStart(BaseModel):
    """Start conversation request model"""
    initial_message: Optional[str] = Field(default=None, description="Initial message")


class ConversationInfo(BaseModel):
    """Conversation info model"""
    conversation_id: str = Field(..., description="Conversation ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    message_count: int = Field(default=0, description="Number of messages in conversation")


class GraphStructure(BaseModel):
    """Graph structure model"""
    nodes: List[str] = Field(..., description="List of nodes")
    edges: List[tuple] = Field(..., description="List of edges")
    start_node: str = Field(..., description="Start node")
    end_nodes: List[str] = Field(..., description="End nodes")
    node_descriptions: Dict[str, str] = Field(default_factory=dict, description="Node descriptions")


class ExecutionHistory(BaseModel):
    """Execution history model"""
    conversation_id: str = Field(..., description="Conversation ID")
    nodes_executed: List[str] = Field(..., description="Nodes executed")
    final_state: str = Field(..., description="Final state")
    timestamp: str = Field(..., description="Execution timestamp")


# ============================================================================
# In-Memory Storage (Replace with database in production)
# ============================================================================

conversations: Dict[str, Dict[str, Any]] = {}
approval_queue: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# Helper Functions
# ============================================================================

def generate_conversation_id() -> str:
    """Generate a unique conversation ID"""
    return f"conv_{uuid.uuid4().hex[:8]}"


def get_or_create_conversation(conversation_id: Optional[str] = None) -> str:
    """Get existing or create new conversation"""
    if conversation_id and conversation_id in conversations:
        return conversation_id
    
    new_id = generate_conversation_id()
    conversations[new_id] = {
        "created_at": datetime.utcnow(),
        "messages": [],
        "user_context": {}
    }
    return new_id


# ============================================================================
# API Routes
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": f"{settings.app_name} API",
        "version": settings.app_version,
        "docs": "/api/docs",
        "health": "/health",
        "graph": "/graph/structure"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        graph = get_chatbot_graph()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "graph_nodes": len(graph.graph.get("nodes", {})),
            "conversations": len(conversations),
            "pending_approvals": len(approval_queue)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============================================================================
# Chat Endpoints
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message using LangGraph workflow
    
    Args:
        request: Chat request containing message and optional conversation ID
        
    Returns:
        ChatResponse with assistant response and metadata
    """
    try:
        # Validate input
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get or create conversation
        conversation_id = get_or_create_conversation(request.conversation_id)
        
        # Get LangGraph instance
        graph = get_chatbot_graph()
        
        # Process message through LangGraph workflow
        result = graph.process_message(
            message=request.message,
            conversation_id=conversation_id,
            user_context=request.user_context or {}
        )
        
        # Store message in conversation
        conversations[conversation_id]["messages"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        conversations[conversation_id]["messages"].append({
            "role": "assistant",
            "content": result["response"],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Handle action requirements
        if result.get("action_required"):
            approval_queue[conversation_id] = {
                "action_type": result.get("action_type"),
                "message": result["response"],
                "timestamp": datetime.utcnow().isoformat(),
                "status": "pending"
            }
        
        return ChatResponse(
            response=result["response"],
            conversation_id=conversation_id,
            action_required=result.get("action_required", False),
            action_type=result.get("action_type", "none"),
            nodes_executed=result.get("nodes_executed", []),
            customer_details=result.get("customer_details")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


# ============================================================================
# Conversation Management Endpoints
# ============================================================================

@app.post("/conversation/start", response_model=Dict[str, Any])
async def start_conversation(request: ConversationStart):
    """
    Start a new conversation
    
    Args:
        request: Conversation start request
        
    Returns:
        Conversation ID and initial response
    """
    try:
        conversation_id = get_or_create_conversation()
        
        if request.initial_message:
            graph = get_chatbot_graph()
            result = graph.process_message(
                message=request.initial_message,
                conversation_id=conversation_id
            )
            response = result["response"]
            
            conversations[conversation_id]["messages"].append({
                "role": "user",
                "content": request.initial_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            conversations[conversation_id]["messages"].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            response = f"Welcome to {settings.app_name}! How can I assist you today?"
        
        return {
            "conversation_id": conversation_id,
            "response": response,
            "created_at": conversations[conversation_id]["created_at"].isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting conversation: {str(e)}")


@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation details and history
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Conversation details
    """
    try:
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv = conversations[conversation_id]
        return {
            "conversation_id": conversation_id,
            "created_at": conv["created_at"].isoformat(),
            "message_count": len(conv["messages"]),
            "messages": conv["messages"],
            "user_context": conv["user_context"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")


@app.post("/conversation/{conversation_id}/clear")
async def clear_conversation(conversation_id: str):
    """
    Clear conversation history
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Success message
    """
    try:
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversations[conversation_id]["messages"] = []
        return {"message": "Conversation cleared successfully", "conversation_id": conversation_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")


@app.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Success message
    """
    try:
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        del conversations[conversation_id]
        if conversation_id in approval_queue:
            del approval_queue[conversation_id]
        
        return {"message": "Conversation deleted successfully", "conversation_id": conversation_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")


@app.get("/conversations")
async def list_conversations():
    """
    List all conversations
    
    Returns:
        List of conversation summaries
    """
    try:
        summaries = []
        for conv_id, conv_data in conversations.items():
            summaries.append({
                "conversation_id": conv_id,
                "created_at": conv_data["created_at"].isoformat(),
                "message_count": len(conv_data["messages"])
            })
        return {"conversations": summaries, "total": len(summaries)}
    
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing conversations: {str(e)}")


# ============================================================================
# Human In The Loop (HIL) Endpoints
# ============================================================================

@app.get("/approval/pending")
async def get_pending_approvals():
    """
    Get all pending approvals
    
    Returns:
        List of pending approvals
    """
    try:
        pending = []
        for conv_id, approval in approval_queue.items():
            if approval["status"] == "pending":
                pending.append({
                    "conversation_id": conv_id,
                    "action_type": approval["action_type"],
                    "message": approval["message"],
                    "timestamp": approval["timestamp"]
                })
        return {"pending_approvals": pending, "count": len(pending)}
    
    except Exception as e:
        logger.error(f"Error getting approvals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting approvals: {str(e)}")


@app.post("/approval/{conversation_id}/approve")
async def approve_action(conversation_id: str):
    """
    Approve a pending action
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Success message
    """
    try:
        if conversation_id not in approval_queue:
            raise HTTPException(status_code=404, detail="No pending approval for this conversation")
        
        approval_queue[conversation_id]["status"] = "approved"
        return {
            "message": "Action approved",
            "conversation_id": conversation_id,
            "status": "approved"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error approving action: {str(e)}")


@app.post("/approval/{conversation_id}/reject")
async def reject_action(conversation_id: str):
    """
    Reject a pending action
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Success message
    """
    try:
        if conversation_id not in approval_queue:
            raise HTTPException(status_code=404, detail="No pending approval for this conversation")
        
        approval_queue[conversation_id]["status"] = "rejected"
        return {
            "message": "Action rejected",
            "conversation_id": conversation_id,
            "status": "rejected"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rejecting action: {str(e)}")


# ============================================================================
# Graph Management Endpoints
# ============================================================================

@app.get("/graph/structure", response_model=GraphStructure)
async def get_graph_structure():
    """
    Get LangGraph structure
    
    Returns:
        Graph structure with nodes and edges
    """
    try:
        graph = get_chatbot_graph()
        structure = graph.get_graph_structure()
        return GraphStructure(**structure)
    
    except Exception as e:
        logger.error(f"Error getting graph structure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting graph structure: {str(e)}")


@app.get("/graph/execution-history/{conversation_id}")
async def get_execution_history(conversation_id: str):
    """
    Get execution history for a conversation
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Execution history
    """
    try:
        graph = get_chatbot_graph()
        history = graph.get_execution_history(conversation_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="No execution history found")
        
        return history
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting execution history: {str(e)}")


@app.post("/graph/reset")
async def reset_graph_instance():
    """
    Reset the graph instance (for testing)
    
    Returns:
        Success message
    """
    try:
        reset_graph()
        return {"message": "Graph instance reset successfully"}
    
    except Exception as e:
        logger.error(f"Error resetting graph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resetting graph: {str(e)}")


# ============================================================================
# Customer Memory Endpoints
# ============================================================================

@app.get("/customer/{conversation_id}/details", response_model=CustomerDetailsModel)
async def get_customer_details(conversation_id: str):
    """
    Get customer details for a conversation
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Customer details
    """
    try:
        graph = get_chatbot_graph()
        details = graph.get_customer_details(conversation_id)
        return CustomerDetailsModel(**details)
    
    except Exception as e:
        logger.error(f"Error getting customer details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting customer details: {str(e)}")


@app.get("/customer/{conversation_id}/interactions")
async def get_customer_interactions(conversation_id: str, limit: int = 10):
    """
    Get interaction history for a customer
    
    Args:
        conversation_id: Conversation ID
        limit: Maximum interactions to return
        
    Returns:
        List of interactions
    """
    try:
        graph = get_chatbot_graph()
        interactions = graph.get_customer_interactions(conversation_id, limit=limit)
        return {
            "conversation_id": conversation_id,
            "interactions": interactions,
            "total_count": len(interactions)
        }
    
    except Exception as e:
        logger.error(f"Error getting interactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting interactions: {str(e)}")


@app.get("/customer/{conversation_id}/export")
async def export_customer_data(conversation_id: str):
    """
    Export all customer data for a conversation
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Complete customer data export
    """
    try:
        graph = get_chatbot_graph()
        data = graph.export_customer_data(conversation_id)
        
        if not data:
            raise HTTPException(status_code=404, detail="No customer data found")
        
        return data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting customer data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting customer data: {str(e)}")


@app.delete("/customer/{conversation_id}/clear")
async def clear_customer_data(conversation_id: str):
    """
    Clear all customer data for a conversation
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Success message
    """
    try:
        graph = get_chatbot_graph()
        graph.clear_customer_data(conversation_id)
        return {
            "message": "Customer data cleared successfully",
            "conversation_id": conversation_id
        }
    
    except Exception as e:
        logger.error(f"Error clearing customer data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing customer data: {str(e)}")


@app.get("/customers/all")
async def get_all_customers():
    """
    Get all customer records (admin endpoint)
    
    Returns:
        All customer data
    """
    try:
        graph = get_chatbot_graph()
        customers = graph.get_all_customers()
        return {
            "total_customers": len(customers),
            "customers": customers
        }
    
    except Exception as e:
        logger.error(f"Error getting all customers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting all customers: {str(e)}")


# ============================================================================
# Statistics and Monitoring Endpoints
# ============================================================================

@app.get("/stats")
async def get_statistics():
    """
    Get statistics about the API
    
    Returns:
        Statistics dictionary
    """
    try:
        total_messages = sum(len(conv["messages"]) for conv in conversations.values())
        
        return {
            "total_conversations": len(conversations),
            "total_messages": total_messages,
            "pending_approvals": len([a for a in approval_queue.values() if a["status"] == "pending"]),
            "approved_actions": len([a for a in approval_queue.values() if a["status"] == "approved"]),
            "rejected_actions": len([a for a in approval_queue.values() if a["status"] == "rejected"])
        }
    
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.api_log_level,
    )
