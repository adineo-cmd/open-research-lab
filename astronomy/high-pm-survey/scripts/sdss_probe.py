#!/usr/bin/env python3
"""sdss_probe.py — ROADMAP B-2 retry: SDSS (SkyServer) epoch-2000s blink for
the 35 v3 blink survivors (29 PROMOTED + 6 CONF-A-STAYS), plus endpoint
probing of every route that died in the 2026-11-11 session.

Background: blink_vetting.md "Honest failures" records that on 2026-11-11
SkyServer ImgCutout 404'd on DR16/17/18, crossid.aspx returned no rows, and
NOAO Data Lab was unreachable (DNS / timeout). This script re-probes the
current endpoints (3 attempts each, 20 s timeouts) and logs EVERY HTTP
attempt append-mode to results/sdss_querylog.csv (same style as
results/blink_querylog.csv: ts,phase,sid,ra,dec,svc,n,s,err).

Routes probed:
  - SkyServer DR18 ImgCutout getjpg (test point ra=167.41774 dec=43.81838,
    the v3 shortlist #1) — and DR19 if DR18 fails.
  - SkyServer DR18 crossid.aspx (POST coordinate list; GET fallback).
  - SkyServer DR18 SQL Search (POST cmd=...&format=csv to
    /dr18/en/tools/search/sql.aspx), cone on PhotoObjAll joined to Field
    for per-frame mjd.
  - https://skyserver.sdss.org/dr18/en/help/browser/ (docs reachability).
  - NOAO Data Lab TAP (datalab.noirlab.edu and legacy datalab.noao.edu).
  - DECam LS viewer https://www.legacysurvey.org/decamals/.
  - Gaia TAP mirrors (gaia.aip.de, ESA gea.esac.esa.int) — used by the
    task-2 confidence recompute (parallax_error per source_id).

Blink method (if SkyServer SQL works), mirroring blink_vet.py's rules:
  - positions propagated from Gaia DR3 epoch 2016.0 with propagate()
    (pmra includes cos(dec)); cone CENTERED at the epoch-2000.0 position;
    cone radius = max(3", 1.5 x pm x |t_sdss - 2016.0| + 1) evaluated at the
    worst case of the SDSS epoch range (t >= 2000 -> |t-2016| <= 16 yr);
    per-hit scoring uses the hit's own mjd-derived epoch.
  - implied PM vector = (hit_pos - gaia_pos@2016.0) x 1000 / (t_sdss - 2016.0)
    mas/yr per component (full two-epoch displacement, the blink_vet.py
    2MASS rule); dp = |implied - Gaia PM vector|; sigma =
    sqrt((0.5"/baseline)^2 + 0.5^2) mas/yr (0.5" = SDSS astrometry + match
    tolerance; 0.5 mas/yr = Gaia PM error floor). Consistent iff
    dp <= 3 x max(sigma, 8).
  - verdicts: sdss-corroborated / sdss-none(at limit?) / sdss-interloper /
    sdss-contradiction (slot rule: a source within 2.5" of the expected
    position at its epoch whose implied PM contradicts Gaia at >5 sigma).
  - one 256px ImgCutout jpeg per candidate at the 2000.0 position, saved to
    /tmp/astro_f (never committed), http status recorded.

Separations are computed client-side (IRSA DISTANCE() rule: never trust
server-side distance units on these services).

Every number in results/sdss_blink.csv/md comes from a logged HTTP response.
Candidates, not claims.

Usage: python3 sdss_probe.py [probe|blink|gaiaplx|all]
"""
import csv
import http.cookiejar
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
QLOG = os.path.join(RES, "sdss_querylog.csv")
TMP = "/tmp/astro_f"
STATE = os.path.join(TMP, "sdss_state.json")

EPOCH_GAIA = 2016.0
EPOCH_CAT = 2000.0
GAIA_PMERR_FLOOR = 0.5   # mas/yr, floor for Gaia PM error (G~20)
SDSS_POS_ERR = 0.5       # arcsec, SDSS astrometry + match tolerance
SIGMA_FLOOR = 8.0        # mas/yr, floor for implied-PM sigma (as 2MASS rule)
SLOT_TOL_AS = 2.5        # slot rule radius (as blink_vet.py)

TEST_RA, TEST_DEC = 167.41774, 43.81838  # 778994474926961152 (v3 shortlist #1)

UA = "open-discovery-lab/0.3 (sdss_probe retry of 2026-11-11 B-2)"

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


def logq(phase, sid, ra, dec, svc, n, s, err=""):
    QLOG_LIST.append({"ts": now_iso(), "phase": phase, "sid": sid,
                      "ra": ra, "dec": dec, "svc": svc, "n": n, "s": s,
                      "err": err})


