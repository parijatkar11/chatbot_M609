# Chatbot using Streamlit, FastAPI, and LangGraph

A modern chatbot application that combines the power of Streamlit for the frontend, FastAPI for the backend, and LangGraph for managing AI workflows.

## Project Structure

```
chatbot_streamlit_fastapi_langgraph/
├── backend/           # FastAPI backend
│   ├── main.py       # FastAPI application
│   ├── models.py     # Data models
│   └── graph.py      # LangGraph definitions
├── frontend/         # Streamlit frontend
│   └── app.py        # Streamlit application
├── config/           # Configuration files
│   └── settings.py   # Application settings
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variables template
└── README.md        # This file
```

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys and configuration
```

## Running the Application

### Start Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`
API documentation: `http://127.0.0.1:8000/docs`

### Start Frontend (Streamlit)

In a new terminal:

```bash
cd frontend
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Features

- **FastAPI Backend**: RESTful API for chatbot operations
- **Streamlit Frontend**: Interactive web interface
- **LangGraph**: Workflow management for AI agents
- **Real-time Chat**: Streaming responses

## Development

### Backend Development

- Edit files in `backend/` directory
- FastAPI auto-reloads with `--reload` flag
- View API docs at `http://127.0.0.1:8000/docs`

### Frontend Development

- Streamlit auto-refreshes on file changes
- Check the terminal for any errors

## Environment Variables

See `.env.example` for required environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `API_HOST`: Backend API host
- `API_PORT`: Backend API port
- `MODEL_NAME`: LLM model to use

## License

MIT
