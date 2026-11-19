#!/usr/bin/env python3
"""Fano-free 8-edge non-2-colorable 3-graph probe (A385403, 2026-11-19).

Question: does there exist an 8-edge 3-uniform hypergraph that is
  (a) non-2-colorable (Property B fails), and
  (b) Fano-free (contains no Fano plane as a sub-hypergraph)?

If INFEASIBLE, then every 8-edge non-2-colorable 3-graph contains the Fano
plane, which (by the covering-count argument) proves BOTH
  a(13) = 9   and   a(14) = 10
for OEIS A385403, since the k=9 / k=10 witnesses already exist.

Reduction to a finite model (all steps rigorous):
  * If a non-2-colorable 8-edge 3-graph exists, it contains an edge-minimal
    one with <= 8 edges.  The only 7-edge non-2-colorable 3-graph is the Fano
    plane (m(3)=7), so a Fano-free one has exactly 8 edges and is minimal.
  * A minimal non-2-colorable hypergraph has minimum vertex degree >= 2
    (a degree-1 vertex can always be coloured last, opposite to its edge).
    With 8 edges the degree sum is 24, so it has at most 12 vertices.
  Therefore searching n <= 12 vertices is exhaustive.

Model: edge vars e_t over C(n,3) triples; sum(e) == 8; degree >= 2;
Fano-free constraints (forbid every labelled Fano plane on every 7-subset);
for every 2-colouring c of [n], at least one monochromatic edge is present.
Degree-order symmetry breaking deg(0)>=deg(1)>=... is valid (relabelling).
"""
import argparse
import itertools
import json
import time

from ortools.sat.python import cp_model

# the 7 triples of the Fano plane on the 7 points 0..6
FANO_BASE = [(0, 1, 2), (0, 3, 4), (0, 5, 6),
             (1, 3, 5), (1, 4, 6), (2, 3, 6), (2, 4, 5)]


def labelled_fano_planes():
    """All distinct labelled Fano planes on a fixed 7-element set (30)."""
    planes = set()
    for perm in itertools.permutations(range(7)):
        planes.add(frozenset(frozenset(perm[i] for i in t) for t in FANO_BASE))
    return [sorted(tuple(sorted(t)) for t in p) for p in planes]


def solve(n, edges_target=8, tl=120.0, workers=6, seed=20261119,
          min_degree=2, fano_free=True, with_hint=None):
    triples = list(itertools.combinations(range(n), 3))
    idx = {t: i for i, t in enumerate(triples)}
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"e_{t}") for t in triples]

    m.Add(sum(x) == edges_target)
    deg = [sum(x[idx[t]] for t in triples if v in t) for v in range(n)]
    for v in range(n):
        m.Add(deg[v] >= min_degree)
    for v in range(n - 1):
        m.Add(deg[v] >= deg[v + 1])  # valid symmetry break

    n_fano = 0
    if fano_free:
        planes = labelled_fano_planes()
        for S in itertools.combinations(range(n), 7):
            for plane in planes:
                # map base point labels 0..6 onto the 7 chosen vertices
                mapped = [tuple(sorted(S[p] for p in t)) for t in plane]
                m.Add(sum(x[idx[t]] for t in mapped) <= 6)
                n_fano += 1

    n_col = 0
    for bits in itertools.product((0, 1), repeat=n):
        mono = [x[idx[t]] for t in triples
                if bits[t[0]] == bits[t[1]] == bits[t[2]]]
        m.AddBoolOr(mono)
        n_col += 1

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    t0 = time.time()
    st = solver.Solve(m)
    wall = round(time.time() - t0, 2)
    status = solver.StatusName(st)
    out = {"n": n, "edges": edges_target, "status": status, "wall_s": wall,
           "vars": len(x), "fano_constraints": n_fano,
           "coloring_constraints": n_col, "workers": workers, "seed": seed}
    if status in ("OPTIMAL", "FEASIBLE"):
        witness = [triples[i] for i in range(len(x)) if solver.Value(x[i])]
        out["witness"] = [[a + 1, b + 1, c + 1] for a, b, c in witness]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--edges", type=int, default=8)
    ap.add_argument("--tl", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20261119)
    ap.add_argument("--allow-fano", action="store_true")
    ap.add_argument("--min-degree", type=int, default=2)
    ap.add_argument("--json", type=str)
    a = ap.parse_args()
    r = solve(a.n, a.edges, a.tl, a.workers, a.seed,
              a.min_degree, not a.allow_fano)
    print(json.dumps(r))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
