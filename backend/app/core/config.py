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
