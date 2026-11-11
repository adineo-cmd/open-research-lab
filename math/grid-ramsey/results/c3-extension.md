# Results — 3-color extension past the 11×11 frontier: **T_3(13,7) = 2 exact (new value)**, frontier lower bounds 36/36/52, first UB witnesses at 12×12 / 12×13 / 13×13

Session 2026-11-12 (follow-up to F-24 `results/c3-color-bounds.md` and F-27
`results/c3-11x11-attack.md`, same box, heavily shared: a 12-worker CP-SAT
job owned the machine; all runs `nice -n 10`, CP-SAT `num_workers = 2`,
per-solve limit ≤ 120 s, 1 thread per SA process). Definition as before:
T_3(k,n) = minimum number of monochromatic rectangles over all 3-colorings
of the k×n grid. Tools used unmodified: `tools/joint_relax.py` (F-27 joint
two-sided aggregation relaxation), `tools/sa_ub.py` (F-27 simulated
annealing; handles non-square m×n grids as-is), `tools/min_mono_rect3.py`
(exact count model), `tools/count_rects.py` (independent column-pair
counter). Certificates in `results/certificates/c3_*.json` (new ones listed
at the bottom).

## Headline results

1. **T_3(13,7) = 2, EXACT — new value.** Lower bound: the joint two-sided
   relaxation has proven optimum **2** at 13×7 (CP-SAT OPTIMAL, 14.9 s) —
   valid because every real coloring is a feasible point of that
   relaxation. Upper bound: simulated annealing found a 2-rectangle
   witness (45 s, seed 11), re-counted to 2 by the independent
   column-pair counter. LB = UB = 2. Prior art gives only existence-level
   information here: FGGP 2010 Theorem 6.1 proves G_13,7 is **not**
   3-colorable, i.e. T_3(13,7) ≥ 1 — the exact value 2 is new, and per the
   F-24 audit no c ≥ 3 minimum counts exist anywhere in the literature.
   Witness (0/1/2 = colors, 2 rectangles):

```
1221002
0212011
2121020
0102121
1002201
0021211
2211200
1022110
0211120
1100220
0110202
1010022
2102012
```

2. **T_3(12,7) = 0 certified.** SA found a rectangle-free 12×7 coloring in
   **0.4 s** (seed 12); `tools/count_rects.py` confirms 0; the joint
   relaxation's proven optimum is 0, as it must be. This *independently
   reproduces* FGGP Theorem 6.5 (G_12,7 is 3-colorable). Witness:

```
1220201
1002112
2010210
2212100
2021011
1011222
0120012
1122020
2101002
0012201
2100121
0201120
```

3. **Frontier lower-bound sweep (all CP-SAT OPTIMAL — exact relaxation
   optima, hence valid LBs on T_3):**

| m×n | LB_3 (joint, OPTIMAL) | wall | note |
|---|---|---|---|
| 12×12 | **18** | 10.7 s | revalidates F-24's one-sided 18 |
| 12×13 | **36** | 21.2 s | new |
| 13×12 | **36** | 17.9 s | new; equals transposed orientation (joint model kills the F-24 asymmetry at these sizes too) |
| 13×13 | **52** | 24.6 s | new |

4. **First upper-bound witnesses past 11×11** (`tools/sa_ub.py`, all
   counts verified by two independent code paths):

| m×n | UB (SA witness) | bracket |
|---|---|---|
| 12×12 | **23** | **18 ≤ T_3(12,12) ≤ 23** |
| 12×13 | **40** | **36 ≤ T_3(12,13) ≤ 40** |
| 13×12 | **40** (transpose of the 12×13 witness, re-counted) | **36 ≤ T_3(13,12) ≤ 40** |
| 13×13 | **54** | **52 ≤ T_3(13,13) ≤ 54** |
| 12×7 | 0 | **T_3(12,7) = 0 exact** |
| 13×7 | 2 | **T_3(13,7) = 2 exact** |

## Prior-art correction (self-check caught it — important)

The session brief stated that FGGP's OBS_3 = {G_19,4, G_16,5, G_13,7,
G_11,10, G_10,11, G_7,13, G_5,16, G_4,19} is the set of 3-colorable
(rectangle-free) grids, making (13,7) rect-free. **The full text of
arXiv:1005.3750 (verified 2026-11-12 via ar5iv) says the opposite:**
Definition 1.4 defines OBS_c as the set of grids that are *not* c-colorable
but all properly contained grids are (the minimal **obstructions**), and
Theorem 6.5 states OBS_3 = that set; Theorem 6.1 explicitly lists G_19,4,
G_16,5, G_13,7, G_12,10, G_11,11 (and transposes) as **not** 3-colorable,
while G_18,4, G_15,6, G_12,9 (and transposes) and G_10,10 (Thm 6.2) **are**.

