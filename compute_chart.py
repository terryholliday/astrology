#!/usr/bin/env python3
"""
Swiss Ephemeris Engine — CLI Entry Point

Usage:
    python compute_chart.py --datetime "1977-09-05T17:24:00Z" --lat 37.82 --lon -79.82 --pretty
    python compute_chart.py --json '{"datetime_utc": "1977-09-05T17:24:00Z", "latitude": 37.82, "longitude": -79.82}'
"""

import sys
from astro_engine.cli import main

if __name__ == "__main__":
    sys.exit(main())
