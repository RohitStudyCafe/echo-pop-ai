from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AI Provider Defaults
    DEFAULT_PROVIDER: Literal["openai", "gemini"] = "openai"
    
    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # Google Gemini Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Latency and Turn-based Voice Optimization
    REQUEST_TIMEOUT_SECONDS: float = 7.0  # Echo Pop voice requests should finish under 8s
    MAX_HISTORY_MESSAGES: int = 8         # Keep history compact for fast inference
    
    # Alexa Skills Kit Security
    VERIFY_ALEXA_SIGNATURE: bool = False  # Set to True in production VPS
    ALEXA_SKILL_ID: str = ""              # Optional skill ID restriction
    
    # Memory Persistence
    PERSISTENCE_ENABLED: bool = False     # Off by default until user runs init_db.sql
    DATABASE_URL: str = ""                # e.g., postgresql+asyncpg://... or sqlite+aiosqlite:///./data/echo_ai.db

    # Default Voice System Prompt
    DEFAULT_SYSTEM_PROMPT: str = (
        "You are an AI voice assistant running on an Amazon Echo Pop speaker. "
        "Your responses must be spoken aloud by Alexa. "
        "Keep your answers concise, direct, natural, and conversational (typically 1 to 3 sentences). "
        "Never use markdown formatting, bold, italics, bullet points, asterisks, URLs, or code blocks. "
        "Avoid emojis and special punctuation."
    )

settings = Settings()
