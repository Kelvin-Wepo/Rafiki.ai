"""
Citizen interaction routes for anonymous feedback, emergency reporting, and corruption reporting.

Features:
- Anonymous feedback submission
- Emergency reporting with immediate guidance
- Corruption reporting with whistleblower protection
- Accessibility-first design for screen readers
"""

from datetime import datetime
import uuid
import hashlib
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.utils.logger import get_logger
from backend.utils.encryption import get_encryption_service
from backend.services.fraud_service import FraudService

logger = get_logger(__name__)
router = APIRouter(prefix="/citizen", tags=["Citizen Interaction"])


# ============== Request/Response Models ==============

class FeedbackRequest(BaseModel):
    """Request model for citizen feedback."""
    category: str = Field(..., description="Feedback category (suggestion, complaint, praise, other)")
    message: str = Field(..., min_length=10, max_length=2000, description="Feedback message")
    is_anonymous: bool = Field(True, description="Whether to submit anonymously")
    contact_info: Optional[str] = Field(None, description="Optional contact info if not anonymous")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    success: bool
    reference_id: str
    message: str
    is_anonymous: bool
    timestamp: str


class EmergencyRequest(BaseModel):
    """Request model for emergency reports."""
    emergency_type: str = Field(..., description="Type: police, fire, ambulance, other")
    description: str = Field(..., min_length=5, max_length=1000, description="Brief description")
    location: Optional[str] = Field(None, description="Location if known")
    session_id: Optional[str] = Field(None, description="Session ID")


class EmergencyResponse(BaseModel):
    """Response model for emergency reports."""
    success: bool
    emergency_number: str
    instructions: list
    reference_id: Optional[str]
    message: str


class CorruptionReportRequest(BaseModel):
    """Request model for corruption reports (anonymous)."""
    incident_type: str = Field(..., description="Type: bribery, fraud, embezzlement, abuse_of_office, other")
    description: str = Field(..., min_length=20, max_length=5000, description="Detailed description")
    location: Optional[str] = Field(None, description="Where incident occurred")
    date_occurred: Optional[str] = Field(None, description="When incident occurred")
    evidence_description: Optional[str] = Field(None, description="Description of any evidence")
    # Note: No personal info fields - this is intentionally anonymous


class CorruptionReportResponse(BaseModel):
    """Response model for corruption reports."""
    success: bool
    reference_id: str
    message: str
    eacc_contact: str
    next_steps: list
    privacy_notice: str


# ============== In-memory storage (replace with database in production) ==============
_feedback_store: Dict[str, Dict[str, Any]] = {}
_emergency_store: Dict[str, Dict[str, Any]] = {}
_corruption_store: Dict[str, Dict[str, Any]] = {}


