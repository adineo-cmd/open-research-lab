#!/usr/bin/env python3
"""Lazy-cutting-plane version of the Fano-free 8-edge probe.

Same mathematics as fano_free_probe.py, but instead of adding all ~24k
labelled-Fano constraints up front, it solves a base model (8 edges, minimum
degree 2, degree symmetry, all 2^n colouring constraints), then iteratively:
  - extracts the incumbent 8-edge hypergraph,
  - searches its C(8,7)=8 seven-edge sub-families for a Fano plane,
  - if one is found, adds the single constraint forbidding that exact
    7-edge configuration and re-solves,
  - if none is found, the witness is a genuine Fano-free non-2-colourable
    8-edge 3-graph (a counterexample to the hoped-for theorem),
  - if the model becomes INFEASIBLE, the theorem is proved.
"""
import argparse
import itertools
import json
import time

from ortools.sat.python import cp_model

FANO_BASE = [(0, 1, 2), (0, 3, 4), (0, 5, 6),
             (1, 3, 5), (1, 4, 6), (2, 3, 6), (2, 4, 5)]


def is_fano(edges):
    vs = set(v for e in edges for v in e)
    if len(vs) != 7 or len(edges) != 7:
        return False
    pairs = [tuple(sorted(p)) for e in edges for p in itertools.combinations(e, 2)]
    return len(pairs) == 21 and len(set(pairs)) == 21


def solve_lazy(n, edges_target=8, iter_tl=40.0, max_iter=300, workers=8,
               seed=20261119, min_degree=2):
    triples = list(itertools.combinations(range(n), 3))
    idx = {t: i for i, t in enumerate(triples)}
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"e_{t}") for t in triples]
    m.Add(sum(x) == edges_target)
    deg = [sum(x[idx[t]] for t in triples if v in t) for v in range(n)]
    for v in range(n):
        m.Add(deg[v] >= min_degree)
    for v in range(n - 1):
        m.Add(deg[v] >= deg[v + 1])
    for bits in itertools.product((0, 1), repeat=n):
        mono = [x[idx[t]] for t in triples
                if bits[t[0]] == bits[t[1]] == bits[t[2]]]
        m.AddBoolOr(mono)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = iter_tl
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed

    t0 = time.time()
    cuts_added = 0
    seen_cuts = set()
    for it in range(1, max_iter + 1):
        st = solver.Solve(m)
        status = solver.StatusName(st)
        if status == "INFEASIBLE":
            return {"n": n, "edges": edges_target, "status": "INFEASIBLE",
                    "verdict": "no Fano-free non-2-colourable 8-edge 3-graph on <= %d vertices" % n,
                    "iterations": it, "cuts_added": cuts_added,
                    "wall_s": round(time.time() - t0, 2)}
        if status not in ("OPTIMAL", "FEASIBLE"):
            return {"n": n, "edges": edges_target, "status": "UNKNOWN",
                    "iteration": it, "cuts_added": cuts_added,
                    "wall_s": round(time.time() - t0, 2)}
        witness = [triples[i] for i in range(len(x)) if solver.Value(x[i])]
        fanos = [c for c in itertools.combinations(witness, 7) if is_fano(c)]
        if not fanos:
            return {"n": n, "edges": edges_target, "status": "COUNTEREXAMPLE",
                    "verdict": "Fano-free non-2-colourable 8-edge 3-graph FOUND",
                    "witness": [[a + 1, b + 1, c + 1] for a, b, c in witness],
                    "iterations": it, "cuts_added": cuts_added,
                    "wall_s": round(time.time() - t0, 2)}
        added = 0
        for f in fanos:
            key = frozenset(f)
            if key in seen_cuts:
                continue
            seen_cuts.add(key)
            m.Add(sum(x[idx[t]] for t in f) <= 6)
            cuts_added += 1
            added += 1
        if added == 0:
            return {"n": n, "edges": edges_target, "status": "STALLED",
                    "iteration": it, "cuts_added": cuts_added,
                    "wall_s": round(time.time() - t0, 2)}
    return {"n": n, "edges": edges_target, "status": "ITER_LIMIT",
            "iterations": max_iter, "cuts_added": cuts_added,
            "wall_s": round(time.time() - t0, 2)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--edges", type=int, default=8)
    ap.add_argument("--iter-tl", type=float, default=40.0)
    ap.add_argument("--max-iter", type=int, default=300)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--min-degree", type=int, default=2)
    ap.add_argument("--json", type=str)
    a = ap.parse_args()
    r = solve_lazy(a.n, a.edges, a.iter_tl, a.max_iter, a.workers,
                   20261119, a.min_degree)
    print(json.dumps(r))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
