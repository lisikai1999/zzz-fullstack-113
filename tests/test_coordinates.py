"""Tests for coordinate transformations."""
import sys
import math
sys.path.insert(0, '/opt/Coconut_Eval/task/zzz-fullstack-113')

from backend.sgp4.coordinate_transforms import (
    eci_to_ecef, ecef_to_geodetic, geodetic_to_ecef, ecef_to_look_angles
)
from backend.sgp4.time_utils import gmst, julian_date
from backend.sgp4.constants import DEG2RAD, RAD2DEG, RE_WGS84


def test_gmst_j2000():
    """GMST at J2000.0 epoch should be ~280.46 degrees."""
    jd_j2000 = 2451545.0
    theta = gmst(jd_j2000)
    theta_deg = theta * RAD2DEG
    # GMST at J2000.0 is approximately 280.46 degrees
    assert 270 < theta_deg < 290, f"GMST at J2000: {theta_deg:.2f} deg"


def test_geodetic_to_ecef_equator():
    """Point on equator at prime meridian should be at (RE, 0, 0)."""
    x, y, z = geodetic_to_ecef(0, 0, 0)
    assert abs(x - RE_WGS84) < 0.001
    assert abs(y) < 0.001
    assert abs(z) < 0.001


def test_geodetic_to_ecef_pole():
    """North pole should be at (0, 0, ~RE*(1-f))."""
    x, y, z = geodetic_to_ecef(math.pi / 2, 0, 0)
    expected_z = RE_WGS84 * (1 - 1.0 / 298.257223563)  # RE * (1 - f) approximately
    assert abs(x) < 0.001
    assert abs(y) < 0.001
    # Semi-minor axis b = RE * (1-f) ~ 6356.752 km
    assert abs(z - 6356.752) < 1.0


def test_ecef_roundtrip():
    """geodetic -> ECEF -> geodetic should round-trip."""
    lat_orig = 40.0 * DEG2RAD
    lon_orig = -74.0 * DEG2RAD
    alt_orig = 0.1  # km

    x, y, z = geodetic_to_ecef(lat_orig, lon_orig, alt_orig)
    lat, lon, alt = ecef_to_geodetic(x, y, z)

    assert abs(lat - lat_orig) < 1e-8, f"Lat error: {(lat - lat_orig) * RAD2DEG} deg"
    assert abs(lon - lon_orig) < 1e-8, f"Lon error: {(lon - lon_orig) * RAD2DEG} deg"
    assert abs(alt - alt_orig) < 0.01, f"Alt error: {alt - alt_orig} km"


def test_look_angles_overhead():
    """A satellite directly overhead should have ~90 deg elevation."""
    # Station at equator, prime meridian
    station_lat = 0.0
    station_lon = 0.0
    station_alt = 0.0

    # Satellite directly above at 400km
    sat_x, sat_y, sat_z = geodetic_to_ecef(0.0, 0.0, 400.0)

    az, el, rng = ecef_to_look_angles(
        (sat_x, sat_y, sat_z), station_lat, station_lon, station_alt
    )

    assert abs(el * RAD2DEG - 90.0) < 0.5, f"Overhead elevation: {el * RAD2DEG:.1f}"
    assert abs(rng - 400.0) < 1.0, f"Range to overhead: {rng:.1f} km"


def test_look_angles_horizon():
    """A satellite far away at same altitude should have low elevation."""
    station_lat = 0.0
    station_lon = 0.0
    station_alt = 0.0

    # Satellite 90 degrees away at 400km altitude
    sat_x, sat_y, sat_z = geodetic_to_ecef(0.0, 90.0 * DEG2RAD, 400.0)

    az, el, rng = ecef_to_look_angles(
        (sat_x, sat_y, sat_z), station_lat, station_lon, station_alt
    )

    # Should be below horizon (elevation < 0)
    assert el * RAD2DEG < 0, f"90-deg away elevation should be negative: {el * RAD2DEG:.1f}"


def test_look_angles_azimuth_east():
    """A satellite due East should have azimuth ~90 degrees."""
    station_lat = 0.0
    station_lon = 0.0
    station_alt = 0.0

    # Satellite slightly East and above
    sat_x, sat_y, sat_z = geodetic_to_ecef(0.0, 5.0 * DEG2RAD, 400.0)

    az, el, rng = ecef_to_look_angles(
        (sat_x, sat_y, sat_z), station_lat, station_lon, station_alt
    )

    assert 80 < az * RAD2DEG < 100, f"East azimuth: {az * RAD2DEG:.1f}"


def test_eci_to_ecef_rotation():
    """ECI to ECEF should rotate by GMST."""
    # At GMST = 0, ECI = ECEF
    # Use a JD where GMST is close to 0 for easier testing
    x_eci, y_eci, z_eci = 7000.0, 0.0, 0.0
    jd = 2451545.0  # J2000

    x_ecef, y_ecef, z_ecef = eci_to_ecef(x_eci, y_eci, z_eci, jd)

    # The result should be rotated by GMST from the input
    theta = gmst(jd)
    expected_x = x_eci * math.cos(theta) + y_eci * math.sin(theta)
    expected_y = -x_eci * math.sin(theta) + y_eci * math.cos(theta)

    assert abs(x_ecef - expected_x) < 0.001
    assert abs(y_ecef - expected_y) < 0.001
    assert abs(z_ecef - z_eci) < 0.001


if __name__ == '__main__':
    test_gmst_j2000()
    test_geodetic_to_ecef_equator()
    test_geodetic_to_ecef_pole()
    test_ecef_roundtrip()
    test_look_angles_overhead()
    test_look_angles_horizon()
    test_look_angles_azimuth_east()
    test_eci_to_ecef_rotation()
    print("All coordinate transform tests passed!")
