"""
Vocalis SaaS Configuration
Environment-based settings management
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Vocalis SaaS"
    DEBUG: bool = True
    
    # Metronome Integration
    METRONOME_API_KEY: Optional[str] = None
    METRONOME_API_URL: str = "https://api.metronome.com/v1"
    METRONOME_RATE_CARD_NAME: str = "Vocalis rate card 2025"
    # Custom pricing unit for Vocalis credits (override in .env if different)
    VOCALIS_CREDIT_TYPE_ID: str = "21984655-5f0c-4161-973e-bdc5d2ecd530"

    # Plans
    METRONOME_PLAN_CREATOR_DOLLARS: int = 49
    METRONOME_PLAN_PRO_DOLLARS: int = 199
    METRONOME_TRIAL_CREDITS: int = 50000
    METRONOME_TRIAL_DAYS: int = 14
    
    # Voice Generation (placeholder for future AI service)
    VOICE_API_KEY: Optional[str] = None
    VOICE_API_URL: str = "https://api.voice-service.com/v1"
    
    # Database (for future use)
    DATABASE_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"

settings = Settings()
