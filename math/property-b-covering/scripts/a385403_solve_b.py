#!/usr/bin/env python3
"""
A385403 computation agent -- session B (this is a NEW file; the prior session's
scripts/a385403_solve.py is left untouched).

Task: settle a(n) = minimum number of triples (3-subsets) that cover {1..n}
such that every 2-coloring of {1..n} leaves at least one monochromatic triple
(OEIS A385403; known a(5..10) = 10,10,7,8,8,8; conjecture a(n) = 7+ceil((n-7)/3)
for n >= 7, the %F upper bound by extending the Fano plane).

Exact model for edge budget k (primal formulation):
  variables: s_t in {0,1} for every 3-subset t of {1..n}   (C(n,3) variables)
  (1) sum_t s_t = k
  (2) coverage: for each vertex v, sum_{t contains v} s_t >= 1
  (3) hitting: for every 2-coloring c of {1..n}:
        sum_{t monochromatic under c} s_t >= 1
A triple is monochromatic under c iff all 3 elements get the same color.
a(n) = min feasible k.  Each value is settled by two probes:
  INFEASIBLE at k-1  (lower-bound proof; CP-SAT status INFEASIBLE = proof)
  FEASIBLE  at k     (upper-bound witness; brute-force re-verified over ALL 2^n
                      colorings before any certificate is written)

Model forms:
  full   : constraints (3) for all 2^n colorings                      (exact)
  halved : constraints (3) only for the 2^(n-1) colorings with vertex 1 = red
           (exact: complementing all colors leaves the set of monochromatic
           triples of a coloring invariant, so c and ~c impose the identical
           constraint; every coloring is represented exactly once by its
           complement-canonical form).  Prescribed for n >= 14; used as a
           documented escalation for stubborn probes at n <= 13.
  lazy   : cutting-plane variant of the same exact model.  Master: variables
           (1)+(2) plus the hitting constraints for colorings found so far;
           separator: tiny CP-SAT model searching for a 2-coloring with no
           monochromatic chosen triple; each coloring found adds its exact
           hitting constraint to the master.  Master INFEASIBLE is a valid
           lower-bound proof because it is infeasibility over a SUBSET of all
           coloring constraints (fewer constraints = superset of solutions).
           FEASIBLE is emitted only when the separator fails, and the witness
           is brute-force re-verified over all 2^n colorings.

Certificate layout (no existing file is ever overwritten):
  results/certificates/session_b/          every probe run this session
  results/certificates/a385403_n{nn}_k{kk}_{STATUS}.json
      decisive new-term certs are ALSO copied here (only if the filename does
      not already exist -- n<=12 filenames belong to the prior session)
  results/certificates/a385403_session_b.json     session summary (the spec'd
      name a385403_session.json already exists from the prior session and is
      left untouched)
  /tmp/propertyb/witnesses.json   incremental, task-format:
      {"n": {"k":.., "status":.., "witness_edges":[..], "infeasible_below":..}}
"""

import argparse
import datetime
import glob
import itertools
import json
import os
import random
import time
from importlib.metadata import version as _pkg_version

from ortools.sat.python import cp_model

REPO = "/home/aditya/repos/open-research-lab/math/property-b-covering"
CERT_TOP = os.path.join(REPO, "results", "certificates")
CERT_DIR = os.path.join(CERT_TOP, "session_b")
TMP = "/tmp/propertyb"
WITNESS_FILE = os.path.join(TMP, "witnesses.json")
SESSION_FILE = os.path.join(CERT_TOP, "a385403_session_b.json")

TOOL = f"ortools CP-SAT {_pkg_version('ortools')} (python)"
DATE = datetime.date.today().isoformat()

KNOWN = {5: 10, 6: 10, 7: 7, 8: 8, 9: 8, 10: 8}

# Canonical Fano plane on {1..7}: not 2-colorable, covers {1..7}.
FANO = [(1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 5, 6)]

HALVED_NOTE = ("halved formulation, exact: hitting constraints only for the "
               "2^(n-1) complement-canonical colorings (vertex 1 = red); "
               "complementing all colors leaves the set of monochromatic "
               "triples invariant, so each equivalence class imposes one "
               "identical constraint and is represented exactly once.")
