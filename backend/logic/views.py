from django.http import JsonResponse
from . import logic
from .drik import get_panchanga_drik

"""def get_panchangam(request):
    date = request.GET.get('date')
    time = request.GET.get('time')
    timezone = request.GET.get('timezone')
    if not all([date, time, timezone]):
        return JsonResponse({'error': 'Missing required parameters: date, time, or timezone'}, status=400)
    result = logic.get_panchanga(date, time, timezone)
    return JsonResponse(result)"""

def get_panchangam(request):
    date = request.GET.get("date")       # "2025-11-14"
    time = request.GET.get("time")       # "10:30"
    tz   = request.GET.get("timezone")   # "Asia/Kolkata"
    # you MUST provide coordinates (Drik is location-based)
    lat  = float(request.GET.get("lat", "17.3850"))   # Hyderabad default
    lon  = float(request.GET.get("lon", "78.4867"))
    elev = float(request.GET.get("elev", "0"))

    data = get_panchanga_drik(date, time, tz, lat, lon, elev)
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})