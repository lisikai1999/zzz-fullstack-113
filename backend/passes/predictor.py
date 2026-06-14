"""Pass prediction engine: finds satellite passes over a ground station."""
import math
from ..sgp4.tle_parser import TLERecord
from ..sgp4.propagator import propagate
from ..sgp4.coordinate_transforms import eci_to_ecef, ecef_to_look_angles
from ..sgp4.time_utils import minutes_from_epoch, unix_from_jd
from ..sgp4.constants import DEG2RAD, RAD2DEG


def _elevation_at(tle, jd, station_lat_rad, station_lon_rad, station_alt_km):
    """Compute satellite elevation from a station at a given Julian Date."""
    tsince = minutes_from_epoch(jd, tle.epoch_jd)
    result = propagate(tle, tsince)
    x_ecef, y_ecef, z_ecef = eci_to_ecef(result.x, result.y, result.z, jd)
    _, el, _ = ecef_to_look_angles(
        (x_ecef, y_ecef, z_ecef),
        station_lat_rad, station_lon_rad, station_alt_km
    )
    return el * RAD2DEG


def _full_look_at(tle, jd, station_lat_rad, station_lon_rad, station_alt_km):
    """Compute full look angles at a given Julian Date."""
    tsince = minutes_from_epoch(jd, tle.epoch_jd)
    result = propagate(tle, tsince)
    x_ecef, y_ecef, z_ecef = eci_to_ecef(result.x, result.y, result.z, jd)
    az, el, rng = ecef_to_look_angles(
        (x_ecef, y_ecef, z_ecef),
        station_lat_rad, station_lon_rad, station_alt_km
    )
    return az * RAD2DEG, el * RAD2DEG, rng


def _bisect_crossing(tle, jd_below, jd_above, station_lat_rad, station_lon_rad,
                     station_alt_km, threshold=0.0, iterations=40):
    """Find the exact time when elevation crosses threshold using bisection.
    jd_below: time when elevation < threshold
    jd_above: time when elevation > threshold
    """
    for _ in range(iterations):
        jd_mid = (jd_below + jd_above) / 2.0
        el = _elevation_at(tle, jd_mid, station_lat_rad, station_lon_rad, station_alt_km)
        if el < threshold:
            jd_below = jd_mid
        else:
            jd_above = jd_mid
    return (jd_below + jd_above) / 2.0


def _find_max_elevation(tle, jd_start, jd_end, station_lat_rad, station_lon_rad,
                        station_alt_km):
    """Find TCA (max elevation) within a pass using golden section search."""
    gr = (math.sqrt(5) + 1) / 2
    a = jd_start
    b = jd_end

    for _ in range(60):
        if abs(b - a) < 0.1 / 86400.0:
            break
        c = b - (b - a) / gr
        d = a + (b - a) / gr
        fc = _elevation_at(tle, c, station_lat_rad, station_lon_rad, station_alt_km)
        fd = _elevation_at(tle, d, station_lat_rad, station_lon_rad, station_alt_km)
        if fc > fd:
            b = d
        else:
            a = c

    tca_jd = (a + b) / 2.0
    max_el = _elevation_at(tle, tca_jd, station_lat_rad, station_lon_rad, station_alt_km)
    return tca_jd, max_el


def predict_passes(tle: TLERecord, station_lat_deg: float, station_lon_deg: float,
                   station_alt_km: float, start_jd: float, days: float = 7.0,
                   min_elevation_deg: float = 10.0):
    """
    Predict satellite passes over a ground station.

    Uses a two-phase approach:
    1. Coarse scan with 60-second steps to detect horizon crossings
    2. Bisection to refine AOS/LOS to sub-second accuracy
    3. Golden section search for TCA (max elevation)
    4. Filter passes below min_elevation threshold
    """
    station_lat_rad = station_lat_deg * DEG2RAD
    station_lon_rad = station_lon_deg * DEG2RAD

    end_jd = start_jd + days
    passes = []

    # Coarse step: 60 seconds. For LEO (90 min period), a pass lasts ~10 min max.
    # 60s step ensures we never skip a complete pass.
    coarse_step = 60.0 / 86400.0  # 60 seconds in days

    jd = start_jd
    prev_el = _elevation_at(tle, jd, station_lat_rad, station_lon_rad, station_alt_km)
    in_pass = prev_el > 0
    pass_start_jd = jd if in_pass else None

    jd += coarse_step

    while jd < end_jd:
        el = _elevation_at(tle, jd, station_lat_rad, station_lon_rad, station_alt_km)

        if not in_pass and el > 0 and prev_el <= 0:
            # Rising above horizon
            aos_jd = _bisect_crossing(
                tle, jd - coarse_step, jd, station_lat_rad, station_lon_rad,
                station_alt_km, threshold=0.0
            )
            in_pass = True
            pass_start_jd = aos_jd

        elif in_pass and el <= 0 and prev_el > 0:
            # Setting below horizon
            los_jd = _bisect_crossing(
                tle, jd - coarse_step, jd, station_lat_rad, station_lon_rad,
                station_alt_km, threshold=0.0
            )

            # Find max elevation (TCA)
            tca_jd, max_el = _find_max_elevation(
                tle, pass_start_jd, los_jd, station_lat_rad, station_lon_rad,
                station_alt_km
            )

            # Only include pass if max elevation exceeds minimum threshold
            if max_el >= min_elevation_deg:
                aos_az, _, _ = _full_look_at(tle, pass_start_jd, station_lat_rad, station_lon_rad, station_alt_km)
                los_az, _, _ = _full_look_at(tle, los_jd, station_lat_rad, station_lon_rad, station_alt_km)
                tca_az, _, _ = _full_look_at(tle, tca_jd, station_lat_rad, station_lon_rad, station_alt_km)

                duration_seconds = (los_jd - pass_start_jd) * 86400.0

                passes.append({
                    'aos_jd': pass_start_jd,
                    'los_jd': los_jd,
                    'tca_jd': tca_jd,
                    'aos_unix': unix_from_jd(pass_start_jd),
                    'los_unix': unix_from_jd(los_jd),
                    'tca_unix': unix_from_jd(tca_jd),
                    'max_elevation_deg': max_el,
                    'duration_seconds': duration_seconds,
                    'aos_azimuth_deg': aos_az,
                    'los_azimuth_deg': los_az,
                    'tca_azimuth_deg': tca_az,
                })

            in_pass = False

        prev_el = el
        jd += coarse_step

    return passes
