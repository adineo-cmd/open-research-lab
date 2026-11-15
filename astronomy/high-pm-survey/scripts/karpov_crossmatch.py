#!/usr/bin/env python3
"""B-4: cross-check the lab's high-PM candidate list against Karpov, Malkov &
Avdeeva 2025, "New ultracool dwarf candidates from multi-epoch WISE data",
A&A 695, A195 (arXiv:2408.15067), catalog J/A+A/695/A195.

What exists of that catalog (established 2026-11-15, see results/karpov_crosscheck.md):
  - VizieR J/A+A/695/A195 deposits exactly ONE table, "table2" = the 258
    previously-unpublished objects ("New high-proper-motion objects detected
    in this work"; no SIMBAD and no Gaia DR3/DR2 association by construction).
  - The same table (93 cols) is published by the authors on Zenodo,
    doi:10.5281/zenodo.14651237 (file new_moving_final.vot).
  - The FULL 21,885-detection list is NOT published as a table anywhere
    (not in the VizieR deposit, not on arXiv, not on Zenodo).  So this
    crosscheck runs against the 258-unpublished subset only; verdicts are
    phrased accordingly.

Crossmatch method (epoch-aware):
  - Our candidates: Gaia DR3 positions at epoch 2016.0, pmra already
    includes cos(dec).
  - Karpov table2: raj2016/dej2016 are documented at Ep=J2016.0 (ReadMe +
    Zenodo field names raj2016/dej2016; the paper propagated its tracks to
    J2016.0 to match Gaia DR3 with a 2" radius).  So the common epoch is
    2016.0 for BOTH sides and the propagation term vanishes; the general
    formula is kept so the script stays correct if a per-row-epoch table
    is ever substituted.
  - Accept radius = max(2.5", 1.5 * pm_karp * |t_karp - 2016.0| + 2") = 2.5".
    Near-matches out to 5" are recorded but flagged for manual review.
  - Client-side separations only (numpy, RA/Dec window prefilter; no server
    DISTANCE() anywhere).

Verdicts (candidates-not-claims):
  - "karpov-corroborated (unpublished)" : match inside the 258 with a PM
    vector consistent with Gaia's (dp < 5 sigma).  Independent-discovery
    overlap: both surveys found it; the "uncatalogued" claim narrows to
    "uncatalogued in SIMBAD; newly listed by Karpov 2025".
  - "karpov-contradiction (flag only)"  : positional match but PM vector
    disagrees at >= 5 sigma -> possible coincidence, needs eyes.
  - "no-karpov-detection"               : nothing inside tolerance.  NOTE:
    Karpov's base list (21,885) also has a Gaia-associated published
    portion (~21,627 objects) that was NOT retrievable; a non-detection
    here does NOT rule out presence in that portion.  For pm < ~300 mas/yr
    objects Karpov's ~0.3"/yr motion floor also means a miss can simply
    reflect their flux/quality cuts.

  EXPECTED OUTCOME (realized 2026-11-15): our whole 621 cohort has pm
  160-250 mas/yr, strictly below Karpov's structural detection floor
  (pairs of unTimely detections >=3" apart over a ~10.9 yr baseline ->
  ~275-300 mas/yr), so "no-karpov-detection" for all 621 is the
  by-construction result, not a statement about candidate quality.

Inputs (cached under /tmp/astro_e, refetched if absent):
  results/possible_new_final.csv   621 candidates (source_id, ra2016, dec2016, ...)
  /tmp/astro_e/gaia621.csv         Gaia DR3 vectors for the 621 (TAP fetch)
  /tmp/astro_e/karpov258.csv       Karpov 258 (Zenodo VOTable -> csv)

Outputs:
  results/karpov_crossmatch.csv    one row per candidate (621 rows)
  /tmp/astro_e/karpov_hits.json    dossier of every hit (manual review)
"""

import csv
import json
import math
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np

REPO = "/home/aditya/repos/open-research-lab/astronomy/high-pm-survey"
CACHE = "/tmp/astro_e"
GAIA_EPOCH = 2016.0

CAND_CSV = f"{REPO}/results/possible_new_final.csv"
GAIA_CSV = f"{CACHE}/gaia621.csv"
KAR_CSV = f"{CACHE}/karpov258.csv"
OUT_CSV = f"{REPO}/results/karpov_crossmatch.csv"
HITS_JSON = f"{CACHE}/karpov_hits.json"
QLOG = f"{REPO}/results/karpov_querylog.csv"

