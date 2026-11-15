#!/usr/bin/env python3
"""
A385403 computation agent.

a(n) = minimum number of triples (3-subsets) that cover {1..n} such that every
2-coloring of {1..n} yields at least one monochromatic triple.

Exact CP-SAT model, for edge budget k:
  variables: s_t in {0,1} for every 3-subset t of {1..n}
  (1) sum_t s_t = k
  (2) coverage: for each vertex v, sum_{t contains v} s_t >= 1
  (3) hitting: for every 2-coloring c of {1..n},
        sum_{t monochromatic under c} s_t >= 1
A triple t is monochromatic under c iff all 3 of its vertices get the same color.

Model form:
  - "full":     constraints (3) for all 2^n colorings      (used for n <= 13)
  - "halved":   constraints (3) for the 2^(n-1) colorings with vertex 1 = red
                (exact: mono-triple sets are invariant under complementing all
                colors, so every coloring is represented by its complement-
                canonical form).  Used for n >= 14.

a(n) is settled per n by proving INFEASIBLE at k-1 (lower bound) and FEASIBLE
at k (witness).  Status INFEASIBLE from CP-SAT is a proof; status FEASIBLE
comes with a witness that is independently re-verified by brute force over
all 2^n colorings before it is written to any certificate.

Certificates: results/certificates/a385403_n{nn}_k{kk}_{STATUS}.json
Session log : results/certificates/a385403_session.json
Witness map : /tmp/propertyb/witnesses.json   (n -> witness edges, incremental)
"""

import argparse
import datetime
import itertools
import json
import os
import sys
import time
from importlib.metadata import version as _pkg_version

from ortools.sat.python import cp_model

REPO_DIR = "/home/aditya/repos/open-research-lab/math/property-b-covering"
CERT_DIR = os.path.join(REPO_DIR, "results", "certificates")
TMP_DIR = "/tmp/propertyb"
WITNESS_FILE = os.path.join(TMP_DIR, "witnesses.json")
SESSION_FILE = os.path.join(CERT_DIR, "a385403_session.json")

TOOL = f"ortools CP-SAT { _pkg_version('ortools') } (python)"
DATE = datetime.date.today().isoformat()

# Canonical Fano plane on {1..7} (every pair covered exactly once; not 2-colorable).
FANO = [(1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 5, 6)]

# Known published values (offset 5), used for the mandatory validation phase.
KNOWN = {5: 10, 6: 10, 7: 7, 8: 8, 9: 8, 10: 8}


def conjecture_bound(n):
    """%F upper bound: a(n) <= 7 + ceil((n-7)/3) for n >= 7."""
    return 7 + (n - 5) // 3  # == 7 + ceil((n-7)/3) for n >= 7


def construction(n):
    """Fano plane on {1..7} + groups-of-3 cover of {8..n}.
    Achieves k = 7 + ceil((n-7)/3) edges covering all of {1..n}."""
    edges = [tuple(e) for e in FANO]
    rest = list(range(8, n + 1))
    i = 0
    while i < len(rest):
        chunk = rest[i:i + 3]
        if len(chunk) == 3:
            edges.append((chunk[0], chunk[1], chunk[2]))
        elif len(chunk) == 2:
            edges.append((1, chunk[0], chunk[1]))
        else:  # single leftover vertex
            edges.append((1, 2, chunk[0]))
        i += 3
    return edges


def verify_witness(n, edges):
    """Brute-force check: edges cover {1..n} and hit the mono triples of ALL
    2^n colorings.  Returns (ok, message)."""
    if len(set(frozenset(e) for e in edges)) != len(edges):
        return False, "duplicate edges"
    if len(edges) == 0:
        return False, "empty edge list"
    full = (1 << n) - 1
    masks = []
    for e in edges:
        if len(set(e)) != 3 or not all(1 <= x <= n for x in e):
            return False, f"bad triple {e}"
        m = (1 << (e[0] - 1)) | (1 << (e[1] - 1)) | (1 << (e[2] - 1))
        masks.append(m)
    cov = 0
    for m in masks:
        cov |= m
    if cov != full:
        return False, "edges do not cover {1..n}"
    for col in range(1 << n):
        hit = False
        for m in masks:
            x = m & col
            if x == 0 or x == m:
                hit = True
                break
        if not hit:
            return False, f"coloring {col:0{n}b} has no monochromatic chosen triple"
    return True, "ok"


