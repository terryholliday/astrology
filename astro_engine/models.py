"""
Pydantic models for strict input/output contracts.
"""

from typing import Optional, Dict, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class ChartInput(BaseModel):
    """Input contract for chart calculation."""
    
    datetime_utc: str = Field(
        ...,
        description="ISO 8601 UTC datetime string (e.g., '1977-09-05T17:24:00Z')"
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Geographic latitude in decimal degrees"
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Geographic longitude in decimal degrees"
    )
    house_system: Literal["W"] = Field(
        default="W",
        description="House system (W = Whole Sign only)"
    )
    zodiac: Literal["tropical"] = Field(
        default="tropical",
        description="Zodiac type (tropical only)"
    )
    ayanamsa: Optional[str] = Field(
        default=None,
        description="Ayanamsa for sidereal (not supported, must be null)"
    )

    @field_validator("datetime_utc")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        """Validate ISO 8601 format."""
        try:
            if v.endswith("Z"):
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            else:
                datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {v}. Use ISO 8601 (e.g., '1977-09-05T17:24:00Z')") from e
        return v

    @field_validator("ayanamsa")
    @classmethod
    def validate_ayanamsa(cls, v: Optional[str]) -> Optional[str]:
        """Ayanamsa must be null for tropical zodiac."""
        if v is not None:
            raise ValueError("Sidereal zodiac not supported. ayanamsa must be null.")
        return v


class PlanetPosition(BaseModel):
    """Position data for a single planet."""
    
    longitude: float = Field(..., ge=0.0, lt=360.0)
    sign: str
    degree: float = Field(..., ge=0.0, lt=30.0)
    retrograde: bool = False


class AnglePosition(BaseModel):
    """Position data for an angle (Ascendant, Midheaven)."""
    
    longitude: float = Field(..., ge=0.0, lt=360.0)
    sign: str
    degree: float = Field(..., ge=0.0, lt=30.0)


class ChartMetadata(BaseModel):
    """Metadata about the calculation."""
    
    ephemeris: str = "Swiss Ephemeris"
    calculation_method: str = "pyswisseph"
    julian_day: float
    precision: str = "arcsecond"
    ephemeris_mode: str  # "swiss" or "moshier"


class ChartOutput(BaseModel):
    """Output contract for chart calculation."""
    
    planets: Dict[str, PlanetPosition]
    angles: Dict[str, AnglePosition]
    houses: Dict[str, str]  # House number -> Sign name
    metadata: ChartMetadata