LAZY_NOTE = ("lazy cutting-plane formulation of the same exact model: master "
             "carries budget+coverage+hitting constraints for the colorings "
             "found so far; a separating CP-SAT model searches for a "
             "2-coloring with no monochromatic chosen triple and its coloring "
             "is added as a new exact hitting constraint. Master INFEASIBLE "
             "is a valid lower-bound proof (infeasibility over a subset of "
             "all coloring constraints implies infeasibility of the full "
             "model); FEASIBLE requires the separator to fail and the "
             "witness to pass brute-force verification over all 2^n colorings.")


def log(msg):
    print(msg, flush=True)


def atomic_write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def conjecture_bound(n):
    """OEIS %F upper bound: a(n) <= 7 + ceil((n-7)/3) for n >= 7."""
    return 7 + (n - 5) // 3  # == 7 + ceil((n-7)/3) for n >= 7


def construction(n):
    """Fano plane on {1..7} + ceil((n-7)/3) triples covering {8..n}."""
    edges = [tuple(e) for e in FANO]
    rest = list(range(8, n + 1))
    i = 0
    while i < len(rest):
        chunk = rest[i:i + 3]
        if len(chunk) == 3:
            edges.append((chunk[0], chunk[1], chunk[2]))
        elif len(chunk) == 2:
            edges.append((1, chunk[0], chunk[1]))
        else:
            edges.append((1, 2, chunk[0]))
        i += 3
    return edges


def verify_witness(n, edges):
    """Brute force: edges cover {1..n} and hit the mono triples of ALL 2^n
    colorings. Returns (ok, msg)."""
    if len(set(frozenset(e) for e in edges)) != len(edges):
        return False, "duplicate edges"
    if not edges:
        return False, "empty edge list"
    masks = []
    for e in edges:
        if len(set(e)) != 3 or not all(isinstance(x, int) and 1 <= x <= n for x in e):
            return False, f"bad triple {e}"
        masks.append((1 << (e[0] - 1)) | (1 << (e[1] - 1)) | (1 << (e[2] - 1)))
    cov = 0
    for m in masks:
        cov |= m
    if cov != (1 << n) - 1:
        return False, "edges do not cover {1..n}"
    for col in range(1 << n):
        for m in masks:
            x = m & col
            if x == 0 or x == m:
                break
        else:
            return False, f"coloring {col:0{n}b} has no monochromatic chosen triple"
    return True, "ok"


# ----------------------------------------------------------------- model forms

def triple_data(n):
    trips = list(itertools.combinations(range(1, n + 1), 3))
    tmask = [(1 << (a - 1)) | (1 << (b - 1)) | (1 << (c - 1)) for a, b, c in trips]
    return trips, tmask


def build_primal(n, k, halved, hint_edges=None):
    """Exact primal model: full (2^n) or halved (2^(n-1), vertex 1 red)."""
    trips, tmask = triple_data(n)
    T = len(trips)
    full = (1 << n) - 1
    model = cp_model.CpModel()
    s = [model.new_bool_var(f"s_{i}") for i in range(T)]
    model.add(sum(s) == k)
    for v in range(1, n + 1):
        idx = [i for i, t in enumerate(trips) if v in t]
        model.add(sum(s[i] for i in idx) >= 1)
    colors = range(1, 1 << n, 2) if halved else range(1 << n)
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


def solve_primal(n, k, halved, tl, workers, seed, hint_edges=None, lin2=False):
    t0 = time.time()
    model, s, trips, n_con = build_primal(n, k, halved, hint_edges)
    build_s = time.time() - t0
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    if lin2:
        solver.parameters.linearization_level = 2
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
    return {"status": status, "wall_s": round(time.time() - t0, 2),
            "build_s": round(build_s, 2), "solve_s": round(solve_s, 2),
            "witness": witness, "n_vars": len(trips),
            "n_coloring_constraints": n_con}


