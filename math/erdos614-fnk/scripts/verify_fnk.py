#!/usr/bin/env python3
"""
Solver-independent verifier for Erdos problem #614 (EP614) certificates.

f(n,k) = min |E(G)| over simple graphs G on n vertices (vertex set {1..n})
such that EVERY (k+2)-vertex subset S induces a subgraph with maximum degree
>= k, i.e. some v in S has at least k neighbours inside S.

Pure Python, standard library only.  NO OR-Tools / CP-SAT: this verifier is
deliberately independent of the solver that produced the certificates
(scripts/fnk_solve.py).  Every OPTIMAL certificate is re-checked from scratch:

  (i)   witness_edges is a list of 2-subsets of {1..n}, no loops, no duplicates
        -> a valid simple graph on exactly n labelled vertices;
  (ii)  |E| == recorded objective value;
  (iii) FULL enumeration of all C(n, k+2) subsets: each must contain a vertex
        of induced degree >= k (no sampling, no early exit on success).

FEASIBLE certificates have no witness, so they are reported as BOUND with the
recorded lower bound (solver BestObjectiveBound); no verification is possible.

The k=1 closed form (f(n,1) = C(n,2) - floor(n^2/4)) is validated against any
k=1 certificates present (see the results doc's claim of fnk_n*_k1.json).

Subcommands
-----------
  one <certificate.json>          verify a single certificate
  all --cert-dir <dir>            verify every fnk_n*_k*.json in <dir>

Exit codes: 0 = no OPTIMAL certificate failed; 1 = at least one OPTIMAL
certificate FAILED (or a malformed/unreadable certificate was encountered).

Rule 0 / prior art (recorded by the subagent, 2026-11-19):
  - websearch "github verify_fnk.py erdos 614 certificate verifier
    solver-independent" and "Erdos 614 f(n,k) graph verifier certificate
    python witness_edges" both failed (HTTP 402, search integration
    unavailable), so no external prior art could be resolved this session.
  - In-repo prior art followed: math/property-b-covering/scripts/verify_a385403.py
    (stdlib-only, full-enumeration, PASS/FAIL, "all" driver, summary table) and
    math/erdos614-fnk/scripts/fnk_solve.py (certificate schema / edge encoding).
  - This file is a NEW artifact; no solver-independent EP614 verifier existed
    in the repo before it.
"""

import argparse
import itertools
import json
import os
import sys
from math import comb


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def f1_closed(n):
    """Known closed form: f(n,1) = C(n,2) - floor(n^2/4)."""
    return comb(n, 2) - (n * n) // 4


def popcount(x):
    """Portable popcount (int.bit_count is not available on older Pythons)."""
    return bin(x).count("1")


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def load_cert(path):
    with open(path) as f:
        return json.load(f)


def build_adjacency(n, edges):
    """Validate witness_edges and return (ok, msg, adj, vertices_used).

    adj[v] is a bitmask of neighbours of v; bit (u-1) denotes vertex u.
    Isolated vertices are allowed: the vertex set is exactly {1..n}.
    """
    if not isinstance(edges, list):
        return False, "witness_edges is not a list", None, set()
    adj = [0] * (n + 1)  # 1-indexed
    seen = set()
    used = set()
    for idx, e in enumerate(edges):
        if not isinstance(e, (list, tuple)) or len(e) != 2:
            return False, "edge #%d is not a 2-element list: %r" % (idx, e), None, set()
        u, v = e
        if not (is_int(u) and is_int(v)):
            return False, "edge #%d has non-integer endpoints: %r" % (idx, e), None, set()
        if u == v:
            return False, "edge #%d is a loop (%d,%d)" % (idx, u, v), None, set()
        if not (1 <= u <= n and 1 <= v <= n):
            return False, ("edge #%d has endpoint outside {1..%d}: %r"
                           % (idx, n, e)), None, set()
        key = (min(u, v), max(u, v))
        if key in seen:
            return False, "duplicate edge %s" % (key,), None, set()
        seen.add(key)
        adj[u] |= 1 << (v - 1)
        adj[v] |= 1 << (u - 1)
        used.add(u)
        used.add(v)
    return True, ("%d distinct edges, valid simple graph on {1..%d} "
                  "(%d vertices incident, %d isolated)"
                  % (len(edges), n, len(used), n - len(used))), adj, used


def check_property(n, k, adj):
    """Full enumeration of all C(n,k+2) subsets.

    Returns (ok, checked, first_bad) where first_bad is
    (subset_tuple, {vertex: induced_degree}) for the first violating subset.
    """
    if k + 2 > n:
        return True, 0, None  # vacuous: no (k+2)-subsets exist
    checked = 0
    for S in itertools.combinations(range(1, n + 1), k + 2):
        smask = 0
        for v in S:
            smask |= 1 << (v - 1)
        degs = {}
        hit = False
        for v in S:
            d = popcount(adj[v] & smask)
            degs[v] = d
            if d >= k:
                hit = True
                break
        checked += 1
        if not hit:
            # recompute all degrees so the diagnostic is complete
            degs = {v: popcount(adj[v] & smask) for v in S}
            return False, checked, (S, degs)
    return True, checked, None


