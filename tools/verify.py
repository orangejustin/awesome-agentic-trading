#!/usr/bin/env python3
"""Check the catalog against the live sources and write a report of what moved.

    python tools/verify.py papers      # arXiv API: title, first-version date, latest-version date
    python tools/verify.py projects    # each repository: reachable, HEAD moved, license file changed, archived
    python tools/verify.py links       # article, milestone and pinned evidence links: alive, dead, or unverifiable
    python tools/verify.py all [--report DIR] [--strict]

A green run is not a promise that every source still says what the catalog says; it says that
nothing changed in a way a program can see. The report lists everything that moved so a person
can re-check it:

- **Failures** (exit code 1): a repository that cannot be reached, a repository newly archived
  upstream, a license file that changed or disappeared since the checked commit, a paper whose
  title or first-version date changed, a link that returns 404 or 410.
- **To re-check**: a repository whose HEAD moved since `last_sha` (with the new commit and its
  date), a paper with a newer version. Normal for active projects; `--strict` makes them fail.
- **Unverifiable**: a link that refused the checker (403, 429, timeouts). Sites that block bots
  are common; these are listed, not failed.

Archive status and GitHub's own license detection need the GitHub API: set GITHUB_TOKEN (the
weekly workflow does). Without it those columns read "unknown" and everything else still runs.

`--report DIR` writes report.md and report.json there (the workflow uploads them and appends
report.md to the job summary). Standard library only; needs network access and `git` on PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from build import load_all
except ImportError:  # imported as tools.verify
    from tools.build import load_all

ATOM = {"a": "http://www.w3.org/2005/Atom"}
API = "http://export.arxiv.org/api/query"
UA = "awesome-agentic-trading-verify/2.0 (+https://github.com/orangejustin/awesome-agentic-trading)"
PT = ZoneInfo("America/Los_Angeles")


def finding(kind: str, ident: str, level: str, message: str, **detail) -> dict:
    """level: fail | recheck | unverifiable | ok"""
    return {"kind": kind, "id": ident, "level": level, "message": message, **detail}


# ---------------------------------------------------------------- papers

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def fetch_arxiv(ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(ids), 40):
        chunk = ids[i:i + 40]
        url = f"{API}?{urllib.parse.urlencode({'id_list': ','.join(chunk), 'max_results': len(chunk)})}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
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


def compare_paper(p: dict, got: dict | None) -> list[dict]:
    if not got:
        return [finding("paper", p["arxiv"], "fail", "not found on arXiv")]
    out = []
    if norm(got["title"]) != norm(p["title"]):
        out.append(finding("paper", p["arxiv"], "fail", "title changed", catalog=p["title"], live=got["title"].strip()))
    if got["published"] != p["published"]:
        out.append(finding("paper", p["arxiv"], "fail", "first-version date changed",
                           catalog=p["published"], live=got["published"]))
    if got["updated"] > p["updated"]:
        out.append(finding("paper", p["arxiv"], "recheck", "newer version", catalog=p["updated"], live=got["updated"]))
    return out


def verify_papers(papers: list[dict]) -> list[dict]:
    live = fetch_arxiv([p["arxiv"] for p in papers])
    out: list[dict] = []
    for p in papers:
        out += compare_paper(p, live.get(p["arxiv"])) or [finding("paper", p["arxiv"], "ok", "unchanged")]
    return out


# ---------------------------------------------------------------- projects

def git(args: list[str], cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    env = {"GIT_TERMINAL_PROMPT": "0", "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/local/bin"),
           "HOME": os.environ.get("HOME", "/tmp"), "GIT_LFS_SKIP_SMUDGE": "1"}
    for k in ("HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "no_proxy",
              "SSL_CERT_FILE", "GIT_SSL_CAINFO"):
        if k in os.environ:
            env[k] = os.environ[k]
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


def ls_remote(repo: str) -> str | None:
    r = git(["ls-remote", f"https://github.com/{repo}.git", "HEAD"], timeout=60)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return r.stdout.split()[0]


def commit_facts(repo: str, shas: list[str], license_file: str) -> dict[str, dict]:
    """For each commit: Pacific committer date and the blob id of the license file ('' if absent).

    Fetches only the commit objects (tree:0) and lets git lazily fetch the one root tree it needs."""
    tmp = tempfile.mkdtemp(prefix="verify-")
    try:
        git(["init", "-q", "--bare", tmp])
        git(["remote", "add", "origin", f"https://github.com/{repo}"], cwd=tmp)
        git(["config", "remote.origin.promisor", "true"], cwd=tmp)
        git(["config", "remote.origin.partialclonefilter", "tree:0"], cwd=tmp)
        out: dict[str, dict] = {}
        for sha in shas:
            if git(["fetch", "-q", "--depth", "1", "--filter=tree:0", "origin", sha], cwd=tmp).returncode:
                out[sha] = {"error": "commit not fetchable (rewritten history?)"}
                continue
            ts = git(["log", "-1", "--format=%ct", sha], cwd=tmp).stdout.strip()
            day = datetime.fromtimestamp(int(ts), PT).date().isoformat() if ts else ""
            blob = ""
            if license_file:
                r = git(["rev-parse", "--verify", "--quiet", f"{sha}:{license_file}"], cwd=tmp)
                blob = r.stdout.strip() if r.returncode == 0 else ""
            out[sha] = {"date": day, "license_blob": blob}
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def github_api(repo: str, token: str) -> dict | None:
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}", headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": UA,
        "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        return {"archived": bool(d.get("archived")), "spdx": (d.get("license") or {}).get("spdx_id") or "",
                "pushed_at": d.get("pushed_at", "")}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def compare_project(p: dict, head: str | None, facts: dict[str, dict], api: dict | None) -> list[dict]:
    """Turn what was observed for one repository into findings. Pure, so it can be tested offline."""
    pid = p["id"]
    if head is None:
        return [finding("repo", pid, "fail", "not reachable", repo=p["repo"])]
    out: list[dict] = []
    if api and api["archived"] and p.get("maintenance") != "archived":
        out.append(finding("repo", pid, "fail", "archived upstream but not marked archived in the catalog", repo=p["repo"]))
    lf = p.get("license_file", "")
    old, new = facts.get(p["last_sha"], {}), facts.get(head, {})
    if head != p["last_sha"]:
        out.append(finding("repo", pid, "recheck", "HEAD moved since the checked commit", repo=p["repo"],
                           old_sha=p["last_sha"], new_sha=head, old_date=p["last_commit"], new_date=new.get("date", "")))
        if "error" in old:
            out.append(finding("repo", pid, "recheck", f"checked commit can no longer be fetched ({old['error']})",
                               repo=p["repo"], old_sha=p["last_sha"]))
        if lf and "license_blob" in old and "license_blob" in new:
            if not new["license_blob"]:
                out.append(finding("repo", pid, "fail", f"license file {lf} is gone at HEAD", repo=p["repo"], new_sha=head))
            elif old["license_blob"] and new["license_blob"] != old["license_blob"]:
                out.append(finding("repo", pid, "fail", f"license file {lf} changed since the checked commit",
                                   repo=p["repo"], old_sha=p["last_sha"], new_sha=head))
        elif not lf and new.get("license_blob"):
            pass  # a license file appearing where there was none is good news, reported via HEAD moved
    if api and api["spdx"] and p.get("license_status") in ("declared", "none"):
        out.append(finding("repo", pid, "recheck", f"GitHub now detects a license ({api['spdx']}) where the catalog has none",
                           repo=p["repo"]))
    return out


def verify_projects(projects: list[dict], token: str | None) -> list[dict]:
    out: list[dict] = []
    for p in projects:
        head = ls_remote(p["repo"])
        facts: dict[str, dict] = {}
        if head and head != p["last_sha"]:
            facts = commit_facts(p["repo"], [p["last_sha"], head], p.get("license_file", ""))
        api = github_api(p["repo"], token) if token else None
        found = compare_project(p, head, facts, api)
        if not found:
            found = [finding("repo", p["id"], "ok", "unchanged", repo=p["repo"])]
        for f in found:
            f["archived"] = "unknown" if api is None else ("yes" if api["archived"] else "no")
        out += found
    return out


# ---------------------------------------------------------------- links

X_POST = re.compile(r"^https://(?:x|twitter)\.com/([^/]+)/status/(\d+)")


def classify_http(status: int | None) -> str:
    if status is None:
        return "unverifiable"
    if 200 <= status < 400:
        return "ok"
    if status in (404, 410):
        return "fail"
    return "unverifiable"  # 401, 403, 429, 5xx: the site refused or failed, which says nothing about the page


def http_status(url: str) -> int | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        return None


def check_url(url: str) -> tuple[str, str]:
    """Returns (level, how). X posts are checked through a public mirror's JSON API."""
    m = X_POST.match(url)
    if m:
        status = http_status(f"https://api.fxtwitter.com/{m.group(1)}/status/{m.group(2)}")
        return classify_http(status), f"fxtwitter mirror: {status}"
    status = http_status(url)
    return classify_http(status), f"HTTP {status}"


