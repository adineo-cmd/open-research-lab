#!/usr/bin/env python3
"""k_solve.py — exact small values of the Erdős–Rado directed Ramsey number.

Picked from https://www.erdosproblems.com/112 (open).  k(n,m) is the least N
such that every digraph on N vertices contains either an independent set of
size n or a transitive tournament of size m.  This script searches for a
*witness* digraph on N vertices avoiding both:

  status FEASIBLE/OPTIMAL -> k(n,m) > N, with the arc list as witness;
  status INFEASIBLE       -> k(n,m) <= N (every digraph on N vertices has
                             one of the two configurations).

Encoding (m=3 only so far):
  * per unordered pair {u,v}, booleans a_uv (u->v), a_vu (v->u) with
    a_uv + a_vu <= 1.  Two-cycles may be dropped WLOG: deleting one arc from
    each 2-cycle preserves independent sets and only destroys transitive
    tournaments (problem-page comment, islomifaridun, 22 Sep 2026).
  * no independent n-set: for every n-subset, at least one arc inside it.
  * no transitive 3-tournament: for every ordered triple (x,y,z), forbid
    x->y AND y->z AND x->z.  (The six permutations cover all transitive
    orientations; a directed 3-cycle is allowed.)
  * valid symmetry break: relabel vertices by non-increasing out-degree.

Validation 2026-11-19: k(3,3)=9 reproduced (witness at N=8, INFEASIBLE at
N=9 in 0.03 s), and the known witness at N=14 for n=4 is reproduced.
k(4,3)=15 / k(5,3) infeasibility proofs are compute-heavy — see results doc.

Usage:
  k_solve.py --n 5 --m 3 --N 21 --tl 100 --workers 4 --json out.json
"""
import argparse
import itertools
import json
import time

from ortools.sat.python import cp_model


def solve_m3(n, N, tl=120.0, workers=6, seed=20261119, sym=True):
    m = cp_model.CpModel()
    a = {}
    for u, v in itertools.combinations(range(N), 2):
        a[(u, v)] = m.NewBoolVar(f"a_{u}_{v}")
        a[(v, u)] = m.NewBoolVar(f"a_{v}_{u}")
        m.Add(a[(u, v)] + a[(v, u)] <= 1)

    for S in itertools.combinations(range(N), n):
        arcs = [a[(u, v)] for u, v in itertools.combinations(S, 2)]
        arcs += [a[(v, u)] for u, v in itertools.combinations(S, 2)]
        m.AddBoolOr(arcs)

    for x, y, z in itertools.permutations(range(N), 3):
        m.Add(a[(x, y)] + a[(y, z)] + a[(x, z)] <= 2)

    # STRONG IMPLIED CONSTRAINTS: if v->x, v->y and x->y then {v,x,y} is a
    # transitive 3-tournament, forbidden.  Hence N+(v), N-(v) are independent
    # sets and |N+(v)|,|N-(v)| <= n-1.  Implied by the constraints above, but
    # adding explicitly dramatically improves propagation.
    out = [sum(a[(v, u)] for u in range(N) if u != v) for v in range(N)]
    inn = [sum(a[(u, v)] for u in range(N) if u != v) for v in range(N)]
    for v in range(N):
        m.Add(out[v] <= n - 1)
        m.Add(inn[v] <= n - 1)

    if sym:
        for v in range(N - 1):
            m.Add(out[v] >= out[v + 1])

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    t0 = time.time()
    st = solver.Solve(m)
    wall = round(time.time() - t0, 2)
    status = solver.StatusName(st)
    out = {"n": n, "m": 3, "N": N, "status": status, "wall_s": wall,
           "workers": workers, "seed": seed}
    if status in ("OPTIMAL", "FEASIBLE"):
        arcs = []
        for u, v in itertools.combinations(range(N), 2):
            if solver.Value(a[(u, v)]):
                arcs.append([u + 1, v + 1])
            if solver.Value(a[(v, u)]):
                arcs.append([v + 1, u + 1])
        out["arcs"] = arcs
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--m", type=int, default=3)
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--tl", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20261119)
    ap.add_argument("--json", type=str)
    a = ap.parse_args()
    if a.m != 3:
        raise SystemExit("only m=3 is implemented")
    r = solve_m3(a.n, a.N, a.tl, a.workers, a.seed)
    print(json.dumps(r))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
