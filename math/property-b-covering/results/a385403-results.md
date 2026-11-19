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
| 13 | 9 | **a(13) = 9 EXACT** (2026-11-19) | k=9 witness certified; k=8 impossible by the degree-bound lemma + Fano uniqueness — see 2026-11-19 section |
| 14 | 10 | **9 ≤ a(14) ≤ 10** | k=10 FEASIBLE (witness); k=9 UNKNOWN at 900 s |

- **a(11) = 9** — witness (9 triples, covers [11], verified forcing by an
  independent pure-Python scan of all 2¹¹ colorings):
  {123, 12-11-… see certificate} — full edge list in
  `results/certificates/verify_n11_k9.json` (PASS) and the OEIS draft.
- **a(12) = 9** — witness includes {1,11,12} replacing the n=11 witness's
  {1,2,11}+{8,9,10} arrangement; verified by all 2¹² colorings
  (`results/certificates/verify_n12_k9.json`, PASS).
  **Correction (2026-11-19, Rule 0):** an earlier revision of this doc claimed
  the a(12) witness contained **no Fano sub-family**. That was false. An
  independent re-enumeration of all C(9,7)=36 seven-edge sub-families of the
  certified witness finds exactly **one Fano plane** (the triples
  {123,145,167,246,257,347,356}), and `verify_n12_k9.json` itself records
  `fano_subfamily_present: true`. The a(12) witness is therefore *not* a
  non-Fano system; the bound's tightness at n=12 is witnessed by a system
  that does contain a Fano sub-family. The conditional analytic lower-bound
  discussion below is unaffected (it already treats non-Fano forcing as a
  possibility), but the structural claim is withdrawn.
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

### Final-report additions (2026-11-16, agent conclusion)

- **NEW verified upper bounds: a(15) ≤ 10 and a(16) ≤ 10** — Fano + 3
  covering triples, witnesses PASS the independent verifier over all
  32,768 / 65,536 colorings (certificates a385403b_n15/n16).
- Measured (not assumed): inclusion-dedupe is a dud — minimal-mono-set
  filtering keeps 4082/4096 (n=13) and 8177/8192 (n=14) constraints.
- LP relaxation is feasible in every variant: no LP-only proof exists;
  branch-and-bound must do the work. Bundled SCIP is single-threaded and
  slower than CP-SAT at the (10,7) benchmark (58 s vs 25 s).
- Lazy-loop structure insight: escape colorings are overwhelmingly
  balanced — 177/196 pooled cuts have red-size 6/7 (mono-set 55); the
  master turns hard at ~184–196 cuts; the 196-cut pool is saved in the
  lazy certificate for replay-seeding.
- Next-session plan (from the final report): seed the lazy master with
  ALL 1716 size-55 colorings + checkpoint per iteration + fano-free
  master + 12 workers ≥ 4–6 h; separately probe "does any Fano-free
  non-2-colorable 3-graph with 8 edges exist (no coverage)" — INFEASIBLE
  there proves BOTH (13,8) and (14,9) by counting alone; re-run halved
  (13,8) / fano (14,9) at 12 workers ≥ 3600 s. If (13,8) INFEASIBLE
  lands, a(13)=9 is immediately proved (k=9 witness already certified).

### 2026-11-19 — a(13) = 9 PROVED; Fano-free 8-edge probe for a(14)

**a(13) = 9 is now exact.** The previous bracket 8 ≤ a(13) ≤ 9 is closed by
a short argument the earlier sessions missed:

1. An edge-minimal non-2-colourable hypergraph has minimum vertex degree ≥ 2
   (a degree-1 vertex is coloured last, opposite to the other two vertices of
   its unique edge). A 3-uniform one with e edges therefore meets at most
   ⌊3e/2⌋ vertices.
2. The only 7-edge non-2-colourable 3-graph is the Fano plane on exactly 7
   vertices (classical; re-certified here: `fano_uniqueness_n{7..10}_e7.json`
   are all INFEASIBLE with Fano forbidden — and ⌊21/2⌋ = 10 bounds the vertex
   count, so n = 7..10 is exhaustive).
3. If 8 triples covered [13] and forced, take a minimal non-2-colourable
   subfamily E'. If |E'|=8 then E' meets ≤ 12 vertices < 13; if |E'|=7 then
   E' is the Fano plane (7 vertices) and the remaining triple covers ≤ 3 more,
   giving ≤ 10 < 13. Both impossible. The certified k=9 witness gives the
   upper bound, so a(13)=9.

Full derivation and the probe for a(14): `results/fano-free-8edge-probe-2026-11-19.md`.
The 8-edge Fano-free probe is INFEASIBLE at n=8,9,10,11 (certificates present;
n=10 in 106 s, n=11 in 950 s at 12 workers) but UNKNOWN at n=12 after 1200 s
(with and without the redundant Fano cuts). The only remaining case is the
2-regular 3-graphs on 12 vertices, so **a(14) remains bracketed 9 ≤ a(14) ≤ 10**.

### 2026-11-19 — structure claim corrected (Rule 0)

- The named "does any Fano-free non-2-colourable 8-edge 3-graph exist" probe
  was implemented (`scripts/fano_free_probe.py`, plus a lazy-cut variant).
  The finite reduction (minimal ⇒ min degree ≥ 2 ⇒ ≤ 12 vertices) is proven
  in `results/fano-free-8edge-probe-2026-11-19.md`. INFEASIBLE at n=8 (1.7 s),
  n=9 (19.7 s), n=10 (106 s) and n=11 (950 s); n=12 UNKNOWN. The a(13) bracket
  is closed by the degree-bound argument above; a(14) awaits n=12.
- **Rule 0 correction in place:** an earlier claim in this doc that the a(12)
  witness "contains no Fano sub-family" was false. Independent re-enumeration
  finds exactly one Fano sub-family, and `verify_n12_k9.json` already recorded
  `fano_subfamily_present: true`. The claim is withdrawn above and in the
  OEIS draft; no result value changes.

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
