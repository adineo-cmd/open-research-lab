#!/usr/bin/env python3
"""sat_ladder.py — 3-color 11x11 LB attack: CP-SAT satisfaction ladder.

Question answered per run: does a c-coloring of the m x n grid with AT MOST
t monochromatic rectangles exist?  (pure satisfaction, obj <= t as a hard
constraint -- no minimization, so INFEASIBLE is a definitive answer and
raises the lower bound to t+1; SAT yields a witness grid).

Model: the exact count model of tools/min_mono_rect3.py (c-ary, reified
agreement counts a_ij^a per row pair/color, exact C(v,2) linearization,
row-0 color-canonical + rows-1..m-1 lex symmetry breaking), STRICTLY
strengthened with two families of cheap exact constraints that embed the
proven F-24 aggregation structure into the exact model:

  (E1) z_{k,a} = #cells of color a in column k (IntVar, sum_a = m);
       sum_{i<j} a_ij^a = sum_k C(z_{k,a}, 2)   [exact identity, F-24]
       -> the solver gets the aggregation relaxation's propagation power.
  (E2) row pigeonhole: w_{i,a} = row i's count of color a;
       a_ij^a >= w_ic + w_jc - n  and  a_ij^a <= min(w_ic, w_jc)
       [exact: |A n B| >= |A|+|B|-n for the column sets A,B where rows
        i / j have color a]

All added constraints are equalities/valid inequalities on every real
coloring, so both directions (INFEASIBLE claim and SAT witness) stay sound.

Usage:
  python3 sat_ladder.py m n --colors 3 --target t [--time-limit S]
      [--workers K] [--json OUT] [--grid-out FILE]
Prints JSON {m, n, colors, target, status, wall_s, workers} and, on SAT,
the witness grid (also written to --grid-out).
"""
import argparse
import json
import time

from ortools.sat.python import cp_model


def count_mono(cells, m, n):
    """Embedded corner-based pure-Python counter (validator)."""
    cnt = 0
    for r1 in range(m):
        for r2 in range(r1 + 1, m):
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    v = cells[r1][c1]
                    if v == cells[r1][c2] == cells[r2][c1] == cells[r2][c2]:
                        cnt += 1
    return cnt


def c2(model, v, upper, tag):
    terms = []
    for t in range(1, upper + 1):
        u = model.NewBoolVar(f"{tag}_ge{t}")
        model.Add(v >= t).OnlyEnforceIf(u)
        model.Add(v <= t - 1).OnlyEnforceIf(u.Not())
        if t - 1:
            terms.append((t - 1) * u)
    return sum(terms) if terms else 0


def _and_var(model, a, b):
    v = model.NewBoolVar("and_tmp")
    model.AddBoolAnd([a, b]).OnlyEnforceIf(v)
    model.AddBoolOr([a.Not(), b.Not()]).OnlyEnforceIf(v.Not())
    return v


