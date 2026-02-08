"""
Location Services Routes

Handles Huduma Centre lookup, government office directions, and traffic information.
Integrates with Google Maps API for directions.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import httpx
import os

from backend.utils.logger import get_logger
from backend.config import get_settings

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter(prefix="/location", tags=["Location Services"])


# ============== Huduma Centre Data ==============

HUDUMA_CENTRES = [
    {
        "name": "Huduma Centre GPO",
        "city": "Nairobi",
        "county": "Nairobi",
        "address": "GPO Building, Kenyatta Avenue, Nairobi",
        "coordinates": {"lat": -1.2833, "lng": 36.8167},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "Passport", "KRA PIN", "NHIF", "NSSF", "Business Registration"]
    },
    {
        "name": "Huduma Centre Makadara",
        "city": "Nairobi",
        "county": "Nairobi",
        "address": "Jogoo Road, Makadara, Nairobi",
        "coordinates": {"lat": -1.2972, "lng": 36.8550},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "KRA PIN", "NHIF", "NSSF"]
    },
    {
        "name": "Huduma Centre Mombasa",
        "city": "Mombasa",
        "county": "Mombasa",
        "address": "Treasury Square, Mombasa",
        "coordinates": {"lat": -4.0435, "lng": 39.6682},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "Passport", "KRA PIN", "NHIF", "NSSF", "Business Registration"]
    },
    {
        "name": "Huduma Centre Kisumu",
        "city": "Kisumu",
        "county": "Kisumu",
        "address": "Mega Plaza, Kisumu",
        "coordinates": {"lat": -0.0917, "lng": 34.7680},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "KRA PIN", "NHIF", "NSSF", "Business Registration"]
    },
    {
        "name": "Huduma Centre Nakuru",
        "city": "Nakuru",
        "county": "Nakuru",
        "address": "Provincial Headquarters, Nakuru",
        "coordinates": {"lat": -0.2833, "lng": 36.0667},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "KRA PIN", "NHIF", "NSSF"]
    },
    {
        "name": "Huduma Centre Eldoret",
        "city": "Eldoret",
        "county": "Uasin Gishu",
        "address": "KVDA Plaza, Eldoret",
        "coordinates": {"lat": 0.5143, "lng": 35.2698},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "KRA PIN", "NHIF", "NSSF"]
    },
    {
        "name": "Huduma Centre Thika",
        "city": "Thika",
        "county": "Kiambu",
        "address": "Thika Town, Kiambu",
        "coordinates": {"lat": -1.0333, "lng": 37.0693},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "KRA PIN", "NHIF"]
    },
    {
        "name": "Huduma Centre Nyeri",
        "city": "Nyeri",
        "county": "Nyeri",
        "address": "Nyeri Town",
        "coordinates": {"lat": -0.4167, "lng": 36.9500},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "KRA PIN", "NHIF", "NSSF"]
    }
]


# ============== Request/Response Models ==============

class HudumaCentreResponse(BaseModel):
    """Response model for Huduma Centre."""
    name: str
    city: str
    county: str
    address: str
    coordinates: Dict[str, float]
    phone: str
    hours: str
    services: List[str]
    distance_km: Optional[float] = None
    spoken_description: Optional[str] = None


class NearestCentresResponse(BaseModel):
    """Response for nearest Huduma Centres."""
    success: bool
    centres: List[HudumaCentreResponse]
    message: str
    spoken_response: str


class DirectionsRequest(BaseModel):
    """Request model for directions."""
    origin: str = Field(..., description="Starting location (address or coordinates)")
    destination: str = Field(..., description="Destination (address or coordinates)")
    transport_mode: str = Field("driving", description="Mode: driving, walking, transit")


class DirectionsResponse(BaseModel):
    """Response model for directions."""
    success: bool
    origin: str
    destination: str
    distance: str
    duration: str
    steps: List[str]
    alternative_routes: Optional[List[Dict[str, Any]]] = None
    spoken_directions: str
    map_url: Optional[str] = None


class TrafficRequest(BaseModel):
    """Request model for traffic info."""
    origin: str = Field(..., description="Starting location")
    destination: str = Field(..., description="Destination")


class TrafficResponse(BaseModel):
    """Response model for traffic info."""
    success: bool
    current_conditions: str
    estimated_duration: str
    estimated_duration_in_traffic: str
    delay_minutes: int
    alternative_routes: List[Dict[str, str]]
    spoken_summary: str


# ============== Helper Functions ==============

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in kilometers.
    """
    import math
    
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return round(R * c, 2)