def solve_lazy(n, k, tl, workers, seed, hint_edges=None, n_seed_cuts=48):
    """Cutting-plane variant; see LAZY_NOTE.  Cuts accumulate on one model."""
    t0 = time.time()
    trips, tmask = triple_data(n)
    T = len(trips)
    full = (1 << n) - 1

    def mono_idx(col):
        comp = full ^ col
        return [i for i in range(T)
                if (tmask[i] & col) == tmask[i] or (tmask[i] & comp) == tmask[i]]

    model = cp_model.CpModel()
    s = [model.new_bool_var(f"s_{i}") for i in range(T)]
    model.add(sum(s) == k)
    for v in range(1, n + 1):
        idx = [i for i, t in enumerate(trips) if v in t]
        model.add(sum(s[i] for i in idx) >= 1)
    if hint_edges is not None:
        hint_set = {frozenset(e) for e in hint_edges}
        for i, t in enumerate(trips):
            model.add_hint(s[i], 1 if frozenset(t) in hint_set else 0)

    rng = random.Random(seed)
    seen = set()
    cuts = 0
    while len(seen) < n_seed_cuts:          # seed with random canonical colorings
        m = rng.getrandbits(n) | 1          # canonical: vertex 1 red
        if m in seen:
            continue
        seen.add(m)
        model.add(sum(s[i] for i in mono_idx(m)) >= 1)
        cuts += 1

    iters = 0
    status = "UNKNOWN"
    witness = None
    master_s = inner_s = 0.0
    while time.time() - t0 < tl:
        iters += 1
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max(1.0, tl - (time.time() - t0))
        solver.parameters.num_search_workers = workers
        solver.parameters.random_seed = seed
        ta = time.time()
        st = solver.solve(model)
        master_s += time.time() - ta
        if st == cp_model.INFEASIBLE:
            status = "INFEASIBLE"
            break
        if st not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            status = "UNKNOWN"              # master timed out
            break
        E = [trips[i] for i in range(T) if solver.value(s[i])]
        # separator: 2-coloring with no monochromatic chosen edge
        mi = cp_model.CpModel()
        x = [mi.new_bool_var(f"x_{v}") for v in range(1, n + 1)]
        for (a, b, c) in E:
            mi.add_bool_or([x[a - 1].Not(), x[b - 1].Not(), x[c - 1].Not()])
            mi.add_bool_or([x[a - 1], x[b - 1], x[c - 1]])
        si = cp_model.CpSolver()
        si.parameters.max_time_in_seconds = 30
        si.parameters.num_search_workers = 8
        tb = time.time()
        st2 = si.solve(mi)
        inner_s += time.time() - tb
        if st2 == cp_model.INFEASIBLE:
            status = "FEASIBLE"             # E is a forcing system
            witness = [list(e) for e in E]
            break
        if st2 not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            status = "UNKNOWN"
            break
        col = sum((1 << (v - 1)) for v in range(1, n + 1) if si.value(x[v - 1]))
        if not (col & 1):                   # canonicalize: vertex 1 red
            col = full ^ col
        if col in seen:                     # cannot happen; defensive
            status = "UNKNOWN"
            break
        seen.add(col)
        model.add(sum(s[i] for i in mono_idx(col)) >= 1)
        cuts += 1
    return {"status": status, "wall_s": round(time.time() - t0, 2),
            "build_s": 0.0, "solve_s": round(master_s + inner_s, 2),
            "witness": witness, "n_vars": T, "n_coloring_constraints": cuts,
            "iters": iters, "master_s": round(master_s, 2),
            "inner_s": round(inner_s, 2)}


def run_attempt(n, k, form, tl, workers, seed, hint=False, lin2=False):
    hint_edges = construction(n) if hint else None
    if form == "lazy":
        res = solve_lazy(n, k, tl, workers, seed, hint_edges=hint_edges)
    else:
        res = solve_primal(n, k, halved=(form == "halved"), tl=tl, workers=workers,
                           seed=seed, hint_edges=hint_edges, lin2=lin2)
    res.update({"form": form, "tl": tl, "seed": seed, "workers": workers,
                "lin2": lin2, "hint": hint})
    return res


# ---------------------------------------------------------------- bookkeeping

def session_add_run(run_summary):
    sess = load_json(SESSION_FILE, {})
    sess.setdefault("runs", []).append(run_summary)
    atomic_write_json(SESSION_FILE, sess)


def session_add_result(entry):
    sess = load_json(SESSION_FILE, {})
    sess["results"] = [x for x in sess.get("results", []) if x["n"] != entry["n"]]
    sess["results"].append(entry)
    sess["results"].sort(key=lambda x: x["n"])
    atomic_write_json(SESSION_FILE, sess)


def session_add_validation(entry):
    sess = load_json(SESSION_FILE, {})
    sess["validation"] = [x for x in sess.get("validation", []) if x["n"] != entry["n"]]
    sess["validation"].append(entry)
    sess["validation"].sort(key=lambda x: x["n"])
    atomic_write_json(SESSION_FILE, sess)


def cert_filename(n, k, status, seed=None):
    if status in ("INFEASIBLE", "FEASIBLE"):
        return f"a385403_n{n:02d}_k{k:02d}_{status}.json"
    return f"a385403_n{n:02d}_k{k:02d}_UNKNOWN_seed{seed}.json"