KAR_DOI_RESOLVER = "https://zenodo.org/api/records/14651237/files/new_moving_final.vot/content"
KAR_VIZIER_FALLBACK = "https://vizier.cfa.harvard.edu/viz-bin/asu-tsv?-source=J/A%2BA/695/A195/table2&-out=all"


def log_route(route, status, nbytes, outcome):
    """Append one line to results/karpov_querylog.csv (append mode)."""
    import datetime
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    newfile = not os.path.exists(QLOG)
    with open(QLOG, "a", newline="") as f:
        w = csv.writer(f)
        if newfile:
            w.writerow(["timestamp", "route", "status", "bytes", "outcome"])
        w.writerow([ts, route, status, nbytes, outcome])


def http_get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "open-research-lab/1.0 (B-4 crosscheck)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------- inputs
def load_candidates():
    out = []
    with open(CAND_CSV) as f:
        lines = [l for l in f if not l.startswith("#")]
        for r in csv.DictReader(lines):
            out.append(r)
    return out


def fetch_gaia621(cands):
    """Gaia DR3 vectors for the candidate source_ids via gaia.aip.de sync TAP."""
    ids = [c["source_id"] for c in cands]
    chunks = [ids[i::2] for i in range(2)]  # split IN-list in halves
    rows = {}
    ns = {"v": "http://www.ivoa.net/xml/VOTable/v1.3"}
    for part, chunk in zip("ab", chunks):
        q = ("SELECT source_id,ra,dec,pmra,pmdec,pmra_error,pmdec_error,parallax,parallax_error,"
             "phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag,bp_rp,ruwe "
             f"FROM gaiadr3.gaia_source WHERE source_id IN ({','.join(chunk)})")
        data = urllib.parse.urlencode(
            {"LANG": "ADQL", "FORMAT": "votable", "REQUEST": "doQuery", "QUERY": q}
        ).encode()
        req = urllib.request.Request("https://gaia.aip.de/tap/sync", data=data)
        with urllib.request.urlopen(req, timeout=300) as r:
            xml = r.read()
        root = ET.fromstring(xml)
        table = root.find(".//v:TABLE", ns)
        fields = [f.get("name") for f in table.findall("v:FIELD", ns)]
        n = 0
        for tr in table.findall(".//v:TR", ns):
            vals = [td.text if td.text is not None else "" for td in tr.findall("v:TD", ns)]
            r = dict(zip(fields, vals))
            rows[r["source_id"]] = r
            n += 1
        log_route(f"gaia.aip.de sync TAP chunk {part}", "200", len(xml),
                  f"{n} rows for {len(chunk)} ids")
    with open(GAIA_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(next(iter(rows.values())).keys()))
        w.writeheader()
        for sid in sorted(rows):
            w.writerow(rows[sid])
    return rows


def load_gaia(cands):
    if os.path.exists(GAIA_CSV):
        rows = {}
        with open(GAIA_CSV) as f:
            for r in csv.DictReader(f):
                rows[r["source_id"]] = r
        if all(c["source_id"] in rows for c in cands):
            log_route(f"cache {GAIA_CSV}", "hit", os.path.getsize(GAIA_CSV),
                      f"{len(rows)} Gaia DR3 rows reused")
            return rows
    return fetch_gaia621(cands)


