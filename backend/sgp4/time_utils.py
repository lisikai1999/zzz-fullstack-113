import math
from .constants import TWO_PI, DEG2RAD, SECONDS_PER_DAY


def julian_date(year, month, day, hour=0, minute=0, second=0.0):
    """Convert calendar date to Julian Date."""
    if month <= 2:
        year -= 1
        month += 12
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    jd = (int(365.25 * (year + 4716)) + int(30.6001 * (month + 1))
          + day + B - 1524.5)
    jd += (hour + minute / 60.0 + second / 3600.0) / 24.0
    return jd


def epoch_to_jd(epoch_year, epoch_days):
    """Convert TLE epoch (2-digit year + fractional day) to Julian Date."""
    if epoch_year < 57:
        year = epoch_year + 2000
    else:
        year = epoch_year + 1900
    jd = julian_date(year, 1, 1, 0, 0, 0.0) + epoch_days - 1.0
    return jd


def jd_to_datetime_components(jd):
    """Convert JD to (year, month, day, hour, minute, second)."""
    jd += 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e)
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    day_frac = f
    hour = int(day_frac * 24)
    minute = int((day_frac * 24 - hour) * 60)
    second = ((day_frac * 24 - hour) * 60 - minute) * 60.0
    return year, month, day, hour, minute, second


def gmst(jd):
    """Greenwich Mean Sidereal Time in radians (IAU 1982)."""
    # Julian centuries from J2000.0
    t_ut1 = (jd - 2451545.0) / 36525.0
    # GMST in seconds
    theta = (67310.54841
             + (876600.0 * 3600.0 + 8640184.812866) * t_ut1
             + 0.093104 * t_ut1 ** 2
             - 6.2e-6 * t_ut1 ** 3)
    # Convert seconds to radians (86400 seconds = 2*pi radians)
    theta_rad = (theta % SECONDS_PER_DAY) / SECONDS_PER_DAY * TWO_PI
    theta_rad = theta_rad % TWO_PI
    if theta_rad < 0:
        theta_rad += TWO_PI
    return theta_rad


def minutes_from_epoch(jd, epoch_jd):
    """Time since epoch in minutes."""
    return (jd - epoch_jd) * 1440.0


def jd_from_unix(timestamp):
    """Convert Unix timestamp to Julian Date."""
    return timestamp / 86400.0 + 2440587.5


def unix_from_jd(jd):
    """Convert Julian Date to Unix timestamp."""
    return (jd - 2440587.5) * 86400.0
