"""Propagation API endpoints."""
import time
from fastapi import APIRouter
from ..models.schemas import PropagateRequest, TrackRequest, PropagateResponse
from ..sgp4.tle_parser import parse_tle
from ..sgp4.propagator import propagate
from ..sgp4.coordinate_transforms import eci_to_ecef, ecef_to_geodetic, ecef_to_look_angles, compute_look_angles
from ..sgp4.time_utils import jd_from_unix, minutes_from_epoch
from ..sgp4.constants import DEG2RAD, RAD2DEG

router = APIRouter(prefix="/api", tags=["propagation"])


@router.post("/propagate")
async def propagate_single(req: PropagateRequest):
    """Propagate TLE to a single timestamp."""
    tle = parse_tle(req.tle.name, req.tle.line1, req.tle.line2)
    ts = req.timestamp_unix or time.time()
    jd = jd_from_unix(ts)
    tsince = minutes_from_epoch(jd, tle.epoch_jd)

    result = propagate(tle, tsince)
    x_ecef, y_ecef, z_ecef = eci_to_ecef(result.x, result.y, result.z, jd)
    lat, lon, alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)

    response = {
        'eci': {'x': result.x, 'y': result.y, 'z': result.z},
        'ecef': {'x': x_ecef, 'y': y_ecef, 'z': z_ecef},
        'geodetic': {'lat_deg': lat * RAD2DEG, 'lon_deg': lon * RAD2DEG, 'alt_km': alt},
        'velocity': {'vx': result.vx, 'vy': result.vy, 'vz': result.vz},
        'timestamp_unix': ts,
    }

    if req.ground_station:
        az, el, rng = ecef_to_look_angles(
            (x_ecef, y_ecef, z_ecef),
            req.ground_station.lat * DEG2RAD,
            req.ground_station.lon * DEG2RAD,
            req.ground_station.alt_km
        )
        response['look_angles'] = {
            'azimuth_deg': az * RAD2DEG,
            'elevation_deg': el * RAD2DEG,
            'range_km': rng,
        }

    return response


@router.post("/propagate/track")
async def propagate_track(req: TrackRequest):
    """Propagate TLE over a time range."""
    tle = parse_tle(req.tle.name, req.tle.line1, req.tle.line2)
    positions = []

    t = req.start_unix
    while t <= req.end_unix:
        jd = jd_from_unix(t)
        tsince = minutes_from_epoch(jd, tle.epoch_jd)
        result = propagate(tle, tsince)
        x_ecef, y_ecef, z_ecef = eci_to_ecef(result.x, result.y, result.z, jd)
        lat, lon, alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)

        point = {
            'timestamp_unix': t,
            'eci': {'x': result.x, 'y': result.y, 'z': result.z},
            'geodetic': {'lat_deg': lat * RAD2DEG, 'lon_deg': lon * RAD2DEG, 'alt_km': alt},
        }

        if req.ground_station:
            az, el, rng = ecef_to_look_angles(
                (x_ecef, y_ecef, z_ecef),
                req.ground_station.lat * DEG2RAD,
                req.ground_station.lon * DEG2RAD,
                req.ground_station.alt_km
            )
            point['look_angles'] = {
                'azimuth_deg': az * RAD2DEG,
                'elevation_deg': el * RAD2DEG,
                'range_km': rng,
            }

        positions.append(point)
        t += req.step_seconds

    return {'positions': positions, 'count': len(positions)}
