#!/usr/bin/env python3
"""sa_ub.py — simulated-annealing upper-bound search for the minimum number
of monochromatic rectangles in a c-coloring of an m x n grid.

Local search with exact delta evaluation: flipping cell (r,c) from color a
to color b changes the rectangle count by
    delta = R_{r,c}(b) - R_{r,c}(a)
where R_{r,c}(v) = #{(r',c'): r'!=r, c'!=c, grid[r'][c]=v, grid[r][c']=v,
grid[r'][c']=v}  (rectangles having (r,c) as a corner, under the
hypothetical value v).  R_{r,c}(v) is computed in O(m*n) per evaluation,
so tens of thousands of flips per second in pure Python.

Schedule: geometric cooling with reheat, best-ever tracking; the starting
grid is either a file (digit rows, e.g. the F-24 18-rectangle witness) or
uniform random.  Output: best count found + grid (verify independently
with tools/count_rects.py before claiming anything).

Usage:
  python3 sa_ub.py m n --colors 3 [--start FILE|random] [--seconds S]
      [--seed N] [--out FILE] [--kick cells|rows]
Prints JSON {best, steps, restarts, wall_s, seed} and the best grid.
"""
import argparse
import json
import random
import sys
import time


def count_full(g, m, n, colors):
    """Column-pair full count (matches tools/count_rects.py)."""
    from math import comb
    total = 0
    for p in range(n):
        for q in range(p + 1, n):
            cnt = [0] * colors
            for r in range(m):
                if g[r][p] == g[r][q]:
                    cnt[g[r][p]] += 1
            total += sum(comb(x, 2) for x in cnt)
    return total


def rects_through(g, r, c, v, m, n):
    """Mono rectangles with (r,c) as a corner if g[r][c] were v."""
    total = 0
    gr = g[r]
    for r2 in range(m):
        if r2 == r or g[r2][c] != v:
            continue
        row2 = g[r2]
        s = 0
        for c2 in range(n):
            if c2 != c and gr[c2] == v and row2[c2] == v:
                s += 1
        total += s
    return total


def anneal(m, n, colors, g, seconds, rng, t_init=2.0, t_final=0.02, decay=0.9995,
           kick="cells"):
    cur = [row[:] for row in g]
    cur_count = count_full(cur, m, n, colors)
    best, best_grid = cur_count, [row[:] for row in cur]
    T = t_init
    t_end = time.time() + seconds
    steps = 0
    restarts = 0
    cells = [(r, c) for r in range(m) for c in range(n)]
    while time.time() < t_end:
        steps += 1
        T = t_final + (T - t_final) * decay
        r, c = rng.choice(cells)
        old = cur[r][c]
        new = rng.randrange(colors)
        if new == old:
            continue
        delta = rects_through(cur, r, c, new, m, n) - rects_through(cur, r, c, old, m, n)
        if delta <= 0 or rng.random() < pow(2.718281828, -delta / max(T, 1e-9)):
            cur[r][c] = new
            cur_count += delta
            if cur_count < best:
                best = cur_count
                best_grid = [row[:] for row in cur]
        if cur_count == 0:
            break
        # reheat when frozen near a local optimum for a while
        if steps % 40000 == 0 and T < 0.05:
            T = t_init * 0.5
            restarts += 1
            if kick == "rows":
                # strong kick: fully randomize 2 random rows
                for _ in range(2):
                    rr = rng.randrange(m)
                    cur[rr] = [rng.randrange(colors) for _ in range(n)]
            else:
                for _ in range(m // 2):  # small kick: randomize a few cells
                    rr, cc = rng.choice(cells)
                    cur[rr][cc] = rng.randrange(colors)
            cur_count = count_full(cur, m, n, colors)
    return best, best_grid, steps, restarts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("m", type=int)
    ap.add_argument("n", type=int)
    ap.add_argument("--colors", type=int, default=3)
    ap.add_argument("--start", type=str, default="random")
    ap.add_argument("--seconds", type=float, default=480.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--kick", type=str, default="cells", choices=["cells", "rows"])
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()
    m, n, colors = args.m, args.n, args.colors
    rng = random.Random(args.seed)

    if args.start == "random":
        g = [[rng.randrange(colors) for _ in range(n)] for _ in range(m)]
    else:
        g = [[int(ch) for ch in line.split()[0]]
             for line in open(args.start).read().splitlines() if line.strip()]

    t0 = time.time()
    best, best_grid, steps, restarts = anneal(m, n, colors, g, args.seconds, rng,
                                              kick=args.kick)
    wall = time.time() - t0
    res = {
        "m": m, "n": n, "colors": colors, "start": args.start, "kick": args.kick,
        "best": best, "steps": steps, "restarts": restarts,
        "wall_s": round(wall, 1), "seed": args.seed,
        "recount_full": count_full(best_grid, m, n, colors),
        "best_grid": best_grid,
    }
    print(json.dumps(res))
    for row in best_grid:
        print("".join(str(v) for v in row))
    if args.out:
        with open(args.out, "w") as f:
            for row in best_grid:
                f.write("".join(str(v) for v in row) + "\n")


if __name__ == "__main__":
    main()
