# Track B v4 — observation-ready spectroscopy target package for the 29 F-21 promoted high-PM candidates

Status: complete (2026-11-11 session). Script:
`scripts/spectroscopy_targets.py`; machine-readable package:
`results/spectroscopy_targets.csv`; query log
`results/spectroscopy_querylog.csv` (created only on live IRSA runs;
the packaged run was offline — see Honest failures).

## Related work

Method-level prior art: Karpov, Malkov & Avdeeva 2025, "New ultracool
dwarf candidates from multi-epoch WISE data", A&A 695, A195
(doi:10.1051/0004-6361/202452011, arXiv:2408.15067) publishes 258
previously-unpublished high-PM WISE (unTimely) objects, most consistent
with ultracool dwarfs, selected by WISE-internal motion plus
cross-survey color typing. Delta of this package: targets come from a
full-sky Gaia DR3 harvest vetted per object and epoch-aware across
2MASS / CatWISE2020 / Gaia DR3 / LS-DR9 (see `results/blink_vetting.md`),
each with a published three-epoch coherent-motion evidence trail
(`results/blink_vetting.csv`), here packaged into observation-ready
coordinates at any epoch, priority order and NIR exposure estimates.
The Karpov+ candidate list (CDS J/A+A/695/A195) should be
cross-checked against these 29 targets at follow-up time.

## Purpose and framing

F-21 (blink_vetting) promoted 29 of the 39 confidence-A candidates to
**three-epoch coherent motion** (2MASS ~1998-2000 → CatWISE2020 2015.5 →
Gaia DR3 2016.0, implied PMs agreeing with Gaia within ~3 sigma) with
zero catalog identity in v2's epoch-aware SIMBAD/GCNS screens. This
package turns those 29 *possible-new candidates* into an
observation-ready spectroscopy target list: coordinates at any needed
epoch, colors, absolute magnitudes, a color-based spectral-class
*plausibility* (flagged estimates — not classifications), visibility
windows, and an exposure rule-of-thumb. Nothing here is a discovery
claim; every object stays a candidate until spectroscopy says otherwise.

## Inputs and provenance

| input | role | provenance |
|---|---|---|
| `results/blink_vetting.csv` (F-21) | the 29 PROMOTED source_ids; 2MASS designations, epochs, blink z | F-21 session 2026-11-11 |
| `results/blink_state.json` (F-21, local) | per-object 2MASS fp_psc hits (j_m/h_m/k_m + sigmas + ph_qual + jdate) and catwise_2020 hits (w1mpro/w2mpro) | IRSA TAP queries 2026-11-11 (F-21); the script re-queries IRSA live for any missing object and on `--live` |
| `results/chunks/all_high_pm.csv` | full Gaia DR3 astrometry: ra/dec (epoch 2016.0), pmra/pmdec, parallax(+error), G/BP/RP, bp_rp, ruwe | F-9/F-13 harvest (gaia.aip.de TAP) |

Cross-check: for one object (6196682920934083328 = 2MASS
13281113-2106220) a live IRSA `fp_psc` re-query during this session
returned the identical counterpart (same designation, J=16.235,
H=16.138, K=15.425, same jdate, ph_qual ACC) at 0.54" from the
epoch-2000 slot — exactly the F-21 evidence. The other 28 reuse the
F-21 state hits unchanged.

## Method (explicit)

- **Coordinates**: Gaia DR3 ra/dec are epoch 2016.0; positions are
  propagated with the F-21 `propagate()` rule (pmra includes cos(dec))
  to J2000.0 (dt = −16 yr) and to the session epoch 2026.86 (dt =
  +10.86 yr). At pm ≈ 220-250 mas/yr the 2016→2026.86 motion is
  ~2.4-2.7" — the "current" coordinates matter for acquisition.
- **Galactic coordinates** computed from the standard J2000 pole
  (α=192.85948°, δ=+27.12825°, l_NCP=122.93192°). Validated against
  four reference directions: Galactic center (l=0.0002°, b=0.0001°),
  Vega (67.45, +19.24), Sirius (227.23, −8.89), M31 core (121.17,
  −21.57) — all match published values to ~0.2°.
