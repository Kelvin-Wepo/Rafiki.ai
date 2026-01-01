"""
Booking service for managing government service appointments.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List

from config import get_settings, GOVERNMENT_SERVICES
from models.schemas import ServiceType, TimeSlot, BookingStatus
from utils.logger import get_logger
from services.sms_service import sms_service

logger = get_logger(__name__)


class Booking:
    """Represents a service booking."""
    
    def __init__(
        self,
        service_type: ServiceType,
        user_name: str,
        phone_number: str,
        time_slot: TimeSlot,
        appointment_date: date,
        additional_notes: Optional[str] = None
    ):
        self.booking_id = str(uuid.uuid4())[:8].upper()
        self.service_type = service_type
        self.user_name = user_name
        self.phone_number = phone_number
        self.time_slot = time_slot
        self.appointment_date = appointment_date
        self.additional_notes = additional_notes
        self.status = BookingStatus.PENDING
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.confirmation_sent = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert booking to dictionary."""
        service_info = GOVERNMENT_SERVICES.get(self.service_type.value, {})
        return {
            "booking_id": self.booking_id,
            "service_type": self.service_type.value,
            "service_name": service_info.get("name", self.service_type.value),
            "department": service_info.get("department", ""),
            "user_name": self.user_name,
            "phone_number": self.phone_number,
            "time_slot": self.time_slot.value,
            "appointment_date": self.appointment_date.isoformat(),
            "additional_notes": self.additional_notes,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confirmation_sent": self.confirmation_sent,
            "requirements": service_info.get("requirements", [])
        }


