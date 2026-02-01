"""
Tests for BookingService
Covers booking creation, management, and availability checks.
"""

import pytest
from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.booking_service import BookingService, booking_service, Booking
from models.schemas import ServiceType, TimeSlot, BookingStatus


@pytest.fixture
def booking_test_service():
    """Create a fresh BookingService instance."""
    return BookingService()


# ============== Booking Creation Tests ==============

@pytest.mark.asyncio
async def test_create_booking_success(booking_test_service, sample_booking_data):
    """Test creating a valid booking."""
    result = await booking_test_service.create_booking(
        service_type=ServiceType(sample_booking_data["service_type"]),
        user_name=sample_booking_data["user_name"],
        phone_number=sample_booking_data["phone_number"],
        time_slot=TimeSlot(sample_booking_data["time_slot"]),
        appointment_date=sample_booking_data["appointment_date"],
        additional_notes=sample_booking_data["additional_notes"],
        send_sms=False  # Don't send SMS in tests
    )
    
    assert result["success"] is True
    assert "booking_id" in result
    assert result["booking_id"] is not None


@pytest.mark.asyncio
async def test_create_booking_past_date(booking_test_service, sample_booking_data):
    """Test creating booking with past date."""
    past_date = date.today() - timedelta(days=1)
    
    result = await booking_test_service.create_booking(
        service_type=ServiceType(sample_booking_data["service_type"]),
        user_name=sample_booking_data["user_name"],
        phone_number=sample_booking_data["phone_number"],
        time_slot=TimeSlot(sample_booking_data["time_slot"]),
        appointment_date=past_date,
        send_sms=False
    )
    
    assert result["success"] is False
    assert "past" in result.get("error", "").lower() or "date" in result.get("error", "").lower()


@pytest.mark.asyncio
async def test_create_duplicate_booking(booking_test_service, sample_booking_data):
    """Test creating duplicate booking for same slot."""
    # Create first booking
    await booking_test_service.create_booking(
        service_type=ServiceType(sample_booking_data["service_type"]),
        user_name=sample_booking_data["user_name"],
        phone_number=sample_booking_data["phone_number"],
        time_slot=TimeSlot(sample_booking_data["time_slot"]),
        appointment_date=sample_booking_data["appointment_date"],
        send_sms=False
    )
    
    # Try to create duplicate
    result = await booking_test_service.create_booking(
        service_type=ServiceType(sample_booking_data["service_type"]),
        user_name=sample_booking_data["user_name"],
        phone_number=sample_booking_data["phone_number"],
        time_slot=TimeSlot(sample_booking_data["time_slot"]),
        appointment_date=sample_booking_data["appointment_date"],
        send_sms=False
    )
    
    assert result["success"] is False
    assert "duplicate" in result.get("error", "").lower() or "already" in result.get("error", "").lower()


# ============== Booking Retrieval Tests ==============

@pytest.mark.asyncio
async def test_get_booking(booking_test_service, sample_booking_data):
    """Test retrieving a booking by ID."""
    # Create booking first
    create_result = await booking_test_service.create_booking(
        service_type=ServiceType(sample_booking_data["service_type"]),
        user_name=sample_booking_data["user_name"],
        phone_number=sample_booking_data["phone_number"],
        time_slot=TimeSlot(sample_booking_data["time_slot"]),
        appointment_date=sample_booking_data["appointment_date"],
        send_sms=False
    )
    
    booking_id = create_result["booking_id"]
    
    # Retrieve it
    result = await booking_test_service.get_booking(booking_id)
    
    assert result["success"] is True
    assert result["booking"]["id"] == booking_id


@pytest.mark.asyncio
async def test_get_booking_not_found(booking_test_service):
    """Test retrieving non-existent booking."""
    result = await booking_test_service.get_booking("nonexistent_id")
    
    assert result["success"] is False


@pytest.mark.asyncio
async def test_get_user_bookings(booking_test_service, sample_booking_data):
    """Test retrieving all bookings for a user."""
    # Create a booking
    await booking_test_service.create_booking(
        service_type=ServiceType(sample_booking_data["service_type"]),
        user_name=sample_booking_data["user_name"],
        phone_number=sample_booking_data["phone_number"],
        time_slot=TimeSlot(sample_booking_data["time_slot"]),
        appointment_date=sample_booking_data["appointment_date"],
        send_sms=False
    )
    
    # Get user bookings
    result = await booking_test_service.get_user_bookings(
        sample_booking_data["phone_number"]
    )
    
    assert result["success"] is True
    assert "bookings" in result
    assert len(result["bookings"]) >= 1


# ============== Booking Update Tests ==============

@pytest.mark.asyncio
async def test_update_booking(booking_test_service, sample_booking_data):
    """Test updating a booking."""
    # Create booking
    create_result = await booking_test_service.create_booking(
        service_type=ServiceType(sample_booking_data["service_type"]),
        user_name=sample_booking_data["user_name"],
        phone_number=sample_booking_data["phone_number"],
        time_slot=TimeSlot(sample_booking_data["time_slot"]),
        appointment_date=sample_booking_data["appointment_date"],
        send_sms=False
    )
    
    booking_id = create_result["booking_id"]
    
    # Update it
    new_date = sample_booking_data["appointment_date"] + timedelta(days=1)
    result = await booking_test_service.update_booking(
        booking_id=booking_id,
        appointment_date=new_date
    )
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_cancel_booking(booking_test_service, sample_booking_data):
    """Test canceling a booking."""
    # Create booking
    create_result = await booking_test_service.create_booking(
        service_type=ServiceType(sample_booking_data["service_type"]),
        user_name=sample_booking_data["user_name"],
        phone_number=sample_booking_data["phone_number"],
        time_slot=TimeSlot(sample_booking_data["time_slot"]),
        appointment_date=sample_booking_data["appointment_date"],
        send_sms=False
    )
    
    booking_id = create_result["booking_id"]
    
    # Cancel it
    result = await booking_test_service.cancel_booking(
        booking_id=booking_id,
        send_sms=False
    )
    
    assert result["success"] is True


# ============== Availability Tests ==============

@pytest.mark.asyncio
async def test_get_available_dates(booking_test_service):
    """Test getting available dates for a service."""
    result = await booking_test_service.get_available_dates(
        service_type=ServiceType.PASSPORT,
        days_ahead=14
    )
    
    assert result["success"] is True
    assert "available_dates" in result
    assert isinstance(result["available_dates"], list)


# ============== Service Info Tests ==============

def test_get_service_info(booking_test_service):
    """Test getting service information."""
    info = booking_test_service.get_service_info("passport")
    
    assert info is not None
    assert "name" in info or "description" in info


def test_get_all_services(booking_test_service):
    """Test getting all available services."""
    services = booking_test_service.get_all_services()
    
    assert isinstance(services, dict)
    assert len(services) > 0


# ============== Booking Model Tests ==============

def test_booking_to_dict(sample_booking_data):
    """Test Booking model to_dict method."""
    booking = Booking(
        service_type=ServiceType(sample_booking_data["service_type"]),
        user_name=sample_booking_data["user_name"],
        phone_number=sample_booking_data["phone_number"],
        time_slot=TimeSlot(sample_booking_data["time_slot"]),
        appointment_date=sample_booking_data["appointment_date"]
    )
    
    booking_dict = booking.to_dict()
    
    assert isinstance(booking_dict, dict)
    assert "id" in booking_dict
    assert booking_dict["user_name"] == sample_booking_data["user_name"]


def test_booking_service_singleton():
    """Test that booking_service singleton exists."""
    assert booking_service is not None
    assert isinstance(booking_service, BookingService)
