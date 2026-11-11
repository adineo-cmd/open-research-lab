#!/usr/bin/env python3
"""Track B v4 - observation-ready spectroscopy target package for the 29
F-21 PROMOTED high-proper-motion candidates (three-epoch coherent motion
2MASS -> WISE -> Gaia, zero catalog identity).

Inputs (already on disk; no network needed by default):
  results/blink_vetting.csv   - the 39 confidence-A rows with per-object
                                verdicts and the F-21 2MASS/CatWISE evidence
  results/blink_state.json    - full IRSA TAP hits per object (2MASS
                                fp_psc: j_m/h_m/k_m/jdate + ph_qual;
                                catwise_2020: w1mpro/w2mpro + measured PM).
                                Queried from IRSA 2026-11-11 in F-21; the
                                script re-queries IRSA live for any object
                                missing from the state file (--live forces
                                a re-pull for all).
  results/chunks/all_high_pm.csv - full Gaia DR3 astrometry (BP, RP,
                                parallax_error, ruwe per source)

Outputs:
  results/spectroscopy_targets.csv - machine-readable package
  results/spectroscopy-targets.md  - human package (written separately,
                                     numbers generated here via --md)

Computed per target: J2000 + epoch-2026.86 coordinates, Galactic l/b,
2MASS JHK + jdate, CatWISE W1/W2, J-H / H-W2 / W1-W2, distance, M_J,
reduced proper motion in J, a color-based spectral-class PLAUSIBILITY
(candidates-not-claims: flagged estimates only), V estimate from G
(Gaia DR2 Carrasco polynomial, extrapolated - see caveat), RA-based
visibility season from a +20 deg site, and a priority score
(brighter J + nearer + tighter PM coherence = first).

Usage: python3 spectroscopy_targets.py [--live] [--md]
"""
import csv
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")
STATE = os.path.join(RES, "blink_state.json")
VET = os.path.join(RES, "blink_vetting.csv")
ALLPM = os.path.join(RES, "chunks", "all_high_pm.csv")

EPOCH_GAIA = 2016.0
EPOCH_WISE = 2015.5
EPOCH_NOW = 2026.86          # 2026-11-11 session date
SITE_LAT = 20.0              # deg, mid-northern reference site
IRSA_URL = "https://irsa.ipac.caltech.edu/TAP"

# Gaia DR2 -> Johnson V: G-V = f(BP-RP), Carrasco et al., Gaia DR2
# documentation sec 5.3.7 Table 5.8, valid -0.5 < BP-RP < 2.75,
# sigma 0.046 mag (fit on bright G<13 solar-metallicity standards -
# EXTRAPOLATED here for BP-RP 2.6-3.5; see caveat in the md).
G_V_BPRP = (-0.01760, -0.006860, -0.1732)

# Approximate disk-dM anchor sequence (M_J, J-H, W1-W2 per SpT).
# Compiled from standard color tables (Pecaut & Mamajek-style M_K/J
# values, WISE colors ~ Skrzypek et al. 2015-like); good to ~0.3-0.5
# mag and ~0.05 mag in color. Used only for qualitative plausibility.
DM_ANCHORS = [
    # (SpT, M_J, J-H, W1-W2)
    ("M0", 5.4, 0.55, 0.02),
    ("M1", 5.9, 0.56, 0.03),
    ("M2", 6.4, 0.57, 0.04),
    ("M3", 6.9, 0.58, 0.06),
    ("M4", 7.5, 0.60, 0.08),
    ("M5", 8.2, 0.62, 0.11),
    ("M6", 9.3, 0.66, 0.16),
    ("M7", 10.7, 0.70, 0.24),
    ("M8", 12.3, 0.68, 0.32),
    ("M9", 13.5, 0.60, 0.40),
]


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


def galactic(ra, dec):
    """Equatorial J2000 -> Galactic l, b (IAU 1958 poles, J2000 frame)."""
    ra_n = math.radians(192.85948)   # RA of Galactic north pole
    dec_n = math.radians(27.12825)   # dec of Galactic north pole
    l_ncp = math.radians(122.93192)  # Galactic longitude of the NCP
    r, d = math.radians(ra), math.radians(dec)
    sinb = math.sin(d) * math.sin(dec_n) + \
        math.cos(d) * math.cos(dec_n) * math.cos(r - ra_n)
    b = math.asin(max(-1.0, min(1.0, sinb)))
    y = math.cos(d) * math.sin(r - ra_n)
    x = math.sin(d) * math.cos(dec_n) - \
        math.cos(d) * math.sin(dec_n) * math.cos(r - ra_n)
    l = (l_ncp - math.atan2(y, x)) % (2 * math.pi)
    return math.degrees(l), math.degrees(b)


