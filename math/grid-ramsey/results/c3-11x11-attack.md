# Results — 3-color 11×11 attack session: UB 18 → 10, joint relaxation built (negative at 11×11), ladder t=2 UNKNOWN

Session 2026-11-11 (follow-up to F-24, same box, heavily shared: a 12-worker
CP-SAT job owned the machine; all runs below `nice -n 10` with
`num_workers ≤ 2` for CP-SAT and 1 thread per SA process). Definition as in
`results/c3-color-bounds.md`: T_3(k,n) = minimum number of monochromatic
rectangles over all 3-colorings of the k×n grid. **Composed bound moved from
2 ≤ T_3(11,11) ≤ 18 to 2 ≤ T_3(11,11) ≤ 10.** New tools:
`tools/joint_relax.py` (joint two-sided aggregation relaxation — the
strengthening F-24 listed as "not built"), `tools/sat_ladder.py` (exact
model + embedded aggregation + pigeonhole links, satisfaction ladder),
`tools/sa_ub.py` (simulated annealing with exact delta evaluation).

## Headline results

1. **UB: T_3(11,11) ≤ 10** (was 18). Witness found by 20 s of simulated
   annealing from the F-24 18-rectangle witness (`tools/sa_ub.py`, seed 1,
   ~1.5M flips). Count verified by two independent code paths (embedded
   corner counter = 10; `tools/count_rects.py` column-pair = 10):
   `results/certificates/c3_T3_k11_n11_ub10.json`. Witness:

```
20211202011
01202120012
21121220000
00110212202
01012201120
11022012001
22102101201
10221011220
12120000112
20001110122
12010122020
```

2. **Joint two-sided aggregation relaxation built and solved** (`tools/joint_relax.py`):
   keeps the row-pair view AND the column-pair view of the same quantity
   with all cheap exact links (color totals, row/column pigeonhole
   a_ij^c ≥ w_ic + w_jc − n, a_ij^c ≤ min(w_ic, w_jc), and transposes).
   Validation: reproduces F-24's one-sided optima where known —
   LB_joint(11,12) = 15 (= one-sided 15; kills the 15-vs-0 orientation
   asymmetry at the model level), LB_joint(12,12) = 18 (= one-sided 18).
   **At 11×11 the joint model gives OPTIMAL lb = 2 — no improvement over
   the one-sided bound. Honest negative:** the missing ingredient for
   LB ≥ 3 is realizability of the aggregate profiles, not one-sidedness.

3. **LB ladder (exact model, target t):** see run table below.

## Run table (all `nice -n 10`; CP-SAT seed 20261109)

| run | tool | target/limit | outcome | wall |
|---|---|---|---|---|
| joint_relax validation 11×12 | tools/joint_relax.py | 60 s / 2 workers | OPTIMAL lb = 15 (matches F-24 one-sided; asymmetry fixed) | 26.3 s |
| joint_relax validation 12×12 | tools/joint_relax.py | 60 s / 2 workers | OPTIMAL lb = 18 (matches F-24) | 28.2 s |
| joint_relax 11×11 | tools/joint_relax.py | 240 s / 2 workers | **OPTIMAL lb = 2** (no gain over one-sided) | 58.6 s |
| SA seed 1, start = 18-witness | tools/sa_ub.py | 20 s | **best = 10** (verified ×2 counters) → UB 10 | 20.0 s |
| SA seed 11, start = 10-grid | tools/sa_ub.py | 330 s | best = 10 (14.8M steps, 235 restarts; no improvement; recount_full = 10, count_rects = 10) | 330 s |
| SA seed 12, start = 10-grid | tools/sa_ub.py | 330 s | best = 10 (14.2M steps, 231 restarts; no improvement) | 330 s |
| SA seed 21, strong row-kick, start = 10-grid | tools/sa_ub.py | 360 s | best = 10 (9.6M steps, 167 restarts; no improvement) | 360 s |
| ladder t = 2, attempt 1 (11×11) | tools/sat_ladder.py | 420 s / 2 workers | **UNKNOWN** (timeout; no witness, no infeasibility) | 420.1 s |
| ladder t = 2, attempt 2 (11×11, seed 31337) | tools/sat_ladder.py | 330 s / 2 workers | **UNKNOWN** (timeout; no witness, no infeasibility) | 330.1 s |

## Ladder outcome

- **t = 2: UNKNOWN** (attempt 1: 420 s, 2 workers, seed 20261109 — status
  UNKNOWN; attempt 2: 330 s, 2 workers, seed 31337 — status UNKNOWN; two
  independent search trajectories, neither SAT nor INFEASIBLE within
  budget).  So **LB ≥ 3 was NOT established**; the
  composed bound stays 2 ≤ T_3(11,11) ≤ 10.  The strengthened encoding
  (aggregation identity + pigeonhole links embedded in the exact model)
  ran but did not close the gap on a box shared with a 12-worker job.
  Honest per-run record, no claim made either direction from these runs.

## Notes / honest negatives

1. Joint relaxation does not move LB(11,11) past 2 — the two-sided model
   with pigeonhole links is strictly stronger than one-sided (it fixes the
   11×12/12×11 asymmetry: both orientations now give 15-class bounds), but
   at the square threshold instance its optimum is still 2. Any LB ≥ 3
   proof needs the exact model (realizability), not more aggregation.
2. LB ≥ 3 via CP-SAT exact model not achieved within this session's budget
   (see ladder outcome; two seeds, 2 workers on a box shared with a
   12-worker job — both runs UNKNOWN).
3. UB 10 not proven optimal; no claim is made about T_3(11,11) below 10.
   Three further independent SA runs from the 10-grid (seeds 11/12, plus
   a strong row-kick variant seed 21; ~39M flips total, 230+ reheat
   restarts combined) could not beat 10 — 10 sits in a deep
   local-optimum basin for this neighborhood; no claim about the true
   optimum either way.

## Reproduce

```bash
python3 tools/joint_relax.py 11 12 --colors 3      # -> lb: 15 (validates vs F-24)
python3 tools/joint_relax.py 12 12 --colors 3      # -> lb: 18 (validates vs F-24)
python3 tools/joint_relax.py 11 11 --colors 3      # -> lb: 2 (honest negative)
python3 tools/sa_ub.py 11 11 --colors 3 --start W18 --seconds 20 --seed 1   # -> best: 10
python3 tools/count_rects.py --colors 3 W10        # -> rectangles: 10 (W10 = the witness above)
python3 tools/sat_ladder.py 11 11 --colors 3 --target 2 --time-limit 420 --workers 2
```