def fetch_karpov258():
    """Fetch the Karpov 258-unpublished table (Zenodo primary, VizieR fallback)."""
    try:
        raw = http_get(KAR_DOI_RESOLVER, timeout=180)
        log_route("zenodo record 14651237 new_moving_final.vot", "200", len(raw),
                  "downloaded; parse VOTable")
        root = ET.fromstring(raw)
        ns = {"v": "http://www.ivoa.net/xml/VOTable/v1.3"}
        table = root.find(".//v:TABLE", ns)
        fields = [f.get("name") for f in table.findall("v:FIELD", ns)]
        rows = []
        for tr in table.findall(".//v:TR", ns):
            vals = [td.text if td.text is not None else "" for td in tr.findall("v:TD", ns)]
            rows.append(dict(zip(fields, vals)))
        assert len(rows) == 258, f"unexpected row count {len(rows)}"
        keep = ["candid", "cwise", "raj2016", "dej2016", "pmra", "e_pmra", "pmdec",
                "e_pmdec", "pm", "e_pm", "W1", "e_W1", "W2", "e_W2", "spt",
                "dist", "dist_err", "vtan", "vtan_err"]
        with open(KAR_CSV, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(keep)
            for r in rows:
                w.writerow([r.get(k, "") for k in keep])
        log_route("zenodo record 14651237 new_moving_final.vot", "parsed", len(raw),
                  f"{len(rows)} rows x {len(fields)} fields -> {KAR_CSV}")
        return rows
    except Exception as e:  # noqa: BLE001 - honest fallback chain
        log_route("zenodo record 14651237 new_moving_final.vot", "fail", 0, repr(e))
    # fallback: VizieR table2 TSV
    raw = http_get(KAR_VIZIER_FALLBACK, timeout=300)
    lines = raw.decode(errors="replace").splitlines()
    body = [l for l in lines if not l.startswith("#") and l.strip()]
    hdr = body[0].split("\t")
    rows = []
    for l in body:
        parts = [p.strip() for p in l.split("\t")]
        if not parts[0].isdigit():
            continue
        rows.append(dict(zip(hdr, parts)))
    assert len(rows) == 258, f"unexpected row count {len(rows)}"
    keep = ["Candid", "CWISE", "RA_ICRS", "DE_ICRS", "pmRA", "e_pmRA", "pmDE",
            "e_pmDE", "PM", "e_PM", "W1", "e_W1", "W2", "e_W2", "SpType",
            "Dist", "e_Dist", "Vtan", "e_Vtan"]
    with open(KAR_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candid", "cwise", "raj2016", "dej2016", "pmra", "e_pmra",
                    "pmdec", "e_pmdec", "pm", "e_pm", "W1", "e_W1", "W2", "e_W2",
                    "spt", "dist", "dist_err", "vtan", "vtan_err"])
        for r in rows:
            w.writerow([r.get(k, "") for k in keep])
    log_route("vizier.cfa.harvard.edu asu-tsv J/A+A/695/A195/table2", "200", len(raw),
              f"{len(rows)} rows -> {KAR_CSV} (zenodo route failed)")
    return rows


def load_karpov():
    if os.path.exists(KAR_CSV):
        with open(KAR_CSV) as f:
            rows = list(csv.DictReader(f))
        if len(rows) == 258:
            log_route(f"cache {KAR_CSV}", "hit", os.path.getsize(KAR_CSV),
                      "258 Karpov rows reused")
            return rows
    return fetch_karpov258()


# ------------------------------------------------------------ crossmatch
def ang_sep_arcsec(ra1, de1, ra2, de2):
    """Great-circle separation in arcsec; inputs in degrees (numpy broadcast)."""
    r1, d1, r2, d2 = (np.radians(x) for x in (ra1, de1, ra2, de2))
    sd = np.sin((d2 - d1) / 2.0)
    sr = np.sin((r2 - r1) / 2.0)
    a = sd * sd + np.cos(d1) * np.cos(d2) * sr * sr
    return np.degrees(2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))) * 3600.0


