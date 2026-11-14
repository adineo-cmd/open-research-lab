# Results — frontier LB sweep at 11×12…14×14, T₃(12,13) = T₃(13,12) = 36 EXACT, T₃(13,13) = 52 EXACT, 12×12 UB 23→22

Session 2026-11-15 (follow-up to F-24 `results/c3-color-bounds.md`, F-27
`results/c3-11x11-attack.md`, and session 2026-11-12
`results/c3-extension.md`). Definition as before: T_c(k,n) = minimum number
of monochromatic rectangles over all c-colorings of the k×n grid. Tools used
unmodified: `tools/joint_relax.py` (F-27 joint two-sided aggregation
relaxation), `tools/sa_ub.py` (F-27 simulated annealing),
`tools/count_rects.py` (independent column-pair counter).

Environment: this box, no competing load; CP-SAT 4 workers (ortools
9.9.3963 — note: the 2026-11-12 sessions used 9.15.6755; all revalidations
reproduced the committed optima exactly); SA 1 thread per run.

Baseline reproduction before extending (all exact): committed witnesses
re-counted 2/0/23/40/40/54 via `tools/count_rects.py`; joint re-solves
OPTIMAL — 12×12 = 18 (3.07 s), 13×13 = 52 (5.48 s), 12×13 = 36 (6.57 s),
all matching the committed values.

## Headline results

1. **Eleven new joint-relaxation lower bounds (all CP-SAT OPTIMAL, all
   orientation-symmetric):**

| k×n | LB₃ (joint, OPTIMAL) | wall (4 workers) |
|---|---|---|
| 11×12 / 12×11 | **15** | 3.4 / 2.6 s |
| 11×13 / 13×11 | **30** | 2.1 / 3.8 s |
| 11×14 / 14×11 | **45** | 3.8 / 4.3 s |
| 12×14 / 14×12 | **54** | 5.3 / 4.0 s |
| 13×14 / 14×13 | **74** | 7.2 / 8.6 s |
| 14×14 | **91** | 8.4 s |

   Structural note: the 11×n row runs 15/30/45 — arithmetic +15 per added
   column for n = 12, 13, 14. The joint model kills the F-24 one-sided
   orientation asymmetry at every new size (one-sided LB(12,11) = 0 →
   joint 15). 14×14 is the largest grid measured in the lab to date.
   Validity: every real coloring induces a feasible relaxation point whose
   objective equals its true rectangle count, so each proven optimum is a
   valid lower bound on T₃.

2. **T₃(12,13) = 36 EXACT and T₃(13,12) = 36 EXACT — new exact values, the
   first exact c ≥ 3 counts beyond the (k,7) row.** LB: proven
   joint-relaxation optimum 36 at both orientations (session 2026-11-12,
   `c3_lbjoint_frontier.json`; re-solved OPTIMAL this session). UB: SA
   witness with 36 rectangles (seed 24, 240 s, cells kick, random start),
   re-counted by `tools/count_rects.py` and a session-written naive quad
   scan (both 36); the 13×12 witness is the transpose, re-counted
   independently. Trajectory at 12×13: committed witness 40 → seed-23
   restart 37 → seed-24 36 = LB. Certificates:
   `c3_T3_k12_n13_exact36.json`, `c3_T3_k13_n12_exact36.json`.

3. **T₃(13,13) = 52 EXACT — new exact value; the largest c=3 bracket is
   CLOSED** (52 ≤ T₃(13,13) ≤ 54 from the 2026-11-12 session). LB: proven
   joint-relaxation optimum 52. UB: SA witness with 52 rectangles (seed
   25, 300 s, rows kick, restarted from the committed 54-witness),
   double-recounted; an independent second run (seed 26, random start,
   cells kick) also reached 52 — two distinct witnesses. Trajectory:
   55 → 54 (2026-11-12) → 52 (this session). Witness (0/1/2 = colors):

```
2011100211220
0111210220012
2100102122012
1010222010212
1201202100120
0210121222100
0002011112222
2220010101112
2122002210101
1202110020201
0021201002211
1122021021020
2012220101001
```

   Certificates: `c3_T3_k13_n13_exact52.json` (canonical, seed 25),
   `c3_T3_k13_n13_ub52_seed26.json` (second witness).

