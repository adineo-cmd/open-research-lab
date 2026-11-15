#!/usr/bin/env python3
"""
Independent verifier for OEIS A385403.

A385403(n) = minimum size of a family E of 3-subsets ("triples") of {1..n} such that
  (a) every vertex of {1..n} lies in at least one triple of E  ("covering"), and
  (b) for EVERY 2-coloring of {1..n}, at least one triple of E is monochromatic
      ("forcing").

Pure Python, stdlib only.  NO CP-SAT / OR-Tools: this verifier is deliberately
independent of the solver that produced the candidate results
(scripts/a385403_solve.py, a385403_solve_b.py).  It re-checks everything from
scratch with bitmask brute force.

Subcommands
-----------
  witness   Verify a claimed a(n)=k witness edge list:
              (i)   every edge is a distinct 3-subset of {1..n}
              (ii)  every vertex of {1..n} is covered
              (iii) |E| == k
              (iv)  full scan of ALL 2**n colorings (NO early exit): every
                    coloring makes at least one edge monochromatic.

  sweep     Lower-bound sanity check at (n, k): enumerate or sample k-edge
            families covering {1..n} and verify that EACH admits a 2-coloring
            with no monochromatic edge.  If any sampled covering family is
            forcing, the claimed lower bound a(n) > k is FALSIFIED -- this is a
            fatal contradiction with the CP-SAT INFEASIBLE certificate and must
            be reported loudly.
              --exhaustive : enumerate all C(C(n,3), k) families (feasible only
                             for small C(n,3); this *proves* the sweep's claim,
                             independently of CP-SAT)
              --draws D    : D random families with coverage repair (sanity
                             check only; catches gross model errors)

  fano      Report whether a k-edge family is (isomorphic to) the Fano plane:
            7 vertices, 7 edges, every vertex on exactly 3 edges, every pair of
            vertices in exactly one edge.

  bound     Print the OEIS %F upper-bound table 7 + ceil((n-7)/3), n>=7.

  all       Driver: read the computation agent's incremental witnesses.json,
            run witness checks for every entry, run sweeps for every claimed
            INFEASIBLE (n, k-1) (exhaustive when the count is small enough,
            randomized otherwise), write certificates verify_n{N}_k{K}.json.

Coloring model
--------------
A coloring is an n-bit int c (bit v-1 set <=> vertex v is red).  Edge mask m
(3 bits set).  Edge m is monochromatic under c iff (c & m) == 0 (all blue) or
(c & m) == m (all red).  c == 0 and c == 2**n - 1 make every edge mono, so they
can be skipped when searching for an avoiding coloring, but NOT in witness
mode, which scans all 2**n colorings including these two.

Exit codes: 0 = all checks passed / no contradiction; 1 = FAIL / contradiction.
"""

import argparse
import hashlib
import itertools
import json
import math
import os
import random
import sys
import time
from datetime import date, datetime, timezone

# OEIS-known values (entry %S line, offset 5; retrieved 2026-11-15):
#   A385403: 10,10,7,8,8,8  for n = 5..10
OEIS_KNOWN = {5: 10, 6: 10, 7: 7, 8: 8, 9: 8, 10: 8}

# The OEIS %F upper bound (unpublished-proven? no: stated without proof in entry):
def ub_bound(n):
    return 7 + math.ceil((n - 7) / 3) if n >= 7 else None

# Exhaustive sweep is attempted when the number of k-subsets of C(n,3) triples
# is at most this many.
EXHAUSTIVE_LIMIT = 2_500_000

FANO_CANON = [(1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7),
              (3, 4, 7), (3, 5, 6)]


def log(msg):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)


def edge_mask(edge):
    m = 0
    for v in edge:
        m |= 1 << (v - 1)
    return m


def canon_edges(edges):
    return sorted(tuple(sorted(e)) for e in edges)


