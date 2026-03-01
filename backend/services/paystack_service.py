"""
paystack_service.py
-------------------
Rafiki.ai – Paystack M-PESA payment integration
Handles STK push initiation and payment verification via Paystack's API.

Docs: https://paystack.com/docs/payments/mobile-money/
"""

import logging
import httpx
from typing import Optional

from rafiki_settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_BASE_URL = "https://api.paystack.co"

# Kenya M-PESA via Paystack uses the "mobile_money" channel with provider "mpesa"
PAYSTACK_CURRENCY = "KES"
PAYSTACK_PROVIDER = "mpesa"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def _format_phone(phone: str) -> str:
    """Normalize Kenyan phone to 07XXXXXXXX format for Paystack."""
    phone = phone.strip().replace(" ", "")
    if phone.startswith("+254"):
        phone = "0" + phone[4:]
    elif phone.startswith("254"):
        phone = "0" + phone[3:]
    return phone


async def initiate_stk_push(
    phone: str,
    amount_ksh: int,
    email: str,
    reference: str,
    description: str = "Rafiki.ai Government Service Payment",
    callback_url: Optional[str] = None,
) -> dict:
    """
    Initiate an M-PESA STK push via Paystack.

    Args:
        phone:        Customer phone number (07XXXXXXXX / +2547XXXXXXXX)
        amount_ksh:   Amount in Kenyan Shillings (Paystack expects kobo/cents × 100)
        email:        Customer email (required by Paystack)
        reference:    Unique transaction reference
        description:  Payment description shown to customer
        callback_url: Webhook URL for payment confirmation

    Returns:
        dict with keys: success (bool), reference, authorization_url, message
    """
    if not PAYSTACK_SECRET_KEY:
        logger.error("PAYSTACK_SECRET_KEY is not set")
        return {"success": False, "message": "Payment service not configured. Please contact support."}

    formatted_phone = _format_phone(phone)
    amount_kobo = amount_ksh * 100  # Paystack uses smallest currency unit

    payload = {
        "email": email,
        "amount": amount_kobo,
        "currency": PAYSTACK_CURRENCY,
        "reference": reference,
        "channels": ["mobile_money"],
        "mobile_money": {
            "phone": formatted_phone,
            "provider": PAYSTACK_PROVIDER,
        },
        "metadata": {
            "description": description,
            "platform": "rafiki_ai",
        },
    }

    if callback_url:
        payload["callback_url"] = callback_url

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{PAYSTACK_BASE_URL}/charge",
                json=payload,
                headers=_headers(),
            )
            data = response.json()

            if response.status_code == 200 and data.get("status"):
                charge_data = data.get("data", {})
                logger.info(f"STK push initiated: ref={reference}, phone={formatted_phone}")
                return {
                    "success": True,
                    "reference": reference,
                    "charge_status": charge_data.get("status"),
                    "display_text": charge_data.get("display_text", "Check your phone for the M-PESA prompt."),
                    "message": "STK push initiated successfully.",
                }
            else:
                logger.error(f"Paystack charge failed: {data}")
                return {
                    "success": False,
                    "message": data.get("message", "Payment initiation failed. Please try again."),
                }

    except httpx.RequestError as e:
        logger.error(f"Paystack request error: {e}")
        return {"success": False, "message": "Could not reach payment service. Please try again."}


async def verify_payment(reference: str) -> dict:
    """
    Verify the status of a Paystack transaction.

    Args:
        reference: The transaction reference returned from initiate_stk_push

    Returns:
        dict with keys: success (bool), paid (bool), amount_ksh, message
    """
    if not PAYSTACK_SECRET_KEY:
        return {"success": False, "paid": False, "message": "Payment service not configured."}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                headers=_headers(),
            )
            data = response.json()

            if response.status_code == 200 and data.get("status"):
                tx = data.get("data", {})
                tx_status = tx.get("status", "").lower()
                paid = tx_status == "success"
                amount_ksh = tx.get("amount", 0) // 100

                logger.info(f"Payment verification: ref={reference}, status={tx_status}, paid={paid}")
                return {
                    "success": True,
                    "paid": paid,
                    "status": tx_status,
                    "amount_ksh": amount_ksh,
                    "gateway_response": tx.get("gateway_response", ""),
                    "message": "Payment confirmed." if paid else f"Payment status: {tx_status}",
                }
            else:
                return {
                    "success": False,
                    "paid": False,
                    "message": data.get("message", "Could not verify payment."),
                }

    except httpx.RequestError as e:
        logger.error(f"Paystack verification error: {e}")
        return {"success": False, "paid": False, "message": "Could not reach payment service."}


def generate_reference(session_id: str, service: str) -> str:
    """Generate a unique, readable transaction reference."""
    import uuid, time
    short_uuid = str(uuid.uuid4()).replace("-", "")[:8].upper()
    service_code = service.replace(" ", "_").upper()[:10]
    timestamp = int(time.time())
    return f"RAFIKI-{service_code}-{timestamp}-{short_uuid}"