def sun_ra_deg(jd):
    """Low-precision solar RA (Meeus-style, ~0.01 deg, fine for seasons)."""
    d = jd - 2451545.0
    L = (280.460 + 0.9856474 * d) % 360.0
    g = math.radians((357.528 + 0.9856003 * d) % 360.0)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 4.0e-7 * d)
    ra = math.degrees(math.atan2(math.cos(eps) * math.sin(lam),
                                 math.cos(lam))) % 360.0
    return ra


def jd_of(year, month, day):
    """Gregorian -> Julian date (Fliegel-Van Flandern)."""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400
    return jdn - 32045.5


def visibility_months(ra_deg):
    """Months (next 12, Dec 2026..Nov 2027) when the target is up at
    night from a +20 deg site, from the target RA vs the mid-month solar
    RA only (documented approximation: ignores declination effects and
    twilight; good to about +/- 2 weeks). A month counts as observable
    when the target is within 4.5 h of RA of the anti-solar point
    (~>6 h/night above moderate airmass for fair declinations)."""
    months = []
    y, m = 2026, 12
    anti = (ra_deg / 15.0 - 12.0) % 24.0
    for _ in range(12):
        ra_sun = sun_ra_deg(jd_of(y, m, 15)) / 15.0
        d = abs((anti - ra_sun + 36.0) % 24.0 - 12.0)  # 0..12 h
        months.append((f"{y}-{m:02d}", round(d, 1)))
        m += 1
        if m > 12:
            m = 1
            y += 1
    obs = [mn for mn, d in months if d < 4.5]
    best = min(months, key=lambda t: t[1])[0]
    return obs, best, months


def ra_hms(ra_deg):
    h = ra_deg / 15.0
    rh = int(h)
    rm = int((h - rh) * 60)
    rs = (h - rh - rm / 60.0) * 3600.0
    return f"{rh:02d}h{rm:02d}m{rs:04.1f}s"


def dec_dms(dec_deg):
    sign = "-" if dec_deg < 0 else "+"
    d = abs(dec_deg)
    dd = int(d)
    dm = int((d - dd) * 60)
    ds = (d - dd - dm / 60.0) * 3600.0
    return f"{sign}{dd:02d}d{dm:02d}m{ds:04.1f}s"


def tap(url, query):
    import urllib.parse
    import urllib.request
    q = urllib.parse.urlencode({"REQUEST": "doQuery", "LANG": "ADQL",
                                "FORMAT": "csv", "QUERY": query})
    req = urllib.request.Request(url + "/sync?" + q,
                                 headers={"User-Agent":
                                          "open-discovery-lab/track-b-v4"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def qlog(rows, phase, sid, svc, q, n):
    rows.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "phase": phase, "source_id": sid, "svc": svc,
                 "n": n, "status": "ok" if n >= 0 else "failed",
                 "query_head": q[:140]})


def fetch_2mass(sid, ra2016, dec2016, pmra, pmdec, pm, qlog_rows):
    """Live IRSA fp_psc cone at the epoch-2000.0 position (same rule as
    blink_vet.py); returns the best hit dict or None."""
    ra2000, dec2000 = propagate(ra2016, dec2016, pmra, pmdec,
                                2000.0 - EPOCH_GAIA)
    radius_as = max(10.0, 1.5 * pm * (EPOCH_GAIA - 1997.25) / 1000.0 + 1.0)
    q = ("SELECT TOP 12 designation, ra, dec, j_m, j_msig, h_m, h_msig,"
         " k_m, k_msig, ph_qual, jdate FROM fp_psc "
         f"WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS',"
         f" {ra2000!r}, {dec2000!r}, {radius_as / 3600.0:.6f}))")
    try:
        body = tap(IRSA_URL, q)
        lines = [r for r in body.splitlines() if r.strip()]
        hits = []
        for row in lines[1:]:
            f = [c.strip().strip('"') for c in row.split(",")]
            if len(f) < 11:
                continue
            h = {"des": f[0], "ra": float(f[1]), "dec": float(f[2])}
            for k, v in zip(("j_m", "j_msig", "h_m", "h_msig", "k_m",
                             "k_msig"), f[3:9]):
                h[k] = None if v == "" else float(v)
            h["ph_qual"] = f[9]
            h["jdate"] = float(f[10]) if f[10] else None
            h["sep2000_as"] = round(ang_sep_as(ra2000, dec2000,
                                               h["ra"], h["dec"]), 2)
            hits.append(h)
        qlog(qlog_rows, "twomass", sid, "irsa-fp_psc", q, len(hits))
        if not hits:
            return None
        # the blink counterpart: nearest to the expected 2000.0 slot
        return min(hits, key=lambda h: h["sep2000_as"])
    except Exception:
        qlog(qlog_rows, "twomass", sid, "irsa-fp_psc", q, -1)
        return None


