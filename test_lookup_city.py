import datetime as dt
from timezonefinder import TimezoneFinder
import pytz
import requests

def lookup_city(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1}
    response = requests.get(url, params=params, headers={"User-Agent": "birth-chart-app"})
    data = response.json()
    if not data:
        raise ValueError("City not found")

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])

    tf = TimezoneFinder()
    tz_string = tf.timezone_at(lat=lat, lng=lon)
    if tz_string is None:
        tz_string = tf.closest_timezone_at(lat=lat, lng=lon) or "Etc/GMT"

    tz = pytz.timezone(tz_string)
    utc_offset = tz.utcoffset(dt.datetime.now()).total_seconds() / 3600

    return lat, lon, utc_offset, tz_string

# --- Test cases ---
for city in ["Chirala", "New York", "London", "Tokyo"]:
    lat, lon, offset, tz = lookup_city(city)
    print(f"{city}: lat={lat}, lon={lon}, tz={tz}, offset={offset}")