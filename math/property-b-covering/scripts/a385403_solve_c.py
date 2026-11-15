#!/usr/bin/env python3
"""
A385403 session C -- improved encodings for the open lower-bound proofs.

Open questions this session attacks (conjecture a(n) = 7 + ceil((n-7)/3)):
  (13, 8): is there an 8-triple covering system on {1..13} forcing a mono
           triple under every 2-coloring?  (a(13) = 8 if yes, 9 if no)
  (14, 9): same with 9 triples on {1..14}  (a(14) = 9 if yes, 10 if no)
  later:   (15, 9), (16, 9).

Model family (all exact or exact-subset; see proof_scope on each certificate):
  full   : all 2^n colorings.
  halved : 2^(n-1) complement-canonical colorings (vertex 1 red) -- exact:
           complementing all colors leaves the monochromatic-triple set of a
           coloring invariant, so each complement class imposes one identical
           hitting constraint and is represented exactly once.
  sizes  : halved restricted to colorings whose monochromatic-triple set has
           size |M(c)| = C(r,3)+C(n-r,3) <= X (r = red count).  Smaller M(c)
           means a stronger (harder-to-hit) constraint, so this keeps the
           strongest constraints.  INFEASIBILITY-ONLY: it drops constraints,
           hence INFEASIBLE over the subset implies INFEASIBLE of the full
           model -- a valid lower-bound proof.  FEASIBLE/UNKNOWN here prove
           nothing about the full model.
  fano   : halved + exact Fano-freeness nogoods.  INFEASIBILITY-ONLY for the
           lower bound, paired with a counting argument for the other case:
           a Fano plane uses 7 edges on 7 vertices; the remaining k-7 edges
           cover at most 3(k-7) further vertices, so any k-edge system that
           contains a Fano plane covers at most 7 + 3(k-7) vertices, which is
           < n for (n,k) = (13,8), (14,9), (15,9), (16,9); such systems
           violate the coverage requirement.  Therefore
              "no covering k-system forces a mono triple"
           is equivalent to "no Fano-free covering k-system forces a mono
           triple", and the fano model encodes the latter exactly by adding,
           for each of the C(n,7) vertex 7-subsets and each of the 30 distinct
           Fano planes on it, the nogood  sum of its 7 triples <= 6.
  lazy   : cutting plane.  Master = budget + coverage (+ optional fano
           nogoods) + exact hitting constraints for a pool of canonical
           colorings; separator = tiny CP-SAT model searching for a
           2-coloring with no monochromatic chosen triple.  Master
           INFEASIBLE implies full-model INFEASIBLE (infeasibility over a
           subset of exact constraints): valid lower-bound proof; the final
           pool is re-solved from scratch ("replay") and saved in the
           certificate.  Separator INFEASIBLE => the chosen edges form a
           forcing witness, brute-force re-verified over ALL 2^n colorings
           before any certificate is written.

Experiment log (honest):
  * inclusion-dedupe of hitting constraints (keep only inclusion-minimal
    M(c) sets): measured 4096 -> 4082 (n=13), 8192 -> 8177 (n=14); mono-sets
    of distinct colorings are essentially never nested, so the reduction is
    negligible and is NOT used in any model below.
  * n=13 k=8 had only ever been run with the FULL (8192-constraint) model
    before this session; the exact halved (4096) model is tried here.

Certificates: results/certificates/a385403b_*.json  (never overwritten)
Session log : results/certificates/a385403b_session.json
Witness map : /tmp/propertyb2/witnesses_b.json   (task format, incremental)
"""

import argparse
import datetime
import itertools
import json
import os
import random
import time
from importlib.metadata import version as _pkg_version
from math import comb

from ortools.sat.python import cp_model

REPO = "/home/aditya/repos/open-research-lab/math/property-b-covering"
CERT_DIR = os.path.join(REPO, "results", "certificates")
TMP = "/tmp/propertyb2"
WITNESS_FILE = os.path.join(TMP, "witnesses_b.json")
SESSION_FILE = os.path.join(CERT_DIR, "a385403b_session.json")

TOOL = f"ortools CP-SAT {_pkg_version('ortools')} (python)"
DATE = datetime.date.today().isoformat()

KNOWN = {5: 10, 6: 10, 7: 7, 8: 8, 9: 8, 10: 8}

# Canonical Fano plane on {1..7}: 7 edges, not 2-colorable.
FANO = [(1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 5, 6)]

