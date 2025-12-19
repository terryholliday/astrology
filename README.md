# Swiss Ephemeris Engine — Proveniq Astro Core

Production-grade planetary position calculator using Swiss Ephemeris.

**Zero tolerance for approximation. All calculations derived from Swiss Ephemeris.**

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Ephemeris Files (REQUIRED for production precision)

See `EPHEMERIS_SETUP.md` for detailed instructions.

```powershell
cd ephemeris_data
Invoke-WebRequest -Uri "https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1" -OutFile "sepl_18.se1"
Invoke-WebRequest -Uri "https://www.astro.com/ftp/swisseph/ephe/semo_18.se1" -OutFile "semo_18.se1"
```

**Note:** Without `.se1` files, the engine falls back to Moshier ephemeris (~1 arcsecond precision vs ~0.001 arcsecond with Swiss Ephemeris files).

### 3. Compute a Chart

**CLI:**
```bash
python compute_chart.py --datetime "1977-09-05T17:24:00Z" --lat 37.82 --lon -79.82 --pretty
```

**Python:**
```python
from astro_engine import compute_chart, ChartInput

input_data = ChartInput(
    datetime_utc="1977-09-05T17:24:00Z",
    latitude=37.82,
    longitude=-79.82
)

result = compute_chart(input_data)
print(result.planets["Sun"].sign)  # "Virgo"
print(result.angles["Ascendant"].longitude)  # 252.xxx
```

## Input Contract

```json
{
  "datetime_utc": "1977-09-05T17:24:00Z",
  "latitude": 37.82,
  "longitude": -79.82,
  "house_system": "W",
  "zodiac": "tropical",
  "ayanamsa": null
}
```

- `datetime_utc`: ISO 8601 UTC datetime
- `latitude`: Geographic latitude (-90 to 90)
- `longitude`: Geographic longitude (-180 to 180)
- `house_system`: "W" (Whole Sign only)
- `zodiac`: "tropical" (only supported option)
- `ayanamsa`: Must be null (sidereal not supported)

## Output Contract

```json
{
  "planets": {
    "Sun": { "longitude": 162.345, "sign": "Virgo", "degree": 12.345, "retrograde": false }
  },
  "angles": {
    "Ascendant": { "longitude": 252.110, "sign": "Sagittarius", "degree": 12.110 },
    "Midheaven": { "longitude": 166.003, "sign": "Virgo", "degree": 16.003 }
  },
  "houses": {
    "1": "Sagittarius",
    "2": "Capricorn",
    ...
  },
  "metadata": {
    "ephemeris": "Swiss Ephemeris",
    "calculation_method": "pyswisseph",
    "julian_day": 2443392.225,
    "precision": "arcsecond",
    "ephemeris_mode": "swiss"
  }
}
```

## Calculated Bodies

- **Planets:** Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto
- **Points:** True Node
- **Angles:** Ascendant, Midheaven

## Validation

The engine performs strict validation:

1. All longitudes must be in [0, 360)
2. All degrees must be in [0, 30)
3. No NaN values allowed
4. Whole Sign house mapping must be consistent with Ascendant
5. House sequence must follow zodiac order

**If ANY validation fails → ERROR is raised. No silent failures.**

## Testing

```bash
pytest tests/ -v
```

## Architecture

```
astro_engine/
├── __init__.py      # Public API exports
├── engine.py        # Core calculation engine
├── models.py        # Pydantic input/output contracts
├── constants.py     # Zodiac signs, planet IDs
├── exceptions.py    # Custom exceptions
└── cli.py           # Command-line interface
```

## Error Handling

- `EphemerisError`: Swiss Ephemeris operation failed
- `EphemerisFileError`: Required ephemeris files missing
- `CalculationError`: Calculation produced invalid results
- `ValidationError`: Input or output validation failed

All errors are **LOUD**. No silent degradation.

## License

Swiss Ephemeris is licensed under AGPL or Swiss Ephemeris Professional License.
See https://www.astro.com/swisseph/ for details.
