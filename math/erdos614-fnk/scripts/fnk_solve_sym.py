#!/usr/bin/env python3
"""fnk_solve_sym.py — faster exact solver for Erdős problem #614 (EP614).

f(n,k) = min |E(G)| over simple graphs G on n vertices such that EVERY
(k+2)-vertex subset S induces a subgraph with maximum degree >= k
(some v in S has >= k neighbours inside S).

This is an improved encoding over fnk_solve.py, adding two levers:

1. Degree-order symmetry breaking. The target property is invariant under
   relabelling, so we may assume deg(0) >= deg(1) >= ... >= deg(n-1).
   This cuts the search space dramatically (e.g. n=10,k=2 goes from a
   240 s FEASIBLE timeout to OPTIMAL in ~12 s; n=10,k=3 in ~33 s).
2. FEASIBLE witnesses are saved. fnk_solve.py only emitted witness_edges
   on OPTIMAL; here the incumbent solution is recorded on every status so
   a bound run still yields a usable graph and can seed a later hint.

Modes:
  optimize (default) : minimise edge count; OPTIMAL objective = f(n,k).
  prove              : add sum(e) <= ub-1 and solve as pure feasibility.
                       INFEASIBLE proves f(n,k) >= ub (a lower-bound proof).

Validation 2026-11-19: reproduces all previous exact values
n=9 k=2=23, k=3=22, k=4=21, n=8 k=4=15, n=7 k=4=9, n=6 k=4=4,
n=8 k=2=17 (7/7 OK) before any new value is trusted.

Usage:
  fnk_solve_sym.py --n 10 --k 2 --tl 600 --workers 6 --json out.json
  fnk_solve_sym.py --n 10 --k 2 --mode prove --ub 29 --workers 10
"""
import argparse
import itertools
import json
import time

from ortools.sat.python import cp_model


def build(n, k):
    """Return (model, edge_vars, degree_exprs, subsets)."""
    m = cp_model.CpModel()
    e = {}
    for u, v in itertools.combinations(range(n), 2):
        e[(u, v)] = m.NewBoolVar(f"e_{u}_{v}")

    deg = [sum(e[tuple(sorted((v, u)))] for u in range(n) if u != v)
           for v in range(n)]
    # Valid symmetry break: relabel by non-increasing degree.
    for v in range(n - 1):
        m.Add(deg[v] >= deg[v + 1])

    subsets = list(itertools.combinations(range(n), k + 2))
    for si, S in enumerate(subsets):
        bs = []
        for v in S:
            b = m.NewBoolVar(f"b_{si}_{v}")
            neis = [e[tuple(sorted((v, u)))] for u in S if u != v]
            m.Add(sum(neis) >= k).OnlyEnforceIf(b)
            bs.append(b)
        # at least one vertex of S reaches induced degree >= k
        m.AddBoolOr(bs)
    return m, e, deg, subsets


def solve(n, k, tl=120.0, workers=6, seed=20261115, mode="optimize",
          ub=None, hint_file=None):
    if k + 2 > n:
        return {"n": n, "k": k, "status": "VACUOUS", "value": 0,
                "note": "no (k+2)-subsets exist; property vacuous", "wall_s": 0.0}

    m, e, deg, subsets = build(n, k)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed

    if mode == "prove":
        if ub is None:
            raise ValueError("prove mode requires --ub")
        m.Add(sum(e.values()) <= ub - 1)
    else:
        m.Minimize(sum(e.values()))
        if hint_file:
            # Hints belong to the MODEL in OR-Tools 9.9 (CpSolver has no AddHint).
            d = json.load(open(hint_file))
            for uv in d.get("witness_edges", []):
                u, v = uv[0] - 1, uv[1] - 1
                m.AddHint(e[tuple(sorted((u, v)))], 1)
            # edges outside the hint get value 0 so the hint is a full assignment
            hinted = {tuple(sorted((uv[0]-1, uv[1]-1)))
                      for uv in d.get("witness_edges", [])}
            for t in e:
                if t not in hinted:
                    m.AddHint(e[t], 0)

    t0 = time.time()
    st = solver.Solve(m)
    wall = round(time.time() - t0, 2)
    status = solver.StatusName(st)
    out = {"n": n, "k": k, "mode": mode, "status": status, "wall_s": wall,
           "subsets": len(subsets), "workers": workers, "seed": seed}

    if mode == "prove":
        out["claim"] = (f"f({n},{k}) >= {ub}" if status == "INFEASIBLE"
                        else "not proved")
        return out

    # incumbent graph is available on FEASIBLE as well as OPTIMAL
    edges = [t for t, var in e.items() if solver.Value(var)]
    out["witness_edges"] = [[u + 1, v + 1] for u, v in edges]
    if status == "OPTIMAL":
        out["value"] = int(solver.ObjectiveValue())
    elif status == "FEASIBLE":
        out["best"] = int(solver.BestObjectiveBound())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--tl", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20261115)
    ap.add_argument("--mode", choices=["optimize", "prove"], default="optimize")
    ap.add_argument("--ub", type=int, help="prove mode: claim f(n,k) >= ub")
    ap.add_argument("--hint-file", type=str, help="certificate JSON to seed a hint")
    ap.add_argument("--json", type=str, help="write result JSON here")
    a = ap.parse_args()
    r = solve(a.n, a.k, a.tl, a.workers, a.seed, a.mode, a.ub, a.hint_file)
    print(json.dumps(r))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