# The (n, k) pairs for which the Fano-containing case of the lower-bound
# probe is killed by pure counting: 7 + 3*(k-7) < n.
FANO_COUNTING_KILLS = {(13, 8): "7 + 3*1 = 10 < 13",
                       (14, 9): "7 + 3*2 = 13 < 14",
                       (15, 9): "7 + 3*2 = 13 < 15",
                       (16, 9): "7 + 3*2 = 13 < 16"}


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
    return 7 + (n - 5) // 3


def construction(n):
    """Fano plane on {1..7} + groups-of-3 cover of {8..n}."""
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
    """Brute force over ALL 2^n colorings (no early exit shortcuts beyond
    first-failure): edges cover {1..n} and every coloring leaves some edge
    monochromatic.  Returns (ok, msg)."""
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


# ----------------------------------------------------------------- triple data

_TRIPLE_CACHE = {}


def triple_data(n):
    if n in _TRIPLE_CACHE:
        return _TRIPLE_CACHE[n]
    trips = list(itertools.combinations(range(1, n + 1), 3))
    idx_of = {t: i for i, t in enumerate(trips)}
    _TRIPLE_CACHE[n] = (trips, idx_of)
    return _TRIPLE_CACHE[n]


def mono_idx(col, n, idx_of):
    """Indices of triples monochromatic under canonical coloring col."""
    red = [v for v in range(1, n + 1) if (col >> (v - 1)) & 1]
    blue = [v for v in range(1, n + 1) if not ((col >> (v - 1)) & 1)]
    out = []
    for base in (red, blue):
        if len(base) >= 3:
            for t in itertools.combinations(base, 3):
                out.append(idx_of[t])
    return out


def canonical_colors(n):
    return range(1, 1 << n, 2)  # vertex 1 red


def mono_size(n, col):
    r = bin(col).count("1")
    return comb(r, 3) + comb(n - r, 3)


def filtered_colors(n, max_mono_size):
    """Canonical colorings with |M(c)| <= max_mono_size, strongest first."""
    cols = [c for c in canonical_colors(n) if mono_size(n, c) <= max_mono_size]
    cols.sort(key=lambda c: mono_size(n, c))
    return cols


def mono_size_histogram(n):
    from collections import Counter
    c = Counter(mono_size(n, col) for col in canonical_colors(n))
    return dict(sorted(c.items()))


# --------------------------------------------------------------- Fano nogoods

_FANO_PATTERNS = None


def fano_patterns():
    """The 30 distinct Fano planes on 7 fixed points {0..6}, as tuples of
    7 position-triples each."""
    global _FANO_PATTERNS
    if _FANO_PATTERNS is not None:
        return _FANO_PATTERNS
    base = [[a - 1, b - 1, c - 1] for a, b, c in FANO]
    seen = set()
    for perm in itertools.permutations(range(7)):
        s = frozenset(frozenset(perm[x] for x in edge) for edge in base)
        seen.add(s)
    pats = []
    for s in seen:
        pats.append(tuple(sorted(tuple(sorted(e)) for e in s)))
    pats.sort()
    assert len(pats) == 30, f"expected 30 Fano planes on 7 points, got {len(pats)}"
    _FANO_PATTERNS = pats
    return pats


def add_fano_nogoods(model, s, n, idx_of):
    """Forbid every Fano plane on every 7-subset of {1..n}:
    for each embedding, sum of its 7 triple-variables <= 6."""
    count = 0
    for S in itertools.combinations(range(1, n + 1), 7):
        for pat in fano_patterns():
            idxs = [idx_of[tuple(S[p] for p in e)] for e in pat]
            model.add(sum(s[i] for i in idxs) <= 6)
            count += 1
    return count


# ------------------------------------------------------------------- builders

def build_skeleton(n, k, fano_free=False, hint_edges=None):
    """Budget + coverage (+ Fano-freeness nogoods) + hints."""
    trips, idx_of = triple_data(n)
    model = cp_model.CpModel()
    s = [model.new_bool_var(f"s_{i}") for i in range(len(trips))]
    model.add(sum(s) == k)
    for v in range(1, n + 1):
        idx = [i for i, t in enumerate(trips) if v in t]
        model.add(sum(s[i] for i in idx) >= 1)
    n_nogoods = 0
    if fano_free:
        n_nogoods = add_fano_nogoods(model, s, n, idx_of)
    if hint_edges is not None:
        hint_set = {frozenset(e) for e in hint_edges}
        for i, t in enumerate(trips):
            model.add_hint(s[i], 1 if frozenset(t) in hint_set else 0)
    return model, s, trips, n_nogoods


