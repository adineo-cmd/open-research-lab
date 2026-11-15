#!/usr/bin/env python3
"""generate_registry.py — reproduce discovery-sources/registry.json and
categories/*.md from the fetched/aggregated inputs + the curated tier.

Tiers:
  curated    — curated_sources.json (lead-authored; hand-annotated with
               discovery_value + agent_use; URLs curl-verified at creation)
  aggregated — per-origin JSONs produced by scripts/parse.py from the raw
               fetches of four attributed public registries:
                 awesomedata/awesome-public-datasets (README.rst, MIT),
                 punkpeye/awesome-mcp-servers (README.md, MIT),
                 dataportals.org /api/data.json (PDDL-1.0),
                 Zooniverse Panoptes API (launch_approved projects).

Reproduce: fetch the raw sources (see ATTRIBUTION.md for exact URLs),
run scripts/parse.py, then run this script. Nothing is invented here:
entries are only ever read from the fetched parses or curated_sources.json.

Usage: python3 generate_registry.py [--agg-dir /tmp/registry] [--curated curated_sources.json]
"""
import argparse, json, re, os
from collections import Counter

CATEGORIES = [
    "open-data-portals", "life-sciences", "biomedical-clinical",
    "earth-climate-weather", "astronomy-space", "physics-energy",
    "chemistry-materials", "math-computing", "economics-finance",
    "law-policy-gov", "history-humanities-language", "geography-maps",
    "environment-biodiversity", "social-data-news-media",
    "citizen-science-volunteer", "competitions-benchmarks",
    "ml-ai-resources", "agent-infrastructure", "format-re-targets",
    "archives-libraries-dumps", "datasets-general",
]

APD_MAP = {
    "agriculture": "environment-biodiversity", "anatomy": "life-sciences",
    "biology": "life-sciences", "bioinformatics": "life-sciences",
    "genetics/genomics": "life-sciences", "chemistry": "chemistry-materials",
    "materials": "chemistry-materials", "climate/weather": "earth-climate-weather",
    "meteorology": "earth-climate-weather", "earth science": "earth-climate-weather",
    "economics": "economics-finance", "finance": "economics-finance",
    "geology": "geography-maps", "geospatial": "geography-maps",
    "maps": "geography-maps", "government": "law-policy-gov",
    "law": "law-policy-gov", "health/medicine": "biomedical-clinical",
    "medicine": "biomedical-clinical", "pharmacology": "biomedical-clinical",
    "history": "history-humanities-language", "languages": "history-humanities-language",
    "astronomy": "astronomy-space", "physics": "physics-energy",
    "energy": "physics-energy", "machine learning": "ml-ai-resources",
    "social sciences": "social-data-news-media", "sports": "social-data-news-media",
    "time series": "social-data-news-media", "transportation": "geography-maps",
    "music": "history-humanities-language", "art": "history-humanities-language",
    "computers": "math-computing", "network data": "math-computing",
    "software": "math-computing", "psychology": "social-data-news-media",
    "neuroscience": "life-sciences", "ecology": "environment-biodiversity",
}

ORIGIN_CATEGORY = {
    "aggregated:dataportals.org": "open-data-portals",
    "aggregated:zooniverse": "citizen-science-volunteer",
    "aggregated:awesome-mcp-servers": "agent-infrastructure",
}

DEFAULT_AGENT_USE = {
    "aggregated:awesome-mcp-servers": "Connect via MCP (Model Context Protocol) — one server entry per integration.",
    "aggregated:awesome-public-datasets": "Bulk/API dataset per its landing page; load, analyze, mine.",
    "aggregated:dataportals.org": "National/regional portal — harvest its catalog via CKAN/DCAT APIs where offered.",
    "aggregated:zooniverse": "Live citizen-science project — task queue open to public volunteers; classification data via Panoptes.",
}

def norm_url(u):
    if not u: return None
    u = str(u).strip().rstrip("/")
    u = re.sub(r"[?&](utm_[^&]+|fbclid|ref)[^&]*", "", u)
    return u if u.startswith("http") else None

