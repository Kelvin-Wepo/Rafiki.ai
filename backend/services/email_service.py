"""
Email Service for Rafiki.ai
Handles sending OTP and notification emails via SMTP.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from rafiki_settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Thread pool for async email sending
_executor = ThreadPoolExecutor(max_workers=3)


class EmailService:
    """
    Service for sending emails via SMTP.
    Supports Gmail, SendGrid, and other SMTP providers.
    """
    
    def __init__(self):
        """Initialize email service."""
        self.settings = get_settings()
        self._initialized = False
    
    def _mask_email(self, email: str) -> str:
        """Mask email for logging."""
        if "@" not in email:
            return "***@***"
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            return f"{local[0]}***@{domain}"
        return f"{local[0]}***{local[-1]}@{domain}"
    
    def initialize(self) -> bool:
        """
        Verify SMTP configuration is valid.
        
        Returns:
            True if configuration is valid
        """
        if not self.settings.EMAIL_ENABLED:
            logger.warning("Email service disabled (EMAIL_ENABLED=False)")
            return False
        
        if not self.settings.SMTP_USERNAME or not self.settings.SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured")
            return False
        
        self._initialized = True
        logger.info("Email service initialized successfully")
        return True
    
    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email synchronously (called from thread pool).
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content (optional)
        
        Returns:
            Result dict with success status
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.settings.SMTP_FROM_NAME} <{self.settings.SMTP_FROM_EMAIL}>"
            msg["To"] = to_email
            
            # Add plain text version
            if text_body:
                part1 = MIMEText(text_body, "plain")
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_body, "html")
            msg.attach(part2)
            
            # Create secure connection
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                server.sendmail(
                    self.settings.SMTP_FROM_EMAIL,
                    to_email,
                    msg.as_string()
                )
            
            logger.info(f"Email sent to {self._mask_email(to_email)}")
            return {"success": True}
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return {"success": False, "error": "SMTP authentication failed"}
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email asynchronously.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content (optional)
        
        Returns:
            Result dict with success status
        """
        if not self._initialized:
            if not self.initialize():
                # Simulate success in development/testing
                if self.settings.DEBUG or self.settings.OTP_SIMULATE:
                    logger.info(f"[SIMULATION] Email would be sent to {self._mask_email(to_email)}")
                    return {"success": True, "simulated": True}
                return {"success": False, "error": "Email service not initialized"}
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            self._send_email_sync,
            to_email,
            subject,
            html_body,
            text_body
        )
        return result
    
    async def send_otp_email(
        self,
        to_email: str,
        otp: str,
        expiry_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Send OTP verification email.
        
        Args:
            to_email: Recipient email address
            otp: The OTP code
            expiry_minutes: OTP validity in minutes
        
        Returns:
            Result dict with success status
        """
        # Log OTP for debugging (same as SMS/voice)
        logger.warning(f"📧 EMAIL OTP - To: {self._mask_email(to_email)}, OTP: {otp}")
        print(f"\n{'='*60}")
        print(f"📧 EMAIL OTP for {to_email}: {otp}")
        print(f"{'='*60}\n", flush=True)
        
        subject = f"Your Rafiki.ai Verification Code: {otp}"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0D1117 0%, #1a1f2e 100%); padding: 30px; text-align: center;">
            <h1 style="color: #C8860A; margin: 0; font-size: 28px; font-weight: 600;">Rafiki.ai</h1>
            <p style="color: #ffffff99; margin: 8px 0 0 0; font-size: 14px;">Your Government Services Assistant</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 30px; text-align: center;">
            <h2 style="color: #333; margin: 0 0 20px 0; font-size: 22px;">Verification Code</h2>
            <p style="color: #666; margin: 0 0 30px 0; font-size: 16px; line-height: 1.5;">
                Use the code below to verify your account. This code will expire in {expiry_minutes} minutes.
            </p>
            
            <!-- OTP Code -->
            <div style="background: #FAF3E0; border: 2px dashed #C8860A; border-radius: 8px; padding: 20px; margin: 0 auto; max-width: 250px;">
                <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #7A3B1E;">{otp}</span>
            </div>
            
            <p style="color: #999; margin: 30px 0 0 0; font-size: 13px;">
                If you didn't request this code, you can safely ignore this email.
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background: #f9f9f9; padding: 20px 30px; text-align: center; border-top: 1px solid #eee;">
            <p style="color: #999; margin: 0; font-size: 12px;">
                This is an automated message from Rafiki.ai.<br>
                Please do not reply to this email.
            </p>
        </div>
    </div>
</body>
</html>
"""
        
        text_body = f"""
Rafiki.ai - Verification Code

Your verification code is: {otp}

This code will expire in {expiry_minutes} minutes.

If you didn't request this code, you can safely ignore this email.

---
This is an automated message from Rafiki.ai.
"""
        
        return await self.send_email(to_email, subject, html_body, text_body)
    
    async def send_welcome_email(
        self,
        to_email: str,
        full_name: str
    ) -> Dict[str, Any]:
        """
        Send welcome email after successful registration.
        
        Args:
            to_email: Recipient email address
            full_name: User's full name
        
        Returns:
            Result dict with success status
        """
        first_name = full_name.split()[0] if full_name else "there"
        subject = f"Welcome to Rafiki.ai, {first_name}! 🎉"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0D1117 0%, #1a1f2e 100%); padding: 30px; text-align: center;">
            <h1 style="color: #C8860A; margin: 0; font-size: 28px; font-weight: 600;">Welcome to Rafiki.ai! 🎉</h1>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 30px;">
            <h2 style="color: #333; margin: 0 0 20px 0;">Habari {first_name}!</h2>
            <p style="color: #666; margin: 0 0 20px 0; font-size: 16px; line-height: 1.6;">
                Your account has been successfully created. You can now access government services 
                through our AI-powered assistant.
            </p>
            
            <div style="background: #FAF3E0; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h3 style="color: #7A3B1E; margin: 0 0 10px 0;">What you can do:</h3>
                <ul style="color: #666; margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li>Book appointments with government agencies</li>
                    <li>Check service requirements</li>
                    <li>Track your applications</li>
                    <li>Get directions to Huduma Centres</li>
                    <li>Access KRA, NTSA, and more services</li>
                </ul>
            </div>
            
            <p style="color: #666; margin: 20px 0 0 0; font-size: 14px;">
                Have questions? Just start a conversation with Rafiki!
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background: #f9f9f9; padding: 20px 30px; text-align: center; border-top: 1px solid #eee;">
            <p style="color: #999; margin: 0; font-size: 12px;">
                Rafiki.ai - Your Government. Made Simple.
            </p>
        </div>
    </div>
</body>
</html>
"""
        
        text_body = f"""
Welcome to Rafiki.ai, {first_name}! 🎉

Your account has been successfully created. You can now access government services through our AI-powered assistant.

What you can do:
- Book appointments with government agencies
- Check service requirements
- Track your applications
- Get directions to Huduma Centres
- Access KRA, NTSA, and more services

Have questions? Just start a conversation with Rafiki!

---
Rafiki.ai - Your Government. Made Simple.
"""
        
        return await self.send_email(to_email, subject, html_body, text_body)


# Singleton instance
email_service = EmailService()


def get_email_service() -> EmailService:
    """Get the email service singleton."""
    return email_service
