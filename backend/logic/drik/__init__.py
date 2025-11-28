# backend/logic/drik/__init__.py

from .api import (
    get_core_panchanga,
    get_hindu_time,
    merge_panchanga,
)

# Import get_planet_positions from the parent drik.py (Skyfield version)
# This is a workaround since the function uses Skyfield, not Swiss Ephemeris
import sys
from pathlib import Path
_parent_drik = Path(__file__).parent.parent / "drik.py"
if _parent_drik.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("drik_skyfield", _parent_drik)
    drik_skyfield = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(drik_skyfield)
    get_planet_positions = drik_skyfield.get_planet_positions
else:
    # Fallback: define a stub if file doesn't exist
    def get_planet_positions(*args, **kwargs):
        raise NotImplementedError("get_planet_positions requires drik.py (Skyfield version)")

__all__ = [
    "get_core_panchanga",
    "get_hindu_time",
    "merge_panchanga",
    "get_planet_positions",
]
