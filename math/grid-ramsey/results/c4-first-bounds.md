# Results — first quantitative 4-color grid Ramsey bounds and the first four exact T₄ values: T₄(41,5)=1, T₄(31,6)=2, T₄(29,7)=3, T₄(25,9)=6 EXACT; T₄(23,10) ∈ [4,5]

Session 2026-11-15 (ROADMAP D-3 started; complement to `results/c3-frontier2.md`,
same session and box). Definition: T_c(k,n) = minimum number of
monochromatic rectangles over all c-colorings of the k×n grid. Tools used
unmodified: `tools/joint_relax.py --colors 4`, `tools/sa_ub.py --colors 4`,
`tools/count_rects.py --colors 4`. CP-SAT 4 workers (ortools 9.9.3963);
SA 1 thread per run, 120 s each.

## Prior-art anchor (Rule 0, verified from the FGGP full text via ar5iv on 2026-11-15)

FGGP (arXiv:1005.3750) is existence-only for c = 4: Theorem 7.7 gives
OBS₄ = {G₄₁,₅, G₃₁,₆, G₂₉,₇, G₂₅,₉, G₂₃,₁₀, G₂₂,₁₁, G₂₁,₁₃, G₁₉,₁₇} ∪
transposes (minimal NOT-4-colorable grids); Theorem 7.1/7.2 prove those
grids not 4-colorable via counting. 4-colorable positives per Thms
7.3–7.6: G₂₄,₉, G₂₁,₁₂, G₂₂,₁₀, G₁₈,₁₈, G₁₇,₁₇ (the solved $289 challenge,
Steinbach–Posthoff 2012). **No minimum-count value for any c ≥ 3 exists in
the literature** (F-24 audit 2026-11-11; web search repeated 2026-11-15 —
the only c=4-count statement found is a Gasarch-blog comment claiming "4
monochromatic rectangles is a hard-limit minimum for 17×17 4-colorings",
which is refuted by the existence of a rectangle-free 4-coloring of
G₁₇,₁₇: T₄(17,17) = 0). Everything below is therefore first-in-literature.

## Headline results

1. **Four exact values — the first exact 4-color grid Ramsey minima:**

| grid | LB (proven relaxation optimum) | UB (SA witness, double-recounted) | value |
|---|---|---|---|
| 41×5 | 1 (24.0 s) | 1 (seed 41, 120 s, rows) | **T₄(41,5) = 1 EXACT** |
| 31×6 | 2 (28.0 s) | 2 (seed 42) | **T₄(31,6) = 2 EXACT** |
| 29×7 | 3 (28.8 s) | 3 (seed 43) | **T₄(29,7) = 3 EXACT** |
| 25×9 | 6 (22.4 s) | 6 (seed 44) | **T₄(25,9) = 6 EXACT** |

   Every real coloring induces a feasible point of the joint two-sided
   relaxation whose objective equals its true rectangle count, so each
   proven optimum is a valid lower bound; each SA witness was re-counted
   by `tools/count_rects.py` and a session-written naive quad scan (both
   match the SA value; no SA-embedded counter is claimed). Certificates:
   `c4_T4_k41_n5_exact1.json`, `c4_T4_k31_n6_exact2.json`,
   `c4_T4_k29_n7_exact3.json`, `c4_T4_k25_n9_exact6.json`.

2. **T₄(23,10) ∈ [4, 5]** — LB 4 (OPTIMAL, 21.0 s) + SA witness 5
   (seed 45; bracket certificate `c4_T4_k23_n10_ub5_seed45.json`). All
   five LBs are orientation-symmetric (the transposed runs give identical
   optima: `c4_lbjoint_boundary.json` carries all 17 runs).

3. **Non-monotonicity worth noting:** the bound at 25×9 (6) exceeds the
   bound at 23×10 (4) — the count is not monotone in either dimension
   across different aspect ratios at the OBS₄ boundary.

## Self-checks (the model must agree with FGGP before it can be trusted)

| grid | FGGP status | joint LB (c=4) | consistent? |
|---|---|---|---|
| 18×18 | 4-colorable (Thm 7.6) | 0 OPTIMAL | yes |
| 21×12 | 4-colorable (Thm 7.4) | 0 OPTIMAL | yes |
| 22×10 | 4-colorable (Thm 7.5) | 0 OPTIMAL | yes |

## Honest negatives

1. **Relaxation blindness at 19×17 / 17×19:** proven-OPTIMAL LB = 0
   although FGGP Thm 7.2 proves G₁₉,₁₇ not 4-colorable. The joint
   two-sided model cannot see this instance — exactly parallel to the c=3
   blindness at 11×10 (F-27). Blindness is instance-specific, not
   systematic (the (·,5)–(·,9) rows are all visible).
2. **Timeouts at 22×11 / 11×22:** 180 s solve limit hit at FEASIBLE with
   proven bound 0 (objective 2 feasible point found) — no LB claimable
   even though FGGP Thm 7.1 places G₂₂,₁₁ in OBS₄. Longer budgets or a
   tighter model (D-1's open lever) are needed.
3. No exact count-model runs at c=4 (the c=3 exact model already times
   out at comparable sizes; the LB/UB composition is the working method).
4. The SA witnesses at the exact sizes were found in ≤ 120 s each, but
   their optimality is established only by the LB composition — the exact
   model has not independently certified any of them.

## Certificates (new this session, dated 2026-11-15)

- `c4_lbjoint_boundary.json` — all 17 joint-relaxation runs (self-checks,
  new LBs, blind spots, timeouts) with roles and walls.
- `c4_T4_k41_n5_exact1.json`, `c4_T4_k31_n6_exact2.json`,
  `c4_T4_k29_n7_exact3.json`, `c4_T4_k25_n9_exact6.json` — exact values.
- `c4_T4_k23_n10_ub5_seed45.json` — the 4..5 bracket.

## Reproduce

```bash
python3 tools/joint_relax.py 41 5 --colors 4 --time-limit 180 --workers 4   # -> lb: 1 (also 31 6 -> 2, 29 7 -> 3, 25 9 -> 6, 23 10 -> 4)
python3 tools/joint_relax.py 18 18 --colors 4 --time-limit 180 --workers 4  # -> lb: 0 (self-check)
python3 tools/sa_ub.py 41 5 --colors 4 --seconds 120 --seed 41 --kick rows  # -> best: 1
python3 tools/sa_ub.py 25 9 --colors 4 --seconds 120 --seed 44 --kick rows  # -> best: 6
python3 tools/count_rects.py --colors 4 results/certificates/c4_T4_k41_n5_exact1.json  # -> rectangles: 1
python3 tools/count_rects.py --colors 4 results/certificates/c4_T4_k25_n9_exact6.json  # -> rectangles: 6
```

Next steps: UB witnesses at the new c=3 LB sizes (11×12…14×14); 23×10
exactness attack (needs a 4-witness); longer budgets at 22×11; the D-1
model improvement that would break the 19×17/11×10 blindness.
