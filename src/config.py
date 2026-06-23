from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

# Load all .env variables into os.environ globally so tools can access them
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

class Settings(BaseSettings):
    LLM_PROVIDER: str = "openai" # anthropic, openai, google_vertex_ai, google_genai
    LLM_MODEL: str = "gpt-4o-mini"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    
    # LangSmith Tracing
    LANGSMITH_TRACING: str = "true"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "debate_colosseum"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Map user's LANGSMITH_* to LangChain's expected OS env vars
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
    temperature: float = 0.0
) -> BaseChatModel:
    """LLM Factory using LangChain's init_chat_model.
    
    Supports:
        - openai
        - anthropic
        - google_vertex_ai
        - google_genai
    """
    _provider = provider or settings.LLM_PROVIDER
    _model = model or settings.LLM_MODEL
    
    return init_chat_model(
        model=_model,
        model_provider=_provider,
        temperature=temperature
    )
