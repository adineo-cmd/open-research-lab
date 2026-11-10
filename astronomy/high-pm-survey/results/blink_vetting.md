# Track B v3 — deep blink-comparison vetting of the 39 confidence-A candidates

Status: complete (2026-11-11 session). Script: `scripts/blink_vet.py`
(multi-epoch blink comparison + PM-baseline computation + verdict logic);
evidence CSV: `results/blink_vetting.csv`; append-mode query log:
`results/blink_querylog.csv`.

## Why v3 (recap of the F-13 position)

v2's confidence-A class (39 candidates) rested on SIMBAD cones at two
epochs + ident + CatWISE top-50 + GCNS id/position screens — but none of
those asked the standard confirmation question for a high-proper-motion
object: **is the source actually detected at an earlier epoch, at the
position Gaia's PM predicts, moving at the rate Gaia measures?** v3 runs
that blink comparison end-to-end for all 39: a 2MASS (1997-2001) detection
at the propagated pre-Gaia position implies a ~17-year PM baseline; the
CatWISE2020 measured PM vector adds a third epoch (2015.5); LS-DR9 imagery
at both the 2016.0 and 2000.0 positions gives the two-position imagery
blink. Nothing in this note is a discovery claim — these remain
*possible-new candidates* until spectroscopic follow-up.

## Method (explicit per catalog)

Positions are propagated from Gaia DR3 epoch 2016.0 exactly as in vet2.py
(`propagate()`; pmra includes cos(dec)). All separations are computed
client-side (see honest failures: IRSA TAP `DISTANCE()` units are
unreliable on these tables).

