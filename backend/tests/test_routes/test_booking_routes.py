"""Tests for booking routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from main import app
from models.schemas import ServiceType, TimeSlot, BookingStatus


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_booking_service():
    """Mock booking service."""
    with patch("routes.booking.booking_service") as mock:
        yield mock


class TestBookingRoutes:
    """Test booking endpoints."""

    def test_create_booking_success(self, client, mock_booking_service):
        """Test successful booking creation."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        mock_booking_service.create_booking.return_value = {
            "success": True,
            "message": "Booking created successfully",
            "booking": {
                "booking_id": "BK001",
                "service_type": "passport",
                "user_name": "John Doe",
                "phone_number": "+254712345678",
                "appointment_date": tomorrow.isoformat(),
                "time_slot": "08:00-12:00",
                "status": "confirmed"
            },
            "sms_sent": True
        }
        
        response = client.post(
            "/booking/create",
            json={
                "service_type": "passport",
                "user_name": "John Doe",
                "phone_number": "+254712345678",
                "appointment_date": tomorrow.isoformat(),
                "time_slot": "morning"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["booking_id"] == "BK001"
        assert data["sms_sent"] is True

    def test_create_booking_past_date(self, client, mock_booking_service):
        """Test booking with past date."""
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        mock_booking_service.create_booking.return_value = {
            "success": False,
            "error": "Cannot book for past date"
        }
        
        response = client.post(
            "/booking/create",
            json={
                "service_type": "passport",
                "user_name": "John Doe",
                "phone_number": "+254712345678",
                "appointment_date": yesterday.isoformat(),
                "time_slot": "morning"
            }
        )
        
        assert response.status_code == 400

    def test_create_booking_duplicate(self, client, mock_booking_service):
        """Test duplicate booking prevention."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        mock_booking_service.create_booking.return_value = {
            "success": False,
            "error": "Duplicate booking exists"
        }
        
        response = client.post(
            "/booking/create",
            json={
                "service_type": "passport",
                "user_name": "Jane Doe",
                "phone_number": "+254701234567",
                "appointment_date": tomorrow.isoformat(),
                "time_slot": "afternoon"
            }
        )
        
        assert response.status_code == 400

    def test_get_booking_success(self, client, mock_booking_service):
        """Test retrieving booking by ID."""
        mock_booking_service.get_booking.return_value = {
            "booking_id": "BK001",
            "service_type": "passport",
            "user_name": "John Doe",
            "phone_number": "+254712345678",
            "status": "confirmed"
        }
        
        response = client.get("/booking/BK001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["booking_id"] == "BK001"
        assert data["status"] == "confirmed"

    def test_get_booking_not_found(self, client, mock_booking_service):
        """Test retrieving non-existent booking."""
        mock_booking_service.get_booking.return_value = None
        
        response = client.get("/booking/BK999")
        
        assert response.status_code == 404

    def test_get_user_bookings(self, client, mock_booking_service):
        """Test retrieving user's bookings."""
        mock_booking_service.get_user_bookings.return_value = [
            {
                "booking_id": "BK001",
                "service_type": "passport",
                "status": "confirmed"
            },
            {
                "booking_id": "BK002",
                "service_type": "national_id",
                "status": "pending"
            }
        ]
        
        response = client.get(
            "/booking/user/254712345678"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["booking_id"] == "BK001"

    def test_update_booking_success(self, client, mock_booking_service):
        """Test updating booking."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        mock_booking_service.update_booking.return_value = {
            "success": True,
            "message": "Booking updated",
            "booking": {
                "booking_id": "BK001",
                "appointment_date": tomorrow.isoformat(),
                "time_slot": "14:00-17:00",
                "status": "updated"
            }
        }
        
        response = client.put(
            "/booking/BK001",
            json={
                "appointment_date": tomorrow.isoformat(),
                "time_slot": "afternoon"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_cancel_booking_success(self, client, mock_booking_service):
        """Test cancelling booking."""
        mock_booking_service.cancel_booking.return_value = {
            "success": True,
            "message": "Booking cancelled",
            "booking": {
                "booking_id": "BK001",
                "status": "cancelled"
            }
        }
        
        response = client.delete("/booking/BK001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["booking"]["status"] == "cancelled"

    def test_get_available_dates(self, client, mock_booking_service):
        """Test retrieving available appointment dates."""
        mock_booking_service.get_available_dates.return_value = {
            "service_type": "passport",
            "available_dates": [
                {"date": "2026-02-05", "available_slots": 5},
                {"date": "2026-02-06", "available_slots": 3},
                {"date": "2026-02-07", "available_slots": 8}
            ]
        }
        
        response = client.get("/booking/available-dates/passport")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["available_dates"]) == 3
        assert data["available_dates"][0]["available_slots"] > 0

    def test_get_service_info(self, client, mock_booking_service):
        """Test retrieving service information."""
        mock_booking_service.get_service_info.return_value = {
            "service_type": "passport",
            "description": "Passport application service",
            "required_documents": ["ID", "Birth Certificate"],
            "processing_time": "2-4 weeks",
            "fee": 3000
        }
        
        response = client.get("/booking/service-info/passport")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service_type"] == "passport"
        assert "required_documents" in data

    def test_get_all_services(self, client, mock_booking_service):
        """Test retrieving all available services."""
        mock_booking_service.get_all_services.return_value = [
            {
                "service_type": "passport",
                "description": "Passport application",
                "fee": 3000
            },
            {
                "service_type": "national_id",
                "description": "National ID application",
                "fee": 1000
            },
            {
                "service_type": "driving_license",
                "description": "Driving license",
                "fee": 2000
            }
        ]
        
        response = client.get("/booking/services")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert data[0]["service_type"] == "passport"

    def test_invalid_service_type(self, client, mock_booking_service):
        """Test booking with invalid service type."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        mock_booking_service.create_booking.return_value = {
            "success": False,
            "error": "Invalid service type"
        }
        
        response = client.post(
            "/booking/create",
            json={
                "service_type": "invalid_service",
                "user_name": "John Doe",
                "phone_number": "+254712345678",
                "appointment_date": tomorrow.isoformat(),
                "time_slot": "morning"
            }
        )
        
        assert response.status_code == 400