GH_PINNED = re.compile(r"^https://github\.com/([^/]+/[^/]+)/(?:blob|tree|commit)/([0-9a-f]{7,40})(?:/([^?#]*))?")


def check_pinned(repo: str, sha: str, paths: set[str]) -> dict[str, str]:
    """Check with git that a commit exists and that each path exists at it. Returns {path: level}."""
    tmp = tempfile.mkdtemp(prefix="verify-")
    try:
        git(["init", "-q", "--bare", tmp])
        git(["remote", "add", "origin", f"https://github.com/{repo}"], cwd=tmp)
        git(["config", "remote.origin.promisor", "true"], cwd=tmp)
        git(["config", "remote.origin.partialclonefilter", "blob:none"], cwd=tmp)
        r = git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", sha], cwd=tmp)
        if r.returncode:
            if ls_remote(repo) is None:
                return {p: "unverifiable" for p in paths}  # the host, not the link, is the problem
            return {p: "fail" for p in paths}
        full = git(["rev-parse", "FETCH_HEAD"], cwd=tmp).stdout.strip()
        return {p: ("ok" if not p or git(["cat-file", "-e", f"{full}:{p}"], cwd=tmp).returncode == 0 else "fail")
                for p in paths}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def verify_links(c: dict) -> list[dict]:
    """Articles, milestones and every pinned evidence link. GitHub links pinned to a commit are checked with git
    (does the commit exist, does the file exist at it); everything else over HTTP."""
    targets = [("article", a["url"], a["url"]) for a in c["articles"]]
    targets += [("milestone", m["title"], m["link"]) for m in c["milestones"]]
    targets += [("source", f"{p['id']} ({s['what']})", s["url"]) for p in c["projects"] for s in p.get("sources", [])]
    out: list[dict] = []
    pinned: dict[tuple[str, str], list[tuple[str, str, str, str]]] = {}
    for kind, ident, url in targets:
        m = GH_PINNED.match(url)
        if m:
            pinned.setdefault((m.group(1), m.group(2)), []).append((kind, ident, url, urllib.parse.unquote(m.group(3) or "")))
            continue
        level, how = check_url(url)
        msg = {"ok": "reachable", "fail": "dead link", "unverifiable": "could not be checked"}[level]
        out.append(finding(kind, ident, level, msg, url=url, how=how))
    for (repo, sha), items in pinned.items():
        levels = check_pinned(repo, sha, {path for *_, path in items})
        for kind, ident, url, path in items:
            level = levels[path]
            msg = {"ok": "pinned file exists", "fail": "pinned commit or file not found",
                   "unverifiable": "could not be checked"}[level]
            out.append(finding(kind, ident, level, msg, url=url, how=f"git: {sha[:7]}:{path or '(commit)'}"))
    return out