- **V estimate**: G−V = −0.01760 − 0.006860·(BP−RP) −
  0.1732·(BP−RP)² (Carrasco et al., Gaia DR2 documentation §5.3.7,
  Table 5.8), V = G − (G−V). Valid −0.5 < BP−RP < 2.75 (σ=0.046);
  **this cohort sits at BP−RP 2.6-3.5, i.e. extrapolated beyond the
  fitted range** on solar-metallicity bright standards, so each V_est
  carries roughly ±0.3-0.5 mag of systematic uncertainty (independent
  check: V_est ≈ J + 4.5-5.5 for mid-M colors is consistent with the
  same numbers). Treat V_est as a feasibility figure, not photometry.
- **Distance / M_J**: d = 1000/parallax (parallax S/N ≈ 12-23 for the
  cohort; distance systematics ≲ 8%); M_J = J − 5·log10(d/10pc).
  Extinction ignored — most targets sit at |b| > 20° (median |b| ~ 44°)
  and the J-band extinction is small; this biases M_J bright by ≲ 0.1
  mag for most, slightly more for the two low-|b| objects.
- **Spectral-class plausibility** (estimates, not classifications):
  temperature is ranked by W1−W2 (the disk-dM J−H sequence is nearly
  degenerate, J−H ≈ 0.55-0.70 from M0 to M7, so J−H alone cannot rank
  temperature); then M_J and J−H are compared to the disk-dM anchor at
  that temperature. A metal-poor subdwarf sits *bluer and fainter* than
  the disk sequence at matched W1−W2. Anchor table (approximate,
  ±0.3-0.5 mag / ±0.05 mag; Pecaut-Mamajek-style M_J and
  Skrzypek-style WISE colors): M0 (5.4, 0.55, 0.02), M3 (6.9, 0.58,
  0.06), M5 (8.2, 0.62, 0.11), M6 (9.3, 0.66, 0.16), M7 (10.7, 0.70,
  0.24), M8 (12.3, 0.68, 0.32) — (M_J, J−H, W1−W2). Labels: dM-locus /
  subdwarf-tendency / sdM-esdM-consistent / underluminous-vs-dM /
  overluminous-flag. The subdwarf-vs-dwarf boundary at these colors is
  a genuine research question (metallicity, gravity, and the
  W1−W2-temperature mapping all shift it); the labels only say where an
  object sits relative to the disk-dM locus, never what it is.
- **Visibility season**: for each target the sun's mid-month RA over
  the next 12 months (low-precision solar position, ~0.01°) is compared
  to the anti-solar RA; a month counts as observable when the target is
  within 4.5 h of RA of the anti-solar point (≈ >6 h/night at moderate
  airmass for fair declinations, twilight ignored). This is an
  RA-only rule documented as approximate; declination effects are
  handled separately (3 targets south of −45° are marginal or
  inaccessible from a +20° site; see below). Best month = minimum
  sun-RA distance to anti-target.
- **Priority score** (the task's rule: brighter J + shorter distance +
  higher PM confidence = first):
  `priority = 10 × (0.5·f_J + 0.3·f_d + 0.2·f_z)` where each f ∈ [0,1]
  is the min-max normalized (J, distance, blink z) over the 29 and
  f = 1 − norm (so brightest / nearest / tightest blink = highest).
  Weights are a stated choice, not a derived result. z_blink =
  2MASS-blink |implied−Gaia| PM mismatch / sigma from F-21
  (0.08-2.03 here).

## Priority table (all 29, sorted by priority)

J, J−H from 2MASS (F-21); H−W2, W1−W2 from CatWISE2020 (F-21);
d from Gaia DR3 parallax; M_J and V_est as above; class estimate =
plausibility label vs the disk-dM locus. "visible" = observable months
(RA rule, next 12 months; `D`=2026-12, otherwise 2027).

