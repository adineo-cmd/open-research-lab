#!/usr/bin/env python3
"""Parse fetched registry sources into clean JSON entry lists.
Run with: python3 -I /tmp/registry/scripts/parse.py
Reads raw files from /tmp/registry/raw, writes outputs to /tmp/registry/.
Only records what is actually parsed from the fetched files.
"""
import json
import os
import re
import stat
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit

RAW = "/tmp/registry/raw"
OUT = "/tmp/registry"

TRACKING_PARAMS = {"fbclid"} | {k for k in ["utm_source", "utm_medium", "utm_campaign",
                                            "utm_term", "utm_content", "utm_id", "utm_reader",
                                            "utm_social", "utm_social_source"]}


def clean_url(u):
    """Keep http(s) only; strip tracking params and fragments; return None if not http(s)."""
    if not u:
        return None
    u = u.strip()
    if not re.match(r"^https?://", u, re.I):
        return None
    parts = urlsplit(u)
    if parts.scheme.lower() not in ("http", "https"):
        return None
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")]
    return urlunsplit((parts.scheme.lower(), parts.netloc, parts.path or "/",
                       urlencode(query), ""))


def norm_key(u):
    """Dedupe key: lowercase host+path, strip trailing '/', drop scheme/query/fragment."""
    p = urlsplit(u)
    host = (p.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = (p.path or "").rstrip("/")
    return host + path


def trim300(s):
    s = re.sub(r"\s+", " ", s or "").strip()
    if len(s) > 300:
        s = s[:297].rstrip() + "..."
    return s


def fetch_time(path):
    st = os.stat(path)
    return datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- APD (RST)
def parse_apd():
    path = os.path.join(RAW, "apd_readme.rst")
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    entries, skipped_nonhttp, dropped_dupe = [], 0, 0
    category = None
    seen = set()
    header_re = re.compile(r"^-{3,}\s*$")
    entry_re = re.compile(
        r"^\*\s+\|(?:OK|FIXME)_ICON\|\s+`(.+?)\s*<((?:https?|ftp)://[^>]+)>`_")
    for i, line in enumerate(lines):
        if header_re.match(line) and i > 0 and lines[i - 1].strip():
            category = lines[i - 1].strip()
            continue
        m = entry_re.match(line)
        if not m:
            continue
        text_part, url = m.group(1).strip(), m.group(2).strip()
        cu = clean_url(url)
        if cu is None:
            skipped_nonhttp += 1
            continue
        if " - " in text_part:
            name, desc = text_part.split(" - ", 1)
        else:
            name, desc = text_part, ""
        key = norm_key(cu)
        if key in seen:
            dropped_dupe += 1
            continue
        seen.add(key)
        entries.append({"name": name.strip(), "url": cu, "desc": trim300(desc),
                        "category_raw": category, "origin":
                        "aggregated:awesome-public-datasets"})
    return entries, {"skipped_non_http": skipped_nonhttp, "dupes_removed": dropped_dupe}


# ---------------------------------------------------------------- MCP (MD)
BADGE_RE = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)")


def clean_mcp_category(raw):
    c = re.sub(r'<a name="[^"]*"></a>', "", raw)
    c = re.sub(r"^[^A-Za-z]+", "", c.strip())  # strip emoji/symbols before first letter
    return c.strip()


def parse_mcp():
    path = os.path.join(RAW, "mcp_readme_main.md")
    lines = open(path, encoding="utf-8").read().splitlines()
    entries, skipped_nonhttp, dropped_dupe, no_desc = [], 0, 0, 0
    seen = set()
    h2 = h3 = None
    link_re = re.compile(r"^- \[([^\]]+)\]\((\S+?)\)\s*(.*)$")
    for line in lines:
        m2 = re.match(r"^## (.+?)\s*$", line)
        if m2:
            h2, h3 = m2.group(1).strip(), None
            continue
        m3 = re.match(r"^### (.+?)\s*$", line)
        if m3:
            h3 = clean_mcp_category(m3.group(1))
            continue
        m = link_re.match(line)
        if not m:
            continue
        name, url, rest = m.group(1).strip(), m.group(2).strip(), m.group(3)
        cu = clean_url(url)
        if cu is None:
            skipped_nonhttp += 1
            continue
        category = h3 if (h3 and h2 == "Server Implementations") else h2
        rest = BADGE_RE.sub("", rest)
        rest = rest.strip()
        # strip leading icon cluster (emojis etc.) before the " - " separator
        mm = re.match(r"^(?:[^\w\[]*\s)*+(.*?)(?:\s+-\s+(.*))?$", rest, re.S)
        if mm and mm.group(2) is not None:
            desc = mm.group(2)
        elif rest:
            # no " - " separator found: treat remaining text (minus icons) as desc
            rest2 = re.sub(r"^[^\w\[]*\s*", "", rest)
            desc = rest2 if rest2 and not re.match(r"^[^\w\[]*$", rest) else ""
        else:
            desc = ""
        if not desc.strip():
            no_desc += 1
        key = norm_key(cu)
        if key in seen:
            dropped_dupe += 1
            continue
        seen.add(key)
        entries.append({"name": name, "url": cu, "desc": trim300(desc),
                        "category_raw": category, "origin": "aggregated:awesome-mcp-servers"})
    return entries, {"skipped_non_http": skipped_nonhttp, "dupes_removed": dropped_dupe,
                     "entries_without_desc": no_desc}