def load_agg(agg_dir, fname, origin):
    p = os.path.join(agg_dir, fname)
    if not os.path.exists(p): return [], {"origin": origin, "entry_count": 0, "fetch_status": "missing (run scripts/parse.py first)"}
    ents = json.load(open(p, encoding="utf-8"))
    out = []
    for e in ents:
        out.append({
            "name": e.get("name") or e.get("title") or "(unnamed)",
            "url": e.get("url"),
            "desc": (e.get("desc") or e.get("notes") or "")[:300],
            "category_raw": e.get("category_raw") or e.get("country") or "General",
            "origin": origin,
            "access": "browse",
            "agent_use": DEFAULT_AGENT_USE[origin],
        })
    meta = {"origin": origin, "entry_count": len(out), "fetch_status": "ok (from cache)"}
    return out, meta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agg-dir", default="/tmp/registry")
    ap.add_argument("--curated", default="curated_sources.json")
    args = ap.parse_args()

    all_entries, meta = [], []
    for fname, origin in [
        ("fetched_awesome_public_datasets.json", "aggregated:awesome-public-datasets"),
        ("fetched_awesome_mcp_servers.json", "aggregated:awesome-mcp-servers"),
        ("fetched_dataportals.json", "aggregated:dataportals.org"),
        ("fetched_zooniverse.json", "aggregated:zooniverse"),
    ]:
        ents, m = load_agg(args.agg_dir, fname, origin)
        all_entries += ents; meta.append(m)

    cur_path = args.curated if os.path.exists(args.curated) else os.path.join(args.agg_dir, args.curated)
    curated = json.load(open(cur_path, encoding="utf-8"))
    for e in curated:
        e["origin"] = "curated"
        e.setdefault("desc", "")
        e.setdefault("access", "browse")
    meta.append({"origin": "curated", "entry_count": len(curated),
                 "fetch_status": "ok (lead-authored, URL-verified at creation; see README tiers)"})
    all_entries += curated

    # dedupe by normalized URL; curated wins (sorted first)
    seen, out, dups = set(), [], 0
    for e in sorted(all_entries, key=lambda x: 0 if x["origin"] == "curated" else 1):
        u = norm_url(e.get("url"))
        if not u or u in seen:
            dups += 1; continue
        seen.add(u); e["url"] = u
        # category
        if e["origin"] == "curated":
            cat = e.get("category") if e.get("category") in CATEGORIES else "datasets-general"
        elif e["origin"] in ORIGIN_CATEGORY:
            cat = ORIGIN_CATEGORY[e["origin"]]
        elif e["origin"] == "aggregated:awesome-public-datasets":
            cat = APD_MAP.get((e.get("category_raw") or "").lower().strip(), "datasets-general")
        else:
            cat = "datasets-general"
        e["category"] = cat
        e.setdefault("url_status", "sampled (aggregated tier; per-source license/provenance in ATTRIBUTION.md)")
        out.append(e)

    out.sort(key=lambda e: (CATEGORIES.index(e["category"]), e["name"].lower()))
    json.dump(out, open("registry.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(meta, open("sources_meta.json", "w", encoding="utf-8"), indent=1)

    os.makedirs("categories", exist_ok=True)
    for cat in CATEGORIES:
        rows = [e for e in out if e["category"] == cat]
        if not rows: continue
        with open(f"categories/{cat}.md", "w", encoding="utf-8") as f:
            f.write(f"# {cat} — {len(rows)} sources\n\n")
            f.write("| source | what you can do there | agent access | tier | url check |\n|---|---|---|---|---|\n")
            for e in rows:
                dv = (e.get("discovery_value") or e.get("desc") or "").replace("|", "/")[:220]
                au = (e.get("agent_use") or "").replace("|", "/")[:160]
                tier = "curated" if e["origin"] == "curated" else "aggregated"
                f.write(f"| [{e['name']}]({e['url']}) | {dv} | {au} | {tier} | {e.get('url_status','')} |\n")

    stats = {"total": len(out), "duplicates_or_invalid_removed": dups,
             "by_tier": dict(Counter(e["origin"] for e in out)),
             "by_category": dict(Counter(e["category"] for e in out)),
             "curated_url_status": dict(Counter(e.get("url_status","") for e in out if e["origin"]=="curated"))}
    json.dump(stats, open("registry_stats.json", "w", encoding="utf-8"), indent=1)
    print(json.dumps(stats, indent=1))

if __name__ == "__main__":
    main()