async def get_google_directions(
    origin: str,
    destination: str,
    mode: str = "driving",
    alternatives: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Get directions from Google Maps API.
    Returns None if API key not configured or request fails.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    if not api_key:
        logger.warning("Google Maps API key not configured")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "alternatives": "true" if alternatives else "false",
                    "departure_time": "now",  # For traffic info
                    "key": api_key
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Google Maps API error: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error calling Google Maps API: {e}")
        return None


# ============== Endpoints ==============

@router.get(
    "/huduma-centres",
    response_model=NearestCentresResponse,
    summary="Find Huduma Centres",
    description="Find Huduma Centres, optionally sorted by distance from a location"
)
async def find_huduma_centres(
    lat: Optional[float] = Query(None, description="User latitude"),
    lng: Optional[float] = Query(None, description="User longitude"),
    city: Optional[str] = Query(None, description="Filter by city"),
    county: Optional[str] = Query(None, description="Filter by county"),
    service: Optional[str] = Query(None, description="Filter by service offered"),
    limit: int = Query(5, ge=1, le=20, description="Maximum results")
):
    """
    Find Huduma Centres.
    
    - Provide lat/lng to get centres sorted by distance
    - Filter by city, county, or service offered
    - Returns accessibility-friendly spoken descriptions
    """
    try:
        centres = HUDUMA_CENTRES.copy()
        
        # Apply filters
        if city:
            centres = [c for c in centres if city.lower() in c["city"].lower()]
        
        if county:
            centres = [c for c in centres if county.lower() in c["county"].lower()]
        
        if service:
            centres = [c for c in centres if any(service.lower() in s.lower() for s in c["services"])]
        
        # Calculate distances if coordinates provided
        if lat is not None and lng is not None:
            for centre in centres:
                centre["distance_km"] = calculate_distance(
                    lat, lng,
                    centre["coordinates"]["lat"],
                    centre["coordinates"]["lng"]
                )
            # Sort by distance
            centres.sort(key=lambda x: x.get("distance_km", float("inf")))
        
        # Limit results
        centres = centres[:limit]
        
        # Add spoken descriptions
        results = []
        for centre in centres:
            spoken = f"{centre['name']} is located at {centre['address']}. "
            if centre.get("distance_km"):
                spoken += f"It is approximately {centre['distance_km']} kilometers away. "
            spoken += f"Operating hours are {centre['hours']}. Phone number is {centre['phone']}."
            
            results.append(HudumaCentreResponse(
                **centre,
                spoken_description=spoken
            ))
        
        # Build spoken response
        if results:
            if lat and lng:
                spoken_response = f"I found {len(results)} Huduma Centres near you. "
                spoken_response += f"The nearest is {results[0].name}, {results[0].distance_km} kilometers away."
            else:
                spoken_response = f"I found {len(results)} Huduma Centres. "
                spoken_response += f"The first is {results[0].name} in {results[0].city}."
        else:
            spoken_response = "I could not find any Huduma Centres matching your criteria."
        
        return NearestCentresResponse(
            success=True,
            centres=results,
            message=f"Found {len(results)} Huduma Centres",
            spoken_response=spoken_response
        )
        
    except Exception as e:
        logger.error(f"Error finding Huduma Centres: {e}")
        raise HTTPException(status_code=500, detail="Failed to find Huduma Centres")


@router.post(
    "/directions",
    response_model=DirectionsResponse,
    summary="Get directions",
    description="Get directions to a government office or location"
)
async def get_directions(request: DirectionsRequest):
    """
    Get directions to a destination.
    
    - Supports driving, walking, and transit modes
    - Returns step-by-step directions
    - Provides spoken directions for accessibility
    - Falls back to structured response if Google Maps unavailable
    """
    try:
        # Try Google Maps API
        api_result = await get_google_directions(
            request.origin,
            request.destination,
            request.transport_mode
        )
        
        if api_result and api_result.get("status") == "OK":
            route = api_result["routes"][0]
            leg = route["legs"][0]
            
            # Extract steps
            steps = []
            for i, step in enumerate(leg["steps"], 1):
                # Clean HTML from instructions
                instruction = step["html_instructions"]
                import re
                instruction = re.sub(r'<[^>]+>', '', instruction)
                steps.append(f"Step {i}: {instruction} ({step['distance']['text']})")
            
            # Build spoken directions
            spoken = (
                f"To get from {leg['start_address']} to {leg['end_address']}, "
                f"the total distance is {leg['distance']['text']} and "
                f"it will take approximately {leg['duration']['text']}. "
            )
            spoken += f"Here are the directions: {'. '.join(steps[:5])}"  # First 5 steps
            if len(steps) > 5:
                spoken += f" ...and {len(steps) - 5} more steps."
            
            # Alternative routes
            alternatives = []
            for alt_route in api_result["routes"][1:3]:  # Up to 2 alternatives
                alt_leg = alt_route["legs"][0]
                alternatives.append({
                    "distance": alt_leg["distance"]["text"],
                    "duration": alt_leg["duration"]["text"],
                    "summary": alt_route.get("summary", "Alternative route")
                })
            
            # Generate Google Maps URL
            map_url = f"https://www.google.com/maps/dir/{request.origin}/{request.destination}"
            
            return DirectionsResponse(
                success=True,
                origin=leg["start_address"],
                destination=leg["end_address"],
                distance=leg["distance"]["text"],
                duration=leg["duration"]["text"],
                steps=steps,
                alternative_routes=alternatives if alternatives else None,
                spoken_directions=spoken,
                map_url=map_url
            )
        
        # Fallback when Google Maps not available
        logger.warning("Google Maps API not available, returning fallback response")
        
        return DirectionsResponse(
            success=True,
            origin=request.origin,
            destination=request.destination,
            distance="Distance unavailable",
            duration="Duration unavailable",
            steps=[
                f"Step 1: Navigate from {request.origin} to {request.destination}",
                "Step 2: Use Google Maps or ask for local directions",
                "Step 3: The Huduma Kenya helpline is 0800 221 199"
            ],
            alternative_routes=None,
            spoken_directions=(
                f"I can help you get to {request.destination}. "
                f"For precise directions, please use Google Maps or call Huduma Kenya at 0800 221 199 for assistance."
            ),
            map_url=f"https://www.google.com/maps/dir/{request.origin}/{request.destination}"
        )
        
    except Exception as e:
        logger.error(f"Error getting directions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get directions")


@router.post(
    "/traffic",
    response_model=TrafficResponse,
    summary="Get traffic information",
    description="Get current traffic conditions and alternatives"
)
async def get_traffic_info(request: TrafficRequest):
    """
    Get traffic information for a route.
    
    - Returns current traffic conditions
    - Estimates delay time
    - Suggests alternative routes
    - Provides spoken summary for accessibility
    """
    try:
        # Try Google Maps API with traffic
        api_result = await get_google_directions(
            request.origin,
            request.destination,
            "driving",
            alternatives=True
        )
        
        if api_result and api_result.get("status") == "OK":
            route = api_result["routes"][0]
            leg = route["legs"][0]
            
            base_duration = leg["duration"]["value"]  # seconds
            traffic_duration = leg.get("duration_in_traffic", {}).get("value", base_duration)
            delay_seconds = max(0, traffic_duration - base_duration)
            delay_minutes = delay_seconds // 60
            
            # Determine conditions
            if delay_minutes <= 5:
                conditions = "Traffic is flowing smoothly"
            elif delay_minutes <= 15:
                conditions = "There is moderate traffic"
            elif delay_minutes <= 30:
                conditions = "There is heavy traffic"
            else:
                conditions = "There is severe traffic congestion"
            
            # Build alternatives
            alternatives = []
            for alt_route in api_result["routes"][1:3]:
                alt_leg = alt_route["legs"][0]
                alt_duration = alt_leg.get("duration_in_traffic", alt_leg["duration"])
                alternatives.append({
                    "route": alt_route.get("summary", "Alternative"),
                    "duration": alt_duration.get("text", alt_leg["duration"]["text"]),
                    "distance": alt_leg["distance"]["text"]
                })
            
            spoken = (
                f"{conditions} on the route from {request.origin} to {request.destination}. "
                f"The estimated travel time is {leg.get('duration_in_traffic', leg['duration'])['text']}. "
            )
            if delay_minutes > 5:
                spoken += f"There is approximately {delay_minutes} minutes of delay due to traffic. "
            if alternatives:
                spoken += f"I found {len(alternatives)} alternative routes that may be faster."
            
            return TrafficResponse(
                success=True,
                current_conditions=conditions,
                estimated_duration=leg["duration"]["text"],
                estimated_duration_in_traffic=leg.get("duration_in_traffic", leg["duration"])["text"],
                delay_minutes=delay_minutes,
                alternative_routes=alternatives,
                spoken_summary=spoken
            )
        
        # Fallback
        return TrafficResponse(
            success=True,
            current_conditions="Traffic information unavailable",
            estimated_duration="Unknown",
            estimated_duration_in_traffic="Unknown",
            delay_minutes=0,
            alternative_routes=[],
            spoken_summary=(
                "I'm unable to get current traffic information. "
                "For real-time traffic updates, please check Google Maps or listen to local radio traffic reports."
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting traffic info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get traffic information")


@router.get(
    "/huduma-centre/{centre_name}",
    response_model=HudumaCentreResponse,
    summary="Get specific Huduma Centre details",
    description="Get detailed information about a specific Huduma Centre"
)
async def get_huduma_centre_details(centre_name: str):
    """
    Get details for a specific Huduma Centre by name.
    """
    for centre in HUDUMA_CENTRES:
        if centre_name.lower() in centre["name"].lower():
            spoken = (
                f"{centre['name']} is located at {centre['address']}. "
                f"It is open {centre['hours']}. "
                f"You can reach them at {centre['phone']}. "
                f"Services available include: {', '.join(centre['services'])}."
            )
            return HudumaCentreResponse(**centre, spoken_description=spoken)
    
    raise HTTPException(status_code=404, detail=f"Huduma Centre '{centre_name}' not found")
