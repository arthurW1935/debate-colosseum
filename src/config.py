from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
import logging
from dotenv import load_dotenv

# Load all .env variables into os.environ globally so tools can access them
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    LLM_PROVIDER: str = "anthropic"
    LLM_MODEL: str = "claude-sonnet-4-6"

    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    # Google Auth & JWT
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 168
    FRONTEND_URL: str = "http://localhost:3000"
    API_BASE_URL: str = "http://localhost:8000"

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 15
    RATE_LIMIT_RUNS_PER_HOUR: int = 5

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # External action
    SLACK_WEBHOOK_URL: Optional[str] = None

    # LangSmith Tracing
    LANGSMITH_TRACING: str = "true"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "debate-colosseum"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Map LANGSMITH_* vars to LangChain's expected OS env vars so LangGraph
        # nodes are automatically traced without per-node setup.
        if self.LANGSMITH_API_KEY:
            os.environ["LANGCHAIN_API_KEY"] = self.LANGSMITH_API_KEY
        if self.LANGSMITH_PROJECT:
            os.environ["LANGCHAIN_PROJECT"] = self.LANGSMITH_PROJECT
        if self.LANGSMITH_ENDPOINT:
            os.environ["LANGCHAIN_ENDPOINT"] = self.LANGSMITH_ENDPOINT
        if self.LANGSMITH_TRACING:
            os.environ["LANGCHAIN_TRACING_V2"] = self.LANGSMITH_TRACING


settings = Settings()


def get_chat_model(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> BaseChatModel:
    """Return an LLM instance via LangChain's init_chat_model.

    Supports: anthropic, openai, google_vertex_ai, google_genai.
    Defaults come from Settings so .env drives model choice.
    """
    _provider = provider or settings.LLM_PROVIDER
    _model = model or settings.LLM_MODEL
    return init_chat_model(model=_model, model_provider=_provider, temperature=temperature, timeout=90)