def build_primal(n, k, form, max_mono_size=None, hint_edges=None):
    """full / halved / sizes / fano primal models."""
    trips, idx_of = triple_data(n)
    fano_free = form == "fano"
    model, s, trips, n_nogoods = build_skeleton(n, k, fano_free, hint_edges)
    if form == "full":
        cols = list(range(1 << n))
    else:
        cols = list(canonical_colors(n))
        if form == "sizes" and max_mono_size is not None:
            cols = [c for c in cols if mono_size(n, c) <= max_mono_size]
            cols.sort(key=lambda c: mono_size(n, c))
    for col in cols:
        idx = mono_idx(col, n, idx_of)
        model.add(sum(s[i] for i in idx) >= 1)
    return model, s, trips, len(cols), n_nogoods


def new_solver(tl, workers, seed, lin2=False):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    if lin2:
        solver.parameters.linearization_level = 2
    return solver


def status_str(st):
    if st == cp_model.INFEASIBLE:
        return "INFEASIBLE"
    if st in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return "FEASIBLE"
    return "UNKNOWN"


def solve_primal(n, k, form, tl, workers, seed, max_mono_size=None,
                 hint_edges=None, lin2=False):
    t0 = time.time()
    model, s, trips, n_con, n_nogoods = build_primal(n, k, form, max_mono_size,
                                                     hint_edges)
    build_s = time.time() - t0
    solver = new_solver(tl, workers, seed, lin2)
    t1 = time.time()
    st = solver.solve(model)
    solve_s = time.time() - t1
    status = status_str(st)
    witness = None
    if status == "FEASIBLE":
        witness = [list(trips[i]) for i in range(len(trips)) if solver.value(s[i])]
    return {"status": status, "wall_s": round(time.time() - t0, 2),
            "build_s": round(build_s, 2), "solve_s": round(solve_s, 2),
            "witness": witness, "n_vars": len(trips),
            "n_coloring_constraints": n_con, "n_fano_nogoods": n_nogoods}


# --------------------------------------------------------------- lazy solver

def coloring_violates(col, edge_masks):
    """True iff no chosen edge is monochromatic under col."""
    for m in edge_masks:
        x = m & col
        if x == 0 or x == m:
            return False
    return True


def separator_coloring(n, E):
    """A 2-coloring of {1..n} with no monochromatic edge of E, or None.
    Returned as a canonical mask (vertex 1 red)."""
    mi = cp_model.CpModel()
    x = [mi.new_bool_var(f"x_{v}") for v in range(1, n + 1)]
    for (a, b, c) in E:
        mi.add_bool_or([x[a - 1].Not(), x[b - 1].Not(), x[c - 1].Not()])
        mi.add_bool_or([x[a - 1], x[b - 1], x[c - 1]])
    si = new_solver(30, 8, 7)
    st = si.solve(mi)
    if st == cp_model.INFEASIBLE:
        return None
    if st not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return "UNKNOWN"
    full = (1 << n) - 1
    col = sum((1 << (v - 1)) for v in range(1, n + 1) if si.value(x[v - 1]))
    if not (col & 1):
        col = full ^ col
    return col


def balanced_canonical(n, rng):
    """Random canonical coloring with balanced color classes."""
    half = n // 2
    r = rng.choice([half, n - half])          # red count (includes vertex 1)
    others = rng.sample(range(2, n + 1), r - 1)
    col = 1
    for v in others:
        col |= 1 << (v - 1)
    return col


