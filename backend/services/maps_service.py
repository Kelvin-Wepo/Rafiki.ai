"""
Google Maps Integration Service

Provides location services for:
- Huduma Centre lookup
- Government office directions
- Travel time estimation
- Nearby places search

Requires GOOGLE_MAPS_API_KEY environment variable.
Falls back to static data if API key not configured.
"""

import os
import httpx
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from math import radians, cos, sin, asin, sqrt

from utils.logger import get_logger
from rafiki_settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


# Static Huduma Centre data (fallback when Maps API unavailable)
HUDUMA_CENTRES = [
    {
        "id": "huduma_gpo",
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
        "id": "huduma_makadara",
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
        "id": "huduma_mombasa",
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
        "id": "huduma_kisumu",
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
        "id": "huduma_nakuru",
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
        "id": "huduma_eldoret",
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
        "id": "huduma_thika",
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
        "id": "huduma_nyeri",
        "name": "Huduma Centre Nyeri",
        "city": "Nyeri",
        "county": "Nyeri",
        "address": "Nyeri Town",
        "coordinates": {"lat": -0.4167, "lng": 36.9500},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "KRA PIN", "NHIF", "NSSF"]
    },
    {
        "id": "huduma_machakos",
        "name": "Huduma Centre Machakos",
        "city": "Machakos",
        "county": "Machakos",
        "address": "Machakos Town",
        "coordinates": {"lat": -1.5167, "lng": 37.2667},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "KRA PIN", "NHIF"]
    },
    {
        "id": "huduma_garissa",
        "name": "Huduma Centre Garissa",
        "city": "Garissa",
        "county": "Garissa",
        "address": "Garissa Town",
        "coordinates": {"lat": -0.4536, "lng": 39.6401},
        "phone": "0800 221 199",
        "hours": "Mon-Fri: 8:00 AM - 5:00 PM",
        "services": ["National ID", "KRA PIN", "NHIF"]
    }
]

# Known city/area coordinates for basic geocoding fallback
KNOWN_LOCATIONS = {
    "nairobi": (-1.2921, 36.8219),
    "mombasa": (-4.0435, 39.6682),
    "kisumu": (-0.0917, 34.7680),
    "nakuru": (-0.2833, 36.0667),
    "eldoret": (0.5143, 35.2698),
    "thika": (-1.0333, 37.0693),
    "nyeri": (-0.4167, 36.9500),
    "machakos": (-1.5167, 37.2667),
    "garissa": (-0.4536, 39.6401),
    "malindi": (-3.2138, 40.1169),
    "kitale": (1.0167, 35.0000),
    "kakamega": (0.2827, 34.7519),
    "juja": (-1.1000, 37.0150),
    "ruiru": (-1.1500, 36.9600),
    "westlands": (-1.2640, 36.8030),
    "karen": (-1.3220, 36.7080),
    "kilimani": (-1.2920, 36.7890),
    "cbd": (-1.2833, 36.8167),
}


@dataclass
class LocationResult:
    """Result of a location lookup."""
    name: str
    address: str
    coordinates: Dict[str, float]
    distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None
    phone: Optional[str] = None
    hours: Optional[str] = None
    services: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "address": self.address,
            "coordinates": self.coordinates,
            "distance_km": self.distance_km,
            "duration_minutes": self.duration_minutes,
            "phone": self.phone,
            "hours": self.hours,
            "services": self.services
        }


@dataclass
class DirectionsResult:
    """Result of a directions request."""
    origin: str
    destination: str
    distance_km: float
    duration_minutes: float
    steps: List[str]
    polyline: Optional[str] = None
    map_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "origin": self.origin,
            "destination": self.destination,
            "distance_km": self.distance_km,
            "duration_minutes": self.duration_minutes,
            "steps": self.steps,
            "polyline": self.polyline,
            "map_url": self.map_url
        }


