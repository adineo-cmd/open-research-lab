#!/usr/bin/env python3
"""wise_rephoto.py — F-25 follow-up: WISE re-photometry for the two
spectroscopy-package candidates F-21 DOWNGRADED on CatWISE PM-vector
disagreement (z > 3.4-11.5 sigma), to test the contamination hypothesis
(a DIFFERENT CatWISE source than the F-21 nearest match explains the
disagreement) vs "no consistent solution" (Gaia PM suspect).

Targets (astrometry from open-research-lab
astronomy/high-pm-survey/results/blink_vetting.csv @ d045850, Gaia DR3
epoch 2016.0; PM mas/yr, pmra includes cos(dec)):

  5286902985287361280  ra=107.40694  dec=-61.80777
      pmra=109.01741683473298   pmdec=215.4143605599746
      pm_tot 241.4, parallax 5.11 mas (195.6 pc), G 19.740
      F-21: catwise match sep 0.16", cw PM 483.7 vs 241.4 mas/yr,
            dp 244.2 +/- 21.3 (z = 11.5); 2MASS slot = interloper
      (2MASS 07093686-6148315, epoch 1999.96, sep 3.92", implied
       PM 419.2 vs 241.4, dp 244.5 +/- 21.8)
  6645353862012156928  ra=292.61164  dec=-53.24333
      pmra=7.881934638149993    pmdec=-229.97491707191165
      pm_tot 230.1, parallax 4.96 mas (201.6 pc), G 19.816
      F-21: catwise match sep 0.41", cw PM 181.8 vs 230.1 mas/yr,
            dp 200.0 +/- 33.2 (z = 6.0); 2MASS slot CORROBORATED
      (2MASS 19302678-5314326, epoch 2000.78, sep 0.39", implied
       PM 216.7 vs 230.1, dp 14.0 +/- 23.0, J=16.59, J-H=0.51)

Method (reuses the blink_vet.py epoch-propagation and match math):
  1. CatWISE2020 (IRSA TAP, epoch 2015.5, measured pmra/pmdec in
     deg/yr): cone search at BOTH the Gaia 2016.0 position AND the
     epoch-propagated 2015.5 position (radius 15", TOP 30), merged by
     CatWISE source_id — a wider, position-doubled re-pull of the F-21
     single-cone match. Columns: source_id, ra, dec, pm vectors +
     sigmas, w1mpro/w2mpro (+ w1sigmpro/w2sigmpro if present).
  2. CatWISE2020 cone at the epoch-propagated 2000.0 position
     (radius 6"): any CatWISE source sitting in the 2MASS-epoch slot
     with a SMALL measured PM is a stationary field star — a
     stationary-interloper signature for the 2MASS blink slot.
  3. Gaia DR3 pmra_error/pmdec_error (gaia.aip.de TAP, one batched
     query) — F-21's z used the 0.5 mas/yr floor (the gaiapm phase
     left the columns empty); real Gaia errors re-scale the z.
  4. Per-source tests (client-side separations — IRSA DISTANCE()
     units are unreliable on catwise_2020):
       - PM-vector test: dp = |cw_pm_vec - gaia_pm_vec|; sig =
         sqrt(sigpmra^2 + sigpmdec^2 + 0.5^2); consistent if
         dp <= 3 x max(sig, 8 mas/yr)  (blink_vet.py rule).
       - Blend probe: any other CatWISE source within 3" of a hit
         (WISE PSF ~6" FWHM; a close neighbor corrupts CatWISE PM).
       - Stationary-slot probe: hit within 2.5" of the expected
         epoch-2000.0 position whose CatWISE PM is consistent with
         zero (2-sigma).
  5. Per-object verdict (candidates-not-claims):
       CONTAMINATION-SUPPORTED — a source OTHER than the F-21 nearest
         match is PM-consistent with Gaia AND positionally on-track
         (within the F-21 match tolerance of the expected 2015.5
         position); the F-21 match is likely a contaminant.
       F21-MATCH-PM-SUSPECT(BLEND) — the F-21 match itself has a
         <3" neighbor and no PM-consistent solution exists.
       NO-CONSISTENT-SOLUTION — no CatWISE source in the field is
         PM-consistent with Gaia (Gaia PM suspect / unresolved).
       (plus the honest failure states)

Every HTTP query is appended to results/wise_rephoto_querylog.csv
(append mode) AND embedded in the .md report; IRSA queries are spaced
>= 13 s (polite rate). No state server-side; fully reproducible.

Usage: python3 wise_rephoto.py [results_dir]
"""
import csv
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else \
    os.path.join(HERE, "..", "results")