# ---------------------------------------------------------------- dataportals
def parse_dataportals():
    path = os.path.join(RAW, "dataportals_data.json")
    data = json.load(open(path, encoding="utf-8"))
    entries, skipped_nonhttp, dropped_dupe = [], 0, 0
    seen = set()
    for slug, p in data.items():
        url = p.get("url") or ""
        cu = clean_url(url)
        if cu is None:
            skipped_nonhttp += 1
            continue
        desc = p.get("description") or p.get("title") or slug
        name = p.get("title") or slug
        key = norm_key(cu)
        if key in seen:
            dropped_dupe += 1
            continue
        seen.add(key)
        entries.append({"name": name, "url": cu, "desc": trim300(desc),
                        "country": (p.get("country") or "").strip(),
                        "region": (p.get("place") or "").strip(),
                        "category_raw": "data portal", "origin": "aggregated:dataportals.org"})
    return entries, {"skipped_non_http": skipped_nonhttp, "dupes_removed": dropped_dupe}


# ---------------------------------------------------------------- Zooniverse
def parse_zooniverse():
    zdir = os.path.join(RAW, "zooniverse")
    pages = sorted(f for f in os.listdir(zdir) if re.match(r"page_\d+\.json$", f))
    entries, skipped_nonhttp, dropped_dupe, no_desc = [], 0, 0, 0
    seen = set()
    for f in pages:
        d = json.load(open(os.path.join(zdir, f), encoding="utf-8"))
        for p in d.get("projects", []):
            slug = p.get("slug") or ""
            name = p.get("display_name") or p.get("title") or slug
            url = f"https://www.zooniverse.org/projects/{slug}" if slug else ""
            cu = clean_url(url)
            if cu is None:
                skipped_nonhttp += 1
                continue
            desc = p.get("description") or p.get("title") or ""
            if not desc.strip():
                no_desc += 1
            key = norm_key(cu)
            if key in seen:
                dropped_dupe += 1
                continue
            seen.add(key)
            entries.append({"name": name, "url": cu, "desc": trim300(desc),
                            "category_raw": "citizen science", "origin": "aggregated:zooniverse"})
    return entries, {"skipped_non_http": skipped_nonhttp, "dupes_removed": dropped_dupe,
                     "entries_without_desc": no_desc}


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def main():
    report = {}
    results = {}
    for label, fn in [("awesome-public-datasets", parse_apd),
                      ("awesome-mcp-servers", parse_mcp),
                      ("dataportals.org", parse_dataportals),
                      ("zooniverse", parse_zooniverse)]:
        entries, stats = fn()
        results[label] = entries
        report[label] = stats
        print(label, "entries:", len(entries), "stats:", stats)

    fname = {"awesome-public-datasets": "fetched_awesome_public_datasets.json",
             "awesome-mcp-servers": "fetched_awesome_mcp_servers.json",
             "dataportals.org": "fetched_dataportals.json",
             "zooniverse": "fetched_zooniverse.json"}
    for label, entries in results.items():
        write_json(os.path.join(OUT, fname[label]), entries)

    # cross-list dedupe, preserving source order
    merged, cross_dupes = [], []
    seen = {}
    for label in ["awesome-public-datasets", "awesome-mcp-servers",
                  "dataportals.org", "zooniverse"]:
        for e in results[label]:
            k = norm_key(e["url"])
            if k in seen:
                cross_dupes.append({"url": e["url"], "kept_origin": seen[k],
                                    "removed_origin": e["origin"],
                                    "removed_name": e["name"]})
                continue
            seen[k] = e["origin"]
            merged.append(e)
    write_json(os.path.join(OUT, "all_entries.json"), merged)

    cross_removed = {}
    for d in cross_dupes:
        cross_removed[d["removed_origin"]] = cross_removed.get(d["removed_origin"], 0) + 1
    per_origin = {}
    for label in results:
        final_in_merged = sum(1 for e in merged if e["origin"] ==
                              results[label][0]["origin"])
        raw_parsed = (len(results[label]) + report[label]["dupes_removed"]
                      + report[label]["skipped_non_http"])
        per_origin[label] = {
            "raw_parsed": raw_parsed,
            "skipped_non_http_url": report[label]["skipped_non_http"],
            "within_duplicates_removed": report[label]["dupes_removed"],
            "after_within_dedupe": len(results[label]),
            "removed_in_cross_dedupe": cross_removed.get(
                results[label][0]["origin"], 0),
            "final_in_merged": final_in_merged,
        }
    dedupe_report = {
        "per_origin_counts": per_origin,
        "duplicates_removed": {
            "within_origin": {label: report[label]["dupes_removed"] for label in results},
            "cross_origin_count": len(cross_dupes),
            "cross_origin_examples": cross_dupes[:20],
            "merged_total": len(merged),
        },
        "note": ("raw_parsed counts entries matching the list-entry syntax in the "
                 "fetched source, including later duplicates. within dedupe keys on "
                 "normalized URL (lowercase host+path, trailing '/' stripped, scheme/"
                 "query/fragment dropped). cross dedupe keeps the first origin in "
                 "order: awesome-public-datasets, awesome-mcp-servers, dataportals.org, "
                 "zooniverse."),
    }
    write_json(os.path.join(OUT, "dedupe_report.json"), dedupe_report)
    print("merged:", len(merged), "cross dupes:", len(cross_dupes))


if __name__ == "__main__":
    sys.exit(main())
