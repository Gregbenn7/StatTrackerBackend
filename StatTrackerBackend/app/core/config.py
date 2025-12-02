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
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 1500
    OPENAI_TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate_openai_key(self) -> bool:
        """Check if OpenAI key is configured."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.startswith('sk-'))


# Global settings instance
settings = Settings()

# Validate on startup
if not settings.validate_openai_key():
    print("\n" + "="*60)
    print("WARNING: OPENAI_API_KEY not properly configured!")
    print("Game recap features will not work.")
    print("Please set OPENAI_API_KEY in your .env file.")
    print("="*60 + "\n")
else:
    print("✓ OpenAI API key configured successfully")