| # | pri | 2MASS designation | Gaia DR3 source_id | RA/Dec J2000 | RA/Dec 2026.86 | l,b deg | G | J | J-H | H-W2 | W1-W2 | d pc | M_J | V est | class estimate | visible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9.7 | 13375104+3700289 | 1472427974342097152 | 13h37m50.4s +37d00m29.3s | 204.46044 37.00813 | 81.04, 76.08 | 19.87 | 15.84 | 0.556 | 0.65 | 0.218 | 122.5 | 10.4 | 21.48 | dM-locus | 02-06 |
| 2 | 9.4 | 12530387-2202334 | 3502334246914338432 | 12h53m04.1s -22d02m41.2s | 193.2668 -22.04446 | 303.43, 40.83 | 19.72 | 15.87 | 0.601 | 0.609 | 0.244 | 123.2 | 10.42 | 21.43 | dM-locus | 02-05 |
| 3 | 9.4 | 01291182-4111092 | 5008076354130872704 | 01h29m12.5s -41d11m12.1s | 22.3015 -41.18656 | 276.43, -73.94 | 19.90 | 15.91 | 0.393 | 0.859 | 0.241 | 108.8 | 10.73 | 21.55 | subdwarf-tendency | 12; 08-11 |
| 4 | 9.1 | 10505100-0719353 | 3764064640489783424 | 10h50m50.5s -07d19m34.1s | 162.71071 -7.3262 | 258.3, 44.84 | 19.73 | 15.97 | 0.365 | 0.714 | 0.277 | 125.6 | 10.47 | 21.71 | subdwarf-tendency | 01-04 |
| 5 | 8.4 | 01010126-1851052 | 2356451987547034624 | 01h01m01.8s -18d51m08.5s | 15.25705 -18.85223 | 138.35, -81.44 | 19.77 | 15.99 | 0.612 | 0.43 | 0.16 | 144.9 | 10.18 | 21.43 | subdwarf-tendency | 08-11 |
| 6 | 7.9 | 20465615-2010032 | 6857242878104953472 | 20h46m56.2s -20d10m10.8s | 311.73426 -20.16935 | 25.98, -34.1 | 19.78 | 16.11 | 0.429 | 0.736 | 0.264 | 144.0 | 10.32 | 21.29 | subdwarf-tendency | 06-09 |
| 7 | 7.9 | 01591123+3038356 | 301092566253730176 | 01h59m11.1s +30d38m28.6s | 29.79646 30.6416 | 139.76, -30.01 | 19.89 | 16.22 | 0.757 | 0.702 | 0.255 | 124.1 | 10.75 | 21.88 | dM-locus | 12; 08-11 |
| 8 | 7.7 | 01105250+4836063 | 401818418452566528 | 01h10m53.3s +48d36m07.5s | 17.72152 48.60202 | 126.25, -14.14 | 19.84 | 16.16 | 0.492 | 0.662 | 0.216 | 135.5 | 10.5 | 21.63 | dM-locus | 12; 08-11 |
| 9 | 7.3 | 08165243+3249042 | 901648948375442304 | 08h16m52.4s +32d48m56.8s | 124.21849 32.81609 | 189.28, 31.3 | 19.98 | 16.25 | 0.448 | 0.818 | 0.215 | 159.4 | 10.23 | 21.61 | subdwarf-tendency | 12; 01-03 |
| 10 | 7.2 | 11053702-3917324 | 5390732032963218560 | 11h05m36.9s -39d17m40.7s | 166.4039 -39.29428 | 281.53, 19.14 | 19.94 | 16.17 | 0.696 | 0.432 | 0.184 | 164.2 | 10.09 | 21.73 | dM-locus | 01-05 |
| 11 | 7.0 | 23581181-4809099 | 6524223380403161216 | 23h58m12.5s -48d09m11.4s | 359.55164 -48.15308 | 325.64, -66.56 | 19.85 | 16.16 | 0.523 | 0.796 | 0.267 | 149.4 | 10.29 | 21.23 | dM-locus | 07-11 |
| 12 | 6.5 | 13281113-2106220 | 6196682920934083328 | 13h28m10.6s -21d06m25.5s | 202.04444 -21.10693 | 314.3, 40.95 | 19.76 | 16.23 | 0.097 | 0.872 | 0.146 | 192.4 | 9.81 | 21.49 | subdwarf-tendency | 02-06 |
| 13 | 6.5 | 17373995+5757128 | 1422465410061938816 | 17h37m39.3s +57d57m07.5s | 264.41434 57.95233 | 86.33, 32.41 | 19.87 | 16.34 | 0.546 | 0.72 | 0.181 | 146.0 | 10.52 | 21.2 | sdM/esdM-consistent | 04-08 |
| 14 | 6.0 | 13353242+4737281 | 1552157548201668352 | 13h35m31.8s +47d37m29.3s | 203.88285 47.62477 | 103.02, 67.76 | 19.93 | 16.12 | 0.21 | 0.937 | 0.214 | 154.4 | 10.18 | 21.75 | subdwarf-tendency | 02-06 |
| 15 | 5.8 | 02360140-2326537 | 5125419911539221760 | 02h36m02.0s -23d26m52.6s | 39.00784 -23.448 | 209.91, -66.12 | 19.82 | 16.26 | 0.415 | 0.479 | 0.164 | 205.9 | 9.69 | 21.13 | dM-locus | 12; 09-11 |
| 16 | 5.6 | 14143528-5459154 | 5895741949871112320 | 14h14m34.9s -54d59m21.7s | 213.64564 -54.98909 | 314.74, 5.96 | 19.97 | 16.49 | 0.954 | 0.321 | -0.198 | 165.9 | 10.39 | 21.82 | underluminous-vs-dM | 02-06 |
| 17 | 5.4 | 23280842+1406391 | 2813361564957760896 | 23h28m09.0s +14d06m37.8s | 352.0371 14.11056 | 94.26, -44.07 | 19.82 | 16.39 | 0.468 | 0.627 | 0.156 | 194.2 | 9.95 | 21.32 | subdwarf-tendency | 07-11 |
| 18 | 5.1 | 18171236+2700060 | 4585911133706711680 | 18h17m12.2s +26d59m57.7s | 274.30086 26.9997 | 54.23, 18.97 | 19.83 | 16.44 | 0.796 | 0.516 | 0.181 | 164.3 | 10.36 | 21.41 | underluminous-vs-dM | 05-08 |
| 19 | 4.5 | 10155907+3739175 | 754205087630663808 | 10h15m58.9s +37d39m10.5s | 153.99552 37.65321 | 185.07, 55.81 | 19.93 | 16.52 | 0.538 | 0.68 | 0.243 | 207.2 | 9.94 | 21.27 | dM-locus | 01-04 |
| 20 | 4.3 | 11094034+4349100 | 778994474926961152 | 11h09m40.2s +43d49m02.4s | 167.41744 43.81766 | 167.1, 63.59 | 20.00 | 16.49 | 0.316 | 0.655 | 0.221 | 248.6 | 9.52 | 21.57 | subdwarf-tendency | 01-05 |
| 21 | 4.2 | 13203250+0608566 | 3717399923897977984 | 13h20m32.0s +06d08m53.8s | 200.1338 6.1484 | 322.49, 67.91 | 19.87 | 16.64 | 0.975 | 0.362 | 0.202 | 186.2 | 10.29 | 21.56 | dM-locus | 02-06 |
| 22 | 3.8 | 14473938+0734261 | 1173260339417897344 | 14h47m39.1s +07d34m20.4s | 221.91298 7.57259 | 2.94, 56.23 | 19.98 | 16.57 | 0.523 | 0.406 | 0.222 | 214.8 | 9.91 | 21.31 | dM-locus | 03-06 |
| 23 | 3.8 | 20580002-1648251 | 6882834217400083968 | 20h58m00.4s -16d48m30.5s | 314.5014 -16.80826 | 30.94, -35.37 | 19.96 | 16.62 | 0.497 | 0.634 | 0.156 | 204.2 | 10.07 | 22.15 | subdwarf-tendency | 06-10 |
| 24 | 3.7 | 14592461+4050354 | 1296928326363004416 | 14h59m24.0s +40d50m30.5s | 224.85044 40.84201 | 68.77, 60.37 | 19.97 | 16.75 | 0.568 | 0.5 | 0.137 | 205.3 | 10.18 | 21.23 | subdwarf-tendency | 03-06 |
| 25 | 3.6 | 20141504-5819572 | 6444364648283689984 | 20h14m15.2s -58d20m05.3s | 303.56314 -58.33446 | 339.05, -33.59 | 19.74 | 16.66 | 0.509 | 0.692 | 0.189 | 220.8 | 9.94 | 21.37 | subdwarf-tendency | 06-09 |
| 26 | 3.2 | 09121662+1905436 | 635546381171304704 | 09h12m16.6s +19d05m35.9s | 138.0691 19.09364 | 209.77, 39.35 | 19.95 | 16.72 | 0.557 | 0.346 | 0.056 | 281.0 | 9.48 | 21.16 | underluminous-vs-dM | 12; 01-04 |
| 27 | 3.0 | 15062695-0655349 | 6333056821300966272 | 15h06m26.5s -06d55m37.4s | 226.61056 -6.92694 | 351.68, 42.81 | 19.71 | 16.56 | 0.724 | 0.27 | 0.079 | 304.8 | 9.14 | 21.23 | underluminous-vs-dM | 03-06 |
| 28 | 3.0 | 02145061+3014535 | 324266972833697920 | 02h14m51.2s +30d14m48.6s | 33.71292 30.24702 | 143.57, -29.26 | 19.76 | 16.68 | 0.316 | 0.93 | 0.296 | 213.1 | 10.03 | 21.36 | subdwarf-tendency | 12; 09-11 |
| 29 | 1.8 | 05164710+2721224 | 3421414069467005696 | 05h16m47.6s +27d21m16.9s | 79.19786 27.35492 | 177.84, -6.18 | 19.79 | 16.82 | 0.574 | 0.658 | 0.079 | 348.3 | 9.11 | 21.19 | underluminous-vs-dM | 12; 01; 10-11 |

