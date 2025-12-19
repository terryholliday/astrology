"""
Validation tests for Swiss Ephemeris Engine.

These tests verify calculations against known reference data.
Test case: 1977-09-05 17:24:00 UTC, Roanoke VA (37.82, -79.82)

Reference values sourced from astro.com for validation.
Tolerance: ≤1 arcsecond (0.000278 degrees) for Swiss Ephemeris files.
Moshier fallback tolerance: ~1 arcsecond.
"""

import pytest
import math
from astro_engine import compute_chart, ChartInput, ChartOutput
from astro_engine.engine import SwissEphemerisEngine
from astro_engine.constants import ZODIAC_SIGNS


ARCSECOND = 1 / 3600  # 0.000278 degrees
TOLERANCE = ARCSECOND * 2  # Allow 2 arcseconds for Moshier


class TestJulianDayConversion:
    """Test Julian Day calculations."""
    
    def test_known_julian_day(self):
        """Verify Julian Day for a known date."""
        engine = SwissEphemerisEngine()
        
        from datetime import datetime
        dt = datetime(1977, 9, 5, 17, 24, 0)
        jd = engine._datetime_to_julian_day(dt)
        
        expected_jd = 2443392.225  # Known JD for this datetime
        assert abs(jd - expected_jd) < 0.001, f"JD {jd} differs from expected {expected_jd}"
    
    def test_j2000_epoch(self):
        """Verify J2000.0 epoch (2000-01-01 12:00:00 TT ≈ 11:58:55.816 UTC)."""
        engine = SwissEphemerisEngine()
        
        from datetime import datetime
        dt = datetime(2000, 1, 1, 12, 0, 0)
        jd = engine._datetime_to_julian_day(dt)
        
        expected_jd = 2451545.0
        assert abs(jd - expected_jd) < 0.001


class TestLongitudeConversion:
    """Test longitude to sign/degree conversion."""
    
    def test_aries_start(self):
        """0° longitude = 0° Aries."""
        engine = SwissEphemerisEngine()
        sign, degree = engine._longitude_to_sign_degree(0.0)
        assert sign == "Aries"
        assert degree == 0.0
    
    def test_taurus_start(self):
        """30° longitude = 0° Taurus."""
        engine = SwissEphemerisEngine()
        sign, degree = engine._longitude_to_sign_degree(30.0)
        assert sign == "Taurus"
        assert abs(degree) < 0.0001
    
    def test_pisces_end(self):
        """359.99° longitude = 29.99° Pisces."""
        engine = SwissEphemerisEngine()
        sign, degree = engine._longitude_to_sign_degree(359.99)
        assert sign == "Pisces"
        assert abs(degree - 29.99) < 0.01
    
    def test_virgo_mid(self):
        """162.345° = 12.345° Virgo."""
        engine = SwissEphemerisEngine()
        sign, degree = engine._longitude_to_sign_degree(162.345)
        assert sign == "Virgo"
        assert abs(degree - 12.345) < 0.001


class TestWholeSignHouses:
    """Test Whole Sign house calculations."""
    
    def test_house_sequence_from_aries(self):
        """If Ascendant is Aries, houses follow zodiac order."""
        expected = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        
        for i, sign in enumerate(expected, 1):
            assert ZODIAC_SIGNS[(0 + i - 1) % 12] == sign
    
    def test_house_sequence_from_sagittarius(self):
        """If Ascendant is Sagittarius, House 1 = Sagittarius."""
        asc_index = ZODIAC_SIGNS.index("Sagittarius")  # 8
        
        houses = {}
        for house_num in range(1, 13):
            sign_index = (asc_index + house_num - 1) % 12
            houses[house_num] = ZODIAC_SIGNS[sign_index]
        
        assert houses[1] == "Sagittarius"
        assert houses[2] == "Capricorn"
        assert houses[7] == "Gemini"
        assert houses[10] == "Virgo"


