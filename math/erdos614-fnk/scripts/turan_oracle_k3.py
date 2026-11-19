#!/usr/bin/env python3
"""Independent Turán-reduction oracle for f(n,3) (EP614 validation).

This is a DIFFERENT model from the lab's `fnk_solve_sym.py`.  Instead of
minimizing edges of G subject to "every 5-set has an induced vertex of degree
>= 3", it maximizes edges of the complement H subject to the published
Turán reduction of Quanyu Tang (erdos614_note.pdf, Cor. 4.6):

    f(n,3) = C(n,2) - ex(n, {C5, K2,3, K1 v 2K2})

where the three members are forbidden as (not necessarily induced) SUBGRAPHS
(the note's Lemma 4.2 / Definition 4.1; F_k^min are edge-minimal graphs on
k+2 = 5 vertices with minimum degree >= 2).

Model: one Boolean per possible edge of H; for every 5-subset S and every
distinct embedding of each forbidden graph onto S, forbid all its edges being
present.  Degree-order symmetry breaking deg(0) >= ... >= deg(n-1) is valid
because the property is relabelling-invariant.  Maximize sum of edges.

Self-check: brute-force enumerate ALL labeled 5-vertex graphs, and verify that
the edge-minimal min-degree-2 ones are exactly the 37 labelings of the three
canonical graphs (12 C5 + 10 K2,3 + 15 bowtie).  This independently verifies
the family printed in the note.

Usage:
    ~/repos/venv-math/bin/python scripts/turan_oracle_k3.py \
        --validate --n 10 --tl 240 --workers 4
"""

import argparse
import itertools
import json
import math
import sys
import time

from ortools.sat.python import cp_model

# ---------------------------------------------------------------------------
# The family F_3^min (canonical labeled representatives on vertices 0..4)
# ---------------------------------------------------------------------------

