"""
Swiss Ephemeris Engine — Core Calculation Module.

This is the heart of the system. All calculations derive from Swiss Ephemeris.
NO approximations. NO estimations. FAIL LOUD on any error.
"""

import os
import math
from datetime import datetime
from typing import Dict, Tuple, Optional
from pathlib import Path

import swisseph as swe

from .models import (
    ChartInput,
    ChartOutput,
    PlanetPosition,
    AnglePosition,
    ChartMetadata,
)
from .constants import ZODIAC_SIGNS, PLANET_IDS, SUPPORTED_HOUSE_SYSTEM
from .exceptions import (
    EphemerisError,
    EphemerisFileError,
    CalculationError,
    ValidationError,
)


class SwissEphemerisEngine:
    """
    Production-grade Swiss Ephemeris calculation engine.
    
    All calculations are derived from Swiss Ephemeris.
    Fails loud on any error — no silent degradation.
    """

    def __init__(self, ephemeris_path: Optional[str] = None):
        """
        Initialize the engine with ephemeris file path.
        
        Args:
            ephemeris_path: Path to directory containing .se1 files.
                           If None, uses ./ephemeris_data relative to this file.
        """
        if ephemeris_path is None:
            ephemeris_path = str(
                Path(__file__).parent.parent / "ephemeris_data"
            )
        
        self.ephemeris_path = os.path.abspath(ephemeris_path)
        self._ephemeris_mode = "unknown"
        self._initialize_ephemeris()

    def _initialize_ephemeris(self) -> None:
        """Initialize Swiss Ephemeris and verify file availability."""
        swe.set_ephe_path(self.ephemeris_path)
        
        se1_files = list(Path(self.ephemeris_path).glob("*.se1"))
        
        if not se1_files:
            self._ephemeris_mode = "moshier"
            print(
                f"WARNING: No .se1 files found in {self.ephemeris_path}. "
                f"Using Moshier ephemeris (reduced precision ~1 arcsecond). "
                f"For production, download Swiss Ephemeris files."
            )
        else:
            self._ephemeris_mode = "swiss"
            print(f"Swiss Ephemeris initialized with {len(se1_files)} data files.")

    def _parse_datetime(self, datetime_utc: str) -> datetime:
        """Parse ISO 8601 datetime string to datetime object."""
        if datetime_utc.endswith("Z"):
            return datetime.fromisoformat(datetime_utc.replace("Z", "+00:00"))
        return datetime.fromisoformat(datetime_utc)

    def _datetime_to_julian_day(self, dt: datetime) -> float:
        """
        Convert datetime to Julian Day (UT).
        
        Uses Swiss Ephemeris julday function for exact conversion.
        """
        hour_decimal = (
            dt.hour + 
            dt.minute / 60.0 + 
            dt.second / 3600.0 + 
            dt.microsecond / 3600000000.0
        )
        
        jd = swe.julday(
            dt.year,
            dt.month,
            dt.day,
            hour_decimal
        )
        
        return jd

    def _longitude_to_sign_degree(self, longitude: float) -> Tuple[str, float]:
        """
        Convert ecliptic longitude (0-360) to sign and degree within sign.
        
        Args:
            longitude: Ecliptic longitude in degrees (0-360)
            
        Returns:
            Tuple of (sign_name, degree_within_sign)
        """
        if not (0 <= longitude < 360):
            raise CalculationError(f"Invalid longitude: {longitude}. Must be in [0, 360).")
        
        sign_index = int(longitude / 30)
        degree_in_sign = longitude % 30
        
        return ZODIAC_SIGNS[sign_index], degree_in_sign

    def _calculate_planet_position(
        self, 
        jd: float, 
        planet_id: int,
        planet_name: str
    ) -> PlanetPosition:
        """
        Calculate exact position for a single planet.
        
        Args:
            jd: Julian Day (UT)
            planet_id: Swiss Ephemeris planet ID
            planet_name: Name of the planet (for error messages)
            
        Returns:
            PlanetPosition with longitude, sign, degree, retrograde status
        """
        try:
            result, flags = swe.calc_ut(jd, planet_id)
        except Exception as e:
            raise CalculationError(
                f"Failed to calculate position for {planet_name}: {e}"
            ) from e
        
        longitude = result[0]
        speed = result[3]  # Daily motion in longitude
        
        if math.isnan(longitude):
            raise CalculationError(
                f"NaN longitude returned for {planet_name}. "
                f"Check ephemeris files and date range."
            )
        
        longitude = longitude % 360
        if longitude < 0:
            longitude += 360
        
        sign, degree = self._longitude_to_sign_degree(longitude)
        retrograde = speed < 0
        
        return PlanetPosition(
            longitude=round(longitude, 6),
            sign=sign,
            degree=round(degree, 6),
            retrograde=retrograde
        )

    def _calculate_houses_and_angles(
        self,
        jd: float,
        latitude: float,
        longitude: float
    ) -> Tuple[Dict[str, AnglePosition], Dict[str, str]]:
        """
        Calculate house cusps and angles using Whole Sign houses.
        
        For Whole Sign houses:
        - The Ascendant determines the 1st house sign
        - Each subsequent house is the next sign in order
        
        Args:
            jd: Julian Day (UT)
            latitude: Geographic latitude
            longitude: Geographic longitude
            
        Returns:
            Tuple of (angles_dict, houses_dict)
        """
        try:
            cusps, ascmc = swe.houses(jd, latitude, longitude, b"W")
        except Exception as e:
            raise CalculationError(
                f"Failed to calculate houses: {e}"
            ) from e
        
        asc_longitude = ascmc[0]
        mc_longitude = ascmc[1]
        
        if math.isnan(asc_longitude) or math.isnan(mc_longitude):
            raise CalculationError(
                "NaN value returned for Ascendant or Midheaven. "
                "Check latitude/longitude and date."
            )
        
        asc_longitude = asc_longitude % 360
        mc_longitude = mc_longitude % 360
        
        asc_sign, asc_degree = self._longitude_to_sign_degree(asc_longitude)
        mc_sign, mc_degree = self._longitude_to_sign_degree(mc_longitude)
        
        angles = {
            "Ascendant": AnglePosition(
                longitude=round(asc_longitude, 6),
                sign=asc_sign,
                degree=round(asc_degree, 6)
            ),
            "Midheaven": AnglePosition(
                longitude=round(mc_longitude, 6),
                sign=mc_sign,
                degree=round(mc_degree, 6)
            )
        }
        
        asc_sign_index = ZODIAC_SIGNS.index(asc_sign)
        houses = {}
        for house_num in range(1, 13):
            sign_index = (asc_sign_index + house_num - 1) % 12
            houses[str(house_num)] = ZODIAC_SIGNS[sign_index]
        
        return angles, houses

    def _validate_output(
        self,
        planets: Dict[str, PlanetPosition],
        angles: Dict[str, AnglePosition],
        houses: Dict[str, str]
    ) -> None:
        """
        Validate calculation output for consistency.
        
        Checks:
        - All longitudes in [0, 360)
        - No NaN values
        - Whole Sign house mapping is correct
        - Ascendant sign matches House 1
        """
        for name, pos in planets.items():
            if not (0 <= pos.longitude < 360):
                raise ValidationError(
                    f"Planet {name} longitude {pos.longitude} out of range [0, 360)"
                )
            if not (0 <= pos.degree < 30):
                raise ValidationError(
                    f"Planet {name} degree {pos.degree} out of range [0, 30)"
                )
        
        for name, pos in angles.items():
            if not (0 <= pos.longitude < 360):
                raise ValidationError(
                    f"Angle {name} longitude {pos.longitude} out of range [0, 360)"
                )
        
        asc_sign = angles["Ascendant"].sign
        house_1_sign = houses["1"]
        if asc_sign != house_1_sign:
            raise ValidationError(
                f"Whole Sign house validation failed: "
                f"Ascendant is in {asc_sign} but House 1 is {house_1_sign}"
            )
        
        asc_index = ZODIAC_SIGNS.index(asc_sign)
        for house_num in range(1, 13):
            expected_sign = ZODIAC_SIGNS[(asc_index + house_num - 1) % 12]
            actual_sign = houses[str(house_num)]
            if expected_sign != actual_sign:
                raise ValidationError(
                    f"Whole Sign house {house_num} should be {expected_sign}, "
                    f"got {actual_sign}"
                )

    def compute(self, input_data: ChartInput) -> ChartOutput:
        """
        Compute a complete natal chart.
        
        This is the primary entry point for chart calculation.
        
        Args:
            input_data: Validated ChartInput with datetime, location, settings
            
        Returns:
            ChartOutput with planets, angles, houses, and metadata
            
        Raises:
            CalculationError: If any calculation fails
            ValidationError: If output validation fails
        """
        dt = self._parse_datetime(input_data.datetime_utc)
        jd = self._datetime_to_julian_day(dt)
        
        planets = {}
        for planet_name, planet_id in PLANET_IDS.items():
            planets[planet_name] = self._calculate_planet_position(
                jd, planet_id, planet_name
            )
        
        angles, houses = self._calculate_houses_and_angles(
            jd,
            input_data.latitude,
            input_data.longitude
        )
        
        self._validate_output(planets, angles, houses)
        
        metadata = ChartMetadata(
            ephemeris="Swiss Ephemeris",
            calculation_method="pyswisseph",
            julian_day=round(jd, 6),
            precision="arcsecond",
            ephemeris_mode=self._ephemeris_mode
        )
        
        return ChartOutput(
            planets=planets,
            angles=angles,
            houses=houses,
            metadata=metadata
        )

    def close(self) -> None:
        """Clean up Swiss Ephemeris resources."""
        swe.close()


_engine_instance: Optional[SwissEphemerisEngine] = None


def get_engine(ephemeris_path: Optional[str] = None) -> SwissEphemerisEngine:
    """Get or create the singleton engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SwissEphemerisEngine(ephemeris_path)
    return _engine_instance


def compute_chart(input_data: ChartInput) -> ChartOutput:
    """
    Primary API function: Compute a natal chart.
    
    Args:
        input_data: ChartInput with datetime_utc, latitude, longitude, etc.
        
    Returns:
        ChartOutput with planets, angles, houses, metadata
        
    Example:
        >>> from astro_engine import compute_chart, ChartInput
        >>> input_data = ChartInput(
        ...     datetime_utc="1977-09-05T17:24:00Z",
        ...     latitude=37.82,
        ...     longitude=-79.82
        ... )
        >>> result = compute_chart(input_data)
        >>> print(result.planets["Sun"].sign)
        'Virgo'
    """
    engine = get_engine()
    return engine.compute(input_data)
