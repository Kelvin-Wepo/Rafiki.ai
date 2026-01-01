"""
SMS service using Africa's Talking API.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import africastalking
try:
    import africastalking
    AFRICASTALKING_AVAILABLE = True
except ImportError:
    AFRICASTALKING_AVAILABLE = False
    logger.warning("africastalking library not installed")


class SMSService:
    """
    Service for sending SMS notifications via Africa's Talking.
    """
    
    def __init__(self):
        """Initialize SMS service."""
        self.settings = get_settings()
        self._sms_client = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the Africa's Talking SMS client.
        
        Returns:
            True if initialization successful
        """
        if not AFRICASTALKING_AVAILABLE:
            logger.error("africastalking library not available")
            return False
        
        try:
            username = self.settings.AFRICASTALKING_USERNAME
            api_key = self.settings.AFRICASTALKING_API_KEY
            
            if not username or not api_key:
                logger.error("Africa's Talking credentials not configured")
                return False
            
            africastalking.initialize(username=username, api_key=api_key)
            self._sms_client = africastalking.SMS
            self._initialized = True
            
            logger.info("SMS service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SMS service: {e}")
            return False
    
    async def send_booking_confirmation(
        self,
        phone_number: str,
        booking_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send booking confirmation SMS.
        
        Args:
            phone_number: Recipient phone number
            booking_details: Booking information
        
        Returns:
            SMS send result
        """
        if not self._initialized:
            if not self.initialize():
                return {
                    "success": False,
                    "error": "SMS service not initialized"
                }
        
        try:
            service_name = booking_details.get("service_name", "Government Service")
            time_slot = booking_details.get("time_slot", "scheduled time")
            date = booking_details.get("date", "scheduled date")
            booking_id = booking_details.get("booking_id", "N/A")
            
            message = (
                f"eCitizen Booking Confirmed!\n\n"
                f"Service: {service_name}\n"
                f"Date: {date}\n"
                f"Time: {time_slot}\n"
                f"Booking ID: {booking_id}\n\n"
                f"Please arrive 15 minutes early with required documents.\n"
                f"Thank you for using eCitizen services."
            )
            
            return await self.send_sms(phone_number, message)
            
        except Exception as e:
            logger.error(f"Failed to send booking confirmation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an SMS message.
        
        Args:
            phone_number: Recipient phone number (or list of numbers)
            message: Message content
            sender_id: Optional sender ID
        
        Returns:
            Send result with status
        """
        if not self._initialized:
            if not self.initialize():
                return {
                    "success": False,
                    "error": "SMS service not initialized"
                }
        
        try:
            # Ensure phone number is a list
            recipients = [phone_number] if isinstance(phone_number, str) else phone_number
            
            # Use configured sender ID if not provided
            sender = sender_id or self.settings.AFRICASTALKING_SENDER_ID
            
            logger.info(f"Sending SMS to {recipients}")
            
            # Send SMS
            if sender:
                response = self._sms_client.send(message, recipients, sender_id=sender)
            else:
                response = self._sms_client.send(message, recipients)
            
            logger.info(f"SMS response: {response}")
            
            # Parse response
            sms_data = response.get("SMSMessageData", {})
            recipients_data = sms_data.get("Recipients", [])
            
            success_count = sum(
                1 for r in recipients_data 
                if r.get("status") == "Success"
            )
            
            return {
                "success": success_count > 0,
                "message_id": sms_data.get("Message", ""),
                "recipients": recipients_data,
                "cost": sms_data.get("TotalCost", "0"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_reminder(
        self,
        phone_number: str,
        booking_details: Dict[str, Any],
        hours_before: int = 24
    ) -> Dict[str, Any]:
        """
        Send appointment reminder SMS.
        
        Args:
            phone_number: Recipient phone number
            booking_details: Booking information
            hours_before: Hours before appointment
        
        Returns:
            SMS send result
        """
        service_name = booking_details.get("service_name", "your appointment")
        time_slot = booking_details.get("time_slot", "scheduled time")
        date = booking_details.get("date", "tomorrow")
        
        message = (
            f"Reminder: You have a {service_name} appointment "
            f"on {date} at {time_slot}.\n\n"
            f"Required documents:\n"
            f"- National ID\n"
            f"- Passport photos\n\n"
            f"Please arrive 15 minutes early."
        )
        
        return await self.send_sms(phone_number, message)
    
    async def send_cancellation(
        self,
        phone_number: str,
        booking_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send booking cancellation SMS.
        
        Args:
            phone_number: Recipient phone number
            booking_details: Booking information
        
        Returns:
            SMS send result
        """
        service_name = booking_details.get("service_name", "your appointment")
        booking_id = booking_details.get("booking_id", "N/A")
        
        message = (
            f"Your {service_name} booking (ID: {booking_id}) has been cancelled.\n\n"
            f"If you did not request this cancellation, please contact support.\n"
            f"You can book a new appointment anytime through eCitizen."
        )
        
        return await self.send_sms(phone_number, message)
    
    def get_balance(self) -> Optional[str]:
        """Get SMS balance from Africa's Talking."""
        if not self._initialized:
            if not self.initialize():
                return None
        
        try:
            application = africastalking.Application
            response = application.fetch_application_data()
            return response.get("UserData", {}).get("balance", "Unknown")
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            return None


# Global service instance
sms_service = SMSService()
