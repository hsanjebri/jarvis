"""
JARVIS Backend Configuration

Manages environment variables and application settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Configuration
    app_name: str = "JARVIS"
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)
    secret_key: str = Field(default="change-me-in-production")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://jarvis:password@localhost:5432/jarvis"
    )
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    
    # AI Services
    claude_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
    
    # Telegram
    telegram_bot_token: str = Field(default="")
    
    # Claude Model Configuration
    claude_model: str = Field(default="claude-sonnet-4-20250514")
    claude_max_tokens: int = Field(default=4096)
    
    # Whisper Configuration
    whisper_model: str = Field(default="whisper-1")
    
    # Google Account (for meeting automation)
    google_account_email: str = Field(default="")
    google_account_password: str = Field(default="")
    
    # Browser Configuration
    browser_headless: bool = Field(default=False)  # Set True for production
    browser_data_dir: str = Field(default="./browser_data")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience instance
settings = get_settings()
