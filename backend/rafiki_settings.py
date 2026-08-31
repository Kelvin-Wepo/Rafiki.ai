"""
Configuration management for the eCitizen Voice Assistant.
All sensitive credentials are loaded from environment variables.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import field_validator
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
    # Include the Vite frontend default (5173) and the common React default (3000).
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    
    # Google Gemini API
    GEMINI_API_KEY: str = ""
    # Default to Gemini 2.5 for better reasoning and language detection
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # ElevenLabs Conversational AI
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_AGENT_ID: str = ""
    ELEVENLABS_BRANCH_ID: str = ""
    ELEVENLABS_VOICE_ID: str = "jqcCZkN6Knx8BJ5TBdYR"
    
    # Dialogflow Settings
    DIALOGFLOW_PROJECT_ID: str = ""
    DIALOGFLOW_LANGUAGE_CODE: str = "en"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Africa's Talking SMS
    AFRICASTALKING_USERNAME: str = ""
    AFRICASTALKING_API_KEY: str = ""
    AFRICASTALKING_SENDER_ID: Optional[str] = None
    AFRICASTALKING_VIRTUAL_NUMBER: str = "+254711082025"  # Virtual number for voice calls

    @field_validator("AFRICASTALKING_SENDER_ID", mode="before")
    def coerce_africastalking_sender_id(cls, value):
        if value is None:
            return None
        return str(value).strip()

    # Email/SMTP settings for OTP delivery
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "kelvinwepo7710@gmail.com"
    SMTP_FROM_NAME: str = "Kelvin Wepo"
    EMAIL_ENABLED: bool = False  # Set to True when SMTP is configured

    # OTP/SMS simulation (dev only)
    OTP_SIMULATE: bool = False
    
    # Session Settings
    SESSION_SECRET_KEY: str = "change-this-to-a-secure-random-string"
    SESSION_EXPIRE_MINUTES: int = 60
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # SadTalker Settings
    COLAB_SADTALKER_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    # Voice Settings
    SPEECH_RECOGNITION_LANGUAGE: str = "en-KE"
    TTS_VOICE_ID: int = 1
    TTS_RATE: int = 150
    
    # eCitizen Services
    ECITIZEN_BASE_URL: str = "https://www.ecitizen.go.ke"
    
    # KRA (Kenya Revenue Authority) API
    KRA_API_URL: str = "https://itax.kra.go.ke/api"
    KRA_CLIENT_ID: str = ""
    KRA_CLIENT_SECRET: str = ""
    KRA_API_KEY: Optional[str] = None
    KRA_ENABLED: bool = False
    
    # Paystack Payment Integration (M-PESA)
    PAYSTACK_SECRET_KEY: str = ""
    
    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rafiki"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False  # Set to True for SQL query logging
    
    # Extra fields from .env
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-this-to-a-secure-random-string"
    SESSION_TIMEOUT_MINUTES: int = 30
    
    # RAG System Configuration
    RAG_VECTOR_DB_PATH: str = "./backend/data/chroma_db"
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    GOOGLE_API_KEY: str = ""  # For embeddings (same as Gemini)
    
    @property
    def BASE_DIR(self) -> Path:
        """Get the base directory of the project"""
        return Path(__file__).parent.parent
    
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


# Supported agencies (top-level)
SUPPORTED_AGENCIES = {
    "ntsa": {
        "name": "NTSA",
        "full_name": "National Transport and Safety Authority",
        "description": "Vehicle registration, driving licenses, logbook services",
        "services": ["driving_license", "vehicle_registration", "logbook_search"],
        "contact": "0800 723 473"
    },
    "kra": {
        "name": "KRA",
        "full_name": "Kenya Revenue Authority",
        "description": "Tax services, KRA PIN, nil returns, compliance certificates",
        "services": ["kra_pin", "nil_returns", "tax_compliance"],
        "contact": "0800 724 253"
    },
    "nrb": {
        "name": "NRB",
        "full_name": "National Registration Bureau",
        "description": "National ID cards, ID replacement",
        "services": ["national_id"],
        "contact": "0800 221 199"
    },
    "dcrs": {
        "name": "DCRS",
        "full_name": "Department of Civil Registration Services",
        "description": "Birth certificates, death certificates, marriage certificates",
        "services": ["birth_certificate"],
        "contact": "0800 221 199"
    },
    "brs": {
        "name": "BRS",
        "full_name": "Business Registration Service",
        "description": "Company registration, business names, partnerships",
        "services": ["business_registration"],
        "contact": "0800 221 199"
    },
    "dci": {
        "name": "DCI",
        "full_name": "Directorate of Criminal Investigations",
        "description": "Certificate of Good Conduct, police clearance",
        "services": ["good_conduct"],
        "contact": "0800 722 203"
    },
    "cpb": {
        "name": "Counsellors and Psychologists Board",
        "full_name": "Counsellors and Psychologists Board",
        "description": "Professional licensing for counsellors and psychologists",
        "services": [],
        "contact": "020 271 9510"
    },
    "moh": {
        "name": "Ministry of Health",
        "full_name": "Ministry of Health Services",
        "description": "Health records, medical certifications, facility services",
        "services": ["health_records"],
        "contact": "0800 720 990"
    },
    "county": {
        "name": "County Services",
        "full_name": "County Government Services",
        "description": "Local permits, land rates, county-specific services",
        "services": [],
        "contact": "Varies by county"
    }
}


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
        "morning": "Good morning! I am Rafiki, your AI government assistant. How can I help you today? The supported agencies are NTSA, KRA, National Registration Bureau (NRB), Department of Civil Registration Services (DCRS), Business Registration Service (BRS), Directorate of Criminal Investigations (DCI), Counsellors and Psychologists Board, Ministry of Health services, and County services.",
        "afternoon": "Good afternoon! I am Rafiki, your AI government assistant. How can I help you today? The supported agencies are NTSA, KRA, National Registration Bureau (NRB), Department of Civil Registration Services (DCRS), Business Registration Service (BRS), Directorate of Criminal Investigations (DCI), Counsellors and Psychologists Board, Ministry of Health services, and County services.",
        "evening": "Good evening! I am Rafiki, your AI government assistant. How can I help you today? The supported agencies are NTSA, KRA, National Registration Bureau (NRB), Department of Civil Registration Services (DCRS), Business Registration Service (BRS), Directorate of Criminal Investigations (DCI), Counsellors and Psychologists Board, Ministry of Health services, and County services.",
        "default": "Hi, I am Rafiki your AI government assistant. How can I help you today? The supported agencies are NTSA, KRA, National Registration Bureau (NRB), Department of Civil Registration Services (DCRS), Business Registration Service (BRS), Directorate of Criminal Investigations (DCI), Counsellors and Psychologists Board, Ministry of Health services, and County services."
    },
    "agencies_list": "The supported agencies are: NTSA for transport and driving licenses, KRA for tax services, NRB for National ID, DCRS for birth and death certificates, BRS for business registration, DCI for good conduct certificates, Counsellors and Psychologists Board for professional licensing, Ministry of Health for health services, and County services for local government needs. Which agency would you like to access?",
    "services_list": "I can help you with: booking appointments, managing appointments, checking appointment status, getting directions to Huduma Centres, answering constitutional questions, submitting anonymous feedback, reporting emergencies, and reporting corruption anonymously. What would you like to do?",
    "booking_confirmed": "Your appointment has been successfully booked. You will receive an SMS confirmation shortly.",
    "error_generic": "I apologize, but I encountered an error. Please try again or say 'help' for assistance.",
    "rag_fallback": "I'm unable to retrieve that information right now. Please try again or rephrase your question.",
    "unsupported_agency": "I'm sorry, that agency is not currently supported. The supported agencies are: NTSA, KRA, NRB, DCRS, BRS, DCI, Counsellors and Psychologists Board, Ministry of Health, and County services.",
    "help": "You can say things like: 'Book an appointment with KRA', 'Check my appointment status', 'Directions to nearest Huduma Centre', 'What is the bill of rights?', 'I want to report corruption', or 'Help me with an emergency'. How can I help you?"
}