def write_cert(run, res, claim, phase, expected, extra_attempts=None):
    """Write the certificate for one probe. Returns (path, published_top_path)."""
    n, k = run["n"], run["k"]
    status = res["status"]
    verified = verify_msg = None
    if status == "FEASIBLE" and res.get("witness"):
        verified, verify_msg = verify_witness(n, res["witness"])
        if not verified:
            log(f"!! WITNESS FAILED VERIFICATION at n={n} k={k}: {verify_msg}")
    notes = {"halved": HALVED_NOTE, "lazy": LAZY_NOTE}.get(res["form"])
    cert = {
        "n": n, "k": k, "status": status,
        "wall_s": res["wall_s"], "workers": res["workers"],
        "model_form": res["form"], "claim": claim, "date": DATE, "tool": TOOL,
        "seed": res["seed"], "phase": phase,
        "conjecture_bound": conjecture_bound(n) if n >= 7 else None,
        "expected": expected,
        "n_vars": res.get("n_vars"),
        "n_coloring_constraints": res.get("n_coloring_constraints"),
        "build_s": res.get("build_s"), "solve_s": res.get("solve_s"),
        "linearization_level": 2 if res.get("lin2") else 1,
        "hint_used": bool(res.get("hint")),
        "model_note": notes,
        "verified": verified, "verify_msg": verify_msg,
        "attempts": extra_attempts or [],
    }
    if status == "FEASIBLE" and verified:
        cert["witness_edges"] = res["witness"]
    fname = cert_filename(n, k, status, res["seed"])
    path = os.path.join(CERT_DIR, fname)
    atomic_write_json(path, cert)
    top = os.path.join(CERT_TOP, fname)
    published = None
    if not os.path.exists(top):
        atomic_write_json(top, cert)
        published = top
    return path, published, verified


def witnesses_update_entry(n, k, status, edges, infeasible_below, source):
    wit = load_json(WITNESS_FILE, {})
    if not isinstance(wit, dict) or (wit and not all(isinstance(v, dict) for v in wit.values())):
        wit = {}  # prior session's {"n": [edges]} format found; replace with task format
    wit[str(n)] = {"k": k, "status": status, "witness_edges": edges,
                   "infeasible_below": infeasible_below, "source": source}
    atomic_write_json(WITNESS_FILE, {x: wit[x] for x in sorted(wit, key=int)})


def init_witnesses_from_prior():
    """Seed witnesses.json (task format) from the prior session's top-level
    certificates for n = 5..12, marking the provenance."""
    for n in range(5, 13):
        cand = sorted(glob.glob(os.path.join(CERT_TOP, f"a385403_n{n:02d}_k*_FEASIBLE.json")))
        if not cand:
            continue
        chi = load_json(cand[-1], None)
        if chi is None or chi.get("status") != "FEASIBLE":
            continue
        k = chi["k"]
        lo = os.path.join(CERT_TOP, f"a385403_n{n:02d}_k{k - 1:02d}_INFEASIBLE.json")
        clo = load_json(lo, None)
        if clo is None or clo.get("status") != "INFEASIBLE" or clo["k"] != k - 1:
            continue
        src = (f"prior-session certs {os.path.basename(lo)} + {os.path.basename(cand[-1])}")
        witnesses_update_entry(n, k, "FEASIBLE", chi["witness_edges"],
                               k - 1, src)
        log(f"[witness-init] n={n}: k={k} adopted from prior certs "
            f"(lower proof at k={k-1} INFEASIBLE)")


# ------------------------------------------------------------------ commands

