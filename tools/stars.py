#!/usr/bin/env python3
"""Refresh the star counts in catalog/projects.toml from the GitHub API, and report renamed repositories.

    GITHUB_TOKEN=... python tools/stars.py            # show what would change
    GITHUB_TOKEN=... python tools/stars.py --write    # update stars and stars_asof, then run tools/build.py tables

Stars only order entries within a category; they are never a reason to list something. A repository the
API reports under another name was renamed or transferred: the old address still redirects, so fix `repo`
and its pinned links by hand. Needs a token (any read-only one): the unauthenticated limit is too low.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    from build import ROOT, load_all
    from verify import github_api
except ImportError:  # imported as tools.stars
    from tools.build import ROOT, load_all
    from tools.verify import github_api


def short(n: int) -> str:
    """12345 -> '12.3k', 507 -> '507', the way the catalog writes them."""
    if n < 1000:
        return str(n)
    k = f"{n / 1000:.1f}".rstrip("0").rstrip(".")
    return f"{k}k"


def refresh(text: str, projects: list[dict], fetch, today: str) -> tuple[str, list[str], list[str]]:
    """Returns the new file text, the lines describing each change, and the renames found."""
    changes, renames = [], []
    for p in projects:
        api = fetch(p["repo"])
        if not api or api.get("stars") is None:
            changes.append(f"{p['id']}: no answer, left as is")
            continue
        name = api.get("full_name", "")
        if name and name.lower() != p["repo"].lower():
            renames.append(f"{p['id']}: {p['repo']} is now {name}")
        new = short(api["stars"])
        pat = re.compile(r'(\[\[project\]\]\nid = "' + re.escape(p["id"]) + r'"\n(?:(?!\[\[project\]\]).)*?)'
                         r'stars = "[^"]*"\nstars_asof = "[^"]*"', re.S)
        text, n = pat.subn(lambda m: f'{m.group(1)}stars = "{new}"\nstars_asof = "{today}"', text, count=1)
        if n and new != p.get("stars"):
            changes.append(f"{p['id']}: {p.get('stars') or 'none'} -> {new}")
    return text, changes, renames


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="update catalog/projects.toml")
    a = ap.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("set GITHUB_TOKEN (read-only is enough)", file=sys.stderr)
        return 2
    path = ROOT / "catalog" / "projects.toml"
    projects = [p for p in load_all()["projects"] if p.get("repo") and "stars" in p]
    text, changes, renames = refresh(path.read_text(), projects, lambda r: github_api(r, token), date.today().isoformat())
    print("\n".join(changes) or "no star count changed")
    for r in renames:
        print("RENAMED", r)
    if a.write:
        path.write_text(text)
        print("written; now run: python tools/build.py tables")
    return 1 if renames else 0


if __name__ == "__main__":
    sys.exit(main())
