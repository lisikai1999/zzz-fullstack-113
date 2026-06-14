"""Satellite Tracking System — FastAPI application."""
import time
import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api.routes_propagation import router as propagation_router
from .api.routes_passes import router as passes_router
from .api.routes_scheduling import router as scheduling_router
from .api.routes_realtime import router as realtime_router
from .api.routes_validation import router as validation_router
from .config import CELESTRAK_TLE_URL, ISS_NORAD_ID

app = FastAPI(title="Satellite Tracking System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(propagation_router)
app.include_router(passes_router)
app.include_router(scheduling_router)
app.include_router(realtime_router)
app.include_router(validation_router)

# Mount frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def root():
    """Redirect to frontend."""
    from fastapi.responses import FileResponse
    index = frontend_path / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Satellite Tracking System API", "docs": "/docs"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}


@app.get("/api/tle/iss")
async def get_iss_tle():
    """Fetch latest ISS TLE from CelesTrak."""
    url = f"{CELESTRAK_TLE_URL}?CATNR={ISS_NORAD_ID}&FORMAT=TLE"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            lines = resp.text.strip().split('\n')
            if len(lines) >= 3:
                return {
                    'name': lines[0].strip(),
                    'line1': lines[1].strip(),
                    'line2': lines[2].strip(),
                }
            elif len(lines) >= 2:
                return {
                    'name': 'ISS (ZARYA)',
                    'line1': lines[0].strip(),
                    'line2': lines[1].strip(),
                }
    except Exception as e:
        return {'error': str(e), 'fallback': True, **ISS_FALLBACK_TLE}


ISS_FALLBACK_TLE = {
    'name': 'ISS (ZARYA)',
    'line1': '1 25544U 98067A   24045.51782528  .00011834  00000+0  21410-3 0  9994',
    'line2': '2 25544  51.6415 208.9534 0003570  84.9720  29.4174 15.49911407440007',
}


@app.get("/api/tle/fallback")
async def get_fallback_tle():
    """Get hardcoded ISS TLE for offline testing."""
    return ISS_FALLBACK_TLE
