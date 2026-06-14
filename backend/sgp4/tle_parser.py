import math
from dataclasses import dataclass
from .constants import DEG2RAD, TWO_PI, MINUTES_PER_DAY, RE, KE
from .time_utils import epoch_to_jd


@dataclass
class TLERecord:
    """Parsed TLE orbital elements."""
    name: str
    norad_id: int
    classification: str
    intl_designator: str
    epoch_year: int
    epoch_days: float
    epoch_jd: float
    bstar: float
    inclination: float  # radians
    raan: float  # radians
    eccentricity: float
    arg_perigee: float  # radians
    mean_anomaly: float  # radians
    mean_motion: float  # radians/min
    rev_number: int
    # Derived
    semi_major_axis: float  # earth radii
    period: float  # minutes


def _parse_decimal_exponent(s):
    """Parse TLE's special exponential notation like ' 12345-4' → 0.12345e-4."""
    s = s.strip()
    if not s or s == '00000-0' or s == ' 00000-0':
        return 0.0
    sign = 1.0
    if s[0] == '-':
        sign = -1.0
        s = s[1:]
    elif s[0] == '+' or s[0] == ' ':
        s = s[1:]
    # Find exponent sign
    if '-' in s:
        mantissa_str, exp_str = s.split('-')
        exp_sign = -1
    elif '+' in s:
        mantissa_str, exp_str = s.split('+')
        exp_sign = 1
    else:
        return sign * float('0.' + s)
    mantissa = float('0.' + mantissa_str)
    exponent = exp_sign * int(exp_str)
    return sign * mantissa * (10.0 ** exponent)


def parse_tle(name, line1, line2):
    """Parse a two-line element set into a TLERecord."""
    name = name.strip() if name else "UNKNOWN"

    # Line 1 parsing
    norad_id = int(line1[2:7])
    classification = line1[7]
    intl_designator = line1[9:17].strip()
    epoch_year = int(line1[18:20])
    epoch_days = float(line1[20:32])
    bstar = _parse_decimal_exponent(line1[53:61])

    # Line 2 parsing
    inclination = float(line2[8:16]) * DEG2RAD
    raan = float(line2[17:25]) * DEG2RAD
    eccentricity = float('0.' + line2[26:33])
    arg_perigee = float(line2[34:42]) * DEG2RAD
    mean_anomaly = float(line2[43:51]) * DEG2RAD
    mean_motion_revs = float(line2[52:63])  # revs/day
    rev_number = int(line2[63:68])

    # Convert mean motion to radians/minute
    mean_motion = mean_motion_revs * TWO_PI / MINUTES_PER_DAY

    # Compute epoch Julian Date
    epoch_jd = epoch_to_jd(epoch_year, epoch_days)

    # Semi-major axis (earth radii)
    a = (KE / mean_motion) ** (2.0 / 3.0)

    # Period in minutes
    period = MINUTES_PER_DAY / mean_motion_revs

    return TLERecord(
        name=name,
        norad_id=norad_id,
        classification=classification,
        intl_designator=intl_designator,
        epoch_year=epoch_year,
        epoch_days=epoch_days,
        epoch_jd=epoch_jd,
        bstar=bstar,
        inclination=inclination,
        raan=raan,
        eccentricity=eccentricity,
        arg_perigee=arg_perigee,
        mean_anomaly=mean_anomaly,
        mean_motion=mean_motion,
        rev_number=rev_number,
        semi_major_axis=a,
        period=period,
    )