def fetch_catwise(sid, ra2016, dec2016, pmra, pmdec, pm, qlog_rows):
    """Live IRSA catwise_2020 cone at the epoch-2015.5 position."""
    raw15, dec15 = propagate(ra2016, dec2016, pmra, pmdec,
                             EPOCH_WISE - EPOCH_GAIA)
    radius_as = max(8.0, 1.3 * pm * (EPOCH_GAIA - EPOCH_WISE) / 1000.0 + 2.0)
    q = ("SELECT TOP 8 source_id, ra, dec, w1mpro, w2mpro FROM catwise_2020 "
         f"WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS',"
         f" {raw15!r}, {dec15!r}, {radius_as / 3600.0:.6f}))")
    try:
        body = tap(IRSA_URL, q)
        lines = [r for r in body.splitlines() if r.strip()]
        hits = []
        for row in lines[1:]:
            f = [c.strip().strip('"') for c in row.split(",")]
            if len(f) < 5 or f[3] == "" or f[4] == "":
                continue
            hits.append({"cw_id": f[0], "ra": float(f[1]), "dec": float(f[2]),
                         "w1mpro": float(f[3]), "w2mpro": float(f[4]),
                         "sep_as": round(ang_sep_as(raw15, dec15,
                                                    float(f[1]),
                                                    float(f[2])), 2)})
        qlog(qlog_rows, "catwise", sid, "irsa-catwise_2020", q, len(hits))
        if not hits:
            return None
        return min(hits, key=lambda h: h["sep_as"])
    except Exception:
        qlog(qlog_rows, "catwise", sid, "irsa-catwise_2020", q, -1)
        return None


def load_state_phot(state, sid):
    """2MASS + CatWISE photometry from the F-21 state file (best hits)."""
    s = state.get(sid, {})
    tm, cw = s.get("twomass", {}), s.get("catwise", {})
    tmh, cwb = tm.get("best") or {}, cw.get("best") or {}
    if not tmh and tm.get("hits"):
        tmh = tm["hits"][0]
    if not cwb and cw.get("hits"):
        cwb = cw["hits"][0]
    return (tmh if tmh else None), (cwb if cwb else None)


