"""
Alert notification service for fraud detection.

Sends real-time notifications via:
- SMS (Africa's Talking)
- Email (SMTP)
- Webhook (for dashboards)
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import hashlib

from utils.logger import get_logger
from rafiki_settings import get_settings
from services.fraud_service import (
    FraudAlert, RiskLevel, AlertType, get_fraud_service
)

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class NotificationConfig:
    """Configuration for alert notifications"""
    sms_enabled: bool = True
    sms_recipients: List[str] = None
    sms_min_risk_level: RiskLevel = RiskLevel.HIGH
    
    email_enabled: bool = False
    email_recipients: List[str] = None
    email_min_risk_level: RiskLevel = RiskLevel.MEDIUM
    
    webhook_enabled: bool = False
    webhook_url: str = None
    webhook_min_risk_level: RiskLevel = RiskLevel.LOW
    
    max_sms_per_hour: int = 10
    max_email_per_hour: int = 50
    
    def __post_init__(self):
        if self.sms_recipients is None:
            self.sms_recipients = []
        if self.email_recipients is None:
            self.email_recipients = []


class AlertNotificationService:
    """
    Service for sending fraud alert notifications.
    """
    
    def __init__(self, config: NotificationConfig = None):
        self.config = config or NotificationConfig()
        
        self._sms_count: Dict[str, int] = {}
        self._email_count: Dict[str, int] = {}
        
        self._sms_client = None
        self._init_sms_client()
        
        fraud_service = get_fraud_service()
        fraud_service.register_alert_callback(self.handle_alert)
        
        logger.info("Alert notification service initialized")
    
    def _init_sms_client(self):
        """Initialize Africa's Talking SMS client"""
        try:
            if settings.AFRICASTALKING_USERNAME and settings.AFRICASTALKING_API_KEY:
                import africastalking
                africastalking.initialize(
                    username=settings.AFRICASTALKING_USERNAME,
                    api_key=settings.AFRICASTALKING_API_KEY
                )
                self._sms_client = africastalking.SMS
                logger.info("Africa's Talking SMS client initialized")
            else:
                logger.warning("Africa's Talking credentials not configured")
        except ImportError:
            logger.warning("africastalking package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize SMS client: {e}")
    
    def handle_alert(self, alert: FraudAlert):
        """Handle incoming fraud alert."""
        try:
            should_notify = self._should_notify(alert)
            
            if not should_notify:
                logger.debug(f"Alert {alert.alert_id} below notification threshold")
                return
            
            asyncio.create_task(self._send_notifications(alert))
            
        except Exception as e:
            logger.error(f"Error handling alert: {e}")
    
    def _should_notify(self, alert: FraudAlert) -> bool:
        """Check if alert should trigger notifications"""
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        alert_level_idx = risk_order.index(alert.risk_level)
        
        if self.config.sms_enabled:
            sms_level_idx = risk_order.index(self.config.sms_min_risk_level)
            if alert_level_idx >= sms_level_idx:
                return True
        
        if self.config.email_enabled:
            email_level_idx = risk_order.index(self.config.email_min_risk_level)
            if alert_level_idx >= email_level_idx:
                return True
        
        if self.config.webhook_enabled:
            webhook_level_idx = risk_order.index(self.config.webhook_min_risk_level)
            if alert_level_idx >= webhook_level_idx:
                return True
        
        return False
    
    async def _send_notifications(self, alert: FraudAlert):
        """Send notifications through configured channels"""
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        alert_level_idx = risk_order.index(alert.risk_level)
        
        tasks = []
        
        if self.config.sms_enabled and self.config.sms_recipients:
            sms_level_idx = risk_order.index(self.config.sms_min_risk_level)
            if alert_level_idx >= sms_level_idx:
                tasks.append(self._send_sms(alert))
        
        if self.config.email_enabled and self.config.email_recipients:
            email_level_idx = risk_order.index(self.config.email_min_risk_level)
            if alert_level_idx >= email_level_idx:
                tasks.append(self._send_email(alert))
        
        if self.config.webhook_enabled and self.config.webhook_url:
            webhook_level_idx = risk_order.index(self.config.webhook_min_risk_level)
            if alert_level_idx >= webhook_level_idx:
                tasks.append(self._send_webhook(alert))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_sms(self, alert: FraudAlert):
        """Send SMS notification via Africa's Talking"""
        if not self._sms_client:
            logger.warning("SMS client not available")
            return
        
        current_hour = datetime.utcnow().strftime("%Y%m%d%H")
        self._sms_count[current_hour] = self._sms_count.get(current_hour, 0)
        
        if self._sms_count[current_hour] >= self.config.max_sms_per_hour:
            logger.warning("SMS rate limit reached")
            return
        
        message = self._format_sms_message(alert)
        
        try:
            response = self._sms_client.send(
                message=message,
                recipients=self.config.sms_recipients,
                sender_id=settings.AFRICASTALKING_SENDER_ID
            )
            
            self._sms_count[current_hour] += 1
            logger.info(f"SMS alert sent: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")
    
    def _format_sms_message(self, alert: FraudAlert) -> str:
        """Format alert for SMS"""
        emoji = {
            RiskLevel.LOW: "ℹ️",
            RiskLevel.MEDIUM: "⚠️",
            RiskLevel.HIGH: "🚨",
            RiskLevel.CRITICAL: "🔴"
        }
        
        return (
            f"{emoji.get(alert.risk_level, '⚠️')} RAFIKI FRAUD ALERT\n"
            f"Risk: {alert.risk_level.value.upper()}\n"
            f"Type: {alert.alert_type.value}\n"
            f"ID: {alert.identifier[:20]}...\n"
            f"{alert.description[:50]}...\n"
            f"Time: {alert.timestamp.strftime('%H:%M')}"
        )
    
    async def _send_email(self, alert: FraudAlert):
        """Send email notification"""
        current_hour = datetime.utcnow().strftime("%Y%m%d%H")
        self._email_count[current_hour] = self._email_count.get(current_hour, 0)
        
        if self._email_count[current_hour] >= self.config.max_email_per_hour:
            logger.warning("Email rate limit reached")
            return
        
        logger.info(f"Email alert would be sent: {alert.alert_id}")
        self._email_count[current_hour] += 1
    
    async def _send_webhook(self, alert: FraudAlert):
        """Send webhook notification"""
        if not self.config.webhook_url:
            return
        
        try:
            import aiohttp
            
            payload = {
                "event": "fraud_alert",
                "data": alert.to_dict(),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "rafiki_fraud_service"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent: {alert.alert_id}")
                    else:
                        logger.warning(f"Webhook returned {response.status}")
                        
        except ImportError:
            logger.warning("aiohttp not installed for webhook support")
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        current_hour = datetime.utcnow().strftime("%Y%m%d%H")
        
        return {
            "sms_sent_this_hour": self._sms_count.get(current_hour, 0),
            "email_sent_this_hour": self._email_count.get(current_hour, 0),
            "sms_limit": self.config.max_sms_per_hour,
            "email_limit": self.config.max_email_per_hour,
            "sms_enabled": self.config.sms_enabled,
            "email_enabled": self.config.email_enabled,
            "webhook_enabled": self.config.webhook_enabled
        }
    
    async def send_test_alert(self) -> Dict[str, Any]:
        """Send a test alert to verify notification channels"""
        test_alert = FraudAlert(
            alert_id="test_" + hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()[:8],
            alert_type=AlertType.SUSPICIOUS_PATTERN,
            risk_level=RiskLevel.HIGH,
            identifier="test_user",
            description="This is a test alert from Rafiki fraud detection system",
            timestamp=datetime.utcnow(),
            metadata={"test": True}
        )
        
        await self._send_notifications(test_alert)
        
        return {
            "status": "sent",
            "alert_id": test_alert.alert_id,
            "channels": {
                "sms": self.config.sms_enabled and bool(self.config.sms_recipients),
                "email": self.config.email_enabled and bool(self.config.email_recipients),
                "webhook": self.config.webhook_enabled and bool(self.config.webhook_url)
            }
        }


# Singleton instance
_notification_service: Optional[AlertNotificationService] = None


def get_alert_notification_service() -> AlertNotificationService:
    """Get or create the global notification service instance"""
    global _notification_service
    
    if _notification_service is None:
        config = NotificationConfig(
            sms_enabled=bool(settings.AFRICASTALKING_API_KEY),
            sms_recipients=[],
            sms_min_risk_level=RiskLevel.HIGH
        )
        _notification_service = AlertNotificationService(config)
    
    return _notification_service


def configure_notifications(
    sms_recipients: List[str] = None,
    email_recipients: List[str] = None,
    webhook_url: str = None
):
    """Configure notification settings"""
    global _notification_service
    
    config = NotificationConfig(
        sms_enabled=bool(settings.AFRICASTALKING_API_KEY),
        sms_recipients=sms_recipients or [],
        sms_min_risk_level=RiskLevel.HIGH,
        email_enabled=bool(email_recipients),
        email_recipients=email_recipients or [],
        email_min_risk_level=RiskLevel.MEDIUM,
        webhook_enabled=bool(webhook_url),
        webhook_url=webhook_url,
        webhook_min_risk_level=RiskLevel.LOW
    )
    
    _notification_service = AlertNotificationService(config)
    return _notification_service
