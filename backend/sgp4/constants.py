import math

TWO_PI = 2.0 * math.pi
DEG2RAD = math.pi / 180.0
RAD2DEG = 180.0 / math.pi
MINUTES_PER_DAY = 1440.0
SECONDS_PER_DAY = 86400.0

# WGS-72 constants (Spacetrack Report #3)
RE = 6378.135  # Earth equatorial radius (km)
MU = 398600.8  # Earth gravitational parameter (km^3/s^2)
J2 = 1.0826158e-3
J3 = -2.53881e-6
J4 = -1.65597e-6
KE = 60.0 / math.sqrt(RE**3 / MU)  # radians/min per (earth radii)^1.5
OMEGA_E = 7.29211514670698e-5  # Earth rotation rate rad/s

# In SGP4, all distances are in earth radii (ae = 1)
XK2 = 0.5 * J2  # CK2 = 1/2 * J2 * ae^2, ae=1
XK4 = -0.375 * J4  # -3/8 * J4 * ae^4, ae=1
A3OVK2 = -J3 / XK2  # -J3 / CK2 = -J3 / (0.5*J2)
J3OJ2 = -J3 / J2  # Vallado convention: -J3/J2

# WGS-84 for geodetic conversions
RE_WGS84 = 6378.137  # km
F_WGS84 = 1.0 / 298.257223563
E_EARTH_SQ = F_WGS84 * (2.0 - F_WGS84)

# Derived
QOMS2T = ((120.0 - 78.0) / RE) ** 4  # (q0 - s)^4
S_ORIG = 78.0 / RE + 1.0  # s parameter original value (earth radii)
