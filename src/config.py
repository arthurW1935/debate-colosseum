from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
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
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "debate_colosseum"

    # Aliases
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.LANGSMITH_API_KEY and not self.LANGCHAIN_API_KEY:
            self.LANGCHAIN_API_KEY = self.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_API_KEY"] = self.LANGSMITH_API_KEY
            
        if self.LANGSMITH_PROJECT:
            self.LANGCHAIN_PROJECT = self.LANGSMITH_PROJECT
            os.environ["LANGCHAIN_PROJECT"] = self.LANGSMITH_PROJECT
            
        if self.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = self.LANGCHAIN_TRACING_V2

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