The CSV carries the full detail per object: pmra/pmdec, parallax with
error, ruwe, 2MASS ph_qual and jdate, blink z, H_J reduced proper
motion, the per-object class-estimate note, and the full 12-month
visibility list.

## Top-10 quick-look (commissioning subset)

| # | 2MASS | blink z | ruwe | plx ± err (mas) | 2MASS ph_qual | best month |
|---|---|---|---|---|---|---|
| 1 | 13375104+3700289 | 0.22 | 1.07 | 8.164 ± 0.422 | AAA | 2027-04 |
| 2 | 12530387-2202334 | 0.34 | 0.97 | 8.119 ± 0.434 | AAC | 2027-04 |
| 3 | 01291182-4111092 | 0.29 | 1.06 | 9.193 ± 0.386 | ABB | 2027-10 |
| 4 | 10505100-0719353 | 0.15 | 1.01 | 7.961 ± 0.544 | AAC | 2027-03 |
| 5 | 01010126-1851052 | 0.42 | 1.01 | 6.903 ± 0.400 | AAC | 2027-10 |
| 6 | 20465615-2010032 | 0.29 | 1.09 | 6.947 ± 0.558 | ABC | 2027-08 |
| 7 | 01591123+3038356 | 0.09 | 1.08 | 8.060 ± 0.484 | AAC | 2027-10 |
| 8 | 01105250+4836063 | 0.42 | 1.02 | 7.381 ± 0.454 | ABB | 2027-10 |
| 9 | 08165243+3249042 | 0.08 | 1.06 | 6.273 ± 0.494 | ABB | 2027-01 |
| 10 | 11053702-3917324 | 0.48 | 1.12 | 6.089 ± 0.483 | ABC | 2027-03 |

