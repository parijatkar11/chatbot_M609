import config.settings as settings_module
from config.settings import Settings


_PROFILE_ENV = (
    "APP_NAME",
    "APP_VERSION",
    "APP_DESCRIPTION",
    "API_HOST",
    "API_PORT",
    "API_DEBUG",
    "API_LOG_LEVEL",
    "API_BASE_URL",
    "API_CORS_ORIGINS",
    "API_DOCS_ENABLED",
    "API_REQUEST_TIMEOUT",
    "API_STATS_TIMEOUT",
    "API_CUSTOMER_TIMEOUT",
    "MAX_INPUT_LENGTH",
    "OPENAI_API_KEY",
    "MODEL_NAME",
    "MODEL_TEMPERATURE",
    "MODEL_TEMPERATURE_MIN",
    "MODEL_TEMPERATURE_MAX",
    "MODEL_TEMPERATURE_STEP",
    "MODEL_MAX_TOKENS",
    "MODEL_MAX_TOKENS_MIN",
    "MODEL_MAX_TOKENS_MAX",
    "MODEL_MAX_TOKENS_STEP",
    "STREAMLIT_PORT",
    "STREAMLIT_PAGE_TITLE",
    "STREAMLIT_PAGE_ICON",
    "STREAMLIT_LAYOUT",
    "STREAMLIT_SIDEBAR_STATE",
    "STREAMLIT_HIL_ENABLED",
    "STREAMLIT_HIL_TIMEOUT_MIN",
    "STREAMLIT_HIL_TIMEOUT_MAX",
    "STREAMLIT_HIL_TIMEOUT_DEFAULT",
    "STREAMLIT_HIL_TIMEOUT_STEP",
    "LANGGRAPH_DEBUG",
    "LANGGRAPH_TIMEOUT",
)


def test_settings_defaults_to_dev_profile(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    for name in _PROFILE_ENV:
        monkeypatch.delenv(name, raising=False)

    settings = settings_module._load_settings()
    assert settings.app_env == "dev"
    assert settings.app_name == "Mortgage Chatbot (Development)"
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000
    assert settings.api_debug is True
    assert settings.openai_api_key == ""
    assert settings.model_name == "gpt-4"
    assert settings.model_temperature == 0.7
    assert settings.model_max_tokens == 500
    assert settings.streamlit_port == 8501
    assert settings.langgraph_debug is True
    assert settings.langgraph_timeout == 60
    assert settings.app_version == "1.0.0"
    assert settings.resolved_api_base_url == "http://127.0.0.1:8000"
    assert settings.cors_origins == ["http://127.0.0.1:8501", "http://localhost:8501"]


def test_test_and_prod_profiles(monkeypatch):
    for name in _PROFILE_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("APP_ENV", "test")
    test_settings = settings_module._load_settings()
    assert test_settings.app_env == "test"
    assert test_settings.api_port == 8001
    assert test_settings.api_docs_enabled is False
    assert test_settings.model_name == "test-model"
    assert test_settings.streamlit_layout == "centered"
    assert test_settings.langgraph_timeout == 5

    monkeypatch.setenv("APP_ENV", "prod")
    prod_settings = settings_module._load_settings()
    assert prod_settings.app_env == "prod"
    assert prod_settings.api_host == "0.0.0.0"
    assert prod_settings.api_debug is False
    assert prod_settings.api_docs_enabled is False
    assert prod_settings.cors_origins == ["https://your-frontend.example.com"]


def test_process_environment_overrides_selected_profile(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("API_PORT", "8123")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MODEL_NAME", "test-model")
    settings = settings_module._load_settings()
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8123
    assert settings.openai_api_key == "test-key"
    assert settings.model_name == "test-model"
    assert settings.resolved_api_base_url == "http://0.0.0.0:8123"


def test_explicit_api_base_url_and_invalid_profile(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("API_BASE_URL", "https://api.example.test/")
    assert settings_module._load_settings().resolved_api_base_url == "https://api.example.test"

    monkeypatch.setenv("APP_ENV", "staging")
    try:
        settings_module._load_settings()
    except ValueError as error:
        assert "APP_ENV" in str(error)
    else:
        raise AssertionError("Unsupported environment name should fail")


def test_control_slider_configuration_is_validated():
    try:
        Settings(model_temperature=2.5)
    except ValueError as error:
        assert "less than or equal to 2" in str(error)
    else:
        raise AssertionError("Temperature outside supported range should fail")

    try:
        Settings(streamlit_hil_timeout_min=200, streamlit_hil_timeout_default=120)
    except ValueError as error:
        assert "within its configured slider range" in str(error)
    else:
        raise AssertionError("HIL default outside slider range should fail")