def build_model(n, k, halved, hint_edges=None):
    """Build the exact CP-SAT model for (n, k)."""
    trips = list(itertools.combinations(range(1, n + 1), 3))
    T = len(trips)
    tmask = [(1 << (a - 1)) | (1 << (b - 1)) | (1 << (c - 1)) for a, b, c in trips]
    full = (1 << n) - 1

    model = cp_model.CpModel()
    s = [model.new_bool_var(f"s_{i}") for i in range(T)]

    # (1) edge budget
    model.add(sum(s) == k)
    # (2) coverage
    for v in range(1, n + 1):
        idx = [i for i, t in enumerate(trips) if v in t]
        model.add(sum(s[i] for i in idx) >= 1)

    # (3) hitting constraints over the chosen coloring set
    if halved:
        colors = range(1, 1 << n, 2)  # vertex 1 (bit 0) red
    else:
        colors = range(1 << n)
    n_con = 0
    for col in colors:
        comp = full ^ col
        idx = [i for i in range(T)
               if (tmask[i] & col) == tmask[i] or (tmask[i] & comp) == tmask[i]]
        model.add(sum(s[i] for i in idx) >= 1)
        n_con += 1

    if hint_edges is not None:
        hint_set = {frozenset(e) for e in hint_edges}
        for i, t in enumerate(trips):
            model.add_hint(s[i], 1 if frozenset(t) in hint_set else 0)

    return model, s, trips, n_con


def solve_probe(n, k, halved, tl=300.0, workers=8, seed=42, hint_edges=None):
    """One feasibility probe.  Returns dict with status/witness/timing."""
    t0 = time.time()
    model, s, trips, n_con = build_model(n, k, halved, hint_edges)
    build_s = time.time() - t0

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed

    t1 = time.time()
    st = solver.solve(model)
    solve_s = time.time() - t1

    if st == cp_model.INFEASIBLE:
        status = "INFEASIBLE"
    elif st in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        status = "FEASIBLE"
    else:
        status = "UNKNOWN"

    witness = None
    if status == "FEASIBLE":
        witness = [list(trips[i]) for i in range(len(trips)) if solver.value(s[i])]

    return {
        "status": status,
        "wall_s": round(time.time() - t0, 2),
        "build_s": round(build_s, 2),
        "solve_s": round(solve_s, 2),
        "witness": witness,
        "n_vars": len(trips),
        "n_coloring_constraints": n_con,
    }


# ---------------------------------------------------------------- bookkeeping

def cert_path(n, k, status):
    return os.path.join(CERT_DIR, f"a385403_n{n:02d}_k{k:02d}_{status}.json")


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def atomic_write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def update_witnesses(best):
    """best: dict n(str) -> edges (current best/only witness per n)."""
    atomic_write_json(WITNESS_FILE, {n: best[n] for n in sorted(best, key=int)})


def update_session(session):
    atomic_write_json(SESSION_FILE, session)


def record_run(run, session, best_witness):
    """Write certificate JSON + update session + witnesses (if FEASIBLE)."""
    n, k, status = run["n"], run["k"], run["status"]
    cert = {
        "n": n,
        "k": k,
        "status": status,
        "wall_s": run["wall_s"],
        "workers": run["workers"],
        "seed": run["seed"],
        "model_form": run["model_form"],
        "claim": run["claim"],
        "date": DATE,
        "tool": TOOL,
        # extras
        "phase": run["phase"],
        "conjecture_bound": run.get("conjecture_bound"),
        "expected": run.get("expected"),
        "matches_conjecture": run.get("matches_conjecture"),
        "verified": run.get("verified"),
        "verify_msg": run.get("verify_msg"),
        "n_vars": run.get("n_vars"),
        "n_coloring_constraints": run.get("n_coloring_constraints"),
        "build_s": run.get("build_s"),
        "solve_s": run.get("solve_s"),
        "retries": run.get("retries", []),
    }
    if status == "FEASIBLE" and run.get("witness") is not None:
        cert["witness_edges"] = run["witness"]
    atomic_write_json(cert_path(n, k, status), cert)

    session["runs"].append({key: cert[key] for key in (
        "n", "k", "status", "wall_s", "model_form", "claim", "verified")})
    update_session(session)

    if status == "FEASIBLE" and run.get("verified"):
        prev = best_witness.get(str(n))
        if prev is None or k < prev[0]:
            best_witness[str(n)] = (k, run["witness"])
        update_witnesses({nn: w[1] for nn, w in best_witness.items()})


# ------------------------------------------------------------------- phases

