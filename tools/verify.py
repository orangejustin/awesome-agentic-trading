#!/usr/bin/env python3
"""Check the catalog against the live sources.

    python tools/verify.py papers      # arXiv API: title, first-version date, latest-version date
    python tools/verify.py projects    # git ls-remote: does each repository still exist, and has HEAD moved
    python tools/verify.py all [--strict]

`papers` fails on a changed title or first-version date (a retitled or mismatched identifier) and
warns when a newer version exists. `projects` fails when a repository cannot be reached and reports
when HEAD no longer starts with the recorded `last_sha`. `--strict` turns warnings into failures.
Stars, licenses and last-commit dates are read by hand at snapshot time and are not re-checked here.

Standard library only; needs network access and `git` on PATH.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

try:
    from atlas import load
except ImportError:  # imported as tools.verify
    from tools.atlas import load

ATOM = {"a": "http://www.w3.org/2005/Atom"}
API = "http://export.arxiv.org/api/query"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def fetch_arxiv(ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(ids), 40):
        chunk = ids[i:i + 40]
        url = f"{API}?{urllib.parse.urlencode({'id_list': ','.join(chunk), 'max_results': len(chunk)})}"
        req = urllib.request.Request(url, headers={"User-Agent": "agentic-trading-atlas-verify/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            root = ET.fromstring(r.read())
        for e in root.findall("a:entry", ATOM):
            ident = e.findtext("a:id", "", ATOM).rsplit("/abs/", 1)[-1]
            ident = re.sub(r"v\d+$", "", ident)
            out[ident] = {
                "title": e.findtext("a:title", "", ATOM),
                "published": e.findtext("a:published", "", ATOM)[:10],
                "updated": e.findtext("a:updated", "", ATOM)[:10],
            }
        time.sleep(3)  # the API asks for one request every three seconds
    return out


def verify_papers(papers: list[dict], strict: bool) -> int:
    live = fetch_arxiv([p["arxiv"] for p in papers])
    bad = warn = 0
    for p in papers:
        got = live.get(p["arxiv"])
        if not got:
            print(f"FAIL {p['arxiv']}: not found on arXiv")
            bad += 1
            continue
        if norm(got["title"]) != norm(p["title"]):
            print(f"FAIL {p['arxiv']}: title changed\n     catalog: {p['title']}\n     arXiv:   {got['title'].strip()}")
            bad += 1
        if got["published"] != p["published"]:
            print(f"FAIL {p['arxiv']}: first-version date {p['published']} in catalog, {got['published']} on arXiv")
            bad += 1
        if got["updated"] > p["updated"]:
            print(f"WARN {p['arxiv']}: newer version on {got['updated']} (catalog {p['updated']})")
            warn += 1
    print(f"papers: {len(papers)} checked, {bad} failures, {warn} warnings")
    return 1 if bad or (strict and warn) else 0


def ls_remote(repo: str) -> str | None:
    env = {"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    r = subprocess.run(["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
                       capture_output=True, text=True, timeout=60, env=env)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return r.stdout.split()[0]


def verify_projects(projects: list[dict], strict: bool) -> int:
    bad = warn = 0
    for p in projects:
        sha = ls_remote(p["repo"])
        if sha is None:
            print(f"FAIL {p['id']}: {p['repo']} not reachable")
            bad += 1
        elif not sha.startswith(p["last_sha"]):
            print(f"WARN {p['id']}: HEAD moved to {sha[:7]} (catalog {p['last_sha']}, last commit {p['last_commit']})")
            warn += 1
    print(f"projects: {len(projects)} checked, {bad} failures, {warn} warnings")
    return 1 if bad or (strict and warn) else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["papers", "projects", "all"])
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    a = ap.parse_args(argv)
    papers, projects = load()
    rc = 0
    if a.what in ("papers", "all"):
        rc |= verify_papers(papers, a.strict)
    if a.what in ("projects", "all"):
        rc |= verify_projects(projects, a.strict)
    return rc


if __name__ == "__main__":
    sys.exit(main())
