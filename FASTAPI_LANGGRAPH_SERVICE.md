# FastAPI LangGraph Service Documentation

## Overview

This is a comprehensive FastAPI service that integrates with LangGraph for managing complex chatbot workflows. The service handles mortgage inquiries with a state machine workflow engine.

## Architecture

### Components

```
Backend Structure:
├── main.py           - FastAPI application with all endpoints
├── graph.py          - LangGraph workflow definitions and state machine
├── models.py         - Pydantic data models
├── utils.py          - Utility functions and managers
├── __init__.py       - Package initialization
└── config/
    └── settings.py   - Application configuration
```

### LangGraph Workflow

The chatbot uses a multi-node workflow:

```
START
  ↓
INPUT_VALIDATION (Validate & sanitize user input)
  ↓
INTENT_CLASSIFICATION (Classify user intent)
  ↓
CONTEXT_RETRIEVAL (Retrieve relevant information)
  ↓
RESPONSE_GENERATION (Generate response)
  ↓
[CONDITIONAL]
├─→ HUMAN_APPROVAL (if action_required=true)
└─→ END (if action_required=false)
```

## API Endpoints

### Chat Endpoints

#### POST /chat
Process a message through the LangGraph workflow.

**Request:**
```json
{
  "message": "What are current mortgage rates?",
  "conversation_id": "conv_abc123",
  "user_context": {}
}
```

**Response:**
```json
{
  "response": "Current mortgage rates are...",
  "conversation_id": "conv_abc123",
  "action_required": false,
  "action_type": "none",
  "nodes_executed": [
    "input_validation",
    "intent_classification",
    "context_retrieval",
    "response_generation"
  ]
}
```

#### POST /conversation/start
Start a new conversation.

**Request:**
```json
{
  "initial_message": "Hello, I'm interested in a mortgage"
}
```

**Response:**
```json
{
  "conversation_id": "conv_abc123",
  "response": "Welcome to the Mortgage Chatbot!",
  "created_at": "2024-01-15T10:30:00"
}
```

#### GET /conversation/{conversation_id}
Get conversation details and history.

**Response:**
```json
{
  "conversation_id": "conv_abc123",
  "created_at": "2024-01-15T10:30:00",
  "message_count": 5,
  "messages": [...],
  "user_context": {}
}
```

#### POST /conversation/{conversation_id}/clear
Clear conversation history.

#### DELETE /conversation/{conversation_id}
Delete an entire conversation.

#### GET /conversations
List all conversations.

### Human In The Loop (HIL) Endpoints

#### GET /approval/pending
Get all pending approvals.

**Response:**
```json
{
  "pending_approvals": [
    {
      "conversation_id": "conv_abc123",
      "action_type": "human_review",
      "message": "Sensitive data requires approval",
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "count": 1
}
```

#### POST /approval/{conversation_id}/approve
Approve a pending action.

#### POST /approval/{conversation_id}/reject
Reject a pending action.

### Graph Management Endpoints

#### GET /graph/structure
Get the LangGraph structure.

**Response:**
```json
{
  "nodes": [
    "input_validation",
    "intent_classification",
    "context_retrieval",
    "response_generation",
    "human_approval"
  ],
  "edges": [
    ["input_validation", "intent_classification"],
    ["intent_classification", "context_retrieval"],
    ["context_retrieval", "response_generation"]
  ],
  "start_node": "input_validation",
  "end_nodes": ["response_generation"],
  "node_descriptions": {
    "input_validation": "Validates and sanitizes user input",
    ...
  }
}
```

#### GET /graph/execution-history/{conversation_id}
Get execution history for a conversation.

#### POST /graph/reset
Reset the graph instance (for testing).

