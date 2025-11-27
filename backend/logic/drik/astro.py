# backend/logic/drik/astro.py
"""
Astronomical core for Drik Panchang.
Implements:
- Tropical Sun longitude
- Sidereal Sun, Moon longitude (Lahiri)
- Tithi
- Nakshatra
- Yoga  (tropical Sun + sidereal Moon)
- Karana
- Boundary solvers
"""

import math
import swisseph as swe
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .utils import (
    norm_deg,
    utc_to_jd,
    jd_to_utc,
    init_ephemeris,
)

def _extract_lon(res):
    """
    Normalize swisseph calc_ut() output across Linux/Mac/Windows:
    Possible forms:
        (lon, lat)
        (lon, lat, dist)
        ((lon, lat), extra)
        ((lon,), extra)
    We always return lon as float.
    """
    # Case A: (lon, lat) or (lon, lat, dist)
    if isinstance(res, (list, tuple)) and isinstance(res[0], (int, float)):
        return float(res[0])

    # Case B: ((lon, lat), something)
    if isinstance(res, (list, tuple)) and isinstance(res[0], (list, tuple)):
        inner = res[0]
        if isinstance(inner[0], (int, float)):
            return float(inner[0])

    # If all fails:
    raise ValueError(f"Unknown calc_ut output format: {res}")


# -------------------------------------------------------
# Initialize Swiss Ephemeris (Lahiri)
# -------------------------------------------------------
init_ephemeris()

# -------------------------------------------------------
# Constants
# -------------------------------------------------------

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashirsha","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula",
    "Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

RASHIS = [
    "Mesha","Vrishabha","Mithuna","Karka","Simha","Kanya",
    "Tula","Vrischika","Dhanu","Makara","Kumbha","Meena"
]

YOGA_NAMES = [
    "Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda",
    "Sukarman","Dhriti","Shoola","Ganda","Vriddhi","Dhruva","Vyaghata",
    "Harshana","Vajra","Siddhi","Vyatipata","Variyana","Parigha","Shiva",
    "Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti"
]

MOVABLE_KARANAS = ["Bava","Balava","Kaulava","Taitila","Garaja","Vanija","Vishti"]
FIXED_KARANAS = ["Shakuni","Chatushpada","Naga","Kistughna"]


# -------------------------------------------------------
# Tropical Sun, Sidereal Sun, Sidereal Moon
# -------------------------------------------------------

def tropical_sun_longitude(jd):
    flag = swe.FLG_SWIEPH
    res = swe.calc_ut(jd, swe.SUN, flag)
    lon = _extract_lon(res)
    return norm_deg(lon)



def sidereal_moon_longitude(jd):
    flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    res = swe.calc_ut(jd, swe.MOON, flag)
    lon = _extract_lon(res)
    return norm_deg(lon)


def sidereal_sun_longitude(jd):
    flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    res = swe.calc_ut(jd, swe.SUN, flag)
    lon = _extract_lon(res)
    return norm_deg(lon)



# -------------------------------------------------------
# Tithi
# -------------------------------------------------------
def compute_tithi(jd):
    """
    Tithi index (1–30)
    Using sidereal Moon - sidereal Sun (Lahiri)
    """
    sun = sidereal_sun_longitude(jd)
    moon = sidereal_moon_longitude(jd)
    diff = norm_deg(moon - sun)
    return int(diff // 12) + 1


def compute_paksha(tithi):
    return "Shukla" if tithi <= 15 else "Krishna"


# -------------------------------------------------------
# Nakshatra
# -------------------------------------------------------
def compute_nakshatra(jd):
    moon = sidereal_moon_longitude(jd)
    index = int((moon * 60) // 800)     # 800 minutes = 13°20'
    name = NAKSHATRAS[index]
    return index + 1, name  # 1–27


# -------------------------------------------------------
# Yoga
# -------------------------------------------------------
def compute_yoga(jd):
    """
    Drik Panchang formula:
    Yoga = floor( (tropicalSun + siderealMoon) / 13°20' ) + 1
    """
    sun = tropical_sun_longitude(jd)
    moon = sidereal_moon_longitude(jd)
    total = norm_deg(sun + moon)
    index = int((total * 60) // 800)
    name = YOGA_NAMES[index]
    return index + 1, name  # 1–27


# -------------------------------------------------------
# Karana
# -------------------------------------------------------
def compute_karana(jd):
    """
    Karana index (1–60), mapped to:
    - 56–59 = 4 fixed karanas
    - 0–55 = repeating 7 movable karanas
    Based on half-tithis: each karana = 6° lunar elongation.
    """
    sun = sidereal_sun_longitude(jd)
    moon = sidereal_moon_longitude(jd)
    diff = norm_deg(moon - sun)
    half = int(diff // 6)  # 0–59

    if half >= 56:
        return FIXED_KARANAS[half - 56]
    else:
        return MOVABLE_KARANAS[half % 7]


# -------------------------------------------------------
# Rashi
# -------------------------------------------------------
def compute_rashi(jd):
    """Moon's rashi (sidereal)."""
    moon = sidereal_moon_longitude(jd)
    index = int(moon // 30)
    return RASHIS[index]


# -------------------------------------------------------
# boundary solvers — tithi/nakshatra/yoga/karana transitions
# -------------------------------------------------------
def _angle_tithi(jd):
    sun = sidereal_sun_longitude(jd)
    moon = sidereal_moon_longitude(jd)
    return norm_deg(moon - sun)


def _angle_nak(jd):
    return sidereal_moon_longitude(jd)


def _angle_yoga(jd):
    return norm_deg(tropical_sun_longitude(jd) + sidereal_moon_longitude(jd))


def binary_search_angle(func, start_jd, end_jd, target_deg, tol_seconds=1.0):
    """
    Generic modular-angle boundary finder.
    """
    def f(j):
        ang = func(j)
        x = norm_deg(ang - target_deg)
        return x - 360 if x > 180 else x

    a = start_jd
    b = end_jd
    fa = f(a)
    fb = f(b)

    if fa == 0:
        return a
    if fb == 0:
        return b

    # Ensure we bracket
    if fa * fb > 0:
        return None

    # Binary search
    while (b - a) * 86400 > tol_seconds:
        m = 0.5 * (a + b)
        fm = f(m)
        if fa * fm <= 0:
            b = m
            fb = fm
        else:
            a = m
            fa = fm

    return 0.5 * (a + b)