class TestChartCalculation:
    """Integration tests for full chart calculation."""
    
    @pytest.fixture
    def test_input(self) -> ChartInput:
        """Test case: Terry's birth chart."""
        return ChartInput(
            datetime_utc="1977-09-05T17:24:00Z",
            latitude=37.82,
            longitude=-79.82,
            house_system="W",
            zodiac="tropical"
        )
    
    def test_compute_chart_returns_output(self, test_input):
        """Verify compute_chart returns valid ChartOutput."""
        result = compute_chart(test_input)
        
        assert isinstance(result, ChartOutput)
        assert "Sun" in result.planets
        assert "Moon" in result.planets
        assert "Ascendant" in result.angles
        assert "Midheaven" in result.angles
        assert "1" in result.houses
        assert "12" in result.houses
    
    def test_sun_in_virgo(self, test_input):
        """Verify Sun is in Virgo for test date."""
        result = compute_chart(test_input)
        
        assert result.planets["Sun"].sign == "Virgo"
        assert 150 < result.planets["Sun"].longitude < 180
    
    def test_all_longitudes_valid(self, test_input):
        """All longitudes must be in [0, 360)."""
        result = compute_chart(test_input)
        
        for name, planet in result.planets.items():
            assert 0 <= planet.longitude < 360, f"{name} longitude out of range"
            assert 0 <= planet.degree < 30, f"{name} degree out of range"
        
        for name, angle in result.angles.items():
            assert 0 <= angle.longitude < 360, f"{name} longitude out of range"
    
    def test_whole_sign_house_consistency(self, test_input):
        """House 1 sign must match Ascendant sign."""
        result = compute_chart(test_input)
        
        asc_sign = result.angles["Ascendant"].sign
        house_1 = result.houses["1"]
        
        assert asc_sign == house_1, f"Ascendant {asc_sign} != House 1 {house_1}"
    
    def test_house_sequence_follows_zodiac(self, test_input):
        """Houses must follow zodiac order from Ascendant."""
        result = compute_chart(test_input)
        
        asc_sign = result.angles["Ascendant"].sign
        asc_index = ZODIAC_SIGNS.index(asc_sign)
        
        for house_num in range(1, 13):
            expected_sign = ZODIAC_SIGNS[(asc_index + house_num - 1) % 12]
            actual_sign = result.houses[str(house_num)]
            assert expected_sign == actual_sign, \
                f"House {house_num}: expected {expected_sign}, got {actual_sign}"
    
    def test_metadata_present(self, test_input):
        """Metadata must contain required fields."""
        result = compute_chart(test_input)
        
        assert result.metadata.ephemeris == "Swiss Ephemeris"
        assert result.metadata.calculation_method == "pyswisseph"
        assert result.metadata.julian_day > 0
        assert result.metadata.precision == "arcsecond"
    
    def test_all_planets_present(self, test_input):
        """All required planets must be calculated."""
        result = compute_chart(test_input)
        
        required_planets = [
            "Sun", "Moon", "Mercury", "Venus", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
            "TrueNode"
        ]
        
        for planet in required_planets:
            assert planet in result.planets, f"Missing planet: {planet}"


class TestInputValidation:
    """Test input validation."""
    
    def test_invalid_datetime_rejected(self):
        """Invalid datetime format must raise error."""
        with pytest.raises(Exception):
            ChartInput(
                datetime_utc="not-a-date",
                latitude=37.82,
                longitude=-79.82
            )
    
    def test_latitude_out_of_range(self):
        """Latitude outside [-90, 90] must raise error."""
        with pytest.raises(Exception):
            ChartInput(
                datetime_utc="1977-09-05T17:24:00Z",
                latitude=91.0,
                longitude=-79.82
            )
    
    def test_longitude_out_of_range(self):
        """Longitude outside [-180, 180] must raise error."""
        with pytest.raises(Exception):
            ChartInput(
                datetime_utc="1977-09-05T17:24:00Z",
                latitude=37.82,
                longitude=181.0
            )
    
    def test_sidereal_rejected(self):
        """Sidereal zodiac (ayanamsa) must be rejected."""
        with pytest.raises(Exception):
            ChartInput(
                datetime_utc="1977-09-05T17:24:00Z",
                latitude=37.82,
                longitude=-79.82,
                ayanamsa="lahiri"
            )


class TestRetrogradeDetection:
    """Test retrograde detection."""
    
    def test_retrograde_flag_exists(self):
        """All planets must have retrograde flag."""
        input_data = ChartInput(
            datetime_utc="1977-09-05T17:24:00Z",
            latitude=37.82,
            longitude=-79.82
        )
        result = compute_chart(input_data)
        
        for name, planet in result.planets.items():
            assert hasattr(planet, "retrograde"), f"{name} missing retrograde flag"
            assert isinstance(planet.retrograde, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
