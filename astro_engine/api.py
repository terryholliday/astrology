"""
FastAPI REST API for Swiss Ephemeris Engine.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError, BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import ChartInput, ChartOutput
from .engine import compute_chart, get_engine
from .exceptions import EphemerisError, ValidationError
from .database import get_db, init_db
from .db_models import StoredChart

app = FastAPI(
    title="TrueArk Ephemeris API",
    description="Canonical source of astrological truth. Production-grade planetary position calculator using Swiss Ephemeris.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChartInputWithEntity(ChartInput):
    """Chart input with optional entity linking."""
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None


class StoredChartResponse(BaseModel):
    """Response model for stored chart."""
    id: str
    datetime_utc: str
    latitude: float
    longitude: float
    planets: dict
    angles: dict
    houses: dict
    julian_day: float
    ephemeris_mode: str
    created_at: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize ephemeris engine and database on startup."""
    get_engine()
    init_db()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "engine": "TrueArk Ephemeris"}


@app.post("/chart", response_model=ChartOutput)
async def calculate_chart(input_data: ChartInput) -> ChartOutput:
    """
    Calculate a natal chart (no persistence).
    
    Returns planetary positions, angles, and Whole Sign houses.
    """
    try:
        result = compute_chart(input_data)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except EphemerisError as e:
        raise HTTPException(status_code=500, detail=f"Ephemeris calculation error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.post("/chart/store", response_model=StoredChartResponse)
async def calculate_and_store_chart(
    input_data: ChartInputWithEntity,
    db: AsyncSession = Depends(get_db)
) -> StoredChartResponse:
    """
    Calculate a natal chart and persist to database.
    
    This creates a permanent truth record.
    """
    try:
        result = compute_chart(input_data)
        
        stored = StoredChart(
            datetime_utc=input_data.datetime_utc,
            latitude=input_data.latitude,
            longitude=input_data.longitude,
            planets={k: v.model_dump() for k, v in result.planets.items()},
            angles={k: v.model_dump() for k, v in result.angles.items()},
            houses=result.houses,
            julian_day=result.metadata.julian_day,
            ephemeris_mode=result.metadata.ephemeris_mode,
            entity_id=input_data.entity_id,
            entity_type=input_data.entity_type,
        )
        
        db.add(stored)
        await db.commit()
        await db.refresh(stored)
        
        return StoredChartResponse(**stored.to_dict())
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except EphemerisError as e:
        raise HTTPException(status_code=500, detail=f"Ephemeris calculation error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.get("/charts", response_model=List[StoredChartResponse])
async def list_charts(
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> List[StoredChartResponse]:
    """
    List stored charts with optional filtering.
    """
    query = select(StoredChart).order_by(StoredChart.created_at.desc()).limit(limit)
    
    if entity_id:
        query = query.where(StoredChart.entity_id == entity_id)
    if entity_type:
        query = query.where(StoredChart.entity_type == entity_type)
    
    result = await db.execute(query)
    charts = result.scalars().all()
    
    return [StoredChartResponse(**c.to_dict()) for c in charts]


@app.get("/charts/{chart_id}", response_model=StoredChartResponse)
async def get_chart(
    chart_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> StoredChartResponse:
    """
    Retrieve a specific stored chart by ID.
    """
    result = await db.execute(select(StoredChart).where(StoredChart.id == chart_id))
    chart = result.scalar_one_or_none()
    
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    
    return StoredChartResponse(**chart.to_dict())


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "TrueArk Ephemeris API",
        "version": "1.0.0",
        "domain": "trueark.io",
        "endpoints": {
            "POST /chart": "Calculate natal chart (no persistence)",
            "POST /chart/store": "Calculate and persist chart",
            "GET /charts": "List stored charts",
            "GET /charts/{id}": "Get specific chart",
            "GET /health": "Health check",
        },
        "documentation": "/docs",
    }
