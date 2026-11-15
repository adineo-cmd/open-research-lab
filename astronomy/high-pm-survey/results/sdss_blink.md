# SDSS (SkyServer) epoch-2000s imagery/catalog blink — ROADMAP B-2 retry, + Rule-1 conf fix

Status: complete (2026-11-15 session). Script: `scripts/sdss_probe.py`
(endpoint probing + SDSS SQL cone blink + ImgCutout fetches + Gaia
parallax pull); evidence CSV: `results/sdss_blink.csv`; append-mode query
log: `results/sdss_querylog.csv` (223 entries, 10:19:56Z-10:45:46Z UTC).
**Candidates, not claims** — nothing here is a discovery claim; these
remain *possible-new candidates* until spectroscopic follow-up.

## Context

The 2026-11-11 session (blink_vetting.md "Honest failures") could not use
the SDSS (~2000-2006) third epoch: `ImgCutout/getjpg` 404 on DR16/17/18,
`crossid.aspx` no rows, NOAO Data Lab unreachable (DNS / timeout). This
session re-probed every one of those routes with current endpoints (3
attempts each, 20 s timeouts, every attempt logged), found that the
SkyServer portal is alive but **reorganized** (ASP.NET MVC routes +
anti-CSRF tokens), and ran the full SDSS blink for the 35 v3 survivors
(29 PROMOTED + 6 CONF-A-STAYS; the 4 DOWNGRADED ids 5286902985287361280,
3424352381146733824, 6645353862012156928, 4829516627852875904 are
excluded, as in v3).

## Route table (definitive — every route, so nobody retries blind)

| route | status | outcome |
|---|---|---|
| `skyserver.sdss.org/dr18/ImgCutout/getjpg` (legacy path) | HTTP 404 (10:19:56Z) | dead |
| `skyserver.sdss.org/dr19/ImgCutout/getjpg` | HTTP 404 (10:19:57Z) | dead |
| `.../dr18/SkyServerWS/imgcutout/getjpg` (lowercase variants) | HTTP 404 (10:23:57Z) | dead — wrong case/name |
| `.../dr18/SkyServerWS/ImgCutout/getjpeg` | **200, JPEG** (10:34:04Z) | **WORKS** (also on dr15). `getjpeg`, not `getjpg`; path found from the DR15 URL embedded in the DR18 Navigate tool page |
| `http://` (non-TLS) ImgCutout | HTTP 404 | dead |
| `crossid.aspx` legacy (`/dr18/crossid.aspx`, `/dr18/en/tools/crossid.aspx`; POST-raw / POST-form / GET, `u=n&version=dr18`) | HTTP 404 (10:20:04-18Z) | dead (path gone) |
| NEW crossid `/dr18/CrossMatchTools/ObjectCrossID` | page 200; 5 POST payload variants (raw body, form-encoded, multipart file-upload with field `upload`, all with CSRF token) 10:34:52-35:11Z | **FAILED** — every POST returns the generic "Error 500 · request ..." page; superseded by the SQL route (superset evidence) |
| legacy SQL POST `/dr18/en/tools/search/sql.aspx` (`cmd`+`format=csv`) | HTTP 200 but HTML "Error 500" page (10:20:07Z, 10:24:19Z, 10:28:29Z) | dead for scripted use — the form requires `__RequestVerificationToken` + session cookies |
| **NEW SQL** `/dr18/SearchTools/sql` — GET the form (CSRF token + cookies) then POST `searchtool=SQL&TaskName=Skyserver.Search.SQL&syntax=NoSyntax&ReturnHtml=false&cmd=<SQL>&format=CSV&TableName=<>&__RequestVerificationToken=<token>` | **200 CSV** (10:32:07Z probe, 10:32:48Z token flow) | **WORKS** — this is the blink route |
| SkyServer schema notes | — | `Field` carries per-band `mjd_u..mjd_z` (plain `mjd` is invalid); PhotoObjAll↔SpecObjAll join key is `p.objid = s.bestObjID` (verified reachable 10:34:03Z; empty at the test point) |
| SkyServer docs (`help.skyserver.sdss.org`, `/dr18/en/help/browser/`, `/dr18/en/help`) | DNS failure / HTTP 404 (10:20:03Z, 10:24:12-13Z) | unreachable; endpoint discovery done from the SQL Search form page HTML instead |
| `datalab.noirlab.edu/tap/sync` (Data Lab TAP) | **200** (10:20:24Z) | **WORKS** — used for the task-2 Gaia DR3 parallax pull (`gaia_dr3.gaia_source`); `ls_dr9.tractor` also answers |
| `datalab.noao.edu` (legacy host) | DNS "Name or service not known" (10:20:37Z) | dead (unchanged from 2026-11-11) |
| Data Lab `sdss_dr17.photoobj` / `sdss_dr18.photoobj` | TAP ERROR "Table not found" (10:24:46-54Z) | Data Lab carries **no SDSS photometric object catalog** — `sdss_dr*` schemas are spectro-only (`specobj`, `photoplate`, ...; TAP_SCHEMA 10:27:54-30:49Z); the SDSS catalog blink had to go through SkyServer itself |
| `www.legacysurvey.org/decamals/` | HTTP 404 (10:20:38Z) | dead (DECaLS tile-viewer path gone; the LS-DR9 `viewer/jpeg-cutout` route used by v3 was already verified in that session) |
| `gaia.aip.de/tap/sync` | 200, QUERY_STATUS OK but returns VOTABLE even with FORMAT=csv (10:20:40Z; POST variant 10:28:40Z) | reachable; superseded by Data Lab (CSV) for the parallax pull |
| `gea.esac.esa.int/tap-server/tap/sync` (ESA Gaia archive) | timeout after 3 attempts (10:21:52Z, 10:26:34Z) | unreachable |

