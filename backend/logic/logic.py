import requests, re, numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict

URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

# --- 27 Nakshatras ---
NAKSHATRAS = [
    "Ashwini (अश्विनी)", "Bharani (भरणी)", "Krittika (कृत्तिका)", "Rohini (रोहिणी)",
    "Mrigashira (मृगशीर्ष)", "Ardra (आर्द्रा)", "Punarvasu (पुनर्वसु)", "Pushya (पुष्य)",
    "Ashlesha (आश्लेषा)", "Magha (मघा)", "Purva Phalguni (पूर्व फाल्गुनी)", "Uttara Phalguni (उत्तर फाल्गुनी)",
    "Hasta (हस्त)", "Chitra (चित्रा)", "Swati (स्वाति)", "Vishakha (विशाखा)",
    "Anuradha (अनुराधा)", "Jyeshtha (ज्येष्ठा)", "Mula (मूल)", "Purva Ashadha (पूर्वाषाढा)",
    "Uttara Ashadha (उत्तराषाढा)", "Shravana (श्रवण)", "Dhanishtha (धनिष्ठा)", "Shatabhisha (शतभिषक्)",
    "Purva Bhadrapada (पूर्व भाद्रपदा)", "Uttara Bhadrapada (उत्तर भाद्रपदा)", "Revati (रेवती)"
]

# --- Nakshatra → Masa mapping ---
MASA_MAPPING = {
    "Chitra": "Chaitra", "Vishakha": "Vaishakha", "Jyeshtha": "Jyeshtha", "Mula": "Jyeshtha",
    "Purva Ashadha": "Ashadha", "Uttara Ashadha": "Ashadha", "Shravana": "Shravana",
    "Purva Bhadrapada": "Bhadrapada", "Uttara Bhadrapada": "Bhadrapada",
    "Ashwini": "Ashvina", "Krittika": "Karttika", "Mrigashira": "Margashirsha",
    "Pushya": "Pausha", "Magha": "Magha", "Purva Phalguni": "Phalguna", "Uttara Phalguni": "Phalguna"
}

# --- 12 Rashis ---
RASHIS = [
    ("Mesha (Aries)", 0, 30), ("Vrishabha (Taurus)", 30, 60), ("Mithuna (Gemini)", 60, 90),
    ("Karka (Cancer)", 90, 120), ("Simha (Leo)", 120, 150), ("Kanya (Virgo)", 150, 180),
    ("Tula (Libra)", 180, 210), ("Vrishchika (Scorpio)", 210, 240),
    ("Dhanu (Sagittarius)", 240, 270), ("Makara (Capricorn)", 270, 300),
    ("Kumbha (Aquarius)", 300, 330), ("Meena (Pisces)", 330, 360)
]


# --- Missing constants / helpers (paste near top of file) ---
from dataclasses import dataclass

# Yoga names (27)
YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
    "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti"
]

# Build 60-karana cycle (0..59)
KARANA_REPEATING = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti (Bhadra)"]
def _build_karana_cycle():
    seq = ["Kimstughna"]  # index 0
    for i in range(1, 56):
        seq.append(KARANA_REPEATING[(i-1) % 7])
    seq += ["Shakuni", "Chatushpada", "Naga"]
    seq.append("Kimstughna")
    return seq
KARANAS_60 = _build_karana_cycle()

# Simple Location container used by sunrise/sunset helper
@dataclass(frozen=True)
class Location:
    lat: float
    lon: float
    elevation_m: float = 0.0


# Safe sunrise/sunset wrapper:
# - If you already have a precise _sunrise_sunset (for example the one using Swiss Ephemeris),
#   keep it in the module — this wrapper will attempt to call that exact function first.
# - If not present, we return a sane approximate fallback (06:30 / 18:00 local) so your API doesn't 500.
def _sunrise_sunset(dt_local, loc: Location, tz):
    # If a more precise function exists in this module under the same name, prefer it.
    # (This avoids accidentally overriding your SwissEphemeris version.)
    try:
        # attempt to import the "real" function if defined earlier in same module
        real = globals().get("_sunrise_sunset_real")
        if real and callable(real):
            return real(dt_local, loc, tz)
    except Exception:
        pass

    # Otherwise approximate (non-astronomical). This is intentionally conservative.
    # NOTE: Replace this with your precise Swiss Ephemeris implementation for production accuracy.
    date = dt_local.date()
    sunrise = datetime(date.year, date.month, date.day, 6, 30, tzinfo=tz)
    sunset  = datetime(date.year, date.month, date.day, 18, 0, tzinfo=tz)
    return sunrise, sunset

# If you already have a precise implementation, simply rename it to _sunrise_sunset_real
# at module scope (or assign it) so the wrapper above will call it:
#
#   _sunrise_sunset_real = your_precise_function
#
# Example: if you have a function named sunrise_true(dt_local, loc, tz) -> (sunrise, sunset),
# assign:
#   _sunrise_sunset_real = sunrise_true

