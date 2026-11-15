# B-4 — cross-check against Karpov, Malkov & Avdeeva 2025 (J/A+A/695/A195)

**What this is.** Roadmap item B-4: cross-check the lab's high-PM candidate
lists (621 possible-new survivors; the 35 highest-priority = 29 PROMOTED +
6 CONF-A-STAYS from `results/blink_vetting.md`) against Karpov, Malkov &
Avdeeva 2025, "New ultracool dwarf candidates from multi-epoch WISE data",
A&A 695, A195 (arXiv:2408.15067) — 21,885 significant-PM detections in
unTimely single-epoch WISE coadds. **Candidates, not claims.**

**What actually exists of that catalog** (established below): the authors
publish **only the 258-object "previously unpublished" table** — as VizieR
`J/A+A/695/A195/table2` ("New high-proper-motion objects detected in this
work", the objects with no SIMBAD *and* no Gaia DR3/DR2 association) and,
with all 93 columns, on Zenodo (doi:10.5281/zenodo.14651237). The full
21,885-row list is **not published as a table anywhere** (paper text gives
only aggregate association counts: 20,555 Gaia DR3 + 104 Gaia DR2
associations; 21,370 SIMBAD associations). The B-4 headline "how many
appear in the full 21,885" is therefore **not computable from public data**
— documented as an honest limitation, not a network failure.

**Headline results** (vs the 258-unpublished subset, the only published table):

| question | result |
|---|---|
| priority-35 candidates in Karpov's 258-unpublished | **0 / 35** |
| all 621 possible-new candidates in Karpov's 258-unpublished | **0 / 621** |
| any candidate vs Karpov-258 within 5" near-band | 0 (closest approach **778"** ≈ 13′) |
| candidates in the full 21,885 | **not computable** (list unpublished) |
| why zero is expected | **all 621 have pm 160–250 mas/yr, strictly below Karpov's structural detection floor (~275–300 mas/yr)** |

---

## 1. Route history (full log: `results/karpov_querylog.csv`)

Tried in the prescribed order, with retries:

1. **dc.g-vo.org TAP** (G-VO mirror) — connects fine; `TAP_SCHEMA` search
   for `%695%`/Karpov/unTimely returns 0 rows; schema list shows G-VO hosts
   curated schemas only (no VizieR/metaviz mirror). No Karpov table. Dead end.
2. **vizier.cfa.harvard.edu TAP** — `/TAP` and `/tap/sync` 404 (still down
   for TAP; the asu-tsv CGI on the same host works).
3. **CFA asu-tsv** (working route) —
   `https://vizier.cfa.harvard.edu/viz-bin/asu-tsv?-source=J/A%2BA/695/A195&-out=all`
   returns the catalog **default table = `table2`, 258 rows, 96 columns
   (499 KB)**. Subtable probes: `/main`, `/table1`, `/list`, `/data`, … all
   absent (`Error=Table 'table1' does not exist in catalog`); the
   VOTable metadata endpoint (`votable?-source=…&-out.max=0`) enumerates
   exactly **one** `<TABLE>` in the deposit. So the VizieR deposit IS only
   the 258.
4. **CDS Strasbourg** — `cdsarc.cds.unistra.fr` connection fails (curl exit
   000), as expected; CFA's `/viz-bin/cat` and `/viz-bin/ReadMe` time out
   (ReadMe 302-redirects to unreachable CDS anyway).
5. **arXiv:2408.15067 source tarball** (`arxiv.org/e-print`) — fetched
   (1.07 MB); contains LaTeX + figures only, **no machine-readable tables**.
   But `main.tex` names the data release: *"The table is published at
   doi:10.5281/zenodo.14651236"* (commented-out earlier DOI …13362690).
6. **Zenodo** (working route, API reachable) — record 14651236 → version
   14651237, *"New moving objects detected in unTimely WISE W2 band data as
   of 2025-01-15"*, single file `new_moving_final.vot` (494 KB), **258 rows,
   93 columns**.

Two independent copies of the 258 obtained; cross-verified: identical
`candid` sets, max position difference 0.0000″, max PM difference
0.000 mas/yr (bit-identical data). Cached at `/tmp/astro_e/karpov258.csv`.

