"""Tests for SGP4 propagator using known ISS positions."""
import sys
import math
sys.path.insert(0, '/opt/Coconut_Eval/task/zzz-fullstack-113')

from backend.sgp4.tle_parser import parse_tle
from backend.sgp4.propagator import propagate
from backend.sgp4.coordinate_transforms import eci_to_ecef, ecef_to_geodetic
from backend.sgp4.time_utils import jd_from_unix, minutes_from_epoch, gmst
from backend.sgp4.constants import RAD2DEG


# ISS TLE for testing
ISS_NAME = "ISS (ZARYA)"
ISS_LINE1 = "1 25544U 98067A   24045.51782528  .00011834  00000+0  21410-3 0  9994"
ISS_LINE2 = "2 25544  51.6415 208.9534 0003570  84.9720  29.4174 15.49911407440007"


def test_propagate_at_epoch():
    """Propagate at t=0 (epoch) should give reasonable LEO position."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    result = propagate(tle, 0.0)

    # ISS orbit radius ~6770 km
    r = math.sqrt(result.x**2 + result.y**2 + result.z**2)
    assert 6300 < r < 6900, f"Radius {r} km is not LEO"

    # Velocity should be ~7.7 km/s
    v = math.sqrt(result.vx**2 + result.vy**2 + result.vz**2)
    assert 7.0 < v < 8.5, f"Velocity {v} km/s is not LEO"


def test_propagate_forward():
    """Propagate 60 minutes forward should still give reasonable position."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    result = propagate(tle, 60.0)

    r = math.sqrt(result.x**2 + result.y**2 + result.z**2)
    assert 6300 < r < 6900, f"Radius {r} km at t+60min"

    v = math.sqrt(result.vx**2 + result.vy**2 + result.vz**2)
    assert 7.0 < v < 8.5, f"Velocity {v} km/s at t+60min"


def test_propagate_one_period():
    """After one orbital period, satellite should be at similar radius (J2 causes ground track shift)."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)

    r0 = propagate(tle, 0.0)
    r1 = propagate(tle, tle.period)

    # Radius should be nearly identical (orbit is near-circular)
    rad0 = math.sqrt(r0.x**2 + r0.y**2 + r0.z**2)
    rad1 = math.sqrt(r1.x**2 + r1.y**2 + r1.z**2)
    assert abs(rad1 - rad0) < 10, f"Radius changed by {abs(rad1-rad0):.1f} km after one period"

    # Speed should be nearly identical
    v0 = math.sqrt(r0.vx**2 + r0.vy**2 + r0.vz**2)
    v1 = math.sqrt(r1.vx**2 + r1.vy**2 + r1.vz**2)
    assert abs(v1 - v0) < 0.01, f"Speed changed by {abs(v1-v0):.4f} km/s"


def test_altitude_in_range():
    """ISS altitude should be 350-450 km throughout propagation."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)

    for tsince in range(0, 90, 10):
        result = propagate(tle, float(tsince))
        jd = tle.epoch_jd + tsince / 1440.0
        x_ecef, y_ecef, z_ecef = eci_to_ecef(result.x, result.y, result.z, jd)
        lat, lon, alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)
        assert 300 < alt < 500, f"ISS altitude {alt:.1f} km at t+{tsince}min out of range"


def test_inclination_constraint():
    """ISS latitude should never exceed inclination (~51.6 deg)."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    max_inc = 51.6415 + 1.0  # small tolerance

    for tsince in range(0, 90, 5):
        result = propagate(tle, float(tsince))
        jd = tle.epoch_jd + tsince / 1440.0
        x_ecef, y_ecef, z_ecef = eci_to_ecef(result.x, result.y, result.z, jd)
        lat, lon, alt = ecef_to_geodetic(x_ecef, y_ecef, z_ecef)
        assert abs(lat * RAD2DEG) <= max_inc, f"Latitude {lat*RAD2DEG:.1f} exceeds inclination"


def test_propagate_negative_tsince():
    """Backward propagation should also work."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    result = propagate(tle, -60.0)

    r = math.sqrt(result.x**2 + result.y**2 + result.z**2)
    assert 6300 < r < 6900


def test_long_propagation():
    """Propagate 7 days forward — should still be valid (some accuracy loss expected)."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    tsince = 7 * 1440.0  # 7 days in minutes
    result = propagate(tle, tsince)

    r = math.sqrt(result.x**2 + result.y**2 + result.z**2)
    assert 6200 < r < 7000, f"7-day propagation radius {r} km"


if __name__ == '__main__':
    test_propagate_at_epoch()
    test_propagate_forward()
    test_propagate_one_period()
    test_altitude_in_range()
    test_inclination_constraint()
    test_propagate_negative_tsince()
    test_long_propagation()
    print("All propagator tests passed!")