def probe_with_retry(n, k, halved, session, best_witness, phase, expected,
                     claim, tl, workers, seed, hint=None, conjecture=None):
    """Run a probe; if UNKNOWN, retry once with a different seed and 2x time.
    Records a certificate for the decisive run."""
    tries = []
    attempt = dict(halved=halved, tl=tl, seed=seed, hint=hint)
    for attempt_no in range(2):
        res = solve_probe(n, k, attempt["halved"], attempt["tl"], workers,
                          attempt["seed"], attempt["hint"])
        tries.append({"model_form": "halved" if attempt["halved"] else "full",
                      "tl": attempt["tl"], "seed": attempt["seed"],
                      "status": res["status"], "wall_s": res["wall_s"]})
        if res["status"] != "UNKNOWN":
            break
        # retry with different seed, doubled time limit
        attempt = dict(halved=attempt["halved"], tl=min(2 * attempt["tl"], 900),
                       seed=seed + 100 * (attempt_no + 1), hint=attempt["hint"])

    model_form = "halved" if attempt["halved"] else "full"
    verified = verify_msg = None
    if res["status"] == "FEASIBLE" and res["witness"] is not None:
        verified, verify_msg = verify_witness(n, res["witness"])
        if not verified:
            print(f"!! WITNESS INVALID at n={n} k={k}: {verify_msg}", flush=True)

    matches = None
    if conjecture is not None:
        matches = {"INFEASIBLE": (k == conjecture - 1),
                   "FEASIBLE": (k == conjecture)}.get(res["status"])

    run = {
        "n": n, "k": k, "status": res["status"], "wall_s": res["wall_s"],
        "build_s": res["build_s"], "solve_s": res["solve_s"],
        "workers": workers, "seed": attempt["seed"],
        "model_form": model_form, "witness": res["witness"],
        "n_vars": res["n_vars"], "n_coloring_constraints": res["n_coloring_constraints"],
        "phase": phase, "expected": expected, "claim": claim,
        "conjecture_bound": conjecture, "matches_conjecture": matches,
        "verified": verified, "verify_msg": verify_msg, "retries": tries[:-1],
    }
    record_run(run, session, best_witness)
    print(f"[cert] n={n} k={k} -> {res['status']} "
          f"(wall {res['wall_s']}s, build {res['build_s']}s, solve {res['solve_s']}s, "
          f"{model_form}, vars={res['n_vars']}, colorings={res['n_coloring_constraints']}"
          + (f", witness verified: {verify_msg}" if verified is not None else "")
          + ")", flush=True)
    return run


def run_validation(session, best_witness, tl, workers):
    """Mandatory: reproduce the six known values a(5..10)."""
    print("=== VALIDATION PHASE (known values must be reproduced) ===", flush=True)
    session["validation"] = []
    ok_all = True
    for n in (5, 6, 7, 8, 9, 10):
        a = KNOWN[n]
        r_lo = probe_with_retry(
            n, a - 1, halved=False, session=session, best_witness=best_witness,
            phase="validation", expected="INFEASIBLE",
            claim=f"a({n}) >= {a}: no covering {a-1}-triple-system of {{1..{n}}} "
                  f"forces a mono triple (published a({n})={a})",
            tl=tl, workers=workers, seed=42)
        r_hi = probe_with_retry(
            n, a, halved=False, session=session, best_witness=best_witness,
            phase="validation", expected="FEASIBLE",
            claim=f"a({n}) <= {a}: witness covering {a}-triple-system "
                  f"(published a({n})={a})",
            tl=tl, workers=workers, seed=42, hint=construction(n))
        ok = (r_lo["status"] == "INFEASIBLE" and r_hi["status"] == "FEASIBLE")
        ok_all = ok_all and ok
        session["validation"].append({
            "n": n, "known_a": a,
            "k=a-1": r_lo["status"], "k=a": r_hi["status"],
            "ok": ok, "wall_s_lo": r_lo["wall_s"], "wall_s_hi": r_hi["wall_s"]})
        update_session(session)
        print(f"[validate] a({n})={a}: k={a}-1 -> {r_lo['status']} "
              f"({r_lo['wall_s']}s), k={a} -> {r_hi['status']} ({r_hi['wall_s']}s) "
              f"{'OK' if ok else 'MISMATCH'}", flush=True)
    update_session(session)
    if not ok_all:
        print("!! VALIDATION FAILED: known values not reproduced. STOP.", flush=True)
        sys.exit(2)
    print("=== VALIDATION PASSED ===", flush=True)


