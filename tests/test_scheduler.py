"""Tests for antenna scheduler."""
import sys
sys.path.insert(0, '/opt/Coconut_Eval/task/zzz-fullstack-113')

from backend.passes.scheduler import schedule_passes


def _make_pass(name, priority, start, end, max_el=45.0):
    return {
        'satellite_name': name,
        'priority': priority,
        'aos_unix': start,
        'los_unix': end,
        'max_elevation_deg': max_el,
        'duration_seconds': end - start,
    }


def test_no_conflicts():
    """Non-overlapping passes should all be scheduled."""
    passes = [
        _make_pass('SAT1', 1, 1000, 1500),
        _make_pass('SAT2', 2, 2000, 2500),
        _make_pass('SAT3', 3, 3000, 3500),
    ]
    result = schedule_passes(passes, num_antennas=1)

    assert result['stats']['scheduled'] == 3
    assert result['stats']['conflicted'] == 0
    assert len(result['antennas']['1']) == 3


def test_conflict_resolved_by_priority():
    """Overlapping passes should be resolved by priority."""
    passes = [
        _make_pass('LOW', 3, 1000, 2000, 60.0),
        _make_pass('HIGH', 1, 1500, 2500, 30.0),
    ]
    result = schedule_passes(passes, num_antennas=1)

    # HIGH priority (1) should be scheduled, LOW (3) conflicted
    assert len(result['antennas']['1']) == 1
    assert result['antennas']['1'][0]['satellite_name'] == 'HIGH'
    assert len(result['conflicts']) == 1
    assert result['conflicts'][0]['satellite_name'] == 'LOW'


def test_multiple_antennas_handle_overlap():
    """With 2 antennas, overlapping passes should be distributed."""
    passes = [
        _make_pass('SAT1', 1, 1000, 2000),
        _make_pass('SAT2', 2, 1500, 2500),
    ]
    result = schedule_passes(passes, num_antennas=2)

    assert result['stats']['scheduled'] == 2
    assert result['stats']['conflicted'] == 0


def test_three_overlapping_two_antennas():
    """3 overlapping passes, 2 antennas: lowest priority is conflicted."""
    passes = [
        _make_pass('HIGH', 1, 1000, 2000),
        _make_pass('MED', 2, 1200, 2200),
        _make_pass('LOW', 3, 1400, 2400),
    ]
    result = schedule_passes(passes, num_antennas=2)

    assert result['stats']['scheduled'] == 2
    assert result['stats']['conflicted'] == 1
    assert result['conflicts'][0]['satellite_name'] == 'LOW'


def test_priority_tiebreaker_by_elevation():
    """Same priority: higher max elevation wins."""
    passes = [
        _make_pass('LOW_EL', 1, 1000, 2000, max_el=30.0),
        _make_pass('HIGH_EL', 1, 1500, 2500, max_el=70.0),
    ]
    result = schedule_passes(passes, num_antennas=1)

    # HIGH_EL should be scheduled (sorted by -max_elevation as tiebreaker)
    assert result['antennas']['1'][0]['satellite_name'] == 'HIGH_EL'


def test_empty_passes():
    """Empty input should return empty schedule."""
    result = schedule_passes([], num_antennas=3)
    assert result['stats']['total_passes'] == 0
    assert result['stats']['scheduled'] == 0


def test_many_antennas():
    """More antennas than passes should schedule all."""
    passes = [
        _make_pass('SAT1', 1, 1000, 2000),
        _make_pass('SAT2', 2, 1000, 2000),
    ]
    result = schedule_passes(passes, num_antennas=5)
    assert result['stats']['scheduled'] == 2
    assert result['stats']['conflicted'] == 0


def test_utilization():
    """Utilization percentage should be correct."""
    passes = [
        _make_pass('A', 1, 1000, 2000),
        _make_pass('B', 2, 1500, 2500),
        _make_pass('C', 3, 1800, 2800),
    ]
    result = schedule_passes(passes, num_antennas=1)
    # Only 1 scheduled out of 3
    assert result['stats']['utilization_percent'] == round(1 / 3 * 100, 1)


if __name__ == '__main__':
    test_no_conflicts()
    test_conflict_resolved_by_priority()
    test_multiple_antennas_handle_overlap()
    test_three_overlapping_two_antennas()
    test_priority_tiebreaker_by_elevation()
    test_empty_passes()
    test_many_antennas()
    test_utilization()
    print("All scheduler tests passed!")
