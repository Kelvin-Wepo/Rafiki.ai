"""
Waitlist API routes.

Endpoints for user waitlist management:
- POST /waitlist/join - Join the waitlist
- GET /waitlist/status - Check waitlist status
- GET /waitlist/stats - Get waitlist statistics (admin)
- POST /waitlist/activate - Activate next batch (admin)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from models.schemas import (
    JoinWaitlistRequest, WaitlistEntryResponse, 
    WaitlistListResponse, CheckWaitlistStatusResponse
)
from services.waitlist_service import get_waitlist_service
from database import get_db
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post("/join")
async def join_waitlist(
    request: JoinWaitlistRequest,
    db = Depends(get_db)
):
    """
    Join the waitlist for Rafiki services.
    
    Args:
        phone_number: Kenyan phone number (0712345678 or +254712345678)
        email: Email address (optional)
        full_name: Full name (optional)
        service_interest: Type of service (general, passport, national_id, etc.)
    
    Returns:
        Success message with waitlist position
    """
    try:
        waitlist_service = get_waitlist_service(db)
        result = await waitlist_service.join_waitlist(
            phone_number=request.phone_number,
            email=request.email,
            full_name=request.full_name,
            service_interest=request.service_interest.value
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error joining waitlist: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to join waitlist: {str(e)}"
        )


@router.get("/status")
async def check_waitlist_status(
    phone_number: str = Query(..., description="Phone number to check"),
    db = Depends(get_db)
) -> CheckWaitlistStatusResponse:
    """
    Check the waitlist status for a phone number.
    
    Args:
        phone_number: Phone number to check (0712345678 or +254712345678)
    
    Returns:
        Status information including position if pending
    """
    try:
        waitlist_service = get_waitlist_service(db)
        result = await waitlist_service.check_status(phone_number)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Phone number not found on waitlist")
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking waitlist status: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to check status: {str(e)}"
        )


@router.get("/stats")
async def get_waitlist_statistics(db = Depends(get_db)):
    """
    Get waitlist statistics.
    
    Returns:
        Total count, pending count, activated count
    """
    try:
        waitlist_service = get_waitlist_service(db)
        stats = await waitlist_service.get_waitlist_stats()
        
        if not stats.get("success"):
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve statistics"
            )
        
        return {
            "total": stats["total"],
            "pending": stats["pending"],
            "activated": stats["activated"],
            "cancelled": stats["cancelled"]
        }
    
    except Exception as e:
        logger.error(f"Error getting waitlist stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/activate")
async def activate_waitlist_entries(
    count: int = Query(10, description="Number of entries to activate"),
    db = Depends(get_db)
):
    """
    Activate the next batch of waitlist entries (ADMIN ONLY).
    
    Args:
        count: Number of entries to activate (default 10)
    
    Returns:
        List of activated phone numbers
    """
    try:
        waitlist_service = get_waitlist_service(db)
        result = await waitlist_service.activate_entries(count)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to activate entries")
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Error activating waitlist entries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to activate entries: {str(e)}"
        )


@router.get("/health")
async def waitlist_health():
    """Health check for waitlist service."""
    return {
        "status": "healthy",
        "service": "waitlist"
    }
