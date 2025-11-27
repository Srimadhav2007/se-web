# backend/logic/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from . import drik

DEFAULT_TZ = "Asia/Kolkata"
DEFAULT_LAT = 13.6288
DEFAULT_LON = 79.4192
DEFAULT_ELEV = 0.0

@require_GET
def get_panchangam(request):
    date = request.GET.get("date")
    time = request.GET.get("time")
    tz = request.GET.get("timezone", DEFAULT_TZ)
    try:
        lat = float(request.GET.get("lat", DEFAULT_LAT))
    except (TypeError, ValueError):
        lat = DEFAULT_LAT
    try:
        lon = float(request.GET.get("lon", DEFAULT_LON))
    except (TypeError, ValueError):
        lon = DEFAULT_LON
    try:
        elev = float(request.GET.get("elev", DEFAULT_ELEV))
    except (TypeError, ValueError):
        elev = DEFAULT_ELEV

    if not (date and time):
        return JsonResponse({"error": "Missing required parameters: date and time"}, status=400)

    # Strictly call drik (Skyfield only)
    core = drik.get_core_panchanga(date, time, tz, lat, lon, elev)
    hindu = core["hindu_time"]

    return JsonResponse(core, safe=False)

from django.http import JsonResponse
from . import drik

def get_panchangam(request):
    date = request.GET.get("date")
    time = request.GET.get("time")
    tz = request.GET.get("timezone")
    lat = float(request.GET.get("lat"))
    lon = float(request.GET.get("lon"))
    elev = float(request.GET.get("elev"))

    core = drik.get_core_panchanga(date, time, tz, lat, lon, elev)

    # hindu_time is already inside core, so no need to recompute
    # old line removed:
    # hindu = drik.get_hindu_time(date, time, tz, core)

    return JsonResponse(core, safe=False)
