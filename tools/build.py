#!/usr/bin/env python3
"""Catalog tooling: validate catalog/*.toml and render every generated page from it.

    python tools/build.py check            # schema + cross-reference checks
    python tools/build.py tables           # rewrite the generated pages and blocks
    python tools/build.py tables --check   # fail if anything generated is stale

The READMEs are views of the catalog: the directory, milestones and counts between
`<!-- gen:NAME -->` markers are written here, in English and Chinese from the same entries,
so the two languages cannot drift. Layer pages (layers/*.md), the component matrix
(docs/components.md) and the flat catalog (docs/catalog/*.md) are generated whole.

Every repository entry is pinned to the commit it was checked at (`last_sha`), and every
claim that decides whether to use it (order authority, an unclear or restricted license, a
maintenance declaration) links to the lines at that commit that support it.

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

EVIDENCE = {"L0", "L1", "L2", "L3", "L4", "bench", "n/a"}
REPRO = {"full", "partial", "none", "unverified", "n/a"}
READ_PAPER = {"full", "partial", "abstract", "card"}
READ_PROJECT = {"teardown", "readme", "card"}
ORDERS = {"live", "paper", "none"}
LICENSE_STATUS = {"open", "mixed", "restricted", "declared", "none"}
MAINTENANCE = {"archived", "deprecated", "unmaintained"}
OFF_DIRECTORY = {"archived", "deprecated"}  # shown in the layer page's archive section, not in the directory
SOURCE_WHAT = {"orders", "license", "maintenance", "limit", "data", "runtime", "install", "io", "keys",
               "language", "interface", "integrations", "notes"}
PROJECT_KINDS = {
    "framework", "platform", "infrastructure", "library", "model", "benchmark", "simulator",
    "backtester", "data", "execution", "experiment", "list", "tool",
}
LIST_CATEGORIES = {"related", "style-reference"}  # kind = "list" entries live outside the five layers
ARTICLE_SOURCES = {"x", "blog", "docs", "news", "newsletter", "podcast", "talk", "paper", "tool-page"}
INTERFACES = {"python-lib", "cli", "mcp", "rest-api", "web-ui", "docker-service", "desktop", "typescript-lib", "hosted"}
VERIFICATION = {"docs", "install", "run"}
RECIPE_STATUS = {"design", "upstream", "run"}
ARXIV = re.compile(r"^\d{4}\.\d{4,5}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_OR_MONTH = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
SHA = re.compile(r"^[0-9a-f]{40}$")
BRIEF_FIELDS = ("tagline", "audience", "limit", "tagline_zh", "audience_zh", "limit_zh")

ACTIVITY = {"active": "🟢", "slowing": "🟡", "dormant": "⚪"}
MAINT_ICON = {"archived": "🗄️", "deprecated": "⛔", "unmaintained": "💤"}
MAINT_ZH = {"archived": "已归档", "deprecated": "已弃用", "unmaintained": "作者声明不再维护"}
LICENSE_MARK = {"open": "", "mixed": "🧩 ", "restricted": "🔒 ", "declared": "❓ ", "none": "❓ "}
SOURCE_ICON = {"x": "𝕏", "blog": "📝", "docs": "📘", "news": "📰", "newsletter": "📰", "podcast": "🎧",
               "talk": "🎤", "paper": "📄", "tool-page": "🔧"}
READ_ICON = {"full": "📖", "partial": "📖", "card": "🗂️", "abstract": "🔖"}
READ_LABEL = {"full": "read in full", "partial": "read in part", "card": "method card", "abstract": "abstract only"}
READ_LABEL_ZH = {"full": "全文精读", "partial": "部分精读", "card": "方法卡片", "abstract": "仅读摘要"}
VERIFY_LABEL = {"docs": "📄 docs at the pinned commit", "install": "📦 installed", "run": "▶️ example run"}
RECIPE_LABEL = {"design": "🧭 design reference (not run)", "upstream": "🔗 pairing documented upstream (not run by us)",
                "run": "✅ run end to end by us"}


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
        p.setdefault("sources", [])
        if p["id"] in briefs:
            p["brief"] = briefs[p["id"]]
    return papers, projects


def load_all() -> dict:
    papers, projects = load()
    comp = _toml("components.toml")
    return {
        "layers": load_layers(),
        "papers": papers,
        "projects": projects,
        "articles": _toml("articles.toml").get("article", []),
        "milestones": _toml("milestones.toml").get("milestone", []),
        "components": comp.get("component", []),
        "recipes": comp.get("recipe", []),
    }


# ---------------------------------------------------------------- checks

def pinned(p: dict, url: str) -> bool:
    """A source must point at the checked commit of the project's own repository."""
    return url.startswith(f"https://github.com/{p['repo']}/blob/{p['last_sha']}/")