def http_req(url, method="GET", data=None, headers=None, timeout=20.0,
             attempts=3):
    """Fetch with retries; return (status_or_0, body_bytes, err_str, secs).
    status 0 = transport-level failure. HTTPError carries the status code."""
    hdrs = {"User-Agent": UA}
    if headers:
        hdrs.update(headers)
    last_err, t0 = "", time.time()
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs,
                                         method=method)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return (r.status, r.read(), "", time.time() - t0)
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read(4096)
            except Exception:
                pass
            return (e.code, body, f"HTTP {e.code}", time.time() - t0)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            time.sleep(2 * (attempt + 1))
    return (0, b"", last_err, time.time() - t0)


def tap_sync(base, query, timeout=20.0, attempts=3):
    q = urllib.parse.urlencode({
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query})
    status, body, err, dt = http_req(f"{base}?{q}", timeout=timeout,
                                     attempts=attempts)
    return status, body.decode("utf-8", "replace"), err, dt


def parse_tap_csv(body):
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines or lines[0].lstrip().startswith("<?xml"):
        raise ValueError("TAP returned XML (error page?)")
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


def mjd_to_year(mjd):
    """SDSS MJD -> decimal epoch (MJD 51544.5 = J2000.0 = epoch 2000.0)."""
    return (mjd - 51544.5) / 365.25 + 2000.0


def fmt_s(x):
    return str(round(x, 2)) if isinstance(x, (int, float)) else str(x)


# --------------------------------------------------------------------------
# phase: probe
# --------------------------------------------------------------------------

SQL_TEST = ("SELECT TOP 5 p.objid, p.ra, p.dec, p.run, p.camcol, p.field,"
            " p.psfMag_g, p.psfMag_r, p.clean, f.mjd"
            " FROM PhotoObjAll AS p"
            " JOIN Field AS f ON p.run=f.run AND p.camcol=f.camcol"
            "  AND p.field=f.field"
            f" WHERE p.ra BETWEEN {TEST_RA - 0.01:.5f}"
            f" AND {TEST_RA + 0.01:.5f}"
            f" AND p.dec BETWEEN {TEST_DEC - 0.01:.5f}"
            f" AND {TEST_DEC + 0.01:.5f} AND p.clean=1")

SQL_NEARBY = ("SELECT TOP 5 p.objid, p.ra, p.dec, p.psfMag_r, f.mjd"
              " FROM PhotoObjAll AS p"
              " JOIN dbo.fGetNearbyObjEq(167.41774, 43.81838, 0.5) AS nb"
              " ON p.objid = nb.objid"
              " JOIN Field AS f ON p.run=f.run AND p.camcol=f.camcol"
              "  AND p.field=f.field")

CROSSID_BODY = f"{TEST_RA},{TEST_DEC}\n"


def probe_imgcutout(ver, path="ImgCutout"):
    url = (f"https://skyserver.sdss.org/{ver}/{path}/getjpg"
           f"?ra={TEST_RA}&dec={TEST_DEC}&scale=0.2&width=256&height=256"
           f"&opt=&query=")
    st, body, err, dt = http_req(url, timeout=20, attempts=3)
    kind = ""
    if st == 200:
        kind = ("jpeg" if body[:2] == b"\xff\xd8" else
                f"not-jpeg({body[:40]!r})")
    n = len(body) if st == 200 else -1
    logq("probe", "", TEST_RA, TEST_DEC, f"skyserver-{ver}-{path}-getjpg", n,
         fmt_s(dt), err or kind)
    return {"status": st, "bytes": len(body), "kind": kind or err,
            "err": err}


def probe_docs(url, tag):
    st, body, err, dt = http_req(url, timeout=20, attempts=3)
    logq("probe", "", "", "", f"docs-{tag}", len(body) if st == 200 else -1,
         fmt_s(dt), err)
    return {"status": st, "bytes": len(body), "err": err}


def probe_crossid(ver, base=""):
    url = (f"https://skyserver.sdss.org/{ver}/{base}crossid.aspx"
           f"?u=n&version={ver}")
    variants = [
        ("POST-raw", url, CROSSID_BODY.encode(),
         {"Content-Type": "text/plain"}),
        ("POST-form", url,
         urllib.parse.urlencode({"data": CROSSID_BODY.strip()}).encode(),
         {"Content-Type": "application/x-www-form-urlencoded"}),
    ]
    out = []
    for tag, u, data, hdrs in variants:
        st, body, err, dt = http_req(u, method="POST", data=data,
                                     headers=hdrs, timeout=20, attempts=3)
        text = body.decode("utf-8", "replace")
        nrows = -1
        if st == 200:
            lines = [l for l in text.splitlines() if l.strip()]
            nrows = max(0, len(lines) - 1) if lines else 0
        logq("probe", "", TEST_RA, TEST_DEC,
             f"skyserver-{ver}-{base or ''}crossid-{tag}", nrows, fmt_s(dt),
             err or (text[:60].replace("\n", " ") if st != 200 else ""))
        out.append({"variant": tag, "status": st, "rows": nrows, "err": err,
                    "head": text[:200]})
    return out


