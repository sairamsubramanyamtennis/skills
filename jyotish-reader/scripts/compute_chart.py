#!/usr/bin/env python3
"""
compute_chart.py — Sidereal Vedic chart computation for the jyotish-reader skill.

Uses Swiss Ephemeris (pyswisseph) with:
  - Lahiri ayanamsa (sidereal)
  - Whole Sign houses (Lagna sign = house 1)
  - Moshier built-in ephemeris (no external ephemeris data files needed)

Outputs D1 (Rasi) with nakshatra, pada, house, and retrograde status, any
requested divisional (varga) charts, the Vimshottari dasha sequence
(mahadasha + antardasha, dated, with the period active as of --asof), the full
Sade Sati cycle table across the lifespan (rising/peak/setting phase dates, plus
Kantaka/Ashtama Dhaiyya windows), and current slow-mover transits.

Install once (pinned, recommended — see SETUP.md):
    py -3.11 -m venv .venv          # 3.11 has prebuilt Windows wheels
    .venv/Scripts/python -m pip install -r scripts/requirements.txt
Or run scripts/run_chart.ps1, which creates/repairs that venv automatically.

Quick install (if your Python already has a pyswisseph wheel):
    pip install pyswisseph tzdata
    (Linux PEP-668: add --break-system-packages. tzdata is required on Windows.)

Usage:
    python3 compute_chart.py \\
      --name "Native" --date 1990-08-15 --time "09:42 AM" \\
      --lat 13.0827 --lon 80.2707 --tz Asia/Kolkata \\
      --varga D1,D3,D9,D7,D10,D12

Notes:
  - --date accepts YYYY-MM-DD or DD-MM-YYYY.
  - --time accepts "HH:MM AM/PM" or 24h "HH:MM".
  - You must supply latitude, longitude, and an IANA timezone for the birth place
    (geocode the city beforehand if only a place name is known).
  - Add --json for machine-readable output.
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import swisseph as swe
except ImportError:
    sys.stderr.write(
        "ERROR: pyswisseph not installed.\n"
        "Run: pip install pyswisseph\n"
        "(On PEP-668 Linux, add --break-system-packages.)\n"
    )
    sys.exit(1)

# Pure astronomy (constants, parsing, sign/nakshatra helpers, instant->UT,
# positions) lives in jyotish_core.py, shared with the astro-market build.
import jyotish_core as core
from jyotish_core import (  # noqa: F401  (re-exported for existing importers)
    SIGNS, NAKSHATRAS, PLANETS, SID_FLAGS, parse_date, parse_time, sign_index,
    deg_in_sign, fmt_dms, nakshatra_pada, planet_lon, jd_to_date,
)

# Vimshottari dasha: 9 lords in fixed order with their period lengths (years).
# Total cycle = 120 years. The lord of the Moon's birth nakshatra starts the
# sequence; nakshatra index mod 9 selects the starting lord.
DAYS_PER_YEAR = 365.25  # Vimshottari convention (solar year)
DASHA_SEQ = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
    ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
]



def varga_sign(lon, division):
    """Return sidereal longitude (sign-aligned) for a divisional chart.

    Standard Parashari rules for the commonly used vargas.
    """
    sidx = sign_index(lon)
    d = deg_in_sign(lon)

    if division == 1:  # D1 Rasi
        result_sign = sidx

    elif division == 3:  # D3 Drekkana (siblings/co-borns)
        # 1st third -> same sign; 2nd third -> 5th from it; 3rd third -> 9th from it.
        part = int(d // 10.0)  # 0..2
        result_sign = (sidx + [0, 4, 8][part]) % 12

    elif division == 9:  # D9 Navamsha
        part = int(d // (30.0 / 9))  # 0..8
        # Movable->from same sign; Fixed->from 9th; Dual->from 5th. Equivalent:
        result_sign = (sidx * 9 + part) % 12

    elif division == 7:  # D7 Saptamsha
        part = int(d // (30.0 / 7))  # 0..6
        if sidx % 2 == 0:  # odd sign (Aries=0 is odd-numbered 1st sign)
            result_sign = (sidx + part) % 12
        else:
            result_sign = (sidx + 6 + part) % 12

    elif division == 10:  # D10 Dashamsha
        part = int(d // 3.0)  # 0..9
        if sidx % 2 == 0:
            result_sign = (sidx + part) % 12
        else:
            result_sign = (sidx + 8 + part) % 12

    elif division == 4:  # D4 Chaturthamsha (4 parts of 7°30'; the kendras from sign)
        part = int(d // 7.5)  # 0..3
        result_sign = (sidx + [0, 3, 6, 9][part]) % 12

    elif division == 12:  # D12 Dwadashamsha
        part = int(d // 2.5)  # 0..11
        result_sign = (sidx + part) % 12

    elif division == 16:  # D16 Shodashamsha
        part = int(d // (30.0 / 16))
        movable = [0, 3, 6, 9]
        fixed = [1, 4, 7, 10]
        if sidx in movable:
            start = 0      # Aries
        elif sidx in fixed:
            start = 4      # Leo
        else:
            start = 8      # Sagittarius
        result_sign = (start + part) % 12

    else:
        raise ValueError(
            f"Divisional chart D{division} is not implemented. "
            "Supported: D1, D3, D4, D7, D9, D10, D12, D16. "
            "(Previously this silently returned the D1 chart.)"
        )

    # Return a representative longitude in the middle of the resulting sign.
    return result_sign * 30 + 15.0


# --------------------------------------------------------------------------- #
# Time-domain helpers (Vimshottari dasha, Sade Sati). These assume
# swe.set_sid_mode(SIDM_LAHIRI) and swe.set_ephe_path(None) have already run.
# --------------------------------------------------------------------------- #

def vimshottari_dasha(birth_jd, moon_lon, dasha_years, asof_jd):
    """Return the Vimshottari mahadasha/antardasha sequence from birth.

    Each mahadasha carries its nested antardashas (same Vimshottari order,
    duration = maha_years * antar_years / 120). The first mahadasha begins
    before birth; its pre-birth portion is clipped so the table starts at birth
    with the correct 'balance' remaining. `active` flags the period containing
    asof_jd.
    """
    span = 360.0 / 27.0
    nak_idx = int(moon_lon // span) % 27
    frac = (moon_lon - nak_idx * span) / span  # fraction of nakshatra traversed
    start_idx = nak_idx % 9

    _, first_full = DASHA_SEQ[start_idx]
    # Theoretical start of the first mahadasha (before birth by the elapsed frac).
    theo_start = birth_jd - frac * first_full * DAYS_PER_YEAR
    end_limit = birth_jd + dasha_years * DAYS_PER_YEAR

    mahas = []
    cur = theo_start
    i = start_idx
    while cur < end_limit:
        lord, full = DASHA_SEQ[i % 9]
        m_start, m_end = cur, cur + full * DAYS_PER_YEAR
        if m_end > birth_jd:  # skip any mahadasha that ends before birth
            antars = []
            a = m_start
            for k in range(9):
                alord, afull = DASHA_SEQ[(i + k) % 9]
                a_end = a + full * afull / 120.0 * DAYS_PER_YEAR
                if a_end > birth_jd:
                    eff_a = max(a, birth_jd)
                    antars.append({
                        "lord": alord,
                        "start": jd_to_date(eff_a),
                        "end": jd_to_date(a_end),
                        "active": eff_a <= asof_jd < a_end,
                    })
                a = a_end
            eff_start = max(m_start, birth_jd)
            mahas.append({
                "lord": lord,
                "start": jd_to_date(eff_start),
                "end": jd_to_date(m_end),
                "age_start": round((eff_start - birth_jd) / DAYS_PER_YEAR, 1),
                "age_end": round((m_end - birth_jd) / DAYS_PER_YEAR, 1),
                "balance": m_start < birth_jd,  # True only for the first maha
                "active": m_start <= asof_jd < m_end,
                "antardashas": antars,
            })
        cur = m_end
        i += 1
    return mahas, NAKSHATRAS[nak_idx], round(frac, 4)


def _saturn_intervals(birth_jd, end_jd, step=5.0):
    """List of (start_jd, end_jd, sign_index) for Saturn's sign occupancy.

    Scans forward in `step`-day increments (Saturn moves <0.2deg/step, so it
    cannot skip a sign) and bisects each detected boundary to ~hour precision.
    Retrograde re-entries appear as separate intervals.
    """
    events = []
    jd = birth_jd
    prev = sign_index(planet_lon(jd, swe.SATURN))
    events.append((jd, prev))
    while jd < end_jd:
        njd = min(jd + step, end_jd)
        s = sign_index(planet_lon(njd, swe.SATURN))
        if s != prev:
            lo, hi = jd, njd
            for _ in range(40):
                mid = (lo + hi) / 2.0
                if sign_index(planet_lon(mid, swe.SATURN)) == prev:
                    lo = mid
                else:
                    hi = mid
            events.append((hi, s))
            prev = s
        jd = njd
    intervals = []
    for k, (st, sg) in enumerate(events):
        en = events[k + 1][0] if k + 1 < len(events) else end_jd
        intervals.append((st, en, sg))
    return intervals


# Retrograde excursions across a sign boundary last at most a few months, whereas
# successive Sade Sati cycles are ~22 years apart (Saturn's ~29.5y return minus the
# ~7.5y the cycle itself occupies). A 2-year gap cleanly separates the two: anything
# closer is wobble to be merged, anything farther is a genuinely new cycle.
_MERGE_GAP = 2.0 * DAYS_PER_YEAR


def sade_sati(birth_jd, moon_sign, lifespan_years, asof_jd):
    """Enumerate Sade Sati cycles plus Kantaka (4th) and Ashtama (8th) Dhaiyya.

    Sade Sati = Saturn transiting the 12th, 1st, and 2nd signs from the natal
    Moon. Phases: rising (12th), peak (over Moon, 1st), setting (2nd). Each phase
    is reported from its first ingress to the next phase's first ingress, so the
    three phases are sequential and non-overlapping; brief retrograde re-entries
    are merged into the surrounding cycle rather than reported as separate cycles.
    """
    s12 = (moon_sign - 1) % 12  # 12th from Moon
    s1 = moon_sign              # over the Moon
    s2 = (moon_sign + 1) % 12   # 2nd from Moon
    s4 = (moon_sign + 3) % 12   # Kantaka Shani
    s8 = (moon_sign + 7) % 12   # Ashtama Shani
    target = {s12: "rising", s1: "peak", s2: "setting"}

    end_jd = birth_jd + lifespan_years * DAYS_PER_YEAR
    intervals = _saturn_intervals(birth_jd, end_jd)

    # Collect raw cycles as lists of (sign, start_jd, end_jd) and raw Dhaiyya hits.
    raw_cycles, raw_dhaiyya = [], []
    cur = None
    for st, en, sg in intervals:
        if sg in target:
            (cur := cur if cur is not None else []).append((sg, st, en))
        else:
            if cur:
                raw_cycles.append(cur)
                cur = None
            if sg == s4:
                raw_dhaiyya.append(["Kantaka (4th)", st, en])
            elif sg == s8:
                raw_dhaiyya.append(["Ashtama (8th)", st, en])
    if cur:
        raw_cycles.append(cur)

    # Merge cycles whose gap is below the inter-cycle threshold (retrograde wobble).
    merged = []
    for c in raw_cycles:
        if merged and c[0][1] - merged[-1][-1][2] < _MERGE_GAP:
            merged[-1].extend(c)
        else:
            merged.append(c)

    out = []
    for cyc in merged:
        c_start = min(s for _, s, _ in cyc)
        c_end = max(e for _, _, e in cyc)
        # First ingress into each phase's sign, in chronological order.
        ingress = {}
        for sg, s, _ in cyc:
            ph = target[sg]
            if ph not in ingress or s < ingress[ph]:
                ingress[ph] = s
        present = sorted(ingress.items(), key=lambda kv: kv[1])
        phases = {}
        for i, (ph, ing) in enumerate(present):
            nxt = present[i + 1][1] if i + 1 < len(present) else c_end
            phases[ph] = {"start": jd_to_date(ing), "end": jd_to_date(nxt)}
        out.append({
            "start": jd_to_date(c_start),
            "end": jd_to_date(c_end),
            "age_start": round((c_start - birth_jd) / DAYS_PER_YEAR, 1),
            "age_end": round((c_end - birth_jd) / DAYS_PER_YEAR, 1),
            "active": c_start <= asof_jd < c_end,
            "phases": phases,
        })

    # Merge consecutive same-type Dhaiyya windows separated by retrograde wobble.
    dhaiyya = []
    for typ, st, en in raw_dhaiyya:
        if dhaiyya and dhaiyya[-1]["type"] == typ and st - dhaiyya[-1]["_end"] < _MERGE_GAP:
            dhaiyya[-1]["_end"] = max(dhaiyya[-1]["_end"], en)
            dhaiyya[-1]["end"] = jd_to_date(dhaiyya[-1]["_end"])
        else:
            dhaiyya.append({
                "type": typ, "start": jd_to_date(st), "end": jd_to_date(en),
                "age_start": round((st - birth_jd) / DAYS_PER_YEAR, 1), "_end": en,
            })
    for d in dhaiyya:
        d.pop("_end", None)

    return out, dhaiyya


def transits_asof(asof_jd, lagna_sign, moon_sign):
    """Current sidereal positions of the slow movers used in transit analysis."""
    s12, s1, s2 = (moon_sign - 1) % 12, moon_sign, (moon_sign + 1) % 12
    rows = []
    movers = [("Saturn", swe.SATURN), ("Jupiter", swe.JUPITER),
              ("Rahu", swe.MEAN_NODE)]
    for name, code in movers:
        lon = planet_lon(asof_jd, code)
        if name == "Rahu":
            entries = [("Rahu", lon), ("Ketu", (lon + 180.0) % 360.0)]
        else:
            entries = [(name, lon)]
        for label, l in entries:
            sidx = sign_index(l)
            row = {
                "planet": label,
                "sign": SIGNS[sidx],
                "degree": fmt_dms(deg_in_sign(l)),
                "house_from_lagna": ((sidx - lagna_sign) % 12) + 1,
                "from_moon": ((sidx - moon_sign) % 12) + 1,
            }
            if label == "Saturn":
                row["sade_sati_phase"] = (
                    "rising (12th)" if sidx == s12 else
                    "peak (over Moon)" if sidx == s1 else
                    "setting (2nd)" if sidx == s2 else "not in Sade Sati")
            rows.append(row)
    return rows


def _tz_kwargs(args):
    """Exactly one of --tz / --utc-offset / --lmt (LMT uses --lon)."""
    if getattr(args, "lmt", False):
        return {"lmt_lon": args.lon}
    if getattr(args, "utc_offset", None):
        return {"utc_offset": args.utc_offset}
    return {"tz": args.tz}


def compute(args):
    core.init()  # built-in Moshier ephemeris + Lahiri sidereal mode
    flags = core.SID_SPEED_FLAGS

    dt = parse_date(args.date)
    hh, mm = parse_time(args.time)
    utc, _, _ = core.to_utc(dt.year, dt.month, dt.day, hh, mm, **_tz_kwargs(args))
    jd = core.jd_from_utc(utc)

    # Ascendant (sidereal) via houses_ex; whole-sign => Lagna = sign of ascendant.
    asc_lon, _mc = core.ascendant_mc(jd, args.lat, args.lon, flags)
    lagna_sign = sign_index(asc_lon)

    bodies = []
    for name, code in PLANETS:
        lon, _lat, speed = core.body_raw(jd, code, flags)
        retro = speed < 0
        if name == "Rahu":
            bodies.append(("Rahu", lon, True))   # nodes always retrograde
            ketu_lon = (lon + 180.0) % 360.0
            bodies.append(("Ketu", ketu_lon, True))
        else:
            bodies.append((name, lon, retro))

    def house_from_lagna(sidx):
        return ((sidx - lagna_sign) % 12) + 1

    d1 = {
        "lagna": {
            "sign": SIGNS[lagna_sign],
            "degree": fmt_dms(deg_in_sign(asc_lon)),
            "nakshatra": nakshatra_pada(asc_lon)[0],
            "pada": nakshatra_pada(asc_lon)[1],
        },
        "planets": [],
    }
    for name, lon, retro in bodies:
        sidx = sign_index(lon)
        nak, pada = nakshatra_pada(lon)
        d1["planets"].append({
            "planet": name,
            "sign": SIGNS[sidx],
            "degree": fmt_dms(deg_in_sign(lon)),
            "house": house_from_lagna(sidx),
            "nakshatra": nak,
            "pada": pada,
            "retrograde": retro,
        })

    vargas = {}
    requested = [v.strip().upper() for v in args.varga.split(",")] if args.varga else ["D1"]
    div_map = {"D1": 1, "D3": 3, "D4": 4, "D9": 9, "D7": 7,
               "D10": 10, "D12": 12, "D16": 16}
    for v in requested:
        if v == "D1":
            continue
        n = div_map.get(v)
        if not n:
            raise SystemExit(
                f"ERROR: unknown divisional chart '{v}'. "
                f"Supported: {', '.join(sorted(div_map))}."
            )
        # Compute varga lagna and varga sign for each body.
        vlagna_sign = sign_index(varga_sign(asc_lon, n))
        plist = []
        for name, lon, retro in bodies:
            vsidx = sign_index(varga_sign(lon, n))
            plist.append({
                "planet": name,
                "sign": SIGNS[vsidx],
                "house": ((vsidx - vlagna_sign) % 12) + 1,
                "retrograde": retro,
            })
        vargas[v] = {"lagna_sign": SIGNS[vlagna_sign], "planets": plist}

    out = {
        "name": args.name,
        "ayanamsa": "Lahiri (sidereal)",
        "house_system": "Whole Sign",
        "birth_utc": utc.strftime("%Y-%m-%d %H:%M UTC"),
        "julian_day": round(jd, 6),
        "D1": d1,
        "vargas": vargas,
    }

    # --- Time-domain analytics: Vimshottari dasha, Sade Sati, transits ------- #
    moon_lon = next(lon for name, lon, _ in bodies if name == "Moon")
    moon_sign = sign_index(moon_lon)
    asof_jd = swe.julday(args.asof.year, args.asof.month, args.asof.day, 12.0,
                         swe.GREG_CAL)
    out["asof"] = args.asof.strftime("%Y-%m-%d")
    out["moon_sign"] = SIGNS[moon_sign]

    if not args.no_dasha:
        mahas, janma_nak, frac = vimshottari_dasha(
            jd, moon_lon, args.dasha_years, asof_jd)
        out["dasha"] = {
            "system": "Vimshottari",
            "janma_nakshatra": janma_nak,
            "nakshatra_fraction_elapsed": frac,
            "mahadashas": mahas,
        }

    if not args.no_sadesati:
        cycles, dhaiyya = sade_sati(jd, moon_sign, args.lifespan, asof_jd)
        out["sade_sati"] = {
            "moon_sign": SIGNS[moon_sign],
            "scan_years": args.lifespan,
            "cycles": cycles,
            "dhaiyya": dhaiyya,
        }
        out["transits"] = transits_asof(asof_jd, lagna_sign, moon_sign)

    return out


def print_human(out):
    print(f"\n=== {out['name']} — Vedic Chart ===")
    print(f"Ayanamsa: {out['ayanamsa']} | Houses: {out['house_system']}")
    print(f"Birth (UTC): {out['birth_utc']} | JD {out['julian_day']}\n")

    lg = out["D1"]["lagna"]
    print(f"Lagna (Ascendant): {lg['sign']} {lg['degree']} "
          f"[{lg['nakshatra']} pada {lg['pada']}]\n")

    print("D1 (Rasi):")
    print(f"  {'Planet':<8} {'Sign':<12} {'Degree':<12} {'House':<6} "
          f"{'Nakshatra':<18} {'Pada':<5} Retro")
    for p in out["D1"]["planets"]:
        print(f"  {p['planet']:<8} {p['sign']:<12} {p['degree']:<12} "
              f"{p['house']:<6} {p['nakshatra']:<18} {p['pada']:<5} "
              f"{'R' if p['retrograde'] else '-'}")

    for vname, v in out["vargas"].items():
        print(f"\n{vname} (Lagna: {v['lagna_sign']}):")
        print(f"  {'Planet':<8} {'Sign':<12} {'House':<6} Retro")
        for p in v["planets"]:
            print(f"  {p['planet']:<8} {p['sign']:<12} {p['house']:<6} "
                  f"{'R' if p['retrograde'] else '-'}")

    if "dasha" in out:
        d = out["dasha"]
        print(f"\nVimshottari Dasha (Janma Nakshatra: {d['janma_nakshatra']}, "
              f"{d['nakshatra_fraction_elapsed']*100:.1f}% elapsed at birth):")
        print(f"  {'Maha':<9} {'Start':<12} {'End':<12} {'Age':<12} Note")
        for m in d["mahadashas"]:
            note = "<- now" if m["active"] else ("balance" if m["balance"] else "")
            age = f"{m['age_start']:.1f}-{m['age_end']:.1f}"
            print(f"  {m['lord']:<9} {m['start']:<12} {m['end']:<12} "
                  f"{age:<12} {note}")
        active = next((m for m in d["mahadashas"] if m["active"]), None)
        if active:
            print(f"\n  Antardashas in current {active['lord']} mahadasha "
                  f"(as of {out['asof']}):")
            print(f"    {'Antar':<9} {'Start':<12} {'End':<12} Note")
            for a in active["antardashas"]:
                print(f"    {a['lord']:<9} {a['start']:<12} {a['end']:<12} "
                      f"{'<- now' if a['active'] else ''}")

    if "sade_sati" in out:
        ss = out["sade_sati"]
        print(f"\nSade Sati (natal Moon in {ss['moon_sign']}, "
              f"scanned {ss['scan_years']} yrs):")
        if not ss["cycles"]:
            print("  None within scan window.")
        for i, c in enumerate(ss["cycles"], 1):
            tag = "  <- ACTIVE" if c["active"] else ""
            print(f"  Cycle {i}: {c['start']} -> {c['end']} "
                  f"(age {c['age_start']:.1f}-{c['age_end']:.1f}){tag}")
            for ph in ("rising", "peak", "setting"):
                if ph in c["phases"]:
                    p = c["phases"][ph]
                    print(f"      {ph:<8} {p['start']} -> {p['end']}")
        if ss["dhaiyya"]:
            print("  Secondary (Dhaiyya / half-Sade-Sati):")
            for x in ss["dhaiyya"]:
                print(f"      {x['type']:<14} {x['start']} -> {x['end']} "
                      f"(age {x['age_start']:.1f})")

    if "transits" in out:
        print(f"\nCurrent Transits (as of {out['asof']}):")
        print(f"  {'Planet':<8} {'Sign':<12} {'Degree':<12} "
              f"{'House':<6} {'FromMoon':<9} Note")
        for t in out["transits"]:
            note = t.get("sade_sati_phase", "")
            print(f"  {t['planet']:<8} {t['sign']:<12} {t['degree']:<12} "
                  f"{t['house_from_lagna']:<6} {t['from_moon']:<9} {note}")
    print()


def parse_asof(s):
    if not s:
        return datetime.now()
    return parse_date(s)


# --------------------------------------------------------------------------- #
# mundane subcommand: event finders + instant snapshot (jyotish_core).
#   compute_chart.py mundane --start 2024-01-01 --end 2026-12-31 \
#       [--events eclipse,station,sankranti,lunation,ingress,jupsat] \
#       [--lat 40.7069 --lon -74.0113]          # cast lagna at each event there
#   compute_chart.py mundane --at "2026-10-08 09:30" --tz America/New_York \
#       --lat 40.7069 --lon -74.0113 [--node true]
# --------------------------------------------------------------------------- #

MUNDANE_KINDS = {
    "eclipse": ["solar_eclipse", "lunar_eclipse"],
    "station": ["station"],
    "sankranti": ["sankranti"],
    "lunation": ["lunation"],
    "ingress": ["ingress"],
    "jupsat": ["jupiter_saturn"],
}


def _date_jd(s):
    d = parse_date(s)
    return swe.julday(d.year, d.month, d.day, 0.0, swe.GREG_CAL)


def mundane(args):
    core.init()
    out = {"ayanamsa": "Lahiri (sidereal)", "ephemeris": core.EPHE_LABEL,
           "core_version": core.CORE_VERSION}
    if args.start and args.end:
        start, end = _date_jd(args.start), _date_jd(args.end)
        kinds = []
        for k in (args.events.split(",") if args.events else list(MUNDANE_KINDS)):
            k = k.strip().lower()
            if k not in MUNDANE_KINDS:
                raise SystemExit(f"ERROR: unknown event kind {k!r}; "
                                 f"choose from {', '.join(MUNDANE_KINDS)}")
            kinds += MUNDANE_KINDS[k]
        geo = (args.lon, args.lat, 0.0) if args.lat is not None and args.lon is not None else None
        events = core.find_events(start, end, kinds, geopos=geo)
        for e in events:
            if geo is not None:  # mundane chart cast for the given place
                asc, _ = core.ascendant_mc(e["jd"], args.lat, args.lon)
                e["lagna_sign"] = SIGNS[sign_index(asc)]
            e["jd"] = round(e["jd"], 6)
        out["range_ut"] = [args.start, args.end]
        out["events"] = events
    if args.at:
        parts = args.at.split()
        dt = parse_date(parts[0])
        hh, mm = parse_time(" ".join(parts[1:]) or "00:00")
        utc, off, method = core.to_utc(dt.year, dt.month, dt.day, hh, mm, **_tz_kwargs(args))
        jd = core.jd_from_utc(utc)
        snap = core.snapshot(jd, args.lat, args.lon, node=args.node, conj_orb=args.orb)
        snap["local"] = args.at
        snap["utc_offset"] = core.fmt_offset(off)
        snap["time_basis"] = method
        out["snapshot"] = snap
    return out


def _r(x, n=4):
    if isinstance(x, float):
        return round(x, n)
    if isinstance(x, dict):
        return {k: _r(v, n) for k, v in x.items()}
    if isinstance(x, list):
        return [_r(v, n) for v in x]
    return x


def print_mundane(out):
    if "events" in out:
        print(f"\n=== Mundane events {out['range_ut'][0]} -> {out['range_ut'][1]} (UT, "
              f"Lahiri, {out['ephemeris']}) ===")
        for e in out["events"]:
            extra = {k: v for k, v in e.items() if k not in ("type", "body", "jd", "ut")}
            bits = ", ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
                             for k, v in extra.items())
            print(f"  {e['ut']}  {e['type']:<18} {e['body']:<16} {bits}")
        print(f"  ({len(out['events'])} events)")
    if "snapshot" in out:
        s = out["snapshot"]
        p = s["panchanga"]
        print(f"\n=== Mundane chart {s['local']} ({s['time_basis']}, UTC{s['utc_offset']}) "
              f"= {s['ut']} ===")
        if "ascendant" in s:
            a = s["ascendant"]
            print(f"Lagna: {a['sign']} {fmt_dms(a['deg_in_sign'])} [{a['nakshatra']} {a['pada']}]"
                  f" | MC: {s['mc']['sign']} {fmt_dms(s['mc']['deg_in_sign'])}")
        print(f"Panchanga: tithi {p['tithi']} {p['tithi_name']} ({p['paksha']}, "
              f"{p['tithi_pct_elapsed']:.1f}% elapsed), Sun-Moon {p['sun_moon_angle']:.2f} deg, "
              f"yoga {p['yoga_name']}, karana {p['karana_name']}, vara {p['vara']} "
              f"({p['vara_lord']}, {p['vara_basis']}), Moon in {p['moon_nakshatra']} {p['moon_pada']}")
        print(f"  {'Body':<10} {'Sign':<12} {'Degree':<12} {'Nakshatra':<18} {'Pada':<5} "
              f"{'Speed':>8}  R  C")
        for n, b in s["positions"].items():
            print(f"  {n:<10} {b['sign']:<12} {fmt_dms(b['deg_in_sign']):<12} "
                  f"{b['nakshatra']:<18} {b['pada']:<5} {b['speed']:>8.4f}  "
                  f"{'R' if b['retrograde'] else '-'}  {'C' if b['combust'] else '-'}")
        r = s["relationships"]
        print(f"Relationships (node={r['node']}):")
        print("  sign conjunctions: " + ("; ".join(
            f"{c['sign']}: {'+'.join(c['bodies'])}" for c in r["sign_conjunctions"]) or "none"))
        print("  degree conjunctions: " + ("; ".join(
            f"{c['a']}-{c['b']} {c['sep']:.2f}" for c in r["degree_conjunctions"]) or "none"))
        print("  graha-yuddha: " + ("; ".join(
            f"{c['a']}-{c['b']} {c['sep']:.3f} (winner {c['winner_by_latitude']})"
            for c in r["graha_yuddha"]) or "none"))
        print("  aspects: " + "; ".join(f"{a['from']}->{a['to']}({a['nth']})" for a in r["aspects"]))
        print("  houses from Moon: " + ", ".join(f"{k} {v}" for k, v in r["houses_from_moon"].items()))
    print()


def mundane_main(argv):
    ap = argparse.ArgumentParser(prog="compute_chart.py mundane",
                                 description="Mundane events and instant charts.")
    ap.add_argument("--start", help="UT date, YYYY-MM-DD")
    ap.add_argument("--end", help="UT date, YYYY-MM-DD (exclusive)")
    ap.add_argument("--events", help="comma list: " + ",".join(MUNDANE_KINDS) + " (default all)")
    ap.add_argument("--at", help="local instant 'YYYY-MM-DD HH:MM' for a snapshot chart")
    tzg = ap.add_mutually_exclusive_group()
    tzg.add_argument("--tz", help="IANA tz for --at")
    tzg.add_argument("--utc-offset", help="fixed offset for --at, e.g. -05:00")
    tzg.add_argument("--lmt", action="store_true", help="Local Mean Time from --lon")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--node", choices=["mean", "true"], default="mean",
                    help="node used for relationships (both are always listed)")
    ap.add_argument("--orb", type=float, default=10.0, help="degree-conjunction orb")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not (args.at or (args.start and args.end)):
        ap.error("give --start and --end, and/or --at")
    if args.at and not (args.tz or args.utc_offset or args.lmt):
        ap.error("--at needs one of --tz / --utc-offset / --lmt")
    if args.lmt and args.lon is None:
        ap.error("--lmt needs --lon")
    out = mundane(args)
    if args.json:
        print(json.dumps(_r(out, 6), indent=2))
    else:
        print_mundane(out)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "mundane":
        return mundane_main(sys.argv[2:])
    ap = argparse.ArgumentParser(description="Compute a sidereal Vedic chart.")
    ap.add_argument("--name", default="Native")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD or DD-MM-YYYY")
    ap.add_argument("--time", required=True, help="'HH:MM AM/PM' or 'HH:MM'")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    tzg = ap.add_mutually_exclusive_group(required=True)
    tzg.add_argument("--tz", help="IANA tz, e.g. Asia/Kolkata")
    tzg.add_argument("--utc-offset", help="fixed offset, e.g. -05:00 or +5:30")
    tzg.add_argument("--lmt", action="store_true",
                     help="Local Mean Time from --lon (pre-standard-time charts)")
    ap.add_argument("--varga", default="D1,D9,D7,D10,D12")
    ap.add_argument("--asof", default=None,
                    help="Reference date for 'current' dasha/transits "
                         "(YYYY-MM-DD or DD-MM-YYYY; default: today)")
    ap.add_argument("--dasha-years", type=float, default=120.0,
                    help="Vimshottari span to generate from birth (default 120)")
    ap.add_argument("--lifespan", type=float, default=100.0,
                    help="Years to scan for Sade Sati cycles (default 100)")
    ap.add_argument("--no-dasha", action="store_true",
                    help="Skip Vimshottari dasha computation")
    ap.add_argument("--no-sadesati", action="store_true",
                    help="Skip Sade Sati and transit computation")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    args.asof = parse_asof(args.asof)

    out = compute(args)
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print_human(out)


if __name__ == "__main__":
    main()
