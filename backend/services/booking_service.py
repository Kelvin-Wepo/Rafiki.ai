"""
Booking service for managing government service appointments.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List

from rafiki_settings import get_settings, GOVERNMENT_SERVICES
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
            "id": self.booking_id,
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
                "booking_id": booking.booking_id,
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
            return {"success": True, "booking": booking.to_dict()}
        return {"success": False, "error": "Booking not found"}
    
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
        return {"success": True, "bookings": bookings}
    
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
    
    async def get_available_dates(
        self,
        service_type: ServiceType,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Get available dates for booking.
        Returns a wrapper dict with success and available_dates.
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
        
        return {"success": True, "available_dates": available}
    
    def get_service_info(self, service_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a service.
        
        Args:
            service_type: Service type key
        
        Returns:
            Service information or None
        """
        return GOVERNMENT_SERVICES.get(service_type)
    
    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all available services as a dict keyed by service type."""
        return {key: value for key, value in GOVERNMENT_SERVICES.items()}


# Global service instance
booking_service = BookingService()


# ---------------------------------------------------------------------------
# Agency Workflow Integration - JSON persistence for bookings
# ---------------------------------------------------------------------------
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
AGENCY_BOOKINGS_FILE = DATA_DIR / "agency_bookings.json"


def _ensure_data_dir():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not AGENCY_BOOKINGS_FILE.exists():
        with open(AGENCY_BOOKINGS_FILE, "w") as f:
            json.dump({}, f)


def _load_agency_bookings() -> Dict[str, Any]:
    """Load all agency bookings from storage."""
    _ensure_data_dir()
    try:
        with open(AGENCY_BOOKINGS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_agency_bookings(data: Dict[str, Any]):
    """Save agency bookings to storage."""
    _ensure_data_dir()
    with open(AGENCY_BOOKINGS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def generate_booking_ref(agency: str, service: str) -> str:
    """Generate a unique booking reference."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_id = str(uuid.uuid4())[:6].upper()
    agency_code = agency[:3].upper() if agency else "RAF"
    return f"BK-{agency_code}-{timestamp}-{short_id}"


def get_next_available_slot(agency: str, service: str, county: str = None) -> Dict[str, Any]:
    """
    Get the next available appointment slot.
    In production, this would integrate with agency booking systems.
    """
    import random
    days_ahead = random.randint(2, 5)
    appointment_date = datetime.now() + timedelta(days=days_ahead)
    
    while appointment_date.weekday() >= 5:
        appointment_date += timedelta(days=1)
    
    time_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    appointment_time = random.choice(time_slots)
    
    office_map = {
        "NTSA": {
            "default": "NTSA Head Office, Hill Plaza, Nairobi",
            "Nairobi": "NTSA Times Tower, Nairobi CBD",
            "Mombasa": "NTSA Mombasa Office, Moi Avenue",
            "Kisumu": "NTSA Kisumu Office, Oginga Odinga Street",
        },
        "KRA": {
            "default": "KRA Times Tower, Nairobi",
            "Nairobi": "KRA Times Tower, Haile Selassie Avenue",
            "Mombasa": "KRA Mombasa Office, Customs House",
        },
        "DCI": {
            "default": "DCI Headquarters, Kiambu Road, Nairobi",
        },
    }
    
    agency_offices = office_map.get(agency, {"default": "Huduma Centre, Nairobi"})
    office = agency_offices.get(county, agency_offices.get("default"))
    
    return {
        "date": appointment_date.strftime("%Y-%m-%d"),
        "time": appointment_time,
        "day": appointment_date.strftime("%A"),
        "office": office,
        "office_address": office,
    }


def create_agency_booking(
    session_id: str,
    agency: str,
    service: str,
    applicant_data: Dict[str, Any],
    payment_ref: Optional[str] = None,
    amount: Optional[int] = None,
    appointment_slot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new booking/appointment record for agency workflows.
    """
    bookings = _load_agency_bookings()
    
    booking_ref = generate_booking_ref(agency, service)
    
    if not appointment_slot:
        appointment_slot = get_next_available_slot(
            agency=agency,
            service=service,
            county=applicant_data.get("county"),
        )
    
    booking = {
        "booking_ref": booking_ref,
        "session_id": session_id,
        "agency": agency,
        "service": service,
        "status": "pending_payment" if payment_ref else "draft",
        "applicant": {
            "name": applicant_data.get("name", ""),
            "id_number": applicant_data.get("id", ""),
            "phone": applicant_data.get("phone", "") or applicant_data.get("mpesa", ""),
            "email": applicant_data.get("email", ""),
            "county": applicant_data.get("county", ""),
        },
        "appointment": appointment_slot,
        "payment": {
            "reference": payment_ref,
            "amount": amount,
            "status": "pending" if payment_ref else None,
            "paid_at": None,
        },
        "metadata": applicant_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    bookings[booking_ref] = booking
    _save_agency_bookings(bookings)
    
    logger.info(f"Agency booking created: ref={booking_ref}, agency={agency}")
    return booking


def get_agency_booking(booking_ref: str) -> Optional[Dict[str, Any]]:
    """Get an agency booking by reference."""
    bookings = _load_agency_bookings()
    return bookings.get(booking_ref)


def get_agency_booking_by_payment_ref(payment_ref: str) -> Optional[Dict[str, Any]]:
    """Get an agency booking by payment reference."""
    bookings = _load_agency_bookings()
    
    for booking in bookings.values():
        if booking.get("payment", {}).get("reference") == payment_ref:
            return booking
    
    return None


def mark_agency_booking_paid(
    payment_ref: str,
    transaction_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Mark an agency booking as paid when payment is confirmed."""
    booking = get_agency_booking_by_payment_ref(payment_ref)
    
    if not booking:
        logger.warning(f"No booking found for payment ref: {payment_ref}")
        return None
    
    bookings = _load_agency_bookings()
    booking_ref = booking["booking_ref"]
    
    bookings[booking_ref]["status"] = "confirmed"
    bookings[booking_ref]["payment"]["status"] = "paid"
    bookings[booking_ref]["payment"]["paid_at"] = datetime.now().isoformat()
    
    if transaction_id:
        bookings[booking_ref]["payment"]["transaction_id"] = transaction_id
    
    bookings[booking_ref]["updated_at"] = datetime.now().isoformat()
    
    _save_agency_bookings(bookings)
    
    logger.info(f"Agency booking marked paid: ref={booking_ref}")
    return bookings[booking_ref]