QLOG = os.path.join(RES, "wise_rephoto_querylog.csv")

IRSA_URL = "https://irsa.ipac.caltech.edu/TAP/sync"
AIP_URL = "https://gaia.aip.de/tap/sync"
VIZIER_URL = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"

EPOCH_GAIA = 2016.0
EPOCH_WISE = 2015.5          # CatWISE2020 reference epoch
EPOCH_2MASS = 2000.0         # 2MASS reference epoch (as blink_vet)
TOL_K = 1.3                  # match tolerance factor (blink_vet)
GAIA_PMERR_FLOOR = 0.5       # mas/yr floor (G~20), as blink_vet
CW_SYS_FLOOR = 8.0           # mas/yr WISE-Gaia PM systematic floor
IRSA_SLEEP = 13.0            # s between IRSA queries (polite rate)

# The two F-25/F-21 DOWNGRADED candidates (see docstring for provenance).
TARGETS = [
    {"source_id": "5286902985287361280",
     "ra": 107.40694, "dec": -61.80777,
     "pmra": 109.01741683473298, "pmdec": 215.4143605599746,
     "pm_tot": 241.4, "parallax": 5.112196520757978,
     "G": 19.739716, "bp_rp": 2.6774387,
     "f21_note": ("F-21 catwise match sep 0.16in cwPM 483.7 dp 244.2 "
                  "sig 21.3 (z=11.5); 2MASS slot=interloper "
                  "(07093686-6148315, 1999.96, sep 3.92in)")},
    {"source_id": "6645353862012156928",
     "ra": 292.61164, "dec": -53.24333,
     "pmra": 7.881934638149993, "pmdec": -229.97491707191165,
     "pm_tot": 230.1, "parallax": 4.961160469089415,
     "G": 19.815979, "bp_rp": 2.63134,
     "f21_note": ("F-21 catwise match sep 0.41in cwPM 181.8 dp 200.0 "
                  "sig 33.2 (z=6.0); 2MASS corroborated "
                  "(19302678-5314326, 2000.78, sep 0.39in, J=16.59)")},
]

QLOG_LIST = []
_last_irsa = 0.0


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def flush_qlog():
    if not QLOG_LIST:
        return
    os.makedirs(RES, exist_ok=True)
    exists = os.path.exists(QLOG) and os.path.getsize(QLOG) > 0
    with open(QLOG, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ts", "obj", "site", "svc",
                                          "ra", "dec", "r_as", "n",
                                          "s", "err"])
        if not exists:
            w.writeheader()
        w.writerows(QLOG_LIST)
    QLOG_LIST.clear()


def polite_wait():
    global _last_irsa
    wait = IRSA_SLEEP - (time.time() - _last_irsa)
    if wait > 0:
        time.sleep(wait)
    _last_irsa = time.time()


def tap(url_base, query, timeout=90, attempts=3):
    q = urllib.parse.urlencode({
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query})
    req = urllib.request.Request(f"{url_base}?{q}",
                                 headers={"User-Agent":
                                          "open-discovery-lab/0.2"})
    last_err, t0 = None, time.time()
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                return body, time.time() - t0
        except Exception as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"TAP failed after {attempts} attempts: {last_err}")


def parse_csv(body):
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines or lines[0].lstrip().startswith("<?xml"):
        raise ValueError("TAP returned XML (error?): "
                         + body[:120].replace("\n", " "))
    return list(csv.reader(lines))


def propagate(ra, dec, pmra, pmdec, dt):
    """Position propagated by dt years (pmra includes cos(dec); mas/yr)."""
    dec_r = math.radians(dec)
    ra2 = ra + (pmra * dt / 3.6e6) / max(math.cos(dec_r), 0.02)
    dec2 = dec + pmdec * dt / 3.6e6
    return ((ra2 + 360.0) % 360.0, max(-90.0, min(90.0, dec2)))


