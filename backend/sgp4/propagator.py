"""
SGP4 orbit propagator — Spacetrack Report No. 3 (Hoots & Roehrich 1980)
with corrections from Vallado, Crawford, Hujsak & Kelso (2006).

Near-earth branch only (period < 225 min).
Reference: "Revisiting Spacetrack Report #3", Vallado et al., AIAA 2006-6753.
"""
import math
from dataclasses import dataclass
from .constants import (
    TWO_PI, RE, KE, J2, J3, J4, XK2, XK4, A3OVK2, J3OJ2,
    QOMS2T, S_ORIG, MINUTES_PER_DAY
)
from .tle_parser import TLERecord


@dataclass
class SGP4Init:
    """Pre-computed initialization constants."""
    n0dp: float
    no_kozai: float
    a0dp: float
    e0: float
    i0: float
    omega0: float
    raan0: float
    m0: float
    bstar: float
    epoch_jd: float

    sinio: float
    cosio: float
    cosio2: float
    x1mth2: float
    x3thm1: float
    x7thm1: float
    xlcof: float
    aycof: float

    C1: float
    C3: float
    C4: float
    C5: float
    D2: float
    D3: float
    D4: float
    t2cof: float
    t3cof: float
    t4cof: float
    t5cof: float
    mdot: float
    omgdot: float
    xnodot: float
    xmcof: float
    eta: float
    delmo: float
    sinmo: float
    omgcof: float

    is_deep_space: bool