def sp_class_plausibility(j_h, w1w2, mj, dist):
    """Qualitative spectral-class plausibility from IR colors + M_J.
    Chain: W1-W2 ranks temperature (the disk-dM J-H sequence is nearly
    degenerate 0.5-0.7 over M0-M7), then M_J and J-H are compared to the
    dM anchor AT THAT TEMPERATURE. A subdwarf sits BLUER and FAINTER than
    the disk sequence at matched W1-W2 (metal-poor: suppressed TiO/H2O,
    ~1.5-2.5 mag underluminous in V, less extreme in J). All labels are
    estimates for follow-up, not classifications.
    Returns (label, note)."""
    if 0.0 <= w1w2 <= 0.35:
        near = min(DM_ANCHORS, key=lambda a: abs(a[3] - w1w2))
        temp_from = f"W1-W2={w1w2:.2f}"
    else:
        # W1-W2 outside the dM anchor range: the temperature ranking is
        # unreliable (counterpart photometry suspect); rank from J-H
        near = min(DM_ANCHORS, key=lambda a: abs(a[1] - j_h))
        temp_from = f"J-H={j_h:.2f} (W1-W2={w1w2:.2f} out of anchor range)"
    spt_w, mj_w, jh_w = near[0], near[1], near[2]
    d_mj = mj - mj_w      # + = fainter than dM of same temperature
    d_jh = j_h - jh_w     # - = bluer than dM of same temperature
    flags = []
    if temp_from.startswith("J-H"):
        flags.append(f"{temp_from}: WISE counterpart photometry suspect, "
                     f"temperature ranked from J-H (~{spt_w})")
    if d_jh < -0.12:
        flags.append(f"blue J-H ({j_h:.2f} vs dM-{spt_w} anchor "
                     f"{jh_w:.2f}): metal-poor tendency")
    if d_mj > 1.0:
        flags.append(f"M_J {mj:.1f} is {d_mj:.1f} mag fainter than a disk "
                     f"dM of the same W1-W2 temperature (~{spt_w}): "
                     "subdwarf-consistent")
    elif d_mj < -1.0:
        flags.append(f"M_J {mj:.1f} is {-d_mj:.1f} mag BRIGHTER than a "
                     f"disk dM at this W1-W2 (~{spt_w}): possible "
                     "over-luminosity (binary/blend/parallax) - flag")
    if j_h > 0.9:
        flags.append("very red J-H: verify 2MASS photometry/blend")
    if w1w2 < 0.0:
        flags.append("negative W1-W2 unphysical for a cool photosphere: "
                     "treat WISE photometry/counterpart as suspect")
    if dist > 300:
        flags.append("distance >300 pc: M_J sensitive to parallax "
                     "systematics")

    if d_mj > 1.0 and d_jh < -0.05:
        label = "sdM/esdM-consistent"
    elif (0.5 < d_mj <= 1.0 and d_jh < 0.0) or d_jh < -0.25:
        label = "subdwarf-tendency"
    elif d_mj > 1.0:
        # fainter but NOT bluer than the disk sequence at matched
        # temperature: could be sdM, or a photometry/parallax issue
        label = "underluminous-vs-dM"
    elif d_mj < -1.0:
        label = "overluminous-flag"
    else:
        label = "dM-locus"
    if not flags:
        flags.append("consistent with a disk dM of similar temperature "
                     f"(~{spt_w}); subdwarf vs dwarf needs spectroscopy")
    note = "; ".join(flags) + " [estimate, not a classification]"
    return label, note


