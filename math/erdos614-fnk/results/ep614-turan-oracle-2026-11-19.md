# Independent Turán-oracle validation of f(10,3)=29 — 2026-11-19

**Role:** Rule-0/Rule-1 *validation*, not a novelty claim. This re-derives the
lab's already-submitted exact value `f(10,3)=29` with a **different CP-SAT
model** built from the published Turán reduction, and checks the family used.

## 1. Source note and the exact forbidden family (task 1)

Source: Quanyu Tang, *Erdős Problem #614: a Turán-type reformulation*,
`erdos614_note.pdf` at https://github.com/QuanyuTang/erdos-614-turan-reduction
(forum comment on https://www.erdosproblems.com/forum/discuss/614, 07 Jan 2026).
PDF fetched via `curl` from the raw GitHub URL and read with `pdftotext -layout`.

Verbatim statements from the note:

- **Definition 4.1.** `m := k+2`. `F_k` = finite family of all graphs `F` on
  exactly `m` vertices with `δ(F) ≥ 2`. `F_k^min ⊆ F_k` = those `F` that are
  **edge-minimal** with `δ(F) ≥ 2` (i.e. `δ(F) ≥ 2` but `δ(F−e) ≤ 1` for every
  `e ∈ E(F)`).
- **Lemma 4.2.** "A graph `H` satisfies (⋆) if and only if `H` is `F_k`-free as
  a **(not necessarily induced) subgraph**." → the forbidden family is used
  as **SUBGRAPHS**, explicitly *not* induced subgraphs.
- **Lemma 4.3.** `H` is `F_k`-free iff it is `F_k^min`-free.
- **Theorem 4.5 / Corollary 4.6.** For all `n ≥ 5`,
  `f(n,3) = C(n,2) − ex(n, {C5, K2,3, K1∨2K2})`.
- `K1 ∨ 2K2` = **join of a single vertex with two disjoint edges** — the
  5-vertex, 6-edge "bowtie": one apex adjacent to all four vertices of two
  disjoint edges.

**Exact answer to task 1:** `F_3^min = {C5, K2,3, K1∨2K2}`, all on `m=5`
vertices, forbidden as **(not necessarily induced) subgraphs**. The note's
Lemma 4.2 is the decisive sentence; `ex(n,·)` here is the ordinary (subgraph)
Turán number, so `f(n,3)=C(n,2)−ex(n,F_3^min)`.

Independent brute-force check (in the new script): enumerate all `2^10=1024`
labeled graphs on 5 vertices; exactly **37** are edge-minimal with `δ≥2`, and
this set equals exactly the union of all labelings of the three canonical
graphs — 12 (C5) + 10 (K2,3) + 15 (bowtie) = 37. Family reproduced ✓.

## 2. New model (task 2)

New file only: `scripts/turan_oracle_k3.py` (no other file edited). Run with
`~/repos/venv-math/bin/python`, OR-Tools CP-SAT **9.9.3963**.

- Variables: one Boolean `x[i][j]` per edge of an `n`-vertex complement graph
  `H`; **maximize** `Σ x`.
- Constraints: for every 5-subset `S ⊆ V` and every distinct embedding of each
  forbidden graph onto `S`, forbid all its edges at once:
  `Σ_{e in embedding} x[e] ≤ |E(F)| − 1`. Embeddings are reduced by the
  automorphism group of each `F` via dedup of the image edge set; distinct
  patterns per 5-set: C5 **12**, K2,3 **10**, bowtie **15**. Total cuts:
  `37·C(n,5)` (9,324 at n=10; 17,094 at n=11).
- Symmetry breaking: `deg(0) ≥ deg(1) ≥ … ≥ deg(n−1)`; valid because both
  forbidden-subgraph freeness and edge count are relabelling-invariant.
- Optional valid upper bound on `ex(n)` via the counting argument
  `e(G) ≥ ⌈n·f(n−1,3)/(n−2)⌉`; for n=11, `f(11,3) ≥ ⌈11·29/9⌉ = 36`, i.e.
  `ex(11) ≤ 19` (used only in the second n=11 run).

This is structurally different from the lab's `fnk_solve_sym.py`: that model
*minimizes* edges of `G` with reified induced-degree-≥3 constraints per 5-set;
this one *maximizes* edges of the complement `H` with explicit forbidden
subgraph-embedding cuts from the published Turán reduction.

## 3. Validation against known small values (task 2/3)

Expected complement edge count `ex(n,F_3) = C(n,2) − f(n,3)` from the lab's
exact table: **7, 8, 10, 13, 14** for n=5..9. Time cap 60 s, 4 workers.

| n | C(n,2) | expected ex | found ex (this model) | f(n,3) | status | wall |
|---|--------|-------------|------------------------|--------|--------|------|
| 5 | 10 | 7  | 7  | 3  | OPTIMAL | 0.02 s |
| 6 | 15 | 8  | 8  | 7  | OPTIMAL | 0.05 s |
| 7 | 21 | 10 | 10 | 11 | OPTIMAL | 0.17 s |
| 8 | 28 | 13 | 13 | 15 | OPTIMAL | 0.42 s |
| 9 | 36 | 14 | 14 | 22 | OPTIMAL | 4.48 s |

**5/5 reproduced.** The family brute-force check also passed. Model trusted.

## 4. Results (task 3)

All main runs: 4 workers, ≤240 s cap, seed 0.

| n | cuts | status | ex(n,F_3) | implied f(n,3) | wall |
|---|------|--------|-----------|----------------|------|
| 10 | 9,324 | **OPTIMAL** | **16** | **29** | 45.44 s |
| 11 (plain) | 17,094 | FEASIBLE | 18 ≤ ex ≤ 28 → 27 ≤ f ≤ 37 | bound only | 240.36 s |
| 11 (with `ex≤19`) | 17,094 | FEASIBLE | 18 ≤ ex ≤ 19 → **36 ≤ f ≤ 37** | bound only | 240.66 s |

- **n=10:** converged to OPTIMAL with `ex=16`, hence
  `f(10,3) = C(10,2) − 16 = 45 − 16 = 29`. The optimal witness (16 edges,
  degree multiset `[4,4,3,3,3,3,3,3,3,3]`) was re-checked by direct enumeration
  of all 5-subsets × all forbidden embeddings: **0 forbidden embeddings found**.
  This independently confirms the lab's `f(10,3)=29`.
- **n=11:** did **not** close inside the 240 s cap. The plain run gives a
  37-edge witness (`ex≥18`, i.e. `f≤37`) against a solver bound `ex≤28`;
  adding the proven counting bound `ex≤19` tightens this to `ex ∈ [18,19]`,
  i.e. `f(11,3) ∈ {36,37}`. No exact n=11 value is claimed. (This is stronger
  than the lab's recorded n=11 k=3 bound `28 ≤ f ≤ 37`, and is consistent with
  it; both leave the cell unresolved.)

Environment note: 12 CPUs available but a heavy solve ran elsewhere; all runs
here used at most **4 workers** and caps ≤ **240 s** to avoid contention.

## 5. Verdict

**Rule 0 update 2026-11-20:** web search is now available and found that
Erdős Problem a Day had already computed 14 small exact f(n,k) values in July
2026. This document remains validation only — and the parent results doc has
withdrawn its numeric-novelty claim. See `PRIOR-ART-WATCH.md` at repo root.

1. **f(10,3)=29 is INDEPENDENTLY CONFIRMED.** A separate maximization model
   built from the published Turán reduction (Cor. 4.6), with a different
   variable semantics and different constraints from the lab's solver, returns
   OPTIMAL `ex(10, F_3^min)=16`, giving `f(10,3)=45−16=29`, and reproduces all
   five known small values 5/5. The optimal witness is forbidden-subgraph free
   under direct re-check.
2. This is **validation only — NO novelty claim.** The reduction and the
   forbidden family are published prior art (Quanyu Tang, Jan 2026), and the
   value `f(10,3)=29` is the lab's own already-submitted result. Nothing here
   should be filed as a new OEIS term or advertised as a first.
3. **n=11 remains unresolved:** `f(11,3) ∈ [36,37]` with the counting bound,
   `[27,37]` without it. Honest negative — no exact value claimed.

## 6. Reproduce

```
cd ~/repos/open-research-lab/math/erdos614-fnk
~/repos/venv-math/bin/python scripts/turan_oracle_k3.py --validate --tl 60 --workers 4
~/repos/venv-math/bin/python scripts/turan_oracle_k3.py --n 10 --tl 240 --workers 4
~/repos/venv-math/bin/python scripts/turan_oracle_k3.py --n 11 --tl 240 --workers 4 --ub 19
```

## 7. References

1. Q. Tang, *Erdős Problem #614: a Turán-type reformulation* — note PDF:
   https://github.com/QuanyuTang/erdos-614-turan-reduction/blob/main/erdos614_note.pdf
2. Problem-page comment linking the note — https://www.erdosproblems.com/forum/discuss/614
3. Erdős Problem #614 — https://www.erdosproblems.com/614
4. Lab's prior art audit — `results/ep614-prior-art-2026-11-19.md` (local)
5. Lab's compute log / values — `results/ep614-compute-2026-11-19.md` (local)
