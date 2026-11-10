#!/usr/bin/env python3
"""Compare every repository whose HEAD moved with the commit the catalog checked, and re-pin what did not change.

    python tools/repin.py diff [IDS...] [--out DIR]     # what changed since last_sha (needs network and git)
    python tools/repin.py apply IDS... --read DATE      # re-pin those entries to the new HEAD

The weekly source check lists repositories whose HEAD moved. A moved HEAD does not mean the entry is
stale, and a green link does not mean it was re-read. `diff` answers the questions a person would ask:

- did the license file change (and how)?
- did the README change (the diff is written to DIR/<id>/README.diff for reading)?
- does every line the catalog cites (projects.toml and components.toml) still say the same thing?
  A cited range whose text is found unchanged in the new file is "same" (possibly at new line
  numbers); anything else is "changed" or "gone" and has to be re-read and re-cited by hand.

`apply` only touches entries you name, refuses any that still has a changed or missing citation, and
sets `checked` to the date you pass: the date a person read the diff, never the date a program ran.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from build import ROOT, load_all
except ImportError:  # imported as tools.repin
    from tools.build import ROOT, load_all

CATALOG_FILES = ("catalog/projects.toml", "catalog/components.toml")
URL = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/(blob|tree)/([0-9a-f]{40})(/[^\s\"#?]*)?(\?plain=1)?(#L(\d+)(?:-L(\d+))?)?")
README_NAMES = ("README.md", "README.rst", "README", "readme.md", "Readme.md", "README.MD")


def git(args: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1", GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, errors="replace", timeout=900, env=env)


def citations(repo: str, sha: str, root: Path = ROOT) -> list[dict]:
    """Every link in the catalog files pinned to this repository at this commit."""
    out = []
    for name in CATALOG_FILES:
        for m in URL.finditer((root / name).read_text()):
            if m.group(1).lower() == repo.lower() and m.group(3) == sha:
                out.append({"file": name, "url": m.group(0), "kind": m.group(2), "path": (m.group(4) or "").lstrip("/"),
                            "start": int(m.group(7)) if m.group(7) else None,
                            "end": int(m.group(8) or m.group(7)) if m.group(7) else None})
    return out


def relocate(old_lines: list[str], new_lines: list[str], start: int, end: int) -> tuple[int, int] | None:
    """Where the cited lines (1-based, inclusive) sit in the new file, if their text is unchanged there.
    When the block occurs more than once, the occurrence nearest the old position wins."""
    block = [l.rstrip() for l in old_lines[start - 1:end]]
    if not block or len(block) != end - start + 1:
        return None
    new = [l.rstrip() for l in new_lines]
    hits = [i for i in range(len(new) - len(block) + 1) if new[i:i + len(block)] == block]
    if not hits:
        return None
    i = min(hits, key=lambda h: abs(h - (start - 1)))
    return i + 1, i + len(block)


def compare(p: dict, root: Path = ROOT, out: Path | None = None, remote: str | None = None) -> dict:
    """Fetch the checked commit and the current HEAD of one project and compare them."""
    repo, old = p["repo"], p["last_sha"]
    tmp = tempfile.mkdtemp(prefix="repin-")
    res: dict = {"id": p["id"], "repo": repo, "old_sha": old}
    try:
        git(["init", "-q", "--bare", tmp])
        git(["remote", "add", "origin", remote or f"https://github.com/{repo}"], cwd=tmp)
        git(["config", "remote.origin.promisor", "true"], cwd=tmp)
        git(["config", "remote.origin.partialclonefilter", "blob:none"], cwd=tmp)
        if git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", "HEAD"], cwd=tmp).returncode:
            return {**res, "error": "could not fetch HEAD"}
        new = git(["rev-parse", "FETCH_HEAD"], cwd=tmp).stdout.strip()
        res.update(new_sha=new, new_date=git(["log", "-1", "--format=%cs", new], cwd=tmp).stdout.strip(), moved=new != old)
        if new == old:
            return res
        if git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", old], cwd=tmp).returncode:
            return {**res, "error": "the checked commit is no longer fetchable"}

        def show(sha: str, path: str) -> str | None:
            r = git(["show", f"{sha}:{path}"], cwd=tmp)
            return r.stdout if r.returncode == 0 else None

        def exists(sha: str, path: str) -> bool:
            return not path or git(["cat-file", "-e", f"{sha}:{path}"], cwd=tmp).returncode == 0

        lic = p.get("license_file") or ""
        if lic:
            a, b = show(old, lic), show(new, lic)
            res["license"] = "same" if a == b else ("gone" if b is None else "changed")
            if a != b and out:
                d = out / p["id"]
                d.mkdir(parents=True, exist_ok=True)
                (d / "LICENSE.diff").write_text("".join(difflib.unified_diff(
                    (a or "").splitlines(True), (b or "").splitlines(True), f"{lic}@{old[:7]}", f"{lic}@{new[:7]}")))
        else:
            names = git(["ls-tree", "--name-only", new], cwd=tmp).stdout.split()
            found = [n for n in names if n.upper().startswith(("LICENSE", "LICENCE", "COPYING"))]
            res["license"] = f"appeared: {', '.join(found)}" if found else "still none"
        readme = next((n for n in README_NAMES if exists(new, n) or exists(old, n)), None)
        if readme:
            a, b = show(old, readme) or "", show(new, readme) or ""
            diff = list(difflib.unified_diff(a.splitlines(True), b.splitlines(True), f"{readme}@{old[:7]}", f"{readme}@{new[:7]}"))
            res["readme"] = {"file": readme, "added": sum(1 for l in diff[2:] if l.startswith("+")),
                             "removed": sum(1 for l in diff[2:] if l.startswith("-"))}
            if diff and out:
                d = out / p["id"]
                d.mkdir(parents=True, exist_ok=True)
                (d / "README.diff").write_text("".join(diff))
        cites = []
        for c in citations(repo, old, root):
            if c["start"] is None:
                c["status"] = "same" if exists(new, c["path"]) else "gone"
            else:
                a, b = show(old, c["path"]), show(new, c["path"])
                if b is None:
                    c["status"] = "gone"
                else:
                    at = relocate((a or "").splitlines(), b.splitlines(), c["start"], c["end"])
                    c["status"] = "changed" if at is None else "same"
                    if at:
                        c["new_start"], c["new_end"] = at
            cites.append(c)
        res["citations"] = cites
        return res
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def new_url(c: dict, old: str, new: str) -> str:
    url = c["url"].replace(old, new)
    if c.get("new_start"):
        anchor = f"#L{c['new_start']}" + (f"-L{c['new_end']}" if c["new_end"] != c["new_start"] else "")
        url = re.sub(r"#L\d+(-L\d+)?$", anchor, url)
    return url


def blockers(r: dict) -> list[str]:
    out = []
    if r.get("error"):
        out.append(r["error"])
    if r.get("license") in ("changed", "gone") or str(r.get("license", "")).startswith("appeared"):
        out.append(f"license file {r['license']}")
    out += [f"citation {c['status']}: {c['url']}" for c in r.get("citations", []) if c["status"] != "same"]
    return out


def apply(results: list[dict], read: str, root: Path = ROOT, force: bool = False) -> list[str]:
    """Re-pin the given entries. Returns the ids that were refused."""
    refused = []
    texts = {name: (root / name).read_text() for name in CATALOG_FILES}
    for r in results:
        if not r.get("moved"):
            continue
        if blockers(r) and not force:
            refused.append(r["id"])
            continue
        old, new = r["old_sha"], r["new_sha"]
        for c in r.get("citations", []):
            if c["status"] == "same":
                texts[c["file"]] = texts[c["file"]].replace(c["url"], new_url(c, old, new))
        pat = re.compile(r'last_commit = "[^"]*"\nlast_sha = "' + old + r'"\nchecked = "[^"]*"')
        texts["catalog/projects.toml"], n = pat.subn(
            f'last_commit = "{r["new_date"]}"\nlast_sha = "{new}"\nchecked = "{read}"', texts["catalog/projects.toml"])
        if n != 1:
            raise SystemExit(f"{r['id']}: expected one last_commit/last_sha/checked block, found {n}")
    for name, text in texts.items():
        (root / name).write_text(text)
    return refused


def render(results: list[dict]) -> str:
    L = ["| Entry | New HEAD | License | README | Cited lines |", "|---|---|---|---|---|"]
    for r in results:
        if r.get("error"):
            L.append(f"| {r['id']} | | | | {r['error']} |")
            continue
        if not r.get("moved"):
            continue
        rd = r.get("readme")
        cites = r.get("citations", [])
        bad = [c for c in cites if c["status"] != "same"]
        moved = sum(1 for c in cites if c.get("new_start") and c["new_start"] != c["start"])
        L.append(f"| {r['id']} | `{r['new_sha'][:7]}` {r['new_date']} | {r.get('license', '')} | "
                 f"{'+%d -%d' % (rd['added'], rd['removed']) if rd else 'none'} | "
                 f"{len(cites) - len(bad)} same ({moved} at new lines), {len(bad)} to re-read |")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["diff", "apply"])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--out", default="repin", help="directory for diffs and repin.json (default: repin/)")
    ap.add_argument("--read", metavar="DATE", help="apply: the date you read the diffs (YYYY-MM-DD)")
    ap.add_argument("--force", action="store_true",
                    help="apply: re-pin although a citation or license changed; fix the remaining links by hand")
    a = ap.parse_args(argv)
    if a.what == "apply" and not (a.ids and a.read and re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.read)):
        ap.error("apply needs the entry ids and --read YYYY-MM-DD")
    projects = [p for p in load_all()["projects"] if p.get("repo") and (not a.ids or p["id"] in a.ids)]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(lambda p: compare(p, out=out), projects))
    (out / "repin.json").write_text(json.dumps(results, indent=1) + "\n")
    print(render(results))
    for r in results:
        for b in blockers(r):
            print(f"RE-READ {r['id']}: {b}")
    if a.what == "apply":
        refused = apply(results, a.read, force=a.force)
        for i in refused:
            print(f"REFUSED {i}: fix its citations by hand first")
        return 1 if refused else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
