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
    METRONOME_API_URL: str = "https://api.metronome.com"
    # Set in root .env; no in-code default to avoid ambiguity
    METRONOME_RATE_CARD_NAME: Optional[str] = None
    # Custom pricing unit for Vocalis credits (override in .env if different)
    VOCALIS_CREDIT_TYPE_ID: str = "21984655-5f0c-4161-973e-bdc5d2ecd530"

    # Plans
    METRONOME_PLAN_CREATOR_DOLLARS: int = 49
    METRONOME_PLAN_PRO_DOLLARS: int = 199
    METRONOME_TRIAL_CREDITS: int = 50000
    METRONOME_TRIAL_DAYS: int = 14

    # Email (MailHog by default for demo)
    EMAIL_PROVIDER: str = "smtp"  # "smtp" | "resend"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    EMAIL_FROM: str = "hello@vocalis.ai"
    DEMO_EMAIL_TO: str | None = None
    RESEND_API_KEY: Optional[str] = None
    DASHBOARD_URL: str = "http://localhost:8000/dashboard"
    DOCS_URL: str = "https://docs.vocalis.ai"
    SEND_WELCOME_ON_PLAN_SELECT: bool = False
    
    # Voice Generation (placeholder for future AI service)
    VOICE_API_KEY: Optional[str] = None
    VOICE_API_URL: str = "https://api.voice-service.com/v1"
    
    # Database (for future use)
    DATABASE_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Webhooks
    METRONOME_WEBHOOK_SECRET: Optional[str] = None
    
    class Config:
        # Load env from the project root (../.env) when running with CWD=backend
        env_file = "../.env"

settings = Settings()
