"""Coordinate transformations: ECI(TEME) → ECEF → Geodetic → Topocentric."""
import math
from .constants import TWO_PI, RE_WGS84, E_EARTH_SQ, DEG2RAD, RAD2DEG, OMEGA_E
from .time_utils import gmst


def eci_to_ecef(x_eci, y_eci, z_eci, jd):
    """
    Convert ECI (TEME) position to ECEF by rotating by GMST.

    Args:
        x_eci, y_eci, z_eci: ECI position in km
        jd: Julian Date

    Returns:
        (x_ecef, y_ecef, z_ecef) in km
    """
    theta_g = gmst(jd)
    cos_g = math.cos(theta_g)
    sin_g = math.sin(theta_g)

    x_ecef = x_eci * cos_g + y_eci * sin_g
    y_ecef = -x_eci * sin_g + y_eci * cos_g
    z_ecef = z_eci

    return x_ecef, y_ecef, z_ecef


def ecef_to_geodetic(x_ecef, y_ecef, z_ecef):
    """
    Convert ECEF to geodetic coordinates (lat, lon, alt).

    Uses iterative method (Bowring).

    Returns:
        (lat_rad, lon_rad, alt_km)
    """
    lon = math.atan2(y_ecef, x_ecef)

    # Distance from Z axis
    p = math.sqrt(x_ecef * x_ecef + y_ecef * y_ecef)

    # Iterative latitude computation
    lat = math.atan2(z_ecef, p * (1.0 - E_EARTH_SQ))

    for _ in range(10):
        sin_lat = math.sin(lat)
        N = RE_WGS84 / math.sqrt(1.0 - E_EARTH_SQ * sin_lat * sin_lat)
        lat_new = math.atan2(z_ecef + E_EARTH_SQ * N * sin_lat, p)
        if abs(lat_new - lat) < 1e-12:
            break
        lat = lat_new

    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    N = RE_WGS84 / math.sqrt(1.0 - E_EARTH_SQ * sin_lat * sin_lat)

    if abs(cos_lat) > 1e-10:
        alt = p / cos_lat - N
    else:
        alt = abs(z_ecef) - N * (1.0 - E_EARTH_SQ)

    return lat, lon, alt


def geodetic_to_ecef(lat_rad, lon_rad, alt_km):
    """
    Convert geodetic (lat, lon, alt) to ECEF.

    Args:
        lat_rad: Latitude in radians
        lon_rad: Longitude in radians
        alt_km: Altitude in km

    Returns:
        (x_ecef, y_ecef, z_ecef) in km
    """
    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    sin_lon = math.sin(lon_rad)
    cos_lon = math.cos(lon_rad)

    N = RE_WGS84 / math.sqrt(1.0 - E_EARTH_SQ * sin_lat * sin_lat)

    x = (N + alt_km) * cos_lat * cos_lon
    y = (N + alt_km) * cos_lat * sin_lon
    z = (N * (1.0 - E_EARTH_SQ) + alt_km) * sin_lat

    return x, y, z


def ecef_to_look_angles(sat_ecef, station_lat_rad, station_lon_rad, station_alt_km):
    """
    Compute look angles (azimuth, elevation, range) from a ground station to a satellite.

    Args:
        sat_ecef: (x, y, z) satellite ECEF position in km
        station_lat_rad: Ground station geodetic latitude (radians)
        station_lon_rad: Ground station geodetic longitude (radians)
        station_alt_km: Ground station altitude (km)

    Returns:
        (azimuth_rad, elevation_rad, range_km)
    """
    # Ground station ECEF position
    gs_x, gs_y, gs_z = geodetic_to_ecef(station_lat_rad, station_lon_rad, station_alt_km)

    # Range vector in ECEF
    dx = sat_ecef[0] - gs_x
    dy = sat_ecef[1] - gs_y
    dz = sat_ecef[2] - gs_z

    # Rotate to topocentric horizon frame (South-East-Zenith)
    sin_lat = math.sin(station_lat_rad)
    cos_lat = math.cos(station_lat_rad)
    sin_lon = math.sin(station_lon_rad)
    cos_lon = math.cos(station_lon_rad)

    range_s = sin_lat * cos_lon * dx + sin_lat * sin_lon * dy - cos_lat * dz
    range_e = -sin_lon * dx + cos_lon * dy
    range_z = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz

    # Slant range
    rng = math.sqrt(range_s * range_s + range_e * range_e + range_z * range_z)

    # Elevation
    elevation = math.asin(range_z / rng) if rng > 0 else 0.0

    # Azimuth (measured clockwise from North)
    azimuth = math.atan2(range_e, -range_s)
    if azimuth < 0:
        azimuth += TWO_PI

    return azimuth, elevation, rng


def compute_look_angles(tle, tsince, station_lat_deg, station_lon_deg, station_alt_km, jd):
    """
    High-level convenience: propagate a TLE and get look angles from a station.

    Args:
        tle: TLERecord
        tsince: Minutes since TLE epoch
        station_lat_deg: Station latitude in degrees
        station_lon_deg: Station longitude in degrees
        station_alt_km: Station altitude in km
        jd: Julian date for the propagation time

    Returns:
        dict with azimuth_deg, elevation_deg, range_km, lat_deg, lon_deg, alt_km
    """
    from .propagator import propagate

    result = propagate(tle, tsince)

    # ECI to ECEF
    x_ecef, y_ecef, z_ecef = eci_to_ecef(result.x, result.y, result.z, jd)

    # Satellite geodetic position
    sat_lat, sat_lon, sat_alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)

    # Look angles from station
    station_lat_rad = station_lat_deg * DEG2RAD
    station_lon_rad = station_lon_deg * DEG2RAD

    az, el, rng = ecef_to_look_angles(
        (x_ecef, y_ecef, z_ecef),
        station_lat_rad, station_lon_rad, station_alt_km
    )

    return {
        'azimuth_deg': az * RAD2DEG,
        'elevation_deg': el * RAD2DEG,
        'range_km': rng,
        'sat_lat_deg': sat_lat * RAD2DEG,
        'sat_lon_deg': sat_lon * RAD2DEG,
        'sat_alt_km': sat_alt,
        'eci': {'x': result.x, 'y': result.y, 'z': result.z},
        'ecef': {'x': x_ecef, 'y': y_ecef, 'z': z_ecef},
        'velocity': {'vx': result.vx, 'vy': result.vy, 'vz': result.vz},
    }