def cmd_validate(args):
    log("=== SESSION B VALIDATION (must reproduce a(5..10) = 10,10,7,8,8,8) ===")
    ok_all = True
    for n in sorted(KNOWN):
        a = KNOWN[n]
        r_lo = run_attempt(n, a - 1, "full", args.tl, args.workers, 42)
        p_lo, pub_lo, _ = write_cert(
            {"n": n, "k": a - 1}, r_lo,
            f"a({n}) >= {a}: no covering {a-1}-triple-system of {{1..{n}}} forces "
            f"a mono triple (published a({n})={a})",
            phase="validation", expected="INFEASIBLE")
        r_hi = run_attempt(n, a, "full", args.tl, args.workers, 42, hint=True)
        p_hi, pub_hi, v_hi = write_cert(
            {"n": n, "k": a}, r_hi,
            f"a({n}) <= {a}: witness covering {a}-triple-system (published a({n})={a})",
            phase="validation", expected="FEASIBLE")
        ok = r_lo["status"] == "INFEASIBLE" and r_hi["status"] == "FEASIBLE" and v_hi
        ok_all &= ok
        session_add_validation({
            "n": n, "known_a": a, "k=a-1": r_lo["status"], "k=a": r_hi["status"],
            "ok": ok, "wall_s_lo": r_lo["wall_s"], "wall_s_hi": r_hi["wall_s"],
            "certs": [os.path.basename(p_lo), os.path.basename(p_hi)]})
        log(f"[validate] a({n})={a}: k={a-1} -> {r_lo['status']} ({r_lo['wall_s']}s), "
            f"k={a} -> {r_hi['status']} ({r_hi['wall_s']}s, witness verified: {v_hi}) "
            f"{'OK' if ok else 'MISMATCH'}")
    if not ok_all:
        log("!! VALIDATION FAILED -- STOP. Do not proceed to new n.")
        raise SystemExit(2)
    log("=== VALIDATION PASSED (all six known values reproduced) ===")


def cmd_probe(args):
    res = run_attempt(args.n, args.k, args.form, args.tl, args.workers, args.seed,
                      hint=(not args.no_hint), lin2=args.lin2)
    kind = "lower" if args.claim_kind == "lower" else "upper"
    bound = conjecture_bound(args.n)
    if kind == "lower":
        claim = (f"a({args.n}) >= {args.k + 1}: no covering {args.k}-triple-system "
                 f"of {{1..{args.n}}} forces a mono triple (conjecture lower bound "
                 f"probe at bound-1={bound - 1})")
    else:
        claim = (f"a({args.n}) <= {args.k}: witness covering {args.k}-triple-system "
                 f"(conjecture upper bound {bound})")
    attempts = []
    if args.adopted:
        attempts.append({"adopted_from": args.adopted})
    path, published, verified = write_cert(
        {"n": args.n, "k": args.k}, res, claim,
        phase="new" if args.n >= 11 else "validation",
        expected=("INFEASIBLE" if kind == "lower" else "FEASIBLE"),
        extra_attempts=attempts)
    session_add_run({
        "n": args.n, "k": args.k, "status": res["status"],
        "wall_s": res["wall_s"], "model_form": res["form"], "seed": res["seed"],
        "workers": res["workers"], "lin2": res["lin2"], "claim": claim,
        "cert": os.path.relpath(path, CERT_TOP),
        "published_top": os.path.relpath(published, CERT_TOP) if published else None,
        "verified": verified, "date": DATE})
    log(f"[probe] n={args.n} k={args.k} form={res['form']}"
        f"{' lin2' if args.lin2 else ''} seed={args.seed} -> {res['status']} "
        f"(wall {res['wall_s']}s, solve {res['solve_s']}s, "
        f"coloring-constraints={res['n_coloring_constraints']}"
        + (f", witness verified: {verified}" if verified is not None else "")
        + (f", iters={res['iters']}" if "iters" in res else "")
        + ")")
    log(f"[cert] {os.path.relpath(path, CERT_TOP)}"
        + (f" (also published: {os.path.relpath(published, CERT_TOP)})"
           if published else " (session_b only; top-level name exists)"))
    if res["status"] == "UNKNOWN":
        log("[probe] UNKNOWN -- not a proof; escalate or record as unsettled.")