The solver caught the inversion on its own: an OPTIMAL lb = 2 at (13,7) is
*impossible* if a rectangle-free coloring existed, because every real
coloring induces a feasible point with objective 0 in the relaxation.
Discriminator runs at the FGGP boundary sizes, all OPTIMAL:

| grid | FGGP status (true) | LB_joint | consistent? |
|---|---|---|---|
| 10×10 | 3-colorable (Thm 6.2, F-24 certified 0) | 0 | yes |
| 12×7 | 3-colorable (Thm 6.5 proof item 3) | 0 | yes (and witness found) |
| 13×7 | NOT 3-colorable (Thm 6.1) | **2** | yes — quantifies it |
| 16×5 | NOT 3-colorable (Thm 6.1) | **2** | yes (T_3(16,5) ≥ 2) |
| 19×4 | NOT 3-colorable (Thm 6.1) | **1** | yes (T_3(19,4) ≥ 1) |
| 11×10 | NOT 3-colorable (Thm 6.4) | 0 | blind — honest negative, see below |

So the (k,7) row splits exactly where FGGP says it should: T_3(12,7) = 0
(rect-free exists) and T_3(13,7) = 2 (forced).

## Run table (all `nice -n 10`; CP-SAT seed 20261109, 2 workers; SA 1 thread)

| run | tool | limit | outcome | wall |
|---|---|---|---|---|
| joint 12×7 (self-check) | tools/joint_relax.py | 60 s | OPTIMAL lb = 0 | 5.4 s |
| joint 13×7 | tools/joint_relax.py | 60 s | **OPTIMAL lb = 2** | 14.9 s |
| exact 12×7 | tools/min_mono_rect3.py | 120 s | **FEASIBLE obj = 1, bound = 0** (timeout — did not find the rect-free coloring; see honest negatives) | 120.1 s |
| exact 13×7 | tools/min_mono_rect3.py | 120 s | **FEASIBLE obj = 5, bound = 0** (timeout) | 120.1 s |
| joint 12×12 (validation) | tools/joint_relax.py | 120 s | OPTIMAL lb = 18 (= F-24) | 10.7 s |
| joint 12×13 | tools/joint_relax.py | 120 s | **OPTIMAL lb = 36** | 21.2 s |
| joint 13×12 | tools/joint_relax.py | 120 s | **OPTIMAL lb = 36** | 17.9 s |
| joint 13×13 | tools/joint_relax.py | 120 s | **OPTIMAL lb = 52** | 24.6 s |
| SA 12×12 seed 1 (rows) | tools/sa_ub.py | 45 s | best = 23 (1.13M steps) | 45.0 s |
| SA 12×13 seed 2 (cells) | tools/sa_ub.py | 45 s | best = 40 (0.90M steps) | 45.0 s |
| SA 13×13 seed 3 (rows) | tools/sa_ub.py | 60 s | best = 55 (1.42M steps) | 60.0 s |
| SA 13×7 seed 11 (rows) | tools/sa_ub.py | 45 s | **best = 2** (1.85M steps) → exact value 2 | 45.0 s |
| SA 12×7 seed 12 (rows) | tools/sa_ub.py | 30 s | **best = 0** (88K steps) in 0.4 s → exact value 0 | 0.4 s |
| SA 12×12 seed 13 (cells) | tools/sa_ub.py | 60 s | best = 23 (no improvement; 1.42M steps) | 60.0 s |
| SA 13×13 seed 14 (rows) | tools/sa_ub.py | 60 s | **best = 54** (improved 55 → 54; 1.53M steps) | 60.0 s |
| joint 10×10 (discriminator) | tools/joint_relax.py | 90 s | OPTIMAL lb = 0 | 9.4 s |
| joint 11×10 (discriminator) | tools/joint_relax.py | 90 s | OPTIMAL lb = 0 (blind; see honest negatives) | 4.0 s |
| joint 16×5 (discriminator) | tools/joint_relax.py | 90 s | OPTIMAL lb = 2 | 3.2 s |
| joint 19×4 (discriminator) | tools/joint_relax.py | 90 s | OPTIMAL lb = 1 | 6.3 s |

Every UB witness re-counted by both the SA-embedded column-pair counter and
`tools/count_rects.py` (fresh code path); final pass re-extracted each
`witness_grid` from its certificate JSON and re-counted: 0/2/23/40/40/54 all
match.

