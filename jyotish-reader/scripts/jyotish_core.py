#!/usr/bin/env python3
"""
jyotish_core.py — pure sidereal-astronomy functions shared by compute_chart.py
(natal readings) and the astro-market ephemeris build.

No database code, no argparse, no I/O. Every function is deterministic given
its arguments. Conventions (fixed; recorded per row by any consumer):
  - Ephemeris: Swiss Ephemeris built-in Moshier (no .se1 files) — EPHE_LABEL
  - Ayanamsa: Lahiri — AYANAMSA_LABEL
  - Houses: whole sign (lagna sign = house 1)
  - Nodes: BOTH mean and true are available; Ketu = Rahu + 180

Sections
  1. constants + small helpers (sign, nakshatra, dms)
  2. instant -> UT  (IANA tz | fixed UTC offset | LMT from longitude)
  3. positions      (Sun..Saturn, mean + true node, asc/MC, speed, retro, combustion)
  4. panchanga      (tithi, paksha, yoga, karana, vara, Moon nakshatra)
  5. relationships  (sign/degree conjunctions, graha-yuddha, Vedic aspects, houses from Moon)
  6. event finders  (eclipses, stations, Sankranti, lunations, ingresses, Jupiter-Saturn)

Event instants are UT Julian days refined by bisection to < 0.1 s of the
(Moshier) ephemeris, or taken straight from swe's eclipse search.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

CORE_VERSION = "1.0.0"
EPHE_LABEL = "moshier"
AYANAMSA_LABEL = "lahiri"

# --------------------------------------------------------------------------- #
# 1. Constants and small helpers
# --------------------------------------------------------------------------- #

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

# (display name, swe constant) as used by the natal reader. Rahu = MEAN node.
PLANETS = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY),
    ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN),
    ("Rahu", swe.MEAN_NODE),
]

# Bodies for mundane / ephemeris work: both node types.
BODIES = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
    "Rahu_mean": swe.MEAN_NODE, "Rahu_true": swe.TRUE_NODE,
}
GRAHAS_7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
STAR_PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]  # tara grahas

# Sidereal flags for position-only scans (set_sid_mode must be set first).
SID_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_MOSEPH
# Sidereal flags with speed — the natal reader's flag set.
SID_SPEED_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_MOSEPH
TROP_SPEED_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_MOSEPH
ECL_FLAGS = swe.FLG_MOSEPH

_INIT = False


def init():
    """Moshier ephemeris + Lahiri sidereal mode. Idempotent."""
    global _INIT
    swe.set_ephe_path(None)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    _INIT = True


def _ensure():
    if not _INIT:
        init()


def parse_date(s):
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {s!r} (use YYYY-MM-DD or DD-MM-YYYY)")


def parse_time(s):
    s = s.strip()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M", "%I.%M %p"):
        try:
            t = datetime.strptime(s, fmt)
            return t.hour, t.minute
        except ValueError:
            continue
    raise ValueError(f"Unrecognized time format: {s!r} (use 'HH:MM AM/PM' or 'HH:MM')")


def sign_index(lon):
    return int(lon // 30) % 12


def deg_in_sign(lon):
    return lon % 30


def fmt_dms(deg):
    d = int(deg)
    m_full = (deg - d) * 60
    m = int(m_full)
    s = int((m_full - m) * 60)
    return f"{d:02d}°{m:02d}'{s:02d}\""


def nakshatra_index(lon):
    return int(lon // (360.0 / 27.0)) % 27


def nakshatra_pada(lon):
    # Each nakshatra spans 13°20' = 13.3333°; each pada = 3°20' = 3.3333°.
    span = 360.0 / 27.0
    idx = int(lon // span) % 27
    within = lon - idx * span
    pada = int(within // (span / 4.0)) + 1
    return NAKSHATRAS[idx], pada


def norm360(x):
    return x % 360.0


def angdist(a, b):
    """Shortest arc between two longitudes, 0..180."""
    d = abs((a - b) % 360.0)
    return 360.0 - d if d > 180.0 else d


def signed_diff(a, b):
    """a - b wrapped to (-180, 180]."""
    d = (a - b) % 360.0
    return d - 360.0 if d > 180.0 else d


# --------------------------------------------------------------------------- #
# 2. Instant -> UT
# --------------------------------------------------------------------------- #

def lmt_offset(lon_deg):
    """Local Mean Time offset from longitude (east positive): lon/15 hours."""
    return timedelta(seconds=lon_deg * 240.0)


def fmt_offset(td):
    """timedelta -> '+H:MM:SS' / '-H:MM:SS' (seconds truncated toward zero)."""
    total = td.total_seconds()
    sign = "-" if total < 0 else "+"
    t = int(abs(total))
    return f"{sign}{t // 3600}:{(t % 3600) // 60:02d}:{t % 60:02d}"


def parse_utc_offset(s):
    """'-05:00', '+5:30', '-4:56:02', '-5' -> timedelta."""
    s = s.strip()
    sign = -1 if s.startswith("-") else 1
    parts = [float(p) for p in s.lstrip("+-").split(":")]
    while len(parts) < 3:
        parts.append(0.0)
    h, m, sec = parts
    return sign * timedelta(hours=h, minutes=m, seconds=sec)


def to_utc(year, month, day, hour=0, minute=0, second=0, *, tz=None,
           utc_offset=None, lmt_lon=None):
    """Civil instant -> aware UTC datetime. Exactly one of tz / utc_offset /
    lmt_lon must be given.
      tz         IANA name (zoneinfo; handles DST and pre-1883 LMT for that zone)
      utc_offset timedelta or string like '-05:00'
      lmt_lon    longitude (east +) for Local Mean Time
    Returns (utc_datetime, offset_timedelta, method_label).
    Nonexistent / ambiguous local times follow zoneinfo's fold=0 rule.
    """
    given = [x is not None for x in (tz, utc_offset, lmt_lon)]
    if sum(given) != 1:
        raise ValueError("give exactly one of tz, utc_offset, lmt_lon")
    if tz is not None:
        local = datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo(tz))
        method = f"tz:{tz}"
    else:
        if lmt_lon is not None:
            off = lmt_offset(lmt_lon)
            method = f"lmt:{lmt_lon}"
        else:
            off = parse_utc_offset(utc_offset) if isinstance(utc_offset, str) else utc_offset
            method = f"offset:{fmt_offset(off)}"
        local = datetime(year, month, day, hour, minute, second, tzinfo=timezone(off))
    utc = local.astimezone(ZoneInfo("UTC"))
    return utc, local.utcoffset(), method


def jd_from_utc(utc):
    """Aware UTC datetime -> Julian day (UT). Same arithmetic as compute_chart."""
    ut_hours = utc.hour + utc.minute / 60.0 + utc.second / 3600.0
    if utc.microsecond:
        ut_hours += utc.microsecond / 3.6e9
    return swe.julday(utc.year, utc.month, utc.day, ut_hours, swe.GREG_CAL)


def jd_to_date(jd):
    """Julian day -> 'YYYY-MM-DD' (UTC, day precision)."""
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{y:04d}-{m:02d}-{d:02d}"


def jd_to_datetime(jd):
    """Julian day (UT) -> aware UTC datetime, rounded to the second."""
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    base = datetime(y, m, d, tzinfo=timezone.utc)
    return base + timedelta(seconds=round(h * 3600.0))


def jd_to_iso(jd):
    return jd_to_datetime(jd).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# 3. Positions
# --------------------------------------------------------------------------- #

def planet_lon(jd, code):
    """Sidereal longitude (deg) of a body at a given Julian day."""
    _ensure()
    return swe.calc_ut(jd, code, SID_FLAGS)[0][0]


def planet_speed(jd, code):
    _ensure()
    return swe.calc_ut(jd, code, SID_SPEED_FLAGS)[0][3]


def ayanamsa(jd):
    _ensure()
    return swe.get_ayanamsa_ut(jd)


def ascendant_mc(jd, lat, lon, flags=SID_SPEED_FLAGS):
    """Sidereal ascendant and MC longitudes (whole-sign: lagna = sign of asc)."""
    _ensure()
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', flags)
    return ascmc[0], ascmc[1]


def body_raw(jd, code, flags=SID_SPEED_FLAGS):
    """(lon, lat, speed_lon) straight from swe.calc_ut."""
    _ensure()
    res = swe.calc_ut(jd, code, flags)
    return res[0][0], res[0][1], res[0][3]


def describe_lon(lon):
    sidx = sign_index(lon)
    nak, pada = nakshatra_pada(lon)
    return {"sign_idx": sidx, "sign": SIGNS[sidx], "deg_in_sign": deg_in_sign(lon),
            "nakshatra_idx": nakshatra_index(lon), "nakshatra": nak, "pada": pada}


# Classical combustion orbs (degrees from the Sun) — Surya Siddhanta / Phaladeepika
# convention; Mercury and Venus use the smaller orb when retrograde.
COMBUST_ORB = {"Moon": 12.0, "Mars": 17.0, "Mercury": 14.0, "Jupiter": 11.0,
               "Venus": 10.0, "Saturn": 15.0}
COMBUST_ORB_RETRO = {"Mercury": 12.0, "Venus": 8.0}


def is_combust(name, lon, sun_lon, retrograde=False):
    if name not in COMBUST_ORB:
        return False
    orb = COMBUST_ORB_RETRO.get(name, COMBUST_ORB[name]) if retrograde else COMBUST_ORB[name]
    return angdist(lon, sun_lon) <= orb


def positions(jd, bodies=None, tropical=True):
    """Dict body -> full record at jd. bodies: names from BODIES (default all);
    'Ketu_mean'/'Ketu_true' are derived and always added for each node present.
    retrograde = speed < 0 (true node can be direct; mean node never is)."""
    _ensure()
    names = list(BODIES) if bodies is None else list(bodies)
    out = {}
    for name in names:
        code = BODIES[name]
        lon, lat, spd = body_raw(jd, code)
        rec = {"lon": lon, "lat": lat, "speed": spd, "retrograde": spd < 0}
        if tropical:
            rec["lon_tropical"] = body_raw(jd, code, TROP_SPEED_FLAGS)[0]
        rec.update(describe_lon(lon))
        out[name] = rec
        if name.startswith("Rahu_"):
            k = "Ketu_" + name.split("_", 1)[1]
            klon = (lon + 180.0) % 360.0
            krec = {"lon": klon, "lat": -lat, "speed": spd, "retrograde": spd < 0}
            if tropical:
                krec["lon_tropical"] = (rec["lon_tropical"] + 180.0) % 360.0
            krec.update(describe_lon(klon))
            out[k] = krec
    if "Sun" in out:
        sun = out["Sun"]["lon"]
        for name, rec in out.items():
            rec["combust"] = is_combust(name, rec["lon"], sun, rec["retrograde"])
    return out


# --------------------------------------------------------------------------- #
# 4. Panchanga
# --------------------------------------------------------------------------- #

TITHI_NAMES = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
               "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
               "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi"]
YOGA_NAMES = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
              "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi",
              "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
              "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
              "Shukla", "Brahma", "Indra", "Vaidhriti"]
KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
VARA = [("Sunday", "Sun"), ("Monday", "Moon"), ("Tuesday", "Mars"),
        ("Wednesday", "Mercury"), ("Thursday", "Jupiter"), ("Friday", "Venus"),
        ("Saturday", "Saturn")]


def tithi_name(n):
    """n = 1..30."""
    if n == 15:
        return "Purnima"
    if n == 30:
        return "Amavasya"
    return TITHI_NAMES[(n - 1) % 15]


def karana_name(k):
    """k = 0..59 half-tithi index from the new moon."""
    if k == 0:
        return "Kimstughna"
    if k >= 57:
        return ["Shakuni", "Chatushpada", "Naga"][k - 57]
    return KARANA_MOVABLE[(k - 1) % 7]


def sunrise_before(jd, lat, lon, alt=0.0):
    """UT JD of the last sunrise at or before jd (disc-centre convention with
    refraction, swe default). None in polar day/night."""
    _ensure()
    geo = (lon, lat, alt)
    for back in (1.0, 2.0, 3.0):
        res, tret = swe.rise_trans(jd - back, swe.SUN, swe.CALC_RISE, geo, 0.0, 0.0,
                                   swe.FLG_MOSEPH)
        if res == 0 and tret[0] <= jd:
            # walk forward to the latest rise still <= jd
            t = tret[0]
            while True:
                r2, t2 = swe.rise_trans(t + 0.01, swe.SUN, swe.CALC_RISE, geo, 0.0, 0.0,
                                        swe.FLG_MOSEPH)
                if r2 != 0 or t2[0] > jd:
                    return t
                t = t2[0]
    return None


def weekday_index(jd_ut, lon):
    """0=Sunday.. of the local-mean-time civil date containing jd_ut."""
    return int(jd_ut + lon / 360.0 + 1.5) % 7


def panchanga(jd, lat=None, lon=None, pos=None):
    """Five limbs at instant jd (UT). If lat/lon given, vara is the weekday of
    the last local sunrise (Vedic day runs sunrise to sunrise); otherwise vara
    is the UT civil weekday and vara_basis says so."""
    _ensure()
    if pos is None:
        sun_lon, moon_lon = planet_lon(jd, swe.SUN), planet_lon(jd, swe.MOON)
    else:
        sun_lon, moon_lon = pos["Sun"]["lon"], pos["Moon"]["lon"]
    elong = (moon_lon - sun_lon) % 360.0
    t_idx = int(elong // 12.0)
    tithi = t_idx + 1
    k_idx = int(elong // 6.0)
    y_sum = (sun_lon + moon_lon) % 360.0
    y_idx = int(y_sum // (360.0 / 27.0)) % 27
    nak, pada = nakshatra_pada(moon_lon)
    out = {
        "sun_moon_angle": elong,
        "tithi": tithi,
        "tithi_name": tithi_name(tithi),
        "tithi_pct_elapsed": (elong - t_idx * 12.0) / 12.0 * 100.0,
        "paksha": "Shukla" if tithi <= 15 else "Krishna",
        "yoga": y_idx + 1,
        "yoga_name": YOGA_NAMES[y_idx],
        "karana": k_idx + 1,
        "karana_name": karana_name(k_idx),
        "moon_nakshatra": nak,
        "moon_nakshatra_idx": nakshatra_index(moon_lon),
        "moon_pada": pada,
    }
    if lat is not None and lon is not None:
        sr = sunrise_before(jd, lat, lon)
        if sr is not None:
            w = weekday_index(sr, lon)
            out.update(vara=VARA[w][0], vara_lord=VARA[w][1], vara_basis="sunrise",
                       sunrise_ut=jd_to_iso(sr))
            return out
        w = weekday_index(jd, lon)
        out.update(vara=VARA[w][0], vara_lord=VARA[w][1], vara_basis="lmt-civil")
        return out
    w = weekday_index(jd, 0.0)
    out.update(vara=VARA[w][0], vara_lord=VARA[w][1], vara_basis="ut-civil")
    return out


# --------------------------------------------------------------------------- #
# 5. Relationships
# --------------------------------------------------------------------------- #

# Vedic special aspects (counted inclusively by sign); every graha aspects the 7th.
SPECIAL_ASPECTS = {"Mars": (4, 7, 8), "Jupiter": (5, 7, 9), "Saturn": (3, 7, 10)}
ASPECTING = GRAHAS_7  # nodes excluded (no consensus on node drishti)


def relationships(pos, node="mean", conj_orb=10.0, yuddha_orb=1.0):
    """pos = positions(...) output. node selects which Rahu/Ketu pair is used.
    Returns sign conjunctions, degree conjunctions (<= conj_orb), graha-yuddha
    (< yuddha_orb between two of Mars..Saturn; winner = more northerly ecliptic
    latitude, Surya Siddhanta 7), Vedic aspects (sign-based), houses from Moon."""
    names = GRAHAS_7 + [f"Rahu_{node}", f"Ketu_{node}"]
    names = [n for n in names if n in pos]
    by_sign = {}
    for n in names:
        by_sign.setdefault(pos[n]["sign_idx"], []).append(n)
    sign_conj = [{"sign": SIGNS[s], "bodies": b} for s, b in sorted(by_sign.items()) if len(b) > 1]

    deg_conj, yuddha = [], []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} == {f"Rahu_{node}", f"Ketu_{node}"}:
                continue
            sep = angdist(pos[a]["lon"], pos[b]["lon"])
            if sep <= conj_orb:
                deg_conj.append({"a": a, "b": b, "sep": sep})
            if a in STAR_PLANETS and b in STAR_PLANETS and sep < yuddha_orb:
                winner = a if pos[a]["lat"] >= pos[b]["lat"] else b
                yuddha.append({"a": a, "b": b, "sep": sep, "winner_by_latitude": winner})

    aspects = []
    for a in ASPECTING:
        if a not in pos:
            continue
        for nth in SPECIAL_ASPECTS.get(a, (7,)):
            tgt = (pos[a]["sign_idx"] + nth - 1) % 12
            for b in names:
                if b != a and pos[b]["sign_idx"] == tgt:
                    aspects.append({"from": a, "to": b, "nth": nth})

    moon_sign = pos["Moon"]["sign_idx"]
    from_moon = {n: ((pos[n]["sign_idx"] - moon_sign) % 12) + 1 for n in names}
    return {"node": node, "sign_conjunctions": sign_conj, "degree_conjunctions": deg_conj,
            "graha_yuddha": yuddha, "aspects": aspects, "houses_from_moon": from_moon}


# --------------------------------------------------------------------------- #
# 6. Event finders. All take (start_jd, end_jd) in UT and return lists of
#    {"type", "body", "jd", "ut", ...} sorted by jd.
# --------------------------------------------------------------------------- #

_TOL = 1e-6  # days (~0.09 s)


def _bisect(f, lo, hi, lo_val):
    """f(jd) is a discrete key; find the instant it leaves lo_val in (lo, hi]."""
    while hi - lo > _TOL:
        mid = (lo + hi) / 2.0
        if f(mid) == lo_val:
            lo = mid
        else:
            hi = mid
    return hi


def _scan(f, start, end, step):
    """Yield (jd, old_key, new_key) for each change of discrete key f."""
    jd = start
    prev = f(jd)
    while jd < end:
        nxt = min(jd + step, end)
        k = f(nxt)
        if k != prev:
            t = _bisect(f, jd, nxt, prev)
            yield t, prev, f(t)
            # resume just after the change, re-reading the key (handles 2 changes/step)
            jd, prev = t, f(t)
            continue
        jd, prev = nxt, k


def _ev(typ, body, jd, **kw):
    d = {"type": typ, "body": body, "jd": jd, "ut": jd_to_iso(jd)}
    d.update(kw)
    return d


_SOLAR_TYPES = [(swe.ECL_ANNULAR_TOTAL, "hybrid"), (swe.ECL_TOTAL, "total"),
                (swe.ECL_ANNULAR, "annular"), (swe.ECL_PARTIAL, "partial")]
_LUNAR_TYPES = [(swe.ECL_TOTAL, "total"), (swe.ECL_PARTIAL, "partial"),
                (swe.ECL_PENUMBRAL, "penumbral")]


def _ecl_type(flag, table):
    for bit, label in table:
        if flag & bit == bit:
            return label
    return "unknown"


def solar_eclipses(start, end, geopos=None):
    """Global solar eclipses with max in [start, end) from Sun-Moon geometry
    (swe.sol_eclipse_when_glob). geopos=(lon, lat, alt) adds local magnitude
    (fraction of solar diameter covered; 0 = not visible there)."""
    _ensure()
    out, t = [], start
    while True:
        flag, tret = swe.sol_eclipse_when_glob(t, ECL_FLAGS, 0, False)
        tmax = tret[0]
        if tmax >= end:
            break
        sun = planet_lon(tmax, swe.SUN)
        ev = _ev("solar_eclipse", "Sun", tmax, eclipse_type=_ecl_type(flag, _SOLAR_TYPES),
                 central=bool(flag & swe.ECL_CENTRAL), sun_lon=sun, **_lon_tags(sun))
        if geopos is not None:
            ev.update(_solar_local(tmax, geopos))
        out.append(ev)
        t = tmax + 20.0
    return out


def _solar_local(tmax, geopos):
    """Local circumstances: local maximum within +/-0.5 d of the global maximum.
    local_magnitude = fraction of solar diameter covered (0 = not seen there)."""
    lf, tret, attr = swe.sol_eclipse_when_loc(tmax - 0.5, geopos, ECL_FLAGS, False)
    if lf and abs(tret[0] - tmax) < 0.5 and lf & swe.ECL_VISIBLE:
        return {"local_max_ut": jd_to_iso(tret[0]), "local_magnitude": attr[0],
                "local_max_visible": bool(lf & swe.ECL_MAX_VISIBLE)}
    return {"local_max_ut": None, "local_magnitude": 0.0, "local_max_visible": False}


def lunar_eclipses(start, end):
    """Lunar eclipses (incl. penumbral) with max in [start, end)."""
    _ensure()
    out, t = [], start
    while True:
        flag, tret = swe.lun_eclipse_when(t, ECL_FLAGS, 0, False)
        tmax = tret[0]
        if tmax >= end:
            break
        moon = planet_lon(tmax, swe.MOON)
        out.append(_ev("lunar_eclipse", "Moon", tmax,
                       eclipse_type=_ecl_type(flag, _LUNAR_TYPES), moon_lon=moon,
                       **_lon_tags(moon)))
        t = tmax + 20.0
    return out


def _lon_tags(lon):
    nak, pada = nakshatra_pada(lon)
    return {"sign": SIGNS[sign_index(lon)], "nakshatra": nak, "pada": pada}


def stations(start, end, bodies=("Mercury", "Venus", "Mars", "Jupiter", "Saturn")):
    """Retrograde / direct stations: instants where longitudinal speed = 0."""
    _ensure()
    out = []
    for name in bodies:
        code = BODIES[name]
        f = lambda jd, c=code: planet_speed(jd, c) < 0
        for t, old, new in _scan(f, start, end, 1.0):
            lon = planet_lon(t, code)
            out.append(_ev("station_retrograde" if new else "station_direct", name, t,
                           lon=lon, **_lon_tags(lon)))
    return sorted(out, key=lambda e: e["jd"])


_INGRESS_STEP = {"Moon": 0.25, "Rahu_true": 0.25, "Rahu_mean": 1.0}


def ingresses(start, end, bodies=("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                                  "Saturn", "Rahu_mean", "Rahu_true")):
    """Sidereal sign ingresses (incl. retrograde re-entries). Ketu = Rahu + 6 signs."""
    _ensure()
    out = []
    for name in bodies:
        code = BODIES[name]
        f = lambda jd, c=code: sign_index(planet_lon(jd, c))
        for t, old, new in _scan(f, start, end, _INGRESS_STEP.get(name, 1.0)):
            out.append(_ev("ingress", name, t, from_sign=SIGNS[old], to_sign=SIGNS[new]))
    return sorted(out, key=lambda e: e["jd"])


def sankrantis(start, end):
    """Sidereal (Lahiri) Sun ingresses; named by the sign entered."""
    out = []
    for e in ingresses(start, end, bodies=("Sun",)):
        e["type"] = "sankranti"
        e["name"] = f"{e['to_sign']} Sankranti"
        out.append(e)
    return out


def _elong_half(jd):
    return int(((planet_lon(jd, swe.MOON) - planet_lon(jd, swe.SUN)) % 360.0) // 180.0)


def lunations(start, end):
    """New moons (elongation 0) and full moons (180)."""
    _ensure()
    out = []
    for t, old, new in _scan(_elong_half, start, end, 1.0):
        moon = planet_lon(t, swe.MOON)
        out.append(_ev("new_moon" if new == 0 else "full_moon", "Moon", t,
                       moon_lon=moon, **_lon_tags(moon)))
    return out


def conjunctions(start, end, a="Jupiter", b="Saturn", step=5.0):
    """Exact longitude conjunctions of two bodies (retrograde triples included)."""
    _ensure()
    ca, cb = BODIES[a], BODIES[b]

    def f(jd):
        d = signed_diff(planet_lon(jd, ca), planet_lon(jd, cb))
        # bucket: near 0 -> sign of d; far side -> constant so the 180 wrap is ignored
        return 2 if abs(d) > 90.0 else (1 if d >= 0 else 0)

    out = []
    for t, old, new in _scan(f, start, end, step):
        if {old, new} == {0, 1}:
            lon = planet_lon(t, ca)
            out.append(_ev("conjunction", f"{a}-{b}", t, lon=lon, **_lon_tags(lon)))
    return out


EVENT_FINDERS = {
    "solar_eclipse": solar_eclipses,
    "lunar_eclipse": lunar_eclipses,
    "station": stations,
    "sankranti": sankrantis,
    "lunation": lunations,
    "ingress": ingresses,
    "jupiter_saturn": conjunctions,
}


def find_events(start, end, kinds=None, geopos=None):
    """geopos=(lon, lat, alt) adds local solar-eclipse circumstances."""
    kinds = list(EVENT_FINDERS) if not kinds else kinds
    out = []
    for k in kinds:
        if k == "solar_eclipse":
            out.extend(solar_eclipses(start, end, geopos))
        else:
            out.extend(EVENT_FINDERS[k](start, end))
    return sorted(out, key=lambda e: (e["jd"], e["type"], e["body"]))


# --------------------------------------------------------------------------- #
# Convenience: a full mundane snapshot at one instant
# --------------------------------------------------------------------------- #

def snapshot(jd, lat=None, lon=None, node="mean", conj_orb=10.0):
    pos = positions(jd)
    out = {"jd": jd, "ut": jd_to_iso(jd), "ayanamsa": ayanamsa(jd), "ephe": EPHE_LABEL,
           "positions": pos, "panchanga": panchanga(jd, lat, lon, pos=pos),
           "relationships": relationships(pos, node=node, conj_orb=conj_orb)}
    if lat is not None and lon is not None:
        asc, mc = ascendant_mc(jd, lat, lon)
        out["ascendant"] = dict(lon=asc, **describe_lon(asc))
        out["mc"] = dict(lon=mc, **describe_lon(mc))
    return out
