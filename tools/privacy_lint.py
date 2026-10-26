#!/usr/bin/env python3
"""Catch strings that must not be published: credentials, personal paths, private identifiers.

    python tools/privacy_lint.py                         # generic patterns over tracked and untracked, non-ignored files
    python tools/privacy_lint.py --denylist FILE         # plus your own regexes, one per line (keep FILE out of the repository)
    python tools/privacy_lint.py --history               # also scan every commit's diff, author names, emails and messages

A line containing "privacy-lint: allow" is skipped (used for the pattern definitions and their test fixtures).

The generic patterns run in CI. The denylist is for strings that are themselves private (names, account
fragments, internal project names); it is read from a local file and never committed. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GENERIC = {
    "email address": re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),
    "API key (sk-...)": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "Slack workspace URL": re.compile(r"[A-Za-z0-9-]+\.slack\.com"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "home directory path": re.compile(r"(?:/Users/[^/\s\"']+|/home/[a-z_][^/\s\"']*/|C:\\Users\\[^\\\s\"']+)"),  # privacy-lint: allow
    "named secret-store lookup": re.compile(r"find-generic-password[^\n]*?-s[\"',\s]+(?!YOUR-SERVICE-NAME)[^\s\"',\]]+"),
}
ALLOWED_EMAIL = re.compile(r"(?:^noreply@|@users\.noreply\.github\.com$|@example\.(?:com|org)$|^git@github\.com$)")


def scan_text(text: str, patterns: dict[str, re.Pattern], source: str) -> list[str]:
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        if "privacy-lint: allow" in line:  # for the pattern definitions and their test fixtures
            continue
        for label, pat in patterns.items():
            for m in pat.finditer(line):
                if label == "email address" and ALLOWED_EMAIL.search(m.group(0)):
                    continue
                hits.append(f"{source}:{n}: {label}")
    return hits


def load_denylist(path: Path) -> dict[str, re.Pattern]:
    out = {}
    for i, raw in enumerate(path.read_text().splitlines(), 1):
        raw = raw.strip()
        if raw and not raw.startswith("#"):
            out[f"denylist line {i}"] = re.compile(raw, re.I)
    return out


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, errors="replace", check=True).stdout


def lint_files(patterns: dict[str, re.Pattern]) -> list[str]:
    hits = []
    for rel in git("ls-files", "-co", "--exclude-standard").splitlines():
        path = ROOT / rel
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        hits += scan_text(text, patterns, rel)
    return hits


def lint_history(patterns: dict[str, re.Pattern]) -> list[str]:
    hits = []
    meta = git("log", "--all", "--format=%H%n%an%n%ae%n%cn%n%ce%n%B%n--END--")
    hits += scan_text(meta, patterns, "commit metadata")
    diff = git("log", "--all", "-p", "--no-color", "--format=commit %H")
    hits += scan_text(diff, patterns, "history")
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--denylist", type=Path, help="file of extra regexes, one per line (not committed)")
    ap.add_argument("--history", action="store_true", help="also scan all commits")
    a = ap.parse_args(argv)
    patterns = dict(GENERIC)
    if a.denylist:
        patterns.update(load_denylist(a.denylist))
    hits = lint_files(patterns)
    if a.history:
        hits += lint_history(patterns)
    for h in sorted(set(hits)):
        print("FOUND " + h)
    print(f"privacy lint: {len(set(hits))} problems ({'files and history' if a.history else 'files'}, {len(patterns)} patterns)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
