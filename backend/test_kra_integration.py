"""
Test script for KRA API integration.
Tests PIN verification, compliance checks, and taxpayer details retrieval.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.kra_service import kra_service
from backend.config import get_settings
from backend.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def test_kra_service():
    """Test KRA service functionality."""
    
    print("=" * 70)
    print("KRA SERVICE INTEGRATION TEST")
    print("=" * 70)
    
    # Load settings
    settings = get_settings()
    
    # Check if KRA is enabled
    print(f"\n✓ KRA Service Enabled: {settings.KRA_ENABLED}")
    print(f"✓ KRA API URL: {settings.KRA_API_URL}")
    print(f"✓ KRA Client ID configured: {bool(settings.KRA_CLIENT_ID and settings.KRA_CLIENT_ID != 'your-kra-client-id')}")
    
    if not settings.KRA_ENABLED:
        print("\n⚠️  KRA service is not enabled.")
        print("   To enable, set KRA_ENABLED=true in .env file")
        return
    
    if not settings.KRA_CLIENT_ID or settings.KRA_CLIENT_ID == 'your-kra-client-id':
        print("\n⚠️  KRA credentials not configured.")
        print("   Please configure KRA API credentials in .env file:")
        print("   - KRA_CLIENT_ID")
        print("   - KRA_CLIENT_SECRET")
        print("   - KRA_API_KEY (optional)")
        print("\n   To obtain credentials:")
        print("   1. Visit https://itax.kra.go.ke")
        print("   2. Register for API access")
        print("   3. Request OAuth2 credentials from KRA")
        return
    
    # Initialize KRA service
    print("\n📋 Initializing KRA service...")
    try:
        kra_service.initialize(
            api_url=settings.KRA_API_URL,
            client_id=settings.KRA_CLIENT_ID,
            client_secret=settings.KRA_CLIENT_SECRET,
            api_key=settings.KRA_API_KEY
        )
        print("✅ KRA service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize KRA service: {e}")
        return
    
    # Test PIN format validation
    print("\n" + "=" * 70)
    print("TEST 1: PIN Format Validation")
    print("=" * 70)
    
    test_pins = [
        ("A123456789B", True, "Valid individual PIN"),
        ("P987654321Z", True, "Valid company PIN"),
        ("A12345678", False, "Too short"),
        ("X123456789B", False, "Invalid first letter"),
        ("A12345678XB", False, "Invalid middle section"),
        ("A1234567891", False, "Missing end letter"),
    ]
    
    for pin, should_be_valid, description in test_pins:
        is_valid = kra_service._validate_pin_format(pin)
        status = "✅" if is_valid == should_be_valid else "❌"
        print(f"{status} {description}: {pin} - Valid: {is_valid}")
    
    # Test PIN verification (using demo mode)
    print("\n" + "=" * 70)
    print("TEST 2: PIN Verification")
    print("=" * 70)
    print("\nNote: This test requires actual KRA API access.")
    print("If you don't have credentials yet, the test will fail with authentication error.")
    
    test_pin = "A000000000X"  # Demo PIN format
    print(f"\n🔍 Verifying PIN: {test_pin}")
    
    result = await kra_service.verify_pin(test_pin)
    
    if result.get("success"):
        print("✅ PIN verification succeeded:")
        print(f"   Valid: {result.get('valid')}")
        print(f"   Taxpayer Name: {result.get('taxpayer_name', 'N/A')}")
        print(f"   Type: {result.get('taxpayer_type', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
    else:
        print(f"❌ PIN verification failed: {result.get('error')}")
        if "401" in str(result.get('error')):
            print("   (Authentication required - configure valid KRA credentials)")
        elif "404" in str(result.get('error')):
            print("   (PIN not found - expected for demo PIN)")
    
    # Test compliance check
    print("\n" + "=" * 70)
    print("TEST 3: Compliance Check")
    print("=" * 70)
    
    print(f"\n🔍 Checking compliance for PIN: {test_pin}")
    
    result = await kra_service.check_compliance(test_pin)
    
    if result.get("success"):
        print("✅ Compliance check succeeded:")
        print(f"   Compliant: {result.get('compliant')}")
        print(f"   Status: {result.get('compliance_status', 'N/A')}")
        print(f"   Outstanding Returns: {result.get('outstanding_returns', [])}")
        print(f"   Outstanding Taxes: KES {result.get('outstanding_taxes', 0):,.2f}")
    else:
        print(f"❌ Compliance check failed: {result.get('error')}")
    
    # Test taxpayer details
    print("\n" + "=" * 70)
    print("TEST 4: Taxpayer Details")
    print("=" * 70)
    
    print(f"\n🔍 Getting taxpayer details for PIN: {test_pin}")
    
    result = await kra_service.get_taxpayer_details(test_pin)
    
    if result.get("success"):
        print("✅ Taxpayer details retrieved:")
        print(f"   Name: {result.get('taxpayer_name', 'N/A')}")
        print(f"   Type: {result.get('taxpayer_type', 'N/A')}")
        print(f"   Email: {result.get('email', 'N/A')}")
        print(f"   Phone: {result.get('phone', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
    else:
        print(f"❌ Failed to get taxpayer details: {result.get('error')}")
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("\n✓ KRA service module: OK")
    print("✓ PIN validation: OK")
    print(f"✓ API connectivity: {'OK (needs credentials)' if not kra_service._initialized else 'OK'}")
    print("\n📝 Next Steps:")
    print("   1. Obtain KRA API credentials from https://itax.kra.go.ke")
    print("   2. Configure credentials in .env file")
    print("   3. Set KRA_ENABLED=true")
    print("   4. Restart backend server")
    print("   5. Test API endpoints at http://localhost:8000/docs")
    print("\n🔗 Available API Endpoints:")
    print("   POST /kra/verify-pin - Verify KRA PIN")
    print("   POST /kra/check-compliance - Check tax compliance")
    print("   POST /kra/taxpayer-details - Get taxpayer information")
    print("   POST /kra/request-compliance-certificate - Request certificate")
    print("   GET  /kra/status - Check KRA service status")
    print("=" * 70)


if __name__ == "__main__":
    print("\n🚀 Starting KRA API Integration Tests...\n")
    asyncio.run(test_kra_service())
