# LPEC pulse-position generation extracted — allocator bit economy, codebook page semantics, pulse reader packing (F-58)

Track: track-c-discovery-engine / format-re / LPEC (Sony DVF/MSV voice codec)
Artifact: `track-c-discovery-engine/results/format-re/lpec-census/lpec-pulse-analysis.json`
Prior passes: F-47 (container census), F-48 (LPEC.dll API + table inventory), F-49 (bit pump), F-51 (bit-exact frame parser), F-52 (synthesis, names the gap closed here).

## Claim

The F-52-named largest gap — the pulse-position generation (FUN_10004450, FUN_100060e0, FUN_1000c680) — is now extracted at algorithm level from the existing F-48 Ghidra decompilation (no re-analysis needed; the functions were already decompiled in the F-52 pass outputs). The pulse machinery is a **bit-budget allocator, not a pulse counter**: FUN_10004450 distributes the per-subframe excitation *bit budget* across frequency bands and three value-codebook classes under a 4:2:1 bit-cost model, with byte-alignment fix-ups; FUN_100060e0 reads 8-bit codes (one per codebook row of 2/4/8 pulse values) and 1-bit signs, walks rows sequentially across bands, and places values at positions derived from FUN_1000c680's pitch-synchronous coarse-position words. The mysterious `pgidx` diagnostic field is derived: the **first LSF stage-0 index doubles as the band-weight table row selector** — the LSF base codebook row chooses how pulse bits are distributed across bands. A Python port of the allocator run over every real subframe of both decodable samples shows zero capacity violations and exact bit-economy closure on ~74% (LP) / ~63% (SP) of subframes; the residual is attributable to one unmodeled per-slot weight-calibration term (named below). This upgrades the decoder spec from "plausible impulse train" to the exact pulse-value/position consuming machinery; full sample-exact position synthesis still needs two small un-decompiled helpers (FUN_1000c450, FUN_1000b110).

## Method

