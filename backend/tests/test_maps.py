"""
Tests for the Maps Service

Tests cover:
- Finding nearest Huduma Centres
- Distance calculations
- Directions retrieval
- Government office search
"""

import pytest
import asyncio
from typing import List, Dict

# Import from services
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.maps_service import (
    MapsService,
    LocationResult,
    DirectionsResult,
    HUDUMA_CENTRES
)


@pytest.fixture
def maps_service():
    """Create a maps service instance."""
    return MapsService()


class TestHudumaCentreData:
    """Tests for Huduma Centre static data."""
    
    def test_centres_are_loaded(self, maps_service):
        """Test that Huduma Centres are loaded."""
        centres = HUDUMA_CENTRES
        
        assert len(centres) > 0
        assert any(c["name"] == "Huduma Centre GPO" for c in centres)
    
    def test_centre_has_required_fields(self, maps_service):
        """Test that each centre has required fields."""
        for centre in HUDUMA_CENTRES:
            assert "id" in centre
            assert "name" in centre
            assert "county" in centre
            assert "coordinates" in centre
            assert "lat" in centre["coordinates"]
            assert "lng" in centre["coordinates"]
    
    def test_centre_has_services(self, maps_service):
        """Test that centres have services listed."""
        for centre in HUDUMA_CENTRES:
            assert "services" in centre
            assert len(centre["services"]) > 0
            assert all(isinstance(s, str) for s in centre["services"])


class TestDistanceCalculation:
    """Tests for distance calculations."""
    
    def test_haversine_same_point(self, maps_service):
        """Test distance between same point is zero."""
        distance = maps_service._haversine_distance(-1.2921, 36.8219, -1.2921, 36.8219)
        
        assert distance == 0.0
    
    def test_haversine_known_distance(self, maps_service):
        """Test distance calculation for known points."""
        # Nairobi CBD to Mombasa (approx 440 km)
        distance = maps_service._haversine_distance(
            -1.2921, 36.8219,  # Nairobi
            -4.0435, 39.6682   # Mombasa
        )
        
        # Should be approximately 440 km (allow ±20 km tolerance)
        assert 420 < distance < 460
    
    def test_haversine_short_distance(self, maps_service):
        """Test distance calculation for nearby points."""
        # Two points in Nairobi CBD (should be < 5 km)
        distance = maps_service._haversine_distance(
            -1.2921, 36.8219,
            -1.3000, 36.8300
        )
        
        assert distance < 5.0


class TestFindNearestCentres:
    """Tests for finding nearest Huduma Centres."""
    
    @pytest.mark.asyncio
    async def test_find_nearest_from_cbd(self, maps_service):
        """Test finding centres near Nairobi CBD."""
        result = await maps_service.find_nearest_huduma_centres(
            location="Nairobi CBD",
            limit=3
        )
        
        assert result["success"] is True
        assert len(result["centres"]) <= 3
        
        # Results should be sorted by distance
        distances = [c["distance_km"] for c in result["centres"]]
        assert distances == sorted(distances)
    
    @pytest.mark.asyncio
    async def test_find_nearest_includes_distance(self, maps_service):
        """Test that results include distance information."""
        result = await maps_service.find_nearest_huduma_centres(
            location="Westlands",
            limit=1
        )
        
        centre = result["centres"][0]
        assert "distance_km" in centre
        assert "duration_minutes" in centre
        assert isinstance(centre["distance_km"], float)
    
    @pytest.mark.asyncio
    async def test_find_nearest_limits_results(self, maps_service):
        """Test that limit is respected."""
        result = await maps_service.find_nearest_huduma_centres(
            location="Nairobi",
            limit=2
        )
        
        assert len(result["centres"]) == 2
    
    @pytest.mark.asyncio
    async def test_find_nearest_filter_by_service(self, maps_service):
        """Test filtering centres by available service."""
        result = await maps_service.find_nearest_huduma_centres(
            location="Nairobi",
            limit=5,
            service_filter="Passport"
        )
        
        for centre in result["centres"]:
            assert "Passport" in centre["services"]


class TestDirections:
    """Tests for directions retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_directions(self, maps_service):
        """Test getting directions between locations."""
        result = await maps_service.get_directions(
            origin="Westlands",
            destination="CBD"
        )
        
        assert result["success"] is True
        assert "distance_km" in result
        assert "duration_minutes" in result
    
    @pytest.mark.asyncio
    async def test_get_directions_different_modes(self, maps_service):
        """Test directions with different travel modes."""
        modes = ["driving", "walking", "transit"]
        
        for mode in modes:
            result = await maps_service.get_directions(
                origin="Karen",
                destination="CBD",
                mode=mode
            )
            
            assert result["success"] is True


class TestGovernmentOfficeSearch:
    """Tests for government office search."""
    
    @pytest.mark.asyncio
    async def test_search_by_location(self, maps_service):
        """Test searching offices by location."""
        result = await maps_service.find_nearest_huduma_centres(
            location="Mombasa",
            limit=3
        )
        
        assert result["success"] is True
        assert len(result["centres"]) > 0
    
    @pytest.mark.asyncio
    async def test_search_by_service(self, maps_service):
        """Test searching offices by service offered."""
        result = await maps_service.find_nearest_huduma_centres(
            location="Nairobi",
            service_filter="Passport"
        )
        
        assert result["success"] is True
        for centre in result["centres"]:
            assert "Passport" in centre["services"]


class TestGeocoding:
    """Tests for location geocoding."""
    
    def test_geocode_known_location(self, maps_service):
        """Test geocoding known location."""
        coords = maps_service._geocode_location("Nairobi")
        
        assert coords is not None
        lat, lng = coords
        assert -1.5 < lat < -1.1
        assert 36.5 < lng < 37.0
    
    def test_geocode_county(self, maps_service):
        """Test geocoding county name."""
        coords = maps_service._geocode_location("Mombasa")
        
        assert coords is not None
        lat, lng = coords
        assert -4.5 < lat < -3.5
        assert 39 < lng < 40


class TestFormattedOutput:
    """Tests for formatted output strings."""
    
    @pytest.mark.asyncio
    async def test_spoken_response_included(self, maps_service):
        """Test that spoken response is included in results."""
        result = await maps_service.find_nearest_huduma_centres(
            location="Nairobi",
            limit=3
        )
        
        assert "spoken_response" in result
        assert "Huduma Centre" in result["spoken_response"]


class TestServiceAvailability:
    """Tests for service availability checks."""
    
    def test_centre_has_passport_service(self):
        """Test that some centres have passport service."""
        passport_centres = [c for c in HUDUMA_CENTRES if "Passport" in c["services"]]
        assert len(passport_centres) >= 1
    
    def test_centre_has_national_id_service(self):
        """Test that all centres have National ID service."""
        id_centres = [c for c in HUDUMA_CENTRES if "National ID" in c["services"]]
        assert len(id_centres) == len(HUDUMA_CENTRES)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
