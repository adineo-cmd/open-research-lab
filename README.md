# open-research-lab

Original research in mathematics and public-data science. Every result
ships with reproducible scripts and machine-checkable certificates.
Split from the [Open Discovery Lab](https://github.com/adineo-cmd/open-discovery-lab)
lab notebook (owner directive, 2026-11-10).

## Results

### Mathematics — grid Ramsey minima (`math/grid-ramsey/`)

The minimum number of monochromatic rectangles over 2-colorings of grids
(OEIS A399620/A399621 — entries created 2026-09-05, the OEIS itself asks
for more terms).

- **Four new exact OEIS values** (row 9 of A399621): T(9,3)=3, T(9,4)=6,
  T(9,5)=16, T(9,6)=24 — CP-SAT-proven optimal against a proven exact
  aggregation-relaxation lower bound, witnesses independently re-counted.
- **First bounds for the open a(9): 74 ≤ a(9) ≤ 80** (+ structural
  evidence that 80 is the true value: strict local optimality of the
  80-witness, rigid relaxation profile, pigeonhole exclusion of the
  punctured-Hadamard construction family).
- LB(10,10)=130. Method: exact aggregation relaxation + CP-SAT construction
  search with symmetry breaking. OEIS submission package drafted.

### Astronomy — uncatalogued-object mining (`astronomy/high-pm-survey/`)

- **Full-sky Gaia DR3 high-proper-motion harvest: 130,318 unique sources**
  (|pm|>150 mas/yr, G<20, RUWE<1.4) via 4,096 indexed chunk scans of the
  gaia.aip.de TAP mirror (3.3× parallel speedup, zero failures).
- **1,385 ultracool-dwarf-like candidates → epoch-aware vetting leaves
  621 genuinely uncatalogued (39 confidence-A)** — red/faint/fast at
  110–350 pc, just beyond the GCNS 100-pc wall. Candidate list, not a
  discovery claim: every screen recorded per object.

### Discovery engine (`discovery-engine/`)

A scored queue of unique research targets (novelty × feasibility × value)
harvested from open-problem registries and famous GitHub projects used as
instruments — the systematic version of "find something unique to work on".

## Principles

1. Uniqueness bar: verified gap before any claim. 2. Negative results are
results. 3. Everything reproducible — every number regenerable from
committed scripts. 4. No overclaiming: candidates are candidates.

License: MIT for code, CC BY 4.0 for documentation.