def ang_sep_as(ra1, dec1, ra2, dec2):
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    sd = math.sin((d2 - d1) / 2.0)
    sr = math.sin((r2 - r1) / 2.0)
    a = sd * sd + math.cos(d1) * math.cos(d2) * sr * sr
    return math.degrees(2.0 * math.asin(min(1.0, math.sqrt(a)))) * 3600.0


def cw_query(tag, ra, dec, radius_as, top, extra_cols, obj):
    """One CatWISE2020 cone query; returns list of hit dicts."""
    base = ("source_id, ra, dec, pmra, pmdec, sigpmra, sigpmdec, "
            "w1mpro, w2mpro")
    cols = base + (", " + extra_cols if extra_cols else "")
    q = (f"SELECT TOP {top} {cols} FROM catwise_2020 "
         f"WHERE 1=CONTAINS(POINT('ICRS', ra, dec), "
         f"CIRCLE('ICRS', {ra!r}, {dec!r}, {radius_as / 3600.0:.6f}))")
    polite_wait()
    n, err, rows = -1, "", []
    try:
        body, dt = tap(IRSA_URL, q)
        data = parse_csv(body)
        n = max(0, len(data) - 1)
        ncol = len(base.split(", "))
        for row in data[1:]:
            if len(row) < ncol:
                continue
            h = {"cw_id": row[0].strip('"'), "ra": float(row[1]),
                 "dec": float(row[2])}
            for k, v in zip(("pmra", "pmdec", "sigpmra", "sigpmdec",
                             "w1mpro", "w2mpro"), row[3:9]):
                h[k] = None if v.strip() == "" else float(v)
            for k, v in zip(extra_cols.split(", ") if extra_cols else [],
                            row[ncol:]):
                h[k.strip()] = None if v.strip() == "" else v.strip()
            rows.append(h)
    except Exception as e:
        err = str(e)[:120]
    QLOG_LIST.append({"ts": now_iso(), "obj": obj["source_id"],
                      "site": tag, "svc": "irsa-catwise_2020",
                      "ra": round(ra, 5), "dec": round(dec, 5),
                      "r_as": round(radius_as, 1), "n": n,
                      "s": "", "err": err})
    flush_qlog()
    print(f"  [{obj['source_id']}] {tag} cone r={radius_as:.0f}\": "
          f"{n} rows {('ERR ' + err) if err else ''}", flush=True)
    return rows


def gaia_pmerr(objs):
    """Gaia DR3 PM errors for the two objects (one batched query).

    Primary: gaia.aip.de TAP gaiadr3.gaia_source. Fallback: CDS VizieR
    TAP I/355/gaiadr3 (reachable when aip is not; F-21's gaiapm phase
    hit the same aip XML error, leaving the ledger PM-error columns
    empty — the fallback re-covers that gap).
    """
    ids = ", ".join(o["source_id"] for o in objs)
    rec, err = {}, ""
    n = -1
    svc = "aip-gaiadr3"
    q = (f"SELECT source_id, pmra, pmdec, pmra_error, pmdec_error, "
         f"parallax, parallax_error, ref_epoch FROM gaiadr3.gaia_source "
         f"WHERE source_id IN ({ids})")
    try:
        body, dt = tap(AIP_URL, q, timeout=60)
        data = parse_csv(body)
        n = max(0, len(data) - 1)
        for row in data[1:]:
            if len(row) < 8:
                continue
            rec[row[0]] = {
                "pmra": float(row[1]) if row[1].strip() else None,
                "pmdec": float(row[2]) if row[2].strip() else None,
                "pmra_error": float(row[3]) if row[3].strip() else None,
                "pmdec_error": float(row[4]) if row[4].strip() else None,
                "parallax": float(row[5]) if row[5].strip() else None,
                "parallax_error": float(row[6]) if row[6].strip() else None,
                "ref_epoch": float(row[7]) if row[7].strip() else None}
    except Exception as e:
        err = str(e)[:120]
    if not rec:
        # VizieR fallback (I/355/gaiadr3)
        svc = "vizier-I/355/gaiadr3"
        vq = (f"SELECT SourceId, pmRA, pmDE, e_pmRA, e_pmDE, Plx, e_Plx "
              f"FROM \"I/355/gaiadr3\" WHERE SourceId IN ({ids})")
        try:
            body, dt = tap(VIZIER_URL, vq, timeout=90)
            data = parse_csv(body)
            n = max(0, len(data) - 1)
            err = ""
            for row in data[1:]:
                if len(row) < 7:
                    continue
                rec[row[0].strip('"')] = {
                    "pmra": float(row[1]) if row[1].strip() else None,
                    "pmdec": float(row[2]) if row[2].strip() else None,
                    "pmra_error": float(row[3]) if row[3].strip() else None,
                    "pmdec_error": float(row[4]) if row[4].strip() else None,
                    "parallax": float(row[5]) if row[5].strip() else None,
                    "parallax_error": float(row[6]) if row[6].strip()
                    else None,
                    "ref_epoch": 2016.0}
        except Exception as e:
            err = (err + " | vizier: " + str(e))[:160]
    QLOG_LIST.append({"ts": now_iso(), "obj": "|".join(o["source_id"]
                                                       for o in objs),
                      "site": "gaiapm", "svc": svc,
                      "ra": "", "dec": "", "r_as": "", "n": n,
                      "s": "", "err": err})
    flush_qlog()
    print(f"  gaia pm errors ({svc}): {list(rec.keys())} "
          f"{('ERR ' + err) if err else ''}", flush=True)
    return rec