def check_all(c: dict) -> list[str]:
    errs = check(c["papers"], c["projects"], c["layers"])
    layer_ids = {l["id"] for l in c["layers"]}
    seen: set[str] = set()
    for a in c["articles"]:
        u = a.get("url", "?")
        if u in seen:
            errs.append(f"article {u}: duplicate")
        seen.add(u)
        for k in ("title", "author", "url", "source", "layer", "why", "checked"):
            if not a.get(k):
                errs.append(f"article {u}: missing {k}")
        if a.get("source") not in ARTICLE_SOURCES:
            errs.append(f"article {u}: unknown source {a.get('source')!r}")
        if a.get("layer") not in layer_ids | {"survey"}:
            errs.append(f"article {u}: unknown layer {a.get('layer')!r}")
        if a.get("date") and not DATE_OR_MONTH.match(a["date"]):
            errs.append(f"article {u}: bad date {a['date']!r}")
        if a.get("checked") and not DATE.match(a["checked"]):
            errs.append(f"article {u}: bad checked date")
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
    errs += check_components(c)
    return errs


def check_components(c: dict) -> list[str]:
    errs: list[str] = []
    by_id = {p["id"]: p for p in c["projects"]}
    seen: set[str] = set()
    for m in c["components"]:
        i = m.get("id", "?")
        p = by_id.get(i)
        if not p:
            errs.append(f"component {i}: not a catalogued project")
            continue
        if i in seen:
            errs.append(f"component {i}: duplicate")
        seen.add(i)
        for k in ("language", "runtime", "install", "interface", "inputs", "outputs", "keys_cost", "verification"):
            if not m.get(k):
                errs.append(f"component {i}: missing {k}")
        for f in m.get("interface", []):
            if f not in INTERFACES:
                errs.append(f"component {i}: unknown interface {f!r}")
        if m.get("verification") not in VERIFICATION:
            errs.append(f"component {i}: unknown verification {m.get('verification')!r}")
        if m.get("verification") in ("install", "run") and not (m.get("verify_cmd") and m.get("verify_date")):
            errs.append(f"component {i}: install/run verification needs verify_cmd and verify_date")
        for s in m.get("sources", []):
            # its own repository, or another catalogued one (e.g. a dependency's license), at the checked commit
            if s.get("what") not in SOURCE_WHAT or not any(pinned(q, s.get("url", "")) for q in c["projects"]):
                errs.append(f"component {i}: source {s.get('url')!r} must be pinned to a catalogued project's last_sha")
        if m.get("orders") is not None and m["orders"] != p.get("orders"):
            errs.append(f"component {i}: orders {m['orders']!r} disagrees with the catalog's {p.get('orders')!r}")
        for g in m.get("integrations", []):
            other = by_id.get(g.get("with"))
            if not other:
                errs.append(f"component {i}: integration with unknown project {g.get('with')!r}")
            elif g.get("url") and not (pinned(p, g["url"]) or pinned(other, g["url"])):
                errs.append(f"component {i}: integration link {g['url']!r} must be pinned to either project's last_sha")
    for r in c["recipes"]:
        i = r.get("id", "?")
        for k in ("title", "status", "steps", "why", "gaps"):
            if not r.get(k):
                errs.append(f"recipe {i}: missing {k}")
        if r.get("status") not in RECIPE_STATUS:
            errs.append(f"recipe {i}: unknown status {r.get('status')!r}")
        if r.get("status") == "upstream" and not r.get("links"):
            errs.append(f"recipe {i}: an upstream-documented pairing needs links to that documentation")
        for st in r.get("steps", []):
            p = by_id.get(st.get("component"))
            if not p:
                errs.append(f"recipe {i}: step uses unknown project {st.get('component')!r}")
            elif st.get("layer") not in [p.get("layer"), *p.get("also", [])]:
                errs.append(f"recipe {i}: {p['id']} does not work in the {st.get('layer')!r} layer")
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
        for k in ("name", "repo", "kind", "license", "license_file", "last_commit", "last_sha", "checked",
                  "evidence", "repro", "read", "summary"):
            if k not in p:
                errs.append(f"project {i}: missing {k}")
        if "/" not in p.get("repo", ""):
            errs.append(f"project {i}: repo must be owner/name")
        if not SHA.match(p.get("last_sha", "")):
            errs.append(f"project {i}: last_sha must be the full 40-character commit hash")
        if p.get("evidence") not in EVIDENCE:
            errs.append(f"project {i}: unknown evidence {p.get('evidence')!r}")
        if p.get("repro") not in REPRO:
            errs.append(f"project {i}: unknown repro {p.get('repro')!r}")
        if p.get("read") not in READ_PROJECT:
            errs.append(f"project {i}: unknown read level {p.get('read')!r}")
        if p.get("kind") not in PROJECT_KINDS:
            errs.append(f"project {i}: unknown kind {p.get('kind')!r}")
        whats = {s.get("what") for s in p.get("sources", [])}
        for s in p.get("sources", []):
            if s.get("what") not in SOURCE_WHAT:
                errs.append(f"project {i}: unknown source kind {s.get('what')!r}")
            if not pinned(p, s.get("url", "")):
                errs.append(f"project {i}: source {s.get('url')!r} is not pinned to last_sha")
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
            if p.get("orders") not in ORDERS:
                errs.append(f"project {i}: orders must be one of live, paper, none (got {p.get('orders')!r})")
            elif p["orders"] in ("live", "paper") and "orders" not in whats:
                errs.append(f"project {i}: orders = {p['orders']} needs a pinned 'orders' source")
            st = p.get("license_status")
            if st not in LICENSE_STATUS:
                errs.append(f"project {i}: unknown license_status {st!r}")
            elif st == "open" and not p.get("license_file"):
                errs.append(f"project {i}: an open license needs the license_file it was read from")
            elif st == "declared" and "license" not in whats:
                errs.append(f"project {i}: a declared-only license needs a pinned 'license' source")
            elif st in ("mixed", "restricted") and "license" not in whats and not p.get("license_file"):
                errs.append(f"project {i}: a {st} license needs its license file or a pinned 'license' source")
            elif st == "none" and p.get("license_file"):
                errs.append(f"project {i}: license_status = none but a license_file is recorded")
            mt = p.get("maintenance")
            if mt is not None and mt not in MAINTENANCE:
                errs.append(f"project {i}: unknown maintenance {mt!r}")
            if mt in ("deprecated", "unmaintained") and "maintenance" not in whats:
                errs.append(f"project {i}: maintenance = {mt} needs a pinned 'maintenance' source")
            if mt in OFF_DIRECTORY and not p.get("caveat"):
                errs.append(f"project {i}: {mt} entries need a caveat saying since when and what replaces them")
            if mt and p.get("watch"):
                errs.append(f"project {i}: an entry is either on the watchlist or has a maintenance state, not both")
        if p.get("paper") and p["paper"] not in seen:
            errs.append(f"project {i}: paper {p['paper']} not in papers.toml")
        for k in ("last_commit", "stars_asof", "checked"):
            if p.get(k) and not DATE.match(p[k]):
                errs.append(f"project {i}: bad date in {k}")
        if p.get("last_commit") and p.get("checked") and DATE.match(p["last_commit"]) and DATE.match(p["checked"]) \
                and p["last_commit"] > p["checked"]:
            errs.append(f"project {i}: last_commit is after the check date")
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
    """Commit activity as of the check date. It goes stale with the check, which is why the date is shown."""
    days = (date.fromisoformat(p["checked"]) - date.fromisoformat(p["last_commit"])).days
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
    """Projects shown in the directories: in a layer, with released code, not archived or deprecated."""
    return [p for p in in_layers(projects) if not p.get("watch") and p.get("maintenance") not in OFF_DIRECTORY]