def solve_lazy(n, k, tl, workers, seed, fano_free=False, seed_cuts=64,
               mine=5, caps=(90.0, 300.0, 900.0), hint_edges=None):
    """Cutting-plane solver; see module docstring.  Returns result dict."""
    t0 = time.time()
    trips, idx_of = triple_data(n)
    model, s, trips, n_nogoods = build_skeleton(n, k, fano_free, hint_edges)
    edge_masks = [(1 << (a - 1)) | (1 << (b - 1)) | (1 << (c - 1))
                  for (a, b, c) in trips]

    pool = []          # canonical colorings whose cut is in the master
    in_pool = set()

    def add_cut(col):
        if col in in_pool:
            return False
        in_pool.add(col)
        pool.append(col)
        idx = mono_idx(col, n, idx_of)
        model.add(sum(s[i] for i in idx) >= 1)
        return True

    rng = random.Random(seed)
    while len(pool) < seed_cuts:
        add_cut(balanced_canonical(n, rng))

    cap_i = 0
    iters = 0
    master_s = sep_s = 0.0
    status = "UNKNOWN"
    witness = None
    replay = None
    timed_out = False

    while time.time() - t0 < tl:
        remaining = tl - (time.time() - t0)
        if remaining <= 1:
            timed_out = True
            break
        final = cap_i >= len(caps)
        cap = remaining if final else min(remaining, caps[cap_i])
        iters += 1
        solver = new_solver(cap, workers, seed + iters)
        ta = time.time()
        st = solver.solve(model)
        master_s += time.time() - ta
        stt = status_str(st)
        log(f"[lazy n={n} k={k}] it={iters} status={stt} cuts={len(pool)} "
            f"master={master_s:.1f}s sep={sep_s:.1f}s elapsed="
            f"{time.time() - t0:.0f}s cap={cap:.0f}s")

        if stt == "INFEASIBLE":
            # Valid proof already (subset of exact constraints).  Replay from
            # scratch on the final pool for an independently checkable cert.
            replay_t0 = time.time()
            rmodel, rs, _, _ = build_skeleton(n, k, fano_free)
            for col in pool:
                idx = mono_idx(col, n, idx_of)
                rmodel.add(sum(rs[i] for i in idx) >= 1)
            rsolver = new_solver(max(1.0, tl - (time.time() - t0)), workers, seed)
            rst = rsolver.solve(rmodel)
            replay = {"status": status_str(rst),
                      "wall_s": round(time.time() - replay_t0, 2),
                      "pool_size": len(pool)}
            status = "INFEASIBLE"  # loop proof stands regardless of replay
            break

        if stt == "UNKNOWN":
            if final:
                timed_out = True
                break
            cap_i += 1
            continue

        # FEASIBLE: extract edges, run separator
        E = [trips[i] for i in range(len(trips)) if solver.value(s[i])]
        ta = time.time()
        colv = separator_coloring(n, E)
        sep_s += time.time() - ta
        if colv == "UNKNOWN":
            status = "UNKNOWN"      # separator timed out; conservative
            break
        if colv is None:
            ok, msg = verify_witness(n, E)
            if ok:
                status = "FEASIBLE"
                witness = [list(e) for e in E]
                break
            status = "UNKNOWN"      # should never happen; do not claim
            break
        # new violated coloring(s): the separator's + mined balanced ones
        added = add_cut(colv)
        emasks = [(1 << (a - 1)) | (1 << (b - 1)) | (1 << (c - 1))
                  for (a, b, c) in E]
        got = 1 if added else 0
        tries = 0
        while got < 1 + mine and tries < 4000 and time.time() - t0 < tl:
            tries += 1
            c2 = balanced_canonical(n, rng)
            if c2 not in in_pool and coloring_violates(c2, emasks):
                if add_cut(c2):
                    got += 1
        if not added and got == 0:
            status = "UNKNOWN"      # defensive: repeated solution
            break
        if final:
            timed_out = True
            break

    if status == "UNKNOWN" and not timed_out and time.time() - t0 >= tl:
        timed_out = True
    return {"status": status, "wall_s": round(time.time() - t0, 2),
            "build_s": 0.0,
            "solve_s": round(master_s + sep_s, 2),
            "master_s": round(master_s, 2), "sep_s": round(sep_s, 2),
            "witness": witness, "n_vars": len(trips),
            "n_coloring_constraints": len(pool),
            "n_fano_nogoods": n_nogoods,
            "iters": iters, "pool_hex": [hex(c) for c in pool],
            "replay": replay, "timed_out": timed_out}


# --------------------------------------------------------------- bookkeeping

def session_load():
    s = load_json(SESSION_FILE, None)
    if s is None:
        s = {"task": "OEIS A385403 session C - improved encodings for the "
                     "open (13,8) and (14,9) lower-bound proofs (and n=15/16 "
                     "push); conjecture a(n) = 7 + ceil((n-7)/3).",
             "date": DATE, "tool": TOOL, "runs": [], "results": [],
             "validation": []}
    return s


def session_save(s):
    atomic_write_json(SESSION_FILE, s)


def cert_path(n, k, status, tag):
    base = f"a385403b_n{n:02d}_k{k:02d}_{status}_{tag}.json"
    path = os.path.join(CERT_DIR, base)
    suff = 2
    while os.path.exists(path):          # never overwrite
        base = f"a385403b_n{n:02d}_k{k:02d}_{status}_{tag}_r{suff}.json"
        path = os.path.join(CERT_DIR, base)
        suff += 1
    return path


