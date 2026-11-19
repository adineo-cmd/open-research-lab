# AGENTS.md — standing rules for every agent working in this repo

## ⚠️ RULE 0 — PARAMOUNT: ABSOLUTE UNIQUENESS (owner directive, never override)

**Everything produced here must be unique — no one may have done it before.
Never build anything that has already been built. Research it beforehand:
search the whole internet FIRST.**

Mandatory sequence for every task and finding:

1. **Search before building** — GitHub code search (excluding
   adineo-cmd/*), the wider web, arXiv/Scholar, OEIS (math), published
   survey catalogs (astro). Record exact query strings and dates in the
   deliverable.
2. **Prior art found → do not rebuild.** Find the genuinely new delta or
   pick a different target. Partial overlap is still overlap.
3. **Adversarial audit after** — a dedicated prior-art audit agent
   re-attacks every claim (run every ~10 findings or per session). A
   finding survives only if the auditor genuinely tried to break it.
4. **Corrections in place** — any finding that fails the audit is
   corrected where the original claim lives.

## Rule 1 — IMPROVE PREVIOUS WORK WHEN YOU FIND THE OPPORTUNITY (owner directive)

If during any task you notice something in the lab's prior work that can be
improved — a dangling reference, a stale number, a missing citation, an
uncorrected claim, a missing artifact, a broken link — **fix it in the same
session** (respecting file-walls: only files no other running agent owns).
Improvements are first-class deliverables: list them in your report with
before/after. The lab compounds: every session must leave the repos better
than it found them.

## Fleet rules

- Two agents run concurrently (account cap = 2; a third launch is
  rejected — queue and resume via SendMessage when a slot frees).
- File-wall isolation: agents push ONLY their own directories; shared
  files are edited by the lead when merging agent reports.
- Pushes go through the GitHub MCP (push_files); verify large files
  byte-for-byte after push.

## Role in the lab structure (owner directive, updated 2026-11-19)

`open-research-lab` is now the **single consolidated repo**. The former
`open-discovery-lab` notebook was merged here as `open-discovery-lab/` and its
separate repository (local and GitHub) was retired. `librephone-blob-research`
remains a separate PRIORITY 1 repo; its work is summarised on the website and
its workorders stay at `workorders/` in that repo. The adineo-cmd2 apps are
also summarised on the website.

Open items recorded here: A385403 a(14) (only the 2-regular n=12 case remains),
Erdős #614 f(11,3) in {36,37}, Erdős #112 k(4,4) in [40,50] and k(3,5) in
[31,55], EP614 exact-table extension beyond n=10, and the Track C
format-targets queue.

## Website (owner directive 2026-11-19)

`docs/` is the GitHub Pages source, published at
https://adineo-cmd.github.io/open-research-lab/. Never hand-edit `docs/data.js`:
edit `site/content.json` and run `python3 scripts/build_site_data.py`, which
derives the findings, counts and recent commits from the repository itself.
Every finding and every status shown on the site must already exist in this
repo's record — the site reports work, it does not make claims.

## Repo principles (unchanged — see README.md)

Uniqueness bar · negative results are results · everything reproducible ·
candidates-not-claims · no overclaiming · OEIS filings only for PROVEN
values.
