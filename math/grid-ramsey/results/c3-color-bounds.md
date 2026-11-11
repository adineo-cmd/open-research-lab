# Results — 3-color grid Ramsey minima: first computed values and bounds for T_3(k,n)

Runs 2026-11-11 on the lab box (12 cores; CP-SAT 9.15.6755, seed 20261109,
`num_workers = 3`, per-solve limit 120 s throughout). Definition: for c
colors, a monochromatic rectangle in a k×n grid = 4 cells at two distinct
rows × two distinct columns, all one color; T_c(k,n) = minimum count over
all c-colorings. Tools: `tools/relax_lb3.py` (aggregation LB), 
`tools/min_mono_rect3.py` (exact count model), `tools/count_rects.py`
(independent counter); certificates in `results/certificates/c3_*.json`.

## Prior-art check (all dates verified 2026-11-11)

- **OEIS [A399620](https://oeis.org/A399620) / [A399621](https://oeis.org/A399621)** — minimum mono-rectangle counts, **2-color only** (J. F. Alm, 2026-09-05), rows to n=8. No OEIS sequence gives T_c values for c ≥ 3.
- **OEIS [A191873](https://oeis.org/A191873)** (R. H. Hardin & N. J. A. Sloane, 2011-06-18) — Zarankiewicz numbers (max 1s, no all-1 rectangle): single forbidden symbol, not a c-color minimum count. Not prior art for this question.
- **Cooper, Fenner, Purewal, "Monochromatic Boxes in Colored Grids", [arXiv:0810.3019](https://arxiv.org/abs/0810.3019)** (v1 2008-10-16) — (c,t)-guaranteed grids, i.e. zero-rectangle forcing thresholds. No minimum counts (abstract verified).
- **Fenner, Gasarch, Glover, Purewal, "Rectangle Free Coloring of Grids", [arXiv:1005.3750](https://arxiv.org/abs/1005.3750)** (v1 2010-05; full text verified) — determines **exactly which grids are 3-colorable** (rectangle-free): OBS_3 = {G_19,4, G_16,5, G_13,7, G_11,10, G_10,11, G_7,13, G_5,16, G_4,19}; Lemma 7.2 gives an explicit rectangle-free 3-coloring of G_10,10; Theorem 9.4: bipartite Ramsey number BR(2,3) = 11. **Existence only — no rectangle counts.**
- **Irving, "Bipartite Ramsey numbers and Zarankiewicz numbers"** (Discrete Mathematics, 1979) — b(2,2,2) = 11 (per Radziszowski's dynamic survey DS1): K_10,10 admits a C4-free 3-edge-coloring, K_11,11 does not.
- **Dumitru, Prunescu, [arXiv:2512.23303](https://arxiv.org/abs/2512.23303)** (v1 2025-12-29) — two-color Gallai-type forcing thresholds; no counts, no c ≥ 3.
- **GitHub code search** (2026-11-11): no public minimization solver for c ≥ 3 (nearest hit: a programming-exercise rectangle *counter*).
- cstheory StackExchange question 791 (~2009): 3/4-color obstruction-set discussion, existence only.

**Verdict / delta.** No source computes T_c(k,n) (minimum counts) for any
c ≥ 3. Two kinds of new content below, stated with different strength:

1. **Quantitative lower bounds past the 3-color threshold (new):** the
   exact optimum of a c-ary aggregation relaxation gives
   LB_3(11,11) = 2, LB_3(11,12) = 15, LB_3(12,12) = 18 — the first
   *counting* lower bounds for 3 colors (the literature proves only
   "≥ 1 rectangle is forced" at 11×11, via non-colorability).
2. **Certified exact values in the rectangle-free region (corroboration,
   not new mathematics):** FGGP 2010 already implies T_3 = 0 for every
   grid our instances fit inside (10×10 is 3-colorable). Our contribution
   is machine-checkable certificates: CP-SAT `OPTIMAL` + witness grids
   re-counted by two independent counters.

## Method

1. **Aggregation lower bound** (`tools/relax_lb3.py`): the lab's
   `relax_lb.py` relaxation generalized to c colors, keeping only exact
   identities — mono = Σ_{row pairs} Σ_{colors} C(a^a_ij, 2) with
   a^a_ij = #columns where both rows are color a, and the per-color
   column-count identities Σ_{i<j} a^a_ij = Σ_c C(z_{c,a}, 2); drops only
   realizability → proven CP-SAT optimum is a valid LB. 
   **Validation:** in c=2 mode it reproduces the lab's values
   LB = 1, 6, 21, 40, 74 at (5,5),(6,6),(7,7),(8,8),(9,9) — the middle
   three exactly the OEIS A399620 values (tight), 74 = the lab's a(9) LB.
2. **Exact count model** (`tools/min_mono_rect3.py`): c-ary count model —
   c color-assignment Booleans per cell (one-hot, linked to an IntVar),
   per-row-pair per-color agreement counts, exact linearization
   C(v,2) = Σ_{t≤v}(t−1) over reified thresholds; `--lb` composes the
   aggregation bound into the proof.
   **Symmetry breaking (validity argued in the docstring):** row 0
   color-canonical (colors introduced in increasing order) + row-lex on
   rows 1..m−1. Note: a full row-lex chain *including row 0* is **not**
   jointly valid with color canonicalization (re-sorting after relabeling
   can move a different row into slot 0) — recorded so nobody "fixes" it.
3. **Independent re-count** (`tools/count_rects.py`): column-pair
   decomposition, a fresh code path; every certificate records
   solver objective = embedded corner-counter = column-pair counter.

## Exact values (all CP-SAT OPTIMAL, witnesses re-counted)

| instance | T_3 | status | wall |
|---|---|---|---|
| 3×3, 3×4, 3×5, 3×6, 3×7 | **0** | OPTIMAL | ≤ 0.1 s |
| 4×4 | **0** | OPTIMAL | 0.0 s |
| 4×5 | **0** | OPTIMAL | 0.0 s |
| 5×5 | **0** | OPTIMAL | 0.1 s |
| 10×10 | **0** | OPTIMAL | 94.1 s |

All eight requested instances admit rectangle-free 3-colorings (consistent
with FGGP 2010: everything inside 10×10 is 3-colorable); the 10×10 case is
an independent solver re-derivation of their Lemma 7.2. Certificate
`c3_T3_k10_n10.json`, witness (`0/1/2` = colors):

```
0122012011
0012211102
0202120110
1010222210
1021020121
1120001202
1200112022
2002101221
2111120002
2221201010
```

Smaller witnesses are inside `results/certificates/c3_T3_*.json` (e.g. 4×4:
`0121 / 0002 / 1110 / 2202`; 5×5: `01021 / 02100 / 10010 / 10101 / 21222`).

## Aggregation lower bounds LB_3 (exact optima of the relaxation)

| m×n | LB_3 | status | wall |
|---|---|---|---|
| 3×3, 4×4, 5×5, 6×6, 7×7, 9×9 | 0 | OPTIMAL | ≤ 0.4 s |
| 10×10 | 0 | OPTIMAL | 0.3 s |
| 11×11 | **2** | OPTIMAL | 1.4 s |
| 11×12 (and 12×11 by transpose) | **15** | OPTIMAL | 3.1 s |
| 12×12 | **18** | OPTIMAL | 2.2 s |

Composed brackets (bounds stated as bounds; no UB search past 11×11 was
budgeted except the one run below):

- **T_3(11,11) ≥ 2** — first quantitative lower bound for 3 colors. The
  mechanism, by hand: per color c, Σ_{row pairs} a^c_ij = Σ_{columns}
  C(z_{j,c},2); with 11 cells per column the per-column split is (4,4,3),
  so Σ_c Z_c = 11·15 = 165, but per-color totals are 66−3·n_c with
  Σ n_c = 11 (e.g. 57, 54, 54), while 55 row pairs give only 55 zero-cost
  slots (a^c = 1) per color — the 57 forces two pairs to a^0 = 2, i.e. two
  rectangles. (CP-SAT proves 2 is the exact relaxation optimum.)
- **T_3(11,12) ≥ 15**, **T_3(12,12) ≥ 18** by the same relaxation.
- T_3(11,11) best found coloring: **UB 18** (CP-SAT witness, 120 s,
  status FEASIBLE — not proven optimal; re-counted, see
  `results/certificates/c3_T3_k11_n11_ub.json`),
  so **2 ≤ T_3(11,11) ≤ 18**.
- The relaxation gives 0 for every instance with min(k,n) ≤ 10 — it is
  blind below the threshold (honest negative; the exact model covers that
  regime, where the answer is simply 0).

## Negative results / honest notes

1. **The relaxation is blind below the threshold:** LB_3 = 0 for all
   k,n ≤ 10. For 3 colors there is no "tight at small sizes" story like the
   2-color one (LB 6/21/40 = OEIS at 6/7/8); all information there comes
   from the exact model, and the answers are all 0.
2. **One-sided aggregation is orientation-asymmetric:** LB(11 rows ×
   12 cols) = 15 but LB(12 × 11) = 0. Both are valid (T_3 is
   transpose-invariant); report the max. A joint two-sided model (row-pair
   and column-pair patterns simultaneously) is the obvious strengthening —
   not built in this session.
3. **11×11 not closed:** 2 ≤ T_3(11,11) ≤ 18; the 120 s CP-SAT run proves
   only feasibility of 18 (bound stuck at the composed LB 2). Proving 2 —
   or even matching LB to UB — did not happen in this budget.
4. Values T_3 = 0 are implied by 2010 prior art (existence of rectangle-free
   colorings); claimed here as *certified computations*, not new math.

## Reproduce

```bash
pip install --user --break-system-packages ortools   # 9.15 used
python3 tools/relax_lb3.py --validate                # c=2 battery: 1,6,21,40,74
python3 tools/relax_lb3.py 11 11 --colors 3          # -> lb: 2
python3 tools/relax_lb3.py 12 12 --colors 3          # -> lb: 18
python3 tools/relax_lb3.py 11 12 --colors 3          # -> lb: 15
python3 tools/min_mono_rect3.py 5 5 --colors 3       # -> OPTIMAL 0 + witness
python3 tools/min_mono_rect3.py 10 10 --colors 3 --time-limit 120  # -> OPTIMAL 0 (94 s)
python3 tools/count_rects.py --colors 3 \
    results/certificates/c3_T3_k10_n10.json          # -> rectangles: 0
```
