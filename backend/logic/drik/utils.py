# backend/logic/drik/utils.py
"""
Utility functions for the Drik Panchang engine.
This includes:
- timezone-safe conversions
- cross-platform time formatting
- Julian day conversions
- normalization helpers
- Swiss ephemeris initialization
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os
import swisseph as swe


# -------------------------------------------------------------
# Cross-platform safe time formatting: "4:07", "11:59"
# Drik Panchang does NOT use leading zeros in hour fields
# -------------------------------------------------------------
def fmt_hm(dt):
    if dt is None:
        return "—"
    s = dt.strftime("%I:%M")      # Always Windows-safe
    s = s.lstrip("0")             # Remove leading zero
    return s if s else "0"


# -------------------------------------------------------------
# Local <-> UTC conversions
# -------------------------------------------------------------
def local_to_utc(date_str, time_str, tz_name):
    """
    date_str: "YYYY-MM-DD"
    time_str: "HH:MM"
    returns:
        dt_local (tz-aware)
        dt_utc   (tz-aware UTC)
    """
    if not time_str:
        time_str = "00:00"

    tz = ZoneInfo(tz_name)
    dt_local = datetime.fromisoformat(f"{date_str}T{time_str}")
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=tz)

    return dt_local, dt_local.astimezone(timezone.utc)


# -------------------------------------------------------------
# Julian Day conversions (Swiss Ephemeris)
# -------------------------------------------------------------
def utc_to_jd(dt_utc):
    """
    Convert UTC datetime → Julian Day (UT)
    """
    y = dt_utc.year
    m = dt_utc.month
    d = dt_utc.day
    hour = (
        dt_utc.hour
        + dt_utc.minute / 60
        + dt_utc.second / 3600
        + dt_utc.microsecond / 3_600_000_000
    )
    return swe.julday(y, m, d, hour)


def jd_to_utc(jd):
    """
    Convert Julian Day → datetime (UTC)
    """
    y, m, d, hour = swe.revjul(jd)
    h = int(hour)
    s = int((hour - h) * 3600)
    mi = s // 60
    sec = s - (mi * 60)
    return datetime(y, m, d, h, mi, sec, tzinfo=timezone.utc)


# -------------------------------------------------------------
# Degree normalization 0–360
# -------------------------------------------------------------
def norm_deg(x):
    x = float(x) % 360.0
    return x + 360 if x < 0 else x


# -------------------------------------------------------------
# Initialize Swiss Ephemeris — IMPORTANT
# -------------------------------------------------------------
def init_ephemeris():
    """
    Drik Panchang uses Swiss Ephemeris data files.
    If ephemeris/ directory exists, use it.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # Lahiri ayanamsa

    this = os.path.dirname(os.path.abspath(__file__))
    eph_dir = os.path.join(this, "ephemeris")

    if os.path.isdir(eph_dir):
        swe.set_ephe_path(eph_dir)
    else:
        # fallback to default swisseph data path
        swe.set_ephe_path(os.getcwd())
