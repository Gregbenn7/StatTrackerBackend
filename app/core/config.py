"""Application configuration using pydantic-settings."""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Baseball League Stat Tracker"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = ""
    
    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:8080"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

