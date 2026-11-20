# Prior-art watch — 2026-11-20

A living record of external work that overlaps the lab's claims. This file exists
because a working web-search tool became available on 2026-11-20; earlier audits
were limited by HTTP 402. Entries are dated, with exact queries and URLs.

## Queries run (2026-11-20, searxng metasearch)

- `A385403 a(13)=9 minimum triples cover monochromatic OEIS`
- `Erdos problem 112 k(4,4) directed Ramsey circulant 40`
- `Erdos 614 f(10,3)=29 sparse induced subgraph`
- `site:erdosproblemaday.com 614 f(10,3) 29 f(10,4) 28 exact values`
- `erdosproblemaday 614 submissions exact small values table f(n,k)`
- `A385403 a(13) 9 triples cover 2-coloring known value`
- `10,10,7,8,8,8,9,9,9 OEIS A385403`, `A385403 b-file a(13) terms 2026`
- `erdosproblemaday github repository source data`

## Major hit: Erdős Problem a Day

URL: https://erdosproblemaday.com/ — "Patrick White and Claude have attempted
621 Erdős problems" since July 2026. Full write-ups, working reports and live
attempts, with a label for each.

### Overlap with our Erdős #614 track

Their write-up
https://erdosproblemaday.com/day/614-induced-min-degree-turan (27 Jul 2026,
"LIVE") records:

- the **same** Quanyu Tang forum comment and Tang–Ma note we found on 2026-11-19;
- an independent re-derivation of the Tang–Ma reduction (hand proof plus
  brute-force enumeration of graphs on 3, 4 and 5 vertices);
- **14 small exact values of f(n,k)** computed with OR-Tools CP-SAT directly
  from the definition (their text: "all 14 matched the note's claims exactly"),
  plus 8 more end-to-end checks of the reduction;
- asymptotic orders for k in {1,2,3,4,5,7,8,13}, including two orders they call
  new: f(n,7) = C(n,2) − Θ(n^(4/3)) and f(n,8) = C(n,2) − Θ(n^(6/5));
- a correction of an overclaim that treated the Erdős–Simonovits even-cycle
  conjecture as proved (matching lower bounds known only for cycles 4, 6, 10).

**Consequence for Rule 0.** Our session's new values f(10,3)=29 and f(10,4)=28
were computed in November 2026, ~4 months after their July computation. Their
write-up does not enumerate which 14 cells they solved, so we cannot prove the
cells overlap — but we also cannot prove they do not. Per Rule 0, "partial
overlap is still overlap" and an unverified first claim is not a claim. Our
EP614 novelty language is therefore **withdrawn**: those values must be
described as an independent re-derivation with our own witness/certificate,
not as new exact values. The symmetry-broken solver and the independent Turán
oracle remain our artifacts.

### Overlap with our Erdős #112 track

Their 18 Nov 2026 headline
(https://erdosproblemaday.com/progress) reports an independent rebuild and
verification of Kirtchakov's 245 GB proof of **k(3,4) = 21**: 445 formulas
rebuilt to the recorded hash, 445/445 proofs accepted by cake_lpr, 307
byte-identical. This corroborates the prior-art value in our catalog. We found
no claim there about **k(4,4)** or improved bounds for **k(3,5)**; our
circulant witnesses (k(4,4) ≥ 40, k(3,5) ≥ 39) remain bounded improvements
with no novelty claim beyond the certificates.

### A385403

Targeted searches found no public record of a(13)=9 or of our counting proof.
That is a failed search, not proof of novelty. The OEIS entry was unreachable
during this pass (transport error on `oeis.org/A385403` and on the search URL),
so the check is incomplete. Our earlier 2026-11-15 audit remains the baseline.

## Actions taken

1. Correct `math/erdos614-fnk/results/ep614-results.md` in place: the
   "2026-11-19 NEW" labels become "independently re-derived", with this file
   cited.
2. Correct `math/erdos614-fnk/results/ep614-turan-oracle-2026-11-19.md` and
   the project README wording where needed.
3. Add this watch file to the website's research page as a link.

## Standing instruction

Re-run these queries at the start of every session that makes a novelty claim.
A working search tool removes the excuse for the 2026-11-15 style audit gap.
