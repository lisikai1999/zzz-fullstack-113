"""Real-time tracking SSE endpoint."""
import time
import json
import asyncio
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from ..sgp4.tle_parser import parse_tle
from ..sgp4.propagator import propagate
from ..sgp4.coordinate_transforms import eci_to_ecef, ecef_to_geodetic, ecef_to_look_angles
from ..sgp4.time_utils import jd_from_unix, minutes_from_epoch
from ..sgp4.constants import DEG2RAD, RAD2DEG

router = APIRouter(prefix="/api/realtime", tags=["realtime"])


@router.get("/stream")
async def stream_positions(
    line1: str = Query(...),
    line2: str = Query(...),
    name: str = Query("SATELLITE"),
    lat: float = Query(...),
    lon: float = Query(...),
    alt_km: float = Query(0.0),
):
    """SSE endpoint streaming satellite position updates at ~1Hz."""
    tle = parse_tle(name, line1, line2)
    station_lat_rad = lat * DEG2RAD
    station_lon_rad = lon * DEG2RAD

    async def event_generator():
        while True:
            ts = time.time()
            jd = jd_from_unix(ts)
            tsince = minutes_from_epoch(jd, tle.epoch_jd)

            try:
                result = propagate(tle, tsince)
                x_ecef, y_ecef, z_ecef = eci_to_ecef(result.x, result.y, result.z, jd)
                sat_lat, sat_lon, sat_alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)
                az, el, rng = ecef_to_look_angles(
                    (x_ecef, y_ecef, z_ecef),
                    station_lat_rad, station_lon_rad, alt_km
                )

                data = {
                    'timestamp_unix': ts,
                    'eci': {'x': result.x, 'y': result.y, 'z': result.z},
                    'ecef': {'x': x_ecef, 'y': y_ecef, 'z': z_ecef},
                    'geodetic': {
                        'lat_deg': sat_lat * RAD2DEG,
                        'lon_deg': sat_lon * RAD2DEG,
                        'alt_km': sat_alt
                    },
                    'look_angles': {
                        'azimuth_deg': az * RAD2DEG,
                        'elevation_deg': el * RAD2DEG,
                        'range_km': rng
                    },
                    'velocity': {'vx': result.vx, 'vy': result.vy, 'vz': result.vz},
                }
                yield f"data: {json.dumps(data)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

            await asyncio.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
