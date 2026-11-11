#!/usr/bin/env python3
"""count_rects.py — independent c-color monochromatic-rectangle counter.

Given a c-coloring of a k x n grid (rows of digits 0..c-1), counts
monochromatic axis-parallel rectangles (2 distinct rows x 2 distinct
columns, all 4 corners the same color) via the COLUMN-PAIR decomposition:

    total = sum over column pairs (p,q), over colors a, of C(m_a, 2)
    m_a = #{rows r : grid[r][p] == grid[r][q] == a}

This is a deliberately different code path from the corner-based counter
embedded in tools/min_mono_rect3.py / tools/min_mono_rect.py and from the
row-pair/threshold objective in the CP-SAT models: all three agree iff
every one of them is correct.

Input: a file or stdin containing either
  * rows of digits 0..c-1 (one grid row per line), or
  * a JSON certificate/object with a "grid" (or "witness_grid") key whose
    value is a list of digit rows.

Usage:
  python3 count_rects.py --colors 3 GRIDFILE
  cat grid.txt | python3 count_rects.py --colors 3
  python3 count_rects.py --colors 3 --json results/certificates/c3_T3_k5_n5.json
Prints JSON {k, n, colors, rectangles}; exits 2 on malformed input.
"""
import argparse
import json
import sys
from math import comb


def count_column_pairs(grid, k, n, colors):
    total = 0
    for p in range(n):
        for q in range(p + 1, n):
            m = [0] * colors
            for r in range(k):
                a = grid[r][p]
                if a == grid[r][q]:
                    m[a] += 1
            total += sum(comb(x, 2) for x in m)
    return total


def load_grid(path, colors):
    text = open(path).read() if path else sys.stdin.read()
    grid = None
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            grid = obj.get("grid", obj.get("witness_grid"))
    except (json.JSONDecodeError, ValueError):
        grid = None
    if grid is None:
        grid = [[int(ch) for ch in line.split()[0]]
                for line in text.splitlines() if line.strip()]
    if not isinstance(grid, list) or not grid:
        raise ValueError("no grid found")
    n = len(grid[0])
    for row in grid:
        if len(row) != n:
            raise ValueError("ragged grid")
        for v in row:
            if not isinstance(v, int) or not 0 <= v < colors:
                raise ValueError(f"cell value {v} outside 0..{colors - 1}")
    return grid, len(grid), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gridfile", nargs="?", default=None)
    ap.add_argument("--colors", type=int, default=3)
    ap.add_argument("--json", type=str, default=None,
                    help="also write the result to this JSON file")
    args = ap.parse_args()
    grid, k, n = load_grid(args.gridfile, args.colors)
    total = count_column_pairs(grid, k, n, args.colors)
    out = {"k": k, "n": n, "colors": args.colors, "rectangles": total}
    print(json.dumps(out))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