All ruwe ≤ 1.13 (clean astrometric solutions, no unresolved-binary
warning), plx S/N ≥ 12, blink z ≤ 0.48 (tight three-epoch PM
coherence). Rank 1-2 are the brightest (J 15.84/15.87) and nearest
(~122 pc) with AAA/AAC 2MASS quality — the natural first-night pair.

## Expected spectral features (what to look for)

The cohort's W1−W2 spans −0.2..+0.30 and J−H 0.10..0.97: late-M
photosphere territory, no L-dwarf-like W1−W2 anywhere. The
discrimination the follow-up wants is **disk dM vs metal-poor
subdwarf (sdM/esdM)** — the two families separate most cleanly in the
red-optical, but see the feasibility note below.

Red-optical (6000-9000 Å) — the classic sdM diagnostics:
- **Disk dM**: very deep TiO band heads (670, 710, 760, 820, 845 nm),
  VO at 745 nm appearing toward M6+; strong, pressure-broadened
  Na I 8190 Å and K I 7665/7699 Å; H-alpha emission common.
- **Subdwarf (sdM/esdM)**: TiO/VO visibly weakened for the same
  temperature class; hydrides strengthened — CaH (638, 690 nm),
  MgH (~520 nm), FeH Wing-Ford band (869 nm), CrH (861 nm); narrower
  alkali lines (lower pressure at lower metallicity). The
  CaH/TiO-band-ratio schemes (Lépine-style z-type indices) were built
  exactly for this discrimination.