def probe_sql(ver, query, tag):
    url = f"https://skyserver.sdss.org/{ver}/en/tools/search/sql.aspx"
    data = urllib.parse.urlencode({"cmd": query, "format": "csv"}).encode()
    st, body, err, dt = http_req(url, method="POST", data=data,
                                 headers={"Content-Type":
                                          "application/x-www-form-urlencoded"},
                                 timeout=20, attempts=3)
    text = body.decode("utf-8", "replace")
    is_csv = st == 200 and not text.lstrip().startswith("<")
    nrows = -1
    if is_csv:
        lines = [l for l in text.splitlines() if l.strip()]
        nrows = max(0, len(lines) - 1) if lines else 0
    logq("probe", "", TEST_RA, TEST_DEC, f"skyserver-{ver}-sql-{tag}",
         nrows, fmt_s(dt), err or ("" if is_csv else
                                   "html-error-page(" + text.replace(
                                       "\n", " ")[100:220] + ")"))
    return {"variant": tag, "status": st, "rows": nrows, "err": err,
            "head": text[:400]}


def probe_sql_simple(ver):
    q_simple = ("SELECT TOP 3 objid, ra, dec, psfMag_r FROM PhotoObjAll"
                f" WHERE ra BETWEEN {TEST_RA - 0.005:.5f}"
                f" AND {TEST_RA + 0.005:.5f}"
                f" AND dec BETWEEN {TEST_DEC - 0.005:.5f}"
                f" AND {TEST_DEC + 0.005:.5f}")
    return [probe_sql(ver, q_simple, "simple-nojoin"),
            probe_sql(ver, SQL_TEST, "join-field"),
            probe_sql(ver, SQL_NEARBY, "fGetNearbyObjEq")]


def probe_datalab(host, query, tag):
    url = f"https://{host}/tap/sync"
    st, body, err, dt = http_req(
        url + "?" + urllib.parse.urlencode({
            "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv",
            "QUERY": query}),
        timeout=20, attempts=3)
    text = body.decode("utf-8", "replace")
    nrows = -1
    if st == 200:
        lines = [l for l in text.splitlines() if l.strip()]
        nrows = max(0, len(lines) - 1)
    logq("probe", "", "", "", f"datalab-{host}-{tag}", nrows, fmt_s(dt),
         err or ("" if nrows >= 0 else text[:80].replace("\n", " ")))
    return {"status": st, "rows": nrows, "err": err, "head": text[:300]}


def probe_decamals():
    url = "https://www.legacysurvey.org/decamals/"
    st, body, err, dt = http_req(url, timeout=20, attempts=3)
    logq("probe", "", "", "", "legacysurvey-decamals",
         len(body) if st == 200 else -1, fmt_s(dt), err)
    return {"status": st, "bytes": len(body), "err": err}


def probe_gaia_tap(name, base):
    q = ("SELECT TOP 1 source_id, parallax, parallax_error FROM"
         " gaiadr3.gaia_source WHERE source_id = 778994474926961152")
    st, text, err, dt = tap_sync(base, q, timeout=20, attempts=3)
    nrows = -1
    if st == 200:
        try:
            nrows = len(parse_tap_csv(text)) - 1
        except Exception as e:
            err = f"parse: {e}"
    logq("probe", "778994474926961152", "", "", f"gaia-{name}-tap", nrows,
         fmt_s(dt), err or ("" if nrows >= 0 else
                            text[:120].replace("\n", " ")))
    return {"status": st, "rows": nrows, "err": err, "head": text[:400]}


