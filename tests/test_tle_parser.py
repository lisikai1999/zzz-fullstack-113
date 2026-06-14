"""Tests for TLE parser."""
import sys
sys.path.insert(0, '/opt/Coconut_Eval/task/zzz-fullstack-113')

from backend.sgp4.tle_parser import parse_tle
from backend.sgp4.constants import DEG2RAD, RAD2DEG
import math


def test_iss_tle_parsing():
    """Test ISS TLE parsing extracts correct orbital elements."""
    name = "ISS (ZARYA)"
    line1 = "1 25544U 98067A   24045.51782528  .00011834  00000+0  21410-3 0  9994"
    line2 = "2 25544  51.6415 208.9534 0003570  84.9720  29.4174 15.49911407440007"

    tle = parse_tle(name, line1, line2)

    assert tle.norad_id == 25544
    assert tle.name == "ISS (ZARYA)"
    assert abs(tle.inclination * RAD2DEG - 51.6415) < 0.0001
    assert abs(tle.raan * RAD2DEG - 208.9534) < 0.0001
    assert abs(tle.eccentricity - 0.0003570) < 1e-7
    assert abs(tle.arg_perigee * RAD2DEG - 84.9720) < 0.0001
    assert abs(tle.mean_anomaly * RAD2DEG - 29.4174) < 0.0001
    # Mean motion: 15.49911407 rev/day
    assert abs(tle.period - (1440.0 / 15.49911407)) < 0.01


def test_bstar_parsing():
    """Test B* drag term parsing."""
    name = "TEST"
    line1 = "1 25544U 98067A   24045.51782528  .00011834  00000+0  21410-3 0  9994"
    line2 = "2 25544  51.6415 208.9534 0003570  84.9720  29.4174 15.49911407440007"

    tle = parse_tle(name, line1, line2)
    # B* = 0.21410e-3 = 0.00021410
    assert abs(tle.bstar - 0.21410e-3) < 1e-9


def test_high_eccentricity_tle():
    """Test parsing a Molniya-type high-e orbit."""
    name = "MOLNIYA 1-91"
    line1 = "1 24960U 97054A   24045.65432100  .00000230  00000+0  10000-3 0  9990"
    line2 = "2 24960  62.8500  10.3400 6925324 270.5600  18.9300  2.00613800200001"

    tle = parse_tle(name, line1, line2)
    assert abs(tle.eccentricity - 0.6925324) < 1e-7
    assert abs(tle.inclination * RAD2DEG - 62.8500) < 0.0001


def test_epoch_conversion():
    """Test epoch year/day to JD conversion."""
    name = "TEST"
    line1 = "1 25544U 98067A   24045.51782528  .00011834  00000+0  21410-3 0  9994"
    line2 = "2 25544  51.6415 208.9534 0003570  84.9720  29.4174 15.49911407440007"

    tle = parse_tle(name, line1, line2)
    # Epoch: 2024, day 45.51782528
    # Jan 1, 2024 = JD 2460310.5
    # Day 45.51782528 means Feb 14, 2024 ~12:26 UTC
    expected_jd = 2460310.5 + 45.51782528 - 1.0
    assert abs(tle.epoch_jd - expected_jd) < 0.0001


if __name__ == '__main__':
    test_iss_tle_parsing()
    test_bstar_parsing()
    test_high_eccentricity_tle()
    test_epoch_conversion()
    print("All TLE parser tests passed!")
