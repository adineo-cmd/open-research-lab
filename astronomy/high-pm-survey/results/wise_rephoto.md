# WISE re-photometry — the two F-25 flagged F-21 DOWNGRADED candidates

**What this is.** F-25 flagged two spectroscopy-package candidates whose
colors/counterparts needed WISE re-photometry: Gaia DR3
**5286902985287361280** and **6645353862012156928** — the two of the four
F-21 DOWNGRADED objects that were flagged on **CatWISE PM-vector
disagreement** (z = 11.5 and 6.0). F-21's own downgrades note that 2MASS
still corroborated Gaia in 3 of 4 cases → the working hypothesis was
**contamination** (a different CatWISE source than the F-21 nearest match
explains the disagreement). This note tests that hypothesis with
position-doubled, wider-radius CatWISE2020 re-pulls and per-source
photometry. **Candidates, not claims.**

**Data pulled live 2026-11-12** (IRSA TAP `catwise_2020`, epoch 2015.5;
positions propagated from Gaia DR3 2016.0 with the F-21 ledger PMs using
the `blink_vet.py` math; client-side separations — IRSA `DISTANCE()`
units are unreliable on this table). Cones: 15" at the expected 2015.5
position AND at the Gaia 2016.0 position (merged by `source_id`), plus a
6" probe at the expected 2000.0 (2MASS-epoch) position. Polite rate: one
IRSA query per ≥13 s. 6 IRSA queries total; 2 Gaia-error queries failed
(see Honest failures).

**Headline results**

| object | verdict | one-line |
|---|---|---|
| 6645353862012156928 | **wrong-identity contamination NOT supported; F-21 CatWISE-PM mismatch has a measured blend mechanism** | on-track match confirmed positionally + by the 2MASS 15-yr baseline; a W1=13.4 neighbor at 6.4" (≈1 PSF FWHM) carries a CatWISE PM vector matching Gaia's to 3.7 mas/yr |
| 5286902985287361280 | **no consistent solution; stays DOWNGRADED** | positional match's CatWISE PM is exactly 2.00× Gaia's magnitude at 5.1° (crowding signature); no PM-consistent on-track alternative; 2MASS interloper unexplained |
| both | **colors: not UCD-red** | on-track sources have W1−W2 = 0.19 / 0.23 — well below the ≳0.5 UCD threshold |

---

## 1. Gaia DR3 6645353862012156928 — contamination hypothesis REJECTED, downgrade re-interpreted

Gaia 2016.0: 292.61164 −53.24333; PM (7.9, −230.0) mas/yr (230.1);
ϖ 4.96 mas → 202 pc; G 19.816. Expected 2015.5: 292.61164 −53.24330.

CatWISE2020 field (merged 15" cones; full table in `wise_rephoto.csv`):

| rank | cw source_id | sep(exp2015.5) | W1 | W2 | W1−W2 | CW PM (mas/yr) | CW PM tot | dp vs Gaia | z | f21 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2934m531_b0-014087 | **0.41"** | 15.535 | 15.306 | 0.23 | (155.1, −94.7) | 181.8 | 200.0 | 6.0 | **Y** |
| 2 | 2934m531_b0-002590 | 6.41" | **13.399** | 13.217 | 0.18 | (**4.2, −230.0**) | **230.0** | **3.7** | **0.44** | N |
| 3 | 2934m531_b0-078934 | 10.84" | 17.733 | 17.024 | 0.71 | (−101.7, 245.0) | 265.3 | 487.4 | 3.4 | N |
| 4 | 2934m531_b0-128461 | 13.37" | 18.538 | 17.476 | 1.06 | (127.8, 78.0) | 149.7 | 330.5 | 1.1 | N |

Findings:

1. **The F-21 match is positionally the Gaia object.** 0.41" from the
   expected 2015.5 position; field density ~7.3×10⁴ deg⁻² (4 sources in
   the 15" cone) → P(a random source within 0.41") ≈ 0.3%. Its W1 = 15.54
   fits the 2MASS slot hit (J = 16.588, J−W1 = 1.05) as the same source.
2. **The 2MASS 15-yr baseline corroborates the Gaia PM** (recomputed from
   the F-21 hit 2MASS 19302678-5314326, epoch 2000.78, 0.39" from the
   expected 2000.0 slot): implied PM (+8.0, −222.6) vs Gaia
   (+7.9, −230.0) mas/yr.
3. **The PM-vector failure has a measured mechanism.** Source #2 —
   W1 = 13.40 (7× the flux of the match), **6.4" away ≈ 1 WISE PSF
   FWHM** — has a CatWISE PM vector of (4.2, −230.0) mas/yr: **Gaia's
   vector to 3.7 mas/yr** (PA −89.0° vs −88.0°; magnitude 230.0 vs
   230.1). A 7×-brighter, fast-moving neighbor one PSF width from a
   W1≈15.5 source is exactly the configuration that corrupts a faint
   source's CatWISE PSF-fit PM (the match has no other neighbor within
   3"). Reading #2 as a **co-moving wide companion** (projected 6.5" at
   202 pc ≈ 1300 AU) or as a chance vector match (a priori ~10% for a
   bright source in the cone) does not change the operational conclusion:
   the 181.8-mas/yr CatWISE PM of the positional match is not trustworthy.
