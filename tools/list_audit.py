#!/usr/bin/env python3
"""Recompute how much the four source lists overlap.

    git clone --depth 1 https://github.com/LLMQuant/awesome-trading-agents            DIR/awesome-trading-agents
    git clone --depth 1 https://github.com/Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers DIR/Awesome-LLM-Quantitative-Trading-Papers
    git clone --depth 1 https://github.com/bettyguo/awesome-llm-trading-agents        DIR/awesome-llm-trading-agents
    git clone --depth 1 https://github.com/WallStreetPete/awesome-open-source-trading DIR/awesome-open-source-trading
    python tools/list_audit.py --src DIR [--json]
    python tools/list_audit.py --src DIR --catalog   # check the catalog against the inclusion rule

A "repo" is any github.com/OWNER/NAME link anywhere in the list's files; a "paper"
is any arxiv.org/(abs|pdf|html)/YYMM.NNNNN link. Links are lower-cased and
trailing punctuation is stripped. This counts links, not curated entries: it
over-counts a list that links to its own repository or to a topic page, and it
cannot tell a recommendation from a mention. The numbers in docs/03-lists-compared.md
come from this script; rerun it before quoting them.

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections import Counter
from pathlib import Path

LISTS = {
    "LLMQuant/awesome-trading-agents": ("awesome-trading-agents", ["README.md"]),
    "Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers": ("Awesome-LLM-Quantitative-Trading-Papers", ["README.md"]),
    "bettyguo/awesome-llm-trading-agents": ("awesome-llm-trading-agents", ["README.md", "entries/**/*"]),
    "WallStreetPete/awesome-open-source-trading": (
        "awesome-open-source-trading",
        ["README.md", "docs/*.md", "data/papers.json", "data/tools.json"],
    ),
}
GH = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
AX = re.compile(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})")
NOT_REPOS = {"topics", "orgs", "sponsors", "features", "marketplace", "settings", "login", "apps"}


def links(root: Path, patterns: list[str]) -> tuple[set[str], set[str]]:
    repos: set[str] = set()
    papers: set[str] = set()
    for pat in patterns:
        for f in sorted(root.glob(pat)):
            if not f.is_file():
                continue
            text = f.read_text(errors="ignore")
            for owner, name in GH.findall(text):
                name = re.sub(r"(\.git|[.#)\]]+)$", "", name)
                if owner.lower() in NOT_REPOS or not name:
                    continue
                repos.add(f"{owner.lower()}/{name.lower()}")
            papers.update(AX.findall(text))
    return repos, papers


def audit(src: Path, exclude_self: bool = True) -> dict:
    per: dict[str, dict[str, set[str]]] = {}
    for label, (folder, patterns) in LISTS.items():
        root = src / folder
        if not root.is_dir():
            raise SystemExit(f"missing clone: {root}")
        repos, papers = links(root, patterns)
        if exclude_self:
            repos.discard(label.lower())
        per[label] = {"repos": repos, "papers": papers}
    out: dict = {"lists": {}, "union": {}, "overlap": {}}
    for kind in ("repos", "papers"):
        count = Counter()
        for v in per.values():
            count.update(v[kind])
        out["union"][kind] = len(count)
        out["overlap"][kind] = {
            "in_2_or_more": sum(1 for n in count.values() if n >= 2),
            "in_3_or_more": sum(1 for n in count.values() if n >= 3),
            "in_all_4": sum(1 for n in count.values() if n == 4),
            "only_in_one": sum(1 for n in count.values() if n == 1),
        }
        out["overlap"][kind]["top"] = [
            {"id": k, "lists": n} for k, n in count.most_common() if n >= 3
        ]
    labels = list(per)
    out["pairwise"] = {
        kind: {a: {b: len(per[a][kind] & per[b][kind]) for b in labels} for a in labels}
        for kind in ("repos", "papers")
    }
    for label, v in per.items():
        others_r = set().union(*(w["repos"] for k, w in per.items() if k != label))
        others_p = set().union(*(w["papers"] for k, w in per.items() if k != label))
        out["lists"][label] = {
            "repos": len(v["repos"]),
            "papers": len(v["papers"]),
            "repos_unique_to_list": len(v["repos"] - others_r),
            "papers_unique_to_list": len(v["papers"] - others_p),
        }
    return out


def render(res: dict) -> str:
    lines = ["| List | GitHub repos linked | arXiv papers linked | Repos found nowhere else | Papers found nowhere else |", "|---|---|---|---|---|"]
    for label, v in res["lists"].items():
        lines.append(f"| {label} | {v['repos']} | {v['papers']} | {v['repos_unique_to_list']} | {v['papers_unique_to_list']} |")
    lines.append("")
    for kind in ("repos", "papers"):
        o = res["overlap"][kind]
        lines.append(
            f"- **{kind}**: {res['union'][kind]} distinct across all four; {o['in_2_or_more']} appear in two or more lists, "
            f"{o['in_3_or_more']} in three or more, {o['in_all_4']} in all four; {o['only_in_one']} appear in exactly one."
        )
    for kind in ("repos", "papers"):
        labels = list(res["pairwise"][kind])
        lines += ["", f"Pairwise {kind} in common (diagonal = the list's own total):", "",
                  "| | " + " | ".join(l.split("/")[0] for l in labels) + " |", "|---|" + "---|" * len(labels)]
        for a in labels:
            lines.append(f"| {a.split('/')[0]} | " + " | ".join(str(res["pairwise"][kind][a][b]) for b in labels) + " |")
    return "\n".join(lines)


def check_catalog(src: Path) -> int:
    """The inclusion rule in docs/07-methodology.md, as a check.

    1. Every arXiv paper that two or more lists link is in catalog/papers.toml.
    2. Every repository that two or more lists link is in catalog/projects.toml or catalog/excluded.toml.
    3. Every catalogued repository is linked by at least one list (the two style references excepted), and so is every
    catalogued paper unless a catalogued repository names it as its paper.
    """
    root = Path(__file__).resolve().parent.parent
    papers = {p["arxiv"] for p in tomllib.loads((root / "catalog" / "papers.toml").read_text())["paper"]}
    projects = tomllib.loads((root / "catalog" / "projects.toml").read_text())["project"]
    repos = {p["repo"].lower() for p in projects}
    style_refs = {p["repo"].lower() for p in projects if p["id"].startswith("ref-")}
    excluded = {e["repo"].lower() for e in tomllib.loads((root / "catalog" / "excluded.toml").read_text())["excluded"]}
    rc, rn, pn = Counter(), Counter(), Counter()
    for label, (folder, patterns) in LISTS.items():
        r, p = links(src / folder, patterns)
        r.discard(label.lower())
        rn.update(r)
        pn.update(p)
        rc.update(r)
    bad = 0
    for pid, n in sorted(pn.items()):
        if n >= 2 and pid not in papers:
            print(f"MISSING paper {pid}: in {n} lists, not in catalog/papers.toml")
            bad += 1
    for rid, n in sorted(rn.items()):
        if n >= 2 and rid not in repos and rid not in excluded:
            print(f"MISSING repo {rid}: in {n} lists, in neither projects.toml nor excluded.toml")
            bad += 1
    project_papers = {p["paper"] for p in projects if p.get("paper")}
    for pid in sorted(papers - set(pn) - project_papers):
        print(f"NOT IN ANY LIST paper {pid}")
        bad += 1
    for rid in sorted(repos - set(rn) - style_refs):
        # a list's own repository is dropped from its link set, so list entries are not flagged here
        if not any(rid == label.lower() for label in LISTS):
            print(f"NOT IN ANY LIST repo {rid}")
            bad += 1
    by_papers = Counter(pn.get(a, 0) for a in papers)
    by_repos = Counter(rn.get(r, 0) for r in repos - style_refs - {l.lower() for l in LISTS})
    fmt = lambda c: ", ".join(f"{k} list{'s' if k != 1 else ''}: {c[k]}" for k in sorted(c))
    print(f"catalogued papers by number of lists linking them -> {fmt(by_papers)}")
    print(f"catalogued repos by number of lists linking them -> {fmt(by_repos)}")
    print(f"catalog check: {len(papers)} papers, {len(repos)} repos, {len(excluded)} exclusions, {bad} problems")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, type=Path, help="directory holding the four clones")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--catalog", action="store_true", help="check the catalog against the inclusion rule")
    ap.add_argument("--keep-self-links", action="store_true", help="do not drop a list's link to its own repo")
    args = ap.parse_args(argv)
    if args.catalog:
        return check_catalog(args.src)
    res = audit(args.src, exclude_self=not args.keep_self_links)
    print(json.dumps(res, indent=1) if args.json else render(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
