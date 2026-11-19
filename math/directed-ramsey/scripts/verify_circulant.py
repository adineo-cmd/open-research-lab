#!/usr/bin/env python3
"""Solver-independent verifier for circulant directed-Ramsey witnesses.

Pure stdlib.  A certificate with n, m, N and S (connection set on Z_N) is
checked from scratch:
  (i)   S is oriented (S ∩ -S = empty),
  (ii)  no independent n-subset of Z_N,
  (iii) no transitive m-tournament (all m(m-1)/2 forward arcs present under
        some linear order of an m-subset).
PASS proves k(n,m) > N.
"""
import argparse
import itertools
import json
import sys


def verify(d):
    n, m, N, S = d["n"], d["m"], d["N"], set(d["S"])
    errs = []
    if any((N - s) in S for s in S):
        errs.append("S is not oriented (contains a 2-cycle)")
    if any(not (1 <= s <= N - 1) for s in S):

        errs.append("invalid connection offset")

    def arc(u, v):
        return (v - u) % N in S

    for T in itertools.combinations(range(N), n):
        if not any(arc(u, v) or arc(v, u) for u, v in itertools.combinations(T, 2)):
            errs.append(f"independent {n}-set {T}")
            break
    for T in itertools.combinations(range(N), m):
        for order in itertools.permutations(T):
            if all(arc(order[i], order[j])
                   for i in range(m) for j in range(i + 1, m)):
                errs.append(f"transitive {m}-tournament on {T}, order {order}")
                break
        if errs:
            break
    return not errs, errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("certificate")
    a = ap.parse_args()
    d = json.load(open(a.certificate))
    if d.get("status") in ("INFEASIBLE", "UNKNOWN") or "S" not in d:
        print(f"NO-WITNESS: status={d.get('status')} — nothing to verify")
        return 0
    ok, errs = verify(d)
    print(("PASS" if ok else "FAIL") + f": k({d['n']},{d['m']}) > {d['N']}"
          + ("" if ok else " -- " + "; ".join(errs)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
