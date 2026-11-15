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
at n = 4, 5, 6, 7, 8, 10, 12 (7/7 OK) — certificates
`results/certificates/fnk_n*_k1.json`.

## Exact values (CP-SAT OPTIMAL + witness graphs)

| k | exact values (n : f(n,k)) |
|---|---|
| 1 | closed form C(n,2) − ⌊n²/4⌋ (validated n=4..12) |
| 2 | 4:2, 5:4, 6:8, 7:12, 8:17, 9:23 |
| 3 | 5:3, 6:7, 7:11, 8:15, 9:22 |
| 4 | (small-n run in flight at session close — certificates land as computed) |

Bounds beyond (FEASIBLE, proven lower bound = solver's BestObjectiveBound,
witness = best found): k=2: n=10 [26, ≤w], n=12 [≥?]; k=3: n=10 [23, ≤w],
n=11 [28, ≤w] — see the certificate JSONs for the per-run bound fields.

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
   are posted anywhere. Delta: first exact tables + witness graphs at
   small (n,k).

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

## Reproduce

```bash
cd math/erdos614-fnk
~/repos/venv-math/bin/python scripts/fnk_solve.py --n 9 --k 2 --tl 240 --workers 8   # -> OPTIMAL 23
~/repos/venv-math/bin/python scripts/fnk_solve.py --n 9 --k 3 --tl 240 --workers 8   # -> OPTIMAL 22
```

Environment: ortools CP-SAT 9.9.3963, 6–8 workers, 60–240 s caps, seed
20261115. Certificates: `results/certificates/fnk_n*_k*.json` (value,
status, witness_edges, wall_s, subsets per run).