# ----------------------------------------------------------
# Horizons API Vector Fetcher
# ----------------------------------------------------------
def get_vectors(command, start, stop, step="'6 h'"):
    # Horizons requires quoted date strings:
    start = f"'{start}'"
    stop  = f"'{stop}'"

    params = {
        "format": "json",
        "COMMAND": command,
        "CENTER": "399",
        "EPHEM_TYPE": "VECTORS",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": step,
        "VEC_TABLE": "3",
        "MAKE_EPHEM": "YES"
    }

    r = requests.get(URL, params=params, timeout=20)
    j = r.json()

    if "result" not in j:
        raise RuntimeError("Horizons error")

    text = j["result"]
    block = re.search(r"\$\$SOE(.*?)\$\$EOE", text, re.S)
    if not block:
        print("\n--- Horizons Returned ---")
        print(text)
        raise RuntimeError("No $$SOE data (Horizons rejected time format)")

    data = block.group(1)
    pattern = re.compile(
        r"(\d{4}-[A-Za-z]{3}-\d{2}\s+\d{2}:\d{2}).*?"
        r"X\s*=\s*([-+0-9.DEe]+).*?"
        r"Y\s*=\s*([-+0-9.DEe]+).*?"
        r"Z\s*=\s*([-+0-9.DEe]+)",
        re.S
    )

    times, vecs = [], []
    for t, x, y, z in pattern.findall(data):
        times.append(datetime.strptime(t.strip(), "%Y-%b-%d %H:%M"))
        vecs.append(np.array([float(x.replace("D","E")),
                              float(y.replace("D","E")),
                              float(z.replace("D","E"))]))
    return times, vecs

# ----------------------------------------------------------
# Math Helpers
# ----------------------------------------------------------
def vector_to_longitude(vec):
    x, y, _ = vec
    lon = np.degrees(np.arctan2(y, x))
    return lon % 360

def lahiri_ayanamsa(date):
    base = datetime(2000, 1, 1)
    yrs = (datetime.strptime(date, "%Y-%m-%d") - base).days / 365.25
    return 23.85675 + yrs * (50.29 / 3600)

def calculate_tithi(m, s):
    diff = (m - s) % 360
    num = np.ceil(diff / 12)
    paksha = "Shukla (Waxing)" if num <= 15 else "Krishna (Waning)"
    return int(num), paksha

