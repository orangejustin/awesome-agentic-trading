#!/usr/bin/env python3
"""Catalog tooling: validate catalog/*.toml and render the generated tables.

    python tools/atlas.py check            # schema + cross-reference checks
    python tools/atlas.py tables           # rewrite docs/catalog/*.md
    python tools/atlas.py tables --check   # fail if the generated files are stale

Standard library only (needs Python 3.11+ for tomllib).
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
OUT = ROOT / "docs" / "catalog"

LAYERS = {
    "data": "Data and point-in-time access",
    "perception": "Perception (text and numbers into signals)",
    "decision": "Decision architectures",
    "alpha": "Alpha and research automation",
    "portfolio": "Portfolio, risk and RL",
    "execution": "Execution and infrastructure",
    "evaluation": "Evaluation, benchmarks and bias control",
    "simulation": "Simulation",
    "survey": "Surveys",
}
PAPER_LAYER_ORDER = ["decision", "perception", "data", "alpha", "portfolio", "evaluation", "survey"]
PROJECT_LAYER_ORDER = ["decision", "perception", "alpha", "portfolio", "data", "execution", "evaluation", "simulation"]
EVIDENCE = {"L0", "L1", "L2", "L3", "L4", "bench", "n/a"}
REPRO = {"full", "partial", "none", "unverified", "n/a"}
READ_PAPER = {"full", "partial", "abstract", "card"}
READ_PROJECT = {"teardown", "readme", "card"}
PROJECT_KINDS = {
    "framework", "platform", "infrastructure", "library", "model", "benchmark", "simulator",
    "backtester", "data", "execution", "experiment", "list",
}
ARXIV = re.compile(r"^\d{4}\.\d{4,5}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


BRIEF_FIELDS = ("tagline", "audience", "limit", "tagline_zh", "audience_zh", "limit_zh")
SNAPSHOT = "2026-10-21"


def load() -> tuple[list[dict], list[dict]]:
    with open(CATALOG / "papers.toml", "rb") as f:
        papers = tomllib.load(f)["paper"]
    with open(CATALOG / "projects.toml", "rb") as f:
        projects = tomllib.load(f)["project"]
    briefs_path = CATALOG / "briefs.toml"
    briefs = tomllib.loads(briefs_path.read_text()) if briefs_path.exists() else {}
    for p in projects:
        if p["id"] in briefs:
            p["brief"] = briefs[p["id"]]
    return papers, projects


def check(papers: list[dict], projects: list[dict]) -> list[str]:
    errs: list[str] = []
    for p in projects:
        if p["kind"] == "list":
            continue
        b = p.get("brief")
        if not b:
            errs.append(f"{p['id']}: no entry in catalog/briefs.toml")
            continue
        for f in BRIEF_FIELDS:
            if not str(b.get(f, "")).strip():
                errs.append(f"{p['id']}: briefs.toml field {f} is empty")
    seen: set[str] = set()
    for p in papers:
        i = p.get("arxiv", "?")
        if not ARXIV.match(i):
            errs.append(f"paper {i}: bad arXiv id")
        if i in seen:
            errs.append(f"paper {i}: duplicate")
        seen.add(i)
        for k in ("title", "first_author", "published", "updated", "layer", "kind", "read", "summary"):
            if not p.get(k):
                errs.append(f"paper {i}: missing {k}")
        for k in ("published", "updated"):
            if p.get(k) and not DATE.match(p[k]):
                errs.append(f"paper {i}: bad date in {k}")
        if p.get("layer") not in LAYERS:
            errs.append(f"paper {i}: unknown layer {p.get('layer')!r}")
        if p.get("read") not in READ_PAPER:
            errs.append(f"paper {i}: unknown read level {p.get('read')!r}")
        if p.get("read") == "card" and not (ROOT / "cards" / f"{i}.json").exists():
            errs.append(f"paper {i}: read=card but cards/{i}.json is missing")
    pids: set[str] = set()
    for p in projects:
        i = p.get("id", "?")
        if i in pids:
            errs.append(f"project {i}: duplicate id")
        pids.add(i)
        for k in ("name", "repo", "kind", "license", "stars", "stars_asof", "last_commit", "last_sha", "evidence", "repro", "read", "summary"):
            if k not in p:
                errs.append(f"project {i}: missing {k}")
        if "/" not in p.get("repo", ""):
            errs.append(f"project {i}: repo must be owner/name")
        if p.get("evidence") not in EVIDENCE:
            errs.append(f"project {i}: unknown evidence {p.get('evidence')!r}")
        if p.get("repro") not in REPRO:
            errs.append(f"project {i}: unknown repro {p.get('repro')!r}")
        if p.get("read") not in READ_PROJECT:
            errs.append(f"project {i}: unknown read level {p.get('read')!r}")
        if p.get("kind") not in PROJECT_KINDS:
            errs.append(f"project {i}: unknown kind {p.get('kind')!r}")
        for lay in p.get("layers", []):
            if lay not in LAYERS:
                errs.append(f"project {i}: unknown layer {lay!r}")
        if p.get("paper") and p["paper"] not in seen:
            errs.append(f"project {i}: paper {p['paper']} not in papers.toml")
        for k in ("last_commit", "stars_asof"):
            if p.get(k) and not DATE.match(p[k]):
                errs.append(f"project {i}: bad date in {k}")
    # every teardown must have a file
    for p in projects:
        if p.get("read") == "teardown":
            tf = ROOT / "docs" / "teardowns" / f"{p['id']}.md"
            if not tf.exists():
                errs.append(f"project {p['id']}: read=teardown but {tf.relative_to(ROOT)} is missing")
    return errs


def esc(s: str) -> str:
    return s.replace("|", "\\|")


def render_papers(papers: list[dict]) -> str:
    lines = [
        "<!-- generated by tools/atlas.py from catalog/papers.toml; do not edit by hand -->",
        "# Papers",
        "",
        f"{len(papers)} papers, grouped by the layer of the trading stack they mainly touch "
        "(see [the domain map](../01-domain-map.md)). Dates are arXiv UTC dates: first version / latest version. "
        "**Read** says how much we read: `full` and `partial` mean we read the paper's method and results; "
        "`abstract` means the abstract only, so treat the one-line summary as a pointer, not a review."
        + (" `card` means a machine-extracted [method card](../cards/index.md) whose quotes a program checked "
           "against the paper text; the gloss has not been checked by a person." if any(p["read"] == "card" for p in papers) else ""),
        "",
    ]
    for lay in PAPER_LAYER_ORDER:
        rows = sorted((p for p in papers if p["layer"] == lay), key=lambda p: p["published"])
        if not rows:
            continue
        lines += [f"## {LAYERS[lay]}", "", "| Paper | First author | v1 / latest | Read | What it is |", "|---|---|---|---|---|"]
        for p in rows:
            title = esc(p["title"])
            link = f"[{title}](https://arxiv.org/abs/{p['arxiv']})"
            read = p["read"] if p["read"] != "card" else f"[card](../cards/{p['arxiv']}.md)"
            fa = p["first_author"] + (" et al." if p["n_authors"] > 1 else "")
            lines.append(f"| {link} | {esc(fa)} | {p['published']} / {p['updated']} | {read} | {esc(p['summary'])} |")
        lines.append("")
    return "\n".join(lines)


def render_projects(projects: list[dict]) -> str:
    lines = [
        "<!-- generated by tools/atlas.py from catalog/projects.toml; do not edit by hand -->",
        "# Projects",
        "",
        f"{len(projects)} repositories. Stars are as displayed on GitHub on 2026-10-21 (PT); license and last commit "
        "come from a shallow clone the same day. **Evidence** is the highest rung of the "
        "[evidence ladder](../02-evidence-ladder.md) that a third party can inspect for the project's headline "
        "performance claim (`bench` = it evaluates other systems; `n/a` = infrastructure or no performance claim). "
        "**Repro** says whether the headline numbers can be regenerated from the repo.",
        "",
    ]
    done: set[str] = set()
    for lay in PROJECT_LAYER_ORDER:
        rows = [p for p in projects if p["kind"] != "list" and p["id"] not in done and (p["layers"] or ["?"])[0] == lay]
        if not rows:
            continue
        lines += [f"## {LAYERS[lay]}", "", "| Project | Stars | Last commit (PT) | License | Evidence | Repro | What it is |", "|---|---|---|---|---|---|---|"]
        for p in rows:
            done.add(p["id"])
            name = p["name"]
            link = f"[{esc(name)}](https://github.com/{p['repo']})"
            if p["read"] == "teardown":
                link += f" ([teardown](../teardowns/{p['id']}.md))"
            summ = esc(p["summary"])
            if p.get("caveat"):
                summ += f" **Note:** {esc(p['caveat'])}"
            lines.append(f"| {link} | {p['stars']} | {p['last_commit']} | {esc(p['license'] or 'none found')} | {p['evidence']} | {p['repro']} | {summ} |")
        lines.append("")
    lists = [p for p in projects if p["kind"] == "list"]
    if lists:
        lines += ["## Curated lists (compared in [the list audit](../03-lists-compared.md))", "",
                  "| List | Stars | Last commit (PT) | License | Size by our count |", "|---|---|---|---|---|"]
        for p in lists:
            lines.append(f"| [{esc(p['name'])}](https://github.com/{p['repo']}) | {p['stars']} | {p['last_commit']} | {esc(p['license'] or 'none found')} | {esc(p['summary'])} |")
        lines.append("")
    return "\n".join(lines)


def non_list(projects: list[dict]) -> list[dict]:
    return [p for p in projects if p["kind"] != "list"]


def render_ladder_summary(projects: list[dict]) -> str:
    rows = non_list(projects)
    ev = {k: sum(1 for p in rows if p["evidence"] == k) for k in ("L0", "L1", "L2", "L3", "L4", "bench", "n/a")}
    rp = {k: sum(1 for p in rows if p["repro"] == k) for k in ("full", "partial", "none", "unverified")}
    return (
        f"Of the {len(rows)} non-list repositories in the [catalog](catalog/projects.md): "
        f"{ev['L0']} at L0, {ev['L1']} at L1, {ev['L2']} at L2, {ev['L3']} at L3, {ev['L4']} at L4, "
        f"{ev['bench']} benchmarks or arenas that evaluate other systems, and {ev['n/a']} infrastructure, data or tooling projects with no performance claim. "
        f"On repro, {rp['full']} are graded \"full\", {rp['partial']} \"partial\", {rp['none']} \"none\", "
        f"and {rp['unverified']} \"unverified\" (we read the README and code but did not rerun them)."
    )


def render_layer_counts(papers: list[dict], projects: list[dict]) -> str:
    rows = non_list(projects)
    out = ["| Layer | Papers (primary layer) | Projects (primary layer) | Projects (any layer) |", "|---|---|---|---|"]
    for lay, label in LAYERS.items():
        np_ = sum(1 for p in papers if p["layer"] == lay)
        prim = sum(1 for p in rows if p["layers"] and p["layers"][0] == lay)
        anyl = sum(1 for p in rows if lay in p["layers"])
        if np_ or prim or anyl:
            out.append(f"| {label} | {np_} | {prim} | {anyl} |")
    out.append(f"| **Total** | **{len(papers)}** | **{len(rows)}** | |")
    return "\n".join(out)


def render_headline(papers: list[dict], projects: list[dict]) -> str:
    rows = non_list(projects)
    teardowns = sum(1 for p in rows if p["read"] == "teardown")
    return f"{len(papers)} papers, {len(rows)} projects, {teardowns} teardowns"


def render_headline_zh(papers: list[dict], projects: list[dict]) -> str:
    rows = non_list(projects)
    teardowns = sum(1 for p in rows if p["read"] == "teardown")
    return f"{len(papers)} 篇论文、{len(rows)} 个项目、{teardowns} 个深度拆解"


def activity(last_commit: str, zh: bool = False) -> str:
    from datetime import date
    days = (date.fromisoformat(SNAPSHOT) - date.fromisoformat(last_commit)).days
    if days <= 90:
        return "活跃" if zh else "active"
    if days <= 365:
        return "放缓" if zh else "slowing"
    return "停更" if zh else "dormant"


def render_directory(projects: list[dict], zh: bool = False) -> str:
    """The home-page project directory: one table per category, short lines from catalog/briefs.toml."""
    sfx = "_zh" if zh else ""
    head = ("| 项目 | 做什么 | 适合谁 | 维护 | 许可证 | 关键限制 |" if zh
            else "| Project | What it does | Suits | Maintained | License | Key limit |")
    titles_zh = {"decision": "决策架构（多智能体、单智能体）", "perception": "感知（文本和数字变信号）", "alpha": "因子与研究自动化",
                 "portfolio": "组合、风控与强化学习", "data": "数据与时点访问", "execution": "执行与基础设施",
                 "evaluation": "评测、基准与偏差控制", "simulation": "模拟"}
    out: list[str] = []
    done: set[str] = set()
    for lay in PROJECT_LAYER_ORDER:
        rows = [p for p in non_list(projects) if p["id"] not in done and p["layers"] and p["layers"][0] == lay]
        if not rows:
            continue
        rows.sort(key=lambda p: -float(p["stars"].rstrip("k")) * (1000 if p["stars"].endswith("k") else 1))
        out += [f"### {titles_zh[lay] if zh else LAYERS[lay]}", "", head, "|---|---|---|---|---|---|"]
        for p in rows:
            done.add(p["id"])
            b = p["brief"]
            name = f"[{esc(p['name'])}](https://github.com/{p['repo']})"
            if p["read"] == "teardown":
                name += f" · [{'拆解' if zh else 'deep dive'}](docs/teardowns/{p['id']}.md)"
            lic = esc(p["license"] or ("未找到" if zh else "none found"))
            out.append(f"| {name} | {esc(b['tagline' + sfx])} | {esc(b['audience' + sfx])} | "
                       f"{activity(p['last_commit'], zh)} | {lic} | {esc(b['limit' + sfx])} |")
        out.append("")
    return "\n".join(out).rstrip("\n")


# (file relative to ROOT, block name, renderer(papers, projects))
INJECTIONS = [
    ("docs/02-evidence-ladder.md", "ladder-summary", lambda pa, pr: render_ladder_summary(pr)),
    ("docs/01-domain-map.md", "layer-counts", render_layer_counts),
    ("README.md", "headline", lambda pa, pr: render_headline(pa, pr)),
    ("README.zh-CN.md", "headline-zh", lambda pa, pr: render_headline_zh(pa, pr)),
    ("README.md", "directory", lambda pa, pr: render_directory(pr)),
    ("README.zh-CN.md", "directory-zh", lambda pa, pr: render_directory(pr, zh=True)),
]


def inject(text: str, name: str, body: str) -> str:
    start, end = f"<!-- atlas:{name} -->", f"<!-- /atlas:{name} -->"
    i, j = text.find(start), text.find(end)
    if i < 0 or j < i:
        raise SystemExit(f"missing marker pair for atlas:{name}")
    if "\n" in body:  # block content (a table) needs its own lines
        body = "\n" + body + "\n"
    return text[: i + len(start)] + body + text[j:]


def apply_injections(papers: list[dict], projects: list[dict], only_check: bool) -> bool:
    ok = True
    for rel, name, fn in INJECTIONS:
        path = ROOT / rel
        if not path.exists():
            continue
        old = path.read_text()
        new = inject(old, name, fn(papers, projects))
        if new != old:
            if only_check:
                ok = False
            else:
                path.write_text(new)
    return ok


def write_or_check(path: Path, text: str, only_check: bool) -> bool:
    text = text.rstrip("\n") + "\n"
    if only_check:
        return path.exists() and path.read_text() == text
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    t = sub.add_parser("tables")
    t.add_argument("--check", action="store_true", help="fail instead of writing when files are stale")
    args = ap.parse_args(argv)

    papers, projects = load()
    errs = check(papers, projects)
    if errs:
        print("\n".join(f"error: {e}" for e in errs), file=sys.stderr)
        return 1
    if args.cmd == "check":
        print(f"ok: {len(papers)} papers, {len(projects)} projects")
        return 0
    ok = write_or_check(OUT / "papers.md", render_papers(papers), args.check)
    ok &= write_or_check(OUT / "projects.md", render_projects(projects), args.check)
    ok &= apply_injections(papers, projects, args.check)
    if args.check and not ok:
        print("error: generated docs are stale; run `python tools/atlas.py tables`", file=sys.stderr)
        return 1
    print("tables up to date" if args.check else "tables written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
