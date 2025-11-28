import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo

from .utils import (
    utc_to_jd,
    jd_to_utc,
    local_to_utc,
    norm_deg,
)

from .astro import (
    sidereal_sun_longitude,
    sidereal_moon_longitude,
    tropical_sun_longitude,
    compute_tithi,
    compute_paksha,
    compute_nakshatra,
    compute_yoga,
    compute_karana,
    compute_rashi,
    compute_masa,
    nakshatra_for_jd,
    find_next_full_moon,
)

from .times import (
    get_sunrise_sunset,
    compute_muhurthas,
    compute_varjyam,
    compute_amritakalam,
)


# ----------------------------------------------------------
# Angle differences for end-time finding
# ----------------------------------------------------------

def _angle_tithi(jd_ut):
    """Sun–Moon (sidereal) difference for Tithi."""
    sun = sidereal_sun_longitude(jd_ut)
    moon = sidereal_moon_longitude(jd_ut)
    return norm_deg(moon - sun)


def _angle_nak(jd_ut):
    """Moon’s sidereal longitude."""
    return sidereal_moon_longitude(jd_ut)


def _angle_yoga(jd_ut):
    """Sun + Moon (tropical + sidereal) used by your earlier logic."""
    sun = tropical_sun_longitude(jd_ut)
    moon = sidereal_moon_longitude(jd_ut)
    return norm_deg(sun + moon)


# ----------------------------------------------------------
# END TIME COMPUTATION (general)
# ----------------------------------------------------------

def compute_end_time(jd_now, tz_name, angle_func, span_deg):
    """
    Generic end-time finder:
    Find next moment when angle increases by span_deg.
    """

    tz = ZoneInfo(tz_name)
    start_angle = angle_func(jd_now)
    target_angle = norm_deg(start_angle + span_deg)

    step = 1.0 / 24.0  # coarse: 1 hour
    prev = angle_func(jd_now)
    jd = jd_now

    # Coarse scan
    for _ in range(200):
        jd += step
        ang = angle_func(jd)
        if norm_deg(ang - target_angle) < 3:  # close enough
            break
        prev = ang

    # Refine with binary search
    lo = jd - step
    hi = jd
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        ang_mid = angle_func(mid)

        # check if mid crossed target_angle
        if norm_deg(ang_mid - target_angle) < norm_deg(prev - target_angle):
            hi = mid
        else:
            lo = mid

    final_jd = 0.5 * (lo + hi)
    dt = jd_to_utc(final_jd).astimezone(tz)
    return dt.isoformat()


# ----------------------------------------------------------
# HINDU TIME (unchanged)
# ----------------------------------------------------------

