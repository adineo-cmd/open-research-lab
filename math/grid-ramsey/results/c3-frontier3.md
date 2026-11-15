# Results — frontier collapse: T₃(11,13)=30, T₃(11,14)=45, T₃(12,14)=54, T₃(13,14)=74 EXACT; first UBs at 11×12 (17) and 14×14 (93)

Session 2026-11-15 (second sitting; follow-up to F-60
`results/c3-frontier2.md`, same tools unmodified). Goal: UB witnesses at
the sizes where F-60's session had proven lower bounds but had no
witnesses. Outcome: **four of the six attacked sizes collapsed to exact**,
every witness landing exactly on its proven joint-relaxation LB.

## Headline results

| k×n | proven LB (F-60/F-62, OPTIMAL) | SA witness (this session) | status |
|---|---|---|---|
| 11×12 | 15 | **17** (two independent seeds agree) | bracket **15 ≤ T₃(11,12) ≤ 17** — first UB |
| 11×13 | 30 | **30** | **T₃(11,13) = 30 EXACT** |
| 11×14 | 45 | **45** | **T₃(11,14) = 45 EXACT** |
| 12×14 | 54 | **54** | **T₃(12,14) = 54 EXACT** |
| 13×14 | 74 | **74** | **T₃(13,14) = 74 EXACT** |
| 14×14 | 91 | **93** | bracket **91 ≤ T₃(14,14) ≤ 93** — first UB |

All witnesses re-counted by `tools/count_rects.py` and a session-written
naive quad scan (both match; no SA-embedded counter claimed — stdout
summary lines were again truncated by the run wrapper, so counts come
from the two independent post-hoc recounts). SA parameters: single thread,
120–180 s per run, random starts, kick=rows (cells for two runs).

## The structural discovery: the 11×n row is arithmetic — and now exact where tested

F-60 noted the 11-row LBs run 15/30/45 for n = 12/13/14 (+15 per column,
"pattern unexplained"). This session's witnesses make the pattern **exact
at n = 13, 14** and bracket it tight at n = 12 (15 ≤ T ≤ 17). Two of three
points sitting exactly on the arithmetic progression — with the third one
bracketed within 2 of it — is strong evidence the row is exactly
15·(n−11), i.e. **T₃(11,n) = 15(n−11) for n ≥ 12**, but this is a
hypothesis, not a proven theorem: n = 12 itself is open (could be 15, 16,
or 17), and n ≥ 15 is untested. Conjecture recorded here for the next
session to attack (it would also pin the relaxation as exactly tight
along the whole row).

## Current c=3 state of knowledge (all lab-internal; nothing published anywhere per the F-24 audit + 2026-11-15 web checks)

**Exact (13):** T₃(12,7)=0, T₃(13,7)=2, T₃(12,13)=T₃(13,12)=36,
T₃(13,13)=52, **T₃(11,13)=30, T₃(11,14)=45, T₃(12,14)=54, T₃(13,14)=74**.
**Brackets:** 2 ≤ T₃(11,11) ≤ 10 (D-1, the frontier); 18 ≤ T₃(12,12) ≤ 22;
**15 ≤ T₃(11,12) ≤ 17** (first UB this session); **91 ≤ T₃(14,14) ≤ 93**
(first UB this session).

## Honest negatives

1. 14×14 stopped at 93 (LB 91): one 180 s run; a seeded restart from the
   93-witness (240 s, seed 38) and a seeded 11×12 restart (240 s, seed
   39) were queued as this document was written — their outcomes are in
   the certificates only if they improved the bracket (check
   `c3_T3_k14_n14_*` and `c3_T3_k11_n12_*` certificate files for the
   latest).
2. No exact count-model runs; exactness everywhere comes from LB/UB
   composition (the count model times out at these sizes, F-60).
3. The witnesses were found in ≤ 180 s each — the LBs of F-60 were
   evidently tight by a wide margin; no claim is made about uniqueness of
   the witness colorings.

## Certificates (new this session, all dated 2026-11-15)

- Exact: `c3_T3_k11_n13_exact30.json`, `c3_T3_k11_n14_exact45.json`,
  `c3_T3_k12_n14_exact54.json`, `c3_T3_k13_n14_exact74.json`.
- UB: `c3_T3_k11_n12_ub17_seed31.json`, `c3_T3_k11_n12_ub17_seed32.json`,
  `c3_T3_k14_n14_ub93_seed37.json`.

## Reproduce

```bash
python3 tools/sa_ub.py 11 13 --colors 3 --seconds 150 --seed 33 --kick rows  # -> best: 30 (= LB -> exact)
python3 tools/sa_ub.py 11 14 --colors 3 --seconds 150 --seed 34 --kick rows  # -> best: 45 (= LB -> exact)
python3 tools/sa_ub.py 12 14 --colors 3 --seconds 150 --seed 35 --kick cells # -> best: 54 (= LB -> exact)
python3 tools/sa_ub.py 13 14 --colors 3 --seconds 150 --seed 36 --kick rows  # -> best: 74 (= LB -> exact)
python3 tools/sa_ub.py 11 12 --colors 3 --seconds 120 --seed 31 --kick rows  # -> best: 17
python3 tools/sa_ub.py 14 14 --colors 3 --seconds 180 --seed 37 --kick rows  # -> best: 93
python3 tools/count_rects.py --colors 3 results/certificates/c3_T3_k11_n13_exact30.json  # -> rectangles: 30
python3 tools/count_rects.py --colors 3 results/certificates/c3_T3_k12_n14_exact54.json  # -> rectangles: 54
```

Prior art (Rule 0): unchanged from F-60/F-62 — no c≥3 minimum counts
published anywhere (FGGP arXiv:1005.3750 is existence-only; web checks
2026-11-15). All values above are new.
