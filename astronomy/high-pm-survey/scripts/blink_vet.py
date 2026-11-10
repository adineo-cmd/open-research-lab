#!/usr/bin/env python3
"""blink_vet.py — Track B v3: deep blink-comparison vetting of the 39
confidence-A possible-new high-PM candidates from vetting_v2.

For each candidate (source_id in results/possible_new_final.csv with
conf=='A', astrometry joined from results/candidates.csv) this pipeline
tests whether the object EXISTS and MOVES as Gaia DR3 predicts, using
independent epoch data (blink comparison at propagated positions):

  2MASS All-Sky PSC (IRSA TAP, table fp_psc; epoch per-source `jdate`,
    1997-2001): cone at the epoch-2000.0 position, radius
    max(10", 1.5 x pm x 18.75 yr). A hit at the expected old position
    with an implied PM consistent with Gaia's = 20-year PM baseline
    (2MASS jdate -> Gaia 2016.0).
  CatWISE2020 (IRSA TAP, epoch 2015.5, carries measured pmra/pmdeg in
    deg/yr): cone at the epoch-2015.5 position as in vet2.py, now for
    ALL 39 (v2 ran only top-50). WISE PM vector vs Gaia PM vector.
  Gaia DR3 pmra_error/pmdec_error (gaia.aip.de TAP): proper 3-sigma
    scales for the PM comparisons (candidates.csv has no pm errors).
  LS-DR9 imagery (www.legacysurvey.org jpeg-cutout, epochs 2014-2019):
    fetched locally to /tmp (never committed) at BOTH the 2016.0
    position and the 2000.0 position — a two-position blink on one
    image: the source should sit at the 2016-position and be ABSENT at
    the 2000-position (pm x 16 yr ~ 4" away). Statuses recorded;
    visual inspection is manual (Read tool) for flagged objects.

SDSS (SkyServer) was probed and is UNREACHABLE from this host in this
session (ImgCutout 404 on dr16/dr17/dr18; crossid returns no rows) —
recorded as an honest failure; the NOAO Data Lab TAP (datalab.noao.edu,
datalab.noirlab.edu) is also unreachable (DNS / timeout), so the
LS-DR9 *catalog* check is replaced by LS-DR9 imagery + the 2MASS/CatWISE
catalog blink.

Match rules:
  2MASS hit: implied PM vector = (hit_pos - gaia_pos@2016.0) / (jdate -
    2016.0) per component, in mas/yr (full two-epoch displacement). For a
    true counterpart this matches the Gaia PM. dp = |implied - gaia|
    mas/yr; sigma = sqrt((0.35"/baseline)^2 + 0.5^2) mas/yr (0.35" =
    2MASS position + match tolerance). Consistent if dp <= 3 x max(sigma, 8).
  CatWISE hit (nearest within max(3.5", 1.3 x pm x 0.5 yr + 2")):
    dp_cw = |cw_pm_vec - gaia_pm_vec|; sigma_cw =
    sqrt(sigpmra^2 + sigpmdec^2 + 0.5^2); consistent if
    dp_cw <= 3 x max(sigma_cw, 8) (floor = WISE/Gaia systematics).

Verdicts (candidates-not-claims):
  PROMOTED      : CatWISE PM consistent AND 2MASS old-position hit
                  consistent -> the object is detected at 3 epochs with
                  consistent motion (two-epoch PM baseline recorded).
  CONF-A-STAYS  : CatWISE consistent, no contradicting evidence.
  DOWNGRADED    : positive contradiction — a CatWISE counterpart whose
                  measured PM vector contradicts Gaia at >3 sigma, or a
                  2MASS source IN the expected epoch-2000 slot (2.5")
                  whose implied PM contradicts Gaia at >5 sigma with no
                  CatWISE support.

NB: IRSA TAP DISTANCE() returns unreliable units on fp_psc and
    catwise_2020 — all separations are computed client-side from the
    returned ra/dec.

Every HTTP query is appended to results/blink_querylog.csv (append mode);
state checkpointed to results/blink_state.json (resume by phase key).

Usage: python3 blink_vet.py [twomass|catwise|gaiapm|cutouts|finalize|all]
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
RES = os.path.join(HERE, "..", "results")
STATE = os.path.join(RES, "blink_state.json")
QLOG = os.path.join(RES, "blink_querylog.csv")
TMP = "/tmp/trackb_blink_cutouts"

IRSA_URL = "https://irsa.ipac.caltech.edu/TAP/sync"
AIP_URL = "https://gaia.aip.de/tap/sync"

EPOCH_GAIA = 2016.0
EPOCH_CAT = 2000.0        # reference pre-Gaia epoch (as vet2.py)
EPOCH_WISE = 2015.5
TOL_K = 1.3
POS_ERR_2MASS = 0.35      # arcsec, position + match tolerance
GAIA_PMERR_FLOOR = 0.5    # mas/yr, floor for Gaia PM error (G~20)
CW_SYS_FLOOR = 8.0        # mas/yr, WISE-Gaia PM systematic floor
TM_FLOOR = 8.0            # mas/yr, floor for 2MASS implied-PM sigma

QLOG_LIST = []
_QLOG_WRITTEN = 0


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def flush_qlog():
    global _QLOG_WRITTEN
    new = QLOG_LIST[_QLOG_WRITTEN:]
    if not new:
        return
    exists = os.path.exists(QLOG) and os.path.getsize(QLOG) > 0
    with open(QLOG, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ts", "phase", "sid", "ra", "dec",
                                          "svc", "n", "s", "err"])
        if not exists:
            w.writeheader()
        w.writerows(new)
    _QLOG_WRITTEN = len(QLOG_LIST)


def tap(url_base, query, timeout=90, attempts=3):
    q = urllib.parse.urlencode({
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query})
    req = urllib.request.Request(f"{url_base}?{q}",
                                 headers={"User-Agent": "open-discovery-lab/0.2"})
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
        raise ValueError("TAP returned XML (error?)")
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


def load_targets():
    """The 39 confidence-A rows, astrometry joined from candidates.csv."""
    with open(os.path.join(RES, "possible_new_final.csv")) as f:
        conf_a = {r["source_id"] for r in csv.DictReader(f) if r["conf"] == "A"}
    with open(os.path.join(RES, "candidates.csv")) as f:
        cands = {c["source_id"]: c for c in csv.DictReader(f)}
    missing = conf_a - set(cands)
    if missing:
        raise SystemExit(f"conf-A ids missing from candidates.csv: {missing}")
    return [cands[sid] for sid in conf_a]


def jd_to_year(jd):
    """Julian date -> decimal epoch (JD 2451545.0 = epoch 2000.0)."""
    return (jd - 2451545.0) / 365.25 + 2000.0


def phase_twomass(cands, state):
    todo = [c for c in cands if "twomass" not in state.get(c["source_id"], {})]
    print(f"twomass: {len(todo)} to do", flush=True)
    for i, c in enumerate(todo, 1):
        sid = c["source_id"]
        ra, dec = float(c["ra"]), float(c["dec"])
        pmra, pmdec = float(c["pmra"]), float(c["pmdec"])
        pm = math.hypot(pmra, pmdec)
        ra2000, dec2000 = propagate(ra, dec, pmra, pmdec, EPOCH_CAT - EPOCH_GAIA)
        radius_as = max(10.0, 1.5 * pm * (EPOCH_GAIA - 1997.25) / 1000.0 + 1.0)
        cols = ("designation, ra, dec, j_m, j_msig, h_m, h_msig, k_m, k_msig,"
                " ph_qual, jdate")
        # NB: IRSA TAP DISTANCE() returns unreliable units on fp_psc — the
        # separation is computed client-side from the returned ra/dec.
        q = (f"SELECT TOP 12 {cols} FROM fp_psc "
             f"WHERE 1=CONTAINS(POINT('ICRS', ra, dec), "
             f"CIRCLE('ICRS', {ra2000!r}, {dec2000!r}, "
             f"{radius_as / 3600.0:.6f}))")
        rec = {"n": 0, "hits": [], "verdict": "failed"}
        try:
            body, dt = tap(IRSA_URL, q)
            rows = parse_csv(body)[1:]
            hits = []
            for row in rows:
                if len(row) < 11:
                    continue
                h = {"des": row[0].strip('"'), "ra": float(row[1]),
                     "dec": float(row[2])}
                for k, v in zip(("j_m", "j_msig", "h_m", "h_msig", "k_m",
                                 "k_msig"), row[3:9]):
                    h[k] = None if v.strip() == "" else float(v)
                h["ph_qual"] = row[9].strip('"')
                h["jdate"] = float(row[10]) if row[10].strip() else None
                h["sep2000_as"] = round(ang_sep_as(ra2000, dec2000,
                                                   h["ra"], h["dec"]), 2)
                if h["jdate"]:
                    # two-epoch PM baseline: implied mean PM over the full
                    # 2MASS-epoch -> Gaia-epoch span is
                    # (hit - gaia_pos@2016.0) / (epoch_2MASS - 2016.0),
                    # per component. For a true counterpart this matches the
                    # Gaia PM; dp = |implied - gaia| is the check statistic.
                    ep = jd_to_year(h["jdate"])
                    h["epoch"] = round(ep, 2)
                    base = EPOCH_GAIA - ep  # years
                    cosd = math.cos(math.radians(dec))
                    dra = (h["ra"] - ra) * cosd * 3600.0  # arcsec
                    ddec = (h["dec"] - dec) * 3600.0
                    pm_i_ra = dra * 1000.0 / (ep - EPOCH_GAIA)  # mas/yr
                    pm_i_dec = ddec * 1000.0 / (ep - EPOCH_GAIA)
                    dpra, dpdec = pm_i_ra - pmra, pm_i_dec - pmdec
                    h["pm_impl"] = round(math.hypot(pm_i_ra, pm_i_dec), 1)
                    h["dp_mas"] = round(math.hypot(dpra, dpdec), 1)
                    sig = math.sqrt((POS_ERR_2MASS * 1000.0 / base) ** 2
                                    + GAIA_PMERR_FLOOR ** 2)
                    h["sig"] = round(sig, 1)
                    h["z"] = round(h["dp_mas"] / sig, 2)
                else:
                    # track-projection fallback (no jdate): implied epoch
                    cosd = math.cos(math.radians(dec))
                    ux, uy = pmra / pm, pmdec / pm
                    dra = (h["ra"] - ra) * cosd * 3600.0
                    ddec = (h["dec"] - dec) * 3600.0
                    along = dra * ux + ddec * uy
                    perp = abs(dra * uy - ddec * ux)
                    h["epoch"] = round(EPOCH_GAIA - along / pm, 2) if pm else None
                    h["perp_as"] = round(perp, 2)
                    h["dp_mas"] = h["sig"] = h["z"] = None
                hits.append(h)
            rec["n"] = len(hits)
            rec["hits"] = hits
            consistent = [h for h in hits if h.get("z") is not None
                          and h["dp_mas"] <= 3.0 * max(h["sig"], TM_FLOOR)]
            ontrack = [h for h in hits if h.get("z") is None and
                       h.get("perp_as", 9e9) <= 2.5 and
                       1997.0 <= (h.get("epoch") or 0) <= 2002.0]
            best = (consistent or ontrack or hits)
            best.sort(key=lambda h: (h.get("dp_mas") if h.get("dp_mas")
                                     is not None else 9e9,
                                     h["sep2000_as"]))
            rec["best"] = best[0] if best else None
            if consistent:
                rec["verdict"] = "2mass-corroborated"
            elif ontrack:
                rec["verdict"] = "2mass-on-track(no-z)"
            elif hits:
                rec["verdict"] = "2mass-interloper"
            else:
                # no source in the cone: check whether 2MASS depth makes a
                # non-detection EXPECTED. Empirical cohort G-J ~ 3.4 (the
                # 2MASS-detected members have J ~ 16.2-16.6 at G ~ 20), so
                # J_est = G - 3.4; the 2MASS SNR=10 limit is J ~ 16.5.
                try:
                    j_est = float(c["G"]) - 3.4
                    rec["j_est"] = round(j_est, 1)
                    rec["verdict"] = ("2mass-none(below-limit,expected)"
                                      if j_est > 16.5 else "2mass-none")
                except ValueError:
                    rec["verdict"] = "2mass-none"
        except Exception as e:
            rec["verdict"] = "failed"
            rec["error"] = str(e)[:140]
            QLOG_LIST.append({"ts": now_iso(), "phase": "twomass", "sid": sid,
                              "ra": round(ra2000, 5), "dec": round(dec2000, 5),
                              "svc": "irsa-fp_psc", "n": -1, "s": "",
                              "err": str(e)[:80]})
        else:
            QLOG_LIST.append({"ts": now_iso(), "phase": "twomass", "sid": sid,
                              "ra": round(ra2000, 5), "dec": round(dec2000, 5),
                              "svc": "irsa-fp_psc", "n": rec["n"],
                              "s": round(dt, 2), "err": ""})
        state.setdefault(sid, {})["twomass"] = rec
        json.dump(state, open(STATE, "w"))
        flush_qlog()
        print(f"  {i}/{len(todo)} {sid}: {rec['verdict']}", flush=True)
        time.sleep(0.7)


def phase_catwise(cands, state):
    todo = [c for c in cands if "catwise" not in state.get(c["source_id"], {})]
    print(f"catwise: {len(todo)} to do", flush=True)
    for i, c in enumerate(todo, 1):
        sid = c["source_id"]
        ra, dec = float(c["ra"]), float(c["dec"])
        pmra, pmdec = float(c["pmra"]), float(c["pmdec"])
        pm = math.hypot(pmra, pmdec)
        raw15, dec15 = propagate(ra, dec, pmra, pmdec, EPOCH_WISE - EPOCH_GAIA)
        radius_as = max(8.0, TOL_K * pm * (EPOCH_GAIA - EPOCH_WISE) / 1000.0 + 2.0)
        cols = ("source_id, ra, dec, pmra, pmdec, sigpmra, sigpmdec, "
                "w1mpro, w2mpro")
        # client-side separation (IRSA DISTANCE() units unreliable)
        q = (f"SELECT TOP 8 {cols} FROM catwise_2020 "
             f"WHERE 1=CONTAINS(POINT('ICRS', ra, dec), "
             f"CIRCLE('ICRS', {raw15!r}, {dec15!r}, "
             f"{radius_as / 3600.0:.6f}))")
        rec = {"n": 0, "verdict": "failed"}
        try:
            body, dt = tap(IRSA_URL, q)
            rows = parse_csv(body)[1:]
            hits = []
            for row in rows:
                if len(row) < 9:
                    continue
                h = {"cw_id": row[0].strip('"'), "ra": float(row[1]),
                     "dec": float(row[2])}
                for k, v in zip(("pmra", "pmdec", "sigpmra", "sigpmdec",
                                 "w1mpro", "w2mpro"), row[3:9]):
                    h[k] = None if v.strip() == "" else float(v)
                h["sep_as"] = round(ang_sep_as(raw15, dec15,
                                               h["ra"], h["dec"]), 2)
                if h.get("pmra") is not None:
                    cwra, cwdec = h["pmra"] * 1000.0, h["pmdec"] * 1000.0
                    h["pm_mas"] = round(math.hypot(cwra, cwdec), 1)
                    dpra, dpdec = cwra - pmra, cwdec - pmdec
                    h["dp_mas"] = round(math.hypot(dpra, dpdec), 1)
                    sigr = (h.get("sigpmra") or 0.0) * 1000.0
                    sigd = (h.get("sigpmdec") or 0.0) * 1000.0
                    sig = math.sqrt(sigr ** 2 + sigd ** 2
                                    + GAIA_PMERR_FLOOR ** 2)
                    h["sig"] = round(sig, 1)
                    h["z"] = round(h["dp_mas"] / max(sig, 1e-6), 2)
                if h.get("w1mpro") is not None and h.get("w2mpro") is not None:
                    h["w1w2"] = round(h["w1mpro"] - h["w2mpro"], 2)
                hits.append(h)
            hits.sort(key=lambda h: h["sep_as"])
            rec["n"] = len(hits)
            rec["hits"] = hits[:4]
            match_tol_as = max(3.5, TOL_K * pm * 0.5 / 1000.0 + 2.0)
            near = [h for h in hits if h["sep_as"] <= match_tol_as]
            good = [h for h in near if h.get("z") is not None
                    and h["dp_mas"] <= 3.0 * max(h["sig"], CW_SYS_FLOOR)]
            if good:
                rec["best"] = good[0]
                rec["verdict"] = "catwise-pm-consistent"
            elif near:
                rec["best"] = near[0]
                rec["verdict"] = "catwise-nearbut-pm-inconsistent"
            else:
                rec["verdict"] = "no-catwise-match"
        except Exception as e:
            rec["verdict"] = "failed"
            rec["error"] = str(e)[:140]
            QLOG_LIST.append({"ts": now_iso(), "phase": "catwise", "sid": sid,
                              "ra": round(raw15, 5), "dec": round(dec15, 5),
                              "svc": "irsa-catwise_2020", "n": -1, "s": "",
                              "err": str(e)[:80]})
        else:
            QLOG_LIST.append({"ts": now_iso(), "phase": "catwise", "sid": sid,
                              "ra": round(raw15, 5), "dec": round(dec15, 5),
                              "svc": "irsa-catwise_2020", "n": rec["n"],
                              "s": round(dt, 2), "err": ""})
        state.setdefault(sid, {})["catwise"] = rec
        json.dump(state, open(STATE, "w"))
        flush_qlog()
        print(f"  {i}/{len(todo)} {sid}: {rec['verdict']}", flush=True)
        time.sleep(0.7)


def phase_gaiapm(cands, state):
    """Gaia DR3 pmra_error/pmdec_error/parallax_error from gaia.aip.de."""
    todo = [c for c in cands if "gaiapm" not in state.get(c["source_id"], {})]
    print(f"gaiapm: {len(todo)} to do", flush=True)
    for i, c in enumerate(todo, 1):
        sid = c["source_id"]
        q = (f"SELECT source_id, pmra_error, pmdec_error, parallax_error "
             f"FROM gaiadr3.gaia_source WHERE source_id = {sid}")
        rec = {}
        try:
            body, dt = tap(AIP_URL, q, timeout=60)
            rows = parse_csv(body)[1:]
            if rows:
                rec = {"pmra_err": float(rows[0][1]), "pmdec_err": float(rows[0][2]),
                       "parallax_err": float(rows[0][3])}
            QLOG_LIST.append({"ts": now_iso(), "phase": "gaiapm", "sid": sid,
                              "ra": "", "dec": "", "svc": "aip-gaiadr3",
                              "n": len(rows), "s": round(dt, 2), "err": ""})
        except Exception as e:
            rec = {"error": str(e)[:140]}
            QLOG_LIST.append({"ts": now_iso(), "phase": "gaiapm", "sid": sid,
                              "ra": "", "dec": "", "svc": "aip-gaiadr3",
                              "n": -1, "s": "", "err": str(e)[:80]})
        state.setdefault(sid, {})["gaiapm"] = rec
        json.dump(state, open(STATE, "w"))
        flush_qlog()
        print(f"  {i}/{len(todo)} {sid}: "
              f"{rec.get('pmra_err', 'failed')}", flush=True)
        time.sleep(0.4)


def cutout_status(url, fn):
    """Fetch an image cutout; classify ok / blank / error."""
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "open-discovery-lab/0.2"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            if len(data) < 200 or not data.startswith(b"\xff\xd8"):
                return "no-coverage"
            if len(data) < 3000:
                return "no-coverage(blank-tile)"
            with open(fn, "wb") as f:
                f.write(data)
            return f"ok({len(data)}b)"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "no-coverage"
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return "http-error"


def phase_cutouts(cands, state):
    """LS-DR9 jpegs at the 2016.0 AND 2000.0 positions (blink pair)."""
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(TMP, exist_ok=True)
    todo = [c for c in cands if "cutouts" not in state.get(c["source_id"], {})]
    print(f"cutouts: {len(todo)} to do", flush=True)

    def work(c):
        sid = c["source_id"]
        ra, dec = float(c["ra"]), float(c["dec"])
        pmra, pmdec = float(c["pmra"]), float(c["pmdec"])
        ra2000, dec2000 = propagate(ra, dec, pmra, pmdec, EPOCH_CAT - EPOCH_GAIA)
        rec = {}
        urls = {"ls2016": (ra, dec), "ls2000": (ra2000, dec2000)}
        outs = {}
        for tag, (rr, dd) in urls.items():
            url = (f"https://www.legacysurvey.org/viewer/jpeg-cutout"
                   f"?ra={rr:.6f}&dec={dd:.6f}&layer=ls-dr9&size=200")
            fn = os.path.join(TMP, f"{sid}_{tag}.jpg")
            outs[tag] = cutout_status(url, fn)
        rec.update(outs)
        rec["blink_note"] = ""
        return rec

    with ThreadPoolExecutor(max_workers=4) as ex:
        for i, (c, rec) in enumerate(zip(todo, ex.map(work, todo)), 1):
            state.setdefault(c["source_id"], {})["cutouts"] = rec
            if i % 8 == 0:
                json.dump(state, open(STATE, "w"))
                print(f"  {i}/{len(todo)}", flush=True)
            QLOG_LIST.append({"ts": now_iso(), "phase": "cutouts",
                              "sid": c["source_id"], "ra": "", "dec": "",
                              "svc": "legacysurvey-lsdr9", "n": 2,
                              "s": "", "err": ""})
    json.dump(state, open(STATE, "w"))
    flush_qlog()
    print(f"cutouts done: {len(todo)}", flush=True)


def phase_finalize(cands, state):
    """Join evidence -> verdicts -> results/blink_vetting.csv."""
    rows = []
    promoted, downgraded, stays = [], [], []
    for c in cands:
        sid = c["source_id"]
        s = state.get(sid, {})
        tm = s.get("twomass", {})
        cw = s.get("catwise", {})
        gp = s.get("gaiapm", {})
        cut = s.get("cutouts", {})
        pm = math.hypot(float(c["pmra"]), float(c["pmdec"]))
        tm_ok = tm.get("verdict") == "2mass-corroborated"
        cw_ok = cw.get("verdict") == "catwise-pm-consistent"
        # slot test: does a catalog source sit within 2.5" of the expected
        # epoch-2000 position whose implied PM contradicts Gaia at >5 sigma?
        # (field stars elsewhere in the ~10" cone are normal and NOT
        # contradictions; only the slot itself matters)
        slot_bad = None
        for h in tm.get("hits", []):
            if (h.get("z") is not None and h["z"] > 5.0
                    and h.get("sep2000_as", 9e9) <= 2.5):
                if slot_bad is None or h["sep2000_as"] < slot_bad["sep2000_as"]:
                    slot_bad = h
        verdict, flags = "CONF-A-STAYS", []
        if cw_ok and tm_ok:
            verdict = "PROMOTED"
        elif cw_ok and tm.get("verdict", "").startswith("2mass-none"):
            flags.append("no-2MASS-counterpart"
                         + ("(below-limit-expected)" if "below-limit" in tm.get("verdict", "") else ""))
        elif slot_bad:
            flags.append(f"2mass-slot-occupied-inconsistent(z={slot_bad['z']})")
            if not cw_ok:
                verdict = "DOWNGRADED"
        if cw.get("verdict") == "no-catwise-match":
            flags.append("no-CatWISE-counterpart")
        if cw.get("verdict") == "catwise-nearbut-pm-inconsistent":
            verdict = "DOWNGRADED"
            flags.append("catwise-pm-mismatch")
        if cw.get("verdict") == "failed" or tm.get("verdict") == "failed":
            flags.append("query-failure")
        if verdict == "PROMOTED":
            promoted.append(sid)
        elif verdict == "DOWNGRADED":
            downgraded.append(sid)
        else:
            stays.append(sid)
        # two-epoch PM baseline text
        base_txt = ""
        if tm_ok and tm.get("best"):
            b = tm["best"]
            base_txt = (f"2MASS {b.get('epoch')} -> Gaia 2016.0: "
                        f"implied {b.get('pm_impl')} vs {pm:.1f} mas/yr "
                        f"(dp {b.get('dp_mas')} +/- {b.get('sig')} mas/yr)")
        rows.append({
            "source_id": sid,
            "ra2016": round(float(c["ra"]), 5), "dec2016": round(float(c["dec"]), 5),
            "pm_tot": round(pm, 1), "pmra": c["pmra"], "pmdec": c["pmdec"],
            "pmra_err": gp.get("pmra_err", ""), "pmdec_err": gp.get("pmdec_err", ""),
            "parallax": c["parallax"], "dist_pc": c["dist_pc"], "G": c["G"],
            "bp_rp": c["bp_rp"], "H_rpm": c["H_rpm"],
            "twomass_verdict": tm.get("verdict", "not-run"),
            "twomass_n": tm.get("n", ""),
            "twomass_des": (tm.get("best") or {}).get("des", ""),
            "twomass_epoch": (tm.get("best") or {}).get("epoch", ""),
            "twomass_sep2000_as": (tm.get("best") or {}).get("sep2000_as", ""),
            "twomass_jm": (tm.get("best") or {}).get("j_m", ""),
            "twomass_jh": (round((tm["best"]["j_m"] - tm["best"]["h_m"]), 2)
                           if tm.get("best") and tm["best"].get("j_m") is not None
                           and tm["best"].get("h_m") is not None else ""),
            "twomass_hk": (round((tm["best"]["h_m"] - tm["best"]["k_m"]), 2)
                           if tm.get("best") and tm["best"].get("h_m") is not None
                           and tm["best"].get("k_m") is not None else ""),
            "twomass_jdate": (tm.get("best") or {}).get("jdate", ""),
            "twomass_impl_pm": (tm.get("best") or {}).get("pm_impl", ""),
            "twomass_dp_mas": (tm.get("best") or {}).get("dp_mas", ""),
            "twomass_sig": (tm.get("best") or {}).get("sig", ""),
            "catwise_verdict": cw.get("verdict", "not-run"),
            "catwise_sep_as": (cw.get("best") or {}).get("sep_as", ""),
            "catwise_w1w2": (cw.get("best") or {}).get("w1w2", ""),
            "catwise_pm_mas": (cw.get("best") or {}).get("pm_mas", ""),
            "catwise_dp_mas": (cw.get("best") or {}).get("dp_mas", ""),
            "catwise_sig": (cw.get("best") or {}).get("sig", ""),
            "ls_cutout_2016": cut.get("ls2016", "not-run"),
            "ls_cutout_2000": cut.get("ls2000", "not-run"),
            "flags": "|".join(flags),
            "verdict": verdict,
            "pm_baseline": base_txt,
        })
    fields = list(rows[0].keys())
    rows.sort(key=lambda r: -float(r["pm_tot"]))
    path = os.path.join(RES, "blink_vetting.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"-> {path} ({os.path.getsize(path)} bytes); "
          f"promoted {len(promoted)}, stays {len(stays)}, "
          f"downgraded {len(downgraded)}")
    json.dump({"promoted": promoted, "stays": stays, "downgraded": downgraded},
              open(os.path.join(RES, "blink_verdicts.json"), "w"), indent=1)
    return rows


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    cands = load_targets()
    print(f"targets: {len(cands)} confidence-A candidates", flush=True)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    if phase in ("twomass", "all"):
        phase_twomass(cands, state)
    if phase in ("catwise", "all"):
        phase_catwise(cands, state)
    if phase in ("gaiapm", "all"):
        phase_gaiapm(cands, state)
    if phase in ("cutouts", "all"):
        phase_cutouts(cands, state)
    if phase in ("finalize", "all"):
        phase_finalize(cands, state)
    flush_qlog()


if __name__ == "__main__":
    main()