def main():
    live = "--live" in sys.argv
    emit_md = "--md" in sys.argv

    state = {}
    if os.path.exists(STATE):
        with open(STATE) as f:
            state = json.load(f)

    with open(VET) as f:
        vet = {r["source_id"]: r for r in csv.DictReader(f)}
    promoted = [sid for sid, r in vet.items() if r["verdict"] == "PROMOTED"]
    print(f"promoted: {len(promoted)}", flush=True)

    # full astrometry (BP, RP, parallax_error, ruwe) from the harvest
    need = set(promoted)
    astro = {}
    with open(ALLPM) as f:
        for r in csv.DictReader(f):
            if r["source_id"] in need:
                astro[r["source_id"]] = r
            if len(astro) == len(need):
                break
    missing = need - set(astro)
    if missing:
        raise SystemExit(f"ids missing from all_high_pm.csv: {sorted(missing)}")

    qlog_rows = []
    rows = []
    for sid in promoted:
        v, a = vet[sid], astro[sid]
        ra16, dec16 = float(a["ra"]), float(a["dec"])
        pmra, pmdec = float(a["pmra"]), float(a["pmdec"])
        pm = math.hypot(pmra, pmdec)
        plx = float(a["parallax"])
        dist = 1000.0 / plx
        G = float(a["phot_g_mean_mag"])
        bp_rp = float(a["bp_rp"])
        ruwe = float(a["ruwe"])

        tmh, cwb = load_state_phot(state, sid)
        if tmh is None or live:
            tmh = fetch_2mass(sid, ra16, dec16, pmra, pmdec, pm, qlog_rows) \
                or tmh
            time.sleep(1.5)
        if cwb is None or live:
            cwb = fetch_catwise(sid, ra16, dec16, pmra, pmdec, pm,
                                qlog_rows) or cwb
            time.sleep(1.5)
        if tmh is None or cwb is None:
            raise SystemExit(f"{sid}: missing photometry after "
                             f"state+live (tm={tmh is not None}, "
                             f"cw={cwb is not None})")

        J, H, K = tmh["j_m"], tmh["h_m"], tmh["k_m"]
        jdate = tmh["jdate"]
        W1, W2 = cwb["w1mpro"], cwb["w2mpro"]
        j_h = round(J - H, 3)
        h_w2 = round(H - W2, 3)
        w1w2 = round(W1 - W2, 3)

        mj = J - 5.0 * math.log10(dist) + 5.0
        mj = round(mj, 2)
        # reduced proper motion in J (mu in arcsec/yr)
        h_j = round(J + 5.0 * math.log10(pm / 1000.0) - 5.0, 2)
        label, note = sp_class_plausibility(j_h, w1w2, mj, dist)

        # V estimate (extrapolated Carrasco DR2 polynomial)
        x = bp_rp
        g_v = G_V_BPRP[0] + G_V_BPRP[1] * x + G_V_BPRP[2] * x * x
        V_est = round(G - g_v, 2)   # V = G - (G-V)

        ra2000, dec2000 = propagate(ra16, dec16, pmra, pmdec,
                                    2000.0 - EPOCH_GAIA)
        ranow, decnow = propagate(ra16, dec16, pmra, pmdec,
                                  EPOCH_NOW - EPOCH_GAIA)
        l, b = galactic(ra2000, dec2000)
        obs, best, _ = visibility_months(ra2000)

        rows.append({
            "source_id": sid, "twomass_des": tmh["des"],
            "catwise_sep_as": cwb.get("sep_as"),
            "ra_j2000": round(ra2000, 5), "dec_j2000": round(dec2000, 5),
            "ra_now": round(ranow, 5), "dec_now": round(decnow, 5),
            "epoch_now": EPOCH_NOW,
            "ra_hms": ra_hms(ra2000), "dec_dms": dec_dms(dec2000),
            "glon": round(l, 2), "glat": round(b, 2),
            "pm_tot": round(pm, 1), "pmra": round(pmra, 1),
            "pmdec": round(pmdec, 1),
            "parallax_mas": round(plx, 3),
            "parallax_error_mas": float(a["parallax_error"]),
            "dist_pc": round(dist, 1),
            "G": G, "bp_rp": bp_rp, "ruwe": ruwe,
            "V_est": V_est,
            "J": J, "H": H, "K": K,
            "j_h": j_h, "h_w2": h_w2, "w1_w2": w1w2,
            "M_J": mj, "H_J_rpm": h_j,
            "twomass_jdate": jdate,
            "twomass_epoch": round((jdate - 2451545.0) / 365.25 + 2000.0, 2),
            "ph_qual": tmh.get("ph_qual", ""),
            "blink_z": round(float(v["twomass_dp_mas"]) /
                             float(v["twomass_sig"]), 2),
            "catwise_w1w2_pmcheck": vet[sid]["catwise_w1w2"],
            "sp_class_estimate": label,
            "sp_note": note,
            "obs_months": ";".join(obs),
            "best_month": best,
        })

    # priority score: brighter J + nearer + tighter PM coherence = first
    js = [r["J"] for r in rows]
    ds = [r["dist_pc"] for r in rows]
    zs = [r["blink_z"] for r in rows]
    jlo, jhi, dlo, dhi, zlo, zhi = min(js), max(js), min(ds), max(ds), \
        min(zs), max(zs)
    for r in rows:
        fj = 1 - (r["J"] - jlo) / (jhi - jlo)
        fd = 1 - (r["dist_pc"] - dlo) / (dhi - dlo)
        fz = 1 - (r["blink_z"] - zlo) / (zhi - zlo)
        r["priority"] = round(10 * (0.5 * fj + 0.3 * fd + 0.2 * fz), 1)
    rows.sort(key=lambda r: (-r["priority"], r["J"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    with open(os.path.join(RES, "spectroscopy_targets.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()),
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    if qlog_rows:
        qpath = os.path.join(RES, "spectroscopy_querylog.csv")
        new = not os.path.exists(qpath)
        with open(qpath, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["ts", "phase", "source_id",
                                              "svc", "n", "status",
                                              "query_head"],
                               lineterminator="\n")
            if new:
                w.writeheader()
            w.writerows(qlog_rows)

    print(f"wrote {len(rows)} rows -> spectroscopy_targets.csv "
          f"({len(qlog_rows)} live IRSA queries)")
    if emit_md:
        for r in rows:
            print(f"{r['rank']:2d} P{r['priority']:4.1f} {r['twomass_des']}"
                  f" J={r['J']:.2f} J-H={r['j_h']:.2f} H-W2={r['h_w2']:.2f}"
                  f" W1-W2={r['w1_w2']:.2f} d={r['dist_pc']:.0f}pc"
                  f" MJ={r['M_J']:.1f} V~{r['V_est']:.1f}"
                  f" {r['sp_class_estimate']} best={r['best_month']}")


if __name__ == "__main__":
    main()
