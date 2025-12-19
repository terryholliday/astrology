"""
Constants for the Swiss Ephemeris Engine.
"""

import swisseph as swe

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "TrueNode": swe.TRUE_NODE,
}

HOUSE_SYSTEMS = {
    "W": b"W",  # Whole Sign
    "P": b"P",  # Placidus
    "K": b"K",  # Koch
    "E": b"E",  # Equal
    "R": b"R",  # Regiomontanus
}

SUPPORTED_HOUSE_SYSTEM = "W"  # Whole Sign ONLY per spec
