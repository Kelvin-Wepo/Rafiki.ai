"""
KRA (Kenya Revenue Authority) API Routes
Provides endpoints for KRA PIN verification, compliance checks, and taxpayer information.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional

from backend.models.schemas import (
    KRAPINVerifyRequest, KRAPINVerifyResponse,
    KRAComplianceCheckRequest, KRAComplianceCheckResponse,
    KRATaxpayerDetailsRequest, KRATaxpayerDetailsResponse,
    KRAComplianceCertificateRequest, KRAComplianceCertificateResponse
)
from backend.services.kra_service import kra_service
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/kra", tags=["KRA"])


def check_kra_enabled():
    """Dependency to check if KRA service is enabled."""
    if not settings.KRA_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="KRA service is not enabled. Please configure KRA API credentials."
        )
    if not kra_service._initialized:
        raise HTTPException(
            status_code=503,
            detail="KRA service is not initialized properly."
        )


@router.post(
    "/verify-pin",
    response_model=KRAPINVerifyResponse,
    summary="Verify KRA PIN",
    description="Verify if a KRA PIN is valid and retrieve basic taxpayer information"
)
async def verify_pin(request: KRAPINVerifyRequest, _: None = Depends(check_kra_enabled)):
    """
    Verify a KRA PIN and get basic taxpayer information.
    
    This endpoint checks if the provided KRA PIN is registered and valid
    in the KRA system. It returns taxpayer name, type, and status if found.
    
    **KRA PIN Format:** A000000000X (starts with A or P, 9 digits, ends with letter)
    
    Args:
        request: KRA PIN verification request
        
    Returns:
        Verification result with taxpayer information
        
    Raises:
        HTTPException: If KRA service is not available
    """
    try:
        logger.info(f"Verifying KRA PIN: {request.pin[:3]}****{request.pin[-2:]}")
        
        result = await kra_service.verify_pin(request.pin)
        
        return KRAPINVerifyResponse(**result)
        
    except Exception as e:
        logger.error(f"Error verifying KRA PIN: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify KRA PIN: {str(e)}"
        )


@router.post(
    "/check-compliance",
    response_model=KRAComplianceCheckResponse,
    summary="Check Tax Compliance",
    description="Check the tax compliance status for a given KRA PIN"
)
async def check_compliance(request: KRAComplianceCheckRequest, _: None = Depends(check_kra_enabled)):
    """
    Check tax compliance status for a KRA PIN.
    
    This endpoint retrieves the current tax compliance status including:
    - Whether the taxpayer is compliant
    - Outstanding tax returns
    - Outstanding tax amounts
    - Compliance certificate validity
    
    Args:
        request: Compliance check request with KRA PIN
        
    Returns:
        Compliance status and details
        
    Raises:
        HTTPException: If KRA service is not available
    """
    try:
        logger.info(f"Checking compliance for KRA PIN: {request.pin[:3]}****{request.pin[-2:]}")
        
        result = await kra_service.check_compliance(request.pin)
        
        return KRAComplianceCheckResponse(**result)
        
    except Exception as e:
        logger.error(f"Error checking compliance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check compliance: {str(e)}"
        )


@router.post(
    "/taxpayer-details",
    response_model=KRATaxpayerDetailsResponse,
    summary="Get Taxpayer Details",
    description="Retrieve detailed information about a taxpayer"
)
async def get_taxpayer_details(request: KRATaxpayerDetailsRequest, _: None = Depends(check_kra_enabled)):
    """
    Get detailed taxpayer information from KRA.
    
    This endpoint retrieves comprehensive taxpayer details including:
    - Personal/business information
    - Contact details
    - Registration information
    - Business nature
    
    Args:
        request: Request with KRA PIN
        
    Returns:
        Detailed taxpayer information
        
    Raises:
        HTTPException: If KRA service is not available
    """
    try:
        logger.info(f"Getting taxpayer details for: {request.pin[:3]}****{request.pin[-2:]}")
        
        result = await kra_service.get_taxpayer_details(request.pin)
        
        return KRATaxpayerDetailsResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting taxpayer details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get taxpayer details: {str(e)}"
        )


@router.post(
    "/request-compliance-certificate",
    response_model=KRAComplianceCertificateResponse,
    summary="Request Compliance Certificate",
    description="Request a tax compliance certificate from KRA"
)
async def request_compliance_certificate(
    request: KRAComplianceCertificateRequest,
    _: None = Depends(check_kra_enabled)
):
    """
    Request a tax compliance certificate from KRA.
    
    This endpoint submits a request for a tax compliance certificate.
    The certificate will be sent to the provided email address once processed.
    
    Processing typically takes 2-5 business days.
    
    Args:
        request: Certificate request with PIN and email
        
    Returns:
        Request confirmation with request ID
        
    Raises:
        HTTPException: If KRA service is not available
    """
    try:
        logger.info(f"Requesting compliance certificate for: {request.pin[:3]}****{request.pin[-2:]}")
        
        result = await kra_service.request_compliance_certificate(
            pin=request.pin,
            email=request.email
        )
        
        return KRAComplianceCertificateResponse(**result)
        
    except Exception as e:
        logger.error(f"Error requesting compliance certificate: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to request compliance certificate: {str(e)}"
        )


@router.get(
    "/status",
    summary="KRA Service Status",
    description="Check if KRA service is enabled and operational"
)
async def get_service_status():
    """
    Get KRA service status.
    
    Returns information about whether the KRA integration is enabled
    and properly configured.
    
    Returns:
        Service status information
    """
    return JSONResponse(content={
        "enabled": settings.KRA_ENABLED,
        "initialized": kra_service._initialized,
        "api_url": settings.KRA_API_URL if settings.KRA_ENABLED else None,
        "message": "KRA service is operational" if (settings.KRA_ENABLED and kra_service._initialized) 
                   else "KRA service is not enabled or not configured"
    })
