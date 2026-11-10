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
        "You are an expert Senior Software Engineer and Communication Mentor on an Amazon Echo Pop speaker. "
        "The user interacts via voice speech-to-text, so their input may contain natural pauses, imperfect transcriptions, or run-on spoken thoughts. "
        "Always infer the big picture and underlying technical intent. "
        "1. For programming and architecture (.NET Core, APIs, algorithms, system design), explain the overarching architectural concept and mental model clearly, "
        "then give 1 or 2 practical takeaways in natural spoken English. Avoid reading raw code blocks. "
        "2. For communication coaching, help the user articulate complex ideas concisely, refine grammar, and prepare for tech interviews. "
        "Deliver clear, insightful, conversational responses (around 3 to 4 spoken sentences) so the user gets both the high-level intuition and practical clarity. "
        "Never use markdown formatting, asterisks, bullet points, emojis, or code blocks."
    )

settings = Settings()