## 2. Schema of the Karpov table (what matters for matching)

- `candid` (unTimely candidate id, e.g. `0194m727w2o0020398e004`), `cwise`
  (CatWISE2020 designation `JHHMMSS.ss±DDMMSS.s`).
- **`raj2016`/`dej2016` — positions at Ep=J2016.0** (ReadMe description and
  the Zenodo field names both state it; the paper propagated its tracks to
  J2016.0 to match Gaia DR3 with a 2″ radius). No MJD/epoch column exists
  (single-epoch detections were combined into tracks; the track fit is the
  catalog position).
- `pmra`, `e_pmra`, `pmdec`, `e_pmdec`, `pm`, `e_pm` in **arcsec/yr**;
  `pmra` includes cos(dec) (Gaia convention).
- `W1/e_W1/W2/e_W2`, 40+ optical/IR epochal-photometry columns, `spt*`,
  `dist/dist_err`, `vtan/vtan_err`.
- **No Gaia/SIMBAD id columns and no "unpublished" flag — by construction
  the whole table is the 258-unpublished subset** (paper Table 2: objects
  with no SIMBAD and no Gaia DR3/DR2 association). There is no published
  flag distinguishing a "published portion" because no published portion is
  in the deposit.

Epoch sanity check (independent of metadata): residual between `raj2016`/
`dej2016` and the CatWISE-2015.5 designation position has a per-row
dot-product fit dt with median **0.47 yr ≈ 0.5 yr** — consistent with
J2016.0 given the ~1″ scatter the paper itself attributes to CatWISE2020
deblending/association problems. Adopted common epoch: **J2016.0 on both
sides** (our candidates' `ra2016/dec2016` are Gaia DR3 positions at 2016.0,
verified against a fresh Gaia pull: max offset 0.025″ = rounding).

## 3. Method (`scripts/karpov_crossmatch.py`)

