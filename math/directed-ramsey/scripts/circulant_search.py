#!/usr/bin/env python3
"""circulant_search.py — search for circulant witnesses for open Erdős #112 cells.

A circulant digraph on Z_N with connection set S has i->j iff (j-i) mod N in S.
We restrict to ORIENTED circulants (S ∩ -S = empty), which is WLOG: deleting
one arc from each 2-cycle preserves independent sets and only destroys
transitive tournaments.

By translation symmetry it suffices to constrain subsets containing 0.

Modes:
  --n 4 --m 4 : no independent 4-set, no transitive 4-tournament
  --n 3 --m 5 : no independent 3-set, no transitive 5-tournament
A FEASIBLE result with connection set S proves k(n,m) > N.
"""
import argparse
import itertools
import json
import time

from ortools.sat.python import cp_model


def solve(n, m, N, tl=120.0, workers=6, seed=20261119):
    mdl = cp_model.CpModel()
    y = {s: mdl.NewBoolVar(f"y_{s}") for s in range(1, N)}
    for s in range(1, N):
        t = N - s
        if s < t:
            mdl.Add(y[s] + y[t] <= 1)

    # By translation symmetry it suffices to check subsets containing vertex 0.
    # IMPORTANT: the independent-set constraint applies to n-subsets and the
    # transitive-tournament constraint to m-subsets. Using m for both was a bug
    # caught by the independent verifier on (3,5); n=m in the (4,4) cell, so
    # those results were unaffected.
    n_subsets = [(0,) + rest for rest in itertools.combinations(range(1, N), n - 1)]
    m_subsets = [(0,) + rest for rest in itertools.combinations(range(1, N), m - 1)]

    for T in n_subsets:
        # not independent: at least one arc among the pairs
        arcs = []
        for u, v in itertools.combinations(T, 2):
            arcs += [y[(v - u) % N], y[(u - v) % N]]
        mdl.AddBoolOr(arcs)

    for T in m_subsets:
        # no transitive m-tournament: for each linear order of T, the
        # m(m-1)/2 "forward" arcs cannot all be present.
        for order in itertools.permutations(T):
            terms = [y[(order[j] - order[i]) % N]
                     for i in range(m) for j in range(i + 1, m)]
            mdl.Add(sum(terms) <= len(terms) - 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    t0 = time.time()
    st = solver.Solve(mdl)
    wall = round(time.time() - t0, 2)
    status = solver.StatusName(st)
    out = {"n": n, "m": m, "N": N, "status": status, "wall_s": wall,
           "n_subsets": len(n_subsets), "m_subsets": len(m_subsets),
           "workers": workers, "seed": seed}
    if status in ("OPTIMAL", "FEASIBLE"):
        S = sorted(s for s in range(1, N) if solver.Value(y[s]))
        out["S"] = S
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--m", type=int, required=True)
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--tl", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--json", type=str)
    a = ap.parse_args()
    r = solve(a.n, a.m, a.N, a.tl, a.workers)
    print(json.dumps(r))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
