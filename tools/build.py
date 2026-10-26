#!/usr/bin/env python3
"""Catalog tooling: validate catalog/*.toml and render every generated page from it.

    python tools/build.py check            # schema + cross-reference checks
    python tools/build.py tables           # rewrite the generated pages and blocks
    python tools/build.py tables --check   # fail if anything generated is stale

The READMEs are views of the catalog: the directory, milestones and counts between
`<!-- gen:NAME -->` markers are written here, in English and Chinese from the same entries,
so the two languages cannot drift. Layer pages (layers/*.md) and the flat catalog
(docs/catalog/*.md) are generated whole.

Standard library only (needs Python 3.11+ for tomllib).
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
OUT = ROOT / "docs" / "catalog"
LAYER_DIR = ROOT / "layers"

SNAPSHOT = "2026-10-21"  # default check date for entries without their own `checked`
EVIDENCE = {"L0", "L1", "L2", "L3", "L4", "bench", "n/a"}
REPRO = {"full", "partial", "none", "unverified", "n/a"}
READ_PAPER = {"full", "partial", "abstract", "card"}
READ_PROJECT = {"teardown", "readme", "card"}
ORDERS = {"live", "paper", "none"}
PROJECT_KINDS = {
    "framework", "platform", "infrastructure", "library", "model", "benchmark", "simulator",
    "backtester", "data", "execution", "experiment", "list", "tool",
}
LIST_CATEGORIES = {"related", "style-reference"}  # kind = "list" entries live outside the five layers
ARTICLE_SOURCES = {"x", "blog", "docs", "news", "newsletter", "podcast", "talk", "paper", "tool-page"}
ARXIV = re.compile(r"^\d{4}\.\d{4,5}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_OR_MONTH = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
BRIEF_FIELDS = ("tagline", "audience", "limit", "tagline_zh", "audience_zh", "limit_zh")

STATUS = {"active": "🟢", "slowing": "🟡", "dormant": "⚪"}
STATUS_ZH = {"active": "活跃", "slowing": "放缓", "dormant": "停更"}
SOURCE_ICON = {"x": "𝕏", "blog": "📝", "docs": "📘", "news": "📰", "newsletter": "📰", "podcast": "🎧",
               "talk": "🎤", "paper": "📄", "tool-page": "🔧"}
READ_ICON = {"full": "📖", "partial": "📖", "card": "🗂️", "abstract": "🔖"}


# ---------------------------------------------------------------- loading

def _toml(name: str) -> dict:
    path = CATALOG / name
    return tomllib.loads(path.read_text()) if path.exists() else {}


def load_layers() -> list[dict]:
    return _toml("layers.toml")["layer"]


def load() -> tuple[list[dict], list[dict]]:
    """Papers and projects (projects carry their home-page brief). Kept for the other tools."""
    papers = _toml("papers.toml")["paper"]
    projects = _toml("projects.toml")["project"]
    briefs = _toml("briefs.toml")
    for p in projects:
        p.setdefault("also", [])
        if p["id"] in briefs:
            p["brief"] = briefs[p["id"]]
    return papers, projects


def load_all() -> dict:
    papers, projects = load()
    return {
        "layers": load_layers(),
        "papers": papers,
        "projects": projects,
        "articles": _toml("articles.toml").get("article", []),
        "milestones": _toml("milestones.toml").get("milestone", []),
    }


# ---------------------------------------------------------------- checks

def check_all(c: dict) -> list[str]:
    errs = check(c["papers"], c["projects"], c["layers"])
    layer_ids = {l["id"] for l in c["layers"]}
    seen: set[str] = set()
    for a in c["articles"]:
        u = a.get("url", "?")
        if u in seen:
            errs.append(f"article {u}: duplicate")
        seen.add(u)
        for k in ("title", "author", "url", "source", "date", "layer", "why", "checked"):
            if not a.get(k):
                errs.append(f"article {u}: missing {k}")
        if a.get("source") not in ARTICLE_SOURCES:
            errs.append(f"article {u}: unknown source {a.get('source')!r}")
        if a.get("layer") not in layer_ids | {"survey"}:
            errs.append(f"article {u}: unknown layer {a.get('layer')!r}")
        if a.get("date") and not DATE_OR_MONTH.match(a["date"]):
            errs.append(f"article {u}: bad date {a['date']!r}")
        if a.get("featured") and not a.get("why_zh"):
            errs.append(f"article {u}: featured articles need why_zh for the Chinese README")
        if not str(u).startswith("https://"):
            errs.append(f"article {u}: url must be https")
        if "slack.com" in str(u):
            errs.append(f"article {u}: private workspace links do not belong in a public list")
    for m in c["milestones"]:
        for k in ("date", "title", "title_zh", "why", "why_zh", "link"):
            if not m.get(k):
                errs.append(f"milestone {m.get('title', '?')}: missing {k}")
        if m.get("date") and not DATE_OR_MONTH.match(m["date"]):
            errs.append(f"milestone {m.get('title')}: bad date {m['date']!r}")
    dates = [m["date"] for m in c["milestones"]]
    if dates != sorted(dates):
        errs.append("milestones.toml: entries must be in date order")
    return errs


def check(papers: list[dict], projects: list[dict], layers: list[dict] | None = None) -> list[str]:
    layers = layers or load_layers()
    layer_ids = {l["id"] for l in layers}
    cat_layer = {cat["id"]: l["id"] for l in layers for cat in l["category"]}
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
        for k in ("title", "first_author", "published", "updated", "layer", "category", "kind", "read", "summary"):
            if not p.get(k):
                errs.append(f"paper {i}: missing {k}")
        for k in ("published", "updated"):
            if p.get(k) and not DATE.match(p[k]):
                errs.append(f"paper {i}: bad date in {k}")
        if p.get("layer") == "survey":
            if p.get("category") != "survey":
                errs.append(f"paper {i}: surveys use category 'survey'")
        elif p.get("layer") not in layer_ids:
            errs.append(f"paper {i}: unknown layer {p.get('layer')!r}")
        elif cat_layer.get(p.get("category")) != p["layer"]:
            errs.append(f"paper {i}: category {p.get('category')!r} is not in layer {p['layer']!r}")
        if p.get("read") not in READ_PAPER:
            errs.append(f"paper {i}: unknown read level {p.get('read')!r}")
        if p.get("read") == "card" and not (ROOT / "cards" / f"{i}.json").exists():
            errs.append(f"paper {i}: read=card but cards/{i}.json is missing")
        if p.get("essential") and not p.get("summary_zh"):
            errs.append(f"paper {i}: essential papers need summary_zh for the Chinese README")
    pids: set[str] = set()
    repos: set[str] = set()
    for p in projects:
        i = p.get("id", "?")
        if i in pids:
            errs.append(f"project {i}: duplicate id")
        pids.add(i)
        r = p.get("repo", "").lower()
        if r in repos:
            errs.append(f"project {i}: repository {r} is already catalogued")
        repos.add(r)
        for k in ("name", "repo", "kind", "license", "last_commit", "last_sha", "evidence", "repro", "read", "summary"):
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
        if p.get("kind") == "list":
            if p.get("category") not in LIST_CATEGORIES:
                errs.append(f"project {i}: lists use category 'related' or 'style-reference'")
        else:
            if p.get("layer") not in layer_ids:
                errs.append(f"project {i}: unknown layer {p.get('layer')!r}")
            elif cat_layer.get(p.get("category")) != p["layer"]:
                errs.append(f"project {i}: category {p.get('category')!r} is not in layer {p['layer']!r}")
            for lay in p.get("also", []):
                if lay not in layer_ids or lay == p.get("layer"):
                    errs.append(f"project {i}: bad cross-listed layer {lay!r}")
        if p.get("orders", "none") not in ORDERS:
            errs.append(f"project {i}: unknown orders {p.get('orders')!r}")
        if p.get("paper") and p["paper"] not in seen:
            errs.append(f"project {i}: paper {p['paper']} not in papers.toml")
        for k in ("last_commit", "stars_asof", "checked"):
            if p.get(k) and not DATE.match(p[k]):
                errs.append(f"project {i}: bad date in {k}")
        if p.get("stars") and not p.get("stars_asof"):
            errs.append(f"project {i}: stars need stars_asof")
        if p.get("read") == "teardown":
            tf = ROOT / "docs" / "teardowns" / f"{p['id']}.md"
            if not tf.exists():
                errs.append(f"project {p['id']}: read=teardown but {tf.relative_to(ROOT)} is missing")
    return errs


# ---------------------------------------------------------------- helpers

def esc(s: str) -> str:
    return s.replace("|", "\\|")


def end(s: str) -> str:
    s = s.strip()
    return s if s[-1:] in ".。!?！？)" else s + "."


def end_zh(s: str) -> str:
    s = s.strip()
    return s if s[-1:] in "。！？）)." else s + "。"


def activity(p: dict) -> str:
    checked = p.get("checked", SNAPSHOT)
    days = (date.fromisoformat(checked) - date.fromisoformat(p["last_commit"])).days
    if days <= 90:
        return "active"
    if days <= 365:
        return "slowing"
    return "dormant"


def stars_num(p: dict) -> float:
    s = str(p.get("stars", "0")).replace(",", "")
    if not s:
        return 0.0
    return float(s.rstrip("k")) * (1000 if s.endswith("k") else 1)


def in_layers(projects: list[dict]) -> list[dict]:
    return [p for p in projects if p["kind"] != "list"]


def listed(projects: list[dict]) -> list[dict]:
    """Projects shown in the directories: in a layer and with released code."""
    return [p for p in in_layers(projects) if not p.get("watch")]


def gh(p: dict) -> str:
    return f"https://github.com/{p['repo']}"


def authors(p: dict) -> str:
    return p["first_author"] + (" et al." if p.get("n_authors", 1) > 1 else "")


def counts(c: dict, layer: str) -> tuple[int, int, int]:
    return (sum(1 for p in listed(c["projects"]) if p["layer"] == layer),
            sum(1 for p in c["papers"] if p["layer"] == layer),
            sum(1 for a in c["articles"] if a["layer"] == layer))


def badges(p: dict, zh: bool, base: str) -> str:
    st = activity(p)
    out = [STATUS[st]]
    lic = p["license"] or ("未找到许可证" if zh else "no license file")
    out.append(f"`{lic}`")
    if p.get("orders") == "live":
        out.append("⚡")
    elif p.get("orders") == "paper":
        out.append("📝")
    if p.get("general"):
        out.append("🧰")
    if p["read"] == "teardown":
        out.append(f"[🔬 {'拆解' if zh else 'deep dive'}]({base}docs/teardowns/{p['id']}.md)")
    return " ".join(out)


# ---------------------------------------------------------------- README blocks

def readme_entry(p: dict, zh: bool) -> str:
    b = p["brief"]
    sfx = "_zh" if zh else ""
    tag = end_zh(b["tagline" + sfx]) if zh else end(b["tagline"])
    lim = end_zh(b["limit" + sfx]) if zh else end(b["limit"])
    also = ""
    return f"- [{p['name']}]({gh(p)}) — {tag} ⚠️ {lim} {badges(p, zh, '')}{also}"


def readme_paper(p: dict, zh: bool) -> str:
    year = p["published"][:4]
    s = p["summary_zh"] if zh else p["summary"]
    return f"- [{p['title']}](https://arxiv.org/abs/{p['arxiv']}) — {authors(p)}, {year}. {s}"


def readme_article(a: dict, zh: bool) -> str:
    icon = SOURCE_ICON[a["source"]]
    why = a["why_zh"] if zh else a["why"]
    return f"- {icon} [{a['title']}]({a['url']}) — {a['author']}, {a['date'][:7]}. {why}"


def render_directory(c: dict, zh: bool = False) -> str:
    out: list[str] = []
    for lay in c["layers"]:
        lid = lay["id"]
        nr, np_, na = counts(c, lid)
        if zh:
            out += [f"## {lay['num']}. {lay['title_zh']}：{lay['tagline_zh']}", "",
                    f"> {lay['question_zh']}", "",
                    f"**{nr} 个仓库 · {np_} 篇论文 · {na} 篇文章** · [完整分层页（英文）→](layers/{lid}.md)", ""]
        else:
            out += [f"## {lay['num']}. {lay['title']}: {lay['tagline']}", "",
                    f"> {lay['question']}", "",
                    f"**{nr} repos · {np_} papers · {na} articles** · [Full layer page →](layers/{lid}.md)", ""]
        for cat in lay["category"]:
            rows = [p for p in listed(c["projects"]) if p["category"] == cat["id"]]
            if not rows:
                continue
            rows.sort(key=lambda p: (-stars_num(p), p["name"].lower()))
            out += [f"### {cat['title_zh'] if zh else cat['title']}", ""]
            out += [readme_entry(p, zh) for p in rows]
            out.append("")
        ess = sorted((p for p in c["papers"] if p["layer"] == lid and p.get("essential")), key=lambda p: p["published"])
        feat = sorted((a for a in c["articles"] if a["layer"] == lid and a.get("featured")), key=lambda a: a["date"])
        if ess or feat:
            out += [f"### {'必读' if zh else 'Essential reading'}", ""]
            out += [readme_paper(p, zh) for p in ess]
            out += [readme_article(a, zh) for a in feat]
            out.append("")
    return "\n".join(out).rstrip("\n")


def render_surveys(c: dict, zh: bool = False) -> str:
    rows = sorted((p for p in c["papers"] if p["layer"] == "survey"), key=lambda p: p["published"])
    out = []
    for p in rows:
        s = p.get("summary_zh") if zh and p.get("summary_zh") else p["summary"]
        out.append(f"- [{p['title']}](https://arxiv.org/abs/{p['arxiv']}) — {authors(p)}, {p['published'][:4]}. {s}")
    return "\n".join(out)


def render_related(c: dict, zh: bool = False) -> str:
    rows = [p for p in c["projects"] if p["kind"] == "list" and p.get("category") == "related"]
    rows.sort(key=lambda p: -stars_num(p))
    out = []
    for p in rows:
        s = p.get("summary_zh") if zh and p.get("summary_zh") else p["summary"]
        out.append(f"- [{p['name']}]({gh(p)}) — {end(s) if not zh else end_zh(s)}")
    return "\n".join(out)


def render_milestones(c: dict, zh: bool = False) -> str:
    head = "| 时间 | 里程碑 | 为什么重要 |" if zh else "| When | Milestone | Why it matters |"
    out = [head, "|---|---|---|"]
    for m in c["milestones"]:
        title = m["title_zh"] if zh else m["title"]
        why = m["why_zh"] if zh else m["why"]
        out.append(f"| {m['date'][:7]} | [{esc(title)}]({m['link']}) | {esc(why)} |")
    return "\n".join(out)


def render_stack(c: dict, zh: bool = False) -> str:
    head = ("| 层 | 回答的问题 | 仓库 | 论文 | 文章 |" if zh else "| Layer | The question it answers | Repos | Papers | Articles |")
    out = [head, "|---|---|---|---|---|"]
    for lay in c["layers"]:
        nr, np_, na = counts(c, lay["id"])
        name = f"{lay['num']}. {lay['title_zh']}" if zh else f"{lay['num']}. {lay['title']}"
        q = lay["question_zh"] if zh else lay["question"]
        out.append(f"| [{name}](layers/{lay['id']}.md) | {q} | {nr} | {np_} | {na} |")
    return "\n".join(out)


def headline(c: dict, zh: bool = False) -> str:
    nr = len(listed(c["projects"]))
    np_ = len(c["papers"])
    na = len(c["articles"])
    nt = sum(1 for p in c["projects"] if p["read"] == "teardown")
    if zh:
        return f"{nr} 个开源仓库 · {np_} 篇论文 · {na} 篇文章与帖子 · {nt} 个深度拆解"
    return f"{nr} open-source repos · {np_} papers · {na} articles and posts · {nt} deep dives"


# ---------------------------------------------------------------- layer pages

def render_layer_page(c: dict, lay: dict) -> str:
    lid = lay["id"]
    nr, np_, na = counts(c, lid)
    rows_all = [p for p in in_layers(c["projects"]) if p["layer"] == lid]
    cross = [p for p in listed(c["projects"]) if lid in p.get("also", [])]
    papers = [p for p in c["papers"] if p["layer"] == lid]
    arts = sorted((a for a in c["articles"] if a["layer"] == lid), key=lambda a: a["date"], reverse=True)
    nav = " · ".join(f"**{l['title']}**" if l["id"] == lid else f"[{l['title']}]({l['id']}.md)" for l in c["layers"])
    L = [
        "<!-- generated by tools/build.py from catalog/*.toml; do not edit by hand -->",
        f"# {lay['num']}. {lay['title']}: {lay['tagline']}",
        "",
        f"[← Home](../README.md) · [The stack](README.md) · {nav}",
        "",
        f"> **{lay['question']}**",
        "",
        f"**Scope.** {lay['scope']}",
        "",
        "**Where it usually breaks:** " + "; ".join(lay["failures"]) + ".",
        "",
        f"**Open gap.** {lay['gaps']}",
        "",
        f"{nr} repos · {np_} papers · {na} articles and posts. "
        "Legend: 🟢 active (last commit within 90 days of the check) · 🟡 slowing (within a year) · ⚪ dormant · "
        "⚡ can place real orders · 📝 paper trading · 🧰 general-purpose tool applied here · "
        "📖 read in full · 🗂️ machine-extracted [method card](../docs/cards/index.md) · 🔖 abstract only.",
        "",
        "## Contents",
        "",
        "- [Repositories](#repositories)",
    ]
    if cross:
        L.append("- [Also relevant from other layers](#also-relevant-from-other-layers)")
    if any(p.get("watch") for p in rows_all):
        L.append("- [Watchlist: announced, code not released](#watchlist-announced-code-not-released)")
    L += ["- [Papers](#papers)", "- [Articles and posts](#articles-and-posts)", "- [Builder notes](#builder-notes)", "",
          "## Repositories", ""]
    for cat in lay["category"]:
        rows = [p for p in rows_all if p["category"] == cat["id"] and not p.get("watch")]
        if not rows:
            continue
        rows.sort(key=lambda p: (-stars_num(p), p["name"].lower()))
        L += [f"### {cat['title']}", "",
              "| Project | What it does | Suits | Status | License | Last commit | Key limit |",
              "|---|---|---|---|---|---|---|"]
        for p in rows:
            b = p["brief"]
            name = f"[{esc(p['name'])}]({gh(p)})"
            if p["read"] == "teardown":
                name += f" · [🔬 deep dive](../docs/teardowns/{p['id']}.md)"
            flags = ""
            if p.get("orders") == "live":
                flags = " ⚡"
            elif p.get("orders") == "paper":
                flags = " 📝"
            if p.get("general"):
                flags += " 🧰"
            lic = esc(p["license"] or "no license file")
            L.append(f"| {name}{flags} | {esc(b['tagline'])} | {esc(b['audience'])} | {STATUS[activity(p)]} {activity(p)} | "
                     f"{lic} | {p['last_commit']} | {esc(b['limit'])} |")
        L.append("")
    if cross:
        L += ["## Also relevant from other layers", "",
              "Listed in their primary layer; they also ship working code for this one.", ""]
        for p in sorted(cross, key=lambda p: p["name"].lower()):
            home = next(l for l in c["layers"] if l["id"] == p["layer"])
            L.append(f"- [{p['name']}]({gh(p)}) — {end(p['brief']['tagline'])} *Primary: [{home['title']}]({home['id']}.md).*")
        L.append("")
    watch = [p for p in rows_all if p.get("watch")]
    if watch:
        L += ["## Watchlist: announced, code not released", "",
              "Repositories that exist and are often cited but do not yet hold the system's code. "
              "They move into the directory when code is released.", ""]
        for p in watch:
            L.append(f"- [{p['name']}]({gh(p)}) — {end(p['brief']['tagline'])} ⚠️ {end(p['brief']['limit'])}")
        L.append("")
    L += ["## Papers", ""]
    if not papers:
        L += ["No catalogued paper has this as its primary layer yet. That gap is itself a finding; "
              "[suggest one](../CONTRIBUTING.md) if you know a good one.", ""]
    for cat in lay["category"]:
        rows = sorted((p for p in papers if p["category"] == cat["id"]), key=lambda p: p["published"])
        if not rows:
            continue
        L += [f"### {cat['title']}", "", "| Paper | Authors, year | Read | Takeaway |", "|---|---|---|---|"]
        for p in rows:
            title = f"[{esc(p['title'])}](https://arxiv.org/abs/{p['arxiv']})"
            if p.get("essential"):
                title = "⭐ " + title
            read = READ_ICON[p["read"]] + " " + (f"[card](../docs/cards/{p['arxiv']}.md)" if p["read"] == "card" else p["read"])
            L.append(f"| {title} | {esc(authors(p))}, {p['published'][:4]} | {read} | {esc(p['summary'])} |")
        L.append("")
    L += ["## Articles and posts", ""]
    if arts:
        L += ["Newest first. Icons: 𝕏 post · 📝 blog · 📘 docs · 📰 news · 🎧 podcast · 📄 paper or report. "
              "A post is listed for the idea it carries; its own performance claims are not verified here.", ""]
        for a in arts:
            L.append(f"- {SOURCE_ICON[a['source']]} [{a['title']}]({a['url']}) — {a['author']}, {a['date']}. {a['why']}")
        L.append("")
    else:
        L += ["None yet. [Suggest an article or thread](../CONTRIBUTING.md#articles-and-posts).", ""]
    L += ["## Builder notes", "",
          "Recommendations from this list's maintainers, distilled from the sources above. They are design advice, "
          "not results reported by those sources.", ""]
    for n in lay.get("note", []):
        L.append(f"- **{n['title']}.** {n['body']}")
    return "\n".join(L)


def render_stack_page(c: dict) -> str:
    L = [
        "<!-- generated by tools/build.py from catalog/layers.toml; do not edit by hand -->",
        "# The agentic trading stack",
        "",
        "[← Home](../README.md)",
        "",
        "Every agentic trading system, however it is marketed, is some arrangement of five layers. "
        "A map by layer shows which jobs a project does, which it leaves to you, and which nobody does well yet. "
        "Each layer page lists the open-source repositories, papers, articles and posts for that layer, "
        "with the failure modes to watch and notes for builders.",
        "",
        "![The five layers](../assets/stack.svg)",
        "",
        "| Layer | The question it answers | Scope | Repos | Papers | Articles |",
        "|---|---|---|---|---|---|",
    ]
    for lay in c["layers"]:
        nr, np_, na = counts(c, lay["id"])
        L.append(f"| [{lay['num']}. {lay['title']}]({lay['id']}.md) | {lay['question']} | {lay['scope']} | {nr} | {np_} | {na} |")
    L += ["",
          "## How entries are placed",
          "",
          "- An entry's **primary layer** is the job it does first; it is listed there. A repository that ships working code "
          "for another layer is cross-listed on that layer's page under \"Also relevant\". A README mention is not enough.",
          "- **Data, Agent, Execution** are the pipeline: see, think, act. **Harness** wraps all three: it is how you run, "
          "test and trust them. **Application** sits on top: end-to-end systems aimed at a use case.",
          "- When it is unclear whether something is an Agent or an Application, ask whether its point is *how* a decision is "
          "made (Agent) or *what job* it does for a user (Application).",
          "- Surveys that span the stack are listed on the [home page](../README.md#surveys).",
          ""]
    return "\n".join(L)


# ---------------------------------------------------------------- flat catalog pages

def render_papers(papers: list[dict], layers: list[dict] | None = None) -> str:
    layers = layers or load_layers()
    lines = [
        "<!-- generated by tools/build.py from catalog/papers.toml; do not edit by hand -->",
        "# Papers",
        "",
        f"{len(papers)} papers, grouped by the layer of the [stack](../../layers/README.md) they mainly touch. "
        "Dates are arXiv UTC dates: first version / latest version. **Read** says how much we read: `full` and "
        "`partial` mean we read the paper's method and results; `abstract` means the abstract only, so treat the "
        "summary as a pointer, not a review; `card` means a machine-extracted [method card](../cards/index.md) whose "
        "quotes a program checked against the paper text (the gloss has not been checked by a person). ⭐ marks essential reading.",
        "",
    ]
    groups = [(l["id"], f"{l['num']}. {l['title']}") for l in layers] + [("survey", "Surveys")]
    for lay, label in groups:
        rows = sorted((p for p in papers if p["layer"] == lay), key=lambda p: p["published"])
        if not rows:
            continue
        lines += [f"## {label}", "", "| Paper | First author | v1 / latest | Read | What it is |", "|---|---|---|---|---|"]
        for p in rows:
            link = ("⭐ " if p.get("essential") else "") + f"[{esc(p['title'])}](https://arxiv.org/abs/{p['arxiv']})"
            read = p["read"] if p["read"] != "card" else f"[card](../cards/{p['arxiv']}.md)"
            lines.append(f"| {link} | {esc(authors(p))} | {p['published']} / {p['updated']} | {read} | {esc(p['summary'])} |")
        lines.append("")
    return "\n".join(lines)


def render_projects(projects: list[dict], layers: list[dict] | None = None) -> str:
    layers = layers or load_layers()
    lines = [
        "<!-- generated by tools/build.py from catalog/projects.toml; do not edit by hand -->",
        "# Projects",
        "",
        f"{len(in_layers(projects))} repositories in the five layers, plus the curated lists this one was built from. "
        "Stars are as displayed on GitHub on the date given and are context, not a quality score. License and last commit "
        "come from a shallow clone on the check date. **Evidence** is the highest rung of the "
        "[evidence ladder](../02-evidence-ladder.md) a third party can inspect for the project's headline "
        "performance claim (`bench` = it evaluates other systems; `n/a` = infrastructure or no performance claim). "
        "**Repro** says whether the headline numbers can be regenerated from the repo.",
        "",
    ]
    for lay in layers:
        rows = [p for p in in_layers(projects) if p["layer"] == lay["id"]]
        if not rows:
            continue
        lines += [f"## {lay['num']}. {lay['title']}", "",
                  "| Project | Stars | Last commit | Checked | License | Evidence | Repro | What it is |",
                  "|---|---|---|---|---|---|---|---|"]
        for p in sorted(rows, key=lambda p: -stars_num(p)):
            link = f"[{esc(p['name'])}]({gh(p)})"
            if p["read"] == "teardown":
                link += f" ([teardown](../teardowns/{p['id']}.md))"
            if p.get("watch"):
                link += " (watchlist: code not released)"
            summ = esc(p["summary"])
            if p.get("caveat"):
                summ += f" **Note:** {esc(p['caveat'])}"
            stars = f"{p['stars']} ({p['stars_asof']})" if p.get("stars") else "–"
            lines.append(f"| {link} | {stars} | {p['last_commit']} | {p.get('checked', SNAPSHOT)} | "
                         f"{esc(p['license'] or 'none found')} | {p['evidence']} | {p['repro']} | {summ} |")
        lines.append("")
    lists = [p for p in projects if p["kind"] == "list"]
    if lists:
        lines += ["## Curated lists (compared in [the list audit](../03-lists-compared.md))", "",
                  "| List | Stars | Last commit | License | Size by our count |", "|---|---|---|---|---|"]
        for p in lists:
            lines.append(f"| [{esc(p['name'])}]({gh(p)}) | {p['stars']} | {p['last_commit']} | "
                         f"{esc(p['license'] or 'none found')} | {esc(p['summary'])} |")
        lines.append("")
    return "\n".join(lines)


def render_ladder_summary(projects: list[dict]) -> str:
    rows = in_layers(projects)
    ev = {k: sum(1 for p in rows if p["evidence"] == k) for k in ("L0", "L1", "L2", "L3", "L4", "bench", "n/a")}
    rp = {k: sum(1 for p in rows if p["repro"] == k) for k in ("full", "partial", "none", "unverified")}
    return (
        f"Of the {len(rows)} repositories in the [catalog](catalog/projects.md): "
        f"{ev['L0']} at L0, {ev['L1']} at L1, {ev['L2']} at L2, {ev['L3']} at L3, {ev['L4']} at L4, "
        f"{ev['bench']} benchmarks or arenas that evaluate other systems, and {ev['n/a']} infrastructure, data or tooling projects with no performance claim. "
        f"On repro, {rp['full']} are graded \"full\", {rp['partial']} \"partial\", {rp['none']} \"none\", "
        f"and {rp['unverified']} \"unverified\" (we read the README and code but did not rerun them)."
    )


def render_layer_counts(c: dict) -> str:
    out = ["| Layer | Repos (primary) | Repos (any layer) | Papers | Articles |", "|---|---|---|---|---|"]
    for lay in c["layers"]:
        nr, np_, na = counts(c, lay["id"])
        anyl = sum(1 for p in listed(c["projects"]) if p["layer"] == lay["id"] or lay["id"] in p["also"])
        out.append(f"| [{lay['num']}. {lay['title']}](../layers/{lay['id']}.md) | {nr} | {anyl} | {np_} | {na} |")
    ns = sum(1 for p in c["papers"] if p["layer"] == "survey")
    out.append(f"| Surveys (span the stack) | | | {ns} | |")
    out.append(f"| **Total** | **{len(listed(c['projects']))}** | | **{len(c['papers'])}** | **{len(c['articles'])}** |")
    return "\n".join(out)


# ---------------------------------------------------------------- injection

INJECTIONS = [
    ("docs/02-evidence-ladder.md", "ladder-summary", lambda c: render_ladder_summary(c["projects"])),
    ("docs/01-domain-map.md", "layer-counts", render_layer_counts),
    ("README.md", "headline", lambda c: headline(c)),
    ("README.zh-CN.md", "headline", lambda c: headline(c, zh=True)),
    ("README.md", "stack", lambda c: render_stack(c)),
    ("README.zh-CN.md", "stack", lambda c: render_stack(c, zh=True)),
    ("README.md", "milestones", lambda c: render_milestones(c)),
    ("README.zh-CN.md", "milestones", lambda c: render_milestones(c, zh=True)),
    ("README.md", "directory", lambda c: render_directory(c)),
    ("README.zh-CN.md", "directory", lambda c: render_directory(c, zh=True)),
    ("README.md", "surveys", lambda c: render_surveys(c)),
    ("README.zh-CN.md", "surveys", lambda c: render_surveys(c, zh=True)),
    ("README.md", "related", lambda c: render_related(c)),
    ("README.zh-CN.md", "related", lambda c: render_related(c, zh=True)),
]


def inject(text: str, name: str, body: str) -> str:
    start, stop = f"<!-- gen:{name} -->", f"<!-- /gen:{name} -->"
    i, j = text.find(start), text.find(stop)
    if i < 0 or j < i:
        raise SystemExit(f"missing marker pair for gen:{name}")
    if "\n" in body or body.startswith(("|", "-", "#")):  # block content needs its own lines
        body = "\n" + body + "\n"
    return text[: i + len(start)] + body + text[j:]


def apply_injections(c: dict, only_check: bool) -> bool:
    ok = True
    for rel, name, fn in INJECTIONS:
        path = ROOT / rel
        if not path.exists():
            continue
        old = path.read_text()
        new = inject(old, name, fn(c))
        if new != old:
            if only_check:
                ok = False
            else:
                path.write_text(new)
    return ok


def generated_pages(c: dict) -> dict[Path, str]:
    pages = {
        OUT / "papers.md": render_papers(c["papers"], c["layers"]),
        OUT / "projects.md": render_projects(c["projects"], c["layers"]),
        LAYER_DIR / "README.md": render_stack_page(c),
    }
    for lay in c["layers"]:
        pages[LAYER_DIR / f"{lay['id']}.md"] = render_layer_page(c, lay)
    return pages


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

    c = load_all()
    errs = check_all(c)
    if errs:
        print("\n".join(f"error: {e}" for e in errs), file=sys.stderr)
        return 1
    if args.cmd == "check":
        print(f"ok: {len(listed(c['projects']))} repos, {len(c['papers'])} papers, "
              f"{len(c['articles'])} articles, {len(c['milestones'])} milestones")
        return 0
    ok = True
    for path, text in generated_pages(c).items():
        ok &= write_or_check(path, text, args.check)
    ok &= apply_injections(c, args.check)
    if args.check and not ok:
        print("error: generated pages are stale; run `python tools/build.py tables`", file=sys.stderr)
        return 1
    print("pages up to date" if args.check else "pages written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
