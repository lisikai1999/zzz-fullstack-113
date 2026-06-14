"""N2YO validation comparison endpoint."""
import time
from fastapi import APIRouter, Query
from ..sgp4.tle_parser import parse_tle
from ..sgp4.propagator import propagate
from ..sgp4.coordinate_transforms import eci_to_ecef, ecef_to_look_angles
from ..sgp4.time_utils import jd_from_unix, minutes_from_epoch
from ..sgp4.constants import DEG2RAD, RAD2DEG
from ..services.n2yo_client import get_satellite_positions
from ..config import N2YO_API_KEY

router = APIRouter(prefix="/api/validate", tags=["validation"])


@router.get("/compare/{norad_id}")
async def compare_with_n2yo(
    norad_id: int,
    line1: str = Query(...),
    line2: str = Query(...),
    name: str = Query("SATELLITE"),
    lat: float = Query(...),
    lon: float = Query(...),
    alt_km: float = Query(0.0),
):
    """Compare computed position with N2YO API for validation."""
    if not N2YO_API_KEY:
        return {'error': 'N2YO API key not configured. Set N2YO_API_KEY environment variable.'}

    tle = parse_tle(name, line1, line2)

    # Get N2YO position
    n2yo_positions, n2yo_info = await get_satellite_positions(
        norad_id, lat, lon, alt_km * 1000, seconds=1
    )

    if not n2yo_positions:
        return {'error': 'Failed to get N2YO position'}

    n2yo_pos = n2yo_positions[0]
    ts = n2yo_pos['timestamp_unix']

    # Compute our position at same timestamp
    jd = jd_from_unix(ts)
    tsince = minutes_from_epoch(jd, tle.epoch_jd)
    result = propagate(tle, tsince)
    x_ecef, y_ecef, z_ecef = eci_to_ecef(result.x, result.y, result.z, jd)
    az, el, rng = ecef_to_look_angles(
        (x_ecef, y_ecef, z_ecef),
        lat * DEG2RAD, lon * DEG2RAD, alt_km
    )

    computed = {
        'azimuth_deg': az * RAD2DEG,
        'elevation_deg': el * RAD2DEG,
        'range_km': rng,
    }

    # Compute deviations
    az_delta = abs(computed['azimuth_deg'] - n2yo_pos['azimuth_deg'])
    if az_delta > 180:
        az_delta = 360 - az_delta
    el_delta = abs(computed['elevation_deg'] - n2yo_pos['elevation_deg'])

    return {
        'timestamp_unix': ts,
        'computed': computed,
        'n2yo': n2yo_pos,
        'deviation': {
            'azimuth_deg': round(az_delta, 4),
            'elevation_deg': round(el_delta, 4),
            'within_tolerance': az_delta < 0.5 and el_delta < 0.5,
        },
        'n2yo_info': n2yo_info,
    }


@router.get("/status")
async def validation_status():
    """Check if N2YO validation is available."""
    return {
        'n2yo_configured': bool(N2YO_API_KEY),
        'api_key_set': len(N2YO_API_KEY) > 0,
    }