def calculate_nakshatra(lon):
    idx = int((lon * 60) // 800) % 27
    return idx+1, NAKSHATRAS[idx]

def calculate_rashi(lon):
    for name, a, b in RASHIS:
        if a <= lon < b: return name
    return "Unknown"

# ----------------------------------------------------------
# Yoga (Horizons-based using sidereal Moon+Sun)
# ----------------------------------------------------------
def calculate_yoga(m_sid, s_sid):
    # Yoga = (Moon + Sun) modulo 360, divided by nakshatra arc (13°20')
    NAK_ARC = 13 + 20/60  # 13°20'
    total = (m_sid + s_sid) % 360
    yoga_float = total / NAK_ARC
    idx = int(yoga_float) % 27
    return idx + 1, YOGAS[idx], yoga_float


# ----------------------------------------------------------
# Karana (Horizons-based using sidereal Moon-Sun)
# ----------------------------------------------------------
def calculate_karana(m_sid, s_sid):
    # Karana = half-tithi = 6°
    KARANA_ARC = 6.0
    diff = (m_sid - s_sid) % 360
    karana_float = diff / KARANA_ARC
    idx = int(karana_float) % 60     # 60-karana repeating cycle
    return KARANAS_60[idx], idx


# ----------------------------------------------------------
# Masa via exact Full Moon Nakshatra
# ----------------------------------------------------------
def determine_masa_from_fullmoon(fullmoon_dt):
    if fullmoon_dt.tzinfo: fullmoon_dt = fullmoon_dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    start = (fullmoon_dt - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
    stop  = (fullmoon_dt + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
    times, vecs = get_vectors("301", start, stop, "'5 m'")

    idx = min(range(len(times)), key=lambda i: abs(times[i] - fullmoon_dt))
    used = times[idx]
    lon = vector_to_longitude(vecs[idx])
    lon_sid = (lon - lahiri_ayanamsa(used.strftime("%Y-%m-%d"))) % 360

    index_of_next_nakshatra, nak = calculate_nakshatra(lon_sid)
    for k in MASA_MAPPING:
        if k in nak: return MASA_MAPPING[k], nak, used
    for k in MASA_MAPPING:
        if k in NAKSHATRAS[index_of_next_nakshatra]: return MASA_MAPPING[k], NAKSHATRAS[index_of_next_nakshatra], used
    return "Unknown", nak, used

# ----------------------------------------------------------
# Full Moon Search
# ----------------------------------------------------------
def find_next_full_moon(date_utc):
    stop = (datetime.strptime(date_utc, "%Y-%m-%d") + timedelta(days=35)).strftime("%Y-%m-%d")
    tm, vm = get_vectors("301", date_utc, stop)
    ts, vs = get_vectors("10", date_utc, stop)

    sep = [(vector_to_longitude(m) - vector_to_longitude(s)) % 360 for m, s in zip(vm, vs)]
    for i in range(1, len(sep)):
        if (sep[i-1] < 180 <= sep[i]) or (sep[i-1] > 180 >= sep[i]):
            f = (180 - sep[i-1]) / (sep[i] - sep[i-1])
            return tm[i-1] + (tm[i]-tm[i-1])*f
    return None

# ----------------------------------------------------------
# ✅ MAIN Panchanga API
# ----------------------------------------------------------
def get_panchanga_nasa(
    date_str: str, time_str: str, tz_str: str,
    lat: float = 17.3850, lon: float = 78.4867, elevation_m: float = 0.0
) -> Dict:
    tz = ZoneInfo(tz_str)
    moment_ist = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    moment_utc = moment_ist.astimezone(ZoneInfo("UTC"))

    date_utc = moment_utc.strftime("%Y-%m-%d")

    # ✅ Define start/stop range for one day
    start = f"{date_utc} 00:00"
    stop  = f"{date_utc} 23:59"

    # Get vectors (moon, sun)
    tm, vm = get_vectors("301", start, stop, step="'1 h'")  # Moon
    ts, vs = get_vectors("10", start, stop, step="'1 h'")   # Sun

    # Pick the sample closest to requested moment
    idx = min(range(len(tm)), key=lambda i: abs(tm[i] - moment_utc.replace(tzinfo=None)))
    moon = vm[idx]
    sun = vs[idx]

    # Compute longitudes (tropical)
    m = vector_to_longitude(moon)
    s = vector_to_longitude(sun)

    # Lahiri ayanamsa correction
    ay = lahiri_ayanamsa(date_utc)
    m_sid, s_sid = (m - ay) % 360, (s - ay) % 360

    # Instant panchanga
    tithi, paksha = calculate_tithi(m_sid, s_sid)
    _, nak = calculate_nakshatra(m_sid)
    rashi = calculate_rashi(m_sid)
    yoga_index, yoga_name, _ = calculate_yoga(m_sid, s_sid)
    karana_name, _ = calculate_karana(m_sid, s_sid)

    # Find full moon and masa
    fm = find_next_full_moon(date_utc)
    if fm:
        masa, fm_nak, used = determine_masa_from_fullmoon(fm)
        fm_ist = fm.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    else:
        masa, fm_nak, used, fm_ist = "Unknown", "Unknown", None, None

    # Day (sunrise/sunset)
    # Optional: you can plug in your previous _sunrise_sunset() function here
    try:
        sunrise_local, sunset_local = _sunrise_sunset(moment_ist, Location(lat, lon, elevation_m), tz)
    except Exception:
        sunrise_local = moment_ist.replace(hour=6, minute=30)
        sunset_local = moment_ist.replace(hour=18, minute=0)

    # Sunrise snapshot (recalculate with sunrise time)
    sunrise_utc = sunrise_local.astimezone(ZoneInfo("UTC"))
    idx_sr = min(range(len(tm)), key=lambda i: abs(tm[i] - sunrise_utc.replace(tzinfo=None)))
    moon_sr = vm[idx_sr]
    sun_sr = vs[idx_sr]
    m_sr = vector_to_longitude(moon_sr)
    s_sr = vector_to_longitude(sun_sr)
    m_sr_sid, s_sr_sid = (m_sr - ay) % 360, (s_sr - ay) % 360
    tithi_sr, paksha_sr = calculate_tithi(m_sr_sid, s_sr_sid)
    _, nak_sr = calculate_nakshatra(m_sr_sid)
    yoga_sr_idx, yoga_sr_name, _ = calculate_yoga(m_sr_sid, s_sr_sid)
    rashi_sr = calculate_rashi(m_sr_sid)

    # Build return dictionary (identical structure to get_panchanga_drik)
    return {
        "input": {
            "date": date_str,
            "time": time_str,
            "timezone": tz_str,
            "latitude": lat,
            "longitude": lon,
            "elevation_m": elevation_m
        },
        "instant": {
            "tithi": tithi,
            "paksha": paksha,
            "nakshatra": nak,
            "rashi": rashi,
            "yoga": yoga_name,
            "karana": karana_name,
            "moon_lon_sidereal_deg": round(m_sid, 6),
            "sun_lon_sidereal_deg": round(s_sid, 6),
            "local_time": moment_ist.isoformat()
        },
        "day_by_sunrise": {
            "sunrise_local": sunrise_local.isoformat(),
            "sunset_local": sunset_local.isoformat(),
            "tithi": tithi_sr,
            "paksha": paksha_sr,
            "nakshatra": nak_sr,
            "yoga": yoga_sr_name,
            "rashi_moon": rashi_sr
        },
        "full_moon": None if not fm else {
            "utc": fm.strftime("%Y-%m-%dT%H:%M:%S"),
            "local": fm_ist.isoformat(),
            "nakshatra": fm_nak,
            "masa": masa
        }
    }