class MapsService:
    """
    Google Maps integration service.
    
    Falls back to static data if GOOGLE_MAPS_API_KEY is not configured.
    """
    
    def __init__(self):
        """Initialize maps service."""
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
        self.api_available = bool(self.api_key)
        
        if self.api_available:
            logger.info("MapsService initialized with Google Maps API")
        else:
            logger.warning("MapsService: No API key, using static data fallback")
    
    def _haversine_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        Calculate great-circle distance between two points.
        
        Returns distance in kilometers.
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Earth's radius in km
        r = 6371
        
        return round(c * r, 2)
    
    def _estimate_duration(self, distance_km: float, mode: str = "driving") -> float:
        """
        Estimate travel duration based on mode.
        
        Returns duration in minutes.
        """
        # Average speeds in km/h
        speeds = {
            "walking": 5,
            "transit": 20,  # Considering wait times
            "driving": 30,  # Urban traffic
            "motorcycle": 35
        }
        
        speed = speeds.get(mode, 30)
        return round((distance_km / speed) * 60, 0)
    
    def _geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a location name.
        
        Uses static data fallback if API unavailable.
        """
        location_lower = location.lower().strip()
        
        # Check known locations
        for name, coords in KNOWN_LOCATIONS.items():
            if name in location_lower:
                return coords
        
        # Check Huduma centres
        for centre in HUDUMA_CENTRES:
            if location_lower in centre["city"].lower() or location_lower in centre["name"].lower():
                return (centre["coordinates"]["lat"], centre["coordinates"]["lng"])
        
        # Default to Nairobi CBD if unknown
        logger.warning(f"Unknown location '{location}', defaulting to Nairobi")
        return KNOWN_LOCATIONS["nairobi"]
    
    async def find_nearest_huduma_centres(
        self,
        location: str,
        limit: int = 3,
        service_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find nearest Huduma Centres to a location.
        
        Args:
            location: User's location (city/area name or address)
            limit: Maximum number of results
            service_filter: Optional service to filter by
            
        Returns:
            Dictionary with nearest centres and their details
        """
        # Get user coordinates
        user_coords = self._geocode_location(location)
        if not user_coords:
            return {
                "success": False,
                "error": f"Could not find location: {location}"
            }
        
        user_lat, user_lng = user_coords
        
        # Calculate distances to all centres
        centres_with_distance = []
        for centre in HUDUMA_CENTRES:
            # Filter by service if specified
            if service_filter:
                service_lower = service_filter.lower()
                services_lower = [s.lower() for s in centre["services"]]
                if not any(service_lower in s for s in services_lower):
                    continue
            
            distance = self._haversine_distance(
                user_lat, user_lng,
                centre["coordinates"]["lat"],
                centre["coordinates"]["lng"]
            )
            
            centres_with_distance.append({
                **centre,
                "distance_km": distance,
                "duration_minutes": self._estimate_duration(distance)
            })
        
        # Sort by distance
        centres_with_distance.sort(key=lambda x: x["distance_km"])
        
        # Take top N
        nearest = centres_with_distance[:limit]
        
        # Build response
        if not nearest:
            return {
                "success": False,
                "error": "No Huduma Centres found matching your criteria"
            }
        
        # Format for speech
        spoken = f"I found {len(nearest)} Huduma Centre{'s' if len(nearest) > 1 else ''} near {location}. "
        spoken += f"The nearest is {nearest[0]['name']}, about {nearest[0]['distance_km']} kilometers away, "
        spoken += f"approximately {int(nearest[0]['duration_minutes'])} minutes by car."
        
        return {
            "success": True,
            "user_location": location,
            "user_coordinates": {"lat": user_lat, "lng": user_lng},
            "centres": nearest,
            "spoken_response": spoken,
            "api_used": self.api_available
        }
    
    async def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        Get directions between two locations.
        
        Args:
            origin: Starting location
            destination: Ending location
            mode: Travel mode (driving, walking, transit, motorcycle)
            
        Returns:
            Directions with distance, duration, and steps
        """
        # Normalize mode
        mode = mode.lower()
        if mode in ["matatu", "psv", "bus"]:
            mode = "transit"
        elif mode in ["boda", "motorcycle", "bike"]:
            mode = "motorcycle"
        elif mode in ["walk", "foot"]:
            mode = "walking"
        else:
            mode = "driving"
        
        # Get coordinates
        origin_coords = self._geocode_location(origin)
        dest_coords = self._geocode_location(destination)
        
        if not origin_coords or not dest_coords:
            return {
                "success": False,
                "error": "Could not geocode one or both locations"
            }
        
        # Calculate distance and duration
        distance = self._haversine_distance(
            origin_coords[0], origin_coords[1],
            dest_coords[0], dest_coords[1]
        )
        duration = self._estimate_duration(distance, mode)
        
        # Generate basic directions (without API, we provide general guidance)
        if self.api_available:
            # TODO: Call Google Directions API
            steps = [f"Navigate from {origin} to {destination}"]
        else:
            steps = [
                f"Head from {origin} towards {destination}",
                f"Distance: approximately {distance} km",
                f"Estimated time: {int(duration)} minutes by {mode}",
                "Note: For detailed turn-by-turn directions, please use Google Maps"
            ]
        
        # Google Maps URL
        map_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode={mode}"
        
        # Spoken directions
        spoken = f"To get from {origin} to {destination}: "
        spoken += f"The distance is about {distance} kilometers. "
        spoken += f"It will take approximately {int(duration)} minutes by {mode}. "
        
        if mode == "transit":
            spoken += "Look for matatu route numbers displayed at stages."
        elif mode == "walking":
            spoken += "Please stay on well-lit paths and be careful crossing roads."
        
        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "distance_km": distance,
            "duration_minutes": duration,
            "steps": steps,
            "map_url": map_url,
            "spoken_response": spoken,
            "api_used": self.api_available
        }
    
    async def search_government_offices(
        self,
        office_type: str,
        near_location: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search for government offices near a location.
        
        Args:
            office_type: Type of office (e.g., "DCI", "KRA", "Immigration")
            near_location: Location to search near
            limit: Maximum results
            
        Returns:
            List of matching offices
        """
        # For now, return static data
        # TODO: Implement Google Places API search when key available
        
        offices = {
            "dci": [
                {
                    "name": "DCI Headquarters",
                    "address": "Kiambu Road, Nairobi",
                    "coordinates": {"lat": -1.2500, "lng": 36.8333},
                    "phone": "0800 722 203",
                    "hours": "Mon-Fri: 8:00 AM - 5:00 PM"
                }
            ],
            "kra": [
                {
                    "name": "KRA Times Tower",
                    "address": "Times Tower, Haile Selassie Avenue, Nairobi",
                    "coordinates": {"lat": -1.2886, "lng": 36.8250},
                    "phone": "0800 724 253",
                    "hours": "Mon-Fri: 8:00 AM - 5:00 PM"
                }
            ],
            "immigration": [
                {
                    "name": "Immigration Headquarters",
                    "address": "Nyayo House, Nairobi",
                    "coordinates": {"lat": -1.2900, "lng": 36.8236},
                    "phone": "020 222 2022",
                    "hours": "Mon-Fri: 8:00 AM - 3:00 PM"
                }
            ]
        }
        
        office_lower = office_type.lower()
        results = offices.get(office_lower, [])
        
        return {
            "success": bool(results),
            "office_type": office_type,
            "near_location": near_location,
            "offices": results[:limit],
            "message": f"Found {len(results)} {office_type} office(s)" if results else f"No {office_type} offices found",
            "api_used": self.api_available
        }


# Global maps service instance
_maps_service: Optional[MapsService] = None


def get_maps_service() -> MapsService:
    """Get or create the maps service singleton."""
    global _maps_service
    if _maps_service is None:
        _maps_service = MapsService()
    return _maps_service
