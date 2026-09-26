"""
Configuration settings for the chatbot application
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", 8000))
    api_debug: bool = os.getenv("API_DEBUG", "false").lower() == "true"
    
    # LLM Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4")
    model_temperature: float = 0.7
    model_max_tokens: int = 500
    
    # Streamlit Configuration
    streamlit_port: int = int(os.getenv("STREAMLIT_PORT", 8501))
    streamlit_theme: str = "light"
    
    # LangGraph Configuration
    langgraph_debug: bool = os.getenv("LANGGRAPH_DEBUG", "false").lower() == "true"
    langgraph_timeout: int = 60
    
    # Application Settings
    app_name: str = "Chatbot Assistant"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings
