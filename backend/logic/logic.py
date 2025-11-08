import requests, re, numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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
def get_panchanga(date_str, time_str, tz_str):
    tz = ZoneInfo(tz_str)
    moment_ist = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    moment_utc = moment_ist.astimezone(ZoneInfo("UTC"))

    date_utc = moment_utc.strftime("%Y-%m-%d")
    # ✅ Make sure we request a valid window
    start = f"{date_utc} 00:00"
    stop  = f"{date_utc} 23:59"
    tm, vm = get_vectors("301", start, stop, step="'1 h'")
    ts, vs = get_vectors("10", start, stop, step="'1 h'")
    # pick the sample closest to requested moment
    idx = min(range(len(tm)), key=lambda i: abs(tm[i] - moment_utc.replace(tzinfo=None)))
    moon = vm[idx]
    sun = vs[idx]


    m = vector_to_longitude(moon)
    s = vector_to_longitude(sun)
    ay = lahiri_ayanamsa(date_utc)
    m_sid, s_sid = (m-ay)%360, (s-ay)%360

    tithi, paksha = calculate_tithi(m_sid, s_sid)
    _, nak = calculate_nakshatra(m_sid)
    rashi = calculate_rashi(m_sid)

    fm = find_next_full_moon(date_utc)
    if fm:
        masa, fm_nak, used = determine_masa_from_fullmoon(fm)
        fm_ist = fm.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    else:
        masa, fm_nak, used, fm_ist = "Unknown", "Unknown", None, None

    return {
        "date": date_str,
        "time": time_str,
        "timezone": tz_str,
        "tithi": tithi,
        "paksha": paksha,
        "nakshatra": nak,
        "rashi": rashi,
        "masa": masa,
        "full_moon_utc": fm.strftime("%Y-%m-%d %H:%M:%S") if fm else None,
        "full_moon_ist": fm_ist.strftime("%Y-%m-%d %H:%M:%S") if fm else None,
        "fullmoon_nakshatra": fm_nak
    }
