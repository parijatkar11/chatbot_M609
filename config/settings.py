"""Central application settings with dev, test, and production profiles."""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvironmentName = Literal["dev", "test", "prod"]
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Validated configuration shared by the API, graph, and Streamlit UI."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=None,
        protected_namespaces=(),
    )

    app_env: EnvironmentName = "dev"
    app_name: str = "Mortgage Chatbot"
    app_version: str = "1.0.0"
    app_description: str = "Mortgage chatbot powered by FastAPI and LangGraph"

    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_debug: bool = False
    api_log_level: Literal["critical", "error", "warning", "info", "debug", "notset"] = "info"
    api_base_url: str | None = None
    api_cors_origins: str = "http://127.0.0.1:8501,http://localhost:8501"
    api_docs_enabled: bool = True
    api_request_timeout: float = Field(default=30.0, gt=0)
    api_stats_timeout: float = Field(default=10.0, gt=0)
    api_customer_timeout: float = Field(default=5.0, gt=0)
    max_input_length: int = Field(default=5000, gt=0)

    openai_api_key: str = ""
    model_name: str = "gpt-4"
    model_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    model_temperature_min: float = Field(default=0.0, ge=0.0, le=2.0)
    model_temperature_max: float = Field(default=2.0, ge=0.0, le=2.0)
    model_temperature_step: float = Field(default=0.1, gt=0.0)
    model_max_tokens: int = Field(default=500, gt=0)
    model_max_tokens_min: int = Field(default=50, gt=0)
    model_max_tokens_max: int = Field(default=2000, gt=0)
    model_max_tokens_step: int = Field(default=50, gt=0)

    streamlit_port: int = Field(default=8501, ge=1, le=65535)
    streamlit_page_title: str = "Mortgage Chatbot"
    streamlit_page_icon: str = "🏦"
    streamlit_layout: Literal["centered", "wide"] = "wide"
    streamlit_sidebar_state: Literal["auto", "expanded", "collapsed"] = "expanded"
    streamlit_hil_enabled: bool = False
    streamlit_hil_timeout_min: int = Field(default=30, ge=1)
    streamlit_hil_timeout_max: int = Field(default=300, ge=1)
    streamlit_hil_timeout_default: int = Field(default=120, ge=1)
    streamlit_hil_timeout_step: int = Field(default=30, ge=1)

    langgraph_debug: bool = False
    langgraph_timeout: int = Field(default=60, gt=0)

    @model_validator(mode="after")
    def validate_control_ranges(self) -> "Settings":
        """Ensure configured UI defaults fit within their slider bounds."""
        if self.model_temperature_min >= self.model_temperature_max:
            raise ValueError("MODEL_TEMPERATURE_MIN must be less than MODEL_TEMPERATURE_MAX")
        if not self.model_temperature_min <= self.model_temperature <= self.model_temperature_max:
            raise ValueError("MODEL_TEMPERATURE must be within its configured slider range")
        if self.model_max_tokens_min >= self.model_max_tokens_max:
            raise ValueError("MODEL_MAX_TOKENS_MIN must be less than MODEL_MAX_TOKENS_MAX")
        if not self.model_max_tokens_min <= self.model_max_tokens <= self.model_max_tokens_max:
            raise ValueError("MODEL_MAX_TOKENS must be within its configured slider range")
        if self.streamlit_hil_timeout_min > self.streamlit_hil_timeout_max:
            raise ValueError("STREAMLIT_HIL_TIMEOUT_MIN cannot exceed STREAMLIT_HIL_TIMEOUT_MAX")
        if not self.streamlit_hil_timeout_min <= self.streamlit_hil_timeout_default <= self.streamlit_hil_timeout_max:
            raise ValueError("STREAMLIT_HIL_TIMEOUT_DEFAULT must be within its configured slider range")
        return self

    @property
    def resolved_api_base_url(self) -> str:
        """Return an explicit backend URL or derive it from host and port."""
        if self.api_base_url:
            return self.api_base_url.rstrip("/")
        return f"http://{self.api_host}:{self.api_port}"

    @property
    def cors_origins(self) -> list[str]:
        """Parse the comma-separated CORS origin configuration."""
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


def _load_settings() -> Settings:
    """Load the selected profile file, with process environment taking precedence."""
    raw_environment = os.getenv("APP_ENV", "dev").strip().lower()
    if raw_environment not in {"dev", "test", "prod"}:
        raise ValueError("APP_ENV must be one of: dev, test, prod")

    env_file = PROJECT_ROOT / f".env.{raw_environment}"
    return Settings(_env_file=env_file, app_env=raw_environment)


settings = _load_settings()


def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return settings
