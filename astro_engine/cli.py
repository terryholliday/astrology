"""
Command-line interface for the Swiss Ephemeris Engine.
"""

import argparse
import json
import sys
from typing import Optional

from .models import ChartInput, ChartOutput
from .engine import compute_chart, get_engine
from .exceptions import EphemerisError, ValidationError


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Swiss Ephemeris Engine — Compute natal chart positions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --datetime "1977-09-05T17:24:00Z" --lat 37.82 --lon -79.82
  %(prog)s --json '{"datetime_utc": "1977-09-05T17:24:00Z", "latitude": 37.82, "longitude": -79.82}'
        """
    )
    
    parser.add_argument(
        "--datetime", "-d",
        type=str,
        help="UTC datetime in ISO 8601 format (e.g., '1977-09-05T17:24:00Z')"
    )
    parser.add_argument(
        "--lat", "--latitude",
        type=float,
        help="Geographic latitude in decimal degrees (-90 to 90)"
    )
    parser.add_argument(
        "--lon", "--longitude",
        type=float,
        help="Geographic longitude in decimal degrees (-180 to 180)"
    )
    parser.add_argument(
        "--json", "-j",
        type=str,
        help="Full input as JSON string"
    )
    parser.add_argument(
        "--ephemeris-path", "-e",
        type=str,
        default=None,
        help="Path to ephemeris data files directory"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty-print JSON output"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for CLI."""
    args = parse_args()
    
    try:
        if args.json:
            input_dict = json.loads(args.json)
            input_data = ChartInput(**input_dict)
        elif args.datetime and args.lat is not None and args.lon is not None:
            input_data = ChartInput(
                datetime_utc=args.datetime,
                latitude=args.lat,
                longitude=args.lon
            )
        else:
            print(
                "ERROR: Must provide either --json or (--datetime, --lat, --lon)",
                file=sys.stderr
            )
            return 1
        
        if args.ephemeris_path:
            get_engine(args.ephemeris_path)
        
        result = compute_chart(input_data)
        
        output = result.model_dump()
        
        if args.pretty:
            print(json.dumps(output, indent=2))
        else:
            print(json.dumps(output))
        
        return 0
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON input: {e}", file=sys.stderr)
        return 1
    except ValidationError as e:
        print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        return 2
    except EphemerisError as e:
        print(f"EPHEMERIS ERROR: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        return 99


if __name__ == "__main__":
    sys.exit(main())