def phase_probe():
    out = {}
    out["imgcut-dr18-ImgCutout"] = probe_imgcutout("dr18", "ImgCutout")
    out["imgcut-dr18-SkyServerWS"] = probe_imgcutout("dr18", "SkyServerWS/imgcutout")
    out["imgcut-dr19-SkyServerWS"] = probe_imgcutout("dr19", "SkyServerWS/imgcutout")
    out["docs-skyserver-help"] = probe_docs(
        "https://help.skyserver.sdss.org/dr18/en/help/browser/", "help-host")
    out["docs-skyserver-en-help"] = probe_docs(
        "https://skyserver.sdss.org/dr18/en/help", "en-help")
    out["crossid-dr18"] = probe_crossid("dr18")
    out["crossid-dr18-en-tools"] = probe_crossid("dr18", "en/tools/")
    out["sql-dr18"] = probe_sql_simple("dr18")
    if all(r["rows"] <= 0 for r in out["sql-dr18"]):
        out["sql-dr19"] = probe_sql_simple("dr19")
    out["datalab-lsdr9"] = probe_datalab(
        "datalab.noirlab.edu", "SELECT TOP 1 ra, dec FROM ls_dr9.tractor",
        "tap-lsdr9")
    out["datalab-sdss17"] = probe_datalab(
        "datalab.noirlab.edu",
        "SELECT TOP 1 objid, ra, dec, mjd FROM sdss_dr17.photoobj",
        "tap-sdss_dr17-photoobj")
    out["datalab-sdss18"] = probe_datalab(
        "datalab.noirlab.edu",
        "SELECT TOP 1 objid, ra, dec, mjd FROM sdss_dr18.photoobj",
        "tap-sdss_dr18-photoobj")
    out["datalab-gaiadr3"] = probe_datalab(
        "datalab.noirlab.edu",
        "SELECT TOP 1 source_id, parallax, parallax_error FROM"
        " gaia_dr3.gaia_source", "tap-gaia_dr3")
    out["datalab-noao"] = probe_datalab(
        "datalab.noao.edu", "SELECT TOP 1 ra, dec FROM ls_dr9.tractor",
        "tap-lsdr9")
    out["decamals"] = probe_decamals()
    out["gaia-aip"] = probe_gaia_tap("aip", "https://gaia.aip.de/tap/sync")
    out["gaia-esa"] = probe_gaia_tap(
        "esa", "https://gea.esac.esa.int/tap-server/tap/sync")
    flush_qlog()
    print(json.dumps(out, indent=1, default=str))
    return out


# --------------------------------------------------------------------------
# phase: blink (35 v3 survivors) — routes verified working 2026-11-15:
#   SQL:  GET /dr18/SearchTools/sql (form, CSRF token) then POST same path
#         with fields searchtool=SQL, TaskName=Skyserver.Search.SQL,
#         syntax=NoSyntax, ReturnHtml=false, cmd=<SQL>, format=CSV,
#         TableName="", __RequestVerificationToken=<token>.
#         (The legacy /dr18/en/tools/search/sql.aspx POST 500s.)
#   Cutouts: /dr18/SkyServerWS/ImgCutout/getjpeg (getjpg is 404).
#   Field table carries per-band mjd_u..mjd_z -> use f.mjd_r.
# --------------------------------------------------------------------------

DOWNGRADED = {"5286902985287361280", "3424352381146733824",
              "6645353862012156928", "4829516627852875904"}


class SkyServerSession:
    """SkyServer DR18 form-driven session (cookies + CSRF token)."""

    def __init__(self, ver="dr18"):
        self.ver = ver
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj))
        self.token = None

    def _fetch_token(self):
        req = urllib.request.Request(
            f"https://skyserver.sdss.org/{self.ver}/SearchTools/sql",
            headers={"User-Agent": UA})
        with self.op.open(req, timeout=25) as r:
            pg = r.read().decode("utf-8", "replace")
        mt = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',
                       pg)
        if not mt:
            raise RuntimeError("no CSRF token on SQL Search form")
        self.token = mt.group(1)

    def sql(self, query, timeout=60):
        """POST a SQL query; returns (status, text). Retries once with a
        fresh token on the generic SkyServer error page."""
        for attempt in range(2):
            if self.token is None:
                self._fetch_token()
            fields = {"searchtool": "SQL", "TaskName": "Skyserver.Search.SQL",
                      "syntax": "NoSyntax", "ReturnHtml": "false",
                      "cmd": query, "format": "CSV", "TableName": "",
                      "__RequestVerificationToken": self.token}
            data = urllib.parse.urlencode(fields).encode()
            req = urllib.request.Request(
                f"https://skyserver.sdss.org/{self.ver}/SearchTools/sql",
                data=data,
                headers={"User-Agent": UA,
                         "Content-Type":
                         "application/x-www-form-urlencoded"})
            try:
                with self.op.open(req, timeout=timeout) as r:
                    text = r.read().decode("utf-8", "replace")
                    st = r.status
            except urllib.error.HTTPError as e:
                text, st = e.read().decode("utf-8", "replace"), e.code
            if st == 200 and not text.lstrip().startswith("<"):
                return st, text
            if attempt == 0:
                self._fetch_token()
        return st, text


def load_targets():
    """The 35 v3 survivors (39 confidence-A minus 4 DOWNGRADED), with
    astrometry from results/blink_vetting.csv."""
    rows = []
    with open(os.path.join(RES, "blink_vetting.csv")) as f:
        for r in csv.DictReader(f):
            if r["verdict"] == "DOWNGRADED" or r["source_id"] in DOWNGRADED:
                continue
            rows.append(r)
    assert len(rows) == 35, f"expected 35 survivors, got {len(rows)}"
    return rows


