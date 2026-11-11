#!/usr/bin/env python3
"""joint_relax.py — JOINT two-sided aggregation lower bound for the minimum
number of monochromatic rectangles in a c-coloring of an m x n grid.

This is the strengthening of tools/relax_lb3.py sketched as "obvious
strengthening — not built" in results/c3-color-bounds.md (honest note 2:
one-sided aggregation is orientation-asymmetric, e.g. LB(11,12)=15 but
LB(12,11)=0).  The joint model keeps BOTH aggregate views of the SAME
quantity and all cheap exact identities linking them:

Row side (as relax_lb3.py):
  a_ij^a = #columns where rows i,j are both color a
  T = sum_{i<j} sum_a C(a_ij^a, 2)
  sum_{i<j} a_ij^a = sum_k C(z_{k,a}, 2)   (z_{k,a} = #cells color a in col k)
  sum_a a_ij^a <= n per row pair

Column side (transpose):
  b_pq^a = #rows where columns p,q are both color a
  T = sum_{p<q} sum_a C(b_pq^a, 2)
  sum_{p<q} b_pq^a = sum_r C(w_{r,a}, 2)   (w_{r,a} = #cells color a in row r)
  sum_a b_pq^a <= m per column pair

NEW linking identities (all exact for every real coloring):
  (L1) color totals:  sum_k z_{k,a} = sum_r w_{r,a}  per color a
  (L2) row pigeonhole: a_ij^a >= w_{i,a} + w_{j,a} - n   (|A n B| >= |A|+|B|-n)
       a_ij^a <= min(w_{i,a}, w_{j,a})
  (L3) col pigeonhole: b_pq^a >= z_{p,a} + z_{q,a} - m
       b_pq^a <= min(z_{p,a}, z_{q,a})

Every real coloring induces a feasible point (all identities are equalities/
valid inequalities on it), and the objective equals its true rectangle count;
the proven optimum is therefore a valid lower bound LB_joint(m,n) >= max of
the two one-sided bounds.  C(v,2) linearized exactly as in relax_lb3.py.

Usage:
  python3 joint_relax.py m n --colors 3 [--time-limit S] [--workers K] [--json OUT]
Prints JSON {m, n, colors, lb, status, wall_s}.
"""
import argparse
import json
import time

from ortools.sat.python import cp_model


def c2(model, v, upper, tag):
    """Expression equal to C(v,2) for IntVar v in [0,upper] (exact)."""
    terms = []
    for t in range(1, upper + 1):
        u = model.NewBoolVar(f"{tag}_ge{t}")
        model.Add(v >= t).OnlyEnforceIf(u)
        model.Add(v <= t - 1).OnlyEnforceIf(u.Not())
        if t - 1:
            terms.append((t - 1) * u)
    return sum(terms) if terms else 0


def build(m, n, colors):
    model = cp_model.CpModel()
    RP = m * (m - 1) // 2
    CP = n * (n - 1) // 2

    z = {}  # z[k,a]: cells of color a in column k
    for k in range(n):
        for a in range(colors):
            z[k, a] = model.NewIntVar(0, m, f"z{k}_{a}")
        model.Add(sum(z[k, a] for a in range(colors)) == m)
    w = {}  # w[r,a]: cells of color a in row r
    for r in range(m):
        for a in range(colors):
            w[r, a] = model.NewIntVar(0, n, f"w{r}_{a}")
        model.Add(sum(w[r, a] for a in range(colors)) == n)

    a = {}  # a[pair,c]: agreement count of row pair
    for idx in range(RP):
        for c in range(colors):
            a[idx, c] = model.NewIntVar(0, n, f"a{idx}_{c}")
        model.Add(sum(a[idx, c] for c in range(colors)) <= n)
    b = {}  # b[pair,c]: agreement count of column pair
    for idx in range(CP):
        for c in range(colors):
            b[idx, c] = model.NewIntVar(0, m, f"b{idx}_{c}")
        model.Add(sum(b[idx, c] for c in range(colors)) <= m)

    # exact identities: sum over pairs = sum over columns/rows of C(count,2)
    for c in range(colors):
        model.Add(sum(a[idx, c] for idx in range(RP))
                  == sum(c2(model, z[k, c], m, f"cz{k}_{c}") for k in range(n)))
        model.Add(sum(b[idx, c] for idx in range(CP))
                  == sum(c2(model, w[r, c], n, f"cw{r}_{c}") for r in range(m)))

    # (L1) color totals agree between the two views
    for c in range(colors):
        model.Add(sum(z[k, c] for k in range(n))
                  == sum(w[r, c] for r in range(m)))

    # (L2) row-pair pigeonhole links
    idx = 0
    for i in range(m):
        for j in range(i + 1, m):
            for c in range(colors):
                model.Add(a[idx, c] >= w[i, c] + w[j, c] - n)
                model.Add(a[idx, c] <= w[i, c])
                model.Add(a[idx, c] <= w[j, c])
            idx += 1

    # (L3) column-pair pigeonhole links
    idx = 0
    for p in range(n):
        for q in range(p + 1, n):
            for c in range(colors):
                model.Add(b[idx, c] >= z[p, c] + z[q, c] - m)
                model.Add(b[idx, c] <= z[p, c])
                model.Add(b[idx, c] <= z[q, c])
            idx += 1

    # T equals BOTH views (true for every real coloring)
    T = model.NewIntVar(0, 10 ** 6, "T")
    obj_rows = sum(c2(model, a[idx, c], n, f"ca{idx}_{c}")
                   for idx in range(RP) for c in range(colors))
    obj_cols = sum(c2(model, b[idx, c], m, f"cb{idx}_{c}")
                   for idx in range(CP) for c in range(colors))
    model.Add(T == obj_rows)
    model.Add(T == obj_cols)
    model.Minimize(T)
    return model, T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("m", type=int)
    ap.add_argument("n", type=int)
    ap.add_argument("--colors", type=int, default=3)
    ap.add_argument("--time-limit", type=float, default=300.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()

    model, _ = build(args.m, args.n, args.colors)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.time_limit
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = 20261109
    t0 = time.time()
    status = solver.Solve(model)
    wall = time.time() - t0
    ok = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    res = {
        "m": args.m, "n": args.n, "colors": args.colors,
        "status": solver.StatusName(status),
        "lb": int(round(solver.BestObjectiveBound())) if ok else None,
        "objective": int(round(solver.ObjectiveValue())) if ok else None,
        "wall_s": round(wall, 2), "workers": args.workers,
    }
    print(json.dumps(res))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
