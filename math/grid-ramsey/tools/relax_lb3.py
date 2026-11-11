#!/usr/bin/env python3
"""relax_lb3.py — exact lower bound for the minimum number of monochromatic
rectangles in a c-coloring of an m x n grid, via the aggregation relaxation
of tools/relax_lb.py (2 colors) generalized to c colors; solved to proven
optimality with CP-SAT.

Exact identities (true for every real c-coloring; the relaxation drops only
the realizability of the per-row-pair pattern by an actual grid):

  mono_total = sum over row pairs {i,j} of sum over colors a of C(a_ij^a, 2)
      a_ij^a = #columns where rows i and j are both color a
  (per-color column-count identity)
      sum_{i<j} a_ij^a = sum_k C(z_{k,a}, 2)
      where z_{k,a} = #cells of color a in column k (so sum_a z_{k,a} = m).

Relaxation: minimize sum_{i<j} sum_a C(a_ij^a, 2) subject to
  sum_a a_ij^a <= n per row pair,  sum_{i<j} a_ij^a = sum_k C(z_{k,a}, 2),
  z_{k,a} in [0,m], sum_a z_{k,a} = m per column.
Any real coloring induces a feasible point whose objective equals its true
rectangle count, so the proven optimum of the relaxation is a valid lower
bound LB_c(m,n).  For c=2 the model is exactly tools/relax_lb.py's.
C(v,2) is linearized exactly as sum_{t=1..v} (t-1) via threshold booleans
(same linearization as the 2-color tool).

Validation (--validate): for c=2 the model must reproduce the lab's
relax_lb.py values LB(5,5)=1, LB(6,6)=6, LB(7,7)=21, LB(8,8)=40, LB(9,9)=74
(the middle three are exactly the OEIS A399620 values, i.e. tight).

Usage:
  python3 relax_lb3.py m n --colors 3 [--time-limit S] [--workers K]
      [--json OUT] [--validate]
Prints JSON {m, n, colors, lb, status, wall_s}.
"""
import argparse
import json
import time

from ortools.sat.python import cp_model


def c2(model, v, upper, tag):
    """Return an expression equal to C(v,2) for IntVar v in [0,upper],
    via exact linearization C(v,2) = sum_{t=1..v} (t-1)."""
    terms = []
    for t in range(1, upper + 1):
        u = model.NewBoolVar(f"{tag}_ge{t}")
        model.Add(v >= t).OnlyEnforceIf(u)
        model.Add(v <= t - 1).OnlyEnforceIf(u.Not())
        if t - 1:
            terms.append((t - 1) * u)
    return sum(terms) if terms else 0


def lb(m, n, colors, time_limit=120.0, workers=3):
    model = cp_model.CpModel()
    R = m * (m - 1) // 2
    # per-column per-color cell counts z[k,a]
    z = {}
    for k in range(n):
        for a in range(colors):
            z[k, a] = model.NewIntVar(0, m, f"z{k}_{a}")
        model.Add(sum(z[k, a] for a in range(colors)) == m)
    P = [sum(c2(model, z[k, a], m, f"cz{k}_{a}") for k in range(n))
         for a in range(colors)]
    # per-row-pair per-color agreement counts
    a = {}
    for idx in range(R):
        for c in range(colors):
            a[idx, c] = model.NewIntVar(0, n, f"a{idx}_{c}")
        model.Add(sum(a[idx, c] for c in range(colors)) <= n)
    for c in range(colors):
        model.Add(sum(a[idx, c] for idx in range(R)) == P[c])
    obj = sum(c2(model, a[idx, c], n, f"ca{idx}_{c}")
              for idx in range(R) for c in range(colors))
    model.Minimize(obj)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 20261109
    t0 = time.time()
    status = solver.Solve(model)
    wall = time.time() - t0
    ok = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    # the proven lower bound: objective if OPTIMAL, else BestObjectiveBound
    bound = solver.BestObjectiveBound() if ok else None
    return {
        "m": m, "n": n, "colors": colors,
        "status": solver.StatusName(status),
        "lb": int(round(bound)) if ok else None,
        "objective": int(round(solver.ObjectiveValue())) if ok else None,
        "wall_s": round(wall, 2),
    }


def validate(time_limit, workers):
    """c=2 regression battery against the lab's relax_lb.py values."""
    expected = {(5, 5): 1, (6, 6): 6, (7, 7): 21, (8, 8): 40, (9, 9): 74}
    all_ok = True
    for (m, n), want in expected.items():
        res = lb(m, n, 2, time_limit, workers)
        ok = res["status"] == "OPTIMAL" and res["lb"] == want
        all_ok &= ok
        verdict = "OK" if ok else "MISMATCH"
        print(f"  c=2 ({m},{n}): got {res['lb']} ({res['status']}, "
              f"{res['wall_s']}s) expected {want} -> {verdict}")
    print("VALIDATION", "PASSED" if all_ok else "FAILED")
    return all_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("m", type=int)
    ap.add_argument("n", type=int)
    ap.add_argument("--colors", type=int, default=3)
    ap.add_argument("--time-limit", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--json", type=str, default=None)
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()

    if args.validate:
        ok = validate(args.time_limit, args.workers)
        raise SystemExit(0 if ok else 1)

    res = lb(args.m, args.n, args.colors, args.time_limit, args.workers)
    print(json.dumps(res))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