def _initialize(tle: TLERecord) -> SGP4Init:
    """SGP4 initialization (Vallado 2006 conventions)."""
    e0 = tle.eccentricity
    i0 = tle.inclination
    omega0 = tle.arg_perigee
    raan0 = tle.raan
    m0 = tle.mean_anomaly
    bstar = tle.bstar
    no_kozai = tle.mean_motion

    cosio = math.cos(i0)
    sinio = math.sin(i0)
    cosio2 = cosio * cosio
    x1mth2 = 1.0 - cosio2
    x3thm1 = 3.0 * cosio2 - 1.0
    x7thm1 = 7.0 * cosio2 - 1.0

    # Recover original mean motion and semimajor axis
    a1 = (KE / no_kozai) ** (2.0 / 3.0)
    betao2 = 1.0 - e0 * e0
    betao = math.sqrt(betao2)
    temp0 = 1.5 * XK2 * x3thm1 / (betao * betao2)
    del1 = temp0 / (a1 * a1)
    a0 = a1 * (1.0 - del1 * (1.0 / 3.0 + del1 * (1.0 + 134.0 / 81.0 * del1)))
    del0 = temp0 / (a0 * a0)
    xnodp = no_kozai / (1.0 + del0)
    aodp = a0 / (1.0 - del0)

    period = TWO_PI / xnodp
    is_deep_space = period >= 225.0

    # Perigee height (km)
    perige = (aodp * (1.0 - e0) - 1.0) * RE

    # s parameter and qoms2t
    if perige < 98.0:
        s4 = 20.0
    elif perige < 156.0:
        s4 = perige - 78.0
    else:
        s4 = 78.0
    s = s4 / RE + 1.0
    qoms24 = ((120.0 / RE + 1.0) - s) ** 4

    xi = 1.0 / (aodp - s)
    eta = aodp * e0 * xi
    etasq = eta * eta
    eeta = e0 * eta
    psisq = abs(1.0 - etasq)
    coef = qoms24 * (xi ** 4)
    coef1 = coef / (psisq ** 3.5)

    C2 = coef1 * xnodp * (
        aodp * (1.0 + 1.5 * etasq + eeta * (4.0 + etasq))
        + 0.375 * J2 * xi / psisq * x3thm1 * (8.0 + 3.0 * etasq * (8.0 + etasq))
    )
    C1 = bstar * C2

    C3 = 0.0
    if e0 > 1.0e-4:
        C3 = -2.0 * coef * xi * J3OJ2 * xnodp * sinio / e0

    C4 = 2.0 * xnodp * coef1 * aodp * betao2 * (
        eta * (2.0 + 0.5 * etasq) + e0 * (0.5 + 2.0 * etasq)
        - J2 * xi / (aodp * psisq) * (
            -3.0 * x3thm1 * (1.0 - 2.0 * eeta + etasq * (1.5 - 0.5 * eeta))
            + 0.75 * x1mth2 * (2.0 * etasq - eeta * (1.0 + etasq)) * math.cos(2.0 * omega0)
        )
    )

    C5 = 2.0 * coef1 * aodp * betao2 * (
        1.0 + 2.75 * (etasq + eeta) + eeta * etasq
    )

    pinvsq = 1.0 / (aodp * aodp * betao2 * betao2)

    # Secular rates (Vallado: use J2 directly, n0dp = no_unkozai as base)
    temp1 = 1.5 * J2 * pinvsq * xnodp
    temp2 = 0.5 * temp1 * J2 * pinvsq
    temp3 = -0.46875 * J4 * pinvsq * pinvsq * xnodp

    mdot = (xnodp
            + 0.5 * temp1 * betao * x3thm1
            + 0.0625 * temp2 * betao * (13.0 - 78.0 * cosio2 + 137.0 * cosio2 * cosio2))

    omgdot = (-0.5 * temp1 * (1.0 - 5.0 * cosio2)
              + 0.0625 * temp2 * (7.0 - 114.0 * cosio2 + 395.0 * cosio2 * cosio2)
              + temp3 * (3.0 - 36.0 * cosio2 + 49.0 * cosio2 * cosio2))

    xhdot1 = -temp1 * cosio
    xnodot = (xhdot1
              + (0.5 * temp2 * (4.0 - 19.0 * cosio2)
                 + 2.0 * temp3 * (3.0 - 7.0 * cosio2)) * cosio)

    # Drag corrections
    omgcof = bstar * C3 * math.cos(omega0)
    xmcof = 0.0
    if e0 > 1.0e-4:
        xmcof = -(2.0 / 3.0) * coef * bstar / eeta
    delmo = (1.0 + eta * math.cos(m0)) ** 3
    sinmo = math.sin(m0)

    # Higher-order secular drag
    D2 = 4.0 * aodp * xi * C1 * C1
    D3 = (4.0 / 3.0) * aodp * xi * xi * (17.0 * aodp + s) * (C1 ** 3)
    D4 = (2.0 / 3.0) * aodp * aodp * (xi ** 3) * (221.0 * aodp + 31.0 * s) * (C1 ** 4)
    t2cof = 1.5 * C1
    t3cof = D2 + 2.0 * C1 * C1
    t4cof = 0.25 * (3.0 * D3 + C1 * (12.0 * D2 + 10.0 * C1 * C1))
    t5cof = 0.2 * (3.0 * D4 + 12.0 * C1 * D3 + 6.0 * D2 * D2 + 15.0 * C1 * C1 * (2.0 * D2 + C1 * C1))

    # Long-period periodics coefficients (match Vallado sgp4init lines 1485-1488)
    if abs(1.0 + cosio) > 1.5e-12:
        xlcof = 0.25 * J3OJ2 * sinio * (3.0 + 5.0 * cosio) / (1.0 + cosio)
    else:
        xlcof = 0.25 * J3OJ2 * sinio * (3.0 + 5.0 * cosio) / 1.5e-12
    aycof = 0.5 * J3OJ2 * sinio

    return SGP4Init(
        n0dp=xnodp, no_kozai=no_kozai, a0dp=aodp, e0=e0, i0=i0,
        omega0=omega0, raan0=raan0, m0=m0,
        bstar=bstar, epoch_jd=tle.epoch_jd,
        sinio=sinio, cosio=cosio, cosio2=cosio2,
        x1mth2=x1mth2, x3thm1=x3thm1, x7thm1=x7thm1,
        xlcof=xlcof, aycof=aycof,
        C1=C1, C3=C3, C4=C4, C5=C5,
        D2=D2, D3=D3, D4=D4,
        t2cof=t2cof, t3cof=t3cof, t4cof=t4cof, t5cof=t5cof,
        mdot=mdot, omgdot=omgdot, xnodot=xnodot,
        xmcof=xmcof, eta=eta, delmo=delmo, sinmo=sinmo,
        omgcof=omgcof,
        is_deep_space=is_deep_space,
    )


_init_cache = {}


def _get_init(tle: TLERecord) -> SGP4Init:
    key = (tle.norad_id, tle.epoch_jd)
    if key not in _init_cache:
        _init_cache[key] = _initialize(tle)
    return _init_cache[key]


def clear_cache():
    _init_cache.clear()


@dataclass
class PropagationResult:
    """ECI position and velocity (TEME frame)."""
    x: float   # km
    y: float   # km
    z: float   # km
    vx: float  # km/s
    vy: float  # km/s
    vz: float  # km/s


