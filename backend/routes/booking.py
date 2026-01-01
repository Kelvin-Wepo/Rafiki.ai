"""
Booking API endpoints.
"""

from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Request

from models.schemas import (
    BookingRequest,
    BookingResponse,
    ServiceType,
    TimeSlot,
    BookingStatus
)
from services.booking_service import booking_service
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger, RequestLogger

logger = get_logger(__name__)
router = APIRouter(prefix="/booking", tags=["Booking"])


async def check_rate_limit(request: Request):
    """Dependency to check rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    result = await rate_limiter.check_rate_limit(client_ip)
    
    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "retry_after": result.retry_after_seconds
            }
        )
    
    return result


@router.post(
    "/create",
    response_model=BookingResponse,
    summary="Create a new booking",
    description="Create a new appointment booking for a government service"
)
async def create_booking(
    request: BookingRequest,
    rate_limit: dict = Depends(check_rate_limit)
):
    """
    Create a new appointment booking.
    
    - **service_type**: Type of government service (passport, national_id, driving_license, good_conduct)
    - **user_name**: Full name of the applicant
    - **phone_number**: Phone number for SMS confirmation (Kenyan format)
    - **time_slot**: Preferred time slot (morning: 08:00-12:00, afternoon: 14:00-17:00)
    - **appointment_date**: Preferred date for appointment
    - **additional_notes**: Optional notes or special requirements
    """
    with RequestLogger(logger, "create_booking", service=request.service_type.value):
        result = await booking_service.create_booking(
            service_type=request.service_type,
            user_name=request.user_name,
            phone_number=request.phone_number,
            time_slot=request.time_slot,
            appointment_date=request.appointment_date.date(),
            additional_notes=request.additional_notes,
            send_sms=True
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to create booking")
            )
        
        booking = result.get("booking", {})
        
        return BookingResponse(
            success=True,
            booking_id=booking.get("booking_id"),
            message=result.get("message", "Booking created successfully"),
            booking_details=booking,
            sms_sent=result.get("sms_sent", False),
            appointment_datetime=datetime.fromisoformat(
                f"{booking.get('appointment_date')}T{booking.get('time_slot', '08:00').split('-')[0]}"
            ) if booking.get("appointment_date") else None
        )


@router.get(
    "/{booking_id}",
    summary="Get booking details",
    description="Retrieve details of a specific booking"
)
async def get_booking(booking_id: str):
    """
    Get booking by ID.
    
    - **booking_id**: Unique booking identifier
    """
    booking = await booking_service.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )
    
    return {"booking": booking}


@router.get(
    "/user/{phone_number}",
    summary="Get user bookings",
    description="Retrieve all bookings for a user by phone number"
)
async def get_user_bookings(
    phone_number: str,
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Get all bookings for a user.
    
    - **phone_number**: User's phone number
    - **status**: Optional status filter (pending, confirmed, cancelled, completed)
    """
    # Normalize phone number
    if phone_number.startswith("0"):
        phone_number = "+254" + phone_number[1:]
    elif not phone_number.startswith("+"):
        phone_number = "+254" + phone_number
    
    status_filter = None
    if status:
        try:
            status_filter = BookingStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in BookingStatus]}"
            )
    
    bookings = await booking_service.get_user_bookings(phone_number, status_filter)
    
    return {
        "bookings": bookings,
        "total_count": len(bookings)
    }


@router.delete(
    "/{booking_id}",
    summary="Cancel a booking",
    description="Cancel an existing booking"
)
async def cancel_booking(
    booking_id: str,
    send_sms: bool = Query(True, description="Send cancellation SMS")
):
    """
    Cancel a booking.
    
    - **booking_id**: Unique booking identifier
    - **send_sms**: Whether to send cancellation SMS (default: true)
    """
    result = await booking_service.cancel_booking(booking_id, send_sms=send_sms)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to cancel booking")
        )
    
    return {
        "success": True,
        "message": result.get("message"),
        "booking": result.get("booking")
    }


@router.patch(
    "/{booking_id}",
    summary="Update a booking",
    description="Update an existing booking"
)
async def update_booking(
    booking_id: str,
    time_slot: Optional[TimeSlot] = None,
    appointment_date: Optional[date] = None,
    additional_notes: Optional[str] = None
):
    """
    Update a booking.
    
    - **booking_id**: Unique booking identifier
    - **time_slot**: New time slot (optional)
    - **appointment_date**: New appointment date (optional)
    - **additional_notes**: Updated notes (optional)
    """
    result = await booking_service.update_booking(
        booking_id,
        time_slot=time_slot,
        appointment_date=appointment_date,
        additional_notes=additional_notes
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to update booking")
        )
    
    return {
        "success": True,
        "message": result.get("message"),
        "booking": result.get("booking")
    }


@router.get(
    "/availability/{service_type}",
    summary="Get available dates",
    description="Get available dates and time slots for a service"
)
async def get_availability(
    service_type: ServiceType,
    days_ahead: int = Query(30, ge=1, le=90, description="Days to check ahead")
):
    """
    Get available dates for booking.
    
    - **service_type**: Type of government service
    - **days_ahead**: Number of days ahead to check (1-90, default: 30)
    """
    available_dates = booking_service.get_available_dates(service_type, days_ahead)
    
    return {
        "service_type": service_type.value,
        "available_dates": available_dates,
        "time_slots": [
            {"id": "morning", "label": "Morning (8:00 AM - 12:00 PM)", "value": "08:00-12:00"},
            {"id": "afternoon", "label": "Afternoon (2:00 PM - 5:00 PM)", "value": "14:00-17:00"}
        ]
    }