## Method (identical rules to blink_vet.py, SDSS epoch)

Positions are propagated from Gaia DR3 epoch 2016.0 with the same
`propagate()` (pmra includes cos(dec)); separations are computed
client-side (the IRSA `DISTANCE()` rule: never trust server-side distance
units). For each of the 35 survivors:

1. **Cone**: centered at the epoch-2000.0 position; radius =
   max(3", 1.5 x pm x |t_sdss - 2016.0| + 1), evaluated per hit at its own
   SDSS epoch and at the range worst case (t >= 2000 -> |t-2016| <= 16.2 yr,
   ~7" at pm ~ 250 mas/yr) for the query box; exact separations applied
   client-side. One SkyServer SQL query per candidate:
   `PhotoObjAll` (psfMag_g/r/z + errors, clean=1) JOIN `Field` ON
   run/camcol/field for the per-frame `mjd_r` (SDSS MJD -> epoch:
   (mjd - 51544.5)/365.25 + 2000.0), LEFT JOIN `SpecObjAll` for
   spectroscopic z (empty for these G~19.9 objects).
2. **Implied-PM rule** (same rule as blink_vet.py's 2MASS test): implied
   PM vector = (hit position - Gaia 2016.0 position) x 1000 /
   (t_sdss - 2016.0) mas/yr per component (full two-epoch displacement);
   dp = |implied - Gaia PM vector|; sigma = sqrt((0.5"/baseline)^2 +
   0.5^2) mas/yr (0.5" = SDSS astrometry + match tolerance; 0.5 mas/yr =
   Gaia PM error floor). Consistent iff dp <= 3 x max(sigma, 8).
3. **Slot rule**: a source within 2.5" of the expected position at its
   epoch whose implied PM contradicts Gaia at >5 sigma = contradiction;
   field stars elsewhere in the cone = interloper.
4. **Verdicts**: `sdss-corroborated` / `sdss-none` / `sdss-interloper` /
   `sdss-contradiction`. For every candidate one 256px (51") ImgCutout
   jpeg was fetched at the 2000.0 position into /tmp/astro_f (never
   committed) and its http status recorded.

## Funnel

| stage | rows | out |
|---|---|---|
| v3 survivors entering B-2 (39 conf-A minus 4 DOWNGRADED) | 35 | 35 |
| SDSS DR18 coverage at the 2000.0 position (catalog box empty AND ImgCutout 4xx — both agree per object) | 35 | 18 covered / 17 no-coverage |
| SDSS-era (2000.3-2009.1) detection at the propagated position, implied PM consistent | 18 covered | **18 corroborated** / 0 interloper / 0 contradiction / 0 failed |

## Results (35 rows; positions = epoch-2000.0; dp = |implied - Gaia| mas/yr)

| source_id | ra,dec 2000.0 | objid | run | epoch | sep_track" | psfMag_r | g-r | impl pm | Gaia pm | dp ± sig (z) | verdict | cutout 2000 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2813361564957760896 | 352.035190 14.110800 | 1237652942635073908 | 1739 | 2000.74 | 0.07 | 21.23 | 1.56 | 248.2 | 249.9 | 4.7 ± 32.8 (0.14) | corroborated | ok(4393b) |
| 5390732032963218560 | 166.404270 -39.292450 | - | - | - | - | - | - | - | 248.9 | - | none | no-coverage |
| 324266972833697920 | 33.711100 30.248010 | 1237678892283724266 | 7781 | 2008.83 | 0.03 | 20.73 | 1.60 | 248.3 | 248.9 | 4.0 ± 69.8 (0.06) | corroborated | ok(5424b) |
| 778994474926961152 | 167.418180 43.819440 | 1237661872934945252 | 3818 | 2003.23 | 0.13 | 21.32 | 1.48 | 257.4 | 248.7 | 10.5 ± 39.2 (0.27) | corroborated | ok(3861b) |
| 6333056821300966272 | 226.612320 -6.926320 | - | - | - | - | - | - | - | 248.6 | - | none | no-coverage |
| 4585911133706711680 | 274.301500 27.001460 | - | - | - | - | - | - | - | 247.2 | - | none | no-coverage |
| 914350468044697600 | 126.708120 39.858520 | 1237657595151516416 | 2822 | 2001.96 | 0.07 | 20.37 | 1.69 | 250.0 | 247.1 | 5.3 ± 35.6 (0.15) | corroborated | ok(5900b) |
| 3717399923897977984 | 200.135510 6.149110 | 1237661970118410431 | 3841 | 2003.25 | 0.10 | 21.29 | 1.28 | 243.4 | 246.7 | 8.1 ± 39.2 (0.21) | corroborated | ok(4581b) |
| 1296928326363004416 | 224.852430 40.843070 | 1237661435394786240 | 3716 | 2003.19 | 0.07 | 21.16 | 1.50 | 251.7 | 246.4 | 5.6 ± 39.0 (0.14) | corroborated | ok(4822b) |
| 3485388058311031552 | 174.824710 -26.204560 | - | - | - | - | - | - | - | 246.3 | - | none | no-coverage |
| 6196682920934083328 | 202.046250 -21.106210 | - | - | - | - | - | - | - | 245.6 | - | none | no-coverage |
| 6444364648283689984 | 303.562820 -58.332630 | - | - | - | - | - | - | - | 245.6 | - | none | no-coverage |
| 3151381813350665472 | 119.219360 12.919120 | 1237667211038819116 | 5061 | 2004.95 | 0.03 | 20.25 | 1.66 | 240.0 | 242.0 | 2.6 ± 45.3 (0.06) | corroborated | ok(4842b) |
| 3502334246914338432 | 193.266220 -22.042760 | 1237651698155258788 | 1449 | 2000.34 | 0.14 | 21.84 | 1.85 | 245.6 | 239.2 | 9.0 ± 31.9 (0.28) | corroborated | ok(4795b) |
| 3421414069467005696 | 79.196400 27.356140 | 1237671257449629711 | 6003 | 2006.08 | 0.06 | 20.28 | 1.86 | 237.9 | 238.5 | 5.7 ± 50.4 (0.11) | corroborated | ok(4951b) |
| 3764064640489783424 | 162.712480 -7.326470 | - | - | - | - | - | - | - | 238.4 | - | none | no-coverage |
| 1173260339417897344 | 221.914200 7.573890 | 1237662236945547549 | 3903 | 2003.32 | 0.03 | 21.24 | 1.57 | 235.7 | 237.9 | 2.3 ± 39.4 (0.06) | corroborated | ok(3983b) |
| 5125419911539221760 | 39.005960 -23.448330 | - | - | - | - | - | - | - | 235.3 | - | none | no-coverage |
| 2468119419256161024 | 17.499310 -13.684930 | - | - | - | - | - | - | - | 234.6 | - | none | no-coverage |
| 401818418452566528 | 17.718900 48.601750 | 1237659932686746049 | 3366 | 2002.76 | 0.10 | 21.59 | 1.50 | 239.4 | 234.2 | 7.4 ± 37.8 (0.20) | corroborated | ok(4908b) |
| 6857242878104953472 | 311.734020 -20.167630 | - | - | - | - | - | - | - | 231.2 | - | none | no-coverage |
| 2356451987547034624 | 15.255390 -18.851520 | - | - | - | - | - | - | - | 230.9 | - | none | no-coverage |
| 635546381171304704 | 138.069220 19.095330 | 1237667429555765876 | 5112 | 2005.05 | 0.04 | 20.95 | 1.34 | 229.3 | 227.7 | 3.7 ± 45.6 (0.08) | corroborated | ok(4289b) |
| 5008076354130872704 | 22.299410 -41.185940 | - | - | - | - | - | - | - | 227.0 | - | none | no-coverage |
| 4750308012051385472 | 46.706760 -48.246880 | - | - | - | - | - | - | - | 226.1 | - | none | no-coverage |
| 6524223380403161216 | 359.549190 -48.152690 | - | - | - | - | - | - | - | 224.8 | - | none | no-coverage |
| 1422465410061938816 | 264.416410 57.953590 | 1237659897784238657 | 3358 | 2002.76 | 0.09 | 21.65 | 1.45 | 224.8 | 224.4 | 6.7 ± 37.8 (0.18) | corroborated | ok(4791b) |
| 1472427974342097152 | 204.462520 37.008070 | 1237664854713696504 | 4512 | 2004.21 | 0.16 | 21.95 | 1.46 | 236.0 | 222.9 | 13.4 ± 42.4 (0.32) | corroborated | ok(4179b) |
| 5895741949871112320 | 213.646950 -54.987610 | - | - | - | - | - | - | - | 222.8 | - | none | no-coverage |
| 901648948375442304 | 124.218470 32.817740 | 1237657775537980221 | 2864 | 2002.02 | 0.05 | 22.05 | 1.70 | 223.7 | 221.5 | 3.8 ± 35.8 (0.11) | corroborated | ok(4195b) |
| 6882834217400083968 | 314.500120 -16.807130 | - | - | - | - | - | - | - | 221.3 | - | none | no-coverage |
| 301092566253730176 | 29.796810 30.643220 | 1237679581621453176 | 7941 | 2009.08 | 0.20 | 21.55 | 2.20 | 198.2 | 220.7 | 29.3 ± 72.3 (0.41) | corroborated | ok(4926b) |
| 754205087630663808 | 153.996190 37.654750 | 1237661137423171874 | 3647 | 2003.09 | 0.11 | 21.26 | 1.47 | 216.6 | 218.1 | 8.8 ± 38.7 (0.23) | corroborated | ok(3770b) |
| 1552157548201668352 | 203.885230 47.624560 | 1237661150307222302 | 3650 | 2003.09 | 0.26 | 21.94 | 1.53 | 237.2 | 217.9 | 20.1 ± 38.7 (0.52) | corroborated | ok(4065b) |
| 343753621705610368 | 25.756650 38.430630 | - | - | - | - | - | - | - | 215.3 | - | none | no-coverage |

Headline: **18 of 35 corroborated, 17 none (all no-coverage), 0
interloper, 0 contradiction, 0 failed.** For the 18, the SDSS-era
detection sits 0.03-0.26" from the PM-propagated expected position at its
own frame epoch, and the implied 10-16-year baseline proper motion agrees
with Gaia's (dp median 6.2, max 29.3 mas/yr; z median 0.16, max 0.52 —
all far inside the 3 x max(sigma, 8) acceptance). psfMag_g - psfMag_r =
1.28-2.20 (median 1.54): red, consistent with the cohort's bp_rp
2.6-3.2 late-M / cool-subdwarf-like colors; no corroborated match is an
unrelated blue or extended contaminant. No candidate shows a
contradicting source in its expected slot; the SDSS epoch neither
downgrades nor contradicts any v3 survivor.

## Cross-check with the v3 blink

- 16 of the 18 SDSS-corroborated objects were already 2MASS-corroborated
  in v3; the SDSS implied PMs land in the same consistent band (e.g.
  1552157548201668352, the largest 2MASS z (2.03), has SDSS z = 0.52; 324266972833697920,
  2MASS z = 1.42, SDSS z = 0.06).
- **Two of the six CONF-A-STAYS gain a third epoch**: 914350468044697600
  and 3151381813350665472 were 2MASS non-detections (estimated J at/below
  the 2MASS limit) with only CatWISE+Gaia evidence; SDSS — deeper than
  2MASS — detects both at the propagated position with implied PM
  consistent at z <= 0.15.
- The remaining 4 CONF-A-STAYS (3485388058311031552, 2468119419256161024,
  4750308012051385472, 343753621705610368) and 13 PROMOTED objects have no
  SDSS DR18 coverage at their 2000.0 positions (southern fields and
  off-stripe gaps); their three-epoch evidence stays 2MASS+CatWISE+Gaia.
- The "sdss-none(at limit?)" question is resolved: **not a depth-limit
  artifact** — G = 19.7-20.0 is ~2 mag brighter than the SDSS r ~ 22.2
  5-sigma depth; every non-detection is a coverage gap (catalog box empty
  AND ImgCutout 4xx for all 17, per-object in `results/sdss_blink.csv`).

## Honest failures / notes

- `crossid.aspx` is gone (404) and its replacement
  `/dr18/CrossMatchTools/ObjectCrossID` rejected all 5 POST payload
  variants with the generic Error-500 page (no rows) — the coordinate
  upload contract is not derivable from the form page. Superseded by the
  SQL route, which returns a superset (objid, run/camcol/field, mjd_r,
  psfMags + errors, specobj join).
- SkyServer docs are unreachable (help-host DNS fail, `/dr18/en/help*`
  404) — every endpoint above was discovered from the live portal's own
  HTML (SQL Search form action, Navigate tool's image URL).
- Data Lab hosts no SDSS photometric object catalog (sdss_dr* =
  spectro-only) — an SDSS blink via Data Lab is not possible; SkyServer
  itself is the only SDSS photometry route from this host.
- `sdss_dr17.photoobj`-style table names return TAP ERRORS, not empty
  results; `ls_dr9.tractor`, `gaia_dr3.gaia_source` and TAP_SCHEMA are
  the verified Data Lab tables here.
- The blink ran twice (70 logged cone queries, 70 cutout fetches): the
  first pass was cleared after adding the raw-box counter and the
  no-coverage/depth-limit note logic; verdicts are identical in both
  passes. Append-mode log keeps both.
- Every number above comes from a logged HTTP response in
  `results/sdss_querylog.csv` (223 entries). Cutouts live in /tmp/astro_f
  (never committed).

## Task 2 — Rule-1 fix: stale conf counts in `results/possible_new_final.csv`

blink_vetting.md documented that the committed compact render carries
stale confidence counts (A 39 / B 310 / C 16 / blank 256) vs the
authoritative full-fidelity state (A 39 / B 555 / C 27), an artifact of
the apply_lit_checks re-finalize path. Fixed in this session
(`python3 scripts/sdss_probe.py conf_fix`; only the `conf` values and the
leading NOTE line changed — verified: 257 differing lines = 256 data rows'
conf field + NOTE, zero changes in any other field, LF endings and row
order preserved).

- **Before**: A 39 / B 310 / C 16 / blank 256. **After**: **A 39 / B 555 /
  C 27 / blank 0** (verified value_counts).
- The 39-id A-set: verified set-identical to `results/blink_vetting.csv`
  (all 39 v3 rows, DOWNGRADED included — they are v2-confidence-A).
  Unchanged (already A).
- The 16 previously-C rows stay C, and every one is accounted for:
  12 rows with parallax S/N < 5, 3 rows carrying the `M1` evidence token
  (margin<2 / implied-epoch-corridor class), and the CatWISE PM-ratio row
  5036731890598470912 named in vetting_v2.md.
- **11 rows re-set blank -> C** (exactly the predicted 11):
  - 9 rows with **parallax S/N < 5 recomputed live**: parallax_error for
    all 621 possible-new ids pulled from Gaia DR3 via Data Lab TAP
    (`gaia_dr3.gaia_source`, 5 batched ADQL id-list queries, logged
    `gaiaplx`), plx S/N = round(parallax/parallax_error, 1) exactly as
    `vet2.py finalize`. Identity verified against committed parallax
    values (candidates_top500.csv, blink_vetting.csv,
    spectroscopy_targets.csv): 152 cross-checks, 0 mismatches, max rel
    diff 1.05e-4. Recomputed S/N < 5 population: 21 rows, of which 12
    were already C — the 9 blanks become C. The 39 A-rows all verify
    S/N >= 5.0 (A criterion holds on the live values).
  - 2 rows carrying the **`M1` evidence token** (4515569121405002496,
    5950283224156484608): the compact render's first ev token encodes the
    margin/corridor class (M2 = margin >= 2 for 608 rows incl. all 39
    A-rows; M? = margin empty). Its C-semantics is validated inside the
    file: the 3 already-C M1 rows (5859988030777620480, 1549152136246388352,
    3421334049930104704) have plx S/N 11.3-24.2 and no CatWISE-PM
    condition, so nothing else can explain their C — the M1 token must be
    the vetting_v2.md C-condition (margin < 2x tolerance / implied-epoch
    corridor match). The 2 blank M1 rows therefore join C.
- Arithmetic closure (all disjoint): C = 16 current + 9 plx + 2 M1 = 27;
  B = 310 + (256 - 11) = 555; A = 39. Matches vetting_v2.md exactly.
  Bucket attribution note: vetting_v2.md sketches the 27 as
  "margin < 2: 2 rows, CatWISE ratio: 1, plx < 5: 24"; the row-set fixed
  here is the same 27 (the M1/plx split across buckets differs from that
  prose sketch, which is not machine-readable), and the union is verified
  against the authoritative total rather than the prose.
- The 8 `M?` (margin-empty) rows and all other blanks become B: under the
  `vet2.py finalize` rule an empty margin defaults to 99 (not C), their
  plx S/N are 7.1-15.0 (not C), and none is the CatWISE-PM row.
- The NOTE line was rewritten (it would have been false after the fix):
  it now records the 2026-11-15 correction, the derivation route, and the
  still-valid regeneration path (`scripts/vet2.py finalize` +
  `scripts/apply_lit_checks.py`, state + candidates.csv not committed).

## Reproduce

```
python3 -I astronomy/high-pm-survey/scripts/sdss_probe.py probe    # route table (logged)
python3 -I astronomy/high-pm-survey/scripts/sdss_probe.py blink    # 35 SDSS cones + cutouts (state-resumable, /tmp/astro_f)
python3 -I astronomy/high-pm-survey/scripts/sdss_probe.py gaiaplx  # 621 parallax_error rows (Data Lab, logged)
python3 -I astronomy/high-pm-survey/scripts/sdss_probe.py conf_fix # task-2 fix (writes possible_new_final.csv)
```

SkyServer SQL flow (the part that took discovery): GET
`https://skyserver.sdss.org/dr18/SearchTools/sql` for the
`__RequestVerificationToken` + session cookies, then POST the same URL
with `searchtool=SQL&TaskName=Skyserver.Search.SQL&syntax=NoSyntax&ReturnHtml=false&cmd=<SQL>&format=CSV&TableName=&__RequestVerificationToken=<token>`.
Cutouts: `https://skyserver.sdss.org/dr18/SkyServerWS/ImgCutout/getjpeg?ra=<RA>&dec=<DEC>&scale=0.2&width=256&height=256&opt=&query=`.
Test point ra=167.41774, dec=43.81838 (candidate 778994474926961152,
v3 shortlist #1). Legacy paths (`ImgCutout/getjpg`, `crossid.aspx`,
`en/tools/search/sql.aspx`) are dead — see the route table.

## Files

- `../scripts/sdss_probe.py` — probe + blink + gaiaplx + conf_fix
  (reuses blink_vet.py propagation/match math; every HTTP attempt logged
  append-mode).
- `sdss_blink.csv` — per-candidate evidence for the 35 (positions,
  objid/run/epoch/mjd, separations, implied PM, dp/sigma/z, colors,
  spectro-z columns, verdict, cutout status, raw-box counter).
- `sdss_querylog.csv` — all 223 logged HTTP attempts (probes, blink x2
  passes, gaiaplx).
- `possible_new_final.csv` — task-2 fix (conf column only + NOTE line).
- This note.