## Honest negatives

1. **Exact count model timeouts at the (k,7) row:** `min_mono_rect3.py` at
   12×7 hit FEASIBLE obj = 1 / bound = 0 in 120 s and at 13×7 FEASIBLE
   obj = 5 / bound = 0 in 120 s (2 workers each) — it neither proved
   optimality nor even found witnesses that SA found in 0.4 s / 45 s. The
   row-lex symmetry breaking (13-row lex chain) appears to hurt witness
   *search* here; the exact values above are certified by LB/UB
   composition instead (joint-relaxation optimum + verified witness).
2. **Relaxation blind at 11×10:** LB_joint(11,10) = 0 although FGGP Thm 6.4
   proves G_11,10 is not 3-colorable (via maxrf(11,10) ≤ 36 counting). The
   joint two-sided model still cannot see this instance; quantitative
   counting at (11,10) needs the exact model. Related discriminators
   (16,5) → 2 and (19,4) → 1 show the blindness is instance-specific, not
   systematic.
3. **No bracket closed on the big squares:** 12×12 SA stuck at 23 across
   two seeds/kicks (45 s + 60 s, ~2.5M steps total); 13×13 improved
   55 → 54 across seeds but stayed above LB 52. 12×13 / 13×12 single runs
   (40 vs LB 36). All upper bounds are feasibility witnesses, not optima.
4. **11×11 untouched this session:** the composed bound stays
   2 ≤ T_3(11,11) ≤ 10 (F-27); budget went to the frontier sweep.
5. Per F-24 note 1, the relaxation gives 0 at every grid with
   min(k,n) ≤ 10; nothing new there (exact model covers that regime and
   the answers are 0).

## Certificates (new, this session)

- `results/certificates/c3_lbjoint_frontier.json` — all 10 joint-relaxation
  runs (6 frontier + 4 discriminators) with claims, walls, roles.
- `results/certificates/c3_T3_k13_n7_exact2.json` — **T_3(13,7) = 2** exact:
  LB provenance + witness + double recount.
- `results/certificates/c3_T3_k12_n7.json` — **T_3(12,7) = 0** exact: witness
  + consistency + FGGP cross-reference.
- `results/certificates/c3_T3_k12_n12_ub23.json` — UB 23 witness.
- `results/certificates/c3_T3_k12_n13_ub40.json` — UB 40 witness (12×13).
- `results/certificates/c3_T3_k13_n12_ub40.json` — transposed witness (13×12).
- `results/certificates/c3_T3_k13_n13_ub54.json` — UB 54 witness
  (trajectory 55 → 54 recorded inside).

## Reproduce

```bash
python3 tools/joint_relax.py 12 7 --colors 3 --time-limit 60 --workers 2   # -> lb: 0 (self-check vs FGGP)
python3 tools/joint_relax.py 13 7 --colors 3 --time-limit 60 --workers 2   # -> lb: 2
python3 tools/joint_relax.py 12 13 --colors 3 --time-limit 120 --workers 2 # -> lb: 36
python3 tools/joint_relax.py 13 12 --colors 3 --time-limit 120 --workers 2 # -> lb: 36
python3 tools/joint_relax.py 13 13 --colors 3 --time-limit 120 --workers 2 # -> lb: 52
python3 tools/joint_relax.py 12 12 --colors 3 --time-limit 120 --workers 2 # -> lb: 18 (revalidates F-24)
python3 tools/sa_ub.py 13 7 --colors 3 --seconds 45 --seed 11 --kick rows  # -> best: 2
python3 tools/sa_ub.py 12 7 --colors 3 --seconds 30 --seed 12 --kick rows  # -> best: 0 (0.4 s)
python3 tools/sa_ub.py 12 12 --colors 3 --seconds 45 --seed 1 --kick rows  # -> best: 23
python3 tools/sa_ub.py 12 13 --colors 3 --seconds 45 --seed 2 --kick cells # -> best: 40
python3 tools/sa_ub.py 13 13 --colors 3 --seconds 60 --seed 14 --kick rows # -> best: 54
python3 tools/count_rects.py --colors 3 results/certificates/c3_T3_k13_n7_exact2.json  # -> rectangles: 2
python3 tools/count_rects.py --colors 3 results/certificates/c3_T3_k12_n7.json         # -> rectangles: 0
```

Environment: ortools CP-SAT 9.15.6755; FGGP full text verified at
https://ar5iv.labs.arxiv.org/html/1005.3750 (Def 1.4, Thm 1.5, Thm 6.1,
Thm 6.2, Thm 6.4, Thm 6.5) on 2026-11-12.
