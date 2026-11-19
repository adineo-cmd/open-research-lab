#!/usr/bin/env python3
"""build_project_catalog.py — snapshot the adineo-cmd repository catalog.

Uses the authenticated GitHub CLI if available. The checked-in
site/projects.json is the snapshot the website actually ships, so the site
works without network access; this script is how it gets refreshed.
"""
import json
import os
import subprocess
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "projects.json")
QUERY = ("[.[] | {name:.name, description:(.description // \"\"), "
         "language:(.language // \"\"), stars:.stargazers_count, "
         "forks:.forks_count, updated:(.updated_at // \"\"), "
         "homepage:(.homepage // \"\"), topics:(.topics // []), "
         "archived:.archived, private:.private}]")


def main():
    out = subprocess.check_output(
        ["gh", "api", "users/adineo-cmd/repos?per_page=100&type=owner",
         "--jq", QUERY], text=True)
    repos = json.loads(out)
    repos = [r for r in repos if not r.get("private") and not r.get("archived")]
    repos.sort(key=lambda r: (r.get("updated") or ""), reverse=True)
    payload = {
        "owner": "adineo-cmd",
        "refreshed": datetime.now().strftime("%Y-%m-%d"),
        "count": len(repos),
        "repos": repos,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {OUT}: {len(repos)} public repositories")


if __name__ == "__main__":
    main()
