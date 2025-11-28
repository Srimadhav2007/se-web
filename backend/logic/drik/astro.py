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
    Robust extraction of longitude from swisseph.calc_ut() result across Windows/Linux variants.
    Returns float longitude (degrees).
    """
    # common: res = (lon, lat) or (lon, lat, dist)
    if isinstance(res, (list, tuple)):
        if len(res) >= 1 and isinstance(res[0], (int, float)):
            return float(res[0])
        # sometimes windows returns ((lon,lat), something)
        if len(res) >= 1 and isinstance(res[0], (list, tuple)) and isinstance(res[0][0], (int, float)):
            return float(res[0][0])
    raise ValueError(f"Unknown calc_ut() output format: {res}")


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
    """Tropical Sun longitude in degrees (explicit extraction)."""
    flag = swe.FLG_SWIEPH  # tropical output
    res = swe.calc_ut(jd, swe.SUN, flag)
    lon = _extract_lon(res)
    return norm_deg(lon)


def sidereal_moon_longitude(jd):
    """Sidereal Moon longitude (Lahiri)."""
    flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    res = swe.calc_ut(jd, swe.MOON, flag)
    lon = _extract_lon(res)
    return norm_deg(lon)


def sidereal_sun_longitude(jd):
    """Sidereal Sun longitude (Lahiri)."""
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
    Drik: Yoga = floor((TropicalSun + SiderealMoon) / 13°20') + 1
    """
    sun = tropical_sun_longitude(jd)
    moon = sidereal_moon_longitude(jd)
    total = norm_deg(sun + moon)
    index = int((total * 60) // 800)
    name = YOGA_NAMES[index-2]
    return index + 1, name

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
    index = int(moon // 30) % 12
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

# -------------------------------------------------------
# Masa (Purnimanta) — Sidereal Sun method
# -------------------------------------------------------

MASA_NAMES = [
    "Chaitra","Vaishakha","Jyeshtha","Ashadha",
    "Shravana","Bhadrapada","Ashwin","Kartika",
    "Margashirsha","Pausha","Magha","Phalguna"
]


def compute_masa(jd):
    """
    Purnimanta Masa:
    masa = floor(sidereal_sun_longitude / 30)

    Example:
    0°–30°  → Chaitra
    30°–60° → Vaishakha
    ...
    240°–270° → Margashirsha
    270°–300° → Pausha
    """
    sun_sid = sidereal_sun_longitude(jd)
    idx = int(sun_sid // 30)
    return MASA_NAMES[idx], idx


# -------------------------------------------------------
# Nakshatra helper for any JD (re-use existing logic)
# -------------------------------------------------------

def nakshatra_for_jd(jd):
    idx, name = compute_nakshatra(jd)
    return name, idx


# -------------------------------------------------------
# Full Moon Finder — High Accuracy (~1 second)
# -------------------------------------------------------

def find_next_full_moon(jd_start, max_days=40):
    """
    Find the next full moon: Moon - Sun = 180° (sidereal)

    Steps:
    1. Coarse scan: 1 hour steps
    2. Detect crossing of elongation - 180
    3. Binary refine to ±1 second

    Returns:
        jd_full (float)  - julian day (UT)
    """
    target = 180.0

    # Coarse scan
    step_hours = 1.0
    step = step_hours / 24.0

    prev_jd = jd_start
    prev_diff = norm_deg(sidereal_moon_longitude(prev_jd) -
                         sidereal_sun_longitude(prev_jd)) - target

    for i in range(int(max_days * 24)):  # 40 days × 24 = 960 checks
        jd = jd_start + (i + 1) * step
        diff = norm_deg(sidereal_moon_longitude(jd) -
                        sidereal_sun_longitude(jd)) - target

        # Normalize to [-180,180]
        if prev_diff > 180: prev_diff -= 360
        if prev_diff < -180: prev_diff += 360
        if diff > 180: diff -= 360
        if diff < -180: diff += 360

        # Zero-crossing
        if prev_diff * diff <= 0:
            # refine by binary search
            return _refine_full_moon(prev_jd, jd, target)

        prev_jd = jd
        prev_diff = diff

    return None


def _refine_full_moon(j1, j2, target):
    """Binary refine the full moon moment."""
    for _ in range(60):  # ~60 iterations → sub-second precision
        jm = 0.5 * (j1 + j2)
        d1 = norm_deg(sidereal_moon_longitude(j1) -
                       sidereal_sun_longitude(j1)) - target
        d2 = norm_deg(sidereal_moon_longitude(jm) -
                       sidereal_sun_longitude(jm)) - target

        # normalize into [-180,180]
        if d1 > 180: d1 -= 360
        if d1 < -180: d1 += 360
        if d2 > 180: d2 -= 360
        if d2 < -180: d2 += 360

        if d1 * d2 <= 0:
            j2 = jm
        else:
            j1 = jm

    return 0.5 * (j1 + j2)

