"""
Configuration management for the eCitizen Voice Assistant.
All sensitive credentials are loaded from environment variables.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

# Get the path to the .env file (in parent directory)
ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Settings
    APP_NAME: str = "eCitizen Voice Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Google Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # ElevenLabs Conversational AI
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_AGENT_ID: str = "agent_7901kbqbewwcf1avres326fjahdb"
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice (default)
    
    # Dialogflow Settings
    DIALOGFLOW_PROJECT_ID: str = ""
    DIALOGFLOW_LANGUAGE_CODE: str = "en"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Africa's Talking SMS
    AFRICASTALKING_USERNAME: str = ""
    AFRICASTALKING_API_KEY: str = ""
    AFRICASTALKING_SENDER_ID: Optional[str] = None
    
    # Session Settings
    SESSION_SECRET_KEY: str = "change-this-to-a-secure-random-string"
    SESSION_EXPIRE_MINUTES: int = 60
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    # Voice Settings
    SPEECH_RECOGNITION_LANGUAGE: str = "en-KE"
    TTS_VOICE_ID: int = 1
    TTS_RATE: int = 150
    
    # eCitizen Services
    ECITIZEN_BASE_URL: str = "https://www.ecitizen.go.ke"
    
    # Extra fields from .env
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-this-to-a-secure-random-string"
    DATABASE_URL: str = "sqlite:///./ecitizen.db"
    SESSION_TIMEOUT_MINUTES: int = 30
    
    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Available government services
GOVERNMENT_SERVICES = {
    "passport": {
        "name": "Passport Application",
        "description": "Apply for a new Kenyan passport or renew an existing one",
        "department": "Immigration Department",
        "time_slots": ["08:00-12:00", "14:00-17:00"],
        "requirements": [
            "National ID card",
            "Birth certificate",
            "2 passport photos",
            "Application fee payment receipt"
        ],
        "ecitizen_url": "/immigration/passport"
    },
    "national_id": {
        "name": "National ID Application",
        "description": "Apply for a new national identification card",
        "department": "National Registration Bureau",
        "time_slots": ["08:00-12:00", "14:00-17:00"],
        "requirements": [
            "Birth certificate",
            "Notification of birth",
            "School leaving certificate",
            "2 passport photos"
        ],
        "ecitizen_url": "/nrb/id-application"
    },
    "driving_license": {
        "name": "Driving License",
        "description": "Apply for or renew a driving license",
        "department": "NTSA",
        "time_slots": ["08:00-12:00", "14:00-17:00"],
        "requirements": [
            "National ID card",
            "Medical certificate",
            "Driving school certificate",
            "2 passport photos"
        ],
        "ecitizen_url": "/ntsa/driving-license"
    },
    "good_conduct": {
        "name": "Certificate of Good Conduct",
        "description": "Apply for a police clearance certificate",
        "department": "Directorate of Criminal Investigations",
        "time_slots": ["08:00-12:00", "14:00-17:00"],
        "requirements": [
            "National ID card",
            "2 passport photos",
            "Fingerprint capture"
        ],
        "ecitizen_url": "/dci/good-conduct"
    }
}

# Assistant responses for accessibility
ASSISTANT_RESPONSES = {
    "greeting": {
        "morning": "Good morning! I am Wanjiku, your eCitizen booking assistant. I am here to help you access government services. How may I assist you today?",
        "afternoon": "Good afternoon! I am Wanjiku, your eCitizen booking assistant. I am here to help you access government services. How may I assist you today?",
        "evening": "Good evening! I am Wanjiku, your eCitizen booking assistant. I am here to help you access government services. How may I assist you today?"
    },
    "services_list": "I can help you with the following services: Passport application, National ID application, Driving license, and Certificate of Good Conduct. Which service would you like to access?",
    "booking_confirmed": "Your appointment has been successfully booked. You will receive an SMS confirmation shortly.",
    "error_generic": "I apologize, but I encountered an error. Please try again or say 'help' for assistance.",
    "help": "You can say things like: 'Book a passport appointment', 'Check my appointment status', 'What services are available', or 'Navigate to eCitizen'. How can I help you?"
}
