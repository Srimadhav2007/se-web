# backend/logic/drik/api.py
"""
Public API wrapper for the Drik Panchang engine.

Exports:
- get_core_panchanga
- get_hindu_time
- merge_panchanga
"""

from datetime import timedelta, timezone, datetime
from zoneinfo import ZoneInfo

from .utils import (
    local_to_utc,
    utc_to_jd,
    jd_to_utc,
    fmt_hm,
    norm_deg,
)
from .astro import (
    compute_tithi,
    compute_paksha,
    compute_nakshatra,
    compute_yoga,
    compute_karana,
    compute_rashi,
    _angle_tithi,
    _angle_nak,
    _angle_yoga,
    binary_search_angle,
)
from .times import (
    get_sunrise_sunset,
    compute_muhurthas,
    compute_varjyam,
    compute_amritakalam,
)


# --------------------------------------------------------------
# Helper: compute boundary end-times
# --------------------------------------------------------------

def compute_end_time(jd0, tz_name, func_angle, size_deg):
    """
    Find when an angle crosses (currentAngle + size_deg).
    Search window: jd0 → jd0 + 2 days.
    """
    tz = ZoneInfo(tz_name)

    start_jd = jd0
    end_jd = jd0 + 2  # 48 hours search window

    current_angle = func_angle(jd0)
    target_angle = norm_deg(current_angle + size_deg)

    out_jd = binary_search_angle(func_angle, start_jd, end_jd, target_angle)
    if out_jd is None:
        return None

    return jd_to_utc(out_jd).astimezone(tz).isoformat()


# --------------------------------------------------------------
# MAIN: Core Panchanga
# --------------------------------------------------------------

def get_core_panchanga(date_str, time_str, tz_name, lat, lon, elev):
    """
    Compute the full Drik Panchang core set:
    - tithi + end time
    - nakshatra + end time
    - yoga + end time
    - karana + end time
    - sunrise, sunset
    - muhurthas
    - rashi
    - varjyam
    - amritakalam
    """

    tz = ZoneInfo(tz_name)

    # Convert request to local+UTC
    dt_local, dt_utc = local_to_utc(date_str, time_str, tz_name)
    jd_now = utc_to_jd(dt_utc)

    # Sunrise & sunset for the local date
    sunrise_local, sunset_local = get_sunrise_sunset(dt_local, tz_name, lat, lon, elev)

    # -- Instant values --
    tithi = compute_tithi(jd_now)
    paksha = compute_paksha(tithi)
    nak_idx, nak_name = compute_nakshatra(jd_now)
    yoga_idx, yoga_name = compute_yoga(jd_now)
    karana = compute_karana(jd_now)
    rashi = compute_rashi(jd_now)

    # ----------------------------------------------------------
    # END TIMES (adding degree size for each segment)
    # ----------------------------------------------------------

    # tithi end = 12°
    tithi_end = compute_end_time(jd_now, tz_name, _angle_tithi, 12)

    # nakshatra end = 13°20' = 13.333333°
    nak_end = compute_end_time(jd_now, tz_name, _angle_nak, 13 + (1/3))

    # yoga end = 13°20’
    yoga_end = compute_end_time(jd_now, tz_name, _angle_yoga, 13 + (1/3))

    # karana end = 6°
    karana_end = compute_end_time(jd_now, tz_name, _angle_tithi, 6)

    # ----------------------------------------------------------
    # Muhurthas
    # ----------------------------------------------------------
    muhurthas = compute_muhurthas(sunrise_local, sunset_local, tz_name)

    # ----------------------------------------------------------
    # Varjyam / Amritakalam
    # ----------------------------------------------------------
    varjyam = compute_varjyam(dt_local, tz_name)
    amritakalam = compute_amritakalam(varjyam)

    # ----------------------------------------------------------
    # PACKAGE ALL RESULTS
    # ----------------------------------------------------------
    core = {
        "instant": {
            "tithi": tithi,
            "paksha": paksha,
            "nakshatra": nak_name,
            "nakshatra_idx": nak_idx,
            "yoga": yoga_name,
            "yoga_idx": yoga_idx,
            "karana": karana,
            "rashi": rashi,
        },
        "day_by_sunrise": {
            "sunrise_local": sunrise_local.isoformat(),
            "sunset_local": sunset_local.isoformat(),
        },
        "end_times": {
            "tithi_end": tithi_end,
            "nak_end": nak_end,
            "yoga_end": yoga_end,
            "karana_end": karana_end,
        },
        "muhurthas": muhurthas,
        "varjyam": varjyam,
        "amritakalam": amritakalam,
    }

    return core


# --------------------------------------------------------------
# HINDU TIME
# --------------------------------------------------------------

def get_hindu_time(date_str, time_str, tz_name, core):
    """
    Compute:
    - Ghaṭi
    - Vināḍi
    - Prāṇa
    since today's sunrise
    """

    tz = ZoneInfo(tz_name)

    sunrise_iso = core["day_by_sunrise"]["sunrise_local"]
    sunrise_dt = datetime.fromisoformat(sunrise_iso)

    dt_local, _ = local_to_utc(date_str, time_str, tz_name)

    diff = (dt_local - sunrise_dt).total_seconds()
    day_sec = 24 * 3600
    if diff < 0:
        diff = (diff + day_sec) % day_sec

    # Hindu time components
    SEC_PRANA = 4
    SEC_VINADI = 24
    SEC_GHATI = 24 * 60

    s = int(diff)

    prana = s // SEC_PRANA
    vinadi = s // SEC_VINADI
    ghati_count = (s // SEC_GHATI) % 60

    gh_rem = s % SEC_GHATI
    gh_h = gh_rem // 3600
    gh_m = (gh_rem % 3600) // 60
    gh_s = gh_rem % 60

    muhurta_count = (s // (48*60)) % 30

    return {
        "seconds_since_sunrise": s,
        "ghaTi": {
            "count": ghati_count,
            "in_ghaTi_str": f"{gh_h:02d}:{gh_m:02d}:{gh_s:02d}"
        },
        "vinadi": {
            "total": vinadi,
            "in_current_ghaTi": gh_rem // SEC_VINADI,
        },
        "prana": {
            "total": prana,
            "in_current_ghaTi": gh_rem // SEC_PRANA,
        },
        "muhurta": {
            "count": muhurta_count,
        },
        "now_local_iso": dt_local.isoformat(),
    }


# --------------------------------------------------------------
# FINAL MERGE
# --------------------------------------------------------------

def merge_panchanga(core, hindu):
    out = {}
    out.update(core)
    out["hindu_time"] = hindu
    return out
