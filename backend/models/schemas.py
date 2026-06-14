from pydantic import BaseModel
from typing import List, Optional


class GroundStation(BaseModel):
    lat: float
    lon: float
    alt_km: float = 0.0
    name: Optional[str] = None


class TLEInput(BaseModel):
    name: Optional[str] = "SATELLITE"
    line1: str
    line2: str


class PropagateRequest(BaseModel):
    tle: TLEInput
    timestamp_unix: Optional[float] = None
    ground_station: Optional[GroundStation] = None


class TrackRequest(BaseModel):
    tle: TLEInput
    start_unix: float
    end_unix: float
    step_seconds: float = 10.0
    ground_station: Optional[GroundStation] = None


class PassPredictRequest(BaseModel):
    tle: TLEInput
    ground_station: GroundStation
    days: float = 7.0
    min_elevation_deg: float = 10.0
    start_unix: Optional[float] = None


class SatelliteConfig(BaseModel):
    name: str
    norad_id: Optional[int] = None
    tle: TLEInput
    priority: int = 5


class ScheduleRequest(BaseModel):
    satellites: List[SatelliteConfig]
    ground_station: GroundStation
    num_antennas: int = 2
    days: float = 3.0
    min_elevation_deg: float = 10.0
    start_unix: Optional[float] = None


class RealtimeRequest(BaseModel):
    tle: TLEInput
    ground_station: GroundStation


class ECIPosition(BaseModel):
    x: float
    y: float
    z: float


class ECEFPosition(BaseModel):
    x: float
    y: float
    z: float


class GeodeticPosition(BaseModel):
    lat_deg: float
    lon_deg: float
    alt_km: float


class LookAngles(BaseModel):
    azimuth_deg: float
    elevation_deg: float
    range_km: float


class PropagateResponse(BaseModel):
    eci: ECIPosition
    ecef: ECEFPosition
    geodetic: GeodeticPosition
    look_angles: Optional[LookAngles] = None
    timestamp_unix: float


class PassInfo(BaseModel):
    aos_unix: float
    los_unix: float
    tca_unix: float
    max_elevation_deg: float
    duration_seconds: float
    aos_azimuth_deg: float
    los_azimuth_deg: float
    tca_azimuth_deg: float


class PassPredictResponse(BaseModel):
    satellite_name: str
    passes: List[PassInfo]
    ground_station: GroundStation
    prediction_days: float
    min_elevation_deg: float