# --------------------------------------------------------------------------
# verification of a single certificate (dict)
# --------------------------------------------------------------------------

def verify_optimal(cert, source=""):
    """Return (pass_bool, details_dict) for an OPTIMAL certificate."""
    n, k = cert.get("n"), cert.get("k")
    d = {"source": source, "n": n, "k": k}
    ok = True

    if not (is_int(n) and is_int(k)):
        return False, {"source": source, "error": "n/k missing or non-integer",
                       "n": n, "k": k}
    if n < 1 or k < 1:
        return False, {"source": source, "error": "n and k must be >= 1",
                       "n": n, "k": k}

    value = cert.get("value")
    d["value"] = value
    if not is_int(value):
        d["error"] = "OPTIMAL certificate has no integer 'value'"
        return False, d

    edges = cert.get("witness_edges")
    graph_ok, gmsg, adj, used = build_adjacency(n, edges)
    d["graph_valid"] = graph_ok
    d["graph_msg"] = gmsg
    if not graph_ok:
        return False, d

    num_edges = len(edges)
    d["num_edges"] = num_edges
    size_ok = (num_edges == value)
    d["size_ok"] = size_ok
    if not size_ok:
        d["size_msg"] = "|E| = %d != recorded value %d" % (num_edges, value)
        ok = False

    prop_ok, checked, first_bad = check_property(n, k, adj)
    d["subsets_checked"] = checked
    d["subsets_expected"] = comb(n, k + 2) if k + 2 <= n else 0
    d["property_ok"] = prop_ok
    if not prop_ok:
        S, degs = first_bad
        d["first_bad_subset"] = list(S)
        d["first_bad_induced_degrees"] = degs
        d["property_msg"] = ("subset %s has all induced degrees %s < k=%d"
                             % (S, degs, k))
        ok = False

    # metadata sanity: the recorded subset count should match C(n,k+2)
    recorded_subsets = cert.get("subsets")
    d["subsets_recorded"] = recorded_subsets
    d["subsets_metadata_ok"] = (recorded_subsets == d["subsets_expected"])
    if not d["subsets_metadata_ok"]:
        d["subsets_metadata_msg"] = ("recorded subsets=%r != C(n,k+2)=%d"
                                     % (recorded_subsets, d["subsets_expected"]))

    # k=1 closed-form cross-check: any OPTIMAL k=1 cert must match the formula
    if k == 1:
        expected = f1_closed(n)
        d["closed_form_expected"] = expected
        cf_ok = (value == expected)
        d["closed_form_ok"] = cf_ok
        if not cf_ok:
            d["closed_form_msg"] = ("value %d != f(n,1)=C(n,2)-floor(n^2/4)=%d"
                                    % (value, expected))
            ok = False

    return ok, d


def verify_cert(cert, source=""):
    """Dispatch by status.  Returns (result_label, details_dict)."""
    status = cert.get("status")
    if status == "OPTIMAL":
        ok, d = verify_optimal(cert, source=source)
        d["status"] = status
        return ("PASS" if ok else "FAIL"), d
    if status == "FEASIBLE":
        d = {"source": source, "n": cert.get("n"), "k": cert.get("k"),
             "status": status, "best_lower_bound": cert.get("best"),
             "note": "no witness: bound only, no verification possible"}
        return "BOUND", d
    # VACUOUS / UNKNOWN / anything else: informational, not a FAIL
    d = {"source": source, "n": cert.get("n"), "k": cert.get("k"),
         "status": status, "note": "non-OPTIMAL status; no property check"}
    return "INFO", d


# --------------------------------------------------------------------------
# subcommands
# --------------------------------------------------------------------------

def cmd_one(args):
    cert = load_cert(args.certificate)
    label, d = verify_cert(cert, source=args.certificate)
    print("== %s == %s" % (os.path.basename(args.certificate), label))
    print(json.dumps(d, indent=2, sort_keys=True, default=str))
    return 1 if label == "FAIL" else 0


def _cert_sort_key(path):
    """Sort fnk_n<K>_k<K>.json by (n, k), then filename."""
    import re
    m = re.search(r"_n(\d+)_k(\d+)\.json$", os.path.basename(path))
    if m:
        return (0, int(m.group(1)), int(m.group(2)), path)
    return (1, 0, 0, path)


def _fmt_row(cells, widths):
    return "  ".join(str(c).ljust(w) for c, w in zip(cells, widths))


