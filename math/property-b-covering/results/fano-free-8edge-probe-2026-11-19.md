# Fano-free 8-edge non-2-colourable 3-graph probe — 2026-11-19

Target: the two open A385403 cells a(13) and a(14). Question attacked:

> Does there exist an 8-edge 3-uniform hypergraph that is non-2-colourable
> (fails Property B) yet contains **no Fano plane**?

If the answer is **no**, a(14) ≥ 10 follows. The exact derivations (spelled
out because two different counting steps are involved):

**Lemma (degree bound).** An edge-minimal non-2-colourable hypergraph has
minimum vertex degree ≥ 2 (a degree-1 vertex can be coloured last, opposite
to the other vertices of its unique edge). A 3-uniform one with e edges
therefore uses at most ⌊3e/2⌋ vertices. Also, the only 7-edge non-2-colourable
3-graph is the Fano plane on exactly 7 vertices (classical; re-verified here:
our n=7 Fano-free 7-edge model is INFEASIBLE).

- **a(13) ≥ 9** follows without the probe: let E be a hypothetical 8-triple
  forcing cover of [13], and E' ⊆ E a minimal non-2-colourable subfamily.
  If |E'|=8, E'=E uses ≤ ⌊24/2⌋ = 12 vertices < 13 — impossible. If |E'|=7,
  E' is the Fano plane (7 vertices) and the one remaining triple covers at
  most 3 more, giving ≤ 10 < 13 — impossible.
- **a(14) ≥ 10 needs the probe:** let E be a 9-triple forcing cover of [14],
  E' minimal. |E'|=9 ⇒ ≤ ⌊27/2⌋ = 13 < 14 vertices; |E'|=7 ⇒ Fano (7) plus
  two triples covering ≤ 6 more ⇒ ≤ 13 < 14. The remaining case |E'|=8
  requires that an 8-edge minimal non-2-colourable 3-graph contain a Fano
  plane — exactly the probe's INFEASIBLE verdict — after which Fano (7)
  plus two more triples (≤ 6) gives ≤ 13 < 14, impossible.

The matching upper-bound witnesses at k=9 and k=10 are already certified, so
a(13)=9 and a(14)=10 would both be proved (a(13) from the lemma alone,
a(14) using the probe).

## Reduction (rigorous, makes the search finite)

1. If any non-2-colourable ≤8-edge 3-graph exists, an edge-minimal subgraph
   exists. The only 7-edge non-2-colourable 3-graph is the Fano plane
   (m(3)=7), so a Fano-free one has exactly 8 edges and is minimal.
2. A minimal non-2-colourable hypergraph has minimum vertex degree ≥ 2
   (a degree-1 vertex can be coloured after its edge, opposite to the other
   two vertices). With 8 edges the degree sum is 24, hence ≤ 12 vertices.

So searching n ≤ 12 is exhaustive for the question.

## Model

`scripts/fano_free_probe.py`: edge variables over C(n,3) triples; sum = 8;
min degree ≥ 2; degree-order symmetry breaking; for every 2-colouring of
[n] at least one monochromatic edge; and (upright mode) every labelled Fano
plane on every 7-subset forbidden. Validated on n=7: Fano-free 7-edge search
returns INFEASIBLE in 0.23 s, while allowing Fano returns the plane in 0.02 s.

`scripts/fano_free_probe_lazy.py`: same base model but Fano cuts are added
only when violated by the incumbent (lazy cutting planes), to avoid the
~24k upfront constraints at n=12.

Environment: OR-Tools CP-SAT 9.9.3963, `~/repos/venv-math/bin/python`,
seed 20261119 (upright) / 20261119 (lazy).

## Results so far

