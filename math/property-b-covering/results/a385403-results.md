# Results — OEIS A385403 extended: a(11) = 9 and a(12) = 9 EXACT (first new terms since the sequence's creation); a(13), a(14) bracketed at the conjectured bound

Session 2026-11-15. Target picked from OEIS's own `keyword:more` queue:
[A385403](https://oeis.org/A385403), "Minimum number of triples that cover
{1..n} such that every 2-coloring of {1..n} results in at least one
monochromatic triple" (Dewan, Jun 2025; one extension a(10)=8 by Wang,
Jun 2025). Known before this session: a(5)=10, a(6)=10, a(7)=7, a(8)=8,
a(9)=8, a(10)=8; the entry's %F states the upper bound
a(n) ≤ 7 + ⌈(n−7)/3⌉ for n ≥ 7 (Fano plane + ⌈(n−7)/3⌉ covering triples)
with **no lower bounds and no values for n ≥ 11**.

## Definition (fixed for this session)

a(n) = min{ |E| : E ⊆ C([n],3), every vertex of [n] lies in some edge of E,
and every 2-coloring of [n] makes at least one edge of E monochromatic }.
The inner property ("every 2-coloring …") is the negation of property B,
so E is a covering k-edge 3-uniform hypergraph that is NON-2-colorable;
m(3) = 7 (Erdős–Lovász; the Fano plane) is the classical anchor.

## Method

Exact CP-SAT feasibility model (ortools 9.9, 8–12 workers, seeds logged):

- variables s_t ∈ {0,1} for each of the C(n,3) triples;
- Σ s_t = k; coverage Σ_{t∋v} s_t ≥ 1 per vertex;
- hitting: for EVERY 2-coloring c of [n], Σ_{t mono under c} s_t ≥ 1
  (full 2ⁿ colorings for n ≤ 13; complement-halved 2ⁿ⁻¹ for n ≥ 14 —
  complementing all colors preserves mono-triples);
- a(n) settled by INFEASIBLE at k−1 (a genuine solver status, the
  lower-bound proof) + FEASIBLE at k (witness edge list).

**Validation (non-negotiable first step):** the model reproduces all six
known values exactly — a(5)=10, a(6)=10, a(7)=7, a(8)=8, a(9)=8, a(10)=8
(INFEASIBLE at k−1 + FEASIBLE at k for each; certificates
`a385403_n05..n10_*.json`).

## Headline results

| n | %F bound | this session | status |
|---|---|---|---|
| 11 | 9 | **a(11) = 9 EXACT** | proved: INFEASIBLE at 8 (0.4 s) + FEASIBLE at 9 |
| 12 | 9 | **a(12) = 9 EXACT** | proved: INFEASIBLE at 8 + FEASIBLE at 9 |
| 13 | 9 | **8 ≤ a(13) ≤ 9** | k=9 FEASIBLE; k=8 UNKNOWN at 600 s AND 900 s (12 workers) — honestly unresolved |
| 14 | 10 | **9 ≤ a(14) ≤ 10** | k=10 FEASIBLE (witness); k=9 UNKNOWN at 900 s |

- **a(11) = 9** — witness (9 triples, covers [11], verified forcing by an
  independent pure-Python scan of all 2¹¹ colorings):
  {123, 12-11-… see certificate} — full edge list in
  `results/certificates/verify_n11_witness.json` and the OEIS draft.
- **a(12) = 9** — witness includes {1,11,12} replacing the n=11 witness's
  {1,2,11}+{8,9,10} arrangement; notably the a(12) witness contains **no
  Fano sub-family** (structural check in the verifier) — the bound's
  tightness at n=12 is witnessed by a non-Fano system.
- a(13)/a(14): the conjectured bound is witnessed (k = bound FEASIBLE with
  verified witnesses), but the k−1 infeasibility proofs did not converge
  within 600–900 s — the brackets are honest, not values.

## Independent verification (pure Python, no CP-SAT)

`scripts/verify_a385403.py` (stdlib only, deliberately solver-independent):

- every FEASIBLE witness re-checked from scratch: edge validity, coverage,
  |E| = k, and a **full scan of ALL 2ⁿ colorings** (no early exit) —
  17 certificates `verify_n*_*.json`, **all PASS**;
