"""Tests for pass prediction."""
import sys
sys.path.insert(0, '/opt/Coconut_Eval/task/zzz-fullstack-113')

from backend.sgp4.tle_parser import parse_tle
from backend.sgp4.time_utils import jd_from_unix, epoch_to_jd
from backend.passes.predictor import predict_passes


ISS_NAME = "ISS (ZARYA)"
ISS_LINE1 = "1 25544U 98067A   24045.51782528  .00011834  00000+0  21410-3 0  9994"
ISS_LINE2 = "2 25544  51.6415 208.9534 0003570  84.9720  29.4174 15.49911407440007"


def test_predict_passes_finds_passes():
    """ISS should have multiple passes over New York in 3 days."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    start_jd = tle.epoch_jd

    passes = predict_passes(
        tle, station_lat_deg=40.7128, station_lon_deg=-74.0060,
        station_alt_km=0.01, start_jd=start_jd, days=3.0,
        min_elevation_deg=10.0
    )

    # ISS passes over NYC multiple times per day
    assert len(passes) >= 2, f"Expected multiple passes, got {len(passes)}"


def test_pass_structure():
    """Each pass should have valid structure."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    start_jd = tle.epoch_jd

    passes = predict_passes(
        tle, station_lat_deg=40.7128, station_lon_deg=-74.0060,
        station_alt_km=0.01, start_jd=start_jd, days=3.0,
        min_elevation_deg=5.0
    )

    assert len(passes) > 0
    for p in passes:
        assert 'aos_unix' in p
        assert 'los_unix' in p
        assert 'tca_unix' in p
        assert 'max_elevation_deg' in p
        assert 'duration_seconds' in p
        assert p['aos_unix'] < p['los_unix']
        assert p['aos_unix'] <= p['tca_unix'] <= p['los_unix']
        assert p['max_elevation_deg'] >= 5.0
        assert 0 < p['duration_seconds'] < 1200  # Max ~20 min for LEO pass


def test_pass_max_elevation():
    """Max elevation should be at least the min threshold."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    start_jd = tle.epoch_jd
    min_el = 15.0

    passes = predict_passes(
        tle, station_lat_deg=40.7128, station_lon_deg=-74.0060,
        station_alt_km=0.01, start_jd=start_jd, days=5.0,
        min_elevation_deg=min_el
    )

    for p in passes:
        assert p['max_elevation_deg'] >= min_el, \
            f"Max el {p['max_elevation_deg']:.1f} < min threshold {min_el}"


def test_passes_chronological():
    """Passes should be in chronological order."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    start_jd = tle.epoch_jd

    passes = predict_passes(
        tle, station_lat_deg=40.7128, station_lon_deg=-74.0060,
        station_alt_km=0.01, start_jd=start_jd, days=5.0,
        min_elevation_deg=5.0
    )

    for i in range(1, len(passes)):
        assert passes[i]['aos_unix'] > passes[i-1]['los_unix'], \
            "Passes should not overlap"


def test_different_ground_station():
    """Passes from different locations should differ."""
    tle = parse_tle(ISS_NAME, ISS_LINE1, ISS_LINE2)
    start_jd = tle.epoch_jd

    passes_ny = predict_passes(
        tle, station_lat_deg=40.7128, station_lon_deg=-74.0060,
        station_alt_km=0.01, start_jd=start_jd, days=3.0,
        min_elevation_deg=10.0
    )

    passes_london = predict_passes(
        tle, station_lat_deg=51.5074, station_lon_deg=-0.1278,
        station_alt_km=0.01, start_jd=start_jd, days=3.0,
        min_elevation_deg=10.0
    )

    # Different cities should have different pass times
    if len(passes_ny) > 0 and len(passes_london) > 0:
        assert passes_ny[0]['aos_unix'] != passes_london[0]['aos_unix']


if __name__ == '__main__':
    test_predict_passes_finds_passes()
    test_pass_structure()
    test_pass_max_elevation()
    test_passes_chronological()
    test_different_ground_station()
    print("All pass prediction tests passed!")
