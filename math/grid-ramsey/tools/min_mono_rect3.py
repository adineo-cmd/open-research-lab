#!/usr/bin/env python3
"""min_mono_rect3.py — exact minimum number of monochromatic axis-parallel
rectangles in a c-coloring of an m x n grid, via CP-SAT (Google OR-Tools).

Generalizes tools/min_mono_rect.py (2 colors, count model v2) to c colors.
A "rectangle" = 2 distinct rows x 2 distinct columns; it is monochromatic
iff all 4 corner cells share one color.  For c=3 these are the first
computed values of T_3(k,n): no OEIS sequence or publication gives minimum
monochromatic-rectangle counts for c >= 3 as of 2026-11-11 (see
results/c3-color-bounds.md).

Model (count, v2 c-ary):
  * c color-assignment Booleans per cell: occ[r,k,a] <=> cell(r,k) = a,
    linked to an IntVar col[r,k] in [0,c).
  * per row pair (i,j) and color a: reified agreement Booleans per column;
    a_ij^a = #columns where both rows are color a; monochromatic
    rectangles of that row pair = sum_a C(a_ij^a, 2), linearized exactly as
    C(v,2) = sum_{t<=v} (t-1) over reified thresholds u_t := (a >= t),
    as in the 2-color count model.

Symmetry breaking (both constraints provably valid; the residual color and
column symmetries are left to the solver, like column symmetry in the
2-color tool):
  * row 0 introduces colors in increasing order: occ[0,0,0] fixed and
    occ[0,j,a] -> some earlier occ[0,j',a-1].  Valid: any grid can be
    relabeled (a global color permutation preserves the count) so its
    first row is color-canonical.
  * rows 1..m-1 lexicographically nondecreasing (row 0 excluded from the
    lex chain).  Valid: relabel colors first (does not touch row order),
    then sort rows 1..m-1 (does not touch row 0's pattern).  NOTE: a full
    row-lex chain including row 0 is NOT jointly valid with the
    color-canonical constraint (re-sorting after relabeling can move a
    different row into slot 0), so row 0 is excluded.

Reproducibility: CP-SAT deterministic given --workers/--seed.  Every
witness grid is re-counted here by an embedded corner-based counter and
again, as a fresh code path, by the independent column-pair counter
tools/count_rects.py (see results/certificates/*.json).

Usage:
  python3 min_mono_rect3.py M N --colors 3 [--time-limit S] [--workers K]
      [--lb LB] [--json OUT]
Prints JSON: status, objective, bound, wall_s, grid (digit rows),
count_mono; then the witness grid as digit rows.
"""
import argparse
import json
import time

from ortools.sat.python import cp_model


def count_mono(cells, m, n):
    """Embedded corner-based pure-Python counter (validator, not the model)."""
    cnt = 0
    for r1 in range(m):
        for r2 in range(r1 + 1, m):
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    v = cells[r1][c1]
                    if v == cells[r1][c2] == cells[r2][c1] == cells[r2][c2]:
                        cnt += 1
    return cnt


def _and_var(model, a, b):
    v = model.NewBoolVar("and_tmp")
    model.AddBoolAnd([a, b]).OnlyEnforceIf(v)
    model.AddBoolOr([a.Not(), b.Not()]).OnlyEnforceIf(v.Not())
    return v


def build(m, n, colors, lb=None):
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
                for t in range(1, n + 1):
                    u = model.NewBoolVar(f"u{i}_{j}_{a}_{t}")
                    model.Add(cnt >= t).OnlyEnforceIf(u)
                    model.Add(cnt <= t - 1).OnlyEnforceIf(u.Not())
                    if t - 1:
                        obj_terms.append((t - 1) * u)
    model.Minimize(sum(obj_terms) if obj_terms else 0)
    if lb is not None:
        model.Add(sum(obj_terms) >= lb)

    # --- symmetry breaking (see docstring for the validity argument) ---
    # (1) row 0 introduces colors in increasing order.
    model.Add(occ[0, 0, 0] == 1)
    for k in range(1, n):
        for a in range(1, colors):
            model.AddBoolOr([occ[0, k, a].Not()]
                            + [occ[0, kp, a - 1] for kp in range(k)])
    # (2) rows 1..m-1 lexicographically nondecreasing (row 0 excluded).
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


def solve(m, n, colors, time_limit, workers, lb=None):
    model, col = build(m, n, colors, lb=lb)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 20261109
    t0 = time.time()
    status = solver.Solve(model)
    wall = time.time() - t0
    ok = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    out = {
        "m": m, "n": n, "colors": colors, "model": "count3",
        "status": solver.StatusName(status),
        "objective": int(solver.ObjectiveValue()) if ok else None,
        "bound": int(solver.BestObjectiveBound()) if ok else None,
        "wall_s": round(wall, 1), "workers": workers,
    }
    grid = None
    if ok:
        grid = [[int(solver.Value(col[r, k])) for k in range(n)]
                for r in range(m)]
        out["count_mono"] = count_mono(grid, m, n)
    out["grid"] = grid
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("m", type=int)
    ap.add_argument("n", type=int)
    ap.add_argument("--colors", type=int, default=3)
    ap.add_argument("--time-limit", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--lb", type=int, default=None,
                    help="proven lower bound from relax_lb3.py, added as "
                         "constraint (composition of proofs)")
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()

    res = solve(args.m, args.n, args.colors, args.time_limit, args.workers,
                lb=args.lb)
    grid = res.pop("grid")
    print(json.dumps(res))
    if grid:
        for row in grid:
            print("".join(str(v) for v in row))
    if args.json and grid:
        with open(args.json, "w") as f:
            json.dump({**res, "grid": grid}, f, indent=1)


if __name__ == "__main__":
    main()