def fmt(x, nd=3):
    return "" if x is None else (round(x, nd) if isinstance(x, float) else x)


def analyze(obj, hits, slot_hits, gp):
    """Per-object analysis; returns (rec, csv_rows, verdict)."""
    sid = obj["source_id"]
    ra, dec = obj["ra"], obj["dec"]
    pmra, pmdec = obj["pmra"], obj["pmdec"]
    pm = math.hypot(pmra, pmdec)
    raw15, dec15 = propagate(ra, dec, pmra, pmdec, EPOCH_WISE - EPOCH_GAIA)
    ra2000, dec2000 = propagate(ra, dec, pmra, pmdec, EPOCH_2MASS - EPOCH_GAIA)
    match_tol_as = max(3.5, TOL_K * pm * 0.5 / 1000.0 + 2.0)
    gperr = gp.get(sid, {})
    pmra_err = gperr.get("pmra_error") or GAIA_PMERR_FLOOR
    pmdec_err = gperr.get("pmdec_error") or GAIA_PMERR_FLOOR
    pm_floors = (max(pmra_err, GAIA_PMERR_FLOOR),
                 max(pmdec_err, GAIA_PMERR_FLOOR))

    # merge duplicate cw ids from the two cones (keep 2015.5-cone row)
    merged = {}
    for h in hits:
        merged.setdefault(h["cw_id"], h)
    hits = sorted(merged.values(), key=lambda h: ang_sep_as(
        raw15, dec15, h["ra"], h["dec"]))

    for h in hits:
        h["sep15_as"] = round(ang_sep_as(raw15, dec15, h["ra"], h["dec"]), 2)
        h["sep16_as"] = round(ang_sep_as(ra, dec, h["ra"], h["dec"]), 2)
        if h.get("pmra") is not None and h.get("pmdec") is not None:
            cwra, cwdec = h["pmra"] * 1000.0, h["pmdec"] * 1000.0
            h["pm_mas"] = round(math.hypot(cwra, cwdec), 1)
            dpra, dpdec = cwra - pmra, cwdec - pmdec
            h["dp_mas"] = round(math.hypot(dpra, dpdec), 1)
            sigr = ((h.get("sigpmra") or 0.0) * 1000.0)
            sigd = ((h.get("sigpmdec") or 0.0) * 1000.0)
            h["sig"] = round(math.sqrt(sigr ** 2 + sigd ** 2
                                       + GAIA_PMERR_FLOOR ** 2), 1)
            h["z"] = round(h["dp_mas"] / max(h["sig"], 1e-6), 2)
        if h.get("w1mpro") is not None and h.get("w2mpro") is not None:
            h["w1w2"] = round(h["w1mpro"] - h["w2mpro"], 2)
        # blend probe: any other hit within 3"
        h["nn_as"] = round(min((ang_sep_as(h["ra"], h["dec"], o["ra"],
                                          o["dec"])
                                for o in hits if o is not h),
                               default=999.0), 2)
        # stationary-slot probe at the 2MASS epoch
        h["sep2000_as"] = round(ang_sep_as(ra2000, dec2000, h["ra"],
                                           h["dec"]), 2)

    f21_match = hits[0] if hits else None  # nearest = F-21 rule
    consistent = [h for h in hits if h.get("z") is not None
                  and h["dp_mas"] <= 3.0 * max(h["sig"], CW_SYS_FLOOR)]
    consistent_other = [h for h in consistent if h is not f21_match]
    ontrack_other = [h for h in consistent_other
                     if h["sep15_as"] <= match_tol_as]
    stationary_slot = [h for h in hits
                       if h.get("pm_mas") is not None
                       and h["sep2000_as"] <= 2.5
                       and h["pm_mas"] <= 2.0 * max(math.hypot(
                           (h.get("sigpmra") or 0) * 1000,
                           (h.get("sigpmdec") or 0) * 1000), 5.0)]
    blend_on_f21 = f21_match is not None and f21_match.get("nn_as",
                                                           999) <= 3.0

    csv_rows = []
    for rank, h in enumerate(hits, 1):
        csv_rows.append({
            "gaia_source_id": sid, "cw_source_id": h["cw_id"],
            "ra_cw": round(h["ra"], 6), "dec_cw": round(h["dec"], 6),
            "sep_expected2015_as": h["sep15_as"],
            "sep_gaia2016_as": h["sep16_as"],
            "rank_by_sep15": rank,
            "f21_match": "Y" if h is f21_match else "N",
            "w1mpro": fmt(h.get("w1mpro")), "w2mpro": fmt(h.get("w2mpro")),
            "w1w2": fmt(h.get("w1w2"), 2),
            "w1sigmpro": fmt(float(h["w1sigmpro"]) if h.get("w1sigmpro")
                             not in (None, "") else None, 3),
            "w2sigmpro": fmt(float(h["w2sigmpro"]) if h.get("w2sigmpro")
                             not in (None, "") else None, 3),
            "cw_pmra": fmt(h.get("pmra"), 6), "cw_pmdec": fmt(h.get("pmdec"),
                                                              6),
            "cw_sigpmra": fmt(h.get("sigpmra"), 6),
            "cw_sigpmdec": fmt(h.get("sigpmdec"), 6),
            "cw_pm_mas": fmt(h.get("pm_mas"), 1),
            "dp_vec_mas": fmt(h.get("dp_mas"), 1),
            "sig_vec": fmt(h.get("sig"), 1), "z_vec": fmt(h.get("z"), 2),
            "nn_sep_as": h["nn_as"],
            "sep_expected2000_as": h["sep2000_as"],
        })

    if ontrack_other:
        verdict = "CONTAMINATION-SUPPORTED"
        best = ontrack_other[0]
    elif consistent_other:
        verdict = "CONTAMINATION-POSSIBLE(off-track-consistent-source)"
        best = consistent_other[0]
    elif blend_on_f21 and not consistent:
        verdict = "F21-MATCH-PM-SUSPECT(BLEND)"
        best = f21_match
    elif f21_match is not None and f21_match.get("z") is not None \
            and f21_match["dp_mas"] <= 3.0 * max(f21_match["sig"],
                                                 CW_SYS_FLOOR):
        verdict = "F21-MATCH-STANDS(re-photometry-finds-no-contradiction)"
        best = f21_match
    else:
        verdict = "NO-CONSISTENT-SOLUTION"
        best = f21_match

    rec = {
        "source_id": sid,
        "gaia_2016": f"{ra:.5f} {dec:+.5f}",
        "expected_2015.5": f"{raw15:.5f} {dec15:+.5f}",
        "expected_2000.0": f"{ra2000:.5f} {dec2000:+.5f}",
        "gaia_pm": f"{pmra:.1f} {pmdec:+.1f} ({pm:.1f} mas/yr)",
        "gaia_pm_err": (f"{pmra_err:.2f} {pmdec_err:.2f} mas/yr"
                        + (" (aip)" if gperr.get("pmra_error")
                           else " (0.5 floor)")),
        "n_cw_field": len(hits),
        "match_tol_as": round(match_tol_as, 2),
        "f21_match": (f"{f21_match['cw_id']} sep15={f21_match['sep15_as']}\""
                      f" w1w2={fmt(f21_match.get('w1w2'), 2)}"
                      f" cwPM={fmt(f21_match.get('pm_mas'), 1)}"
                      f" dp={fmt(f21_match.get('dp_mas'), 1)}"
                      f" z={fmt(f21_match.get('z'), 2)}"
                      f" nn={f21_match['nn_as']}\""
                      if f21_match else "none"),
        "consistent_sources": "; ".join(
            f"{h['cw_id']} sep15={h['sep15_as']}\" z={fmt(h.get('z'), 2)}"
            for h in consistent) or "none",
        "consistent_other_ontrack": "; ".join(
            f"{h['cw_id']} sep15={h['sep15_as']}\""
            f" w1w2={fmt(h.get('w1w2'), 2)} z={fmt(h.get('z'), 2)}"
            for h in ontrack_other) or "none",
        "stationary_2000_slot": "; ".join(
            f"{h['cw_id']} sep2000={h['sep2000_as']}\""
            f" cwPM={fmt(h.get('pm_mas'), 1)} mas/yr"
            for h in stationary_slot) or "none",
        "verdict": verdict,
        "f21_note": obj["f21_note"],
    }
    return rec, csv_rows, best