def propagate(tle: TLERecord, tsince: float) -> PropagationResult:
    """
    Propagate a satellite using SGP4.

    Args:
        tle: Parsed TLE record
        tsince: Minutes since TLE epoch

    Returns:
        PropagationResult with position (km) and velocity (km/s) in TEME frame
    """
    init = _get_init(tle)

    if init.is_deep_space:
        raise ValueError("Deep-space satellites (period >= 225 min) not supported")

    # --- Secular effects of drag and gravitation ---
    xmdf = init.m0 + init.mdot * tsince
    omgadf = init.omega0 + init.omgdot * tsince
    xnoddf = init.raan0 + init.xnodot * tsince

    tsq = tsince * tsince
    tcu = tsq * tsince
    tfo = tcu * tsince

    # Mean anomaly with drag correction
    delomg = init.omgcof * tsince
    delm = 0.0
    if init.e0 > 1.0e-4:
        delm = init.xmcof * ((1.0 + init.eta * math.cos(xmdf)) ** 3 - init.delmo)

    xmp = xmdf + delomg + delm
    omega = omgadf - delomg - delm
    xnode = xnoddf

    # Secular update of a, e with drag
    tempa = 1.0 - init.C1 * tsince - init.D2 * tsq - init.D3 * tcu - init.D4 * tfo
    tempe = init.bstar * init.C4 * tsince + init.bstar * init.C5 * (math.sin(xmp) - init.sinmo)
    templ = init.t2cof * tsq + init.t3cof * tcu + init.t4cof * tfo + init.t5cof * tfo * tsince

    a = init.a0dp * tempa * tempa
    e = init.e0 - tempe
    xl = xmp + omega + xnode + init.n0dp * templ

    # Clamp eccentricity
    if e < 1.0e-6:
        e = 1.0e-6
    if e > 1.0 - 1.0e-6:
        e = 1.0 - 1.0e-6

    beta = math.sqrt(1.0 - e * e)
    xn = KE / (a ** 1.5)

    # --- Long-period periodics ---
    axN = e * math.cos(omega)
    temp0 = 1.0 / (a * (1.0 - e * e))
    xLL = xl + temp0 * init.xlcof * axN
    ayN = e * math.sin(omega) + temp0 * init.aycof

    # --- Solve Kepler's equation ---
    capu = (xLL - xnode) % TWO_PI
    if capu < 0.0:
        capu += TWO_PI

    # Newton-Raphson (Vallado form)
    eo1 = capu
    for _ in range(10):
        sinepw = math.sin(eo1)
        cosepw = math.cos(eo1)
        f = capu + axN * sinepw - ayN * cosepw - eo1
        fdot = axN * cosepw + ayN * sinepw - 1.0
        delta = -f / fdot
        eo1 += delta
        if abs(delta) < 1.0e-12:
            break

    # --- Short-period preliminary quantities ---
    sinepw = math.sin(eo1)
    cosepw = math.cos(eo1)

    ecose = axN * cosepw + ayN * sinepw
    esine = axN * sinepw - ayN * cosepw
    elsq = axN * axN + ayN * ayN
    pl = a * (1.0 - elsq)
    if pl < 0.0:
        pl = abs(pl)

    r = a * (1.0 - ecose)
    rdot = KE * math.sqrt(a) * esine / r
    rfdot = KE * math.sqrt(pl) / r

    betal = math.sqrt(1.0 - elsq) if elsq < 1.0 else 0.0

    cosu = (a / r) * (cosepw - axN + ayN * esine / (1.0 + betal))
    sinu = (a / r) * (sinepw - ayN - axN * esine / (1.0 + betal))
    u = math.atan2(sinu, cosu)

    sin2u = 2.0 * sinu * cosu
    cos2u = 2.0 * cosu * cosu - 1.0

    # --- Short-period periodics ---
    temp1 = XK2 / pl
    temp2 = temp1 / pl

    rk = r * (1.0 - 1.5 * temp2 * betal * init.x3thm1) + 0.5 * temp1 * init.x1mth2 * cos2u
    uk = u - 0.25 * temp2 * init.x7thm1 * sin2u
    xnodek = xnode + 1.5 * temp2 * init.cosio * sin2u
    xinck = init.i0 + 1.5 * temp2 * init.cosio * init.sinio * cos2u
    rdotk = rdot - xn * temp1 * init.x1mth2 * sin2u
    rfdotk = rfdot + xn * temp1 * (init.x1mth2 * cos2u + 1.5 * init.x3thm1)

    # --- Orientation vectors ---
    sinuk = math.sin(uk)
    cosuk = math.cos(uk)
    sinik = math.sin(xinck)
    cosik = math.cos(xinck)
    sinnok = math.sin(xnodek)
    cosnok = math.cos(xnodek)

    xmx = -sinnok * cosik
    xmy = cosnok * cosik

    ux = xmx * sinuk + cosnok * cosuk
    uy = xmy * sinuk + sinnok * cosuk
    uz = sinik * sinuk

    vx = xmx * cosuk - cosnok * sinuk
    vy = xmy * cosuk - sinnok * sinuk
    vz = sinik * cosuk

    # --- Position (km) and velocity (km/s) ---
    x = rk * ux * RE
    y = rk * uy * RE
    z = rk * uz * RE

    xdot = rdotk * ux + rfdotk * vx
    ydot = rdotk * uy + rfdotk * vy
    zdot = rdotk * uz + rfdotk * vz

    vfactor = RE / 60.0
    vx_out = xdot * vfactor
    vy_out = ydot * vfactor
    vz_out = zdot * vfactor

    return PropagationResult(x=x, y=y, z=z, vx=vx_out, vy=vy_out, vz=vz_out)