def get_hindu_time(date_str, time_str, tz_name, core):
    tz = ZoneInfo(tz_name)
    sunrise_iso = core["day"]["sunrise"]
    sunrise_dt = datetime.fromisoformat(sunrise_iso)

    dt_local, _ = local_to_utc(date_str, time_str, tz_name)

    diff = (dt_local - sunrise_dt).total_seconds()
    if diff < 0:
        diff += 24 * 3600

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

    muhurta_count = (s // (48 * 60)) % 30

    return {
        "seconds_since_sunrise": s,
        "sunrise_local_iso": sunrise_dt.isoformat(),
        "ghaTi": {
            "count": ghati_count,
            "in_ghaTi_str": f"{gh_h:02d}:{gh_m:02d}:{gh_s:02d}"
        },
        "vinadi": {
            "total": vinadi,
            "in_current_ghaTi": gh_rem // SEC_VINADI
        },
        "prana": {
            "total": prana,
            "in_current_ghaTi": gh_rem // SEC_PRANA
        },
        "muhurta": {
            "count": muhurta_count
        },
        "now_local_iso": dt_local.isoformat(),
    }


# ----------------------------------------------------------
# MAIN PANCHANGA FUNCTION
# ----------------------------------------------------------

def get_core_panchanga(date_str, time_str, tz_name, lat, lon, elev):
    tz = ZoneInfo(tz_name)

    # Convert input
    dt_local, dt_utc = local_to_utc(date_str, time_str, tz_name)
    jd_now = utc_to_jd(dt_utc)

    # Sunrise/Sunset
    sunrise_local, sunset_local = get_sunrise_sunset(dt_local, tz_name, lat, lon, elev)

    # Instant Panchanga
    tithi = compute_tithi(jd_now)
    paksha = compute_paksha(tithi)
    nak_idx, nak_name = compute_nakshatra(jd_now)
    yoga_idx, yoga_name = compute_yoga(jd_now)
    karana = compute_karana(jd_now)
    rashi = compute_rashi(jd_now)

    # Masa for today's date
    masa_today, masa_today_idx = compute_masa(jd_now)

    # END TIMES
    tithi_end = compute_end_time(jd_now, tz_name, _angle_tithi, 12)
    nak_end = compute_end_time(jd_now, tz_name, _angle_nak, 13 + 1/3)
    yoga_end = compute_end_time(jd_now, tz_name, _angle_yoga, 13 + 1/3)
    karana_end = compute_end_time(jd_now, tz_name, _angle_tithi, 6)

    # Muhurthas
    muhurthas = compute_muhurthas(sunrise_local, sunset_local, tz_name)

    # Varjyam / Amritakalam
    varjyam = compute_varjyam(dt_local, tz_name)
    amritakalam = compute_amritakalam(varjyam)

    # NEXT FULL MOON (accurate)
    next_full_jd = find_next_full_moon(jd_now)
    if next_full_jd:
        next_full_local = jd_to_utc(next_full_jd).astimezone(ZoneInfo(tz_name))
        # Human-friendly format (Option A)
        next_full_local_readable = next_full_local.strftime("%d %b %Y, %I:%M %p")
    else:
        next_full_local_readable = None

    masa, masa_idx = compute_masa(next_full_jd)
    fullmoon_nakshatra_name, nk_full_idx = nakshatra_for_jd(next_full_jd)


    masa_full, masa_full_idx = compute_masa(next_full_jd)
    nk_full, nk_full_idx = nakshatra_for_jd(next_full_jd)

    # Diagnostics
    diagnostics = {
        "sun_tropical_deg": tropical_sun_longitude(jd_now),
        "moon_sidereal_deg": sidereal_moon_longitude(jd_now),
        "sum_deg_for_yoga": norm_deg(
            tropical_sun_longitude(jd_now) + sidereal_moon_longitude(jd_now)
        )
    }

    # PACKAGE OUTPUT
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
            "masa": masa_today,
            "masa_idx": masa_today_idx
        },

        "day": {
            "sunrise": sunrise_local.isoformat(),
            "sunset": sunset_local.isoformat(),
            "tithi": tithi,
            "paksha": paksha,
            "nakshatra": nak_name,
            "nakshatra_idx": nak_idx,
            "yoga": yoga_name,
            "yoga_idx": yoga_idx,
            "rashi": rashi
        },

        "events": {
            "tithi_end": tithi_end,
            "nakshatra_end": nak_end,
            "yoga_end": yoga_end,
            "karana_end": karana_end,
            "next_full_moon": next_full_local_readable,
            "masa": masa,                     # must exist
            "masa_idx": masa_idx,             # optional
            "full_moon_nakshatra": fullmoon_nakshatra_name  # must exist
        },


        "periods": {
            "rahukalam": muhurthas["rahukalam"],
            "yamaganda": muhurthas["yamaganda"],
            "gulika": muhurthas["gulika"],
            "brahma_muhurta": muhurthas["brahma_muhurta"],
            "abhijit_muhurta": muhurthas["abhijit_muhurta"],
            "day_slots": muhurthas["day_slots"],
            "varjyam": varjyam,
            "amritakalam": amritakalam
        },

        "diagnostics": diagnostics,

        "input": {
            "requested_date": date_str,
            "requested_time": time_str,
            "timezone": tz_name,
            "latitude": float(lat),
            "longitude": float(lon),
            "elevation_m": float(elev),
            "engine_used": "drik_skyfield"
        },
    }

    return core


# ----------------------------------------------------------
# MERGE PANCHANGA
# ----------------------------------------------------------

def merge_panchanga(core, hindu):
    out = {}
    out.update(core)
    out["hindu_time"] = hindu
    return out
