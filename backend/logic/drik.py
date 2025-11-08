# -*- coding: utf-8 -*-
"""
Drik Panchang core: fast + precise (Swiss Ephemeris) sidereal calculations.

pip install swisseph
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Tuple, Optional, Dict

import swisseph as swe
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Use built-in Moshier ephemeris (no external files needed)
swe.set_ephe_path("")

# ----------------------------
# Constants / Lookups
# ----------------------------

NAKSHATRAS = [
    "Ashwini (अश्विनी)", "Bharani (भरणी)", "Krittika (कृत्तिका)", "Rohini (रोहिणी)",
    "Mrigashira (मृगशीर्ष)", "Ardra (आर्द्रा)", "Punarvasu (पुनर्वसु)", "Pushya (पुष्य)",
    "Ashlesha (आश्लेषा)", "Magha (मघा)", "Purva Phalguni (पूर्व फाल्गुनी)",
    "Uttara Phalguni (उत्तर फाल्गुनी)", "Hasta (हस्त)", "Chitra (चित्रा)", "Swati (स्वाति)",
    "Vishakha (विशाखा)", "Anuradha (अनुराधा)", "Jyeshtha (ज्येष्ठा)", "Mula (मूल)",
    "Purva Ashadha (पूर्वाषाढा)", "Uttara Ashadha (उत्तराषाढा)", "Shravana (श्रवण)",
    "Dhanishtha (धनिष्ठा)", "Shatabhisha (शतभिषक्)", "Purva Bhadrapada (पूर्व भाद्रपदा)",
    "Uttara Bhadrapada (उत्तर भाद्रबदा)", "Revati (रेवती)"
]

RASHIS = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)",
    "Karka (Cancer)", "Simha (Leo)", "Kanya (Virgo)",
    "Tula (Libra)", "Vrishchika (Scorpio)", "Dhanu (Sagittarius)",
    "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
]

YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
    "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti"
]

KARANA_REPEATING = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti (Bhadra)"]
def _build_karana_cycle():
    seq = ["Kimstughna"]
    for i in range(1, 56):
        seq.append(KARANA_REPEATING[(i-1) % 7])
    seq += ["Shakuni", "Chatushpada", "Naga"]
    seq.append("Kimstughna")
    return seq
KARANAS_60 = _build_karana_cycle()

SIDEREAL_ARCLEN = 360.0
NAK_ARC = 13.0 + 20.0/60.0
RASHI_ARC = 30.0
TITHI_ARC = 12.0
KARANA_ARC = 6.0

# ----------------------------
# Data structures
# ----------------------------

@dataclass(frozen=True)
class Location:
    lat: float
    lon: float
    elevation_m: float = 0.0

@dataclass
class InstantPanchanga:
    dt_local: datetime
    jd_ut: float
    tithi: int
    paksha: str
    nakshatra: str
    rashi: str
    yoga: str
    karana: str
    moon_lon_sidereal: float
    sun_lon_sidereal: float

@dataclass
class DayPanchanga:
    sunrise_local: datetime
    sunset_local: datetime
    tithi_at_sunrise: int
    paksha_at_sunrise: str
    nakshatra_at_sunrise: str
    yoga_at_sunrise: str
    rashi_moon_at_sunrise: str

@dataclass
class FullMoonInfo:
    dt_utc: datetime
    dt_local: datetime
    nakshatra_at_fullmoon: str
    masa_from_fullmoon: Optional[str]

# Lahiri sidereal
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

# ----------------------------
# Swiss Ephemeris helpers
# ----------------------------

def _sanity_check_jd(jd: float) -> None:
    if not (2_000_000 < jd < 3_500_000):
        raise RuntimeError(f"JD out of sane range: {jd}")

@lru_cache(maxsize=4096)
def _to_jd_ut(dt_utc: datetime) -> float:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))
    else:
        dt_utc = dt_utc.astimezone(ZoneInfo("UTC"))
    jd = swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600.0,
        swe.GREG_CAL
    )
    _sanity_check_jd(jd)
    return jd

def _sidereal_longitude(jd_ut: float, body: int) -> float:
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
    pos, retflag = swe.calc_ut(jd_ut, body, flags)
    if retflag < 0:
        raise RuntimeError(f"Swiss Ephemeris calculation error for body {body}, retflag={retflag}")
    lon = pos[0]
    return lon % 360.0

def _tropical_longitude(jd_ut: float, body: int) -> float:
    """Get tropical longitude (for sunrise calculation)"""
    flags = swe.FLG_MOSEPH
    pos, retflag = swe.calc_ut(jd_ut, body, flags)
    if retflag < 0:
        raise RuntimeError(f"Swiss Ephemeris calculation error for body {body}, retflag={retflag}")
    lon = pos[0]
    return lon % 360.0

def _revjul_utc(jd_ut: float) -> datetime:
    y, m, d, fr = swe.revjul(jd_ut, swe.GREG_CAL)
    hh = fr * 24.0
    h = int(hh)
    mm_float = (hh - h) * 60.0
    mm = int(mm_float)
    ss_float = (mm_float - mm) * 60.0
    ss = int(round(ss_float))
    
    # Handle edge cases where rounding causes overflow
    if ss >= 60:
        ss = 0
        mm += 1
    if mm >= 60:
        mm = 0
        h += 1
    if h >= 24:
        h = 0
        # Ideally would increment day, but for our use case this is rare
    
    # Clamp values to valid ranges
    h = max(0, min(23, h))
    mm = max(0, min(59, mm))
    ss = max(0, min(59, ss))
    
    return datetime(y, m, d, h, mm, ss, tzinfo=ZoneInfo("UTC"))

def _sun_altitude(jd_ut: float, lat: float, lon: float) -> float:
    """
    Calculate sun's altitude above horizon in degrees.
    Uses tropical coordinates for physical position.
    """
    # Get tropical sun position
    flags = swe.FLG_MOSEPH | swe.FLG_EQUATORIAL
    pos, retflag = swe.calc_ut(jd_ut, swe.SUN, flags)
    if retflag < 0:
        return -999.0
    
    ra = pos[0]  # Right ascension in degrees
    dec = pos[1]  # Declination in degrees
    
    # Calculate local sidereal time
    jd_tt = jd_ut + swe.deltat(jd_ut)
    lst = swe.sidtime(jd_ut) * 15.0  # Convert hours to degrees
    lst += lon  # Add longitude
    
    # Hour angle
    ha = lst - ra
    
    # Convert to radians
    ha_rad = math.radians(ha)
    dec_rad = math.radians(dec)
    lat_rad = math.radians(lat)
    
    # Calculate altitude
    sin_alt = (math.sin(lat_rad) * math.sin(dec_rad) + 
               math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad))
    
    altitude = math.degrees(math.asin(sin_alt))
    return altitude

def _find_sunrise_sunset_simple(dt_local: datetime, loc: Location, tz: ZoneInfo):
    """
    Simple iterative method to find sunrise and sunset.
    Searches for when sun crosses the horizon.
    """
    # Start from midnight local time
    date_midnight = dt_local.replace(hour=0, minute=0, second=0, microsecond=0)
    jd_start = _to_jd_ut(date_midnight.astimezone(ZoneInfo("UTC")))
    
    # Sun altitude at horizon (accounting for refraction and disc)
    horizon_alt = -0.833  # Standard value
    
    sunrise_jd = None
    sunset_jd = None
    
    # Search in 5-minute increments through the day
    step = 5.0 / (24.0 * 60.0)  # 5 minutes in days
    
    for i in range(int(24 * 60 / 5)):  # 24 hours / 5 minutes
        jd = jd_start + i * step
        jd_next = jd + step
        
        alt1 = _sun_altitude(jd, loc.lat, loc.lon)
        alt2 = _sun_altitude(jd_next, loc.lat, loc.lon)
        
        # Sunrise: crosses from below to above horizon
        if alt1 < horizon_alt and alt2 >= horizon_alt and sunrise_jd is None:
            # Refine with bisection
            a, b = jd, jd_next
            for _ in range(10):  # 10 iterations gives ~5 second accuracy
                mid = (a + b) / 2.0
                alt_mid = _sun_altitude(mid, loc.lat, loc.lon)
                if alt_mid < horizon_alt:
                    a = mid
                else:
                    b = mid
            sunrise_jd = (a + b) / 2.0
        
        # Sunset: crosses from above to below horizon
        if alt1 >= horizon_alt and alt2 < horizon_alt and sunset_jd is None:
            # Refine with bisection
            a, b = jd, jd_next
            for _ in range(10):
                mid = (a + b) / 2.0
                alt_mid = _sun_altitude(mid, loc.lat, loc.lon)
                if alt_mid >= horizon_alt:
                    a = mid
                else:
                    b = mid
            sunset_jd = (a + b) / 2.0
        
        if sunrise_jd and sunset_jd:
            break
    
    if not sunrise_jd or not sunset_jd:
        raise RuntimeError(f"Could not find sunrise/sunset for location lat={loc.lat}, lon={loc.lon}")
    
    sunrise_utc = _revjul_utc(sunrise_jd)
    sunset_utc = _revjul_utc(sunset_jd)
    
    return sunrise_utc.astimezone(tz), sunset_utc.astimezone(tz)

def _sunrise_sunset(dt_local: datetime, loc: Location, tz: ZoneInfo):
    """Calculate sunrise and sunset using simple algorithm."""
    return _find_sunrise_sunset_simple(dt_local, loc, tz)

# ----------------------------
# Core Panchanga math (sidereal)
# ----------------------------

def _tithi_and_paksha(moon_lon: float, sun_lon: float) -> Tuple[int, str, float]:
    sep = (moon_lon - sun_lon) % 360.0
    tithi_float = sep / TITHI_ARC
    tithi_num = int(math.floor(tithi_float)) + 1
    paksha = "Shukla (Waxing)" if tithi_num <= 15 else "Krishna (Waning)"
    return tithi_num, paksha, tithi_float

def _nakshatra(moon_lon: float) -> Tuple[int, str, float]:
    nak_float = moon_lon / NAK_ARC
    idx = int(math.floor(nak_float)) % 27
    return idx + 1, NAKSHATRAS[idx], nak_float

def _rashi(lon: float) -> str:
    return RASHIS[int(math.floor(lon / RASHI_ARC)) % 12]

def _yoga(moon_lon: float, sun_lon: float) -> Tuple[int, str, float]:
    y = ((moon_lon + sun_lon) % 360.0) / NAK_ARC
    idx = int(math.floor(y)) % 27
    return idx + 1, YOGAS[idx], y

def _karana(moon_lon: float, sun_lon: float) -> Tuple[str, int]:
    k_idx = int(math.floor(((moon_lon - sun_lon) % 360.0) / KARANA_ARC)) % 60
    return KARANAS_60[k_idx], k_idx

# ----------------------------
# Full moon search & masa mapping
# ----------------------------

def _elongation_deg(jd_ut: float) -> float:
    m = _sidereal_longitude(jd_ut, swe.MOON)
    s = _sidereal_longitude(jd_ut, swe.SUN)
    return (m - s) % 360.0

def _jd_to_datetime_utc(jd_ut: float) -> datetime:
    return _revjul_utc(jd_ut)

def _next_full_moon_utc(start_utc: datetime) -> Optional[datetime]:
    jd = _to_jd_ut(start_utc)
    e0 = _elongation_deg(jd)
    step = 0.25
    for _ in range(400):
        jd2 = jd + step
        e1 = _elongation_deg(jd2)
        crossed = (e0 < 180.0 <= e1) or (e0 > 180.0 >= e1)
        if crossed:
            a, b = jd, jd2
            for _ in range(40):
                mid = (a + b) / 2.0
                em = _elongation_deg(mid)
                if em >= 180.0:
                    b = mid
                else:
                    a = mid
            return _jd_to_datetime_utc((a + b) / 2.0)
        jd, e0 = jd2, e1
    return None

MASA_MAPPING = {
    "Chitra": "Chaitra", "Vishakha": "Vaishakha",
    "Jyeshtha": "Jyeshtha", "Mula": "Jyeshtha",
    "Purva Ashadha": "Ashadha", "Uttara Ashadha": "Ashadha",
    "Shravana": "Shravana",
    "Purva Bhadrapada": "Bhadrapada", "Uttara Bhadrapada": "Bhadrapada",
    "Ashwini": "Ashvina",
    "Krittika": "Karttika",
    "Mrigashira": "Margashirsha",
    "Pushya": "Pausha",
    "Magha": "Magha",
    "Purva Phalguni": "Phalguna", "Uttara Phalguni": "Phalguna",
}

def _masa_from_fullmoon_nak(nak_name: str) -> Optional[str]:
    for key, val in MASA_MAPPING.items():
        if key in nak_name:
            return val
    return None

# ----------------------------
# Public API
# ----------------------------

def get_panchanga_drik(
    date_str: str, time_str: str, tz_str: str, lat: float, lon: float, elevation_m: float = 0.0
) -> Dict:
    tz = ZoneInfo(tz_str)
    loc = Location(lat=lat, lon=lon, elevation_m=elevation_m)

    dt_local = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
    jd = _to_jd_ut(dt_utc)

    moon_lon = _sidereal_longitude(jd, swe.MOON)
    sun_lon  = _sidereal_longitude(jd, swe.SUN)

    tithi_num, paksha, _ = _tithi_and_paksha(moon_lon, sun_lon)
    _, nak_name, _ = _nakshatra(moon_lon)
    _, yoga_name, _ = _yoga(moon_lon, sun_lon)
    rashi_name = _rashi(moon_lon)
    karana_name, _ = _karana(moon_lon, sun_lon)

    instant = InstantPanchanga(
        dt_local=dt_local,
        jd_ut=jd,
        tithi=tithi_num,
        paksha=paksha,
        nakshatra=nak_name,
        rashi=rashi_name,
        yoga=yoga_name,
        karana=karana_name,
        moon_lon_sidereal=moon_lon,
        sun_lon_sidereal=sun_lon,
    )

    sunrise_local, sunset_local = _sunrise_sunset(dt_local, loc, tz)
    jd_sr = _to_jd_ut(sunrise_local.astimezone(ZoneInfo("UTC")))
    moon_lon_sr = _sidereal_longitude(jd_sr, swe.MOON)
    sun_lon_sr  = _sidereal_longitude(jd_sr, swe.SUN)

    tithi_sr, paksha_sr, _ = _tithi_and_paksha(moon_lon_sr, sun_lon_sr)
    _, nak_name_sr, _ = _nakshatra(moon_lon_sr)
    _, yoga_name_sr, _ = _yoga(moon_lon_sr, sun_lon_sr)
    rashi_sr = _rashi(moon_lon_sr)

    day = DayPanchanga(
        sunrise_local=sunrise_local, sunset_local=sunset_local,
        tithi_at_sunrise=tithi_sr, paksha_at_sunrise=paksha_sr,
        nakshatra_at_sunrise=nak_name_sr, yoga_at_sunrise=yoga_name_sr,
        rashi_moon_at_sunrise=rashi_sr
    )

    fm_utc = _next_full_moon_utc(dt_utc)
    if fm_utc:
        nak_fm = _nakshatra(_sidereal_longitude(_to_jd_ut(fm_utc), swe.MOON))[1]
        masa = _masa_from_fullmoon_nak(nak_fm)
        fm_local = fm_utc.astimezone(tz)
        fullmoon = FullMoonInfo(dt_utc=fm_utc, dt_local=fm_local,
                                nakshatra_at_fullmoon=nak_fm, masa_from_fullmoon=masa)
    else:
        fullmoon = None

    return {
        "input": {
            "date": date_str, "time": time_str, "timezone": tz_str,
            "latitude": lat, "longitude": lon, "elevation_m": elevation_m
        },
        "instant": {
            "tithi": instant.tithi, "paksha": instant.paksha,
            "nakshatra": instant.nakshatra, "rashi": instant.rashi,
            "yoga": instant.yoga, "karana": instant.karana,
            "moon_lon_sidereal_deg": round(instant.moon_lon_sidereal, 6),
            "sun_lon_sidereal_deg": round(instant.sun_lon_sidereal, 6),
            "local_time": instant.dt_local.isoformat()
        },
        "day_by_sunrise": {
            "sunrise_local": sunrise_local.isoformat(),
            "sunset_local": sunset_local.isoformat(),
            "tithi": day.tithi_at_sunrise, "paksha": day.paksha_at_sunrise,
            "nakshatra": day.nakshatra_at_sunrise, "yoga": day.yoga_at_sunrise,
            "rashi_moon": day.rashi_moon_at_sunrise
        },
        "full_moon": None if not fullmoon else {
            "utc": fullmoon.dt_utc.isoformat(),
            "local": fullmoon.dt_local.isoformat(),
            "nakshatra": fullmoon.nakshatra_at_fullmoon,
            "masa": fullmoon.masa_from_fullmoon
        }
    }