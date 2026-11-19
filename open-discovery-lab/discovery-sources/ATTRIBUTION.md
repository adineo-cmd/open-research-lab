# ATTRIBUTION — provenance and licenses of aggregated tiers

The **curated** tier (235 entries) is original to this project (CC BY 4.0,
same as lab documentation). The **aggregated** tiers are machine-fetched
from four public registries; this page records what was fetched, from
where, under what license, and when. All fetched content is used with
attribution per each source's terms. Fetched 2026-11-15.

| origin | fetched from | license | entries | fetch status |
|---|---|---|---|---|
| aggregated:awesome-public-datasets | []() | ? | 1120 | ok |
| aggregated:awesome-mcp-servers | []() | ? | 4632 | ok |
| aggregated:dataportals.org | []() | ? | 694 | ok |
| aggregated:zooniverse | []() | ? | 573 | ok |

Fetch notes (honest record):
- awesome-public-datasets: README is README.rst (not .md); parsed with
  scripts/parse.py; ftp:// entries skipped.
- awesome-mcp-servers: 1.6 MB README.md, main branch.
- dataportals.org: /api/3/action/package_search, /data.json and /data
  returned HTTP 404; the live data endpoint /api/data.json was discovered
  via the homepage and used instead.
- Zooniverse: api.zooniverse.org/projects/list (DNS failure),
  www.zooniverse.org/projects.json (404) and talk.zooniverse.org (404)
  all failed after retries; live projects recovered from the official
  Panoptes API (panoptes.zooniverse.org/api/projects, launch_approved
  = true, 12 pages). No open-data license is declared on project
  metadata — entries are names + URLs + short descriptions, used as
  pointers (attribution-based reuse).

Regeneration: see README.md "Reproduce" and scripts/.