def cmd_all(args):
    cert_dir = args.cert_dir
    if not os.path.isdir(cert_dir):
        print("ERROR: cert-dir is not a directory: %s" % cert_dir, file=sys.stderr)
        return 1
    paths = sorted(
        (os.path.join(cert_dir, p) for p in os.listdir(cert_dir)
         if p.startswith("fnk_") and p.endswith(".json")),
        key=_cert_sort_key)
    if not paths:
        print("ERROR: no fnk_*.json certificates found in %s" % cert_dir,
              file=sys.stderr)
        return 1

    results = []  # (basename, n, k, status, label, value_or_bound, detail)
    optimal_failures = []
    k1_rows = []  # (n, basename, expected, recorded, match, property_ok)
    certs_loaded = []

    for path in paths:
        name = os.path.basename(path)
        try:
            cert = load_cert(path)
        except Exception as ex:  # malformed / unreadable cert is a FAIL
            print("ERROR: could not load %s: %s" % (name, ex), file=sys.stderr)
            results.append((name, "?", "?", "LOAD_ERROR", "FAIL", "-", str(ex)))
            optimal_failures.append(name)
            continue
        certs_loaded.append((cert.get("n"), cert.get("k"), name, cert))
        label, d = verify_cert(cert, source=name)
        n, k = cert.get("n"), cert.get("k")
        status = cert.get("status")
        if label == "FAIL":
            optimal_failures.append(name)
        if status == "OPTIMAL":
            value_or_bound = d.get("value")
            detail = ("edges=%s prop=%s size=%s subsets=%s/%s"
                      % (d.get("num_edges"), d.get("property_ok"),
                         d.get("size_ok"), d.get("subsets_checked"),
                         d.get("subsets_expected")))
            if d.get("first_bad_subset"):
                detail += " BAD=%s" % d["first_bad_subset"]
        elif label == "BOUND":
            value_or_bound = d.get("best_lower_bound")
            detail = "lower bound only (no witness)"
        else:
            value_or_bound = "-"
            detail = d.get("note", "")
        results.append((name, n, k, status, label, value_or_bound, detail))

        # k=1 closed-form table row for any k=1 certificate present
        if k == 1 and status == "OPTIMAL":
            expected = f1_closed(n) if isinstance(n, int) else "?"
            recorded = cert.get("value")
            k1_rows.append((n, name, expected, recorded,
                            recorded == expected, d.get("property_ok")))

    # ---------------- summary table ----------------
    print("=" * 78)
    print("EP614 certificate verification — %d certificate(s) in %s"
          % (len(paths), cert_dir))
    print("=" * 78)
    widths = [24, 3, 3, 10, 7, 6, 52]
    print(_fmt_row(["file", "n", "k", "status", "result", "val/bnd", "detail"],
                   widths))
    print(_fmt_row(["-" * w for w in widths], widths))
    for row in results:
        print(_fmt_row([str(c) for c in row], widths))

    n_pass = sum(1 for r in results if r[4] == "PASS")
    n_bound = sum(1 for r in results if r[4] == "BOUND")
    n_info = sum(1 for r in results if r[4] == "INFO")
    n_fail = len(optimal_failures)
    print("-" * 78)
    print("SUMMARY: OPTIMAL PASS=%d  FAIL=%d  |  BOUND=%d  INFO=%d  |  total=%d"
          % (n_pass, n_fail, n_bound, n_info, len(results)))

    # ---------------- k=1 closed-form validation ----------------
    print("=" * 78)
    print("k=1 closed-form validation: f(n,1) = C(n,2) - floor(n^2/4)")
    print("=" * 78)
    if not k1_rows:
        print("No k=1 certificates present (the results doc references "
              "fnk_n*_k1.json for n=4..12 but none exist in this directory).")
        print("Closed form itself: " + ", ".join(
            "n=%d:%d" % (n, f1_closed(n)) for n in range(4, 13)))
    else:
        w = [24, 3, 10, 10, 7, 7]
        print(_fmt_row(["file", "n", "expected", "recorded", "match",
                        "proper"], w))
        for n, name, expected, recorded, match, prop in sorted(k1_rows):
            print(_fmt_row([str(name), str(n), str(expected), str(recorded),
                            str(match), str(prop)], w))
        present = {row[0] for row in k1_rows}
        missing = [n for n in range(4, 13) if n not in present]
        if missing:
            print("k=1 certificates missing for n=4..12: %s" % missing)
        bad_k1 = [row for row in k1_rows if not row[4]]
        if bad_k1:
            print("k=1 CLOSED-FORM MISMATCH: %s" % bad_k1)
            n_fail += len(bad_k1)

    if optimal_failures:
        print("FAILED OPTIMAL certificate(s): %s" % ", ".join(optimal_failures))
    return 1 if n_fail else 0


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pone = sub.add_parser("one", help="verify a single certificate JSON")
    pone.add_argument("certificate", help="path to fnk_n*_k*.json")
    pone.set_defaults(func=cmd_one)

    pall = sub.add_parser("all", help="verify all certificate JSONs in a dir")
    pall.add_argument("--cert-dir", required=True,
                      help="directory containing fnk_n*_k*.json files")
    pall.set_defaults(func=cmd_all)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
