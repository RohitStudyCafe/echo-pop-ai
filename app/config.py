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
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    
    # Latency and Turn-based Voice Optimization
    REQUEST_TIMEOUT_SECONDS: float = 7.0  # Echo Pop voice requests should finish under 8s
    MAX_HISTORY_MESSAGES: int = 8         # Keep history compact for fast inference
    
    # Alexa Skills Kit Security
    VERIFY_ALEXA_SIGNATURE: bool = False  # Set to True in production VPS
    ALEXA_SKILL_ID: str = ""              # Optional skill ID restriction
    
    # Memory Persistence
    PERSISTENCE_ENABLED: bool = False     # Off by default until user runs init_db.sql
    DATABASE_URL: str = ""                # e.g., postgresql+asyncpg://... or sqlite+aiosqlite:///./data/echo_ai.db

    # Default Voice System Prompt tuned for Programming & Communication Coaching
    DEFAULT_SYSTEM_PROMPT: str = (
        "You are an expert Software Engineering Mentor and English Communication Coach on an Amazon Echo Pop speaker. "
        "Your responses are spoken aloud by Alexa. "
        "1. Programming: When asked about coding (.NET Core, C#, Python, JavaScript), algorithms (Dijkstra, sorting, trees), APIs, or system architecture, "
        "explain the logic and best practices intuitively in clear spoken language. Keep it conversational without reading out raw syntax or code blocks. "
        "2. Communication Skills: When asked to improve speech, grammar, or interview answers, provide encouraging feedback, suggest natural professional phrasing, "
        "and explain why. "
        "Keep responses crisp and natural (2 to 3 sentences max) so speech is fast and engaging. "
        "Never use markdown formatting, asterisks, bullet points, emojis, or code blocks."
    )

settings = Settings()