def proof_scope(n, k, form, max_mono_size):
    if form in ("full", "halved"):
        return ("full model: INFEASIBLE is a direct proof that no covering "
                f"{k}-triple system of {{1..{n}}} forces a mono triple")
    if form == "sizes":
        return (f"exact-subset model: only canonical colorings with "
                f"|M(c)| <= {max_mono_size} (smallest/strongest hitting "
                f"constraints).  INFEASIBLE over this subset implies "
                f"INFEASIBLE of the full model (dropped constraints are "
                f"weaker).  FEASIBLE/UNKNOWN prove nothing.")
    if form == "fano":
        kill = FANO_COUNTING_KILLS.get((n, k))
        if kill is None:
            return (f"WARNING: no counting argument registered for (n,k)="
                    f"({n},{k}); a Fano-containing system is NOT excluded "
                    f"by counting, so INFEASIBLE here only covers the "
                    f"Fano-free subcase.")
        return ("case split: (a) Fano-containing systems cover at most "
                f"{kill} vertices, violating coverage of {{1..{n}}}, so "
                f"they are excluded by counting without search; (b) this "
                f"model encodes the Fano-free subcase exactly (30 nogoods "
                f"per 7-subset, one per distinct Fano plane).  INFEASIBLE "
                f"of (b) + the counting exclusion of (a) proves no covering "
                f"{k}-triple system of {{1..{n}}} forces a mono triple.")
    if form == "lazy":
        return ("cutting-plane: master carries budget + coverage (+ fano "
                "nogoods if enabled) + exact hitting constraints for the "
                "pooled canonical colorings only.  Master INFEASIBLE "
                "implies full-model INFEASIBLE (subset of exact "
                "constraints); final pool re-solved from scratch (replay) "
                "and saved for independent checking.")
    return "unknown form"


def write_cert(n, k, res, form, claim, phase, expected, tag, workers, tl, seed,
               lin2=False, max_mono_size=None, engine=TOOL):
    verified = verify_msg = None
    if res["status"] == "FEASIBLE" and res.get("witness"):
        verified, verify_msg = verify_witness(n, res["witness"])
        if not verified:
            log(f"!! WITNESS FAILED VERIFICATION n={n} k={k}: {verify_msg}")
    cert = {
        "n": n, "k": k, "status": res["status"],
        "form": form, "tag": tag, "engine": engine,
        "max_mono_size": max_mono_size,
        "claim": claim, "phase": phase, "expected": expected,
        "proof_scope": proof_scope(n, k, form, max_mono_size),
        "wall_s": res["wall_s"], "build_s": res.get("build_s"),
        "solve_s": res.get("solve_s"), "tl": tl, "workers": workers,
        "seed": seed, "lin2": bool(lin2),
        "date": DATE, "tool": TOOL,
        "conjecture_bound": conjecture_bound(n) if n >= 7 else None,
        "n_vars": res.get("n_vars"),
        "n_coloring_constraints": res.get("n_coloring_constraints"),
        "n_fano_nogoods": res.get("n_fano_nogoods", 0),
        "verified": verified, "verify_msg": verify_msg,
    }
    if form == "lazy":
        cert["lazy_iters"] = res.get("iters")
        cert["master_s"] = res.get("master_s")
        cert["sep_s"] = res.get("sep_s")
        cert["replay"] = res.get("replay")
        cert["cut_pool_hex"] = res.get("pool_hex")
        cert["timed_out"] = res.get("timed_out")
    if res["status"] == "FEASIBLE" and verified:
        cert["witness_edges"] = res["witness"]
    path = cert_path(n, k, res["status"], tag)
    atomic_write_json(path, cert)
    return path, verified


def witnesses_update(n, k, status, edges, infeasible_below, source):
    wit = load_json(WITNESS_FILE, {})
    wit[str(n)] = {"k": k, "status": status, "witness_edges": edges,
                   "infeasible_below": infeasible_below, "source": source,
                   "date": DATE}
    atomic_write_json(WITNESS_FILE, {x: wit[x] for x in sorted(wit, key=int)})


# ----------------------------------------------------------------- validation