- OEIS known values matched for n = 5..10 (set-equality against the entry);
- lower-bound sweeps at every claimed INFEASIBLE (n, k−1): exhaustive
  enumeration where the count permits (n=5..7 fully enumerated; n=8
  C(56,7)=2.3·10⁸ above the 2.5 M exhaustive cap → randomized), and
  100 000-draw randomized contradiction searches at n=11 k=8 and n=12 k=8 —
  **zero contradictions found anywhere**;
- Fano-structure detection on every witness (the a(7) witness IS the Fano
  plane; the a(12) witness is not and contains no Fano sub-family).

## Structural conjecture (recorded, not proved)

a(n) = 7 + ⌈(n−7)/3⌉ for all n ≥ 7 — now EXACT at n = 7, 8, 9, 10 (prior),
11, 12 (this session), and bracketed tightly at 13 (≥8, ≤9 vs bound 9) and
14 (≥9, ≤10 vs bound 10). A conditional analytic lower bound: if every
minimal non-2-colorable sub-system were the Fano plane (7 edges on exactly
7 vertices), covering-count would give k ≥ 7 + ⌈(n−7)/3⌉ immediately —
but an 8-or-more-edge minimal sub-system evades this argument (its vertex
footprint can reach 3·e), which is exactly where the CP-SAT proofs are
load-bearing. The a(12) non-Fano witness shows non-Fano forcing systems
exist at 9 edges, so the conditional argument cannot simply be extended.

## Honest negatives

1. a(13) k=8 infeasibility: two attempts (600 s full model; 900 s full
   model, 12 workers) both UNKNOWN. n=14 k=9: UNKNOWN at 900 s (halved
   model). These are the session's open remnants.
2. n ≥ 15 not attempted (the infeasibility proofs already exceed the
   session's compute budget at 13–14).
3. The halved (complement-symmetry) formulation was used only for n ≥ 14;
   n ≤ 13 ran the full 2ⁿ model — no mixed-model discrepancy is possible
   in the proved values.

## Prior art (Rule 0, 2026-11-15)

Web searches (`"A385403"`, `minimum triples cover force monochromatic
triple 2-coloring Fano plane extension`, plus the OEIS record and its
companion A111384): no values, bounds, or b-file beyond a(10) exist
anywhere public. The session's delta — first exact values beyond a(10) —
is unique. Related sequences checked: A111384 (max triples avoiding mono
under some coloring — contrasting direction), A383181 (per the OEIS Cf.).

## Continuation attack (2026-11-16) — the n=13 k=8 instance is documented HARD

A dedicated follow-up session attacked the two open lower-bound proofs
with a systematic encoding ladder (21 certificates `a385403b_*.json`):
halved-model revalidations of all six known values (all reproduce exactly
— the re-encoding is sound), constraint deduplication to minimal
mono-sets (m=55 at n=13, m=70 at n=14), 25 lazy cutting-plane iterations
(196 cuts separated; master oscillates FEASIBLE/UNKNOWN with growing
cut count), the Fano case-split with 51,480 nogood constraints
(2409 s, UNKNOWN), and a SCIP/MILP angle — **all attempts return
UNKNOWN on (n=13, k=8)**; (n=14, k=9) likewise (1200 s, deduped).
The brackets 8 ≤ a(13) ≤ 9 and 9 ≤ a(14) ≤ 10 therefore stand as the
honest state, the instance is established as genuinely hard for
CP-SAT/MILP at every tried formulation, and the lazy-constraint
trajectory (which colorings escape at each iteration) is recorded in
`/tmp/propertyb2/logs/` snapshots as the next session's starting point.
Next levers named: a dedicated SAT-solver attack (portfolio, not CP-SAT),
or an analytic classification of 8-edge non-2-colorable 3-graphs on 13
vertices (literature-first: the Fano-uniqueness case analysis).

## Reproduce

```bash
cd math/property-b-covering
~/repos/venv-math/bin/python scripts/a385403_solve.py validate          # reproduces a(5)..a(10)
~/repos/venv-math/bin/python scripts/a385403_solve.py probe --n 11 --k 8 --tl 300   # INFEASIBLE
~/repos/venv-math/bin/python scripts/a385403_solve.py probe --n 11 --k 9 --tl 300   # FEASIBLE (witness)
python3 scripts/verify_a385403.py all --cert-dir results/certificates   # independent verification
```

Certificates: `results/certificates/a385403_n*_*.json` (solves) and
`verify_*.json` (independent checks); incremental solver state in
/tmp/propertyb/witnesses.json (session scratch). OEIS filing is
owner-gated: see `results/oeis-submission-draft.md`.