# ============== Endpoints ==============

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit citizen feedback",
    description="Submit feedback anonymously or with contact info"
)
async def submit_feedback(request: FeedbackRequest, req: Request):
    """
    Submit citizen feedback.
    
    - Feedback can be submitted anonymously
    - No personal data is stored when anonymous mode is selected
    - Categories: suggestion, complaint, praise, other
    """
    try:
        # Generate anonymous reference ID
        reference_id = f"FB-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.utcnow()
        
        # Prepare storage data
        feedback_data = {
            "reference_id": reference_id,
            "category": request.category,
            "message": request.message,
            "is_anonymous": request.is_anonymous,
            "timestamp": timestamp.isoformat(),
            "ip_hash": hashlib.sha256(
                (req.client.host if req.client else "unknown").encode()
            ).hexdigest()[:16] if not request.is_anonymous else None,  # Only store hashed IP if not anonymous
        }
        
        # Only store contact info if not anonymous
        if not request.is_anonymous and request.contact_info:
            encryption = get_encryption_service()
            feedback_data["contact_info_encrypted"] = encryption.encrypt(request.contact_info)
        
        # Store feedback
        _feedback_store[reference_id] = feedback_data
        
        # Log without PII
        logger.info(
            f"Feedback submitted: {reference_id}, "
            f"category: {request.category}, "
            f"anonymous: {request.is_anonymous}"
        )
        
        return FeedbackResponse(
            success=True,
            reference_id=reference_id,
            message="Thank you for your feedback. Your input helps improve government services.",
            is_anonymous=request.is_anonymous,
            timestamp=timestamp.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.post(
    "/emergency",
    response_model=EmergencyResponse,
    summary="Report an emergency",
    description="Get immediate guidance for emergencies"
)
async def report_emergency(request: EmergencyRequest, req: Request):
    """
    Report an emergency and get immediate guidance.
    
    - Provides emergency contact numbers
    - Gives safety instructions
    - Logs incident for follow-up (no personal data without consent)
    
    **Emergency Numbers:**
    - Police/Ambulance/Fire: 999
    - National Emergency: 112
    """
    try:
        emergency_numbers = {
            "police": "999",
            "fire": "999",
            "ambulance": "999",
            "other": "112"
        }
        
        emergency_instructions = {
            "police": [
                "Stay calm and find a safe location if possible",
                "Call 999 immediately",
                "Provide your location clearly",
                "Describe the situation briefly",
                "Follow operator instructions"
            ],
            "fire": [
                "Evacuate the building immediately",
                "Call 999 for fire services",
                "Do not use elevators",
                "Stay low if there is smoke",
                "Meet at a safe assembly point"
            ],
            "ambulance": [
                "Call 999 for medical emergency",
                "Describe the medical situation",
                "Provide exact location",
                "Stay with the patient if safe",
                "Follow operator instructions"
            ],
            "other": [
                "Call 112 for national emergency line",
                "Describe your emergency clearly",
                "Provide your location",
                "Follow all instructions given"
            ]
        }
        
        emergency_type = request.emergency_type.lower()
        if emergency_type not in emergency_numbers:
            emergency_type = "other"
        
        # Generate reference (optional logging)
        reference_id = f"EM-{uuid.uuid4().hex[:8].upper()}"
        
        # Log emergency report (minimal data for safety follow-up)
        _emergency_store[reference_id] = {
            "reference_id": reference_id,
            "emergency_type": emergency_type,
            "timestamp": datetime.utcnow().isoformat(),
            "description_hash": hashlib.sha256(request.description.encode()).hexdigest()[:16],
            "location_provided": bool(request.location)
        }
        
        logger.warning(
            f"EMERGENCY REPORT: {reference_id}, type: {emergency_type}"
        )
        
        return EmergencyResponse(
            success=True,
            emergency_number=emergency_numbers[emergency_type],
            instructions=emergency_instructions[emergency_type],
            reference_id=reference_id,
            message=f"For {emergency_type} emergencies, call {emergency_numbers[emergency_type]} immediately. "
                    f"Stay safe and follow the instructions provided."
        )
        
    except Exception as e:
        logger.error(f"Error processing emergency report: {e}")
        # Even on error, provide emergency numbers
        return EmergencyResponse(
            success=False,
            emergency_number="999 or 112",
            instructions=["Call 999 for Police, Fire, or Ambulance", "Call 112 for national emergency line"],
            reference_id=None,
            message="Please call emergency services directly: 999 or 112"
        )


@router.post(
    "/corruption-report",
    response_model=CorruptionReportResponse,
    summary="Report corruption anonymously",
    description="Submit anonymous corruption reports - no personal data collected"
)
async def report_corruption(request: CorruptionReportRequest, req: Request):
    """
    Submit an anonymous corruption report.
    
    **Privacy Guarantees:**
    - No IP addresses stored
    - No personal information collected
    - Report encrypted at rest
    - EACC whistleblower protections apply
    
    **Report Types:**
    - bribery
    - fraud
    - embezzlement
    - abuse_of_office
    - other
    """
    try:
        # Check for potential abuse (rate limiting without storing identity)
        fraud_service = FraudService()
        
        # Use session-based key, not IP, to maintain anonymity
        rate_key = f"corruption_report:{request.incident_type}"
        rate_check = fraud_service.check_rate_limit(rate_key, limit=10, window=3600, block_duration=3600)
        
        if not rate_check.get("allow", True):
            raise HTTPException(
                status_code=429,
                detail="Too many reports submitted. Please try again later."
            )
        
        # Generate anonymous reference ID
        reference_id = f"CR-{uuid.uuid4().hex[:12].upper()}"
        timestamp = datetime.utcnow()
        
        # Encrypt report content for secure storage
        encryption = get_encryption_service()
        
        # Store ONLY encrypted, anonymized data
        report_data = {
            "reference_id": reference_id,
            "incident_type": request.incident_type,
            "timestamp": timestamp.isoformat(),
            # Encrypt sensitive content
            "encrypted_content": encryption.encrypt(
                f"Description: {request.description}\n"
                f"Location: {request.location or 'Not provided'}\n"
                f"Date: {request.date_occurred or 'Not provided'}\n"
                f"Evidence: {request.evidence_description or 'None described'}"
            ),
            # NO IP, NO session, NO identifying information
        }
        
        _corruption_store[reference_id] = report_data
        
        # Log without any identifying information
        logger.info(
            f"Corruption report submitted: {reference_id}, "
            f"type: {request.incident_type}"
        )
        
        return CorruptionReportResponse(
            success=True,
            reference_id=reference_id,
            message="Your report has been securely submitted. Thank you for helping fight corruption.",
            eacc_contact="Ethics and Anti-Corruption Commission: 0800 720 721 (toll-free)",
            next_steps=[
                "Your report is now in our secure system",
                "No personal information has been collected",
                "You may contact EACC directly for follow-up using your reference ID",
                "Whistleblower protections under the Witness Protection Act apply"
            ],
            privacy_notice="This report was submitted anonymously. No IP addresses, personal data, "
                          "or identifying information has been stored. Your identity remains protected "
                          "under Kenyan whistleblower protection laws."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing corruption report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit report. You can report directly to EACC at 0800 720 721"
        )


@router.get(
    "/emergency-numbers",
    summary="Get emergency numbers",
    description="Get list of Kenya emergency contact numbers"
)
async def get_emergency_numbers():
    """
    Get Kenya emergency contact numbers.
    
    Accessible endpoint that provides emergency numbers in a screen-reader friendly format.
    """
    return {
        "emergency_numbers": {
            "police": {"number": "999", "description": "Kenya Police Service"},
            "ambulance": {"number": "999", "description": "Emergency Medical Services"},
            "fire": {"number": "999", "description": "Fire and Rescue Services"},
            "national_emergency": {"number": "112", "description": "National Emergency Number"},
            "eacc": {"number": "0800 720 721", "description": "Ethics and Anti-Corruption Commission (toll-free)"},
            "gender_violence": {"number": "1195", "description": "Gender Violence Helpline"},
            "child_helpline": {"number": "116", "description": "Child Helpline Kenya"}
        },
        "spoken_format": "For Police, Ambulance, or Fire emergencies, call 999. "
                        "For the national emergency line, call 112. "
                        "To report corruption anonymously, call 0800 720 721."
    }
