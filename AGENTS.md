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

## Repo principles (unchanged — see README.md)

Uniqueness bar · negative results are results · everything reproducible ·
candidates-not-claims · no overclaiming · OEIS filings only for PROVEN
values.