- Gaia DR3 vectors for all 621 candidates re-fetched from gaia.aip.de sync
  TAP (2 POST chunks; `ra/dec/pmra/pmdec/pmra_error/pmdec_error/parallax/G/
  bp_rp/ruwe`; 621/621 retrieved). Gaia DR3 native epoch = 2016.0 = Karpov
  epoch, so the propagation term is zero; the epoch-aware code is kept
  general (propagate Gaia position by pm×Δt to each row's epoch) so the
  script stays correct for any future per-row-epoch table.
- Accept radius = max(2.5″, 1.5·pm_karp·|t_karp−2016.0| + 2″) = **2.5″**
  (constant, since t_karp = 2016.0 exactly). Near-band to 5″ recorded for
  review only. All separations client-side (numpy great-circle; RA/Dec
  window prefilter; no server `DISTANCE()`).
- PM-vector test per match: dp = |pm_karp − pm_gaia| with per-component
  σ = √(e_karp² + e_gaia²) (Karpov errors from the table, Gaia errors from
  DR3 — no floor needed), z = dp/σ; z < 5 → corroborated, ≥ 5 →
  contradiction flag.
- Verdicts (per the task's vocabulary): `karpov-corroborated (unpublished)`
  / `karpov-contradiction (flag only)` / `no-karpov-detection`.

**Verification of the matcher and of the zero** (no hits existed to inspect,
so the negative itself was verified):

- *Injection test* (built in, `--selftest`): a synthetic candidate placed
  exactly on Karpov row 0 with Karpov's own PM is recovered at sep 0.0000″,
  dp_z 0.00. The pipeline works end-to-end.
- *Nearest-neighbour distribution*: nearest Karpov-258 row to any of the
  621 candidates is **778.5″** (1st pct 2016″, median 22,188″). No
  positional coincidence exists at any radius that could matter.
- *Widened scan*: zero pairs within 15″ unpropagated.

## 4. Results and why zero is the expected outcome

Karpov's detection algorithm requires **pairs of unTimely epoch detections
separated by ≥ 3″** across epochs spanning ~10.9 yr (Jan 2010–Dec 2020) —
the paper states this "effectively plac[es] a lower limit on the detectable
proper motion of about 0.3″/year". Our cohort:

| set | pm range (mas/yr) | ≥ 275 mas/yr (3″/10.9 yr floor) | ≥ 300 mas/yr (paper's ~0.3″/yr) |
|---|---|---|---|
| 621 possible-new | 159.8 – 250.0 | 0 | 0 |
| 35 priority | 215.3 – 249.9 | 0 | 0 |

**Not one of the 621 candidates reaches Karpov's motion floor.** Their
algorithm cannot detect this cohort even in principle (modulo measurement
noise letting a pair squeak past 3″), so `no-karpov-detection` for all 621
is the by-construction result — a statement about the two surveys'
complementary regimes, not about candidate quality. Karpov's own flux cut
agrees: their efficiency is ~100% for W2 < 15 and degrades for fainter
objects, while our cohort sits at G = 19.0–20.0.

Properties of Karpov's 258 (for contrast): pm 147–1049 mas/yr (median 338;
56 rows below 275 mas/yr because the *published* PMs are refined with
multiwavelength associations on a ~20 yr 2MASS→WISE baseline, which can
fall below the unTimely-only detection floor); W2 11.7–16.1 (median 15.2);
spectral types M4–T8.

### The 35 priority candidates (per-candidate record; no matches exist)

All 35: verdict `no-karpov-detection`, note `below-karpov-motion-floor`,
in_unpublished258 `n`, karpov_match_count 0. Nearest Karpov-258 row:

| source_id | blink verdict | pm mas/yr | nearest Karpov-258 row |
|---|---|---|---|
| 2813361564957760896 | PROMOTED | 249.9 | 12,569″ |
| 5390732032963218560 | PROMOTED | 248.9 | 23,685″ |
| 324266972833697920 | PROMOTED | 248.9 | 20,360″ |
| 778994474926961152 | PROMOTED | 248.7 | 5,698″ |
| 6333056821300966272 | PROMOTED | 248.6 | 14,323″ |
| 4585911133706711680 | PROMOTED | 247.2 | 6,974″ |
| 914350468044697600 | CONF-A-STAYS | 247.1 | 10,818″ |
| 3717399923897977984 | PROMOTED | 246.7 | 34,406″ |
| 1296928326363004416 | PROMOTED | 246.4 | 6,512″ |
| 3485388058311031552 | CONF-A-STAYS | 246.3 | 19,804″ |
| 6444364648283689984 | PROMOTED | 245.6 | 1,117″ |
| 6196682920934083328 | PROMOTED | 245.6 | 13,589″ |
| 3151381813350665472 | CONF-A-STAYS | 242.0 | 31,351″ |
| 3502334246914338432 | PROMOTED | 239.2 | 8,309″ |
| 3421414069467005696 | PROMOTED | 238.5 | 51,278″ |
| 3764064640489783424 | PROMOTED | 238.4 | 20,277″ |
| 1173260339417897344 | PROMOTED | 237.9 | 47,968″ |
| 5125419911539221760 | PROMOTED | 235.3 | 61,097″ |
| 2468119419256161024 | CONF-A-STAYS | 234.6 | 11,209″ |
| 401818418452566528 | PROMOTED | 234.2 | 10,969″ |
| 6857242878104953472 | PROMOTED | 231.2 | 47,719″ |
| 2356451987547034624 | PROMOTED | 230.9 | 9,181″ |
| 635546381171304704 | PROMOTED | 227.7 | 41,743″ |
| 5008076354130872704 | PROMOTED | 227.0 | 18,759″ |
| 4750308012051385472 | CONF-A-STAYS | 226.1 | 28,987″ |
| 6524223380403161216 | PROMOTED | 224.8 | 38,138″ |
| 1422465410061938816 | PROMOTED | 224.4 | 23,076″ |
| 1472427974342097152 | PROMOTED | 222.9 | 27,001″ |
| 5895741949871112320 | PROMOTED | 222.8 | 22,327″ |
| 901648948375442304 | PROMOTED | 221.5 | 18,633″ |
| 6882834217400083968 | PROMOTED | 221.3 | 39,765″ |
| 301092566253730176 | PROMOTED | 220.7 | 23,035″ |
| 754205087630663808 | PROMOTED | 218.1 | 18,309″ |
| 1552157548201668352 | PROMOTED | 217.9 | 9,449″ |
| 343753621705610368 | CONF-A-STAYS | 215.3 | 14,072″ |

(For the remaining 586 of the 621 the same holds; per-candidate rows are in
`results/karpov_crossmatch.csv` — 54.8 KB, one row per candidate.)

## 5. Honest failures and limitations

- **The full 21,885-row list is unpublished** — the binding limitation. It
  is absent from the VizieR deposit (only `table2` exists), from arXiv, and
  from Zenodo; the paper releases only the 258 no-SIMBAD/no-Gaia objects.
  Numbers against the full 21,885 (the "published portion" checks) cannot
  be produced. If the authors were contacted, a full-list cross-check would
  be the natural B-4 follow-up.
- Even for the published portion, an overlap there would be a
  *known-PM-source* corroboration, not an independent-discovery overlap;
  the 258 is the only subset where "independent discovery overlap" could
  apply — and that subset is Gaia-blind by construction (no Gaia DR3/DR2
  association), while our candidates are Gaia sources, so overlap was
  always going to be rare.
- CDS Strasbourg unreachable (all attempts); CFA TAP endpoints 404; CFA
  `/viz-bin/cat` and `/ReadMe` time out at 120–500 s; aanda.org 403.
  CFA asu-tsv CGI and Zenodo API carry the delivery.
- No per-object detection-epoch column exists in any released table; the
  J2016.0 common-epoch assumption rests on the ReadMe text, the Zenodo
  field names (`raj2016`/`dej2016`) and the paper's own Gaia-matching
  procedure, cross-checked against CatWISE designations (§2). Moot for the
  verdict here given the 778″ closest approach.

## 6. Reproduce

```
cd /home/aditya/repos/open-research-lab/astronomy/high-pm-survey
python3 scripts/karpov_crossmatch.py --selftest
```

Refetches Karpov-258 (Zenodo → VizieR fallback) and Gaia-621 (gaia.aip.de
sync TAP) if `/tmp/astro_e/{karpov258.csv,gaia621.csv}` are absent; appends
every route attempt to `results/karpov_querylog.csv`; writes
`results/karpov_crossmatch.csv` and `/tmp/astro_e/karpov_hits.json`.
Raw caches: `/tmp/astro_e/new_moving_final.vot`, `/tmp/astro_e/asu_tsv.tsv`,
`/tmp/astro_e/arxiv_extract/` (arXiv source).

## 7. Relationship to Karpov+

The two searches are complementary, not competing: Karpov+ 2025 search
unTimely single-epoch W2 coadds for tracks moving **faster than ~0.3″/yr
(≈275–300 mas/yr)** at W2 ≲ 16, with no Gaia requirement (indeed their
flagship 258 have *no* Gaia association); this survey selects **Gaia DR3
astrometry at |pm| > 150 mas/yr, G < 20, RUWE < 1.4**, i.e. fainter,
slower, and optically confirmed. The 150–275 mas/yr band where all 621 of
our candidates live is *structurally invisible* to Karpov's pair-separation
algorithm. Zero overlap with their 258-unpublished list is therefore
expected and is not evidence against any candidate; nor does the 258
overlap absence affect our "uncatalogued in SIMBAD" claims, which were
formed against SIMBAD/GCNS/Kirkpatrick sets, not against Karpov's Gaia-
associated base list (whose membership is unpublished). Had any of our
candidates appeared in Karpov's 258, it would have been an
**independent-discovery corroboration** — both surveys found it — and the
claim language would have narrowed to "uncatalogued in SIMBAD; newly listed
by Karpov 2025"; the checked verdicts in `results/karpov_crossmatch.csv`
retain exactly that vocabulary (`karpov-corroborated (unpublished)`) so a
future re-run against any released full list reuses it unchanged. The
actionable takeaway is symmetric: for any future candidate with
pm > 300 mas/yr, a Karpov-258 cross-check becomes informative and this
script runs it as-is.