def cone_query(c):
    """SDSS cone SQL at the epoch-2000.0 position. Cone radius is the
    task rule max(3", 1.5 x pm x |t_sdss-2016| + 1) evaluated at the SDSS
    epoch-range worst case (t >= 2000 -> |t-2016| <= 16.2 yr); per-hit
    scoring then applies the rule at each hit's own epoch. Box padded 1.5x;
    exact angular separation applied client-side. LEFT JOIN SpecObjAll for
    spectroscopic z (empty for almost all faint G~20 objects)."""
    ra, dec = float(c["ra2016"]), float(c["dec2016"])
    pmra, pmdec = float(c["pmra"]), float(c["pmdec"])
    pm = math.hypot(pmra, pmdec)
    ra2000, dec2000 = propagate(ra, dec, pmra, pmdec, EPOCH_CAT - EPOCH_GAIA)
    r_as = max(3.0, 1.5 * pm * 16.2 / 1000.0 + 1.0)
    pad = r_as / 3600.0
    ra_lo = ra2000 - 1.5 * pad / max(math.cos(math.radians(dec2000)), 0.02)
    ra_hi = ra2000 + 1.5 * pad / max(math.cos(math.radians(dec2000)), 0.02)
    dec_lo, dec_hi = dec2000 - 1.5 * pad, dec2000 + 1.5 * pad
    q = ("SELECT TOP 20 p.objid, p.run, p.camcol, p.field, p.ra, p.dec,"
         " p.psfMag_g, p.psfMag_r, p.psfMag_z, p.psfMagErr_r, p.clean,"
         " f.mjd_r, s.z AS spec_z, s.class AS spec_class"
         " FROM PhotoObjAll AS p"
         " JOIN Field AS f ON p.run=f.run AND p.camcol=f.camcol"
         "  AND p.field=f.field"
         " LEFT JOIN SpecObjAll AS s ON p.objid = s.bestObjID"
         f" WHERE p.ra BETWEEN {ra_lo:.6f} AND {ra_hi:.6f}"
         f" AND p.dec BETWEEN {dec_lo:.6f} AND {dec_hi:.6f} AND p.clean=1")
    return q, ra2000, dec2000, r_as


def cutout_status(url, fn):
    """Fetch an image cutout; classify ok / no-coverage / error."""
    for attempt in range(2):
        st, body, err, dt = http_req(url, timeout=45, attempts=1)
        if st == 200:
            if len(body) < 200 or not body.startswith(b"\xff\xd8"):
                return "no-coverage"
            with open(fn, "wb") as f:
                f.write(body)
            return f"ok({len(body)}b)"
        if st in (400, 404):
            return "no-coverage"
        time.sleep(2)
    return f"http-{err}" if st == 0 else f"http-{st}"


