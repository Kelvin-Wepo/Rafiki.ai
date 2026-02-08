"""
IEBC (Independent Electoral and Boundaries Commission) Routes

Handles voter registration verification and polling station lookup.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
import httpx
import re

from backend.utils.logger import get_logger
from backend.services.sms_service import sms_service

logger = get_logger(__name__)
router = APIRouter(prefix="/iebc", tags=["IEBC Voter Services"])


# ============== Request/Response Models ==============

class VoterVerificationRequest(BaseModel):
    """Request model for voter verification."""
    national_id: str = Field(..., min_length=7, max_length=10, description="National ID number")
    
    @validator('national_id')
    def validate_national_id(cls, v):
        """Validate national ID format."""
        # Remove any spaces
        v = v.replace(" ", "")
        # Check it's numeric and reasonable length
        if not v.isdigit():
            raise ValueError("National ID must contain only numbers")
        if len(v) < 7 or len(v) > 10:
            raise ValueError("National ID must be 7-10 digits")
        return v


class VoterVerificationResponse(BaseModel):
    """Response model for voter verification."""
    success: bool
    is_registered: bool
    voter_details: Optional[Dict[str, Any]] = None
    polling_station: Optional[Dict[str, Any]] = None
    message: str
    spoken_response: str
    next_steps: list


class PollingStationRequest(BaseModel):
    """Request model for polling station lookup."""
    national_id: str = Field(..., min_length=7, max_length=10, description="National ID number")
    send_sms: bool = Field(False, description="Send polling station details via SMS")
    phone_number: Optional[str] = Field(None, description="Phone for SMS (required if send_sms=True)")
    
    @validator('national_id')
    def validate_national_id(cls, v):
        v = v.replace(" ", "")
        if not v.isdigit():
            raise ValueError("National ID must contain only numbers")
        return v
    
    @validator('phone_number')
    def validate_phone(cls, v, values):
        if values.get('send_sms') and not v:
            raise ValueError("Phone number required when send_sms is True")
        if v:
            v = re.sub(r'[\s\-]', '', v)
            if not re.match(r'^(\+254|254|0)?[17]\d{8}$', v):
                raise ValueError('Invalid Kenyan phone number format')
            if v.startswith('0'):
                v = '+254' + v[1:]
            elif v.startswith('254'):
                v = '+' + v
            elif not v.startswith('+'):
                v = '+254' + v
        return v


class PollingStationResponse(BaseModel):
    """Response model for polling station lookup."""
    success: bool
    polling_station: Optional[Dict[str, Any]] = None
    directions_hint: Optional[str] = None
    sms_sent: bool = False
    message: str
    spoken_response: str


# ============== Mock IEBC Data (Replace with actual API integration) ==============

# In production, this would query the IEBC OASIS system
MOCK_VOTER_REGISTRY = {
    "12345678": {
        "name": "John Mwangi Kamau",
        "constituency": "Westlands",
        "county": "Nairobi",
        "ward": "Kangemi",
        "polling_station": {
            "code": "027/066/01",
            "name": "Kangemi Primary School",
            "address": "Kangemi, Nairobi",
            "coordinates": {"lat": -1.2569, "lng": 36.7440}
        },
        "registration_date": "2017-02-15"
    },
    "87654321": {
        "name": "Mary Wanjiku Njeri",
        "constituency": "Kibra",
        "county": "Nairobi",
        "ward": "Makina",
        "polling_station": {
            "code": "027/084/03",
            "name": "Olympic Primary School",
            "address": "Kibra, Nairobi",
            "coordinates": {"lat": -1.3126, "lng": 36.7800}
        },
        "registration_date": "2017-01-20"
    }
}


async def query_iebc_api(national_id: str) -> Optional[Dict[str, Any]]:
    """
    Query IEBC OASIS system for voter registration.
    
    In production, this would make an actual API call to IEBC.
    Currently returns mock data for demonstration.
    """
    # Check for mock data first
    if national_id in MOCK_VOTER_REGISTRY:
        return MOCK_VOTER_REGISTRY[national_id]
    
    # Try actual IEBC API if configured
    iebc_api_url = "https://oasis.iebc.or.ke/api/verify"  # Placeholder URL
    iebc_api_key = ""  # Would be from environment
    
    if iebc_api_key:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    iebc_api_url,
                    json={"id_number": national_id},
                    headers={"Authorization": f"Bearer {iebc_api_key}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"IEBC API error: {e}")
    
    return None


# ============== Endpoints ==============

@router.post(
    "/verify-voter",
    response_model=VoterVerificationResponse,
    summary="Verify voter registration",
    description="Check if a citizen is registered as a voter"
)
async def verify_voter_registration(request: VoterVerificationRequest):
    """
    Verify voter registration status.
    
    - Checks IEBC database for registration
    - Returns polling station if registered
    - Provides registration guidance if not registered
    
    **Privacy Note:** Only the last 4 digits of the ID are logged.
    """
    try:
        masked_id = f"****{request.national_id[-4:]}"
        logger.info(f"Verifying voter registration for ID: {masked_id}")
        
        # Query IEBC system
        voter_data = await query_iebc_api(request.national_id)
        
        if voter_data:
            # Voter is registered
            spoken = (
                f"Good news! You are registered to vote. "
                f"Your polling station is {voter_data['polling_station']['name']} "
                f"in {voter_data['ward']} ward, {voter_data['constituency']} constituency. "
                f"Would you like directions to your polling station?"
            )
            
            return VoterVerificationResponse(
                success=True,
                is_registered=True,
                voter_details={
                    "name": voter_data["name"],
                    "constituency": voter_data["constituency"],
                    "county": voter_data["county"],
                    "ward": voter_data["ward"],
                    "registration_date": voter_data["registration_date"]
                },
                polling_station=voter_data["polling_station"],
                message="Voter registration verified successfully",
                spoken_response=spoken,
                next_steps=[
                    "Get directions to polling station",
                    "Send polling station details via SMS",
                    "Check another ID"
                ]
            )
        else:
            # Voter not registered
            spoken = (
                "I could not find your voter registration in the IEBC system. "
                "This could mean you are not registered, or the registration is still being processed. "
                "To register as a voter, visit the nearest IEBC registration center or Huduma Centre "
                "with your National ID card."
            )
            
            return VoterVerificationResponse(
                success=True,
                is_registered=False,
                voter_details=None,
                polling_station=None,
                message="Voter registration not found",
                spoken_response=spoken,
                next_steps=[
                    "Visit IEBC registration center",
                    "Visit nearest Huduma Centre",
                    "Call IEBC helpline: 0800 723 423",
                    "Check IEBC website: iebc.or.ke"
                ]
            )
            
    except Exception as e:
        logger.error(f"Error verifying voter: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify voter registration")


@router.post(
    "/polling-station",
    response_model=PollingStationResponse,
    summary="Find polling station",
    description="Find assigned polling station for a registered voter"
)
async def find_polling_station(request: PollingStationRequest):
    """
    Find a voter's assigned polling station.
    
    - Returns polling station details
    - Can send details via SMS
    - Provides directions hint
    """
    try:
        masked_id = f"****{request.national_id[-4:]}"
        logger.info(f"Looking up polling station for ID: {masked_id}")
        
        # Query IEBC system
        voter_data = await query_iebc_api(request.national_id)
        
        if not voter_data:
            return PollingStationResponse(
                success=True,
                polling_station=None,
                sms_sent=False,
                message="Voter not registered",
                spoken_response=(
                    "I could not find a polling station for this ID. "
                    "Please verify your voter registration first."
                )
            )
        
        station = voter_data["polling_station"]
        
        # Send SMS if requested
        sms_sent = False
        if request.send_sms and request.phone_number:
            sms_result = await sms_service.send_sms(
                request.phone_number,
                f"IEBC Voter Info\n"
                f"Polling Station: {station['name']}\n"
                f"Code: {station['code']}\n"
                f"Location: {station['address']}\n"
                f"Constituency: {voter_data['constituency']}\n"
                f"Ward: {voter_data['ward']}"
            )
            sms_sent = sms_result.get("success", False)
        
        spoken = (
            f"Your polling station is {station['name']}, "
            f"code {station['code']}, "
            f"located at {station['address']}. "
            f"You are registered under {voter_data['ward']} ward "
            f"in {voter_data['constituency']} constituency."
        )
        
        if sms_sent:
            spoken += " I have sent these details to your phone via SMS."
        
        return PollingStationResponse(
            success=True,
            polling_station=station,
            directions_hint=f"Search '{station['name']}' in Google Maps for directions",
            sms_sent=sms_sent,
            message="Polling station found",
            spoken_response=spoken
        )
        
    except Exception as e:
        logger.error(f"Error finding polling station: {e}")
        raise HTTPException(status_code=500, detail="Failed to find polling station")


@router.get(
    "/registration-info",
    summary="Get voter registration information",
    description="Get information about how to register as a voter"
)
async def get_registration_info():
    """
    Get voter registration information and requirements.
    
    Returns accessible, spoken-friendly information about the registration process.
    """
    return {
        "success": True,
        "requirements": [
            "Original National ID card (mandatory)",
            "Be at least 18 years old",
            "Be a Kenyan citizen",
            "Be of sound mind"
        ],
        "registration_centers": [
            "IEBC Constituency offices",
            "Huduma Centres",
            "Mobile registration drives (during registration periods)"
        ],
        "documents_needed": [
            "National ID card"
        ],
        "helpline": "0800 723 423",
        "website": "https://www.iebc.or.ke",
        "verification_portal": "https://oasis.iebc.or.ke/register/",
        "spoken_info": (
            "To register as a voter, you need to be a Kenyan citizen aged 18 or above "
            "with a National ID card. Visit any IEBC constituency office or Huduma Centre "
            "with your National ID to register. Registration is free. "
            "You can also verify your status on the IEBC website at iebc.or.ke "
            "or by calling the toll-free helpline 0800 723 423."
        )
    }


@router.get(
    "/election-dates",
    summary="Get upcoming election dates",
    description="Get information about upcoming elections"
)
async def get_election_dates():
    """
    Get information about upcoming elections (if any).
    """
    # In production, this would be updated with actual election information
    return {
        "success": True,
        "upcoming_elections": [],
        "message": "No upcoming elections scheduled at this time",
        "spoken_response": (
            "There are currently no upcoming elections scheduled. "
            "Please check the IEBC website for updates on future elections."
        ),
        "iebc_website": "https://www.iebc.or.ke"
    }