class BookingService:
    """
    Service for managing appointment bookings.
    """
    
    def __init__(self):
        """Initialize booking service."""
        self.settings = get_settings()
        self._bookings: Dict[str, Booking] = {}
        self._user_bookings: Dict[str, List[str]] = {}  # phone -> booking_ids
    
    async def create_booking(
        self,
        service_type: ServiceType,
        user_name: str,
        phone_number: str,
        time_slot: TimeSlot,
        appointment_date: date,
        additional_notes: Optional[str] = None,
        send_sms: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new booking.
        
        Args:
            service_type: Type of government service
            user_name: User's full name
            phone_number: Phone number for SMS confirmation
            time_slot: Preferred time slot
            appointment_date: Appointment date
            additional_notes: Optional notes
            send_sms: Whether to send SMS confirmation
        
        Returns:
            Booking result with details
        """
        try:
            # Validate date is not in the past
            if appointment_date < date.today():
                return {
                    "success": False,
                    "error": "Appointment date cannot be in the past"
                }
            
            # Validate date is not too far in future (e.g., 90 days)
            max_date = date.today() + timedelta(days=90)
            if appointment_date > max_date:
                return {
                    "success": False,
                    "error": "Appointment date cannot be more than 90 days in the future"
                }
            
            # Check for existing booking at same time
            existing = await self._check_duplicate_booking(
                phone_number, service_type, appointment_date, time_slot
            )
            if existing:
                return {
                    "success": False,
                    "error": "You already have a booking for this service at this time",
                    "existing_booking": existing.to_dict()
                }
            
            # Create booking
            booking = Booking(
                service_type=service_type,
                user_name=user_name,
                phone_number=phone_number,
                time_slot=time_slot,
                appointment_date=appointment_date,
                additional_notes=additional_notes
            )
            
            # Store booking
            self._bookings[booking.booking_id] = booking
            
            if phone_number not in self._user_bookings:
                self._user_bookings[phone_number] = []
            self._user_bookings[phone_number].append(booking.booking_id)
            
            # Send SMS confirmation
            sms_result = {"success": False}
            if send_sms:
                sms_result = await sms_service.send_booking_confirmation(
                    phone_number,
                    booking.to_dict()
                )
                booking.confirmation_sent = sms_result.get("success", False)
            
            # Update status
            booking.status = BookingStatus.CONFIRMED
            booking.updated_at = datetime.utcnow()
            
            logger.info(f"Created booking {booking.booking_id} for {user_name}")
            
            return {
                "success": True,
                "booking": booking.to_dict(),
                "sms_sent": sms_result.get("success", False),
                "message": f"Your appointment for {GOVERNMENT_SERVICES[service_type.value]['name']} "
                          f"has been booked for {appointment_date.strftime('%B %d, %Y')} "
                          f"during {time_slot.value}. Booking ID: {booking.booking_id}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create booking: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _check_duplicate_booking(
        self,
        phone_number: str,
        service_type: ServiceType,
        appointment_date: date,
        time_slot: TimeSlot
    ) -> Optional[Booking]:
        """Check for duplicate bookings."""
        if phone_number not in self._user_bookings:
            return None
        
        for booking_id in self._user_bookings[phone_number]:
            booking = self._bookings.get(booking_id)
            if (booking and 
                booking.status != BookingStatus.CANCELLED and
                booking.service_type == service_type and
                booking.appointment_date == appointment_date and
                booking.time_slot == time_slot):
                return booking
        
        return None
    
    async def get_booking(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """
        Get booking by ID.
        
        Args:
            booking_id: Booking identifier
        
        Returns:
            Booking details or None
        """
        booking = self._bookings.get(booking_id.upper())
        if booking:
            return booking.to_dict()
        return None
    
    async def get_user_bookings(
        self,
        phone_number: str,
        status: Optional[BookingStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all bookings for a user.
        
        Args:
            phone_number: User's phone number
            status: Optional status filter
        
        Returns:
            List of bookings
        """
        booking_ids = self._user_bookings.get(phone_number, [])
        bookings = []
        
        for booking_id in booking_ids:
            booking = self._bookings.get(booking_id)
            if booking:
                if status is None or booking.status == status:
                    bookings.append(booking.to_dict())
        
        # Sort by date, most recent first
        bookings.sort(key=lambda x: x["appointment_date"], reverse=True)
        return bookings
    
    async def cancel_booking(
        self,
        booking_id: str,
        send_sms: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel a booking.
        
        Args:
            booking_id: Booking identifier
            send_sms: Whether to send cancellation SMS
        
        Returns:
            Cancellation result
        """
        booking = self._bookings.get(booking_id.upper())
        
        if not booking:
            return {
                "success": False,
                "error": "Booking not found"
            }
        
        if booking.status == BookingStatus.CANCELLED:
            return {
                "success": False,
                "error": "Booking is already cancelled"
            }
        
        if booking.status == BookingStatus.COMPLETED:
            return {
                "success": False,
                "error": "Cannot cancel a completed booking"
            }
        
        # Update status
        booking.status = BookingStatus.CANCELLED
        booking.updated_at = datetime.utcnow()
        
        # Send cancellation SMS
        if send_sms:
            await sms_service.send_cancellation(
                booking.phone_number,
                booking.to_dict()
            )
        
        logger.info(f"Cancelled booking {booking_id}")
        
        return {
            "success": True,
            "booking": booking.to_dict(),
            "message": "Your booking has been cancelled successfully."
        }
    
    async def update_booking(
        self,
        booking_id: str,
        time_slot: Optional[TimeSlot] = None,
        appointment_date: Optional[date] = None,
        additional_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a booking.
        
        Args:
            booking_id: Booking identifier
            time_slot: New time slot
            appointment_date: New date
            additional_notes: Updated notes
        
        Returns:
            Update result
        """
        booking = self._bookings.get(booking_id.upper())
        
        if not booking:
            return {
                "success": False,
                "error": "Booking not found"
            }
        
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            return {
                "success": False,
                "error": f"Cannot update a {booking.status.value} booking"
            }
        
        # Update fields
        if time_slot:
            booking.time_slot = time_slot
        if appointment_date:
            if appointment_date < date.today():
                return {
                    "success": False,
                    "error": "Appointment date cannot be in the past"
                }
            booking.appointment_date = appointment_date
        if additional_notes is not None:
            booking.additional_notes = additional_notes
        
        booking.updated_at = datetime.utcnow()
        
        logger.info(f"Updated booking {booking_id}")
        
        return {
            "success": True,
            "booking": booking.to_dict(),
            "message": "Your booking has been updated successfully."
        }
    
    def get_available_dates(
        self,
        service_type: ServiceType,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get available dates for booking.
        
        Args:
            service_type: Type of service
            days_ahead: Number of days to check
        
        Returns:
            List of available dates with time slots
        """
        available = []
        today = date.today()
        
        for i in range(days_ahead):
            check_date = today + timedelta(days=i)
            
            # Skip weekends (Saturday=5, Sunday=6)
            if check_date.weekday() >= 5:
                continue
            
            # Check availability for each time slot
            morning_available = True
            afternoon_available = True
            
            # In a real system, this would check against actual capacity
            # For now, assume all slots are available
            
            available.append({
                "date": check_date.isoformat(),
                "day_name": check_date.strftime("%A"),
                "slots": {
                    "morning": morning_available,
                    "afternoon": afternoon_available
                }
            })
        
        return available
    
    def get_service_info(self, service_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a service.
        
        Args:
            service_type: Service type key
        
        Returns:
            Service information or None
        """
        return GOVERNMENT_SERVICES.get(service_type)
    
    def get_all_services(self) -> List[Dict[str, Any]]:
        """Get all available services."""
        return [
            {
                "type": key,
                **value
            }
            for key, value in GOVERNMENT_SERVICES.items()
        ]


# Global service instance
booking_service = BookingService()
