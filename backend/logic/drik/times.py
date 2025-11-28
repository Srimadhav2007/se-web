# backend/logic/drik/times.py
"""
Windows-compatible Swiss Ephemeris rise_trans() implementation.
Drik Panchang accurate sunrise, sunset, Rahukalam, Yamagandam,
Gulika, Abhijit, Varjyam, Amritakalam.
"""

import swisseph as swe
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .utils import (
    utc_to_jd,
    jd_to_utc,
    fmt_hm,
)
from .astro import (
    sidereal_moon_longitude,
    NAKSHATRAS
)

# ------------------------------------------------------------
# 1) Sunrise/Sunset using OLD Windows-style signature
# ------------------------------------------------------------

def get_sunrise_sunset(date_local, tz_name, lat, lon, elev):
    tz = ZoneInfo(tz_name)

    # Local midnight → UTC → JD
    dt_mid_local = date_local.replace(hour=0, minute=0, second=0, microsecond=0)
    dt_mid_utc = dt_mid_local.astimezone(timezone.utc)
    jd_mid = utc_to_jd(dt_mid_utc)

    # geopos = (longitude, latitude, altitude)
    geopos = (float(lon), float(lat), float(elev))

    # Sunrise
    rs = swe.rise_trans(
        jd_mid,
        swe.SUN,
        swe.CALC_RISE | swe.BIT_DISC_CENTER,  # <-- event flags MUST be 3rd argument
        geopos
    )
    sunrise_utc = jd_to_utc(rs[1][0])

    # Sunset
    ss = swe.rise_trans(
        jd_mid,
        swe.SUN,
        swe.CALC_SET | swe.BIT_DISC_CENTER,   # <-- event flags
        geopos
    )
    sunset_utc = jd_to_utc(ss[1][0])

    # Convert UTC → local
    return sunrise_utc.astimezone(tz), sunset_utc.astimezone(tz)




# ------------------------------------------------------------
# 2) Drik Panchang daytime segment → Rahu/Yama/Gulika
# ------------------------------------------------------------

RAHU_SLOTS = {0:8,1:2,2:7,3:5,4:6,5:4,6:3}
YAMA_SLOTS = {
    0: 5,  # Sunday
    1: 1,
    2: 3,
    3: 4,
    4: 6,
    5: 7,
    6: 2
}
GULIKA_SLOTS = {0:7,1:6,2:5,3:4,4:3,5:2,6:1}

# ...existing code...
def compute_muhurthas(sunrise_local, sunset_local, tz_name):
    tz = ZoneInfo(tz_name)

    day_seconds = (sunset_local - sunrise_local).total_seconds()
    part = day_seconds / 8

    slots = []
    for i in range(8):
        s = sunrise_local + timedelta(seconds=part * i)
        e = sunrise_local + timedelta(seconds=part * (i + 1))
        slots.append((s, e))

    weekday = sunrise_local.weekday()
    sunday = (weekday + 1) % 7

    def wrap_slot(slot):
        s, e = slot

        def round_min(dt):
            # round seconds to nearest minute
            if dt is None:
                return "—"
            seconds = dt.second + dt.microsecond / 1_000_000
            if seconds >= 30:
                dt = dt + timedelta(seconds=(60 - seconds))
            dt = dt.replace(second=0, microsecond=0)
            return fmt_hm(dt)

        disp = f"{round_min(s)}-{round_min(e)}"
        if s.date() != e.date():
            disp += "+"
        return {
            "start_iso": s.isoformat(),
            "end_iso": e.isoformat(),
            "display": disp,
            "ends_next_day": s.date() != e.date()
        }

    # Brahma Muhurta: sunrise - 96 min to sunrise - 48 min
    bm_start = sunrise_local - timedelta(minutes=96)
    bm_end = sunrise_local - timedelta(minutes=48)

    # Abhijit: midday ± 24 min
    midday = sunrise_local + (sunset_local - sunrise_local) / 2
    abh_start = midday - timedelta(minutes=24)
    abh_end = midday + timedelta(minutes=24)

    return {
        "rahukalam": wrap_slot(slots[RAHU_SLOTS[sunday] - 1]),
        "yamaganda": wrap_slot(slots[YAMA_SLOTS[sunday] - 1]),
        "gulika": wrap_slot(slots[GULIKA_SLOTS[sunday] - 1]),
        "brahma_muhurta": wrap_slot((bm_start, bm_end)),
        "abhijit_muhurta": wrap_slot((abh_start, abh_end)),
        "day_slots": [wrap_slot(slot) for slot in slots]
    }
# ...existing code...



# ------------------------------------------------------------
# 3) Varjyam: Moon pada-based timing scan
# ------------------------------------------------------------

VARJYAM_PADAS = [
    ("Ashlesha", 4),
    ("Mula", 2),
    ("Revati", 4),
]

def compute_varjyam(date_local, tz_name):
    tz = ZoneInfo(tz_name)

    # Search window: today 00:00 local → +48 hours
    start_local = date_local.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = start_local.astimezone(timezone.utc)
    jd0 = utc_to_jd(start_utc)
    jd1 = jd0 + 2  # 48h

    step = 2 / (24*60)  # 2 minutes in days

    prev = None
    periods = []
    start = None

    jd = jd0
    while jd <= jd1:
        moon = sidereal_moon_longitude(jd)
        nk_index = int((moon * 60) // 800)
        pada = int(((moon * 60) % 800) // 200) + 1
        nk_name = NAKSHATRAS[nk_index]

        is_v = False
        for name,p in VARJYAM_PADAS:
            if nk_name == name and p == pada:
                is_v = True
                break

        if prev is None:
            prev = is_v
        else:
            if prev is False and is_v is True:
                start = jd_to_utc(jd).astimezone(tz)
            elif prev is True and is_v is False:
                end = jd_to_utc(jd).astimezone(tz)
                periods.append((start, end))
        prev = is_v
        jd += step

    out = []
    for s,e in periods:
        disp = f"{fmt_hm(s)}-{fmt_hm(e)}"
        if s.date() != e.date():
            disp += "+"
        out.append({
            "start_iso": s.isoformat(),
            "end_iso": e.isoformat(),
            "display": disp,
            "ends_next_day": s.date() != e.date()
        })

    return out



# ------------------------------------------------------------
# 4) Amritakalam → same as Varjyam (Drik rule simplified)
# ------------------------------------------------------------

def compute_amritakalam(varjyam):
    return varjyam
