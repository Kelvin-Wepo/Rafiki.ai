"""Kenyan MSISDN helpers for Paystack (no plus) and Africa's Talking (+254)."""

from __future__ import annotations


def normalize_kenyan_msisdn(phone: str) -> str:
    """Return a 12-digit Kenyan MSISDN starting with 254.

    Accepts 07XXXXXXXX, 7XXXXXXXX, 2547XXXXXXXX, or +2547XXXXXXXX.
    """
    raw = (phone or "").strip()
    digits = "".join(ch for ch in raw if ch.isdigit())

    if digits.startswith("254") and len(digits) == 12:
        msisdn = digits
    elif digits.startswith("0") and len(digits) == 10:
        msisdn = "254" + digits[1:]
    elif digits.startswith("7") and len(digits) == 9:
        msisdn = "254" + digits
    else:
        raise ValueError(
            "Invalid Kenyan phone number. Use 07XXXXXXXX, 2547XXXXXXXX, or +2547XXXXXXXX."
        )

    if not (msisdn.startswith("254") and len(msisdn) == 12):
        raise ValueError(
            "Invalid Kenyan phone number. Use 07XXXXXXXX, 2547XXXXXXXX, or +2547XXXXXXXX."
        )
    return msisdn


def to_paystack_msisdn(phone: str) -> str:
    """Paystack Kenya M-PESA expects 2547XXXXXXXX with no plus."""
    return normalize_kenyan_msisdn(phone)


def to_africastalking_msisdn(phone: str) -> str:
    """Africa's Talking expects +2547XXXXXXXX."""
    return "+" + normalize_kenyan_msisdn(phone)