4. **T₃(12,12) UB improved 23 → 22** — two independent SA runs (seed 21
   from the committed 23-witness with row kicks; seed 22, random start,
   cell kicks; 240 s each) both reached 22, double-recounted. Composed
   bracket: **18 ≤ T₃(12,12) ≤ 22**. Certificates:
   `c3_T3_k12_n12_ub22_seed21.json`, `c3_T3_k12_n12_ub22_seed22.json`.

## Current c=3 state of knowledge (all lab-internal; nothing published anywhere per the F-24 audit + 2026-11-15 web check)

| grid | bound | status |
|---|---|---|
| T₃(12,7) | 0 | exact |
| T₃(13,7) | 2 | exact |
| T₃(12,13) = T₃(13,12) | **36** | **exact (new)** |
| T₃(13,13) | **52** | **exact (new)** |
| T₃(12,12) | 18 ≤ T ≤ 22 | bracket (was 18..23) |
| T₃(11,11) | 2 ≤ T ≤ 10 | untouched this session (D-1 open) |
| 11×12…14×14 | 15/30/45/54/74/91 | LB only (no witnesses yet — UB next session) |

## Honest negatives

1. No exact count-model runs (`min_mono_rect3.py`) this session — all
   exactness came from LB/UB composition; the 2026-11-12 session showed
   the exact model times out at these sizes anyway.
2. The 11×n LB row's +15/column arithmetic pattern is unexplained — it
   may reflect a product structure worth investigating (it holds at
   n = 12, 13, 14 exactly).
3. The new LBs have no matching UB witnesses yet (except via the exact
   12×13/13×13 values at neighboring sizes); 11×12 SA runs are queued for
   the next session.
4. 11×11 remains blind to the joint relaxation (LB 2, F-27); D-1 open.

## Certificates (new this session, all dated 2026-11-15)

- `c3_lbjoint_frontier2.json` — all 11 new LB runs with claims/walls/roles.
- `c3_T3_k12_n13_exact36.json`, `c3_T3_k13_n12_exact36.json` — exact 36.
- `c3_T3_k13_n13_exact52.json` (canonical), `c3_T3_k13_n13_ub52_seed26.json`
  (second independent witness).
- `c3_T3_k12_n12_ub22_seed21.json`, `c3_T3_k12_n12_ub22_seed22.json`.
- Trajectory keepers: `c3_T3_k12_n13_ub37_seed23.json`,
  `c3_T3_k13_n12_ub37_seed23T.json`, `c3_T3_k12_n13_ub36_seed24.json`.

Every witness certificate reports `count_rects.py` CLI + session-written
naive quad-scan recounts (both match); the SA-embedded counter output was
not captured this session (stdout truncation in the run wrapper) and is
not claimed anywhere.

## Reproduce

```bash
python3 tools/joint_relax.py 11 12 --colors 3 --time-limit 180 --workers 4   # -> lb: 15 (and 12 11 / 11 13 / ... -> 30/45/54/74/91)
python3 tools/joint_relax.py 12 12 --colors 3 --time-limit 120 --workers 4   # -> lb: 18 (revalidation)
python3 tools/joint_relax.py 12 13 --colors 3 --time-limit 120 --workers 4   # -> lb: 36 (revalidation)
python3 tools/joint_relax.py 13 13 --colors 3 --time-limit 120 --workers 4   # -> lb: 52 (revalidation)
python3 tools/sa_ub.py 12 13 --colors 3 --seconds 240 --seed 24 --kick cells # -> best: 36
python3 tools/sa_ub.py 13 13 --colors 3 --seconds 300 --seed 25 --kick rows --start <committed 54-witness> # -> best: 52
python3 tools/count_rects.py --colors 3 results/certificates/c3_T3_k13_n13_exact52.json  # -> rectangles: 52
python3 tools/count_rects.py --colors 3 results/certificates/c3_T3_k12_n13_exact36.json  # -> rectangles: 36
```

Prior art (Rule 0, 2026-11-15): web search for c≥3 minimum-count results —
FGGP (arXiv:1005.3750) is existence-only; Cooper et al. counting is
2-color; Apon's thesis (arXiv:1205.3813) bounds colorability complexity;
Liu 2021 shift patterns are constructions. No published T₃ minimum counts;
all values above are new.
