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

Choose a profile with `APP_ENV=dev`, `APP_ENV=test`, or `APP_ENV=prod`.
The default is `dev`; settings are loaded from `.env.dev`, `.env.test`, or
`.env.prod`. Process environment variables override values in those files.
The profile files contain no credentials. Supply `OPENAI_API_KEY` using a
local, untracked secret or your deployment's secret manager.

```powershell
# Optional: dev is the default
$env:APP_ENV = "dev"
```

## Running the Application

### Start Backend (FastAPI)

```powershell
python -m backend.main
```

The API will be available at the configured API host and port.
API documentation (when enabled): `/api/docs`

### Start Frontend (Streamlit)

In a new terminal:

```powershell
python run_frontend.py
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

See `.env.example` for the full setting list. The profile files configure API
host/port, CORS, docs, logging, request limits/timeouts, model parameters,
Streamlit appearance/port, approval controls, and LangGraph behavior.

## License

MIT
