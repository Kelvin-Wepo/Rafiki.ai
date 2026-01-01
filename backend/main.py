"""
eCitizen Voice Assistant - FastAPI Backend
Main application entry point.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from config import get_settings
from routes import voice_router, booking_router, services_router, session_router
from routes.avatar import router as avatar_router
from routes.elevenlabs import router as elevenlabs_router
from utils.logger import setup_logging, get_logger
from utils.session_manager import session_manager
from utils.rate_limiter import rate_limiter
from services.gemini_service import gemini_service
from services.dialogflow_service import dialogflow_service
from services.voice_service import voice_service
from services.sms_service import sms_service
from services.elevenlabs_service import elevenlabs_service

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize services
    logger.info("Initializing services...")
    
    # Initialize Gemini
    if settings.GEMINI_API_KEY:
        gemini_service.initialize()
    else:
        logger.warning("Gemini API key not configured")
    
    # Initialize Dialogflow
    dialogflow_service.initialize()
    
    # Initialize Voice Service
    voice_service.initialize()
    
    # Initialize SMS Service
    if settings.AFRICASTALKING_USERNAME and settings.AFRICASTALKING_API_KEY:
        sms_service.initialize()
    else:
        logger.warning("Africa's Talking credentials not configured")
    
    # Start session cleanup task
    await session_manager.start_cleanup_task()
    
    logger.info("All services initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await session_manager.stop_cleanup_task()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## eCitizen Voice Assistant API
    
    A voice-enabled chatbot system to help visually impaired users access 
    Kenyan government services through the eCitizen portal.
    
    ### Features
    - **Voice Processing**: Speech-to-text and text-to-speech capabilities
    - **Natural Language Understanding**: Powered by Google Gemini API
    - **Conversation Management**: Dialogflow integration for conversation flow
    - **Service Booking**: Book appointments for government services
    - **SMS Notifications**: Appointment confirmations via Africa's Talking
    
    ### Available Services
    - Passport Application
    - National ID Application
    - Driving License
    - Certificate of Good Conduct
    
    ### Accessibility
    This API is designed with accessibility in mind, providing:
    - Clear, speakable responses
    - Step-by-step guidance
    - Audio feedback options
    """,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Configure CORS - Allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with accessible messages."""
    errors = exc.errors()
    
    # Create user-friendly error messages
    messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        messages.append(f"{field}: {msg}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Please check your input and try again.",
            "details": messages,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else exc.detail.get("error", "Error"),
            "message": exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", str(exc.detail)),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Include routers
app.include_router(voice_router)
app.include_router(booking_router)
app.include_router(services_router)
app.include_router(session_router)
app.include_router(avatar_router)
app.include_router(elevenlabs_router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the status of the application and its services.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "gemini": gemini_service._initialized,
            "dialogflow": dialogflow_service._initialized,
            "voice": voice_service._initialized,
            "sms": sms_service._initialized,
            "elevenlabs": bool(settings.ELEVENLABS_API_KEY)
        }
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Voice-enabled chatbot for eCitizen services",
        "documentation": "/docs" if settings.DEBUG else "Contact administrator for API documentation",
        "health": "/health",
        "endpoints": {
            "voice": "/voice",
            "booking": "/booking",
            "services": "/services",
            "session": "/session"
        }
    }


# Welcome message endpoint for accessibility
@app.get("/welcome", tags=["Accessibility"])
async def get_welcome_message():
    """
    Get a welcome message for the assistant.
    
    Returns a greeting based on the time of day.
    """
    from config import ASSISTANT_RESPONSES
    
    hour = datetime.now().hour
    
    if 0 <= hour < 12:
        greeting = ASSISTANT_RESPONSES["greeting"]["morning"]
    elif 12 <= hour < 18:
        greeting = ASSISTANT_RESPONSES["greeting"]["afternoon"]
    else:
        greeting = ASSISTANT_RESPONSES["greeting"]["evening"]
    
    return {
        "greeting": greeting,
        "services_info": ASSISTANT_RESPONSES["services_list"],
        "help_text": ASSISTANT_RESPONSES["help"],
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