Near-IR (0.9-2.5 µm) — the practical band here (see exposure note):
- FeH 0.99 µm; K I doublet 1.17/1.25 µm (strong and broad in dM,
  weaker/narrower in sdM); H2O bands at 1.4 and 1.9 µm (shallower in
  metal-poor photospheres); CO 2.3 µm overtone (weaker in sdM).
- Cross-checks: low W1−W2 (≤ 0.10) at a mid/late-M temperature ranking
  favors metal-poor photospheres; several targets show exactly this
  combination (09121662+1905436, 15062695-0655349, 05164710+2721224 at
  W1−W2 ≈ 0.06-0.08).

Feasibility note (honest): with V_est ≈ 21.2-22.2, red-optical
spectroscopy of these objects on a 2-4 m telescope is effectively
out of reach (8-10 m class territory); on a 2-4 m the follow-up is a
**NIR (J-band-centered) spectroscopy program**, and the sdM/dM call
must ride on the 0.9-1.3 µm features (FeH 0.99, K I 1.17/1.25, the
1.1-1.35 µm H2O/TiO depression) plus the IR colors — or wait for
8 m-class red-optical access.

## Exposure-time rule-of-thumb (2-4 m class, NIR spectrograph)

Baseline: a modern NIR spectrograph (SpeX-prism / NIHTS / 4MOST-NIR
class, R ≈ 1000-2000) on a 2.5-4 m telescope reaches SNR ≈ 20-30 per
resolution element at J = 16.0 in ~30 min under typical conditions.
Scaling t ≈ 30 min × 10^(0.4·(J−16.0)):

| J | t for SNR ~20-30 |
|---|---|
| 15.84 (rank 1) | ~26 min |
| 16.2 (median) | ~36 min |
| 16.5 | ~47 min |
| 16.82 (faintest) | ~64 min |

So the full 29-target program is roughly 15-20 h of 2-4 m NIR time
(plus overheads), and every target is a single-night feasibility.
Caveats: instrument-dependent (ETC-grade numbers beat this
rule-of-thumb by factors the observer should check), seeing/moon
dependent, and the J≈16.5-16.8 tail assumes good conditions. An
8-10 m class NIR program would take minutes per object.

## Observability summary (RA rule, next 12 months, +20° site)

| months (2026-12 → 2027-11) | 12 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| targets observable | 8 | 7 | 12 | 15 | 15 | 13 | 13 | 7 | 11 | 11 | 10 | 9 |

Every month has ≥7 of the 29 visible; the richest windows are
**Feb-Jun** (12-15 targets each) and a second block **Aug-Nov**.
Peak months (Mar/Apr) are when ranks 1, 2, 12, 14, 21 (the RA 13 h
group) and rank 4/22 transit at midnight. Practical note: the RA-rule
ignores declination — 3 targets (23581181-4809099 at −48°,
14143528-5459154 at −55°, 20141504-5819572 at −58°) are marginal to
inaccessible from a +20° site (max altitude 6-17°) and need a southern
site regardless of month; conversely the +37..+58° dec group is
visible all night in its season from a northern site.

## Cohort color/spectral summary (estimates)

- Class-estimate distribution: 13 subdwarf-tendency, 10 dM-locus,
  5 underluminous-vs-dM (fainter but not bluer than the disk sequence
  at matched temperature — sdM *or* a photometry/parallax issue),
  1 sdM/esdM-consistent (17373995+5757128).