### Health & Statistics Endpoints

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "graph_nodes": 5,
  "conversations": 10,
  "pending_approvals": 2
}
```

#### GET /stats
Get API statistics.

**Response:**
```json
{
  "total_conversations": 10,
  "total_messages": 45,
  "pending_approvals": 2,
  "approved_actions": 5,
  "rejected_actions": 1
}
```

## LangGraph Workflow Nodes

### 1. Input Validation
- Validates user input
- Checks for empty or oversized inputs
- Sanitizes text

### 2. Intent Classification
- Analyzes user message
- Detects intent category:
  - `mortgage_info`: General mortgage information
  - `interest_rates`: Interest rate inquiries
  - `application`: Application inquiries
  - `refinance`: Refinancing questions
  - `payment`: Payment calculations
  - `eligibility`: Qualification questions
  - `general`: Default category

### 3. Context Retrieval
- Gathers relevant information
- Includes:
  - Available mortgage products
  - Current interest rates
  - Conversation history
  - User context data

### 4. Response Generation
- Generates contextual response
- Determines if human approval is needed
- Sets action_type based on response

### 5. Human Approval (Conditional)
- Routes sensitive responses to human reviewers
- Manages approval workflow
- Triggered when:
  - Sensitive keywords detected
  - Complex decisions needed
  - User requests manual review

## Configuration

### Environment Variables

```env
# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
API_DEBUG=false

# LLM Configuration
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-4

# Streamlit Configuration
STREAMLIT_PORT=8501

# LangGraph Configuration
LANGGRAPH_DEBUG=false
LANGGRAPH_TIMEOUT=60
```

### Settings File

See `config/settings.py` for configuration management using Pydantic.

## Running the Service

### Start Backend

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### API Documentation

Access Swagger UI:
```
http://127.0.0.1:8000/api/docs
```

Access ReDoc:
```
http://127.0.0.1:8000/api/redoc
```

## In-Memory Storage

Current implementation uses in-memory storage for:
- Conversations
- Approval queue

**For production, implement:**
- Database storage (PostgreSQL, MongoDB)
- Session persistence
- Message history archival
- Audit logging

## Error Handling

All endpoints include comprehensive error handling:

- **400**: Bad Request - Invalid input
- **404**: Not Found - Resource not found
- **500**: Server Error - Internal server error

## Logging

Logging is configured at the INFO level by default.

Enable debug logging:
```python
# In main.py or via environment
logging.basicConfig(level=logging.DEBUG)
```

## Usage Examples

### Example 1: Simple Chat

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are current mortgage rates?",
    "conversation_id": "conv_123"
  }'
```

### Example 2: Start Conversation with Initial Message

```bash
curl -X POST "http://localhost:8000/conversation/start" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_message": "I am interested in a home loan"
  }'
```

### Example 3: Get Conversation History

```bash
curl "http://localhost:8000/conversation/conv_123"
```

### Example 4: View Graph Structure

```bash
curl "http://localhost:8000/graph/structure"
```

## Testing

### Health Check

```bash
curl "http://localhost:8000/health"
```

### Get Statistics

```bash
curl "http://localhost:8000/stats"
```

## Performance Considerations

- **Timeout**: Requests have 30-second timeout by default
- **Graph Execution**: Optimized for sub-second response times
- **Memory**: In-memory storage suitable for development; use database for production
- **Concurrency**: FastAPI handles multiple concurrent requests

## Future Enhancements

1. **Database Integration**
   - Persistent storage for conversations
   - Audit logging
   - User authentication

2. **Advanced LangGraph Features**
   - Dynamic node creation
   - Custom node types
   - Advanced state management

3. **AI Integration**
   - LangChain integration
   - LLM API calls
   - Embedding-based retrieval

4. **Monitoring**
   - Prometheus metrics
   - OpenTelemetry tracing
   - Performance monitoring

5. **Security**
   - API authentication
   - Rate limiting
   - Input validation enhancements

## Troubleshooting

### Issue: "Cannot connect to backend"
- Ensure backend is running: `uvicorn main:app --reload`
- Check API_HOST and API_PORT in .env

### Issue: Graph execution fails
- Check logs for detailed error messages
- Enable LANGGRAPH_DEBUG=true
- Verify input validation passes

### Issue: Conversations not persisting
- Note: Current implementation uses in-memory storage
- Conversations are lost on server restart
- Implement database storage for persistence

## Support

For issues or questions, refer to:
- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Project README: ../README.md
