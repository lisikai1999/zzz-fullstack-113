"""Antenna scheduling API endpoints."""
import time
from fastapi import APIRouter
from ..models.schemas import ScheduleRequest
from ..sgp4.tle_parser import parse_tle
from ..sgp4.time_utils import jd_from_unix
from ..passes.predictor import predict_passes
from ..passes.scheduler import schedule_passes

router = APIRouter(prefix="/api", tags=["scheduling"])


@router.post("/schedule")
async def schedule(req: ScheduleRequest):
    """Schedule passes across multiple antennas with priority-based conflict resolution."""
    start_unix = req.start_unix or time.time()
    start_jd = jd_from_unix(start_unix)

    # Predict passes for all satellites
    all_passes = []
    for sat in req.satellites:
        tle = parse_tle(sat.name, sat.tle.line1, sat.tle.line2)
        passes = predict_passes(
            tle, req.ground_station.lat, req.ground_station.lon,
            req.ground_station.alt_km, start_jd, req.days, req.min_elevation_deg
        )
        for p in passes:
            p['satellite_name'] = sat.name
            p['priority'] = sat.priority
            p['norad_id'] = sat.norad_id
        all_passes.extend(passes)

    # Run scheduler
    result = schedule_passes(all_passes, req.num_antennas)

    return result