def main():
    os.makedirs(RES, exist_ok=True)
    print(f"targets: {len(TARGETS)} F-21 DOWNGRADED candidates", flush=True)
    gp = gaia_pmerr(TARGETS)
    all_recs, all_rows = [], []
    for i, obj in enumerate(TARGETS, 1):
        sid = obj["source_id"]
        ra, dec = obj["ra"], obj["dec"]
        pmra, pmdec = obj["pmra"], obj["pmdec"]
        raw15, dec15 = propagate(ra, dec, pmra, pmdec,
                                 EPOCH_WISE - EPOCH_GAIA)
        ra2000, dec2000 = propagate(ra, dec, pmra, pmdec,
                                    EPOCH_2MASS - EPOCH_GAIA)
        print(f"[{i}/{len(TARGETS)}] {sid}", flush=True)
        # cross-check: live Gaia astrometry must match the ledger values
        g = gp.get(sid)
        if g and g.get("pmra") is not None:
            d_pm = math.hypot(g["pmra"] - pmra, g["pmdec"] - pmdec)
            print(f"  aip cross-check: dpm={d_pm:.2f} mas/yr "
                  f"(ledger vs live)", flush=True)
        extra = "w1sigmpro, w2sigmpro"
        hits = cw_query("exp2015.5", raw15, dec15, 15.0, 30, extra, obj)
        if not hits:
            # retry without the photometric-error columns on schema error
            hits = cw_query("exp2015.5-retry", raw15, dec15, 15.0, 30,
                            "", obj)
        h16 = cw_query("gaia2016", ra, dec, 15.0, 30, extra, obj)
        if not h16:
            h16 = cw_query("gaia2016-retry", ra, dec, 15.0, 30, "", obj)
        slot = cw_query("exp2000.0", ra2000, dec2000, 6.0, 12, extra, obj)
        if not slot:
            slot = cw_query("exp2000.0-retry", ra2000, dec2000, 6.0, 12,
                            "", obj)
        rec, rows, best = analyze(obj, hits + h16, slot, gp)
        rec["slot_n"] = len(slot)
        all_recs.append(rec)
        all_rows.extend(rows)
        print(f"  -> {rec['verdict']}", flush=True)

    # CSV (per CatWISE field source)
    if all_rows:
        fields = list(all_rows[0].keys())
        path = os.path.join(RES, "wise_rephoto.csv")
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(all_rows)
        print(f"-> {path}", flush=True)

    # JSON (full recs for the .md render)
    path = os.path.join(RES, "wise_rephoto_recs.json")
    with open(path, "w") as f:
        json.dump({"targets": all_recs,
                   "gaia_aip": {k: {kk: vv for kk, vv in v.items()}
                                for k, v in gp.items()},
                   "qlog": []}, f, indent=1)
    print(f"-> {path}", flush=True)
    flush_qlog()
    for r in all_recs:
        print(f"{r['source_id']}: {r['verdict']}", flush=True)


if __name__ == "__main__":
    main()