def cmd_validate(args):
    log("=== SESSION C VALIDATION (halved form; must reproduce "
        "a(5..10) = 10,10,7,8,8,8) ===")
    sess = session_load()
    ok_all = True
    for n in sorted(KNOWN):
        a = KNOWN[n]
        r_lo = solve_primal(n, a - 1, "halved", args.tl, args.workers, 42)
        p_lo, v_lo = write_cert(
            n, a - 1, r_lo, "halved",
            f"a({n}) >= {a}: no covering {a-1}-triple-system of {{1..{n}}} "
            f"forces a mono triple (published a({n})={a})",
            phase="validation", expected="INFEASIBLE",
            tag=f"halved_s{42}", workers=args.workers, tl=args.tl, seed=42)
        r_hi = solve_primal(n, a, "halved", args.tl, args.workers, 42,
                            hint_edges=construction(n))
        p_hi, v_hi = write_cert(
            n, a, r_hi, "halved",
            f"a({n}) <= {a}: witness covering {a}-triple-system "
            f"(published a({n})={a})",
            phase="validation", expected="FEASIBLE",
            tag=f"halved_s{42}", workers=args.workers, tl=args.tl, seed=42)
        ok = r_lo["status"] == "INFEASIBLE" and r_hi["status"] == "FEASIBLE" and v_hi
        ok_all &= ok
        sess["validation"] = [x for x in sess["validation"] if x["n"] != n]
        sess["validation"].append({
            "n": n, "known_a": a, "k=a-1": r_lo["status"],
            "k=a": r_hi["status"], "ok": ok,
            "wall_s_lo": r_lo["wall_s"], "wall_s_hi": r_hi["wall_s"],
            "certs": [os.path.basename(p_lo), os.path.basename(p_hi)]})
        session_save(sess)
        log(f"[validate] a({n})={a}: k={a-1} -> {r_lo['status']} "
            f"({r_lo['wall_s']}s), k={a} -> {r_hi['status']} "
            f"({r_hi['wall_s']}s, witness verified: {v_hi}) "
            f"{'OK' if ok else 'MISMATCH'}")
    if not ok_all:
        log("!! VALIDATION FAILED -- STOP.  New encodings are not trustworthy.")
        raise SystemExit(2)
    log("=== VALIDATION PASSED ===")


# ------------------------------------------------------------- SCIP MIP form

def solve_mip(n, k, form, tl, seed=0, max_mono_size=None, hint_edges=None,
              threads=0):
    """Same mathematical models as the CP-SAT forms (halved/full/sizes/fano)
    but solved with the bundled SCIP MIP solver via ortools pywraplp.
    SCIP INFEASIBLE is an exact MIP infeasibility proof (0/1 LP)."""
    from ortools.linear_solver import pywraplp
    t0 = time.time()
    trips, idx_of = triple_data(n)
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        return {"status": "NO_SCIP", "wall_s": 0.0, "build_s": 0.0,
                "solve_s": 0.0, "witness": None, "n_vars": len(trips),
                "n_coloring_constraints": 0, "n_fano_nogoods": 0}
    if threads > 0:
        try:
            solver.SetSolverSpecificParametersAsString(
                f"parallel/maxnthreads={threads},parallel/minnthreads={threads}")
        except Exception:
            pass
    solver.SetTimeLimit(int(tl * 1000))
    s = [solver.BoolVar(f"s_{i}") for i in range(len(trips))]
    solver.Add(sum(s) == k)
    for v in range(1, n + 1):
        idx = [i for i, t in enumerate(trips) if v in t]
        solver.Add(sum(s[i] for i in idx) >= 1)
    fano = form == "fano"
    n_nogoods = 0
    if fano:
        for S in itertools.combinations(range(1, n + 1), 7):
            for pat in fano_patterns():
                idxs = [idx_of[tuple(S[p] for p in e)] for e in pat]
                solver.Add(sum(s[i] for i in idxs) <= 6)
        n_nogoods = len(list(itertools.combinations(range(1, n + 1), 7))) * 30
    cols = list(range(1 << n)) if form == "full" else list(canonical_colors(n))
    if form == "sizes" and max_mono_size is not None:
        cols = [col for col in cols if mono_size(n, col) <= max_mono_size]
        cols.sort(key=lambda c: mono_size(n, c))
    for col in cols:
        idx = mono_idx(col, n, idx_of)
        solver.Add(sum(s[i] for i in idx) >= 1)
    build_s = time.time() - t0
    st = solver.Solve()
    solve_s = time.time() - t0 - build_s
    if st == pywraplp.Solver.INFEASIBLE:
        status = "INFEASIBLE"
    elif st in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        status = "FEASIBLE"
    else:
        status = "UNKNOWN"
    witness = None
    if status == "FEASIBLE":
        witness = [[int(x) for x in t] for i, t in enumerate(trips)
                   if s[i].solution_value() > 0.5]
    return {"status": status, "wall_s": round(time.time() - t0, 2),
            "build_s": round(build_s, 2), "solve_s": round(solve_s, 2),
            "witness": witness, "n_vars": len(trips),
            "n_coloring_constraints": len(cols), "n_fano_nogoods": n_nogoods}


# --------------------------------------------------------------------- probe

