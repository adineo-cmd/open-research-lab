# Results — Erdős problem #614: exact small-(n,k) tables for f(n,k) (sparse induced subgraphs)

Session 2026-11-15. Target picked from [erdosproblems.com](https://www.erdosproblems.com/614)
(open, formalized at google-deepmind/formal-conjectures `ErdosProblems/614.lean`):

> Let f(n,k) be minimal such that there is a graph with n vertices and f(n,k)
> edges where every set of k+2 vertices induces a subgraph with maximum
> degree at least k. Determine f(n,k).  [FRS97]

Model: exact CP-SAT (edge variables; per (k+2)-subset an indicator per
vertex with reified induced-degree ≥ k, disjunction ≥ 1; minimize edges).
Status OPTIMAL = exact value + witness graph; FEASIBLE = upper bound with
the proven solver bound recorded.

## Validation (before trusting any new value)

f(n,1) has a closed form: every 3-set must contain an edge ⟺ complement
triangle-free ⟺ f(n,1) = C(n,2) − ⌊n²/4⌋. The model reproduces it exactly
at n = 4..12 (9/9 OK: 2, 4, 6, 9, 12, 16, 20, 25, 30) — certificates
`results/certificates/fnk_n{4..12}_k1.json`, all OPTIMAL and independently
verified. (Earlier revisions of this doc claimed 7/7 at n = 4,5,6,7,8,10,12
but no k=1 certificates had actually been stored; the gap is closed as of
2026-11-19 — see the Rule-1 fixes section.)

## Exact values (CP-SAT OPTIMAL + witness graphs)

| k | exact values (n : f(n,k)) |
|---|---|
| 1 | closed form C(n,2) − ⌊n²/4⌋ (validated n=4..12) |
| 2 | 4:2, 5:4, 6:8, 7:12, 8:17, 9:23, **10:29, 11:37** (2026-11-19; prior art — see below) |
| 3 | 5:3, 6:7, 7:11, 8:15, 9:22, **10:29** (2026-11-19 NEW) |
| 4 | 6:4, 7:9, 8:15, 9:21, **10:28** (2026-11-19 NEW) |

Bounds beyond (FEASIBLE, proven lower bound = solver's BestObjectiveBound;
these are the ORIGINAL 2026-11-15 runs, superseded by the symmetry-broken
extension below): k=2: n=10 [≥26], n=12 [≥34]; k=3: n=10 [≥23], n=11 [≥28],
n=12 [≥31]; k=4: n=10 [≥21], n=11 [≥24], n=12 [≥28] — see the certificate
JSONs for the per-run bound fields.

Notable small witnesses: f(5,3)=3 (a 3-star covers the single 5-set);
f(6,3)=7 = K₄-minus-one-vertex centered structure (certificate has the
exact graph).

## Rule 0 (prior art, 2026-11-15)

1. The problem page (erdosproblems.com/614): open; one user comment;
   no values posted; formalized in Lean (`[category research open]`).
2. OEIS searches for the computed k=2 terms (2,4,8,12,17,23): no
   graph-theoretic sequence — numeric overlaps (A393683 midsequence,
   A152125 grid dominos) are unrelated formulas, coincidences at small n.
3. [FRS97] = Faudree–Rousseau–Schelp, "Problems in graph theory from
   Memphis" — the source; per the problem page no exact small-n tables
   are posted anywhere. Delta claimed: first exact tables + witness graphs
   at small (n,k).

> **⚠️ Superseded 2026-11-19:** point 3 was mistaken — a Jan-2026 forum
> comment links a public Turán reduction that determines the k=2 values.
> See the prior-art correction section below before relying on this claim.

## Honest negatives

1. Optimality proofs harden fast: k=2 n=9 took 147 s; n=10 hit the 240 s
   cap at FEASIBLE. The exact frontier this session is n=9 (k=2,3).
2. A sweep-runner defect (ortools API name `BestObjectiveValueBound` vs
   9.9's `BestObjectiveBound`) silently killed the first sweep's n=10..14
   runs — fixed mid-session (scripts/fnk_solve.py); certificates
   re-run for n=10..12 k=2 and the k=3/k=4 legs. Remaining sweep tail
   (n≥13 k=2; k=4 beyond small n) is queued for the next session.
3. No asymptotic claims — FRS97's general determination is untouched;
   this session contributes exact small-n data + reproducible model.

## Extension + corrections (2026-11-19)

A follow-up session attacked the queued "exact-table extension" item with a
stronger model, an adversarial prior-art re-audit, and an independent verifier.
Full log: `results/ep614-compute-2026-11-19.md`; audit:
`results/ep614-prior-art-2026-11-19.md`.

### New tool: symmetry-broken solver

`scripts/fnk_solve_sym.py` adds the following levers to the 2026-11-15 model:

1. **Degree-order symmetry breaking** — the property is relabelling-invariant,
   so we may impose `deg(0) ≥ deg(1) ≥ … ≥ deg(n−1)`. This alone takes
   n=10,k=2 from a 240 s FEASIBLE timeout to OPTIMAL in ~13 s.
2. **FEASIBLE witnesses are now saved** (the old script dropped them), so a
   bound run yields a usable graph and can seed a later hint.
3. A `--mode prove` decision form (`sum(e) ≤ ub−1`, INFEASIBLE ⇒ lower bound).

**Validation before use:** reproduces all seven prior exact values and the
k=1 closed form at n=4..12 (9/9). For k=2, the new OPTIMAL values at n=10
(29) and n=11 (37) independently match the published Turán oracle below.
No new value was trusted without this gauntlet.

### New exact values (OPTIMAL + witness, independently verified)

| n | k | f(n,k) | status | wall_s | certificate |
|---|---|---|---|---|---|
| 10 | 3 | **29** | OPTIMAL | 38.19 | `fnk_n10_k3_s2.json` |
| 10 | 4 | **28** | OPTIMAL | 111.04 | `fnk_n10_k4_s2.json` |

Also landed as OPTIMAL (independent confirmation only — see prior-art
correction): f(10,2)=29 (13.1 s), f(11,2)=37 (213.65 s).
k=1 closed-form certificates now exist for n=4..12 (all OPTIMAL, 0.01–0.19 s).

An **independent Turán-oracle validation** (a structurally different CP-SAT
model built from the published Cor. 4.6: maximize complement edges avoiding
{C5, K2,3, bowtie} as subgraphs) re-derived f(10,3)=29 from scratch, reproduced
all five known small values 5/5, and tightened the unresolved n=11 k=3 cell to
**36 ≤ f(11,3) ≤ 37** (counting bound 36, witness 37). See
`results/ep614-turan-oracle-2026-11-19.md`. This is validation only — no
novelty claim.

All new witnesses PASS `scripts/verify_fnk.py` (full C(n,k+2) enumeration,
stdlib only). Honest negative: **n=11, k=3 and k=4 stayed FEASIBLE** at
600 s and 900 s (best lower bounds 27–28 and 25) — no value claimed there.
A third lever was also tried and did **not** break n=11,k=3: adding all valid
induced-subset cuts `e(T) ≥ f(|T|,k)` for every m-subset T (a counting argument
gives f(11,3) ≥ ⌈11·f(10,3)/9⌉ = 36, far above the solver's own bounds of 27–28),
plus a decision-form run `sum(e) ≤ 36`; both returned UNKNOWN at 300–540 s.
The bound family is recorded here as the next session's starting point, not
as a proof.

### ⚠️ Prior-art correction (Rule 0) — k=2 is NOT novel

The 2026-11-15 audit was incomplete. The adversarial re-audit found:
- Quanyu Tang's public note (07 Jan 2026, ~10 months before the lab's
  session) proves `f(n,2) = C(n,2) − ex(n,C4)` and gives a Turán reduction for
  all k (`f(n,k) = C(n,2) − ex(n,F_k^min)`).
- OEIS **A006855** tabulates `ex(n,C4)` to n=40, so f(n,2) at n=10..14 is
  already determined: 29, 37, 45, 54, 64.

Therefore the k=2 extension is **downgraded from "new exact values" to
"independent CP-SAT verification of published values, with witness
graphs."** The only defensible novelty claim is:
> first exact OPTIMAL certificates + witness graphs at f(10,3)=29 and
> f(10,4)=28, via a symmetry-broken model — explicitly conditional on an
> incomplete GitHub *code* search (sign-in wall) and a rate-limited mirror.

Per Rule 0, no OEIS filing is drafted for k=2. For k=3/k=4, re-run the audit
if code search becomes available before filing anything.

### Rule 1 fixes made this session

1. Generated the nine missing `fnk_n{4..12}_k1.json` certificates the old doc
   claimed existed but did not — claim is now true and verified.
2. Corrected the stale k=4 table row ("run in flight" → landed values
   6:4, 7:9, 8:15, 9:21).
3. Replaced the stale `[≥?]` placeholder at k=2,n=12 with the recorded bound 34.
4. Added a solver-independent verifier (`scripts/verify_fnk.py`); all 28 OPTIMAL
   certificates pass, 0 fail (10 FEASIBLE bound-only rows reported honestly).

## Reproduce

```bash
cd math/erdos614-fnk
# original model (sanity)
~/repos/venv-math/bin/python scripts/fnk_solve.py --n 9 --k 2 --tl 240 --workers 8   # -> OPTIMAL 23
~/repos/venv-math/bin/python scripts/fnk_solve.py --n 9 --k 3 --tl 240 --workers 8   # -> OPTIMAL 22
# symmetry-broken model (new exact values)
~/repos/venv-math/bin/python scripts/fnk_solve_sym.py --n 10 --k 3 --tl 240 --workers 6  # -> OPTIMAL 29
~/repos/venv-math/bin/python scripts/fnk_solve_sym.py --n 10 --k 4 --tl 240 --workers 6  # -> OPTIMAL 28
# independent, stdlib-only verification of every witness
python3 scripts/verify_fnk.py all --cert-dir results/certificates
```

Environment: ortools CP-SAT 9.9.3963, 4–12 workers, 13–900 s caps, seed
20261115 (some retries 42). Certificates: `results/certificates/fnk_n*_k*.json`
(original) and `fnk_n*_k*_s2.json` (symmetry-broken extension), each with
status, value/bound, witness_edges, wall_s and subsets.
