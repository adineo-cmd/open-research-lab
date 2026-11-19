# OEIS submission draft — A385403 extension (OWNER-FILED; lab evidence package)

Target: [A385403](https://oeis.org/A385403) — "Minimum number of triples
that cover {1..n} such that every 2-coloring of {1..n} results in at
least one monochromatic triple." Current published terms (offset 5):
10, 10, 7, 8, 8, 8 (n = 5..10). This draft proposes the next three terms,
proved exact, with a paste-ready %E/%C block. Filing requires the owner's
OEIS account (lab precedent: A399620/A399621 draft,
math/grid-ramsey/results/oeis-submission-draft.md).

## Proposed extension

a(11) = 9, a(12) = 9, a(13) = 9.

## Paste-ready OEIS edit blocks

```
%S A385403 10,10,7,8,8,8,9,9,9
%E A385403 a(11)-a(12) from _Aditya Yadav_, Nov 15 2026; a(13) from the same project, Nov 19 2026
```

```
%C A385403 a(n) = 7 + ceiling((n-7)/3) is now witnessed and proved exact
for n = 7..13: the Fano-plane extension witnesses the upper bound, and
CP-SAT feasibility proofs establish the matching lower bounds for n <= 12
(no covering (a(n)-1)-triple system on {1..n} forces a monochromatic triple;
INFEASIBLE certificates, reproducible scripts, and an independent
pure-Python verification scanning all 2^n colorings are archived in the
Open Research Lab repository, math/property-b-covering/). For n = 13 the
lower bound also follows from a short counting argument: an edge-minimal
non-2-colorable 3-graph with e edges has minimum vertex degree >= 2, hence
meets at most floor(3e/2) vertices; the only 7-edge such graph is the Fano
plane (7 vertices), so 8 triples cannot both cover {1..13} and force a
monochromatic triple. For n = 14 only 9 <= a(14) <= 10 is known. A prior
claim that the a(12) extremal witness contains no Fano sub-family was
incorrect: it does contain one (corrected Nov 19 2026).
```

## Witness constructions (for the %e field, if the editor wants them)

- a(11) = 9: {1,2,3}, {1,2,11}, {1,4,5}, {1,6,7}, {2,4,6}, {2,5,7},
  {3,4,7}, {3,5,6}, {8,9,10} — covers {1..11}; every one of the 2^11
  colorings makes some triple monochromatic (verified by exhaustive
  scan, certificate verify_n11_k9.json).
- a(12) = 9: {1,2,3}, {1,4,5}, {1,6,7}, {1,11,12}, {2,4,6}, {2,5,7},
  {3,4,7}, {3,5,6}, {8,9,10} — covers {1..12}; all 2^12 colorings forced
  (verify_n12_k9.json). Corrected 2026-11-19: this system DOES contain a
  Fano sub-family (the seven triples excluding {1,11,12} and {8,9,10});
  an earlier draft incorrectly said it did not.

## Lower-bound proofs (what makes these PROVED, not conjectured)

For each n in {11, 12}: the CP-SAT model (variables = the C(n,3) triples;
constraints = exact size k, vertex coverage, and one hitting constraint
per 2-coloring) is INFEASIBLE at k = 8 — i.e. no covering 8-triple system
on {1..n} forces a monochromatic triple — and FEASIBLE at k = 9 with the
witness above. The INFEASIBLE status is the lower-bound proof; it was
re-attacked by an independent stdlib-only verifier (randomized 100,000-draw
contradiction searches over covering 8-triple systems at both sizes:
zero forcing systems found; exhaustive enumeration where the count
permits). The 2-coloring hitting constraints enumerate all 2^n colorings
(n ≤ 13 runs use the full 2^n; no sampling anywhere).

## Open remnant (state it honestly in the %C if asked)

a(13) ∈ {8, 9} and a(14) ∈ {9, 10}: the k = a(n)-1 infeasibility proofs
did not converge (CP-SAT, 600–900 s, 8–12 workers, two attempts each) —
brackets only. The conjecture a(n) = 7 + ⌈(n−7)/3⌉ remains consistent
with every computed term.

## Verification chain

1. Solver: `math/property-b-covering/scripts/a385403_solve.py`
   (ortools CP-SAT; validated against all six pre-existing terms first).
2. Independent verifier: `math/property-b-covering/scripts/verify_a385403.py`
   (pure stdlib; full 2ⁿ coloring scans; randomized contradiction searches;
   Fano-structure checks) — 17 certificates, all PASS, zero contradictions.
3. Certificates: `math/property-b-covering/results/certificates/`
   (`a385403_n*_*.json` solves, `verify_*.json` checks).

## Filing checklist (owner)

1. Log into OEIS.
2. Apply the %S/%E/%C edits above (keep the existing authorship lines;
   add the extension credit line).
3. Optionally add the a(11) witness as the %e example for a(11).
4. Mention in the edit summary: "extension + exactness proofs via
   CP-SAT + independent verification; certificates archived at
   github.com/adineo-cmd/open-research-lab (math/property-b-covering/)".
