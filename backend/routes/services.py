"""
Services information API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException

from models.schemas import ServiceType, ServiceInfoResponse, ServicesListResponse
from services.booking_service import booking_service
from config import GOVERNMENT_SERVICES
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/services", tags=["Services"])


@router.get(
    "/",
    response_model=ServicesListResponse,
    summary="List all services",
    description="Get list of all available government services"
)
async def list_services():
    """
    Get all available government services.
    
    Returns a list of services with their details, requirements, and available time slots.
    """
    services = []
    
    for service_key, service_data in GOVERNMENT_SERVICES.items():
        services.append(
            ServiceInfoResponse(
                service_type=ServiceType(service_key),
                name=service_data["name"],
                description=service_data["description"],
                department=service_data["department"],
                time_slots=service_data["time_slots"],
                requirements=service_data["requirements"],
                ecitizen_url=service_data["ecitizen_url"]
            )
        )
    
    return ServicesListResponse(
        services=services,
        total_count=len(services)
    )


@router.get(
    "/{service_type}",
    response_model=ServiceInfoResponse,
    summary="Get service details",
    description="Get detailed information about a specific government service"
)
async def get_service(service_type: ServiceType):
    """
    Get details of a specific service.
    
    - **service_type**: Type of government service (passport, national_id, driving_license, good_conduct)
    
    Returns service details including requirements, available time slots, and eCitizen URL.
    """
    service_data = GOVERNMENT_SERVICES.get(service_type.value)
    
    if not service_data:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service_type.value}' not found"
        )
    
    return ServiceInfoResponse(
        service_type=service_type,
        name=service_data["name"],
        description=service_data["description"],
        department=service_data["department"],
        time_slots=service_data["time_slots"],
        requirements=service_data["requirements"],
        ecitizen_url=service_data["ecitizen_url"]
    )


@router.get(
    "/{service_type}/requirements",
    summary="Get service requirements",
    description="Get the list of required documents for a service"
)
async def get_requirements(service_type: ServiceType):
    """
    Get requirements for a specific service.
    
    - **service_type**: Type of government service
    
    Returns a list of required documents and any additional requirements.
    """
    service_data = GOVERNMENT_SERVICES.get(service_type.value)
    
    if not service_data:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service_type.value}' not found"
        )
    
    # Generate accessibility-friendly requirements text
    requirements_list = service_data["requirements"]
    requirements_text = f"To apply for {service_data['name']}, you will need the following documents: "
    requirements_text += ", ".join(requirements_list[:-1])
    if len(requirements_list) > 1:
        requirements_text += f", and {requirements_list[-1]}."
    else:
        requirements_text += f"{requirements_list[0]}."
    
    return {
        "service_type": service_type.value,
        "service_name": service_data["name"],
        "requirements": requirements_list,
        "requirements_text": requirements_text,
        "department": service_data["department"]
    }


@router.get(
    "/{service_type}/ecitizen-info",
    summary="Get eCitizen portal information",
    description="Get eCitizen portal navigation information for a service"
)
async def get_ecitizen_info(service_type: ServiceType):
    """
    Get eCitizen portal information for a service.
    
    - **service_type**: Type of government service
    
    Returns the eCitizen URL and navigation instructions.
    """
    from config import get_settings
    
    settings = get_settings()
    service_data = GOVERNMENT_SERVICES.get(service_type.value)
    
    if not service_data:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service_type.value}' not found"
        )
    
    full_url = f"{settings.ECITIZEN_BASE_URL}{service_data['ecitizen_url']}"
    
    # Generate accessibility-friendly navigation instructions
    instructions = [
        f"To access {service_data['name']} on eCitizen:",
        "1. Go to the eCitizen website at ecitizen.go.ke",
        "2. Log in with your eCitizen account or create a new account if you don't have one",
        f"3. Navigate to {service_data['department']} services",
        f"4. Select '{service_data['name']}' from the available options",
        "5. Follow the on-screen instructions to complete your application"
    ]
    
    return {
        "service_type": service_type.value,
        "service_name": service_data["name"],
        "department": service_data["department"],
        "ecitizen_base_url": settings.ECITIZEN_BASE_URL,
        "ecitizen_service_url": full_url,
        "navigation_instructions": instructions,
        "instructions_text": " ".join(instructions)
    }