def crossmatch(cands, gaia, karpov):
    # --- Karpov side at its catalog epoch (2016.0, documented) ---
    k_ra = np.array([float(r["raj2016"]) for r in karpov])
    k_de = np.array([float(r["dej2016"]) for r in karpov])
    k_pmra = np.array([float(r["pmra"]) for r in karpov]) * 1000.0   # -> mas/yr
    k_pmde = np.array([float(r["pmdec"]) for r in karpov]) * 1000.0
    k_era = np.array([float(r["e_pmra"] or "nan") for r in karpov]) * 1000.0
    k_ede = np.array([float(r["e_pmdec"] or "nan") for r in karpov]) * 1000.0
    k_epoch = np.full(len(karpov), GAIA_EPOCH)

    hits = []      # list of dicts, one per (candidate, karpov row) pair
    for c in cands:
        g = gaia[c["source_id"]]
        ra16, de16 = float(g["ra"]), float(g["dec"])
        g_pmra, g_pmde = float(g["pmra"]), float(g["pmdec"])
        g_era = float(g["pmra_error"] or "nan")
        g_ede = float(g["pmdec_error"] or "nan")
        # epoch-aware: propagate Gaia 2016.0 position to each Karpov row epoch
        # (here t_karp == 2016.0 exactly, so dt = 0; kept general on purpose)
        dt = k_epoch - GAIA_EPOCH
        # pmra includes cos(dec) already
        ra_prop = ra16 + (g_pmra / 3.6e6) * dt / np.maximum(np.cos(np.radians(de16)), 1e-6)
        de_prop = de16 + (g_pmde / 3.6e6) * dt
        # coarse prefilter: +-3 deg dec window, half-hour RA window scaled by cos(dec)
        pm_k_max = np.hypot(k_pmra, k_pmde) / 3.6e6  # deg/yr
        dtmax = np.abs(dt) + 1.0
        window = np.maximum(3.0 / 3600.0 + pm_k_max * dtmax, 3.0 / 3600.0)
        dec_ok = np.abs(de_prop - k_de) < window
        ra_ok = np.abs((ra_prop - k_ra) * np.cos(np.radians(k_de))) < window
        cand_idx = np.where(ra_ok & dec_ok)[0]
        if len(cand_idx) == 0:
            continue
        sep = ang_sep_arcsec(ra_prop[cand_idx], de_prop[cand_idx],
                             k_ra[cand_idx], k_de[cand_idx])
        # accept radius: max(2.5", 1.5*pm_k*|dt| + 2"); here dt=0 -> 2.5"
        radius = np.maximum(2.5, 1.5 * (np.hypot(k_pmra[cand_idx], k_pmde[cand_idx]) / 1000.0)
                            * np.abs(dt[cand_idx]) + 2.0)
        for j, (idx, s) in enumerate(zip(cand_idx, sep)):
            kr = karpov[idx]
            dp_ra = k_pmra[idx] - g_pmra
            dp_de = k_pmde[idx] - g_pmde
            dp = math.hypot(dp_ra, dp_de)
            sra = math.hypot(k_era[idx], g_era)   # gaia err floor 0.5 if null
            sde = math.hypot(k_ede[idx], g_ede)
            sig = math.hypot(sra, sde)
            z = dp / sig if sig > 0 else float("inf")
            rec = dict(
                source_id=c["source_id"],
                karpov_row=idx,
                candid=kr["candid"], cwise=kr["cwise"],
                sep_as=float(s),
                radius_as=float(radius[j]),
                karpov_epoch=float(k_epoch[idx]),
                karpov_pmra_mas=float(k_pmra[idx]),
                karpov_pmdec_mas=float(k_pmde[idx]),
                karpov_e_pmra=float(k_era[idx]), karpov_e_pmdec=float(k_ede[idx]),
                gaia_pmra=g_pmra, gaia_pmdec=g_pmde,
                gaia_e_pmra=g_era, gaia_e_pmdec=g_ede,
                dp_vector_mas=dp, dp_sigma=sig, dp_z=z,
                w1=float(kr["W1"]) if kr["W1"] else None,
                w2=float(kr["W2"]) if kr["W2"] else None,
                w1w2=(float(kr["W1"]) - float(kr["W2"])) if kr["W1"] and kr["W2"] else None,
                spt=kr["spt"], karpov_dist=kr["dist"], gaia_parallax=g["parallax"],
                gaia_g=g["phot_g_mean_mag"], gaia_bp_rp=g["bp_rp"],
                inside=bool(s <= radius[j]),
            )
            if s <= radius[j] or s <= 5.0:   # accept + near-band for review
                hits.append(rec)
    return hits


def verdict_for(rec):
    if not rec["inside"]:
        return None  # near-band only, manual review
    if rec["dp_z"] < 5.0:
        return "karpov-corroborated (unpublished)"
    return "karpov-contradiction (flag only)"


def selftest(gaia, karpov):
    """Inject a synthetic candidate exactly on a Karpov row (same PM) and
    confirm the matcher recovers it at sep~0 with dp_z~0."""
    row = karpov[0]
    sid = "999999999999999999"
    fake = {"ra": row["raj2016"], "dec": row["dej2016"],
            "pmra": float(row["pmra"]) * 1000, "pmdec": float(row["pmdec"]) * 1000,
            "pmra_error": "0.5", "pmdec_error": "0.5", "parallax": "5",
            "parallax_error": "0.1", "phot_g_mean_mag": "19.5",
            "phot_bp_mean_mag": "19.0", "phot_rp_mean_mag": "16.0",
            "bp_rp": "3.0", "ruwe": "1.0"}
    fc = [{"source_id": sid, "ra2016": row["raj2016"], "dec2016": row["dej2016"]}]
    hits = [h for h in crossmatch(fc, {sid: fake}, karpov) if h["inside"]]
    assert len(hits) == 1 and hits[0]["sep_as"] < 0.01 and hits[0]["dp_z"] < 1.0, hits
    print(f"SELFTEST PASSED: synthetic twin of karpov row 0 recovered "
          f"(sep {hits[0]['sep_as']:.4f}\", dp_z {hits[0]['dp_z']:.2f})")


