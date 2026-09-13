from utils.phone import (
    normalize_kenyan_msisdn,
    to_africastalking_msisdn,
    to_paystack_msisdn,
)
import pytest


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("0712345678", "254712345678"),
        ("+254712345678", "254712345678"),
        ("254712345678", "254712345678"),
        ("712345678", "254712345678"),
        ("07 123 45678", "254712345678"),
    ],
)
def test_normalize_kenyan_msisdn(raw, expected):
    assert normalize_kenyan_msisdn(raw) == expected
    assert to_paystack_msisdn(raw) == expected
    assert to_africastalking_msisdn(raw) == "+" + expected


def test_invalid_phone_raises():
    with pytest.raises(ValueError):
        normalize_kenyan_msisdn("123")
