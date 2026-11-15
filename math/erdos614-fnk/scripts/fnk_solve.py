#!/usr/bin/env python3
"""fnk_solve.py — exact small-(n,k) tables for Erdős problem #614 (EP614).

f(n,k) = min |E(G)| over simple graphs G on n vertices such that EVERY
(k+2)-vertex subset S induces a subgraph with maximum degree >= k
(i.e. some v in S has >= k neighbours inside S).  Open problem, formalized
at google-deepmind/formal-conjectures ErdosProblems/614.lean; ref FRS97.

Model: edge variables e_uv; per (k+2)-subset S an indicator b_{v,S} per
vertex with (b=1 -> sum_{u in S\\v} e_vu >= k, OnlyEnforceIf) and
sum_v b_{v,S} >= 1.  Minimize sum e.  OPTIMAL objective = f(n,k); the
optimal edge set is the witness graph.

Known-value validation: f(n,1) has a closed form (every 3-set must contain
an edge  <=>  complement triangle-free  <=>  f(n,1) = C(n,2) - floor(n^2/4));
the model must reproduce it before new (n,k) are trusted.

Usage: fnk_solve.py --n N --k K [--tl 120] [--workers 8] [--json OUT]
"""
import argparse, json, itertools, sys, time
from math import comb
from ortools.sat.python import cp_model

def solve(n, k, tl=120.0, workers=8, seed=20261115):
    if k + 2 > n:
        return {"n": n, "k": k, "status": "VACUOUS", "value": 0,
                "note": "no (k+2)-subsets exist; property vacuous", "wall_s": 0.0}
    m = cp_model.CpModel()
    e = {}
    for u, v in itertools.combinations(range(n), 2):
        e[(u, v)] = m.NewBoolVar(f"e_{u}_{v}")
    m.Minimize(sum(e.values()))
    subsets = list(itertools.combinations(range(n), k + 2))
    for si, S in enumerate(subsets):
        bs = []
        for v in S:
            b = m.NewBoolVar(f"b_{si}_{v}")
            neis = [e[tuple(sorted((v, u)))] for u in S if u != v]
            m.Add(sum(neis) >= k).OnlyEnforceIf(b)
            bs.append(b)
        m.Add(sum(bs) >= 1)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    t0 = time.time()
    st = solver.Solve(m)
    wall = round(time.time() - t0, 2)
    status = solver.StatusName(st)
    if status == "OPTIMAL":
        edges = [t for t, var in e.items() if solver.Value(var)]
        return {"n": n, "k": k, "status": "OPTIMAL", "value": int(solver.ObjectiveValue()),
                "witness_edges": [[u+1, v+1] for u, v in edges], "wall_s": wall,
                "subsets": len(subsets)}
    return {"n": n, "k": k, "status": status, "best": int(solver.BestObjectiveBound()) if status == "FEASIBLE" else None,
            "wall_s": wall, "subsets": len(subsets)}

def f1_closed(n):
    return comb(n, 2) - n*n // 4

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--tl", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--json", type=str)
    a = ap.parse_args()
    r = solve(a.n, a.k, a.tl, a.workers)
    print(json.dumps(r))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)

if __name__ == "__main__":
    main()