def cmd_probe(args):
    sess = session_load()
    hint_edges = construction(args.n) if (args.hint and not args.lower) else None
    t0 = time.time()
    if args.form == "scip":
        res = solve_mip(args.n, args.k, args.scip_model, args.tl, args.seed,
                        max_mono_size=args.max_mono_size,
                        hint_edges=hint_edges, threads=args.workers)
    elif args.form == "lazy":
        res = solve_lazy(args.n, args.k, args.tl, args.workers, args.seed,
                         fano_free=args.fano_free, seed_cuts=args.seed_cuts,
                         hint_edges=hint_edges)
    else:
        res = solve_primal(args.n, args.k, args.form, args.tl, args.workers,
                           args.seed, max_mono_size=args.max_mono_size,
                           hint_edges=hint_edges, lin2=args.lin2)
    wall = round(time.time() - t0, 2)

    if args.form == "scip":
        model_form = args.scip_model
        engine = "SCIP MIP via ortools pywraplp"
    else:
        model_form = args.form
        engine = TOOL

    bound = conjecture_bound(args.n)
    kind = args.claim_kind
    if kind == "lower":
        claim = (f"a({args.n}) >= {args.k + 1}: no covering {args.k}-triple-"
                 f"system of {{1..{args.n}}} forces a mono triple "
                 f"(conjecture bound {bound} -> INFEASIBLE expected at "
                 f"k={bound - 1})")
    else:
        claim = (f"a({args.n}) <= {args.k}: witness covering {args.k}-triple-"
                 f"system (conjecture bound {bound})")
    tag = args.form
    if args.form == "scip":
        tag = f"scip_{args.scip_model}"
    if args.form in ("sizes", "scip") and args.max_mono_size is not None:
        tag += f"_m{args.max_mono_size}"
    if args.form == "lazy" and args.fano_free:
        tag += "_fanofree"
    tag += f"_w{args.workers}_s{args.seed}"

    path, verified = write_cert(
        args.n, args.k, res, model_form, claim, phase="new",
        expected="INFEASIBLE" if kind == "lower" else "FEASIBLE",
        tag=tag, workers=args.workers, tl=args.tl, seed=args.seed,
        lin2=args.lin2, max_mono_size=args.max_mono_size, engine=engine)

    sess["runs"].append({
        "n": args.n, "k": args.k, "status": res["status"], "form": args.form,
        "engine": engine,
        "max_mono_size": args.max_mono_size, "fano_free": args.fano_free,
        "wall_s": wall, "tl": args.tl, "workers": args.workers,
        "seed": args.seed, "lin2": args.lin2,
        "n_coloring_constraints": res.get("n_coloring_constraints"),
        "n_fano_nogoods": res.get("n_fano_nogoods", 0),
        "claim_kind": kind, "cert": os.path.basename(path),
        "verified": verified, "date": DATE,
        "claim": claim})
    session_save(sess)

    extra = ""
    if args.form == "lazy":
        extra = (f", iters={res.get('iters')}, master={res.get('master_s')}s, "
                 f"sep={res.get('sep_s')}s"
                 + (f", replay={res['replay']['status']} "
                    f"({res['replay']['wall_s']}s)" if res.get("replay") else ""))
    log(f"[probe] n={args.n} k={args.k} form={args.form}"
        + (f" m={args.max_mono_size}" if args.form == "sizes" else "")
        + (" fanofree" if (args.form == "lazy" and args.fano_free) else "")
        + f" -> {res['status']} (wall {res['wall_s']}s, solve "
          f"{res['solve_s']}s, coloring-constraints="
          f"{res['n_coloring_constraints']}"
          + (f", nogoods={res['n_fano_nogoods']}" if res.get("n_fano_nogoods")
             else "") + extra + ")")
    log(f"[cert] {os.path.basename(path)}"
        + (f"  witness verified: {verified}" if verified is not None else ""))
    if res["status"] == "FEASIBLE" and verified and kind == "lower":
        witnesses_update(args.n, args.k, "FEASIBLE", res["witness"], None,
                         f"session C cert {os.path.basename(path)}")
        log(f"!!! CONJECTURE VIOLATION CANDIDATE: FEASIBLE at k={args.k} "
            f"< bound {bound} at n={args.n}; witness saved to "
            f"{WITNESS_FILE}; verify independently with "
            f"scripts/verify_a385403.py")
    if res["status"] == "UNKNOWN":
        log("[probe] UNKNOWN -- not a proof; escalate (more time / bigger "
            "subset / different form) or record as unsettled.")


# --------------------------------------------------------------------- replay

