#!/usr/bin/env python3
"""Solver-independent verifier for directed-Ramsey witness digraphs.

Pure Python stdlib.  For a certificate with fields n, m=3, N and arcs
(1-based [u,v] meaning u->v), checks from scratch:
  (i)   arcs are simple (no loops, no duplicate arcs),
  (ii)  there is no independent n-set (full C(N,n) enumeration),
  (iii) there is no transitive 3-tournament (full C(N,3) enumeration,
        all six transitive orientations).
A FEASIBLE/OPTIMAL certificate that passes proves k(n,3) > N.
"""
import argparse
import itertools
import json
import sys


def verify(d):
    n, m, N = d["n"], d["m"], d["N"]
    arcs = set(tuple(e) for e in d["arcs"])
    errs = []
    if m != 3:
        return False, ["only m=3 supported"]
    if any(u == v or not (1 <= u <= N and 1 <= v <= N) for u, v in arcs):
        errs.append("invalid arc endpoint")
    if len(arcs) != len(d["arcs"]):
        errs.append("duplicate arc")
    adj = [[False] * (N + 1) for _ in range(N + 1)]
    for u, v in arcs:
        adj[u][v] = True
    for S in itertools.combinations(range(1, N + 1), n):
        if not any(adj[u][v] or adj[v][u] for u, v in itertools.combinations(S, 2)):
            errs.append(f"independent {n}-set {S}")
            break
    for x, y, z in itertools.combinations(range(1, N + 1), 3):
        if (adj[x][y] and adj[y][z] and adj[x][z]) or \
           (adj[x][z] and adj[z][y] and adj[x][y]):
            errs.append(f"transitive 3-tournament on {(x, y, z)}")
            break
    return not errs, errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("certificate")
    a = ap.parse_args()
    d = json.load(open(a.certificate))
    ok, errs = verify(d)
    if ok:
        print(f"PASS: k({d['n']},3) > {d['N']} (witness with {len(d['arcs'])} arcs)")
    else:
        print("FAIL:", "; ".join(errs))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