def cmd_record_value(args):
    """After both probes of n are done (or adopted), record the value and
    update witnesses.json in the task format."""
    n, k = args.n, args.k
    lo = load_json(os.path.join(CERT_DIR, f"a385403_n{n:02d}_k{k - 1:02d}_INFEASIBLE.json"),
                   None)
    lo_top = load_json(os.path.join(CERT_TOP, f"a385403_n{n:02d}_k{k - 1:02d}_INFEASIBLE.json"),
                       None)
    hi = load_json(os.path.join(CERT_DIR, f"a385403_n{n:02d}_k{k:02d}_FEASIBLE.json"), None)
    hi_top = load_json(os.path.join(CERT_TOP, f"a385403_n{n:02d}_k{k:02d}_FEASIBLE.json"), None)
    if hi is None or hi.get("status") != "FEASIBLE" or not hi.get("verified"):
        log(f"[record] n={n}: no verified FEASIBLE certificate at k={k}; cannot record.")
        raise SystemExit(1)
    bound = conjecture_bound(n)
    how = None
    if lo is not None and lo["status"] == "INFEASIBLE":
        lo_src = os.path.relpath(os.path.join(CERT_DIR, f"a385403_n{n:02d}_k{k - 1:02d}_INFEASIBLE.json"), CERT_TOP)
        how = "proved (INFEASIBLE at value-1 + FEASIBLE at value, session B)"
    elif lo_top is not None and lo_top["status"] == "INFEASIBLE":
        lo_src = f"prior-session cert a385403_n{n:02d}_k{k - 1:02d}_INFEASIBLE.json (adopted)"
        how = "proved (INFEASIBLE at value-1 [adopted prior session] + FEASIBLE at value [session B])"
    else:
        log(f"[record] n={n}: no INFEASIBLE certificate at k={k-1} (neither session_b "
            f"nor top-level); value k={k} recorded as witness-only, NOT settled.")
        how = "witness only (upper bound; no lower-bound proof available)"
        lo_src = None
    entry = {"n": n, "a_n": k, "conjecture": bound,
             "matches_conjecture": k == bound, "how": how,
             "lower_cert": lo_src,
             "upper_cert": f"session_b/a385403_n{n:02d}_k{k:02d}_FEASIBLE.json"}
    session_add_result(entry)
    witnesses_update_entry(
        n, k, "FEASIBLE", hi["witness_edges"], k - 1,
        "upper witness: session_b/a385403_n%02d_k%02d_FEASIBLE.json; lower: %s"
        % (n, k, lo_src or "none"))
    log(f"[value] a({n}) = {k} (conjecture {bound}) [{how}]")
    log(f"[witnesses] /tmp/propertyb/witnesses.json updated for n={n}")


def cmd_report(args):
    sess = load_json(SESSION_FILE, {})
    wit = load_json(WITNESS_FILE, {})
    log("== validation ==")
    for v in sess.get("validation", []):
        log(f"  n={v['n']}: known {v['known_a']}: {v['k=a-1']}/{v['k=a']} ok={v['ok']}")
    log("== results ==")
    for r in sess.get("results", []):
        log(f"  a({r['n']}) = {r['a_n']} (conjecture {r['conjecture']}, "
            f"{r['matches_conjecture']}) [{r['how']}]")
    log("== runs ==")
    for r in sess.get("runs", []):
        log(f"  n={r['n']} k={r['k']} {r['status']} {r['model_form']} "
            f"seed={r.get('seed')} wall={r['wall_s']}s")
    log("== witnesses.json keys ==")
    log("  " + ", ".join(sorted(wit, key=int)))


def main():
    ap = argparse.ArgumentParser(description="A385403 session-B CP-SAT solver")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--tl", type=float, default=300.0)
    v.add_argument("--workers", type=int, default=8)
    p = sub.add_parser("probe")
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--k", type=int, required=True)
    p.add_argument("--form", choices=["full", "halved", "lazy"], default="full")
    p.add_argument("--tl", type=float, default=300.0)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--lin2", action="store_true")
    p.add_argument("--no-hint", action="store_true")
    p.add_argument("--claim-kind", choices=["lower", "upper"], default="lower")
    p.add_argument("--adopted", default=None,
                   help="note a prior-session cert adopted as context for this probe")
    r = sub.add_parser("record-value")
    r.add_argument("--n", type=int, required=True)
    r.add_argument("--k", type=int, required=True)
    sub.add_parser("init-witnesses")
    sub.add_parser("report")
    args = ap.parse_args()
    os.makedirs(CERT_DIR, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    if not os.path.exists(SESSION_FILE):
        atomic_write_json(SESSION_FILE, {
            "task": "OEIS A385403 - min triples covering {1..n} forcing a mono "
                    "triple under every 2-coloring",
            "session": "B (continuation; prior session same day produced "
                       "a385403_session.json + certs n=5..12 at top level)",
            "date": DATE, "tool": TOOL,
            "model": "exact CP-SAT primal model: s_t binary per 3-subset; "
                     "sum s_t = k; coverage per vertex; hitting constraint "
                     "sum_{t mono under c} s_t >= 1 per coloring. Forms: full "
                     "(2^n), halved (2^(n-1), exact by complement symmetry), "
                     "lazy cutting-plane (exact; see model_note). Values "
                     "settled by INFEASIBLE at k-1 + FEASIBLE at k with "
                     "brute-force witness verification.",
            "validation": [], "results": [], "runs": []})
    {"validate": cmd_validate, "probe": cmd_probe, "record-value": cmd_record_value,
     "init-witnesses": lambda a: init_witnesses_from_prior(),
     "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