def gh(p: dict) -> str:
    return f"https://github.com/{p['repo']}"


def tree_url(p: dict) -> str:
    return f"https://github.com/{p['repo']}/tree/{p['last_sha']}"


def source(p: dict, what: str) -> str | None:
    return next((s["url"] for s in p.get("sources", []) if s["what"] == what), None)


def license_url(p: dict) -> str:
    if p.get("license_file"):
        return f"https://github.com/{p['repo']}/blob/{p['last_sha']}/{p['license_file']}"
    return source(p, "license") or tree_url(p)


def license_badge(p: dict, zh: bool) -> str:
    st = p["license_status"]
    if st == "none":
        return f"❓ [{'无许可证' if zh else 'no license'}]({tree_url(p)})"
    if st == "declared":
        note = "仅声明，无许可证文件" if zh else "declared, no license file"
        return f"❓ [`{p['license']}` {note}]({license_url(p)})"
    return f"{LICENSE_MARK[st]}[`{p['license']}`]({license_url(p)})"


def orders_badge(p: dict) -> str:
    if p["orders"] == "live":
        return f"[⚡]({source(p, 'orders')})"
    if p["orders"] == "paper":
        return f"[📝]({source(p, 'orders')})"
    return ""


def status_badge(p: dict) -> str:
    mt = p.get("maintenance")
    if mt:
        url = source(p, "maintenance")
        return f"[{MAINT_ICON[mt]}]({url})" if url else MAINT_ICON[mt]
    return ACTIVITY[activity(p)]


