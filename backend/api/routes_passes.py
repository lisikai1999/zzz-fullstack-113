"""Pass prediction API endpoints."""
import time
from fastapi import APIRouter
from ..models.schemas import PassPredictRequest, ScheduleRequest
from ..sgp4.tle_parser import parse_tle
from ..sgp4.time_utils import jd_from_unix
from ..passes.predictor import predict_passes

router = APIRouter(prefix="/api/passes", tags=["passes"])


@router.post("/predict")
async def predict_single(req: PassPredictRequest):
    """Predict passes for a single satellite."""
    tle = parse_tle(req.tle.name, req.tle.line1, req.tle.line2)
    start_unix = req.start_unix or time.time()
    start_jd = jd_from_unix(start_unix)

    passes = predict_passes(
        tle, req.ground_station.lat, req.ground_station.lon,
        req.ground_station.alt_km, start_jd, req.days, req.min_elevation_deg
    )

    return {
        'satellite_name': req.tle.name,
        'passes': passes,
        'count': len(passes),
        'ground_station': req.ground_station.model_dump(),
        'prediction_days': req.days,
        'min_elevation_deg': req.min_elevation_deg,
    }


@router.post("/predict/multi")
async def predict_multi(req: ScheduleRequest):
    """Predict passes for multiple satellites."""
    start_unix = req.start_unix or time.time()
    start_jd = jd_from_unix(start_unix)

    results = []
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
        results.extend(passes)

    results.sort(key=lambda p: p['aos_unix'])
    return {'passes': results, 'count': len(results)}