def main():
    cands = load_candidates()
    gaia = load_gaia(cands)
    karpov = load_karpov()
    print(f"candidates: {len(cands)}  gaia rows: {len(gaia)}  karpov rows: {len(karpov)}")
    if "--selftest" in sys.argv:
        selftest(gaia, karpov)

    # sanity: our candidate positions ARE Gaia 2016.0 positions
    worst = 0.0
    for c in cands:
        g = gaia[c["source_id"]]
        worst = max(worst, ang_sep_arcsec(float(c["ra2016"]), float(c["dec2016"]),
                                          float(g["ra"]), float(g["dec"])))
    print(f"max candidate-vs-gaia position offset: {worst:.3f} arcsec (expect ~0)")

    hits = crossmatch(cands, gaia, karpov)
    inside = [h for h in hits if h["inside"]]
    near = [h for h in hits if not h["inside"]]
    print(f"inside-tolerance hits: {len(inside)}   near-band (2.5-5\") hits: {len(near)}")

    for h in hits:
        h["verdict"] = verdict_for(h)

    # --- per-candidate roll-up ---
    prio = set()
    pv = f"{CACHE}/priority35.csv"
    if os.path.exists(pv):
        with open(pv) as f:
            prio = {r["source_id"] for r in csv.DictReader(f)}

    by_sid = {}
    for h in hits:
        by_sid.setdefault(h["source_id"], []).append(h)

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "pm_mas", "karpov_match_count", "best_match_sep_as",
                    "karpov_epoch", "karpov_pmra_mas", "karpov_pmdec_mas",
                    "dp_vector_mas", "dp_sigma_mas", "dp_z",
                    "karpov_candid", "karpov_cwise", "in_unpublished258",
                    "priority35", "verdict", "note"])
        for c in cands:
            sid = c["source_id"]
            hh = [h for h in by_sid.get(sid, []) if h["inside"]]
            pm_mas = float(c["pm"])
            below_floor = pm_mas < 275.0  # Karpov 3"/~11yr unTimely pair floor
            if hh:
                best = min(hh, key=lambda h: h["sep_as"])
                # consistent verdict for the candidate: corroborated unless ALL
                # matches contradict
                verdicts = [h["verdict"] for h in hh]
                v = ("karpov-corroborated (unpublished)"
                     if "karpov-corroborated (unpublished)" in verdicts
                     else "karpov-contradiction (flag only)")
                w.writerow([sid, f"{pm_mas:.1f}", len(hh), f"{best['sep_as']:.3f}",
                            f"{best['karpov_epoch']:.1f}",
                            f"{best['karpov_pmra_mas']:.1f}",
                            f"{best['karpov_pmdec_mas']:.1f}",
                            f"{best['dp_vector_mas']:.1f}",
                            f"{best['dp_sigma']:.1f}",
                            f"{best['dp_z']:.2f}",
                            best["candid"], best["cwise"], "y",
                            "y" if sid in prio else "n", v, ""])
            else:
                w.writerow([sid, f"{pm_mas:.1f}", 0, "", "", "", "", "", "", "",
                            "", "", "n",
                            "y" if sid in prio else "n", "no-karpov-detection",
                            "below-karpov-motion-floor" if below_floor else ""])
    print(f"wrote {OUT_CSV}")

    with open(HITS_JSON, "w") as f:
        json.dump({"inside": inside, "near": near}, f, indent=1)
    print(f"wrote {HITS_JSON}")

    n_prio_hit = sum(1 for h in inside if h["source_id"] in prio)
    n_all_hit = len({h["source_id"] for h in inside})
    print(f"HEADLINE (vs the 258-unpublished subset, the only published table):")
    print(f"  priority-35 candidates matched: {n_prio_hit}")
    print(f"  all-621 candidates matched:     {n_all_hit}")
    print(f"  full-21885 comparison: NOT COMPUTABLE (that list is unpublished)")


if __name__ == "__main__":
    main()