def phase_blink(ver="dr18"):
    os.makedirs(TMP, exist_ok=True)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    targets = load_targets()
    print(f"blink targets: {len(targets)} v3 survivors", flush=True)
    sess = SkyServerSession(ver)
    results = []
    for i, c in enumerate(targets, 1):
        sid = c["source_id"]
        if sid in state:
            print(f"  {i}/35 {sid}: cached", flush=True)
            results.append(state[sid]["row"])
            continue
        ra, dec = float(c["ra2016"]), float(c["dec2016"])
        pmra, pmdec = float(c["pmra"]), float(c["pmdec"])
        pm = math.hypot(pmra, pmdec)
        q, ra2000, dec2000, r_as = cone_query(c)
        rec = {"n": 0, "verdict": "failed"}
        try:
            st, text = sess.sql(q)
            if st != 200:
                raise RuntimeError(f"HTTP {st}: {text[:120]}")
            lines = [l for l in text.splitlines()
                     if l.strip() and not l.startswith("#")]
            rows = list(csv.reader(lines))
            hdr, data = rows[0], rows[1:]
            col = {name: k for k, name in enumerate(hdr)}
            hits = []
            cosd = math.cos(math.radians(dec))
            for row in data:
                if len(row) < len(hdr):
                    continue
                def num(k):
                    v = row[col[k]]
                    return float(v) if v not in ("", "null", "NULL") else None
                h = {"objid": row[col["objid"]],
                     "mjd": num("mjd_r"),
                     "ra": float(row[col["ra"]]),
                     "dec": float(row[col["dec"]]),
                     "g": num("psfMag_g"), "r": num("psfMag_r"),
                     "zz": num("psfMag_z"), "rerr": num("psfMagErr_r"),
                     "run": row[col["run"]], "camcol": row[col["camcol"]],
                     "field": row[col["field"]],
                     "spec_z": row[col["spec_z"]] if col.get("spec_z") is not None else "",
                     "spec_class": row[col["spec_class"]] if col.get("spec_class") is not None else ""}
                if h["mjd"]:
                    t = mjd_to_year(h["mjd"])
                    h["epoch"] = round(t, 2)
                    base = abs(t - EPOCH_GAIA)
                    e_ra, e_dec = propagate(ra, dec, pmra, pmdec,
                                            t - EPOCH_GAIA)
                    h["sep_track_as"] = round(ang_sep_as(e_ra, e_dec,
                                                         h["ra"], h["dec"]), 2)
                    h["sep2000_as"] = round(ang_sep_as(ra2000, dec2000,
                                                       h["ra"], h["dec"]), 2)
                    # implied PM over the full SDSS->Gaia baseline
                    dra = (h["ra"] - ra) * cosd * 3600.0
                    ddec = (h["dec"] - dec) * 3600.0
                    pm_i_ra = dra * 1000.0 / (t - EPOCH_GAIA)
                    pm_i_dec = ddec * 1000.0 / (t - EPOCH_GAIA)
                    dpra, dpdec = pm_i_ra - pmra, pm_i_dec - pmdec
                    h["pm_impl"] = round(math.hypot(pm_i_ra, pm_i_dec), 1)
                    h["dp_mas"] = round(math.hypot(dpra, dpdec), 1)
                    sig = math.sqrt((SDSS_POS_ERR * 1000.0 / base) ** 2
                                    + GAIA_PMERR_FLOOR ** 2)
                    h["sig"] = round(sig, 1)
                    h["z"] = round(h["dp_mas"] / sig, 2)
                    h["r_formal"] = round(max(3.0, 1.5 * pm * base / 1000.0
                                              + 1.0), 1)
                if h.get("g") is not None and h.get("r") is not None:
                    h["g_r"] = round(h["g"] - h["r"], 2)
                hits.append(h)
            # task cone rule at each hit's own epoch: within
            # max(3", 1.5 x pm x |t_sdss-2016| + 1") of the 2000.0 center
            hits = [h for h in hits
                    if h.get("sep2000_as", 9e9) <= h.get("r_formal", 9e9)]
            rec["n"] = len(hits)
            rec["n_raw"] = len(data)
            rec["hits"] = hits
            consistent = [h for h in hits if h.get("z") is not None
                          and h["dp_mas"] <= 3.0 * max(h["sig"], SIGMA_FLOOR)]
            slot_bad = [h for h in hits if h.get("z") is not None
                        and h["z"] > 5.0
                        and h["sep_track_as"] <= SLOT_TOL_AS]
            if consistent:
                best = sorted(consistent, key=lambda h: (h["dp_mas"],
                                                         h["sep_track_as"]))[0]
                rec["best"] = best
                rec["verdict"] = "sdss-corroborated"
            elif slot_bad:
                best = sorted(slot_bad, key=lambda h: h["sep_track_as"])[0]
                rec["best"] = best
                rec["verdict"] = "sdss-contradiction"
            elif hits:
                best = sorted(hits, key=lambda h: (h.get("dp_mas") or 9e9,
                                                   h["sep2000_as"]))[0]
                rec["best"] = best
                rec["verdict"] = "sdss-interloper"
            else:
                rec["verdict"] = "sdss-none"
                if len(data) == 0:
                    rec["limit_note"] = ("no SDSS DR18 photo objects in the "
                                         "padded box -> outside SDSS "
                                         "footprint (no coverage)")
                else:
                    rec["limit_note"] = (
                        "field has SDSS objects but none within the cone "
                        "rule; G~19.9 is ~2 mag brighter than the SDSS "
                        "r~22.2 5-sigma depth -> not a depth-limit artifact")
            logq("sdss-sql", sid, round(ra2000, 5), round(dec2000, 5),
                 f"skyserver-{ver}-photoobj-cone", rec["n"], "")
        except Exception as e:
            rec["verdict"] = "failed"
            rec["error"] = str(e)[:140]
            logq("sdss-sql", sid, round(ra2000, 5), round(dec2000, 5),
                 f"skyserver-{ver}-photoobj-cone", -1, "", str(e)[:80])
        # cutout at the 2000.0 position (256px)
        try:
            cu = (f"https://skyserver.sdss.org/{ver}/SkyServerWS/ImgCutout"
                  f"/getjpeg?ra={ra2000:.6f}&dec={dec2000:.6f}&scale=0.2"
                  f"&width=256&height=256&opt=&query=")
            rec["cutout"] = cutout_status(
                cu, os.path.join(TMP, f"{sid}_sdss2000.jpg"))
            logq("sdss-cutout", sid, round(ra2000, 5), round(dec2000, 5),
                 f"skyserver-{ver}-SkyServerWS-imgcutout-getjpeg",
                 1 if rec["cutout"].startswith("ok") else 0, "",
                 rec["cutout"])
        except Exception as e:
            rec["cutout"] = "http-error"
            logq("sdss-cutout", sid, round(ra2000, 5), round(dec2000, 5),
                 f"skyserver-{ver}-SkyServerWS-imgcutout-getjpeg", -1, "",
                 str(e)[:80])
        b = rec.get("best") or {}
        row = {
            "source_id": sid, "pm_tot": round(pm, 1), "G": c["G"],
            "ra2000": round(ra2000, 5), "dec2000": round(dec2000, 5),
            "n_in_cone": rec["n"], "n_raw_box": rec.get("n_raw", ""),
            "sdss_objid": b.get("objid", ""),
            "sdss_run": b.get("run", ""), "sdss_mjd_r": b.get("mjd", ""),
            "sdss_epoch": b.get("epoch", ""),
            "sep_track_as": b.get("sep_track_as", ""),
            "sep2000_as": b.get("sep2000_as", ""),
            "psfMag_r": b.get("r", ""), "g_r": b.get("g_r", ""),
            "psfMag_z": b.get("zz", ""),
            "spec_z": b.get("spec_z", ""), "spec_class": b.get("spec_class", ""),
            "impl_pm_mas": b.get("pm_impl", ""),
            "gaia_pm_mas": round(pm, 1),
            "dp_mas": b.get("dp_mas", ""), "sig_mas": b.get("sig", ""),
            "z_sigma": b.get("z", ""),
            "verdict": rec["verdict"],
            "sdss_cutout_2000": rec.get("cutout", ""),
            "note": rec.get("limit_note", rec.get("error", "")),
        }
        results.append(row)
        state[sid] = {"row": row}
        json.dump(state, open(STATE, "w"))
        flush_qlog()
        print(f"  {i}/35 {sid}: {rec['verdict']} n={rec['n']}", flush=True)
        time.sleep(1.2)
    flush_qlog()
    fields = list(results[0].keys())
    path = os.path.join(RES, "sdss_blink.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
    print(f"-> {path} ({os.path.getsize(path)} bytes)")
    from collections import Counter
    print("verdicts:", dict(Counter(r["verdict"] for r in results)))
    return results


# --------------------------------------------------------------------------
# phase: gaiaplx (task-2 recompute input: parallax_error per source_id)
# --------------------------------------------------------------------------

def phase_gaiaplx(base="https://datalab.noirlab.edu/tap/sync", chunk=125):
    """Pull parallax, parallax_error for the 621 possible-new source_ids
    (batched ADQL id-list queries). Saved to /tmp/astro_f/gaia_plx.csv.
    Data Lab gaia_dr3.gaia_source verified 2026-11-15 (probe: candidate
    778994474926961152 -> parallax 4.0233, parallax_error 0.7348; matches
    the committed spectroscopy_targets.csv values)."""
    os.makedirs(TMP, exist_ok=True)
    lines = open(os.path.join(RES, "possible_new_final.csv")).read().splitlines()
    rows = list(csv.DictReader(lines[1:]))
    sids = [r["source_id"] for r in rows]
    print(f"gaiaplx: {len(sids)} source_ids", flush=True)
    out = []
    for i in range(0, len(sids), chunk):
        batch = sids[i:i + chunk]
        q = ("SELECT source_id, parallax, parallax_error, pmra, pmdec"
             " FROM gaia_dr3.gaia_source WHERE source_id IN ("
             + ",".join(batch) + ")")
        t0 = time.time()
        try:
            st, text, err, dt = tap_sync(base, q, timeout=60, attempts=3)
            tbl = parse_tap_csv(text)
            hdr = [h.strip() for h in tbl[0]]
            got = 0
            for row in tbl[1:]:
                out.append(dict(zip(hdr, row)))
                got += 1
            logq("gaiaplx", f"batch{i // chunk}", "", "",
                 "datalab-gaia_dr3-gaia_source", got, fmt_s(dt), err)
            print(f"  batch {i // chunk}: {got} rows", flush=True)
        except Exception as e:
            logq("gaiaplx", f"batch{i // chunk}", "", "",
                 "datalab-gaia_dr3-gaia_source", -1,
                 fmt_s(time.time() - t0), str(e)[:80])
            print(f"  batch {i // chunk}: FAILED {e}", flush=True)
        flush_qlog()
        time.sleep(1.0)
    path = os.path.join(TMP, "gaia_plx.csv")
    if out:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            w.writeheader()
            w.writerows(out)
        print(f"-> {path} ({len(out)} rows)", flush=True)
    return out


# --------------------------------------------------------------------------
# phase: conf_fix (task 2: Rule-1 stale-counts fix in possible_new_final.csv)
# --------------------------------------------------------------------------

NOTE_OLD_START = "# NOTE (2026-11-11, improvement sweep):"
NOTE_NEW = (
    "# NOTE (2026-11-15, Rule-1 fix): the conf column's stale counts "
    "(A 39 / B 310 / C 16 / blank 256) were corrected to the authoritative "
    "vetting counts A 39 / B 555 / C 27 (results/vetting_v2.md funnel "
    "summary). 11 rows re-set from blank to C: 9 with parallax S/N < 5 "
    "(parallax_error re-pulled live from Gaia DR3 via Data Lab TAP, identity "
    "verified against committed parallax values: 152 cross-checks, 0 "
    "mismatches) and 2 carrying the M1 evidence token (margin<2 / "
    "corridor-match class; semantics validated by the 3 already-C M1 rows "
    "whose plx/CatWISE evidence cannot explain C). The CatWISE PM-ratio C "
    "row (5036731890598470912) and all 16 previously-C rows are unchanged; "
    "all other columns byte-identical. The 39-id confidence-A set is "
    "set-identical to results/blink_vetting.csv (39 v3 rows). Per-row "
    "derivation: results/sdss_blink.md task-2 section; recompute input "
    "regenerated by `python3 scripts/sdss_probe.py gaiaplx`. Full-fidelity "
    "file still regenerates via scripts/vet2.py finalize + "
    "scripts/apply_lit_checks.py (state + candidates.csv not committed).")


def phase_conf_fix():
    """Fix the stale conf counts in results/possible_new_final.csv.

    Derivation (vet2.py finalize rule, restricted to what committed data +
    the live Gaia DR3 parallax pull can verify):
      A : the 39-id v2 confidence-A set (results/blink_vetting.csv rows;
          verified set-identical to the file's current A rows)
      C : any C-condition holds --
            - plx S/N < 5 (recomputed: parallax/parallax_error from live
              Gaia DR3, round(plx/err, 1) exactly as vet2.py),
            - M1 evidence token (margin<2 / implied-epoch corridor class),
            - CatWISE PM ratio < 0.5 or > 2 (5036731890598470912, per
              vetting_v2.md; already C),
            - rows currently C stay C (task rule)
      B : everything else (including margin-missing "M?" rows: finalize
          defaults margin to 99 when empty, and their plx S/N >= 5)
    Only the conf field of the 11 affected rows and the leading NOTE line
    change; row order and all other columns byte-identical.
    """
    path = os.path.join(RES, "possible_new_final.csv")
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    assert lines[0].startswith("# NOTE (2026-11-11, improvement sweep):")
    rows = list(csv.DictReader(lines[1:]))
    blink = list(csv.DictReader(open(os.path.join(RES, "blink_vetting.csv"))))
    A_set = {r["source_id"] for r in blink}
    assert len(A_set) == 39
    gal = {r["source_id"]: r
           for r in csv.DictReader(open(os.path.join(TMP, "gaia_plx.csv")))}
    assert set(gal) == {r["source_id"] for r in rows}

    def plx_sn(sid):
        g = gal[sid]
        try:
            return round(float(g["parallax"]) / float(g["parallax_error"]), 1)
        except Exception:
            return None

    before = {}
    new_conf = {}
    for i, line in enumerate(lines[2:], 2):
        if not line.strip():
            continue
        fields = line.split(",")
        assert len(fields) == 8, f"unexpected column count at line {i}"
        sid, conf, ev = fields[0], fields[6], fields[7]
        before[sid] = conf
        sn = plx_sn(sid)
        if sid in A_set:
            nc = "A"
        elif conf == "C":
            nc = "C"
        elif (sn is not None and sn < 5.0) or ev.startswith("M1|"):
            nc = "C"
        else:
            nc = "B"
        new_conf[sid] = nc
        if nc != conf:
            fields[6] = nc
            lines[i] = ",".join(fields)
    from collections import Counter
    bc = Counter(before.values())
    ac = Counter(new_conf.values())
    print("before:", {k: bc.get(k, 0) for k in ("A", "B", "C", "")})
    print("after: ", {k: ac.get(k, 0) for k in ("A", "B", "C", "")})
    changed = [(sid, before[sid], new_conf[sid]) for sid in before
               if before[sid] != new_conf[sid]]
    print(f"changed rows: {len(changed)}")
    for sid, b, a in changed:
        print(f"  {sid}: {b or 'blank'!r} -> {a}")
    assert ac == Counter({"B": 555, "A": 39, "C": 27}), ac
    # NOTE line: replace, same single line, same endings
    lines[0] = NOTE_NEW
    out = nl.join(lines)
    if not out.endswith(nl):
        out += nl
    with open(path, "w", newline="") as f:
        f.write(out)
    print(f"-> {path} written "
          f"(line endings {'CRLF' if nl == chr(13) + chr(10) else 'LF'})")


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "probe"
    if phase in ("probe", "all"):
        phase_probe()
    if phase in ("blink", "all"):
        phase_blink()
    if phase in ("gaiaplx", "all"):
        phase_gaiaplx()
    if phase == "conf_fix":
        phase_conf_fix()
    flush_qlog()


if __name__ == "__main__":
    main()
