# discovery-sources — where an agent or a human can do open research, open work, and open discovery

A living registry — currently **7,194 sources** across 21 categories of public websites that offer **real, open work**:
datasets to mine, surveys to search, task queues to join, problems to
solve, formats to decode, competitions to enter, and infrastructure that
lets an AI agent operate on all of it programmatically.

**What this is NOT:** a generic web directory or a list of agent
frameworks. Every entry answers one question — *"what net-new work or
discovery can be done here, and how does an agent get at it?"* Each
curated entry carries `discovery_value` (what can be found/worked on) and
`agent_use` (programmatic access path); aggregated entries carry their
origin list's description plus a category mapping.

## Why this exists (uniqueness statement — Rule 0)

Prior-art searches (2026-11-15, exact queries recorded):

1. Web: `awesome list websites for AI agents research discovery data
   sources registry` — nearest: [e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents)
   and [aloth/awesome-ai-agents](https://github.com/aloth/awesome-ai-agents)
   (agent FRAMEWORKS, not discovery sources).
2. Web: `registry of citizen science projects open research problems task
   queues for volunteers and AI agents` — nearest: [SciStarter](https://scistarter.org)
   (human-only focus; the search itself confirmed no registry mixes
   open-problem task queues for humans AND AI agents).
3. GitHub/web: awesome-public-datasets (datasets only),
   awesome-mcp-servers (MCP servers only), dataportals.org (portals
   only) — each single-purpose; we aggregate them WITH attribution and
   add cross-domain discovery-value metadata.
4. Owner's own repos (adineo-cmd/awesome-website-tools, adineo-cmd/list-of-web)
   are general web directories — not research/discovery-focused, no
   agent-operability annotations.

**Delta:** cross-domain union of *discovery work sources* (not tools, not
frameworks), with per-source `discovery_value` + `agent_use` metadata,
verification status per URL, direct integration with the lab's discovery
engine (`track-c-discovery-engine/targets.md`,
open-research-lab `discovery-engine/`), and the verified
[AGENT-REPOS.md](AGENT-REPOS.md) companion mapping discovery-engine
repositories onto the lab's tracks.

## Layout

| file | what |
|---|---|
| `registry.json` | every entry: name, url, category, access, discovery_value, agent_use, origin, url_status |
| `categories/*.md` | human-browsable tables, one file per category |
| `AGENT-REPOS.md` | verified discovery-engine repositories (skills, autonomous engines, synthesis, evolution loops) |
| `ATTRIBUTION.md` | per-source licenses and fetch provenance |
| `generate_registry.py` | reproduces registry.json + categories/ from the network + `curated_sources.json` |

## Tiers

- **curated** — 235 hand-annotated entries (discovery_value + agent_use),
  URLs curl-checked at creation (`url_status`: 200 / redirect-ok /
  403-bot / error). Grows every session.
- **aggregated** — machine-fetched from attributed public registries
  (awesome-public-datasets: 1099;
  awesome-mcp-servers: 4631;
  dataportals.org: 658; Zooniverse:
  571). Provenance in `ATTRIBUTION.md`. Sample-verified only;
  treat as leads, not facts.

## Standing rule

Entries describe where WORK is open to the public — they do not imply
the lab's claims about any source's contents. License and terms of each
source apply. The owner's exclusions (CVE hunting, classical-cipher
cryptanalysis) are respected in what gets curated.


## Reproduce

```bash
# 1. fetch raw sources (URLs in ATTRIBUTION.md)
# 2. parse:  python3 -I scripts/parse.py
# 3. merge:  python3 scripts/generate_registry.py --agg-dir <dir with fetched_*.json> --curated curated_sources.json
```

Current stats: 7,194 entries, 61 duplicates/invalid removed
at merge; per-category counts in `registry_stats.json`. Generated 2026-11-15.