# ---------------------------------------------------------------- report

def render_report(found: list[dict], when: str) -> str:
    fails = [f for f in found if f["level"] == "fail"]
    rech = [f for f in found if f["level"] == "recheck"]
    unv = [f for f in found if f["level"] == "unverifiable"]
    counts: dict[str, int] = {}
    for f in found:
        counts[f["kind"]] = counts.get(f["kind"], 0) + 1
    L = [f"# Source check, {when}", "",
         "| Checked | " + " | ".join(f"{k}s" for k in sorted(counts)) + " |",
         "|---|" + "---|" * len(counts),
         "| count | " + " | ".join(str(counts[k]) for k in sorted(counts)) + " |", "",
         f"**{len(fails)} failures · {len(rech)} to re-check · {len(unv)} unverifiable.** "
         "Green means nothing changed in a way a program can see, not that every source still says what the catalog says.", ""]
    if fails:
        L += ["## Failures", "", "| Kind | Entry | Problem | Detail |", "|---|---|---|---|"]
        for f in fails:
            detail = ", ".join(f"{k}: {v}" for k, v in f.items() if k not in ("kind", "id", "level", "message", "archived"))
            L.append(f"| {f['kind']} | {f['id']} | {f['message']} | {detail} |")
        L.append("")
    moved = [f for f in rech if f["kind"] == "repo" and "new_sha" in f]
    if moved:
        L += ["## Repositories to re-check (HEAD moved)", "",
              "Update `last_commit`, `last_sha` and `checked` after re-reading the README for changes to order authority, "
              "license and maintenance.", "",
              "| Entry | Checked commit | Now | New commit date | Archived |", "|---|---|---|---|---|"]
        for f in moved:
            old = f"[`{f['old_sha'][:7]}`](https://github.com/{f['repo']}/tree/{f['old_sha']}) ({f['old_date']})"
            new = f"[`{f['new_sha'][:7]}`](https://github.com/{f['repo']}/tree/{f['new_sha']})"
            cmp_ = f"https://github.com/{f['repo']}/compare/{f['old_sha'][:12]}...{f['new_sha'][:12]}"
            L.append(f"| {f['id']} | {old} | {new} ([diff]({cmp_})) | {f.get('new_date', '')} | {f.get('archived', 'unknown')} |")
        L.append("")
    other = [f for f in rech if f not in moved]
    if other:
        L += ["## Other changes to re-check", "", "| Kind | Entry | Change | Detail |", "|---|---|---|---|"]
        for f in other:
            detail = ", ".join(f"{k}: {v}" for k, v in f.items() if k not in ("kind", "id", "level", "message", "archived", "repo"))
            L.append(f"| {f['kind']} | {f['id']} | {f['message']} | {detail} |")
        L.append("")
    if unv:
        L += ["## Unverifiable links", "", "The site refused or failed the request; open these by hand.", "",
              "| Kind | Link | Response |", "|---|---|---|"]
        for f in unv:
            L.append(f"| {f['kind']} | {f.get('url', f['id'])} | {f.get('how', '')} |")
        L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["papers", "projects", "links", "all"])
    ap.add_argument("--strict", action="store_true", help="treat 're-check' findings as failures")
    ap.add_argument("--report", metavar="DIR", help="write report.md and report.json to DIR")
    a = ap.parse_args(argv)
    c = load_all()
    token = os.environ.get("GITHUB_TOKEN") or None
    found: list[dict] = []
    if a.what in ("papers", "all"):
        found += verify_papers(c["papers"])
    if a.what in ("projects", "all"):
        found += verify_projects(c["projects"], token)
    if a.what in ("links", "all"):
        found += verify_links(c)
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = render_report(found, when)
    if a.report:
        d = Path(a.report)
        d.mkdir(parents=True, exist_ok=True)
        (d / "report.md").write_text(report + "\n")
        (d / "report.json").write_text(json.dumps({"when": when, "findings": found}, indent=1) + "\n")
    for f in found:
        if f["level"] != "ok":
            print(f"{f['level'].upper():12} {f['kind']:9} {f['id']}: {f['message']}")
    fails = sum(1 for f in found if f["level"] == "fail")
    rech = sum(1 for f in found if f["level"] == "recheck")
    print(f"{len(found)} checks: {fails} failures, {rech} to re-check")
    return 1 if fails or (a.strict and rech) else 0


if __name__ == "__main__":
    sys.exit(main())