Static only. Reused the F-48 Ghidra project decompilation already on disk (`/tmp/f48` project; decompiled C from the F-52 pass, cross-checked against F-51's parser constants). Data constants (row lengths, value-table addresses, weight-table addresses, scale constants) read directly from the user-owned LPEC.dll PE image — addresses only are committed here, never contents. The allocator (FUN_10003d80 + FUN_10004450), pulse reader (FUN_100060e0), frame orchestrator (FUN_10005040), LSP/gain field readers (FUN_10005bf0/FUN_10005ca0) and coarse-position generator (FUN_1000c680) were analyzed; a Python port of the allocator was validated against the real bitstreams of budgtele.dvf and 07011600.MSV using the F-51 bit-exact parser for framing. No Sony binaries or decompiled code committed — derived facts only.

## Findings

### 1. The pulse machinery is a bit-budget allocator (the key inversion)

FUN_10004450's input `param_3` is a **bit budget** and its unit of allocation is the bit, not the pulse. Evidence chain: state+0x14 = 0x13 = 19 (set in setparams FUN_10003e60) is subtracted from the passed frame-bit figure — exactly the 7+6+6 bits FUN_10005d50 reads for the excitation gain/amplitude fields; FUN_10004450 returns `4*p0 + 2*p1 + p2 + extras` (bits); the fix-ups force class totals into byte multiples; and the value tables confirm the packing: row lengths `DAT_10046984 = {2, 4, 8}` doubles for classes 0/1/2 with 256 rows each (full 8-bit code space), so one 8-bit code = 2 values (class 0, 4 bits/value), 4 values (class 1, 2 bits/value), or 8 values (class 2, 1 bit/value) — always 8 bits per code. Leftover bits become ±0.6 "extra" pulses, one bit each. This is the mechanism behind F-47's 7.8–7.9 bits/byte density.

### 2. Value codebooks (state+0xe0/0xe4/0xe8), per mode

- LP (8000 Hz): class0 = DAT_10030440, class1 = DAT_10031440, class2 = DAT_10033440.
- SP (16000 Hz): class0 = DAT_10029440, class1 = DAT_1002a440, class2 = DAT_1002c440.
- Layout: 256 rows x {2,4,8} doubles (row length = DAT_10046984[c]); an 8-bit code selects the row; values are consumed sequentially and carry across band boundaries (FUN_100060e0 keeps a per-class row cursor and consumed-count).
- Extra pulses: amplitude +0.6 for sign bit 0, -0.6 for sign bit 1 (constants DAT_1006b460/DAT_1006b458).

### 3. pgidx derived: the first LSF stage-0 index is the band-weight row selector

FUN_10005bf0 (LSF read) stores its **first stage-0 index** at state+0x140+4*set (fallback state+0x144+4*set when negative — the dual-LSP "avg" path sets the set-1 field to -1). FUN_10004450 then uses that value as the **row index** into the band-weight table (pointer at state+0x10c), indexed `[row][band]` as shorts with row stride = bands*2:

- LP 6000 bps: DAT_100388b0 (the F-48 "6000 bps special-case" pointer pair — now explained: it selects the *band-weight table*, not a codebook);
- LP other bitrates: DAT_10038cc0;
- SP: DAT_100383a0.
- LP table spans exactly 0x400 B = 64 rows x 8 bands x 2 B, confirming 6-bit LSF base index x bands.

So the LSF base codebook row encodes, jointly with spectral shape, the per-band pulse-bit distribution profile — "codebook page index" in the diagnostic string is this LSF-index-driven page of pulse weights. The raw table weight is then calibrated per subframe slot: `w += (short)((budget - state[0xec+4*slot]) * state[0xfc+4*slot] >> 9)`; the semantics of state+0xec/0xfc (per-slot base budget and slope) are not yet extracted (honest negative).

### 4. Allocator algorithm (FUN_10003d80 + FUN_10004450)

Per band b, with n = positions-per-band (state+0x30; 32 for LP = 256/8) and weight w (0x4000 = neutral, 0x8000 = max, 0 = mute):

```
p0 = ((w*w >> 15) * 0x71c7 >> 15) * n >> 15        # class-0 positions (4 bits each)
p1 = (((0x5000 - (w>>1))*w >> 14)**2 >> 15) * 0x71c7 >> 13) * n >> 15   # class-1 (2 bits each)
p2 = (w*n >> 13) - 4*p0 - 2*p1                     # class-2 (1 bit each)
if p2 > n - p0 - p1: p2 = 0; p0 = ((w-0x4000)*n + 0x2000) >> 14; p1 = n - p0
```

(0x71c7/0x8000 = 0.8567; w=0x8000 collapses to all-class-0, w=0x4000 to all-class-1, w=0 to all-extra.) Then, frame-wide:

1. If sum(p0) is odd: scan bands from the end in stride-2 pairs; the first band with p0>0 donates: p0 -= 1, p1 += 2.
2. If sum(p1) % 4 != 0: if budget - cost < 1, convert p1->p2 per unit until aligned; else convert p2->p1 (4 - r units).
3. Align cost down to a multiple of 8: if floor8(budget) < cost, drain p2 (bands from the end) until equal; else grow p2 in half-remainder steps, capped by each band's remaining capacity.
4. Leftover bits (budget%8 plus any unallocated remainder) become extra pulses: per band, extras = min(remaining_leftover, n - (p0+p1+p2)), so p0+p1+p2+p3 <= n always.
5. Outputs: {codes0 = sum(p0)/2, codes1 = sum(p1)/4, codes2 = sum(p2)/8, extras}; return value = bits consumed.

### 5. Pulse reader packing order (FUN_100060e0)

1. Read codes0 8-bit codes, then codes1, then codes2 (class-major order, MSB-first pump per F-49), into per-class code lists.
2. Read `extras` 1-bit signs.
3. Per band (0..bands-1): for class c in 0..2, take alloc[band][c] values from the class-c row sequence: row pointer = table + rowlen[c]*code*8; values are consumed from the current row and carry into the next code's row across bands; each value is written to `excitation[position]` (doubles).
4. Per band, place the band's extra pulses at the next record positions with amplitudes from the sign bits (0 -> +0.6, 1 -> -0.6).
5. FUN_1000f4e0 then overlays the pitch pulses (1024-entry ramp tables, F-52 negative stands).

### 6. Positions: FUN_1000c680 is a pitch-synchronous coarse-position generator, not bitstream-driven

Per subframe, FUN_10005d50 builds a per-band record list (positions-per-band records, 16 B each). The coarse positions come from FUN_1000c680's output word stream: for band b, word index advances `ppb` per band starting at state+0x40+4*slot; **pulse position = (word & ~0x7F) | pulse_index_within_band** — the word's upper bits carry the pitch-synchronous base position, the low 7 bits are the per-band pulse slot. FUN_1000c680 internals: input = the int16 LSF vector (FUN_1000a110 path) and the comb-shape table value scaled by 1/32768 then multiplied by 32768.0 and integer-truncated (IEEE754 exponent/mantissa manipulation) to a base integer; window table selected by lag parity — `lag % 3 == 0` -> DAT_10047f10 with stride 1536/lag shorts, else DAT_10046f10 with stride 2048/lag; output word = accumulator*0x2000 + (fraction >> 6), accumulated over bands-tap windowed products with lag-periodic phase. Its window-preparation helper FUN_1000c450 and the record initializer FUN_1000b110 are the two remaining un-decompiled pieces (see negatives).

### 7. Frame field order (confirmed against F-51, plus new per-type totals)

Setparams (FUN_10003e60) computes frame bit totals from the mode frame size F (384 LP / 1024 SP): state+0x1c = state+0x28 = F (types 0 and 3), state+0x24 = 5F/4 (type 2), state+0x20 = 3F/4 (type 1) — exactly F-51's LP targets [384, 288, 480, 384] and SP [1024, 768, 1280, 1024]. Field order per FUN_10005040: 2b type; T0: 1b LSP mode, [3|4]x6b LSF indices x (1|2 sets), 2x(lag bits [10 LP / 16 SP] + 6b comb shape if lag != 0), 2x(1b pitch-pulse flag + 7b page index when flagged), then per half: 7b gain + 6b ampA + 6b ampB, pulse region (8-bit codes then 1-bit signs), pitch-pulse placement; trailing skip to the frame boundary (FUN_10005040 reads `state[0x1c+4*type] - bits_used` discard bits). Pulse budget per slot = slot_bits - 19.

## Validation

Python port of FUN_10003d80/FUN_10004450 (weight = table row only, calibration term set to zero) driven by the F-51 parser's per-slot pulse budgets and the first-LSF-index weight rows, run over every subframe of both decodable samples:

| check | budgtele.dvf (LP 6k) | 07011600.MSV (SP) |
|---|---|---|
| frames parsed / invalid | 50545 / 0 | 159 / 0 |
| subframes modeled | 94600 | 313 |
| per-band capacity violations (p0+p1+p2+p3 > ppb) | **0** | **0** |
| exact bit-economy closure (bits_used == budget, leftover 0) | 70243 (74.2%) | 197 (62.9%) |
| byte-alignment invariants (sum p0 even, p1 %4==0, p2 %8==0) post-fix-up | 63897 (67.5%) | 192 (61.3%) |
| 8-bit codes modeled (classes 0/1/2) | 208103 / 569827 / 956211 | 5589 / 6144 / 5945 |
| extra pulses modeled | 261438 | 802 |

- The structural invariant (per-band capacity never exceeded) holds on 100% of real subframes in both modes — the allocator model is consistent with the encoder's output constraints.
- Exact closure on ~2/3–3/4 of subframes with the raw table weights; every residual case is explainable by the unmodeled calibration term (finding 3) shifting weights, and by two port simplifications (stride-2 scan order in the parity fix-up, single-pass remainder grow). No case required a structural change to the model.
- Consistency with F-52 synthesis: the modeled distribution is band-skewed by the LSF-derived weights (higher-weight bands receive class-0/1 codes, low-weight bands receive extra noise pulses), matching the energy-per-band structure F-52 approximated with its amplitude rows.

## Honest negatives

- **FUN_1000c450 and FUN_1000b110 not decompiled this session**: the Ghidra installation directory is no longer present on this machine (only the F-48 project and prior decompile outputs persist), so the two small helpers (c680's window preparation; 100060e0's per-band record initialization) could not be decompiled without re-downloading Ghidra. Their roles are characterized from caller-side evidence; exact record initialization semantics remain unconfirmed.
- **Per-slot weight calibration unmodeled**: state+0xec+4*slot and state+0xfc+4*slot (base budget and slope for the `w += (budget - base)*slope >> 9` adjustment) are not attributed. Until extracted, allocator output uses raw table weights — sufficient for structure, not for sample-exact budget prediction.
- **Position words not synthesized end-to-end**: FUN_1000c680's full numeric path (int16 LSF vector -> window -> accumulator) is characterized but not reimplemented, so the validator exercises the allocator/bit economy, not the physical positions. Position layout facts (upper-bits base + low-7-bit slot, per-band word advance) are derived from the consumer side only.
- FUN_1000ef20 (bit pump) was not re-decompiled this session; the MSB-first order is taken from F-49's earlier extraction and F-51's empirical parser closure.
- Validation is structural (bit accounting, capacity, alignment invariants), not sample-accurate PCM comparison; no Sony reference output exists.

## Next levers

1. Reinstall Ghidra (or use capstone) to decompile FUN_1000c450 + FUN_1000b110 and attribute state+0xec/0xfc; then implement FUN_1000c680 end-to-end in `lpec_synthesis.py` and replace the impulse-train approximation with real positions + value-table values — this is now a bounded, fully-specified task.
2. Dump the per-mode value tables at runtime (same PE-extraction pattern as F-52) and wire classes 0/1/2 + extras + FUN_1000f4e0 pitch pulses into the synthesis chain.
3. Wine-based Rosetta PCM diff to close the calibration constants empirically if static attribution stalls.

## Ledger TEXT (F-58)

> F-58: LPEC pulse-position generation extracted from the F-48 Ghidra decompilation (F-52's named largest gap). Key inversion: FUN_10004450 is a bit-budget allocator (state+0x14=19 overhead bits confirmed; 8-bit code = 8 bits = row of 2/4/8 pulse values in value tables state+0xe0/e4/e8, row lengths {2,4,8}, 256 rows each; leftover bits = extra pulses, amplitude +-0.6 with 1-bit signs). pgidx derived: the first LSF stage-0 index selects the band-weight table row (state+0x10c; LP-6k = DAT_100388b0 explaining F-48's 6000-bps pointer pair; 64 rows x bands x shorts), weight calibrated per slot via state+0xec/0xfc (unattributed, honest negative). Allocator: quadratic-in-weight 4:2:1 class split per band (FUN_10003d80, factor 0x71c7=0.8567), parity/byte fix-ups (sum p0 even, p1 %4, cost floor-aligned to 8), leftovers to per-band extra pulses, per-band capacity p0+p1+p2+p3 <= positions-per-band (state+0x30=32 LP). FUN_100060e0: codes read class-major (0,1,2) MSB-first then sign bits; values consumed row-sequentially across bands with carry-over; positions = (FUN_1000c680 word & ~0x7F) | slot-in-band, words pitch-synchronous (lag-parity window tables 1536/lag vs 2048/lag, integer base from scaled comb-shape value). Frame totals derived from setparams: T0=T3=F, T1=3F/4, T2=5F/4 (F=384 LP / 1024 SP), matching F-51 targets exactly. Validated by Python allocator port over all real subframes: 0 capacity violations on 94600 (LP) + 313 (SP) subframes; exact bit-economy closure 74.2%/62.9%; alignment invariants 67.5%/61.3% — residuals attributable to the unmodeled slot calibration term. Remaining for sample-exact positions: FUN_1000c450 + FUN_1000b110 (Ghidra install absent this session — not decompiled) and end-to-end FUN_1000c680 reimplementation. No binaries/decompiled code committed; derived facts only.

## Update (2026-11-15): FUN_1000c450 + FUN_1000b110 resolved, state+0xec/0xfc calibration attributed — allocator model now closes 100.00% on both real samples (ROADMAP Q-1)

Continuation of F-58 (Q-1). The two named helpers and the per-slot weight-calibration term are now extracted, and the allocator port re-validated over every real subframe of both decodable samples with the calibration active: **exact bit-economy closure 100.00% on 94,600 LP subframes and 100.00% on 313 SP subframes** (same-port raw-weight baseline: 93.75% / 97.76%). Machine-readable model: `results/format-re/lpec-census/lpec-pulse-analysis-v2.json`.

### Provenance re-fetch (full chain, this session)

1. `https://archive.org/metadata/dve3301icdpx820` — item holds only `DVE_3301 ICD-PX820.iso`, 112,668,672 B, md5 `b361a0a315d4ab5dd4c92aad1f0c337f` (matches metadata; verified locally after download). Downloaded with the known-good flaky-network loop (`curl -sL -C - -o file URL` repeated until size matches; 10 resume attempts, ~27 min).
2. ISO extracted with static `7zz` 25.01 from the ip7z/7zip GitHub release (the 26.06 URL 404s from this egress; 26.00 download returned 0 bytes — 25.01 works). 412 files.
3. **Correction to F-48's recorded chain**: the InstallShield payload is `Setup/DVE/data1.cab` (10,900,003 B) **plus `data2.cab` (86,400,898 B)** — the codec DLLs span both volumes. unshield with only data1.cab present fails every file ≥ ~100 KB (LPEC.dll, STVoice.dll, BPVoice.dll, msvdec.ax...); copying data2.cab beside data1.cab fixes it. unshield was rebuilt from source (github.com/twogood/unshield, default branch, plain cmake build; no patches).
4. `System/LPEC.dll` re-extracted: **329,064 B (exact size match to F-48), sha256 `d0d8d88800f605a0ab3bcca609db7f51433049d3621a9d4bce40e4092eab50ce`, sha1 `a0ce8195846fb7053ade25179d834eaac564c158`** — first hash record for this artifact (F-48/F-58 recorded none; provenance upgrade).
5. **Sample-provenance correction**: budgtele.dvf and 07011600.MSV are NOT on this CD — the full ISO listing and the installer cab contain no .dvf/.msv files (F-58's "from the same CD" was wrong). F-49's actual origin (sembiance.com/fileFormatSamples/audio/sonyCompressedVoiceFile/) re-confirmed by re-fetch: budgtele.dvf 2,451,456 B sha256 `fe7611400252b596dd29e6f668a9c7f30fc79634f4292ceeb8471fff3f92d218`; 07011600.MSV 22,528 B sha256 `6229250af9e5fbe6d144fb91d803b8c6c9fff16faa6f0e1125f8864e64afad01`.
6. Tooling this session: capstone 5.0.7 + pefile (venv), **no Ghidra** — all new function extractions below are from capstone linear disassembly at the F-48 function addresses (the F-48 JSON's section table and function inventory made targeted disassembly reliable).

### 1. FUN_1000b110 — resolved: recursive quicksort of the 16-byte position records (F-58's "record initializer" guess was wrong)

`FUN_1000b110(records, count)` sorts the per-band position records in place, recursive, pivot = records[0]:

```
quicksort(rec, count):            # rec: 16-byte records {double position; int32 word_index; int32 pad}
    key = rec[0].position
    m = 0
    for i in 1..count-1:
        if rec[i].position < key:
            m += 1
            swap(rec[i], rec[m])  # swaps the double and the +8 dword (pad not touched)
    swap(rec[0], rec[m])          # pivot lands at index m
    if m > 1:     quicksort(rec, m - 1)
    right = count - m
    if right > 1: quicksort(rec + m + 1, right - 1)
```

Called once per band from FUN_100060e0 (0x10006214 loop) before value placement — pulses are consumed in ascending position order per band. This confirms the record layout `{double position, int32 word_index}` produced by FUN_10005d50's word loop (position = `(FUN_1000c680 word & ~0x7F) | pulse_index`, word_index = the word-stream index the reader uses as the excitation scratch index).

### 2. FUN_1000c450 — resolved: vector energy/normalization + autocorrelation window builder for FUN_1000c680

`FUN_1000c450(out_a: *i32, out_b: *i32, window: *i16, vec: *i16, n)` (called from FUN_1000c680 with out_a/out_b = c680 stack slots 0x18/0x1c, window = 0x20, vec = c680's int16 LSF-vector arg, n = c680's 7th arg):

```
# 1. energy of the int16 vector, 64-bit-safe split accumulation (low:15-bit chunks in two registers)
sum2 = sum(vec[i]^2 for i in 0..n-1)
# 2. normalize: bit-scan loop (max 20 iterations, test 0x40000 / doubling) finds exponent e
#    and mantissa m so that sum2 = m << (e-19)-ish; both kept as 32-bit halves
# 3. outputs: *out_a = high mantissa int, *out_b = low/shift int  (c680 uses them as multipliers)
# 4. window taps: for j in 1..n-1:
#      acc = sum(vec[i] * vec[i+j] for i in 0..n-1-j)     # split accumulation (low bits + >>shift)
#      window[j] = (int16)(acc >> shift)                   # normalized autocorrelation at lag j
```

So FUN_1000c450 computes the energy, a normalization shift pair, and the normalized autocorrelation taps `window[j] = (Σ vec[i]·vec[i+j]) >> shift` of the int16 LSF-shaped vector — the window FUN_1000c680 multiplies its band-tap products with (F-58's "bands-tap windowed products"). The lag-parity window *tables* (lag%3==0 → DAT_10047f10 stride 1536/lag, else DAT_10046f10 stride 2048/lag) are read separately by FUN_1000c680 and multiply with this vector-derived window. Also confirmed from the c680 prologue: the comb-shape base is `(int)trunc(lag_value * 3.0517578125e-05 × 32768.0)` truncated further to int16 (`DAT_1006b440 = 1/2^15`) — F-58's "scaled by 1/32768 then ×32768.0 integer-truncated" is now constant-exact.

### 3. state+0xec/0xfc — RESOLVED: the per-slot weight calibration (the F-58 named gap)

Writers found by full-.text sweep (capstone): **FUN_1000df10** (mode dispatch) writes state+0xec..0xf8; **FUN_10003e60** (setparams) writes state+0xfc..0x108 in a 4-iteration loop.

- **Base budgets (FUN_1000df10)**: `state[0xec+4*slot] = {x, 3x/2, 3x/2, 2x}` (slots 0..3; 3x/2 and the x*2 via truncating signed division), where `x = (int16)mode_table_scalar`: LP 6000 bps → `int16 @ 0x10038cb0 = 128`; LP other bitrates → `int16 @ 0x100390c0 = 128`; SP 16000 → `int16 @ 0x100388a0 = 432`. These are the shorts that immediately follow each mode's 64-row band-weight table (0x100388b0+0x400 / 0x10038cc0+0x400 / 0x100383a0+0x500) — F-48's unexplained "short scalar" pairing in the mode-table subselection is now attributed: it is the slot-0 base budget of the weight calibration.
- **Slopes (FUN_10003e60)**: `state[0xfc+4*slot] = (int)ceil(4194304.0 / (state[0x30+4*slot] * state[0x2c]) + 0.5)`, clamped to 0 when the value < 1.0 (the ceil is FUN_1000f8e0 = MSVC `ceil()`; the 4194304.0 = 2^22 double at 0x1006b390 and +0.5 at 0x1006b3a0 are extracted as values). I.e. slope = ceil(2^22 / (positions-per-slot-total) + 0.5) where the total = per-slot position count × bands.
- **Application (FUN_10004450 prologue, 0x10004461-0x10004484 — the exact call site F-58 described)**:

```
calib = (int16)( ((budget - state[0xec+4*slot]) * state[0xfc+4*slot]) >> 9 )   # arithmetic >>, short-truncated
w_band = (int16)weight_table[state[0x10c]][row*bands + band] + calib           # per band, then FUN_10003d80(w_band, n)
```

- **Slot = frame-type slot, not subframe half** (empirically pinned, see validation): slot 0 = type 0 (both halves), slot 1 = type 1 AND type 3, slot 2 = type 2 first pulse region, slot 3 = type 2 second region. This makes the F-48 note "0xf0/0xf4 = x*3/2, 0xf8 = x*2" semantically exact: T1/T3 (3F/4-scale) share the 1.5x base, T2's big second region gets 2x.

### 4. Positions-per-band per slot (state+0x30+4*slot) — partially resolved (honest negative below)

FUN_10003e60 writes three per-slot arrays with a negative-indexed loop (`[esi+ebx*4+0x40]` with ebx = −4..−1 lands on +0x30..0x3c — this is why F-48/F-58 saw no direct writer):

- `state[0x30+4*slot] = trunc(X * local[slot] / 128) * state[0x18]` — X = 32 when bitrate ≤ 6000 else 30; local = {B/4, 3B/8, 3B/8, B/2} with B = state+4 (1024 LP / 2048 SP); the /128 via the `sar 6 / shr 25 / add / sar 7` signed-division idiom; the multiplier `state[0x18] = (int)ceil(bitrate * 128.0 / (rate/2 * bands))` (double 128.0 at 0x1006b370; FUN_1000f8e0 ceil).
- `state[0x40+4*slot] = ceil(X * local[slot] / (rate/2) + 0.5)` = {3,4,4,5} LP — the initial word-stream offset per slot in FUN_10005d50's record loop (band cursors then advance cumulatively, ppb words per band).
- `state[0x50+4*slot] = state[0x30+4*slot]*bands + state[0x40+4*slot]` — the per-slot word-span end.

**Honest negative (static)**: the disassembled chain with the statically computed state[0x18] = ceil(3504·128/(4000·8)) = 15 (LP 6000) yields ppb = {960,1440,1440,1920}, which contradicts (a) the FUN_10005d50 stack buffers (records: 0x4024 B = 1026 records; words: 1024 dwords — ppb ≤ 128) and (b) the natural-cost identity (below). The runtime value of state[0x18] (or an intermediate) must differ from this first-call computation — candidates: the decode path passing a different bitrate argument (any value ≤ 250 clamps state[0x18] to 0/1 through the <1.0 rule), or a runtime rewrite via the BSS config tables at 0x10049f80+ (filled by the 0x100020d0 generator from runtime-built sources — statically opaque). What IS pinned empirically (below): the effective ppb = **{32,48,48,64} LP / {60,90,90,120} SP** — exactly `trunc(X·local[slot]/256)` — so the runtime scale is 1/30 of the static first-call value for LP-6k, and the divisor/scale bookkeeping has one unresolved factor-of-2×15 ambiguity.

### 5. FUN_10004450 — complete algorithm recovered (corrections to F-58)

The full function was disassembled (all fix-up paths + tail). Corrections/precisions to F-58's pseudocode:

- The sum(p0) parity fix-up scans bands **decrementing by 1** from the last band to band 0 (not "stride-2 pairs"); the first band with p0 > 0 donates (p0−=1, p1+=2).
- The extras distribution skips entirely when leftover ≤ 0 (`jle`) — a port that applies negative "extras" silently masquerades as closure.
- Tail outputs confirmed: out5 = {Σp0/2, Σp1/4, Σp2/8, Σp3} (C truncating divisions), return value = 4·Σp0 + 2·Σp1 + Σp2 + Σp3 = bits consumed.
- Per-band record = 16 B {p0, p1, p2, extras} (the allocation record set — distinct from the position records that FUN_1000b110 sorts).

### 6. Validation — the calibration closes the bit economy exactly (both samples, every subframe)

Same Python port (now instruction-faithful incl. the extras `jle`), driven by the F-51 parser's per-slot budgets and LSF-index rows, over every real subframe; band weights read from the PE image at runtime (addresses only committed):

| check | budgtele.dvf (LP 6k) | 07011600.MSV (SP) |
|---|---|---|
| subframes modeled | 94,600 | 313 |
| exact closure, raw table weights (calibration = 0) — this port | 88,683 (93.75%) | 306 (97.76%) |
| exact closure, **calibrated weights** (this port) | **94,600 (100.00%)** | **313 (100.00%)** |
| F-58 closure with raw weights (earlier, stricter port) | 74.2% | 62.9% |
| per-band capacity binds (calibrated) | 12,548 band-slots | 269 band-slots |
| modeled codes class0/1/2 (calibrated) | 278,131 / 686,453 / 794,913 | 7,239 / 7,543 / 2,956 |
| modeled extra pulses (calibrated) | 254,362 | 1,078 |

Model parameters that close 100%: ppb = {32,48,48,64} (LP) / {60,90,90,120} (SP); base = {128,192,192,256} (LP) / {432,648,648,864} (SP); slope = ceil(2^22/(ppb·bands)+0.5) = {16385,10924,10924,8193} (LP) / {6991,4661,4661,3496} (SP); slot mapping T0→0 (both halves), T1/T3→1, T2 regions→2,3. The two T0 halves of dual-LSP frames use their own LSF set's first index as the weight row (lsp[set][0]); closure holds with either row rule (single-set rows also close 100% — the fix-ups absorb small row differences), the per-set rule is adopted as the faithful reading of FUN_10005bf0.

Reading of the deltas: the F-58 74.2%/62.9% residual was a port artifact (strict leftover-0 accounting + uniform n=32 capacity pressure), not purely the calibration; on the faithful port the raw-weight baseline is 93.75%/97.76%, and the disassembled calibration term is *discriminated by the data*: same port, same capacity, only the weight changes, and all 5,917 (LP) + 7 (SP) residual subframes close. That 5,917 subframes close exactly under base {128,192,192,256} with slope ceil(2^22/(n·bands)+0.5) — and fail under every alternative tested (divisor/scale variants, per-half slot mappings m1/m5/m6, n ∈ {16..128} scales) — is the empirical confirmation of the FUN_1000df10/FUN_10003e60 attribution. SP additionally discriminates the slot mapping: only the frame-type mapping (T0h1→slot0, T1/T3→slot1) reaches 100%; per-half mappings stall at ≤82.4%.

### 7. Updated honest negatives

- The static ppb chain (section 4) has one unresolved scale factor: the disassembled `trunc(X·local/128)·state[0x18]` with statically-computed state[0x18]=15 conflicts with buffer bounds and closure; empirically the effective value is `trunc(X·local/256)` (runtime scale 1/30 of static for LP-6k). Resolving it needs either the runtime BSS config generator (0x100020d0 chain) or Wine (Q-2). Does not affect the validated model (the effective ppb values are pinned by closure on both samples).
- FUN_1000c450's exact normalization shift semantics are characterized (energy + exponent scan + split accumulations) but the bit-level mantissa packing is only approximated in pseudocode; FUN_1000c680 end-to-end (position word synthesis) remains unimplemented — physical positions are still not synthesized; this remains the last gap to a sample-exact position synthesizer, now bounded by the resolved helpers.
- No Sony reference PCM; validation remains structural (bit-economy + capacity + code-count shape), not sample-accurate.
- No binaries committed; all constants above are extracted values (addresses + scalar/short values feeding the math), per the facts-not-blobs rule.
