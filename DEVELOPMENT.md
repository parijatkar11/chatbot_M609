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

4. **Select a configuration profile**
   Set `APP_ENV` to `dev`, `test`, or `prod`; it defaults to `dev` and loads
   the matching `.env.<profile>` file. Environment variables override the file.
   Provide API keys through local secrets or the deployment secret manager.

## Running the Application

### Terminal 1: Start Backend
```powershell
python -m backend.main
```

**API Documentation**: http://127.0.0.1:8000/docs

### Terminal 2: Start Frontend
```powershell
python run_frontend.py
```

**Application**: http://localhost:<STREAMLIT_PORT> (8501 in dev)

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

```powershell
# Create and activate a virtual environment
uv venv
.venv\Scripts\activate

# Install runtime and test dependencies
uv pip install -r requirements-dev.txt

# Run the suite; pytest.ini enforces at least 90% backend/config coverage
python -m pytest
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
- Check whether the port configured by API_PORT is in use.
- Verify APP_ENV selects the expected profile and API_HOST/API_PORT are valid.

### Frontend can't connect to backend
- Ensure backend is running
- Check API_BASE_URL, or API_HOST and API_PORT, are correct
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
