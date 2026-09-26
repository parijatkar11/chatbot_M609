# FastAPI LangGraph Service - Quick Start Guide

## Overview

This guide helps you quickly set up and run the Mortgage Chatbot with FastAPI backend and LangGraph workflow engine.

## What's New

### FastAPI Service Features
✅ Complete FastAPI service with LangGraph integration
✅ State machine workflow for processing chat messages
✅ Human-in-the-loop (HIL) approval system
✅ Comprehensive API endpoints
✅ In-memory conversation management
✅ Execution tracking and statistics

### LangGraph Workflow
The service includes a 5-node workflow:
1. **Input Validation** - Sanitize and validate user input
2. **Intent Classification** - Detect user intent (mortgage info, rates, application, etc.)
3. **Context Retrieval** - Gather relevant information and products
4. **Response Generation** - Create contextual response
5. **Human Approval** - Route sensitive responses for review

## Quick Start

### 1. Install Dependencies

```bash
cd chatbot_streamlit_fastapi_langgraph
python -m venv venv
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
copy .env.example .env

# Edit .env with your settings (optional for basic testing)
# - OPENAI_API_KEY: Your OpenAI API key (if using LLM features)
# - API_HOST: Backend host (default: 127.0.0.1)
# - API_PORT: Backend port (default: 8000)
```

### 3. Start the FastAPI Backend

```bash
# Terminal 1: Start FastAPI server
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Output should show:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Verify Backend is Running:**
```bash
# In another terminal, test health endpoint
curl http://localhost:8000/health

# Response should show:
# {"status":"healthy",...}
```

### 4. Start the Streamlit Frontend

```bash
# Terminal 2: Start Streamlit app
cd frontend
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## API Documentation

Access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Using the Application

### Via Streamlit Frontend

1. **Open** http://localhost:8501 in your browser
2. **Create New Conversation** - Click "➕ New Conversation" in sidebar
3. **Type Message** - Enter a mortgage-related question
4. **View Response** - See the chatbot response with workflow details
5. **Toggle HIL** - Enable "Human Approval for Actions" in sidebar
6. **View History** - Previous conversations shown in left sidebar

### Via API (cURL/Postman)

#### Send a Chat Message

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are current mortgage rates?",
    "conversation_id": "conv_test1",
    "user_context": {}
  }'
```

#### Start a New Conversation

```bash
curl -X POST "http://localhost:8000/conversation/start" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_message": "I am interested in refinancing my home"
  }'
```

#### Get Conversation History

```bash
curl "http://localhost:8000/conversation/conv_test1"
```

#### View Graph Structure

```bash
curl "http://localhost:8000/graph/structure"
```

#### Get API Statistics

```bash
curl "http://localhost:8000/stats"
```

## Testing Different Intents

Try these example messages to test different workflow paths:

### Mortgage Info
```
"Tell me about your mortgage products"
"What types of loans do you offer?"
```

### Interest Rates
```
"What are your current rates?"
"What's the APR for a 30-year fixed?"
```

### Application
```
"I want to apply for a mortgage"
"How do I start the application process?"
```

### Refinancing
```
"Can I refinance my existing loan?"
"What are the benefits of refinancing?"
```

### Payment Calculation
```
"What would my monthly payment be?"
"How much would I pay per month?"
```

### Eligibility
```
"What do I need to qualify?"
"What are the requirements?"
```

## Understanding Workflow Execution

### Response Structure

Each API response includes:
```json
{
  "response": "The chatbot's response",
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

### Workflow Visualization

In the Streamlit frontend:
1. **Expand "🔍 Workflow Execution Details"**
2. See which nodes were executed for each message
3. View the action type if approval was needed

## Human-In-The-Loop (HIL) Features

### Enable HIL Mode

1. In Streamlit sidebar, check "Enable Human Approval for Actions"
2. Set approval timeout (30-300 seconds)
3. Messages containing sensitive keywords trigger approval

### Approve/Reject Actions

When an action requires approval:
1. ⏳ Status shows "Awaiting Human Approval"
2. Click ✅ **Approve** to proceed
3. Click ❌ **Reject** to cancel

### Check Pending Approvals (API)

```bash
curl "http://localhost:8000/approval/pending"
```

## Project File Structure

```
chatbot_streamlit_fastapi_langgraph/
├── backend/
│   ├── main.py                    # FastAPI application with endpoints
│   ├── graph.py                   # LangGraph workflow definitions
│   ├── models.py                  # Pydantic models
│   ├── utils.py                   # Utility functions
│   └── __init__.py
├── frontend/
│   └── app.py                     # Streamlit UI
├── config/
│   └── settings.py                # Configuration management
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── README.md                      # Main documentation
├── DEVELOPMENT.md                 # Development guide
└── FASTAPI_LANGGRAPH_SERVICE.md  # API documentation
```

## Key Files and Their Purpose

### `backend/main.py`
- FastAPI application with all API endpoints
- Conversation management
- HIL approval system
- Statistics and monitoring

### `backend/graph.py`
- LangGraph workflow implementation
- 5-node state machine
- Intent classification logic
- Response generation

### `backend/models.py`
- Pydantic data models
- Type definitions
- Validation schemas

### `backend/utils.py`
- ConversationManager class
- ApprovalManager class
- Utility functions

### `frontend/app.py`
- Streamlit UI
- Chat interface
- Conversation history
- Workflow execution display

## Stopping the Services

### Stop Streamlit
Press Ctrl+C in the Streamlit terminal

### Stop FastAPI
Press Ctrl+C in the uvicorn terminal

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -an | findstr :8000

# Use different port
uvicorn main:app --host 127.0.0.1 --port 8001
```

### Streamlit can't connect to API
- Verify backend is running on correct host/port
- Check .env file for correct API_HOST and API_PORT
- Test with: `curl http://localhost:8000/health`

### Import errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Pydantic errors
```bash
# Ensure pydantic-settings is installed
pip install pydantic-settings
```

## Next Steps

1. **Explore API Endpoints** - Visit http://localhost:8000/api/docs
2. **Test Different Intents** - Try various mortgage-related questions
3. **Enable HIL Mode** - Test human approval workflow
4. **Review Workflow Details** - Expand workflow execution in Streamlit
5. **Check Statistics** - Monitor conversations and approvals

## Advanced Usage

### Enable Debug Mode

```bash
# Set environment variable
set LANGGRAPH_DEBUG=true

# Start backend
uvicorn main:app --reload
```

### Add Custom Intents

Edit `backend/graph.py` in the `_classify_intent()` method:
```python
intents = {
    "your_new_intent": ["keyword1", "keyword2"],
    # ... existing intents
}
```

### Extend Workflow

Add new nodes by modifying `backend/graph.py`:
1. Define new node handler method
2. Add node to graph["nodes"]
3. Define edges for the new node

### Use with Database

Replace in-memory storage in `backend/main.py`:
- Implement PostgreSQL, MongoDB, or other database
- Replace conversations dict with database queries
- Update ApprovalManager for persistence

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Full API Documentation](FASTAPI_LANGGRAPH_SERVICE.md)

## Support & Feedback

For issues:
1. Check logs in terminal output
2. Enable debug mode for detailed information
3. Review FASTAPI_LANGGRAPH_SERVICE.md for API details
4. Check DEVELOPMENT.md for development guidance

---

**Ready to use!** Start with Step 1: Install Dependencies above.
