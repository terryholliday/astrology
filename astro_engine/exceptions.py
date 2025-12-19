"""
Custom exceptions for the Swiss Ephemeris Engine.
All failures are LOUD — no silent degradation.
"""


class EphemerisError(Exception):
    """Raised when Swiss Ephemeris operations fail."""
    pass


class ValidationError(Exception):
    """Raised when input or output validation fails."""
    pass


class EphemerisFileError(EphemerisError):
    """Raised when required ephemeris files are missing or corrupt."""
    pass


class CalculationError(EphemerisError):
    """Raised when a calculation produces invalid results."""
    pass
