"""N2YO API client for satellite position validation."""
import httpx
from ..config import N2YO_API_KEY


async def get_satellite_positions(norad_id: int, lat: float, lon: float,
                                   alt_m: float, seconds: int = 1):
    """
    Fetch satellite position from N2YO API.

    Returns list of position dicts with az, el, range, timestamp.
    """
    alt_m_val = alt_m
    url = (f"https://api.n2yo.com/rest/v1/satellite/positions/"
           f"{norad_id}/{lat}/{lon}/{alt_m_val}/{seconds}"
           f"?apiKey={N2YO_API_KEY}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    positions = []
    if 'positions' in data:
        for pos in data['positions']:
            positions.append({
                'azimuth_deg': pos.get('azimuth', 0),
                'elevation_deg': pos.get('elevation', 0),
                'range_km': pos.get('rangeSat', 0),
                'lat_deg': pos.get('satlatitude', 0),
                'lon_deg': pos.get('satlongitude', 0),
                'alt_km': pos.get('sataltitude', 0),
                'timestamp_unix': pos.get('timestamp', 0),
            })
    return positions, data.get('info', {})