- M_J spans 9.1-10.8: mid-to-late M absolute magnitudes. At their
  J−H colors (median 0.52, several ≤ 0.45) most objects sit at or
  below the disk-dM locus — the expected metal-poor direction — but
  none sits far enough below the disk sequence for a confident
  color-only subdwarf call. That ambiguity is the experiment.
- Two objects carry photometry flags: 14143528-5459154 has
  W1−W2 = −0.20 (unphysical for a cool photosphere; its CatWISE
  counterpart was also the cohort's loosest blink match at 0.98") —
  treat its WISE photometry as suspect pending re-measurement;
  02145061+3014535 pairs a strongly blue J−H (0.32) with a very red
  H−K and high W1−W2 (0.30) — inconsistent color triple, verify
  2MASS/WISE photometry before interpreting. 13203250+0608566
  (J−H = 0.97) is the reddest J−H — possible 2MASS blend, verify.
- 2MASS photometry sits at the survey limit (J 15.8-16.8): most
  objects carry at least one C-quality band (ph_qual in the CSV), so
  individual colors carry ~0.1-0.2 mag uncertainty. The cohort-level
  conclusions are robust to that; per-object calls are not.
- The single lowest PM-coherence object is rank 14
  (1552157548201668352, blink z = 2.03, implied 184 vs Gaia 218
  mas/yr) — still accepted by F-21's 3σ rule but the loosest; if
  telescope time is short, re-check its astrometry before spending an
  exposure.

## Honest failures

- **fetch_2mass propagation sign bug (caught this session)**: the
  first draft of the live-IRSA fallback propagated positions by
  `EPOCH_GAIA - 2000.0` (+16 yr) instead of `2000.0 - EPOCH_GAIA`
  (−16 yr), aiming the 2MASS cone 2×pm×16 yr ≈ 8" off-slot. Caught by
  live spot-checking one object against the F-21 state hit (separation
  returned 8.39" vs the F-21 blink value 0.54"); fixed before any
  packaged number was produced. The default offline path (state file)
  was never affected; the CatWISE fallback dt (−0.5 yr) was correct.
- **Classifier magnitude-sign inversion (caught pre-publication)**: the
  first draft compared M_J to the dM anchors with the inequality
  direction backwards (magnitude conventions), labeling the whole
  cohort "brighter-than-dM". Rewritten to the explicit chain: W1−W2 →
  temperature anchor → M_J/J−H offsets → label; labels now carry
  explicit offsets in the CSV notes.
- **No full live re-pull of IRSA photometry**: the packaged J/H/K/W1/W2
  values come from the F-21 state file (IRSA TAP, 2026-11-11), with a
  one-object live cross-check (exact match, J/H/K/jdate/quality
  identical). A full re-pull (29×2 queries, ~1.5 s + ~13 s each) was
  skipped as redundant within the bounded session; `--live` regenerates
  it if wanted.
- **Visibility rule is RA-only** (documented approximation): no
  declination, twilight, or moon handling; the 3 far-south objects are
  handled by a separate declination note instead.
- **V transformation extrapolated** past its fitted BP−RP range
  (2.75 → cohort 2.6-3.5) and fit on solar-metallicity standards;
  subdwarf V would deviate. ±0.3-0.5 mag systematic on V_est.
- **dM anchor table compiled from memory of standard color tables**
  (Pecaut-Mamajek-style / Skrzypek-style), not re-fitted from data;
  good to ~0.3-0.5 mag in M_J and ~0.05 mag in colors. Labels are
  deliberately coarse (locus / tendency / consistent) to match that
  precision.

## Reproducibility

```
python3 scripts/spectroscopy_targets.py          # package from committed CSVs + local blink_state.json
python3 scripts/spectroscopy_targets.py --live   # force live IRSA re-pull (fp_psc + catwise_2020, polite 1.5 s rate)
python3 scripts/spectroscopy_targets.py --md     # print the per-object summary lines
```

State: no state file for this stage (single-pass, deterministic from
inputs); every live HTTP query is appended to
`results/spectroscopy_querylog.csv`. The Gaia→V polynomial, dM anchor
table, priority weights, and visibility rule are all constants at the
top of the script — change them there and re-run.
