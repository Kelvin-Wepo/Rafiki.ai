"""
paystack_service.py
-------------------
Rafiki.ai – Paystack M-PESA payment integration
Handles STK push initiation and payment verification via Paystack's API.

Docs: https://paystack.com/docs/payments/mobile-money/
"""

import logging
from typing import Optional

import httpx

from rafiki_settings import get_settings
from utils.phone import to_paystack_msisdn

logger = logging.getLogger(__name__)

PAYSTACK_BASE_URL = "https://api.paystack.co"

# Kenya M-PESA via Paystack uses the "mobile_money" channel with provider "mpesa"
PAYSTACK_CURRENCY = "KES"
PAYSTACK_PROVIDER = "mpesa"


def _paystack_secret() -> str:
    return (get_settings().PAYSTACK_SECRET_KEY or "").strip()


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_paystack_secret()}",
        "Content-Type": "application/json",
    }


def _format_phone(phone: str) -> str:
    """Normalize Kenyan phone to 2547XXXXXXXX for Paystack (no plus)."""
    return to_paystack_msisdn(phone)


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
        callback_url: Optional redirect URL after hosted checkout (webhook is dashboard-configured)

    Returns:
        dict with keys: success (bool), reference, display_text, message
    """
    secret = _paystack_secret()
    if not secret:
        logger.error("PAYSTACK_SECRET_KEY is not set; cannot send an M-PESA STK prompt")
        return {
            "success": False,
            "reference": reference,
            "message": "Paystack is not configured. Set PAYSTACK_SECRET_KEY to send an M-PESA prompt.",
        }

    try:
        formatted_phone = _format_phone(phone)
    except ValueError as e:
        logger.error(f"Paystack phone formatting failed: {e}")
        return {"success": False, "message": str(e)}

    amount_kobo = amount_ksh * 100  # Paystack uses smallest currency unit
    settings = get_settings()
    resolved_callback = (callback_url or settings.PAYSTACK_CALLBACK_URL or "").strip() or None

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
    if resolved_callback:
        payload["callback_url"] = resolved_callback

    logger.info(f"Paystack STK push - phone={formatted_phone} amount={amount_ksh} ref={reference}")

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
                display_text = charge_data.get(
                    "display_text",
                    "Check your phone and enter your M-PESA PIN to complete payment.",
                )
                logger.info(f"STK push initiated: ref={reference}, phone={formatted_phone}")
                return {
                    "success": True,
                    "reference": reference,
                    "charge_status": charge_data.get("status"),
                    "display_text": display_text,
                    "message": "STK push initiated successfully.",
                }

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
    if not _paystack_secret():
        return {
            "success": True,
            "paid": False,
            "status": "unconfigured",
            "amount_ksh": 0,
            "message": "Paystack is not configured. Payment cannot be confirmed.",
        }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                headers=_headers(),
            )
            data = response.json()

            if response.status_code == 200 and data.get("status"):
                tx = data.get("data", {})
                tx_status = (tx.get("status") or "").lower()
                paid = tx_status == "success"
                amount_ksh = tx.get("amount", 0) // 100
                transaction_id = str(tx.get("id") or "")

                logger.info(f"Payment verification: ref={reference}, status={tx_status}, paid={paid}")
                return {
                    "success": True,
                    "paid": paid,
                    "status": tx_status,
                    "amount_ksh": amount_ksh,
                    "transaction_id": transaction_id,
                    "gateway_response": tx.get("gateway_response", ""),
                    "message": "Payment confirmed." if paid else f"Payment status: {tx_status}",
                }

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
    import time
    import uuid
    short_uuid = str(uuid.uuid4()).replace("-", "")[:8].upper()
    service_code = service.replace(" ", "_").upper()[:10]
    timestamp = int(time.time())
    return f"RAFIKI-{service_code}-{timestamp}-{short_uuid}"