def slug(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation dropped, spaces to hyphens."""
    h = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return h.replace(" ", "-")


def authors(p: dict) -> str:
    return p["first_author"] + (" et al." if p.get("n_authors", 1) > 1 else "")


def counts(c: dict, layer: str) -> tuple[int, int, int]:
    return (sum(1 for p in listed(c["projects"]) if p["layer"] == layer),
            sum(1 for p in c["papers"] if p["layer"] == layer),
            sum(1 for a in c["articles"] if a["layer"] == layer))


def license_groups(projects: list[dict]) -> tuple[int, int, int]:
    rows = listed(projects)
    return (sum(1 for p in rows if p["license_status"] == "open"),
            sum(1 for p in rows if p["license_status"] in ("mixed", "restricted")),
            sum(1 for p in rows if p["license_status"] in ("declared", "none")))


def article_date(a: dict, zh: bool = False, month: bool = False) -> str:
    if not a.get("date"):
        return f"未注明日期（{a['checked']} 核验）" if zh else f"undated (checked {a['checked']})"
    return a["date"][:7] if month else a["date"]


# ---------------------------------------------------------------- README blocks

def readme_entry(p: dict, zh: bool) -> str:
    b = p["brief"]
    tag = end_zh(b["tagline_zh"]) if zh else end(b["tagline"])
    lim = end_zh(b["limit_zh"]) if zh else end(b["limit"])
    parts = [status_badge(p), license_badge(p, zh), orders_badge(p), "🧰" if p.get("general") else ""]
    if p["read"] == "teardown":
        parts.append(f"[🔬 {'拆解' if zh else 'deep dive'}](docs/teardowns/{p['id']}.md)")
    parts.append(f"[🔍 {p['checked']}]({tree_url(p)})")
    return f"- [{p['name']}]({gh(p)}) — {tag} ⚠️ {lim} " + " ".join(x for x in parts if x)


def readme_paper(p: dict, zh: bool) -> str:
    year = p["published"][:4]
    s = p["summary_zh"] if zh else p["summary"]
    read = f"{READ_ICON[p['read']]} {(READ_LABEL_ZH if zh else READ_LABEL)[p['read']]}"
    return f"- [{p['title']}](https://arxiv.org/abs/{p['arxiv']}) — {authors(p)}, {year} · {read}. {s}"


def readme_article(a: dict, zh: bool) -> str:
    icon = SOURCE_ICON[a["source"]]
    why = a["why_zh"] if zh else a["why"]
    return f"- {icon} [{a['title']}]({a['url']}) — {a['author']}, {article_date(a, zh, month=True)}. {why}"


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
        feat = sorted((a for a in c["articles"] if a["layer"] == lid and a.get("featured")),
                      key=lambda a: a.get("date") or a["checked"])
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
        read = f"{READ_ICON[p['read']]} {(READ_LABEL_ZH if zh else READ_LABEL)[p['read']]}"
        out.append(f"- [{p['title']}](https://arxiv.org/abs/{p['arxiv']}) — {authors(p)}, {p['published'][:4]} · {read}. {s}")
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
    op, rs, un = license_groups(c["projects"])
    np_ = len(c["papers"])
    na = len(c["articles"])
    nt = sum(1 for p in c["projects"] if p["read"] == "teardown")
    if zh:
        return (f"{nr} 个仓库（{op} 个开源 · {rs} 个混合或受限许可 · {un} 个许可待确认）· "
                f"{np_} 篇论文 · {na} 篇文章与帖子 · {nt} 个深度拆解")
    return (f"{nr} repositories ({op} open source · {rs} mixed or restricted license · {un} license unclear) · "
            f"{np_} papers · {na} articles and posts · {nt} deep dives")


# ---------------------------------------------------------------- layer pages

LEGEND = ("Legend: 🟢 active · 🟡 slowing · ⚪ dormant (last commit within 90 days, within a year, or older, counted from "
          "the check date) · 💤 declared unmaintained · ⚡ can place real orders · 📝 paper trading only · "
          "🧩 open core with proprietary parts · 🔒 source-available, restricted · ❓ license unclear · "
          "🧰 general-purpose tool applied here · 📖 read in full · 🗂️ machine-extracted "
          "[method card](../docs/cards/index.md) · 🔖 abstract only. Marks on a row link to the lines that support them, "
          "at the commit we checked.")


def activity_cell(p: dict) -> str:
    mt = p.get("maintenance")
    a = f"{ACTIVITY[activity(p)]} {activity(p)}, last commit {p['last_commit']}"
    if mt:
        url = source(p, "maintenance")
        label = f"{MAINT_ICON[mt]} {mt}" + (f" ([source]({url}))" if url else "")
        return f"{label}; {a}"
    return a


def orders_cell(p: dict) -> str:
    if p["orders"] == "none":
        return "none"
    links = [s["url"] for s in p["sources"] if s["what"] == "orders"]
    refs = " ".join(f"[{n}]({u})" for n, u in enumerate(links, 1))
    return f"{'⚡ live' if p['orders'] == 'live' else '📝 paper'} {refs}"


def license_cell(p: dict) -> str:
    word = {"open": "", "mixed": " (mixed)", "restricted": " (restricted)", "declared": "", "none": ""}[p["license_status"]]
    return esc(license_badge(p, zh=False)) + word


def render_layer_page(c: dict, lay: dict) -> str:
    lid = lay["id"]
    nr, np_, na = counts(c, lid)
    rows_all = [p for p in in_layers(c["projects"]) if p["layer"] == lid]
    cross = [p for p in listed(c["projects"]) if lid in p.get("also", [])]
    papers = [p for p in c["papers"] if p["layer"] == lid]
    arts = sorted((a for a in c["articles"] if a["layer"] == lid), key=lambda a: a.get("date") or a["checked"], reverse=True)
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
        f"{nr} repos · {np_} papers · {na} articles and posts. " + LEGEND,
        "",
        "## Contents",
        "",
        "- [Repositories](#repositories)",
    ]
    if cross:
        L.append("- [Also relevant from other layers](#also-relevant-from-other-layers)")
    if any(p.get("watch") for p in rows_all):
        L.append("- [Watchlist: announced, code not released](#watchlist-announced-code-not-released)")
    if any(p.get("maintenance") in OFF_DIRECTORY for p in rows_all):
        L.append("- [Archived and deprecated](#archived-and-deprecated)")
    L += ["- [Papers](#papers)", "- [Articles and posts](#articles-and-posts)", "- [Builder notes](#builder-notes)", "",
          "## Repositories", ""]
    for cat in lay["category"]:
        rows = [p for p in listed(rows_all) if p["category"] == cat["id"]]
        if not rows:
            continue
        rows.sort(key=lambda p: (-stars_num(p), p["name"].lower()))
        L += [f"### {cat['title']}", "",
              "| Project | What it does | Suits | Activity | License | Orders | Checked | Key limit |",
              "|---|---|---|---|---|---|---|---|"]
        for p in rows:
            b = p["brief"]
            name = f"[{esc(p['name'])}]({gh(p)})"
            if p.get("general"):
                name += " 🧰"
            if p["read"] == "teardown":
                name += f" · [🔬 deep dive](../docs/teardowns/{p['id']}.md)"
            checked = f"[{p['checked']} @ `{p['last_sha'][:7]}`]({tree_url(p)})"
            L.append(f"| {name} | {esc(b['tagline'])} | {esc(b['audience'])} | {activity_cell(p)} | {license_cell(p)} | "
                     f"{orders_cell(p)} | {checked} | {esc(b['limit'])} |")
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
            L.append(f"- [{p['name']}]({gh(p)}) — {end(p['brief']['tagline'])} ⚠️ {end(p['brief']['limit'])} "
                     f"[🔍 {p['checked']}]({tree_url(p)})")
        L.append("")
    archived = [p for p in rows_all if p.get("maintenance") in OFF_DIRECTORY]
    if archived:
        L += ["## Archived and deprecated", "",
              "Kept for reference because they are cited or show a useful design; their authors no longer maintain them.", ""]
        for p in archived:
            L.append(f"- {MAINT_ICON[p['maintenance']]} [{p['name']}]({gh(p)}) — {end(p['brief']['tagline'])} "
                     f"⚠️ {end(p['caveat'])} {orders_badge(p)} [🔍 {p['checked']}]({tree_url(p)})".rstrip())
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
        L += ["Newest first. Icons: 𝕏 post · 📝 blog · 📘 docs · 📰 news · 🎧 podcast · 🎤 talk · 📄 paper or report. "
              "A post is listed for the idea it carries; its own performance claims are not verified here. "
              "Undated pages show the date we checked them.", ""]
        for a in arts:
            note = f" ({a['date_note']})" if a.get("date_note") else ""
            L.append(f"- {SOURCE_ICON[a['source']]} [{a['title']}]({a['url']}) — {a['author']}, {article_date(a)}{note}. {a['why']}")
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
        "[← Home](../README.md) · [Component matrix](../docs/components.md)",
        "",
        "Every agentic trading system, however it is marketed, is some arrangement of five layers. "
        "A map by layer shows which jobs a project does, which it leaves to you, and which nobody does well yet. "
        "Each layer page lists the repositories (with their license status), papers, articles and posts for that layer, "
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


# ---------------------------------------------------------------- component matrix

def render_components(c: dict) -> str:
    by_id = {p["id"]: p for p in c["projects"]}
    order = {l["id"]: l["num"] for l in c["layers"]}
    comps = sorted(c["components"], key=lambda m: (order[by_id[m["id"]]["layer"]], m["id"]))
    L = [
        "<!-- generated by tools/build.py from catalog/components.toml; do not edit by hand -->",
        "# Component matrix",
        "",
        "[← Home](../README.md) · [The stack](../layers/README.md)",
        "",
        f"The {len(comps)} components builders reach for most, side by side, so an agent (or a person) can pick parts "
        "that fit together. Every cell comes from the project's own README and manifests at the commit we checked; "
        "the **Verified** column says how far we went. Nothing here was installed or run by us unless that column says "
        "so, and a green CI on this list says nothing about whether two projects work together.",
        "",
        "**Verified:** 📄 docs at the pinned commit · 📦 installed and imported · ▶️ a documented example run.",
        "",
        "## At a glance",
        "",
        "| Component | Layer | Language | Interface | Orders | License | Keys and cost | Verified |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m in comps:
        p = by_id[m["id"]]
        lay = next(l for l in c["layers"] if l["id"] == p["layer"])
        L.append(f"| [{esc(p['name'])}](#{slug(p['name'])}) | [{lay['title'].split()[0]}](../layers/{lay['id']}.md) | "
                 f"{esc(m['language'])} | {', '.join(m['interface'])} | {orders_cell(p)} | "
                 f"{license_cell(p)} | {esc(m['keys_cost'])} | {VERIFY_LABEL[m['verification']].split()[0]} |")
    L += ["", "## Details", ""]
    for m in comps:
        p = by_id[m["id"]]
        L += [f"### {p['name']}", "",
              f"[Repository]({gh(p)}) · [checked {p['checked']} at `{p['last_sha'][:7]}`]({tree_url(p)})", "",
              "| | |", "|---|---|",
              f"| Runtime | {esc(m['runtime'])} |",
              f"| Install | {esc(m['install'])} |",
              f"| Interface | {', '.join(m['interface'])} |",
              f"| In → out | {esc(m['inputs'])} → {esc(m['outputs'])} |",
              f"| Keys and cost | {esc(m['keys_cost'])} |",
              f"| Orders | {orders_cell(p)} |",
              f"| License | {license_cell(p)} |"]
        if m.get("integrations"):
            ints = "; ".join(f"[{by_id[g['with']]['name']}]({g['url']}): {esc(g['note'])}" if g.get("url")
                             else f"{by_id[g['with']]['name']}: {esc(g['note'])}" for g in m["integrations"])
            L.append(f"| Documented integrations | {ints} |")
        ver = VERIFY_LABEL[m["verification"]]
        if m["verification"] != "docs":
            ver += f": `{esc(m['verify_cmd'])}` on {m.get('verify_env', '')} ({m['verify_date']}): {esc(m.get('verify_result', ''))}"
        L.append(f"| Verified | {ver} |")
        if m.get("sources"):
            groups: dict[str, list[str]] = {}
            for s_ in m["sources"]:
                groups.setdefault(s_["what"], []).append(s_["url"])
            cell = " · ".join(f"{w} " + " ".join(f"[{n}]({u})" for n, u in enumerate(us, 1)) for w, us in groups.items())
            L.append(f"| Sources | {cell} |")
        if m.get("notes"):
            L.append(f"| Notes | {esc(m['notes'])} |")
        L.append("")
    if c["recipes"]:
        L += ["## Cross-layer recipes", "",
              "Ways to combine components across layers. The status says what kind of claim each is: "
              + " · ".join(RECIPE_LABEL[k] for k in ("design", "upstream", "run")) + ". "
              "A design reference is a starting point for your own integration test, not evidence that the parts work together.", ""]
        for r in c["recipes"]:
            L += [f"### {r['title']}", "", f"**Status:** {RECIPE_LABEL[r['status']]}", "", r["why"], ""]
            for n, st in enumerate(r["steps"], 1):
                p = by_id[st["component"]]
                lay = next(l for l in c["layers"] if l["id"] == st["layer"])
                L.append(f"{n}. **{lay['title']}** — [{p['name']}]({gh(p)}): {st['role']}")
            L += ["", f"**What you still have to build or check:** {r['gaps']}", ""]
            if r.get("links"):
                L += ["**Upstream documentation:** " + " · ".join(f"[{x['label']}]({x['url']})" for x in r["links"]), ""]
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
        "Each was checked at the commit linked under **Checked** (default-branch HEAD on that date): license file read "
        "as text, README and code read for order authority. Stars are as displayed on GitHub on the date given and are "
        "context, not a quality score. **Evidence** is the highest rung of the "
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
                  "| Project | Stars | Last commit | Checked | License | Orders | Evidence | Repro | What it is |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for p in sorted(rows, key=lambda p: -stars_num(p)):
            link = f"[{esc(p['name'])}]({gh(p)})"
            if p["read"] == "teardown":
                link += f" ([teardown](../teardowns/{p['id']}.md))"
            if p.get("watch"):
                link += " (watchlist: code not released)"
            if p.get("maintenance"):
                link += f" ({p['maintenance']})"
            summ = esc(p["summary"])
            if p.get("caveat"):
                summ += f" **Note:** {esc(p['caveat'])}"
            stars = f"{p['stars']} ({p['stars_asof']})" if p.get("stars") else "–"
            checked = f"[{p['checked']}]({tree_url(p)})"
            lines.append(f"| {link} | {stars} | {p['last_commit']} | {checked} | {license_cell(p)} | {orders_cell(p)} | "
                         f"{p['evidence']} | {p['repro']} | {summ} |")
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
    if c["components"]:
        pages[ROOT / "docs" / "components.md"] = render_components(c)
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
        print(f"ok: {len(listed(c['projects']))} repos, {len(c['papers'])} papers, {len(c['articles'])} articles, "
              f"{len(c['milestones'])} milestones, {len(c['components'])} components")
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
