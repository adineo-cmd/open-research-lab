#!/usr/bin/env python3
"""Write sources_meta.json and run final validation. Run with python3 -I."""
import json
import os

OUT = "/tmp/registry"

sources_meta = [
    {
        "origin": "aggregated:awesome-public-datasets",
        "source_url": "https://raw.githubusercontent.com/awesomedata/awesome-public-datasets/master/README.rst",
        "license": "MIT (LICENSE at repo root, Copyright (c) 2014-2015 Xiaming Chen; GitHub API also reports MIT)",
        "fetched_at": "2026-11-15T12:28:50Z",
        "entry_count": 1108,
        "fetch_status": "ok",
    },
    {
        "origin": "aggregated:awesome-mcp-servers",
        "source_url": "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md",
        "license": "MIT (LICENSE at repo root, Copyright (c) 2024 Frank Fiegel / glama.ai)",
        "fetched_at": "2026-11-15T12:28:00Z",
        "entry_count": 4631,
        "fetch_status": "ok",
    },
    {
        "origin": "aggregated:dataportals.org",
        "source_url": "https://dataportals.org/api/data.json",
        "license": "PDDL-1.0 (Open Data Commons Public Domain Dedication and License, per dataportals.org site footer)",
        "fetched_at": "2026-11-15T12:33:22Z",
        "entry_count": 686,
        "fetch_status": "ok (note: /api/3/action/package_search, /data.json and /data all returned HTTP 404; live data retrieved from the site's actual data endpoint /api/data.json discovered via the homepage)",
    },
    {
        "origin": "aggregated:zooniverse",
        "source_url": "https://panoptes.zooniverse.org/api/projects?page_size=50&launch_approved=true (12 pages, pages 1-12)",
        "license": "none declared for API data (Zooniverse API terms apply; no open-data license on project metadata)",
        "fetched_at": "2026-11-15T12:32:56Z",
        "entry_count": 573,
        "fetch_status": "ok via fallback endpoint (all 3 suggested endpoints failed after 3 tries each: api.zooniverse.org/projects/list = DNS resolution failure x5 attempts; www.zooniverse.org/projects.json = HTTP 404 x3; talk.zooniverse.org/api/projects = HTTP 404 x2. Live projects obtained from the official Panoptes API, filtered server-side to launch_approved=true live public projects)",
    },
]


def load(name):
    return json.load(open(os.path.join(OUT, name), encoding="utf-8"))


def validate(name, entries):
    problems = []
    origins = set()
    bad_url = bad_origin = empty_name = 0
    cats = {}
    for e in entries:
        origins.add(e.get("origin"))
        if not e.get("url", "").startswith(("http://", "https://")):
            bad_url += 1
        if not e.get("name", "").strip():
            empty_name += 1
        if e.get("origin") not in origins and len(origins) > 1:
            pass
        c = e.get("category_raw")
        cats[c] = cats.get(c, 0) + 1
    if len(origins) != 1:
        problems.append(f"multiple origins in single-source file: {origins}")
    if bad_url:
        problems.append(f"{bad_url} non-http(s) urls")
    if empty_name:
        problems.append(f"{empty_name} empty names")
    print(f"{name}: {len(entries)} entries, {len(cats)} categories, origins={origins}")
    for p in problems:
        print("  PROBLEM:", p)
    return len(entries)


def main():
    with open(os.path.join(OUT, "sources_meta.json"), "w", encoding="utf-8") as fh:
        json.dump(sources_meta, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    total = 0
    total += validate("fetched_awesome_public_datasets.json", load("fetched_awesome_public_datasets.json"))
    total += validate("fetched_awesome_mcp_servers.json", load("fetched_awesome_mcp_servers.json"))
    total += validate("fetched_dataportals.json", load("fetched_dataportals.json"))
    total += validate("fetched_zooniverse.json", load("fetched_zooniverse.json"))
    merged = load("all_entries.json")
    print(f"all_entries.json: {len(merged)} merged entries (sum of fetched files = {total})")
    r = load("dedupe_report.json")
    print("dedupe_report per_origin:", json.dumps(r["per_origin_counts"]))
    print("cross_origin_count:", r["duplicates_removed"]["cross_origin_count"],
          "merged_total:", r["duplicates_removed"]["merged_total"])
    cross = r["duplicates_removed"]["cross_origin_count"]
    within = sum(r["per_origin_counts"][k]["within_duplicates_removed"]
                 for k in r["per_origin_counts"])
    assert len(merged) == total - cross, "merged != sum(fetched) - cross dupes"
    urls = set()
    for e in merged:
        urls.add(e["url"].lower().rstrip("/"))
    print("unique normalized urls in merged:", len(urls))
    sm = load("sources_meta.json")
    print("sources_meta entries:", len(sm), "| origins:", [s["origin"] for s in sm])
    print("licenses:", [s["license"][:40] for s in sm])
    print("ALL FILES:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