def run_new_terms(nmin, nmax, session, best_witness, tl, workers):
    """Settle a(n) for n = nmin..nmax against the conjecture bound."""
    print(f"=== NEW TERMS n={nmin}..{nmax} ===", flush=True)
    for n in range(nmin, nmax + 1):
        bound = conjecture_bound(n)
        halved = n >= 14  # documented choice: halved (exact) formulation for n >= 14
        print(f"--- n={n}: conjecture a({n}) = {bound} "
              f"(model_form={'halved' if halved else 'full'}) ---", flush=True)

        # lower bound: prove INFEASIBLE at bound-1
        k = bound - 1
        r_lo = probe_with_retry(
            n, k, halved=halved, session=session, best_witness=best_witness,
            phase="new", expected="INFEASIBLE",
            claim=f"a({n}) >= {bound}: no covering {k}-triple-system of {{1..{n}}} "
                  f"forces a mono triple (conjecture lower bound)",
            tl=tl, workers=workers, seed=42, conjecture=bound)

        value = None
        if r_lo["status"] == "INFEASIBLE":
            value = bound
        elif r_lo["status"] == "FEASIBLE":
            print(f"!!! CONJECTURE VIOLATED at n={n}: FEASIBLE at k={bound-1} < "
                  f"bound {bound}. Searching downward for the true value...",
                  flush=True)
            value = bound - 1
            while value > 7:
                k2 = value - 1
                r2 = probe_with_retry(
                    n, k2, halved=halved, session=session, best_witness=best_witness,
                    phase="new", expected="INFEASIBLE",
                    claim=f"a({n}) >= {value} probe at k={k2} (conjecture violated "
                          f"at n={n}, seeking true value)",
                    tl=tl, workers=workers, seed=42, conjecture=bound)
                if r2["status"] == "INFEASIBLE":
                    break
                if r2["status"] == "FEASIBLE":
                    value -= 1
                    continue
                value = None  # UNKNOWN: cannot decide
                break
        else:
            print(f"!! lower probe UNKNOWN at n={n} k={bound-1}; no value claim.",
                  flush=True)

        # upper bound: FEASIBLE at value (witness mandatory)
        if value is not None:
            r_hi = probe_with_retry(
                n, value, halved=halved, session=session, best_witness=best_witness,
                phase="new", expected="FEASIBLE",
                claim=f"a({n}) <= {value}: witness covering {value}-triple-system"
                      + (f"; together with INFEASIBLE at {value-1} this proves "
                         f"a({n}) = {value}" if r_lo["status"] == "INFEASIBLE"
                         else ""),
                tl=tl, workers=workers, seed=42, hint=construction(n),
                conjecture=bound)
            if not r_hi["verified"]:
                print(f"!! witness at n={n} k={value} FAILED verification; "
                      f"no value claim.", flush=True)
                value = None
            if r_hi["status"] != "FEASIBLE":
                print(f"!! upper probe at n={n} k={value} returned "
                      f"{r_hi['status']} (construction should be feasible); "
                      f"no value claim.", flush=True)
                value = None

        if value is not None:
            src = ("proved (INFEASIBLE at value-1 + FEASIBLE at value)"
                   if r_lo["status"] == "INFEASIBLE" else "witness only (conjecture violated)")
            entry = {"n": n, "a_n": value, "conjecture": bound,
                     "matches_conjecture": value == bound, "how": src,
                     "wall_s_lower_probe": r_lo["wall_s"]}
            session["results"] = [x for x in session.get("results", []) if x["n"] != n]
            session["results"].append(entry)
            update_session(session)
            flag = "" if value == bound else "  <<< CONJECTURE VIOLATED"
            print(f"[value] a({n}) = {value} (conjecture {bound}) "
                  f"[{src}]{flag}", flush=True)
        update_session(session)
    print("=== NEW TERMS DONE ===", flush=True)


def main():
    ap = argparse.ArgumentParser(description="A385403 CP-SAT solver")
    ap.add_argument("phase", choices=["validate", "newterms", "probe"])
    ap.add_argument("--nmin", type=int, default=11)
    ap.add_argument("--nmax", type=int, default=16)
    ap.add_argument("--n", type=int)
    ap.add_argument("--k", type=int)
    ap.add_argument("--halved", action="store_true")
    ap.add_argument("--tl", type=float, default=300.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(CERT_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)

    session = load_json(SESSION_FILE, {
        "task": "OEIS A385403 - min triples covering {1..n} forcing a mono triple "
                "under every 2-coloring (non-2-colorable covering 3-graphs)",
        "date": DATE, "tool": TOOL,
        "model": "CP-SAT: s_t binary for each 3-subset t; sum s_t = k; coverage "
                 "per vertex; hitting constraint sum_{t mono under c} s_t >= 1 for "
                 "every 2-coloring c (full 2^n for n<=13, halved 2^(n-1) with "
                 "vertex 1 fixed red for n>=14 - exact by complement symmetry). "
                 "a(n) = min feasible k, settled by INFEASIBLE at k-1 + FEASIBLE at k.",
        "validation": [], "results": [], "runs": []})
    best_witness = {}
    w = load_json(WITNESS_FILE, {})
    for nn, edges in w.items():
        best_witness[str(nn)] = (len(edges), edges)

    if args.phase == "validate":
        run_validation(session, best_witness, args.tl, args.workers)
    elif args.phase == "newterms":
        run_new_terms(args.nmin, args.nmax, session, best_witness,
                      args.tl, args.workers)
    elif args.phase == "probe":
        assert args.n and args.k
        probe_with_retry(args.n, args.k, args.halved, session, best_witness,
                         phase="adhoc", expected=None,
                         claim=f"adhoc probe n={args.n} k={args.k}",
                         tl=args.tl, workers=args.workers, seed=args.seed)


if __name__ == "__main__":
    main()
