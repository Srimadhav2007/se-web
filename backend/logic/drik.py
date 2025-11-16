# backend/logic/drik.py
"""
Skyfield-only Panchang implementation (strict).
Requires: backend/logic/ephemeris/de421.bsp present.

Public API (used by views.py):
- get_core_panchanga(date_str, time_str, tz_name, lat, lon, elev)
- get_hindu_time(date_str, time_str, tz_name, core)
- merge_panchanga(core, hindu)
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import math

# --- Skyfield imports ---
from skyfield.api import Loader, wgs84
from skyfield import almanac

# locate local ephemeris directory relative to this file
THIS_DIR = Path(__file__).resolve().parent
EPH_DIR = THIS_DIR / "ephemeris"
EHP_FILENAME = "de421.bsp"
EPH_PATH = EPH_DIR / EHP_FILENAME

if not EPH_PATH.exists():
    raise FileNotFoundError(
        f"Required ephemeris file not found: {EPH_PATH}\n"
        f"Please run: python {THIS_DIR / 'download_ephemeris.py'}\n"
        "or download de421.bsp into this folder."
    )

# Use Loader pointed at local ephemeris folder (no network access required)
load = Loader(str(EPH_DIR))
Eph = load(EHP_FILENAME)
TS = load.timescale()
EARTH = Eph['earth']
SUN = Eph['sun']
MOON = Eph['moon']


# Standard names
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

# 12 rashis
RASHIS = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"
]

# 11 karanas (simple cycle mapping)
KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija",
    "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

# 27 yoga names (for human readable label)
YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarman", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]


# -----------------------
# Utility helpers
# -----------------------
def _normalize_angle_deg(x):
    a = float(x) % 360.0
    if a < 0:
        a += 360.0
    return a

def _ecliptic_longitude(body, t_sf):
    # returns ecliptic longitude in degrees using Skyfield ecliptic_latlon
    astrometric = EARTH.at(t_sf).observe(body).apparent()
    latlon = astrometric.ecliptic_latlon()
    lon = latlon[1].degrees
    return _normalize_angle_deg(lon)


# -----------------------
# Panchang primitives
# -----------------------
def _tithi_from_longitudes(sun_lon, moon_lon):
    diff = _normalize_angle_deg(moon_lon - sun_lon)
    return int(math.floor(diff / 12.0)) + 1  # 1..30

def _paksha_from_tithi(tithi):
    return "Shukla" if tithi <= 15 else "Krishna"

def _nakshatra_from_moon(moon_lon):
    idx = int(math.floor(moon_lon / (360.0 / 27.0)))
    if idx < 0: idx = 0
    if idx >= 27: idx = 26
    return idx + 1, NAKSHATRAS[idx]  # (index, name)

def _yoga_from_sun_moon(sun_lon, moon_lon):
    s = _normalize_angle_deg(sun_lon + moon_lon)
    idx = int(math.floor(s / (360.0 / 27.0)))
    # idx in 0..26 -> yoga index 1..27
    return idx + 1

def _karana_from_longitudes(sun_lon, moon_lon):
    diff = _normalize_angle_deg(moon_lon - sun_lon)
    half_tithi_idx = int(math.floor(diff / 6.0))  # 0..59
    return KARANAS[half_tithi_idx % 11]

def _rashi_from_moon(moon_lon):
    idx = int(math.floor(moon_lon / 30.0))
    if idx < 0: idx = 0
    if idx >= 12: idx = 11
    return RASHIS[idx]


# -----------------------
# Sunrise / sunset using skyfield almanac
# -----------------------
def _sunrise_sunset_local(date_local: datetime, tz_name: str, lat: float, lon: float, elev_m: float):
    tz = ZoneInfo(tz_name)
    observer = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elev_m)

    local_midnight = date_local.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = local_midnight.astimezone(timezone.utc) - timedelta(days=1)
    end_utc = local_midnight.astimezone(timezone.utc) + timedelta(days=2)

    t0 = TS.from_datetime(start_utc)
    t1 = TS.from_datetime(end_utc)

    f = almanac.sunrise_sunset(Eph, observer)
    times, events = almanac.find_discrete(t0, t1, f)

    sunrise_dt = None
    sunset_dt = None
    for ti, ev in zip(times, events):
        dt_utc = ti.utc_datetime().replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone(tz)
        if dt_local.date() == local_midnight.date():
            if ev == 1 and sunrise_dt is None:
                sunrise_dt = dt_local
            elif ev == 0 and sunset_dt is None:
                sunset_dt = dt_local

    if sunrise_dt is None:
        sunrise_dt = local_midnight.replace(hour=6, minute=30, tzinfo=tz)
    if sunset_dt is None:
        sunset_dt = local_midnight.replace(hour=18, minute=30, tzinfo=tz)

    return sunrise_dt, sunset_dt


# -----------------------
# Next full moon using skyfield
# -----------------------
def _next_full_moon_local(from_dt_utc):
    t0 = TS.from_datetime(from_dt_utc)
    t1 = TS.from_datetime(from_dt_utc + timedelta(days=40))
    times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(Eph))
    for ti, ph in zip(times, phases):
        if ph == 2:  # full moon
            return ti.utc_datetime().replace(tzinfo=timezone.utc)
    return (from_dt_utc + timedelta(days=15)).replace(tzinfo=timezone.utc)


# -----------------------
# Public functions (Option C)
# -----------------------
def get_core_panchanga(date_str, time_str, tz_name, lat, lon, elev):
    tz = ZoneInfo(tz_name)

    # parse local datetime
    dt_local = datetime.fromisoformat(f"{date_str}T{time_str}")
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=tz)
    dt_utc = dt_local.astimezone(timezone.utc)

    ts = TS.from_datetime(dt_utc)

    sun_lon = _ecliptic_longitude(SUN, ts)
    moon_lon = _ecliptic_longitude(MOON, ts)

    tithi = _tithi_from_longitudes(sun_lon, moon_lon)
    paksha = _paksha_from_tithi(tithi)
    nak_idx, nak_name = _nakshatra_from_moon(moon_lon)
    yoga_idx = _yoga_from_sun_moon(sun_lon, moon_lon)
    karana = _karana_from_longitudes(sun_lon, moon_lon)
    rashi = _rashi_from_moon(moon_lon)

    # sunrise & sunset local
    sunrise_dt_local, sunset_dt_local = _sunrise_sunset_local(dt_local, tz_name, lat, lon, elev)

    # next full moon (UTC then to local)
    next_fm_utc = _next_full_moon_local(dt_utc)
    next_fm_local = next_fm_utc.astimezone(tz)

    # compute values at sunrise
    t_sr = TS.from_datetime(sunrise_dt_local.astimezone(timezone.utc))
    sun_lon_sr = _ecliptic_longitude(SUN, t_sr)
    moon_lon_sr = _ecliptic_longitude(MOON, t_sr)
    tithi_sr = _tithi_from_longitudes(sun_lon_sr, moon_lon_sr)
    paksha_sr = _paksha_from_tithi(tithi_sr)
    nak_idx_sr, nak_name_sr = _nakshatra_from_moon(moon_lon_sr)
    yoga_sr_idx = _yoga_from_sun_moon(sun_lon_sr, moon_lon_sr)
    rashi_sr = _rashi_from_moon(moon_lon_sr)

    # full moon nakshatra & masa (sidereal solar month mapping)
    t_fm = TS.from_datetime(next_fm_utc)
    moon_lon_fm = _ecliptic_longitude(MOON, t_fm)
    sun_lon_fm = _ecliptic_longitude(SUN, t_fm)
    nak_idx_fm, nak_name_fm = _nakshatra_from_moon(moon_lon_fm)
    solar_month_idx = int(math.floor(sun_lon_fm / 30.0)) % 12
    masa_names = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
                  "Ashwin", "Kartika", "Margashirsha", "Pausa", "Magha", "Phalguna"]
    masa_name = masa_names[solar_month_idx]

    # --- Merge formatted fields as requested ---
    # Nakshatra merged as "Name (index)"
    merged_nak = f"{nak_name} ({nak_idx})"
    merged_nak_sr = f"{nak_name_sr} ({nak_idx_sr})"
    merged_nak_fm = f"{nak_name_fm} ({nak_idx_fm})"

    # Yoga: compute name from index and merge as "YogaName (index)"
    # yoga_idx is 1..27 -> map to YOGA_NAMES list (0-index)
    try:
        yoga_name = YOGA_NAMES[yoga_idx - 1]
    except Exception:
        yoga_name = f"Yoga{yoga_idx}"
    merged_yoga = f"{yoga_name} ({yoga_idx})"

    try:
        yoga_sr_name = YOGA_NAMES[yoga_sr_idx - 1]
    except Exception:
        yoga_sr_name = f"Yoga{yoga_sr_idx}"
    merged_yoga_sr = f"{yoga_sr_name} ({yoga_sr_idx})"

    core = {
        "instant": {
            "tithi": tithi,
            "paksha": paksha,
            "nakshatra": merged_nak,           # merged string
            "nakshatra_index": None,          # deprecated but kept for backward compatibility (null)
            "rashi": rashi,
            "yoga": merged_yoga,              # merged yoga string
            "karana": karana
        },
        "day_by_sunrise": {
            "sunrise_local": sunrise_dt_local.isoformat(),
            "sunset_local": sunset_dt_local.isoformat(),
            "tithi": tithi_sr,
            "paksha": paksha_sr,
            "nakshatra": merged_nak_sr,       # merged string
            "yoga": merged_yoga_sr,           # merged yoga string
            "rashi_moon": rashi_sr
        },
        "full_moon": {
            "utc": next_fm_utc.isoformat(),
            "local": next_fm_local.isoformat(),
            "nakshatra": merged_nak_fm,       # merged string
            "masa": masa_name
        }
    }

    return core


def get_hindu_time(date_str, time_str, tz_name, core):
    tz = ZoneInfo(tz_name)

    sr_iso = core.get("day_by_sunrise", {}).get("sunrise_local")
    if sr_iso:
        try:
            sunrise = datetime.fromisoformat(sr_iso)
            if sunrise.tzinfo is None:
                sunrise = sunrise.replace(tzinfo=tz)
        except Exception:
            sunrise = datetime.fromisoformat(sr_iso).replace(tzinfo=tz)
    else:
        dt_local = datetime.fromisoformat(f"{date_str}T{time_str}")
        if dt_local.tzinfo is None:
            dt_local = dt_local.replace(tzinfo=tz)
        sunrise = dt_local.replace(hour=6, minute=30, second=0, microsecond=0)

    now_local = datetime.now(tz)
    diff = (now_local - sunrise).total_seconds()
    if diff < 0:
        diff += 24 * 3600

    SEC_PRANA = 4
    SEC_VINADI = 24
    SEC_GHATI = 24 * 60
    SEC_MUHURTA = 48 * 60

    total_pranas = int(diff // SEC_PRANA)
    total_vinadis = int(diff // SEC_VINADI)

    ghaTi_count = int((diff // SEC_GHATI) % 60)
    ghaTi_remainder = int(diff % SEC_GHATI)

    ghaTi_h = ghaTi_remainder // 3600
    ghaTi_m = (ghaTi_remainder % 3600) // 60
    ghaTi_s = ghaTi_remainder % 60

    muhr_count = int((diff // SEC_MUHURTA) % 30)
    muh_rem = int(diff % SEC_MUHURTA)
    muh_h = muh_rem // 3600
    muh_m = (muh_rem % 3600) // 60
    muh_s = muh_rem % 60

    vinadi_in_ghati = ghaTi_remainder // SEC_VINADI
    prana_in_ghati = ghaTi_remainder // SEC_PRANA

    def hhmmss(h, m, s):
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

    return {
        "now_local_iso": now_local.isoformat(),
        "sunrise_local_iso": sunrise.isoformat(),
        "seconds_since_sunrise": int(diff),
        "total_pranas_since_sunrise": total_pranas,
        "total_vinadis_since_sunrise": total_vinadis,
        "ghaTi": {
            "count": ghaTi_count,
            "in_ghaTi_str": hhmmss(ghaTi_h, ghaTi_m, ghaTi_s)
        },
        "muhurta": {
            "count": muhr_count,
            "in_muhurta_str": hhmmss(muh_h, muh_m, muh_s)
        },
        "vinadi": {"in_current_ghaTi": int(vinadi_in_ghati)},
        "prana": {"in_current_ghaTi": int(prana_in_ghati)}
    }


def merge_panchanga(core, hindu):
    core.setdefault("hindu_time", {})
    core["hindu_time"].update(hindu)
    return core