| catalog | epoch | test |
|---|---|---|
| 2MASS All-Sky PSC (IRSA TAP `fp_psc`) | per-source `jdate` (1997.25-2001.99) | cone at the epoch-2000.0 position, radius max(10", 1.5 x pm x 18.75 yr); TOP 12; every hit scored |
| CatWISE2020 (IRSA TAP `catwise_2020`) | 2015.5 | cone at the epoch-2015.5 position, radius max(8", 1.3 x pm x 0.5 yr + 2"), as vet2; nearest hit within tolerance; **measured PM vector** vs Gaia PM vector |
| Gaia DR3 (gaia.aip.de TAP) | 2016.0 | `pmra_error`, `pmdec_error`, `parallax_error` per candidate (candidates.csv carries no PM errors) |
| LS-DR9 imagery (www.legacysurvey.org jpeg-cutout) | ~2014-2019 | 200px cutouts fetched locally (/tmp, never committed) at BOTH the 2016.0 and 2000.0 positions — two-position blink on one epoch: the source should sit at the 2016-position and be absent at the 2000-position (~4" away for pm ~ 250 mas/yr) |

**2MASS implied-PM rule** (the core of v3): for each hit,
implied PM vector = (hit position - Gaia 2016.0 position) x 1000 /
(epoch_jdate - 2016.0) mas/yr per component. dp = |implied - Gaia PM
vector|. sigma = sqrt((0.35" / baseline)^2 + 0.5^2) mas/yr (0.35" =
2MASS astrometry + match tolerance; 0.5 mas/yr = Gaia PM error floor).
Consistent iff dp <= 3 x max(sigma, 8).

**CatWISE PM rule**: dp_cw = |CatWISE PM vector - Gaia PM vector|;
sigma_cw = sqrt(sigpmra^2 + sigpmdec^2 + 0.5^2); consistent iff
dp_cw <= 3 x max(sigma_cw, 8) (floor = WISE/Gaia systematic).

**Slot rule**: a catalog source within 2.5" of the expected epoch-2000
position whose implied PM contradicts Gaia at >5 sigma occupies the slot
where the object should be — flagged; DOWNGRADED only if CatWISE ALSO
fails. Field stars elsewhere in the ~10" cone are normal (they produce
the "interloper" label, not a contradiction).

**Verdicts** (candidates-not-claims):
- **PROMOTED** — 2MASS old-position detection with implied PM consistent
  (z <= 3) AND CatWISE PM consistent: the source is detected at three
  epochs (2MASS ~1998-2000, WISE 2015.5, Gaia 2016) moving coherently.
- **CONF-A-STAYS** — CatWISE consistent, no contradicting evidence:
  the six 2MASS non-detections (at/below the 2MASS depth limit).
- **DOWNGRADED** — positive contradiction. Four occurred, all of one
  type: the CatWISE counterpart's **measured PM vector** disagrees with
  Gaia's at 3.4-11.5 sigma while the vet2-era screen had only compared
  PM *magnitudes* (ratios 0.5-2), which misses direction changes. In
  three of the four the 2MASS blink still corroborates the Gaia PM, so
  the likeliest reading is WISE-counterpart contamination (6" WISE FWHM)
  rather than a wrong Gaia PM — they drop from A to needs-eyes, they are
  not rejected.

## Funnel (stage-by-stage)

| stage | rows | in | out |
|---|---|---|---|
| v2 harvest + UCD-like cut + epoch-aware screens (F-13) | 1,385 | 130,318 | 621 possible-new |
| v2 confidence-A (margin >= 2, ident none, GCNS none, CatWISE matched, plx S/N >= 5, bp_rp >= 2.6) | 621 | 621 | 39 |
| v3 2MASS blink: old-position detection with consistent implied PM | 39 | 39 | 32 corroborated / 6 non-detections (4 at-or-below 2MASS limit, 2 just above) / 1 interloper |
| v3 CatWISE2020 PM vector check (all 39) | 39 | 39 | 35 PM-vector consistent / 4 mismatch (3.4-11.5 sigma) |
| v3 verdicts | 39 | 39 | 29 PROMOTED / 6 CONF-A-STAYS / 4 DOWNGRADED (CatWISE PM-vector conflicts) |

## The 2MASS blink (main result)

| source_id | 2MASS designation | epoch | sep2000 as | J | J-H | implied pm | Gaia pm | dp +/- sig (z) |
|---|---|---|---|---|---|---|---|---|
| 2813361564957760896 | 23280842+1406391 | 1997.74 | 0.43 | 16.391 | 0.47 | 240.1 | 249.9 | 15.2 ± 19.2 (0.79) |
| 5390732032963218560 | 11053702-3917324 | 1999.33 | 0.33 | 16.167 | 0.7 | 258.9 | 248.9 | 10.0 ± 21.0 (0.48) |
| 324266972833697920 | 02145061+3014535 | 1997.95 | 0.95 | 16.677 | 0.32 | 271.0 | 248.9 | 27.5 ± 19.4 (1.42) |
| 778994474926961152 | 11094034+4349100 | 1999.24 | 0.19 | 16.493 | 0.32 | 239.6 | 248.7 | 14.7 ± 20.9 (0.7) |
| 6333056821300966272 | 15062695-0655349 | 1999.17 | 0.15 | 16.561 | 0.72 | 231.5 | 248.6 | 18.8 ± 20.8 (0.9) |
| 4585911133706711680 | 18171236+2700060 | 1998.52 | 0.77 | 16.438 | 0.8 | 270.2 | 247.2 | 23.7 ± 20.0 (1.19) |
| 3717399923897977984 | 13203250+0608566 | 2000.21 | 0.34 | 16.644 | 0.97 | 228.4 | 246.7 | 18.3 ± 22.2 (0.82) |
| 1296928326363004416 | 14592461+4050354 | 1998.3 | 0.54 | 16.745 | 0.57 | 252.1 | 246.4 | 10.5 ± 19.8 (0.53) |
| 6196682920934083328 | 13281113-2106220 | 1998.34 | 0.54 | 16.235 | 0.1 | 252.3 | 245.6 | 9.5 ± 19.8 (0.48) |
| 6444364648283689984 | 20141504-5819572 | 1999.82 | 0.31 | 16.665 | 0.51 | 257.2 | 245.6 | 17.4 ± 21.6 (0.81) |
| 3502334246914338432 | 12530387-2202334 | 1998.38 | 0.5 | 15.869 | 0.6 | 245.7 | 239.2 | 6.8 ± 19.9 (0.34) |
| 3421414069467005696 | 05164710+2721224 | 1997.93 | 0.57 | 16.82 | 0.57 | 242.5 | 238.5 | 5.7 ± 19.4 (0.29) |
| 3764064640489783424 | 10505100-0719353 | 1999.07 | 0.17 | 15.967 | 0.37 | 235.4 | 238.4 | 3.1 ± 20.7 (0.15) |
| 1173260339417897344 | 14473938+0734261 | 2000.25 | 0.43 | 16.571 | 0.52 | 232.9 | 237.9 | 26.2 ± 22.2 (1.18) |
| 5125419911539221760 | 02360140-2326537 | 1998.86 | 0.41 | 16.259 | 0.42 | 236.4 | 235.3 | 17.7 ± 20.4 (0.87) |
| 401818418452566528 | 01105250+4836063 | 1998.91 | 0.35 | 16.164 | 0.49 | 238.3 | 234.2 | 8.7 ± 20.5 (0.42) |
| 3424352381146733824 | 05553977+2252554 | 1998.75 | 0.39 | 16.792 | 0.79 | 230.9 | 233.7 | 18.4 ± 20.3 (0.91) |
| 6857242878104953472 | 20465615-2010032 | 1998.5 | 0.29 | 16.115 | 0.43 | 227.3 | 231.2 | 5.8 ± 20.0 (0.29) |
| 2356451987547034624 | 01010126-1851052 | 1998.62 | 0.43 | 15.986 | 0.61 | 236.8 | 230.9 | 8.4 ± 20.2 (0.42) |
| 6645353862012156928 | 19302678-5314326 | 2000.78 | 0.39 | 16.588 | 0.51 | 216.7 | 230.1 | 14.0 ± 23.0 (0.61) |
| 635546381171304704 | 09121662+1905436 | 1998.03 | 0.44 | 16.719 | 0.56 | 226.6 | 227.7 | 5.0 ± 19.5 (0.26) |
| 5008076354130872704 | 01291182-4111092 | 1998.83 | 0.37 | 15.911 | 0.39 | 232.8 | 227.0 | 6.0 ± 20.4 (0.29) |
| 6524223380403161216 | 23581181-4809099 | 1999.8 | 0.28 | 16.16 | 0.52 | 211.3 | 224.8 | 19.0 ± 21.6 (0.88) |
| 1422465410061938816 | 17373995+5757128 | 2000.21 | 0.19 | 16.341 | 0.55 | 229.0 | 224.4 | 12.5 ± 22.2 (0.56) |
| 1472427974342097152 | 13375104+3700289 | 1998.29 | 0.44 | 15.837 | 0.56 | 226.3 | 222.9 | 4.4 ± 19.8 (0.22) |
| 5895741949871112320 | 14143528-5459154 | 2000.14 | 0.13 | 16.493 | 0.95 | 226.1 | 222.8 | 8.9 ± 22.1 (0.4) |
| 901648948375442304 | 08165243+3249042 | 1998.21 | 0.39 | 16.245 | 0.45 | 220.9 | 221.5 | 1.5 ± 19.7 (0.08) |
| 6882834217400083968 | 20580002-1648251 | 1998.43 | 0.57 | 16.625 | 0.5 | 227.9 | 221.3 | 20.5 ± 19.9 (1.03) |
| 301092566253730176 | 01591123+3038356 | 1999.84 | 0.06 | 16.218 | 0.76 | 222.5 | 220.7 | 2.0 ± 21.7 (0.09) |
| 4829516627852875904 | 03473886-5013528 | 1999.79 | 0.16 | 15.866 | 0.67 | 217.0 | 220.5 | 10.7 ± 21.6 (0.5) |
| 754205087630663808 | 10155907+3739175 | 1998.26 | 0.46 | 16.523 | 0.54 | 217.7 | 218.1 | 15.5 ± 19.7 (0.79) |
| 1552157548201668352 | 13353242+4737281 | 1998.4 | 0.44 | 16.124 | 0.21 | 184.0 | 217.9 | 40.4 ± 19.9 (2.03) |

Summary: for 32 of 39 candidates there is **exactly one
2MASS source at the expected pre-Gaia position** (separations 0.06-0.95",
median ~0.4" — consistent with the pm x |2000 - jdate| track offset plus
~0.35" astrometry), and the implied ~17-year proper motion agrees with
Gaia's (median z ~ 0.7; largest accepted z = 2.03). The colors of the
matched 2MASS sources (J-H 0.10-0.97, median ~0.5; H-K -0.1..1.3) span
the late-M / cool-subdwarf range — consistent with the cohort's bp_rp
2.6-3.5 selection; nothing matched looks like an unrelated blue or
galaxy contaminant. Six candidates have no 2MASS source in the cone:
their estimated J (G - 3.4, the cohort's empirical G-J) is 16.3-16.6,
at or just below the 2MASS SNR~10 limit (J ~ 16.5) — a non-detection is
expected there, not evidence against. One candidate
(5286902985287361280) shows only a field star 3.9" off the expected slot
whose implied PM (419 mas/yr) contradicts Gaia (241) at z=11 — the slot
is empty; its CatWISE counterpart's measured PM ALSO contradicts Gaia at
11.5 sigma, so it is DOWNGRADED (its CatWISE 'PM' is likely an
unrelated WISE source or a contaminated blend).

## CatWISE2020 (all 39)

| source_id | sep as | W1-W2 | CW pm mas/yr | dp +/- sig (z) | verdict |
|---|---|---|---|---|---|
| 2813361564957760896 | 0.12 | 0.16 | 266.6 | 30.5 ± 23.9 (1.28) | ok |
| 5390732032963218560 | 0.13 | 0.18 | 264.8 | 43.5 ± 19.8 (2.2) | ok |
| 324266972833697920 | 0.15 | 0.3 | 288.9 | 53.7 ± 28.8 (1.86) | ok |
| 778994474926961152 | 0.25 | 0.22 | 316.6 | 69.2 ± 28.8 (2.4) | ok |
| 6333056821300966272 | 0.38 | 0.08 | 227.9 | 33.3 ± 30.4 (1.1) | ok |
| 4585911133706711680 | 0.09 | 0.18 | 255.1 | 27.3 ± 19.8 (1.38) | ok |
| 914350468044697600 | 0.89 | -0.12 | 194.3 | 65.4 ± 30.0 (2.18) | ok |
| 3717399923897977984 | 0.35 | 0.2 | 266.3 | 33.3 ± 25.5 (1.31) | ok |
| 1296928326363004416 | 0.09 | 0.14 | 286.7 | 41.2 ± 24.8 (1.66) | ok |
| 3485388058311031552 | 0.14 | 0.17 | 309.3 | 65.1 ± 24.7 (2.64) | ok |
| 6196682920934083328 | 0.13 | 0.15 | 288.3 | 57.0 ± 25.5 (2.24) | ok |
| 6444364648283689984 | 0.04 | 0.19 | 262.8 | 31.2 ± 27.7 (1.13) | ok |
| 3151381813350665472 | 0.7 | 0.2 | 250.8 | 22.0 ± 31.1 (0.71) | ok |
| 3502334246914338432 | 0.14 | 0.24 | 241.7 | 12.1 ± 17.2 (0.7) | ok |
| 3421414069467005696 | 0.15 | 0.08 | 241.8 | 37.8 ± 30.7 (1.23) | ok |
| 3764064640489783424 | 0.09 | 0.28 | 256.2 | 23.6 ± 20.5 (1.15) | ok |
| 1173260339417897344 | 0.16 | 0.22 | 227.2 | 24.3 ± 33.1 (0.73) | ok |
| 5125419911539221760 | 0.12 | 0.16 | 269.9 | 42.5 ± 24.5 (1.73) | ok |
| 2468119419256161024 | 0.31 | 0.26 | 231.0 | 34.2 ± 27.9 (1.23) | ok |
| 401818418452566528 | 0.2 | 0.22 | 256.0 | 41.8 ± 18.1 (2.31) | ok |
| 6857242878104953472 | 0.11 | 0.26 | 246.0 | 38.0 ± 25.3 (1.5) | ok |
| 2356451987547034624 | 0.09 | 0.16 | 241.4 | 15.5 ± 20.0 (0.78) | ok |
| 635546381171304704 | 0.07 | 0.06 | 274.3 | 47.3 ± 34.4 (1.38) | ok |
| 5008076354130872704 | 0.06 | 0.24 | 237.6 | 20.1 ± 15.5 (1.3) | ok |
| 4750308012051385472 | 0.18 | 0.03 | 268.2 | 42.8 ± 34.8 (1.23) | ok |
| 6524223380403161216 | 0.28 | 0.27 | 234.4 | 26.3 ± 18.1 (1.45) | ok |
| 1422465410061938816 | 0.02 | 0.18 | 214.0 | 11.6 ± 15.5 (0.75) | ok |
| 1472427974342097152 | 0.16 | 0.22 | 247.2 | 24.4 ± 16.5 (1.48) | ok |
| 5895741949871112320 | 0.98 | -0.2 | 174.2 | 48.6 ± 22.1 (2.2) | ok |
| 901648948375442304 | 0.18 | 0.22 | 253.2 | 33.6 ± 21.2 (1.58) | ok |
| 6882834217400083968 | 0.06 | 0.16 | 232.5 | 16.4 ± 37.5 (0.44) | ok |
| 301092566253730176 | 0.15 | 0.25 | 229.8 | 20.5 ± 17.5 (1.17) | ok |
| 754205087630663808 | 0.11 | 0.24 | 201.1 | 32.9 ± 23.9 (1.38) | ok |
| 1552157548201668352 | 0.16 | 0.21 | 237.0 | 39.0 ± 18.4 (2.12) | ok |
| 343753621705610368 | 0.1 | 0.18 | 173.1 | 50.9 ± 46.6 (1.09) | ok |

All 39 have a CatWISE counterpart within the vet2 match tolerance. For
35 of 39 the **measured** WISE PM vector agrees with Gaia's within
3 sigma (most within 1-2 sigma); 4 disagree (the DOWNGRADED rows above).
W1-W2 spans -0.2..+0.3 — consistent with the v2 note that these are
late-M / cool-subdwarf photospheres, not clear L dwarfs.

## Gaia PM errors and sigma scales

The gaia.aip.de TAP lookup of per-source `pmra_error`/`pmdec_error`
timed out for the whole session (honest failure — the 2016-11-09/10
harvest session used the same service heavily; it may be rate-limiting).
The blink sigma model therefore uses a conservative 0.5 mas/yr Gaia PM
error floor, which is safe: for G = 19.7-20.0 the true DR3 PM errors
are ~0.2-0.9 mas/yr, negligible against the 2MASS-baseline position
term (0.35"/17 yr ~ 21 mas/yr) that dominates every sigma here. The
blink precision is position-limited, as designed; the CatWISE test is
unaffected (CatWISE carries its own measured sigmas).

## Per-object verdicts

| source_id | pm mas/yr | G | dist pc | 2MASS verdict | CatWISE verdict | verdict | flags |
|---|---|---|---|---|---|---|---|
| 2813361564957760896 | 249.9 | 19.815748 | 194.2 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 5390732032963218560 | 248.9 | 19.93698 | 164.2 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 324266972833697920 | 248.9 | 19.76346 | 213.1 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 778994474926961152 | 248.7 | 19.998358 | 248.6 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 6333056821300966272 | 248.6 | 19.705519 | 304.8 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 4585911133706711680 | 247.2 | 19.831089 | 164.3 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 914350468044697600 | 247.1 | 19.7354 | 220.5 | 2mass-none | catwise-pm-consistent | CONF-A-STAYS | no-2MASS-counterpart |
| 3717399923897977984 | 246.7 | 19.865763 | 186.2 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 1296928326363004416 | 246.4 | 19.970005 | 205.3 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 3485388058311031552 | 246.3 | 19.841124 | 176.9 | 2mass-none | catwise-pm-consistent | CONF-A-STAYS | no-2MASS-counterpart |
| 6196682920934083328 | 245.6 | 19.760828 | 192.4 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 6444364648283689984 | 245.6 | 19.741682 | 220.8 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 3151381813350665472 | 242.0 | 19.668144 | 238.5 | 2mass-none | catwise-pm-consistent | CONF-A-STAYS | no-2MASS-counterpart |
| 5286902985287361280 | 241.4 | 19.739716 | 195.6 | 2mass-interloper | catwise-nearbut-pm-inconsistent | DOWNGRADED | catwise-pm-mismatch |
| 3502334246914338432 | 239.2 | 19.716547 | 123.2 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 3421414069467005696 | 238.5 | 19.791248 | 348.3 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 3764064640489783424 | 238.4 | 19.725706 | 125.6 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 1173260339417897344 | 237.9 | 19.982471 | 214.8 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 5125419911539221760 | 235.3 | 19.822056 | 205.9 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 2468119419256161024 | 234.6 | 19.97644 | 198.4 | 2mass-none(below-limit,expected) | catwise-pm-consistent | CONF-A-STAYS | no-2MASS-counterpart(below-limit-expected) |
| 401818418452566528 | 234.2 | 19.837486 | 135.5 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 3424352381146733824 | 233.7 | 19.786867 | 220.8 | 2mass-corroborated | catwise-nearbut-pm-inconsistent | DOWNGRADED | catwise-pm-mismatch |
| 6857242878104953472 | 231.2 | 19.778358 | 144.0 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 2356451987547034624 | 230.9 | 19.77153 | 144.9 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 6645353862012156928 | 230.1 | 19.815979 | 201.6 | 2mass-corroborated | catwise-nearbut-pm-inconsistent | DOWNGRADED | catwise-pm-mismatch |
| 635546381171304704 | 227.7 | 19.948277 | 281.0 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 5008076354130872704 | 227.0 | 19.898323 | 108.8 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 4750308012051385472 | 226.1 | 19.96328 | 322.7 | 2mass-none(below-limit,expected) | catwise-pm-consistent | CONF-A-STAYS | no-2MASS-counterpart(below-limit-expected) |
| 6524223380403161216 | 224.8 | 19.854916 | 149.4 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 1422465410061938816 | 224.4 | 19.866655 | 146.0 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 1472427974342097152 | 222.9 | 19.87109 | 122.5 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 5895741949871112320 | 222.8 | 19.974825 | 165.9 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 901648948375442304 | 221.5 | 19.981035 | 159.4 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 6882834217400083968 | 221.3 | 19.96158 | 204.2 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 301092566253730176 | 220.7 | 19.893147 | 124.1 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 4829516627852875904 | 220.5 | 19.91964 | 120.5 | 2mass-corroborated | catwise-nearbut-pm-inconsistent | DOWNGRADED | catwise-pm-mismatch |
| 754205087630663808 | 218.1 | 19.930948 | 207.2 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 1552157548201668352 | 217.9 | 19.926441 | 154.4 | 2mass-corroborated | catwise-pm-consistent | PROMOTED | - |
| 343753621705610368 | 215.3 | 19.997667 | 278.1 | 2mass-none(below-limit,expected) | catwise-pm-consistent | CONF-A-STAYS | no-2MASS-counterpart(below-limit-expected) |

Two-epoch PM baselines for the PROMOTED objects (2MASS jdate -> Gaia
2016.0; implied PM vs Gaia PM, dp as |vector difference|):

| source_id | 2MASS epoch | implied pm mas/yr | Gaia pm mas/yr | dp ± sig mas/yr (z) |
|---|---|---|---|---|
| 2813361564957760896 | 1997.74 (23280842+1406391) | 240.1 | 249.9 | 15.2 ± 19.2 (0.79) |
| 5390732032963218560 | 1999.33 (11053702-3917324) | 258.9 | 248.9 | 10.0 ± 21.0 (0.48) |
| 324266972833697920 | 1997.95 (02145061+3014535) | 271.0 | 248.9 | 27.5 ± 19.4 (1.42) |
| 778994474926961152 | 1999.24 (11094034+4349100) | 239.6 | 248.7 | 14.7 ± 20.9 (0.7) |
| 6333056821300966272 | 1999.17 (15062695-0655349) | 231.5 | 248.6 | 18.8 ± 20.8 (0.9) |
| 4585911133706711680 | 1998.52 (18171236+2700060) | 270.2 | 247.2 | 23.7 ± 20.0 (1.19) |
| 3717399923897977984 | 2000.21 (13203250+0608566) | 228.4 | 246.7 | 18.3 ± 22.2 (0.82) |
| 1296928326363004416 | 1998.3 (14592461+4050354) | 252.1 | 246.4 | 10.5 ± 19.8 (0.53) |
| 6196682920934083328 | 1998.34 (13281113-2106220) | 252.3 | 245.6 | 9.5 ± 19.8 (0.48) |
| 6444364648283689984 | 1999.82 (20141504-5819572) | 257.2 | 245.6 | 17.4 ± 21.6 (0.81) |
| 3502334246914338432 | 1998.38 (12530387-2202334) | 245.7 | 239.2 | 6.8 ± 19.9 (0.34) |
| 3421414069467005696 | 1997.93 (05164710+2721224) | 242.5 | 238.5 | 5.7 ± 19.4 (0.29) |
| 3764064640489783424 | 1999.07 (10505100-0719353) | 235.4 | 238.4 | 3.1 ± 20.7 (0.15) |
| 1173260339417897344 | 2000.25 (14473938+0734261) | 232.9 | 237.9 | 26.2 ± 22.2 (1.18) |
| 5125419911539221760 | 1998.86 (02360140-2326537) | 236.4 | 235.3 | 17.7 ± 20.4 (0.87) |
| 401818418452566528 | 1998.91 (01105250+4836063) | 238.3 | 234.2 | 8.7 ± 20.5 (0.42) |
| 6857242878104953472 | 1998.5 (20465615-2010032) | 227.3 | 231.2 | 5.8 ± 20.0 (0.29) |
| 2356451987547034624 | 1998.62 (01010126-1851052) | 236.8 | 230.9 | 8.4 ± 20.2 (0.42) |
| 635546381171304704 | 1998.03 (09121662+1905436) | 226.6 | 227.7 | 5.0 ± 19.5 (0.26) |
| 5008076354130872704 | 1998.83 (01291182-4111092) | 232.8 | 227.0 | 6.0 ± 20.4 (0.29) |
| 6524223380403161216 | 1999.8 (23581181-4809099) | 211.3 | 224.8 | 19.0 ± 21.6 (0.88) |
| 1422465410061938816 | 2000.21 (17373995+5757128) | 229.0 | 224.4 | 12.5 ± 22.2 (0.56) |
| 1472427974342097152 | 1998.29 (13375104+3700289) | 226.3 | 222.9 | 4.4 ± 19.8 (0.22) |
| 5895741949871112320 | 2000.14 (14143528-5459154) | 226.1 | 222.8 | 8.9 ± 22.1 (0.4) |
| 901648948375442304 | 1998.21 (08165243+3249042) | 220.9 | 221.5 | 1.5 ± 19.7 (0.08) |
| 6882834217400083968 | 1998.43 (20580002-1648251) | 227.9 | 221.3 | 20.5 ± 19.9 (1.03) |
| 301092566253730176 | 1999.84 (01591123+3038356) | 222.5 | 220.7 | 2.0 ± 21.7 (0.09) |
| 754205087630663808 | 1998.26 (10155907+3739175) | 217.7 | 218.1 | 15.5 ± 19.7 (0.79) |
| 1552157548201668352 | 1998.4 (13353242+4737281) | 184.0 | 217.9 | 40.4 ± 19.9 (2.03) |

## LS-DR9 imagery blink

Cutouts at the 2016.0 position have DR9 coverage for 25 of 39 (12 blank
tiles — no coverage, mostly deep-south fields — plus 2 http-errors); at
the 2000.0 position 26 of 39 (statuses recorded per object in
`results/blink_vetting.csv`, ls_cutout_2016 / ls_cutout_2000). The
images were kept in /tmp (never committed). Because the two slots are
only ~4" apart, both fall inside one 52"-wide frame — the blink is a
sub-frame shift: for the spot-checked candidate 778994474926961152 the
single red point source sits centered in the 2016-position frame and
~15 px up-right of center in the 2000-position frame, exactly the
predicted pm x 16 yr displacement vector, with no second red source at
the alternate slot. This is a human-eyes supplement, not the systematic
evidence — the catalog-level blink (2MASS + CatWISE PM vectors) is.

## Honest failures

- **IRSA TAP `DISTANCE()` units are unreliable** on `fp_psc` and
  `catwise_2020` (returns values inconsistent with any angular unit for
  in-cone sources; e.g. 0.37" separations reported as ~1253"). All
  separations are therefore computed client-side from returned ra/dec.
  The first pipeline run trusted the DISTANCE column, was killed, state
  cleared, and re-run — no verdict in this note depends on it.
- **Implied-PM formula bug (caught pre-verdict)**: the first draft
  divided the residual to the *propagated* Gaia position by the baseline
  instead of the full two-epoch displacement — double-counting Gaia's PM
  and flagging every true counterpart as inconsistent (z ~ 11). Caught
  by validating the very first cone hit against a manual computation
  (2MASS 11094034+4349100 sits 0.19" from candidate 778994474926961152's
  slot); fixed before any verdicts were recorded, state cleared, re-run.
- **J_est model**: the non-detection flag first used J_est = G - 1.8
  (wrong for this cohort: the 2MASS-detected members have G-J ~ 3.4).
  Corrected to G - 3.4 and the six affected objects re-run. The
  corrected estimates (16.3-16.6) sit at the 2MASS limit either way —
  the "non-detection expected" conclusion is unchanged, the arithmetic
  is now honest.
- **SDSS (SkyServer) unreachable**: `ImgCutout/getjpg` 404 on DR16/DR17/
  DR18; `crossid.aspx` returns no rows (DR16/DR17). The SDSS
  (~2000-2006) third imagery epoch could not be used. NOAO Data Lab TAP
  (`datalab.noao.edu` DNS failure, `datalab.noirlab.edu` timeout) is
  also unreachable, so the LS-DR9 *catalog* check was replaced by the
  LS-DR9 imagery + 2MASS/CatWISE catalog blink above.
- **CatWISE hit storage**: only the 4 nearest hits per cone are kept in
  the state file (TOP 8 queried). With cone radii ~4" the expected
  contamination is ~2 objects/cone, so the risk of losing the true
  counterpart is small; all 39 verdicts rely on the nearest hit only.
- **Visual blink depth**: imagery was inspected for a handful of objects
  (Read tool on the /tmp cutouts), not all 39 — the catalog-level blink
  (2MASS + CatWISE PM vectors) is the systematic evidence; the cutouts
  and their statuses are recorded per object for human review.
- **Unreachable services (unchanged)**: CDS Strasbourg, vizier.nao.ac.jp,
  vizier.china-vo.org; additionally this session: SkyServer, NOAO Data
  Lab.
- **v2 compact-CSV discrepancy (noted for the ledger)**: the committed
  compact render `results/possible_new_final.csv` carries stale
  confidence counts (A 39 / B 310 / C 16 / blank 256) versus
  `vetting_v2.md` and the full-fidelity file (39 / 555 / 27) — an
  artifact of the apply_lit_checks re-finalize path. The 39-id
  confidence-A set is IDENTICAL in both files (verified set-equality in
  this session), so v3's target list is unaffected.

## Reproducibility

```
python3 scripts/blink_vet.py all     # 2MASS + CatWISE + Gaia-PM-errs + LS cutouts + finalize
python3 scripts/blink_vet.py finalize  # verdicts from results/blink_state.json alone
python3 scripts/blink_tables.py       # splice evidence tables into this md
```

State checkpoints to `results/blink_state.json` (resume by key;
re-running a phase skips finished objects; state NOT committed — it is
regenerated by re-running the phases). Every HTTP query is appended to
`results/blink_querylog.csv` (append mode; 126 queries this session).
The LS cutouts live in /tmp/trackb_blink_cutouts (not committed).