def cmd_replay(args):
    """Independently re-check a lazy proof: rebuild master from a saved cut
    pool and confirm INFEASIBLE."""
    pool = load_json(args.pool, None)
    if pool is None or "cut_pool_hex" not in pool:
        log(f"!! no cut_pool_hex in {args.pool}")
        raise SystemExit(1)
    n, k = args.n, args.k
    pool_cols = [int(h, 16) for h in pool["cut_pool_hex"]]
    trips, idx_of = triple_data(n)
    model, s, _, _ = build_skeleton(n, k)
    for col in pool_cols:
        idx = mono_idx(col, n, idx_of)
        model.add(sum(s[i] for i in idx) >= 1)
    solver = new_solver(args.tl, args.workers, args.seed)
    st = solver.solve(model)
    log(f"[replay] n={n} k={k} pool={len(pool_cols)} cuts -> "
        f"{status_str(st)} ({args.tl}s cap, {args.workers} workers)")
    if status_str(st) == "INFEASIBLE":
        log("[replay] CONFIRMED: pooled constraints are infeasible at "
            f"k={k}; lower bound a({n}) >= {k+1} stands (subset proof).")


# --------------------------------------------------------------------- report

def cmd_report(args):
    sess = session_load()
    log("== validation ==")
    for v in sess.get("validation", []):
        log(f"  n={v['n']}: known {v['known_a']}: {v['k=a-1']}/{v['k=a']} "
            f"ok={v['ok']}")
    log("== runs ==")
    for r in sess.get("runs", []):
        log(f"  n={r['n']} k={r['k']} {r['status']} {r['form']}"
            + (f" m={r['max_mono_size']}" if r.get("max_mono_size") else "")
            + (" fanofree" if r.get("fano_free") else "")
            + f" wall={r['wall_s']}s tl={r['tl']} w={r['workers']} "
              f"seed={r['seed']} cert={r['cert']}")
    log("== witnesses_b.json ==")
    wit = load_json(WITNESS_FILE, {})
    for nn in sorted(wit, key=int):
        e = wit[nn]
        log(f"  n={nn}: k={e.get('k')} status={e.get('status')} "
            f"infeasible_below={e.get('infeasible_below')}")


def cmd_sizes(args):
    log(f"mono-size histogram (canonical colorings) n={args.n}: "
        f"{mono_size_histogram(args.n)}")
    if args.max_mono_size is not None:
        cols = filtered_colors(args.n, args.max_mono_size)
        log(f"|M(c)| <= {args.max_mono_size}: {len(cols)} colorings")


def main():
    ap = argparse.ArgumentParser(description="A385403 session-C CP-SAT solver")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate")
    v.add_argument("--tl", type=float, default=240.0)
    v.add_argument("--workers", type=int, default=12)

    p = sub.add_parser("probe")
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--k", type=int, required=True)
    p.add_argument("--form", choices=["full", "halved", "sizes", "fano", "lazy",
                                      "scip"], default="halved")
    p.add_argument("--scip-model", choices=["full", "halved", "sizes", "fano"],
                   default="halved",
                   help="scip form: which mathematical model SCIP solves")
    p.add_argument("--max-mono-size", type=int, default=None,
                   help="sizes form: keep colorings with |M(c)| <= X")
    p.add_argument("--fano-free", action="store_true",
                   help="lazy form: add Fano-freeness nogoods to the master")
    p.add_argument("--seed-cuts", type=int, default=64)
    p.add_argument("--lower", action="store_true",
                   help="lower-bound probe (claim a(n) >= k+1)")
    p.add_argument("--hint", action="store_true",
                   help="hint the standard Fano+groups construction")
    p.add_argument("--tl", type=float, default=300.0)
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--lin2", action="store_true")
    p.add_argument("--claim-kind", choices=["lower", "upper"], default="lower")

    r = sub.add_parser("replay")
    r.add_argument("--pool", required=True)
    r.add_argument("--n", type=int, required=True)
    r.add_argument("--k", type=int, required=True)
    r.add_argument("--tl", type=float, default=600.0)
    r.add_argument("--workers", type=int, default=12)
    r.add_argument("--seed", type=int, default=42)

    sub.add_parser("report")
    sz = sub.add_parser("sizes")
    sz.add_argument("--n", type=int, required=True)
    sz.add_argument("--max-mono-size", type=int, default=None)

    args = ap.parse_args()
    os.makedirs(CERT_DIR, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    {"validate": cmd_validate, "probe": cmd_probe, "replay": cmd_replay,
     "report": cmd_report, "sizes": cmd_sizes}[args.cmd](args)


if __name__ == "__main__":
    main()
