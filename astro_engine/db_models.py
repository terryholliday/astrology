"""
SQLAlchemy database models for chart persistence.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class StoredChart(Base):
    """
    Persisted natal chart calculation.
    
    This is the truth ledger — every chart computed becomes a permanent record.
    """
    __tablename__ = "charts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Input parameters (the query)
    datetime_utc = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Computed output (the truth)
    planets = Column(JSON, nullable=False)
    angles = Column(JSON, nullable=False)
    houses = Column(JSON, nullable=False)
    
    # Metadata
    julian_day = Column(Float, nullable=False, index=True)
    ephemeris_mode = Column(String, nullable=False)
    
    # Record keeping
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Optional: link to external entity (for Proveniq integration)
    entity_id = Column(String, nullable=True, index=True)
    entity_type = Column(String, nullable=True)  # "person", "event", "asset", etc.

    __table_args__ = (
        Index("ix_charts_location", "latitude", "longitude"),
        Index("ix_charts_datetime_location", "datetime_utc", "latitude", "longitude"),
    )

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "datetime_utc": self.datetime_utc,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "planets": self.planets,
            "angles": self.angles,
            "houses": self.houses,
            "julian_day": self.julian_day,
            "ephemeris_mode": self.ephemeris_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
        }