| n | mode | status | wall | certificate |
|---|---|---|---|---|
| 7 (validation, 7 edges) | upright | INFEASIBLE | 0.23 s | `fano_uniqueness_n7_e7.json` |
| 7 (validation, Fano allowed) | upright | OPTIMAL (Fano found) | 0.02 s | — |
| 8, 9, 10 (7 edges) — Fano uniqueness | upright | **INFEASIBLE** | 0.13 / 3.37 / 9.13 s | `fano_uniqueness_n{8,9,10}_e7.json` |
| 8 | upright | **INFEASIBLE** | 1.72 s | `fano_free_probe_n8_e8.json` |
| 9 | upright | **INFEASIBLE** | 19.70 s | `fano_free_probe_n9_e8.json` |
| 10 | upright | **INFEASIBLE** (106 s, 12 workers) | — | `fano_free_probe_n10_e8.json` |
| 11 | upright | **INFEASIBLE** (950 s, 12 workers) | — | `fano_free_probe_n11_e8.json` |
| 12 | upright | UNKNOWN (1200 s, 12 workers) | — | `fano_free_probe_n12_e8.json` |
| 12 | upright, Fano cuts omitted (they are redundant at n=12: degree sum 24 over 12 vertices forces all degrees = 2, so no Fano can occur) | UNKNOWN (905 s, 12 workers) | — | `fano_free_n12_deg2.json` |
| 10,11,12 | lazy | UNKNOWN at first base solve (45 s, 12 workers) | — | `fano_free_lazy_n*_e8.json` |

## Consequence already secured: a(13) = 9

The degree-bound lemma above (minimal ⇒ min degree ≥ 2 ⇒ ≤ ⌊3e/2⌋ vertices)
plus the verified Fano uniqueness at 7 edges (table: n=7..10, all INFEASIBLE
without Fano — and ⌊21/2⌋ = 10 bounds the vertex count) proves a(13) ≥ 9 by
the argument in the "Question attacked" section. The k=9 witness for n=13 is
already certified, hence **a(13) = 9 EXACT**. This does not depend on the
8-edge probe at n=10..12; it holds now. (Rule 0: the Fano-uniqueness fact is
classical, so the mathematical content is not claimed as new — the new part
is the machine-checkable certificates and the consequence for A385403, which
the OEIS entry does not record.)

## Honest state

- Proved for n = 8, 9, 10 and 11: no Fano-free non-2-colourable 8-edge
  3-graph exists on ≤ 11 vertices (n=10 INFEASIBLE in 106 s, n=11 in 950 s,
  both at 12 workers).
- n=12 remains UNKNOWN after 1200 s with the full Fano encoding and 905 s
  with Fano cuts removed. The remaining case is exactly the 2-regular
  3-uniform hypergraphs on 12 vertices (degree sum 24 over 12 vertices with
  min degree 2 forces all degrees = 2). **a(14) is therefore NOT changed:**
  9 ≤ a(14) ≤ 10 still stands.
- Next levers (recorded, not executed): a dedicated SAT solver / isomorphism-
  free enumeration of 8-edge minimal non-2-colourable 3-graphs (literature:
  known classifications of small critical 3-graphs), or a stronger analytic
  argument using the structure of the 8-edge degree sequences.
- Prior art still needs a dedicated check before any claim: literature on
  "critical 3-uniform hypergraphs" may already classify the 8-edge case.
  websearch was unavailable (HTTP 402) this session; arxiv search on
  "critical 3-uniform hypergraph small number of edges Fano" returned nothing.

## Reproduction

```bash
cd ~/repos/open-research-lab/math/property-b-covering
~/repos/venv-math/bin/python scripts/fano_free_probe.py --n 7 --edges 7 --allow-fano  # Fano plane
~/repos/venv-math/bin/python scripts/fano_free_probe.py --n 8 --edges 8   # INFEASIBLE
~/repos/venv-math/bin/python scripts/fano_free_probe.py --n 9 --edges 8   # INFEASIBLE
~/repos/venv-math/bin/python scripts/fano_free_probe_lazy.py --n 10 --edges 8
```
