"""
Multi-antenna greedy interval scheduler with priority-based conflict resolution.
"""
from typing import List, Dict, Any


def schedule_passes(passes: List[Dict[str, Any]], num_antennas: int) -> Dict[str, Any]:
    """
    Schedule satellite passes across multiple antennas using greedy algorithm.

    Passes must each have:
        - satellite_name: str
        - priority: int (lower number = higher priority)
        - aos_unix: float (start time)
        - los_unix: float (end time)
        - max_elevation_deg: float

    Args:
        passes: List of pass dictionaries
        num_antennas: Number of available antennas

    Returns:
        {
            'antennas': {antenna_id: [list of assigned passes]},
            'conflicts': [list of unscheduled passes due to conflicts],
            'stats': {...}
        }
    """
    # Sort by priority (ascending = higher priority first), then by max_elevation (descending)
    sorted_passes = sorted(passes, key=lambda p: (p['priority'], -p['max_elevation_deg']))

    # Initialize antenna schedules
    antennas = {str(i + 1): [] for i in range(num_antennas)}
    conflicts = []

    for pass_info in sorted_passes:
        assigned = False
        pass_start = pass_info['aos_unix']
        pass_end = pass_info['los_unix']

        # Try each antenna
        for ant_id in sorted(antennas.keys()):
            # Check for conflicts with existing assignments on this antenna
            has_conflict = False
            for existing in antennas[ant_id]:
                if pass_start < existing['los_unix'] and pass_end > existing['aos_unix']:
                    has_conflict = True
                    break

            if not has_conflict:
                antennas[ant_id].append(pass_info)
                assigned = True
                break

        if not assigned:
            conflicts.append(pass_info)

    # Sort each antenna's schedule by time
    for ant_id in antennas:
        antennas[ant_id].sort(key=lambda p: p['aos_unix'])

    # Stats
    total = len(passes)
    scheduled = total - len(conflicts)

    return {
        'antennas': antennas,
        'conflicts': conflicts,
        'stats': {
            'total_passes': total,
            'scheduled': scheduled,
            'conflicted': len(conflicts),
            'utilization_percent': round(scheduled / total * 100, 1) if total > 0 else 0,
        }
    }