C5 = frozenset({(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)})
K23 = frozenset({(0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4)})  # parts {0,1}|{2,3,4}
BOWTIE = frozenset({(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (3, 4)})  # K1 v 2K2, apex 0

FORBIDDEN = [("C5", C5), ("K2,3", K23), ("K1v2K2 (bowtie)", BOWTIE)]

EDGE_IDX = {frozenset((i, j)): k for k, (i, j) in enumerate(itertools.combinations(range(5), 2))}


def bitmask(edges):
    m = 0
    for u, v in edges:
        m |= 1 << EDGE_IDX[frozenset((u, v))]
    return m


def self_check_family(verbose=True):
    """Verify by brute force that the three canonical graphs are exactly the
    edge-minimal min-degree-2 labeled graphs on 5 vertices."""
    n = 5
    all_edges = list(itertools.combinations(range(n), 2))
    full = (1 << len(all_edges)) - 1

    def degrees(mask):
        d = [0] * n
        for k, (u, v) in enumerate(all_edges):
            if mask & (1 << k):
                d[u] += 1
                d[v] += 1
        return d

    minimal = []
    for mask in range(full + 1):
        d = degrees(mask)
        if min(d) < 2:
            continue
        ok = True
        for k, _ in enumerate(all_edges):
            if mask & (1 << k):
                d2 = degrees(mask ^ (1 << k))
                if min(d2) >= 2:
                    ok = False
                    break
        if ok:
            minimal.append(mask)

    labelings = []
    counts = {}
    for name, F in FORBIDDEN:
        seen = set()
        for perm in itertools.permutations(range(n)):
            seen.add(bitmask((perm[u], perm[v]) for u, v in F))
        counts[name] = len(seen)
        labelings.extend(seen)
    labelings = set(labelings)

    ok = set(minimal) == labelings
    if verbose:
        print(f"[family-check] edge-minimal min-degree-2 labeled graphs: {len(minimal)}")
        print(f"[family-check] labelings: C5={counts['C5']}, K2,3={counts['K2,3']}, "
              f"bowtie={counts['K1v2K2 (bowtie)']}, total={len(labelings)}")
        print(f"[family-check] family {[n for n, _ in FORBIDDEN]} verified: {ok}")
    if not ok:
        raise RuntimeError("Brute-force family check FAILED")
    return ok


def embedding_patterns(F):
    """All distinct embeddings of F onto an abstract sorted 5-tuple (0..4),
    reduced by Aut(F); returned as tuples of index-pairs (i,j), i<j."""
    seen = set()
    for perm in itertools.permutations(range(5)):
        pat = tuple(sorted(frozenset((min(perm[u], perm[v]), max(perm[u], perm[v]))
                                     for u, v in F)))
        seen.add(pat)
    return sorted(seen)


PATTERNS = [(name, F, embedding_patterns(F)) for name, F in FORBIDDEN]


def build_model(n, ub=None):
    """Maximize edges of an n-vertex graph with no forbidden subgraph.
    If ub is given, add the valid constraint sum(edges) <= ub."""
    m = cp_model.CpModel()
    x = {}
    for i, j in itertools.combinations(range(n), 2):
        x[i, j] = m.NewBoolVar(f"x_{i}_{j}")

    # Forbid each embedding of each forbidden graph on each 5-subset.
    total_cuts = 0
    for S in itertools.combinations(range(n), 5):
        for name, F, pats in PATTERNS:
            k = len(F)
            for pat in pats:
                m.Add(sum(x[S[i], S[j]] for i, j in pat) <= k - 1)
                total_cuts += 1

    # Degree-order symmetry breaking: deg(0) >= deg(1) >= ... >= deg(n-1).
    deg = []
    for v in range(n):
        inc = [x[min(v, u), max(v, u)] for u in range(n) if u != v]
        deg.append(sum(inc))
    for v in range(n - 1):
        m.Add(deg[v] >= deg[v + 1])

    if ub is not None:
        m.Add(sum(x.values()) <= ub)

    m.Maximize(sum(x.values()))
    return m, x, total_cuts


def solve(n, tl, workers, seed=0, ub=None):
    m, x, total_cuts = build_model(n, ub=ub)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(tl)
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = False
    t0 = time.time()
    st = solver.Solve(m)
    wall = time.time() - t0
    status = solver.StatusName(st)
    info = {
        "n": n,
        "ub_constraint": ub,
        "status": status,
        "wall_s": round(wall, 2),
        "cuts": total_cuts,
        "ex": None,
        "ex_lb": None,
        "ex_ub": None,
        "witness_edges": None,
        "edge_list": None,
    }
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        chosen = [(i, j) for (i, j), v in x.items() if solver.Value(v)]
        info["witness_edges"] = len(chosen)
        info["edge_list"] = chosen
        info["ex_lb"] = len(chosen)  # feasible solution is a lower bound on the max
        info["ex_ub"] = int(math.ceil(solver.BestObjectiveBound() - 1e-9))
        if st == cp_model.OPTIMAL:
            info["ex"] = len(chosen)
            info["ex_ub"] = len(chosen)
            info["ex_lb"] = len(chosen)
    elif st == cp_model.INFEASIBLE:
        info["ex_ub"] = -1
    print(f"[solve n={n}] status={status} wall={wall:.2f}s cuts={total_cuts} "
          f"ex={info['ex']} lb={info['ex_lb']} ub={info['ex_ub']}")
    return info


KNOWN_EX = {5: 7, 6: 8, 7: 10, 8: 13, 9: 14}  # C(n,2) - f(n,3), lab's exact table


def validate(tl, workers):
    results = []
    all_ok = True
    for n in range(5, 10):
        info = solve(n, tl, workers)
        fval = math.comb(n, 2) - (info["ex"] if info["ex"] is not None else -1)
        ok = (info["status"] == "OPTIMAL" and info["ex"] == KNOWN_EX[n])
        all_ok &= ok
        results.append({"n": n, "expected_ex": KNOWN_EX[n], "ex": info["ex"],
                        "f(n,3)": fval, "status": info["status"], "ok": ok})
        print(f"[validate n={n}] expected ex={KNOWN_EX[n]} got {info['ex']} -> {'OK' if ok else 'FAIL'}")
    print(f"[validate] all known values reproduced: {all_ok}")
    return all_ok, results


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true", help="check n=5..9 against known values")
    ap.add_argument("--n", type=int, action="append", default=[], help="n to solve (repeatable)")
    ap.add_argument("--tl", type=int, default=240, help="time limit seconds per run")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ub", type=int, default=None,
                    help="valid upper bound on ex(n) (e.g. 19 for n=11 via counting)")
    ap.add_argument("--json", default=None, help="write results dict to this path")
    args = ap.parse_args(argv)

    family_ok = self_check_family()
    out = {"family_check": family_ok, "family": [name for name, _ in FORBIDDEN],
           "validation": None, "runs": []}
    if args.validate:
        ok, val = validate(args.tl, args.workers)
        out["validation"] = {"all_ok": ok, "table": val}
    for n in args.n:
        out["runs"].append(solve(n, args.tl, args.workers, args.seed, ub=args.ub))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=2)
        print(f"[json] wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
