import os

N2YO_API_KEY = os.environ.get("N2YO_API_KEY", "")
CELESTRAK_TLE_URL = "https://celestrak.org/NORAD/elements/gp.php"

DEFAULT_STATION = {
    "lat": 40.7128,
    "lon": -74.0060,
    "alt_km": 0.01,
    "name": "New York"
}

ISS_NORAD_ID = 25544