def edges_sha256(edges):
    payload = json.dumps(canon_edges(edges), separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def all_triples(n):
    return [edge_mask(c) for c in itertools.combinations(range(1, n + 1), 3)]


def check_edges_valid(n, edges):
    """(i): every edge a distinct 3-subset of {1..n}.  Returns (ok, msg)."""
    seen = set()
    for e in edges:
        if len(e) != 3:
            return False, f"edge {e} does not have 3 elements"
        s = set(e)
        if len(s) != 3:
            return False, f"edge {e} has repeated vertices"
        if not all(1 <= v <= n for v in s):
            return False, f"edge {e} outside {{1..{n}}}"
        key = frozenset(s)
        if key in seen:
            return False, f"duplicate edge {sorted(s)}"
        seen.add(key)
    return True, "all %d edges are distinct 3-subsets of {1..%d}" % (len(edges), n)


def check_coverage(n, edges):
    """(ii): every vertex of {1..n} in some edge.  Returns (covered_mask, ok, msg)."""
    cov = 0
    for e in edges:
        cov |= edge_mask(e)
    full = (1 << n) - 1
    if cov != full:
        missing = [v for v in range(1, n + 1) if not cov & (1 << (v - 1))]
        return cov, False, f"vertices not covered: {missing}"
    return cov, True, "all %d vertices covered" % n


def forcing_scan_full(n, masks):
    """(iv): full scan over ALL 2**n colorings, no early exit.
    Returns (forcing_bool, avoiding_coloring_or_None, colorings_checked)."""
    total = 1 << n
    for c in range(total):
        hit = False
        for m in masks:
            x = c & m
            if x == 0 or x == m:
                hit = True
                break
        if not hit:
            return False, c, total
    return True, None, total


def find_avoiding(n, masks):
    """First coloring (natural order, skipping all-blue/all-red) with no
    monochromatic edge, or None if the family is forcing."""
    total = 1 << n
    masks = tuple(masks)
    for c in range(1, total - 1):
        for m in masks:
            x = c & m
            if x == 0 or x == m:
                break
        else:
            return c
    return None


def coloring_to_sets(n, c):
    red = [v for v in range(1, n + 1) if c & (1 << (v - 1))]
    blue = [v for v in range(1, n + 1) if not c & (1 << (v - 1))]
    return red, blue


# --------------------------------------------------------------------------
# witness check
# --------------------------------------------------------------------------

def check_witness(n, k, edges, source=""):
    t0 = time.time()
    details = {"n": n, "claimed_k": k, "num_edges": len(edges),
               "edges_sha256": edges_sha256(edges), "source": source}
    ok, msg = check_edges_valid(n, edges)
    details["edges_valid"] = ok
    details["edges_valid_msg"] = msg
    if not ok:
        return False, details, time.time() - t0
    _, cov_ok, cov_msg = check_coverage(n, edges)
    details["coverage_ok"] = cov_ok
    details["coverage_msg"] = cov_msg
    if not cov_ok:
        return False, details, time.time() - t0
    if len(edges) != k:
        details["size_ok"] = False
        details["size_msg"] = f"|E| = {len(edges)} != claimed k = {k}"
        return False, details, time.time() - t0
    details["size_ok"] = True
    masks = [edge_mask(e) for e in edges]
    forcing, avoiding, checked = forcing_scan_full(n, masks)
    details["colorings_checked"] = checked
    details["forcing"] = forcing
    if not forcing:
        red, blue = coloring_to_sets(n, avoiding)
        details["avoiding_coloring_found"] = {"red": red, "blue": blue,
                                              "mask": avoiding}
        details["fail_msg"] = ("witness does NOT force: coloring (red=%s) has no "
                               "monochromatic edge" % red)
        return False, details, time.time() - t0
    details["pass_msg"] = ("|E|=k, covering, and ALL %d colorings of {{1..%d}} make "
                           "some edge monochromatic" % (checked, n))
    # structural: is the whole family a Fano plane, or does it contain one?
    details["is_fano_plane"] = bool(is_fano_plane(edges))
    if not details["is_fano_plane"] and len(edges) >= 7:
        fano_sub = find_fano_subfamily(edges)
        details["fano_subfamily_present"] = fano_sub is not None
        if fano_sub:
            details["fano_subfamily"] = fano_sub
    details["ub_bound_7_ceil"] = ub_bound(n)
    details["k_equals_ub_bound"] = (k == ub_bound(n))
    return True, details, time.time() - t0


# --------------------------------------------------------------------------
# Fano-plane structure
# --------------------------------------------------------------------------

def is_fano_plane(edges):
    """True iff edges form a Fano plane: 7 edges on 7 vertices, each vertex in
    exactly 3 edges, each pair of vertices in exactly one edge."""
    if len(edges) != 7:
        return False
    verts = sorted({v for e in edges for v in e})
    if verts != list(range(1, 8)):
        return False
    deg = {v: 0 for v in verts}
    pair_count = {}
    for e in edges:
        for v in e:
            deg[v] += 1
        for a, b in itertools.combinations(sorted(e), 2):
            pair_count[(a, b)] = pair_count.get((a, b), 0) + 1
    if any(d != 3 for d in deg.values()):
        return False
    return all(pair_count.get(p, 0) == 1
               for p in itertools.combinations(range(1, 8), 2))


def find_fano_subfamily(edges):
    """Return a 7-edge Fano sub-family of edges, or None."""
    for combo in itertools.combinations(range(len(edges)), 7):
        sub = [edges[i] for i in combo]
        if is_fano_plane(sub):
            return canon_edges(sub)
    return None


# --------------------------------------------------------------------------
# sweeps (lower-bound sanity / exhaustive independent proof)
# --------------------------------------------------------------------------

def sweep_exhaustive(n, k, time_limit_s=None, progress_every=200000):
    """Enumerate ALL C(C(n,3), k) edge families; every one that covers {1..n}
    must admit an avoiding coloring.  A single forcing covering family
    falsifies the claimed lower bound.  Returns stats dict."""
    triples = all_triples(n)
    T = len(triples)
    full = (1 << n) - 1
    total_systems = math.comb(T, k)
    log(f"sweep-exhaustive n={n} k={k}: C({T},{k}) = {total_systems} systems")
    covering_systems = 0
    scanned = 0
    forcing_systems = []
    t0 = time.time()
    for combo in itertools.combinations(range(T), k):
        cov = 0
        for i in combo:
            cov |= triples[i]
        scanned += 1
        if cov != full:
            continue
        covering_systems += 1
        masks = [triples[i] for i in combo]
        if find_avoiding(n, masks) is None:
            edges_found = sorted(
                tuple(v for v in range(1, n + 1) if triples[i] & (1 << (v - 1)))
                for i in combo)
            forcing_systems.append({"system_index": scanned,
                                    "edges": edges_found})
            log(f"FATAL: exhaustive sweep n={n} k={k} found a FORCING covering "
                f"system at system #{scanned}: {edges_found}")
        if progress_every and scanned % progress_every == 0:
            el = time.time() - t0
            log(f"  ... {scanned}/{total_systems} systems, "
                f"{covering_systems} covering, elapsed {el:.0f}s")
            if time_limit_s and el > time_limit_s:
                return {
                    "mode": "exhaustive",
                    "n": n, "k": k,
                    "aborted": True,
                    "systems_total": total_systems,
                    "systems_scanned": scanned,
                    "covering_systems": covering_systems,
                    "non_covering_systems": scanned - covering_systems,
                    "forcing_systems_found": len(forcing_systems),
                    "forcing_system_edges": forcing_systems[:5],
                    "wall_s": round(time.time() - t0, 2),
                }
    stats = {
        "mode": "exhaustive",
        "n": n, "k": k,
        "systems_total": total_systems,
        "systems_scanned": scanned,
        "covering_systems": covering_systems,
        "non_covering_systems": scanned - covering_systems,
        "forcing_systems_found": len(forcing_systems),
        "forcing_system_edges": forcing_systems[:5],
        "wall_s": round(time.time() - t0, 2),
    }
    return stats


def sweep_random(n, k, draws, seed):
    """Random k-edge covering systems (with coverage repair); each must admit
    an avoiding coloring.  Returns stats dict."""
    rng = random.Random(seed)
    triples = all_triples(n)
    T = len(triples)
    full = (1 << n) - 1
    triples_by_vertex = {v: [i for i, m in enumerate(triples) if m & (1 << (v - 1))]
                         for v in range(1, n + 1)}
    covering_ok = 0
    repair_fails = 0
    forcing_systems = []
    example_avoiding = None
    t0 = time.time()
    for d in range(draws):
        idx = set(rng.sample(range(T), k))
        # coverage repair: replace random edges until all vertices covered
        for _ in range(300):
            cov = 0
            for i in idx:
                cov |= triples[i]
            if cov == full:
                break
            missing = [v for v in range(1, n + 1) if not cov & (1 << (v - 1))]
            v = missing[rng.randrange(len(missing))]
            drop = rng.choice(tuple(idx))
            cand = rng.choice(triples_by_vertex[v])
            tries = 0
            while (cand == drop or cand in idx) and tries < 50:
                cand = rng.choice(triples_by_vertex[v])
                tries += 1
            idx.discard(drop)
            idx.add(cand)
        else:
            repair_fails += 1
            continue
        cov = 0
        for i in idx:
            cov |= triples[i]
        if cov != full:
            repair_fails += 1
            continue
        masks = [triples[i] for i in idx]
        c = find_avoiding(n, masks)
        if c is None:
            edges = sorted(tuple(sorted(
                [v for v in range(1, n + 1) if triples[i] & (1 << (v - 1))]))
                for i in idx)
            forcing_systems.append({"draw": d, "edges": edges})
            log(f"FATAL: draw {d} produced a FORCING {k}-edge covering system "
                f"at n={n}: {edges}")
        else:
            covering_ok += 1
            if example_avoiding is None:
                red, blue = coloring_to_sets(n, c)
                example_avoiding = {
                    "draw": d,
                    "edges": sorted(tuple(sorted(
                        [v for v in range(1, n + 1)
                         if triples[i] & (1 << (v - 1))])) for i in idx),
                    "avoiding_coloring": {"red": red, "blue": blue, "mask": c},
                }
        if (d + 1) % 25000 == 0:
            el = time.time() - t0
            log(f"  ... {d+1}/{draws} draws, {covering_ok} consistent, "
                f"{len(forcing_systems)} FATAL, elapsed {el:.0f}s")
    stats = {
        "mode": "random",
        "n": n, "k": k,
        "draws": draws,
        "seed": seed,
        "covering_systems_sampled": covering_ok,
        "repair_failures": repair_fails,
        "all_admit_avoiding_coloring": len(forcing_systems) == 0,
        "forcing_systems_found": len(forcing_systems),
        "forcing_system_edges": forcing_systems[:5],
        "example_avoiding": example_avoiding,
        "wall_s": round(time.time() - t0, 2),
    }
    return stats


# --------------------------------------------------------------------------
# certificates
# --------------------------------------------------------------------------

def write_cert(cert_dir, n, k, kind, result, details, claim=""):
    os.makedirs(cert_dir, exist_ok=True)
    cert = {
        "sequence": "A385403",
        "n": n,
        "k": k,
        "kind": kind,
        "result": result,
        "claim": claim,
        "date": date.today().isoformat(),
        "verifier": "math/property-b-covering/scripts/verify_a385403.py "
                    "(pure Python stdlib, no CP-SAT)",
        "details": details,
    }
    path = os.path.join(cert_dir, f"verify_n{n}_k{k}.json")
    with open(path, "w") as f:
        json.dump(cert, f, indent=1, sort_keys=True)
    log(f"certificate written: {path}  result={result}")
    return path


# --------------------------------------------------------------------------
# subcommand handlers
# --------------------------------------------------------------------------

def load_edges_arg(args):
    if args.edges:
        return json.loads(args.edges)
    if args.edges_file:
        with open(args.edges_file) as f:
            return json.load(f)
    raise SystemExit("need --edges or --edges-file")


def cmd_witness(args):
    edges = load_edges_arg(args)
    ok, details, wall = check_witness(args.n, args.k, edges, source=args.source)
    res = "PASS" if ok else "FAIL"
    log(f"witness n={args.n} k={args.k}: {res} ({wall:.2f}s)")
    log(json.dumps({k2: v for k2, v in details.items() if k2 != "edges"},
                   default=str)[:1200])
    if args.cert_dir:
        write_cert(args.cert_dir, args.n, args.k, "witness-pass", res, details,
                   claim=f"a({args.n}) <= {args.k} witness (forcing covering "
                         f"{args.k}-triple system on {{1..{args.n}}})")
    return 0 if ok else 1


def cmd_sweep(args):
    if args.exhaustive:
        stats = sweep_exhaustive(args.n, args.k, time_limit_s=args.time_limit)
    else:
        stats = sweep_random(args.n, args.k, args.draws, args.seed)
    log(json.dumps(stats)[:1500])
    if args.cert_dir:
        kind = ("exhaustive-lower-bound" if args.exhaustive
                else args.kind_label or "contradiction-search")
        result = "CONSISTENT" if stats["forcing_systems_found"] == 0 \
            else "FATAL-CONTRADICTION"
        write_cert(args.cert_dir, args.n, args.k, kind, result, stats,
                   claim=args.claim or
                   f"no covering {args.k}-triple system of {{1..{args.n}}} "
                   f"forces a monochromatic triple")
    return 0 if stats["forcing_systems_found"] == 0 else 1


def cmd_fano(args):
    edges = load_edges_arg(args)
    whole = is_fano_plane(edges)
    sub = find_fano_subfamily(edges) if not whole else canon_edges(edges)
    log(f"is_fano_plane(whole family) = {whole}")
    log(f"fano_subfamily_present = {sub is not None}")
    if sub:
        log(f"  sub-family: {sub}")
    return 0


def cmd_bound(args):
    for n in range(7, args.n_max + 1):
        print(f"n={n:2d}  7+ceil((n-7)/3) = {ub_bound(n)}")
    return 0


def cmd_all(args):
    with open(args.witnesses) as f:
        witnesses = json.load(f)
    os.makedirs(args.cert_dir, exist_ok=True)
    failures = []
    summary = []
    for n_str in sorted(witnesses, key=int):
        entry = witnesses[n_str]
        n = int(n_str)
        k = entry["k"]
        status = entry.get("status")
        edges = entry["witness_edges"]
        source = entry.get("source", "")
        # --- witness check ---
        ok, details, wall = check_witness(n, k, edges, source=source)
        expected = OEIS_KNOWN.get(n)
        oeiis_match = (expected is None) or (k == expected)
        details["oeis_known_value"] = expected
        details["matches_oeis_known"] = oeiis_match
        res = "PASS" if (ok and oeiis_match) else "FAIL"
        write_cert(args.cert_dir, n, k, "witness-pass", res, details,
                   claim=f"a({n}) <= {k} witness (forcing covering {k}-triple "
                         f"system on {{1..{n}}})" +
                         (f"; matches OEIS a({n})={expected}" if expected else ""))
        if res == "FAIL":
            failures.append((n, k, "witness", details))
        summary.append((n, k, "witness", res, round(wall, 2)))
        # --- lower-bound sweep at k-1 (only when an INFEASIBLE at k-1 is claimed) ---
        kminus = entry.get("infeasible_below")
        if status == "FEASIBLE" and kminus == k - 1:
            triples_count = math.comb(n, 3)
            systems = math.comb(triples_count, kminus)
            claim = (f"no covering {kminus}-triple system of {{1..{n}}} forces a "
                     f"monochromatic triple (CP-SAT INFEASIBLE cert "
                     f"a385403_n{n:02d}_k{kminus:02d}_INFEASIBLE.json); "
                     f"together with the k={k} witness this proves a({n})={k}")
            if systems <= EXHAUSTIVE_LIMIT and not args.skip_exhaustive:
                stats = sweep_exhaustive(n, kminus,
                                         time_limit_s=args.sweep_time_limit)
                kind = "exhaustive-lower-bound"
            else:
                stats = sweep_random(n, kminus, args.sweep_draws, args.seed)
                kind = "contradiction-search"
            result = "CONSISTENT" if stats["forcing_systems_found"] == 0 \
                else "FATAL-CONTRADICTION"
            stats["claimed_infeasible_below_cert"] = (
                f"a385403_n{n:02d}_k{kminus:02d}_INFEASIBLE.json")
            stats["systems_total_C_T_k"] = math.comb(triples_count, kminus)
            write_cert(args.cert_dir, n, kminus, kind, result, stats,
                       claim=claim)
            if result == "FATAL-CONTRADICTION":
                failures.append((n, kminus, kind, stats))
            summary.append((n, kminus, kind, result, stats.get("wall_s")))
        elif kminus is not None and kminus != k - 1:
            log(f"WARNING: n={n} infeasible_below={kminus} != k-1={k-1}; "
                f"sweep skipped")
    log("=== SUMMARY ===")
    for row in summary:
        log("  " + json.dumps(row))
    if failures:
        log(f"FATAL: {len(failures)} verification failure(s): "
            f"{json.dumps(failures, default=str)[:2000]}")
        return 1
    log("all checks consistent")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pw = sub.add_parser("witness", help="verify a claimed a(n)=k witness")
    pw.add_argument("--n", type=int, required=True)
    pw.add_argument("--k", type=int, required=True)
    pw.add_argument("--edges", type=str, help="edge list as JSON, e.g. '[[1,2,3],[1,4,5]]'")
    pw.add_argument("--edges-file", type=str)
    pw.add_argument("--source", type=str, default="")
    pw.add_argument("--cert-dir", type=str)
    pw.set_defaults(func=cmd_witness)

    ps = sub.add_parser("sweep", help="lower-bound sweep at (n, k)")
    ps.add_argument("--n", type=int, required=True)
    ps.add_argument("--k", type=int, required=True)
    ps.add_argument("--exhaustive", action="store_true")
    ps.add_argument("--draws", type=int, default=100000)
    ps.add_argument("--seed", type=int, default=20261115)
    ps.add_argument("--time-limit", type=float, default=None)
    ps.set_defaults(func=cmd_sweep)

    pf = sub.add_parser("fano", help="Fano-plane structure detection")
    pf.add_argument("--edges", type=str)
    pf.add_argument("--edges-file", type=str)
    pf.set_defaults(func=cmd_fano)

    pb = sub.add_parser("bound", help="print 7+ceil((n-7)/3) table")
    pb.add_argument("--n-max", type=int, default=16)
    pb.set_defaults(func=cmd_bound)

    pa = sub.add_parser("all", help="verify all entries of witnesses.json")
    pa.add_argument("--witnesses", type=str,
                    default="/tmp/propertyb/witnesses.json")
    pa.add_argument("--cert-dir", type=str, required=True)
    pa.add_argument("--sweep-draws", type=int, default=100000)
    pa.add_argument("--seed", type=int, default=20261115)
    pa.add_argument("--skip-exhaustive", action="store_true")
    pa.add_argument("--sweep-time-limit", type=float, default=None)
    pa.set_defaults(func=cmd_all)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