4. **No wrong-identity solution exists**: the only sources consistent
   with Gaia's PM are #2 (the neighbor above, 6.4" off-track) and #4
   (z = 1.1 via a 299 mas/yr sigma — meaningless); neither can be the
   Gaia counterpart (#2 was already 6.5" from the Gaia position at
   Gaia's own epoch).

**Verdict:** contamination (wrong CatWISE identity) is **not** supported;
the F-21 DOWNGRADE for this object is re-attributed to a **blend-corrupted
CatWISE PM of the correct counterpart**. The candidate is **revivable**
for the spectroscopy package on the strength of the 2MASS+Gaia two-epoch
baseline — pending a visual blink (LS-DR9 has no coverage at dec −53;
F-21 cutouts were blank tiles; unWISE/WISE coadd blink is the follow-up).
Its re-photometry color W1−W2 = **0.23 ± 0.05** is **not UCD-red**
(below ≳0.5) — an independent reason to keep it low-priority.

## 2. Gaia DR3 5286902985287361280 — no consistent solution; stays DOWNGRADED

Gaia 2016.0: 107.40694 −61.80777; PM (109.0, +215.4) mas/yr (241.4);
ϖ 5.11 mas → 196 pc; G 19.740. Expected 2015.5: 107.40691 −61.80780.

CatWISE2020 field (merged 15" cones):

| rank | cw source_id | sep(exp2015.5) | W1 | W2 | W1−W2 | CW PM (mas/yr) | CW PM tot | dp vs Gaia | z | f21 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1073m621_b0-013943 | **0.17"** | 15.771 | 15.580 | 0.19 | (178.9, 449.4) | **483.7** | 244.2 | 11.5 | **Y** |
| 2 | 1073m621_b0-006426 | 3.86" | **14.759** | 14.592 | 0.17 | (87.9, 257.8) | 272.3 | 47.3 | 5.0 | N |
| 3 | 1073m621_b0-050197 | 11.60" | 17.259 | 17.161 | 0.10 | (39.5, 2.8) | 39.6 | 223.7 | 3.3 | N |
| 4 | 1073m621_b0-098004 | 13.63" | 18.353 | 17.796 | 0.56 | (394.2, 127.7) | 414.4 | 298.4 | 2.1 | N |

Findings:

1. The F-21 match is positionally the Gaia object (0.17";
   P(random) ≈ 0.05%), but its CatWISE PM is **exactly 2.00× Gaia's
   magnitude** (483.7 vs 241.4) in nearly the same direction (5.1°) — a
   classic crowding/blend distortion signature. Source #2 sits **3.83"
   away (0.6 PSF FWHM, 2.5× flux) — inside the blend core** — so a
   corrupted CatWISE PM is plausible; but no clean vector recovery is
   possible from the catalog alone.
2. **No source in the field is both PM-consistent and on-track.** The
   only "consistent" source (#4, z = 2.1) is 13.6" off the expected
   position with a 141 mas/yr PM sigma — a physically meaningless pass
   (the pipeline's coarse auto-verdict "CONTAMINATION-POSSIBLE
   (off-track-consistent-source)" reflects exactly this; the manual
   analysis supersedes it).
3. The 2MASS slot hit from F-21 (07093686-6148315, J = 15.5, 3.92"
   behind the track, implied PM 419 vs 241) is confirmed unrelated — and
   it has **no CatWISE counterpart within 15"** despite J = 15.5, itself
   evidence of severe blending in this field. No stationary CatWISE
   occupant of the expected 2000.0 slot either (nearest 3.8").

**Verdict:** **no consistent solution.** The 11.5σ CatWISE PM
disagreement may be a blend artifact, but with no 2MASS corroboration
and an unexplained bright 2MASS interloper, the Gaia association itself
remains suspect. **Stays DOWNGRADED**; do not restore without a visual
blink. Its on-track color W1−W2 = **0.19 ± 0.04** is **not UCD-red**.

## Honest failures

- **gaia.aip.de TAP** returned an XML error page on the batched
  `pmra_error/pmdec_error` query (the same failure that left the F-21
  ledger PM-error columns empty); the **CDS VizieR TAP** fallback
  (I/355/gaiadr3) was unreachable (3× timeout). Gaia PM errors therefore
  fall back to the 0.5 mas/yr floor used throughout F-21 — all z values
  here are directly comparable to F-21's. The ledger PM-error gap
  remains open (flagged for the next pass; gaia.aip.de worked on
  2026-11-10 during F-11).
- LS-DR9 cutouts for object 2's field: no coverage (blank tiles, as in
  F-21) — no imagery blink possible in this pass.

## Query log (every HTTP query, append-mode; also `wise_rephoto_querylog.csv`)

| ts (UTC) | object | site | svc | ra | dec | r" | n | err |
|---|---|---|---|---|---|---|---|---|
| 2026-11-12T15:30:41Z | both | gaiapm | aip-gaiadr3 | | | | −1 | XML error page |
| 2026-11-12T15:37:20Z | both | gaiapm | vizier-I/355/gaiadr3 | | | | −1 | XML + 3× timeout |
| 2026-11-12T15:37:56Z | 5286902985287361280 | exp2015.5 | irsa-catwise_2020 | 107.40691 | −61.80780 | 15 | 4 | |
| 2026-11-12T15:39:17Z | 5286902985287361280 | gaia2016 | irsa-catwise_2020 | 107.40694 | −61.80777 | 15 | 4 | |
| 2026-11-12T15:40:03Z | 5286902985287361280 | exp2000.0 | irsa-catwise_2020 | 107.40591 | −61.80873 | 6 | 2 | |
| 2026-11-12T15:41:11Z | 6645353862012156928 | exp2015.5 | irsa-catwise_2020 | 292.61164 | −53.24330 | 15 | 4 | |
| 2026-11-12T15:42:12Z | 6645353862012156928 | gaia2016 | irsa-catwise_2020 | 292.61164 | −53.24333 | 15 | 4 | |
| 2026-11-12T15:42:45Z | 6645353862012156928 | exp2000.0 | irsa-catwise_2020 | 292.61158 | −53.24231 | 6 | 2 | |

## Files

- `../scripts/wise_rephoto.py` — reproducible pipeline (targets embedded
  with provenance; reuses `blink_vet.py` propagation/match math; logs
  every query append-mode; ≥13 s IRSA spacing).
- `wise_rephoto.csv` — per-CatWISE-source rows for both objects
  (positions, W1/W2 + errors, PM vectors + sigmas, separations, z,
  neighbor distances, F-21-match flags).
- This note.

## Reproduce

```bash
python3 -I astronomy/high-pm-survey/scripts/wise_rephoto.py \
        astronomy/high-pm-survey/results
```
(Re-runs the 6 IRSA cone queries live; ~13 s/query; writes the CSV,
a recs JSON, and the append-mode query log.)

## Ledger text (proposal — F-32-or-next-free; F-31 taken)

> | F-32 | 2026-11-12 | B | **WISE re-photometry resolves the 2 flagged F-21 DOWNGRADES differently**: 6645353862012156928 — wrong-identity contamination NOT supported (on-track match 0.41", P(coinc) 0.3%; 2MASS 15-yr baseline implied PM (+8.0,−222.6) = Gaia (+7.9,−230.0)); the 6σ CatWISE PM mismatch has a measured blend mechanism — W1=13.4 neighbor at 6.4"≈1 PSF FWHM whose own CatWISE PM matches Gaia's to 3.7 mas/yr (CPM-companion hypothesis, ~1300 AU at 202 pc) → REVIVABLE pending visual blink; 5286902985287361280 — no consistent solution (CatWISE PM = exactly 2.00× Gaia at 5.1°, bright neighbor 3.8" inside PSF core; 2MASS interloper has no CW counterpart) → stays DOWNGRADED. Both on-track W1−W2 = 0.19/0.23 — NOT UCD-red (color argument against UCD for both). Honest negatives: gaia.aip.de + VizieR PM-error pull failed (0.5 mas/yr floor retained) | verified (live IRSA re-pull, 6 logged queries) | open-research-lab astronomy/high-pm-survey/results/wise_rephoto.md |

(Task A's EVROS identification is proposed separately in
open-discovery-lab `track-a-android-blobs/docs/evros-identity.md`,
commit bc9ae688.)
