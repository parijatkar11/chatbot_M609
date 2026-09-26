# Development Guide

## Getting Started

### Prerequisites
- Python 3.9+
- pip or poetry
- Git

### Initial Setup

1. **Clone or navigate to the project**
   ```bash
   cd chatbot_streamlit_fastapi_langgraph
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Running the Application

### Terminal 1: Start Backend
```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**API Documentation**: http://127.0.0.1:8000/docs

### Terminal 2: Start Frontend
```bash
cd frontend
streamlit run app.py
```

**Application**: http://localhost:8501

## Project Structure

### Backend
- `main.py` - FastAPI application entry point
- `models.py` - Pydantic data models
- `graph.py` - LangGraph workflow definitions

### Frontend
- `app.py` - Streamlit application

### Config
- `settings.py` - Application configuration

## Development Workflow

### Adding Features

1. **Backend Enhancement**
   - Add new routes in `backend/main.py`
   - Define models in `backend/models.py`
   - Update LangGraph in `backend/graph.py`

2. **Frontend Enhancement**
   - Modify `frontend/app.py`
   - Streamlit auto-refreshes on changes

3. **Update Dependencies**
   ```bash
   pip install <new-package>
   pip freeze > requirements.txt
   ```

## Testing

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with coverage
pytest --cov=backend
```

## Debugging

### Backend
- Check terminal output for FastAPI errors
- Use `--reload` flag for auto-reload
- Access Swagger UI at http://127.0.0.1:8000/docs

### Frontend
- Check Streamlit terminal for errors
- Use `st.write()` for debugging
- Check browser console for JavaScript errors

## Common Issues

### Backend won't start
- Check if port 8000 is in use: `netstat -an | find ":8000"`
- Verify API_HOST and API_PORT in .env

### Frontend can't connect to backend
- Ensure backend is running
- Check API_HOST and API_PORT are correct
- Verify no firewall blocking localhost

### Dependencies issues
- Delete venv and recreate
- Update pip: `pip install --upgrade pip`
- Reinstall: `pip install -r requirements.txt`

## Code Style

- Use type hints for all functions
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions and classes

## Contributing

1. Create a new branch for features
2. Make changes with clear commits
3. Test before submitting
4. Update documentation

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