def build(m, n, colors, target):
    model = cp_model.CpModel()
    col = {}
    occ = {}
    for r in range(m):
        for k in range(n):
            col[r, k] = model.NewIntVar(0, colors - 1, f"col{r}_{k}")
            for a in range(colors):
                occ[r, k, a] = model.NewBoolVar(f"occ{r}_{k}_{a}")
                model.Add(col[r, k] == a).OnlyEnforceIf(occ[r, k, a])
                model.Add(col[r, k] != a).OnlyEnforceIf(occ[r, k, a].Not())

    obj_terms = []
    avars = {}
    for i in range(m):
        for j in range(i + 1, m):
            for a in range(colors):
                agree = []
                for k in range(n):
                    g = model.NewBoolVar(f"g{i}_{j}_{a}_{k}")
                    model.AddBoolAnd(
                        [occ[i, k, a], occ[j, k, a]]).OnlyEnforceIf(g)
                    model.AddBoolOr([occ[i, k, a].Not(),
                                     occ[j, k, a].Not()]).OnlyEnforceIf(g.Not())
                    agree.append(g)
                cnt = model.NewIntVar(0, n, f"a{i}_{j}_{a}")
                model.Add(cnt == sum(agree))
                avars[i, j, a] = cnt
                for t in range(1, n + 1):
                    u = model.NewBoolVar(f"u{i}_{j}_{a}_{t}")
                    model.Add(cnt >= t).OnlyEnforceIf(u)
                    model.Add(cnt <= t - 1).OnlyEnforceIf(u.Not())
                    if t - 1:
                        obj_terms.append((t - 1) * u)
    obj = sum(obj_terms) if obj_terms else 0
    model.Add(obj <= target)

    # (E1) embed the aggregation relaxation: column counts + exact identity
    z = {}
    for k in range(n):
        for a in range(colors):
            z[k, a] = model.NewIntVar(0, m, f"z{k}_{a}")
            model.Add(z[k, a] == sum(occ[r, k, a] for r in range(m)))
    for a in range(colors):
        pairs = [avars[i, j, a] for i in range(m) for j in range(i + 1, m)]
        model.Add(sum(pairs)
                  == sum(c2(model, z[k, a], m, f"cz{k}_{a}") for k in range(n)))

    # (E2) row pigeonhole links (exact, cheap)
    w = {}
    for r in range(m):
        for a in range(colors):
            w[r, a] = model.NewIntVar(0, n, f"w{r}_{a}")
            model.Add(w[r, a] == sum(occ[r, k, a] for k in range(n)))
    for i in range(m):
        for j in range(i + 1, m):
            for a in range(colors):
                model.Add(avars[i, j, a] >= w[i, a] + w[j, a] - n)
                model.Add(avars[i, j, a] <= w[i, a])
                model.Add(avars[i, j, a] <= w[j, a])

    # --- symmetry breaking (as min_mono_rect3.py; validity argued there) ---
    model.Add(occ[0, 0, 0] == 1)
    for k in range(1, n):
        for a in range(1, colors):
            model.AddBoolOr([occ[0, k, a].Not()]
                            + [occ[0, kp, a - 1] for kp in range(k)])
    for r in range(1, m - 1):
        model.Add(col[r, 0] <= col[r + 1, 0])
        prev_eq = None
        for k in range(n):
            if prev_eq is not None:
                gt = model.NewBoolVar(f"gt{r}_{k}")
                model.Add(col[r, k] > col[r + 1, k]).OnlyEnforceIf(gt)
                model.Add(col[r, k] <= col[r + 1, k]).OnlyEnforceIf(gt.Not())
                model.AddBoolOr([prev_eq.Not(), gt.Not()])
            if k < n - 1:
                eqc = model.NewBoolVar(f"eq{r}_{k}")
                model.Add(col[r, k] == col[r + 1, k]).OnlyEnforceIf(eqc)
                model.Add(col[r, k] != col[r + 1, k]).OnlyEnforceIf(eqc.Not())
                prev_eq = eqc if prev_eq is None else _and_var(model, prev_eq, eqc)
    return model, col


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("m", type=int)
    ap.add_argument("n", type=int)
    ap.add_argument("--colors", type=int, default=3)
    ap.add_argument("--target", type=int, required=True)
    ap.add_argument("--time-limit", type=float, default=480.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--json", type=str, default=None)
    ap.add_argument("--grid-out", type=str, default=None)
    args = ap.parse_args()

    model, col = build(args.m, args.n, args.colors, args.target)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.time_limit
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = 20261109
    t0 = time.time()
    status = solver.Solve(model)
    wall = time.time() - t0
    res = {
        "m": args.m, "n": args.n, "colors": args.colors,
        "target": args.target, "status": solver.StatusName(status),
        "wall_s": round(wall, 1), "workers": args.workers,
        "seed": 20261109,
    }
    grid = None
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        grid = [[int(solver.Value(col[r, k])) for k in range(args.n)]
                for r in range(args.m)]
        res["count_mono"] = count_mono(grid, args.m, args.n)
        res["witness_grid"] = grid
        if args.grid_out:
            with open(args.grid_out, "w") as f:
                for row in grid:
                    f.write("".join(str(v) for v in row) + "\n")
    print(json.dumps(res))
    if grid:
        for row in grid:
            print("".join(str(v) for v in row))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
