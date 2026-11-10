#!/usr/bin/env python3
"""Generate assets/*.svg. Counts shown in the figures are read from the catalog, so the pictures cannot drift.

    python tools/make_assets.py          # write the files
    python tools/make_assets.py --check  # fail if they are stale

Standard library only. Every figure carries its own background so it reads the same on light and dark pages.
"""
from __future__ import annotations

import argparse
import sys
from html import escape
from pathlib import Path

try:
    from build import counts, listed, load_all, num
except ImportError:  # imported as tools.make_assets
    from tools.build import counts, listed, load_all, num

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
FONT = "Inter, 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
INK, PAPER, MUTED, LINE = "#0F172A", "#F8FAFC", "#475569", "#CBD5E1"
# one colour per layer, in stack order
COLORS = {"data": "#0E7490", "agent": "#4F46E5", "execution": "#B91C1C", "harness": "#047857", "application": "#B45309"}
TINT = {k: v + "1F" for k, v in COLORS.items()}  # 12% alpha fill


def t(x, y, s, size=13, weight=400, fill=INK, anchor="start", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{escape(s)}</text>'


def svg(w, h, body, title, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-labelledby="t d" font-family="{FONT}">\n<title id="t">{escape(title)}</title>\n<desc id="d">{escape(desc)}</desc>\n'
            f'{body}\n</svg>\n')


def arrow_defs(color=MUTED):
    return (f'<defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M1 1 L9 5 L1 9" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>')


STACK_ZH = {'Five layers of an agentic trading stack': '智能体交易系统的五层结构', 'See, think, act; a harness to run, test and trust all three; applications on top.': '看见、思考、行动；Harness 负责运行、测试并建立信任；应用位于最上层。', 'Application: what you build with it': '应用层：用它做出什么', 'Research desks and reports · AI funds · alpha factories · prediction-market bots': '投研与研报 · AI 基金 · Alpha 工厂 · 预测市场机器人', 'Harness: how you run, test and trust it': 'Harness 层：如何运行、测试并信任它', 'Backtest environments · simulators · benchmarks and live arenas · bias control · agent loops, evals, traces and state': '回测环境 · 模拟器 · 基准与实时竞技场 · 偏差控制 · 智能体循环、评测、追踪与状态', 'Data': '数据层', 'what the agent sees': '智能体看到什么', 'Market, filing and news data': '行情、公告与新闻数据', 'MCP data servers, datasets': 'MCP 数据服务、数据集', 'Text into signals': '把文本变成信号', 'Agent': 'Agent 层', 'how it thinks': '智能体如何思考', 'Finance LLMs and reasoners': '金融基础模型与推理模型', 'Memory, reflection, debate': '记忆、反思、辩论', 'Learned (RL) policies': '学习得到的（RL）策略', 'Execution': '执行层', 'how it acts': '智能体如何下单', 'Broker and venue tools': '券商与交易所工具', 'Engines: backtest = live': '引擎：回测与实盘同一套代码', 'Weights into orders': '把目标权重变成订单', 'fills and P&L are scored against what the agent knew, when': '成交与盈亏，要对照智能体当时知道什么来评分', 'Data, Agent and Execution in a pipeline, wrapped by a Harness that runs, tests and verifies them, with Applications on top.': '数据层、Agent 层、执行层构成主流程，由负责运行、测试与核验的 Harness 层包裹，应用层位于最上方。'}


def stack(c: dict, zh: bool = False) -> str:
    w, h = 960, 530
    tr = (lambda x: STACK_ZH[x]) if zh else (lambda x: x)
    n = {l["id"]: counts(c, l["id"]) for l in c["layers"]}

    def cnt(k):
        r, p = n[k][0], n[k][1]
        return f"{r} 个仓库 · {p} 篇论文" if zh else f"{num(r, 'repo')} · {num(p, 'paper')}"

    b = [f'<rect width="{w}" height="{h}" rx="16" fill="{PAPER}"/>', arrow_defs(),
         t(36, 44, tr("Five layers of an agentic trading stack"), 22, 700),
         t(36, 66, tr("See, think, act; a harness to run, test and trust all three; applications on top."), 13.5, 400, MUTED)]
    # 5 Application
    ax, ay, aw, ah = 36, 88, 888, 78
    b.append(f'<rect x="{ax}" y="{ay}" width="{aw}" height="{ah}" rx="12" fill="{TINT["application"]}" stroke="{COLORS["application"]}" stroke-width="1.5"/>')
    b.append(f'<circle cx="{ax+22}" cy="{ay+24}" r="12" fill="{COLORS["application"]}"/>')
    b.append(t(ax + 22, ay + 29, "5", 13, 700, "#FFFFFF", "middle"))
    b.append(t(ax + 42, ay + 29, tr("Application: what you build with it"), 14.5, 700, INK))
    b.append(t(ax + 14, ay + 54, tr("Research desks and reports · AI funds · alpha factories · prediction-market bots"), 12.5, 400, MUTED))
    b.append(t(ax + aw - 16, ay + 29, cnt("application"), 12.5, 600, COLORS["application"], "end"))
    # 4 Harness frame
    hx, hy, hw, hh = 36, 196, 888, 304
    b.append(f'<path d="M{w//2} {hy-2} L{w//2} {ay+ah+4}" stroke="{MUTED}" stroke-width="1.8" fill="none" marker-end="url(#a)"/>')
    b.append(f'<rect x="{hx}" y="{hy}" width="{hw}" height="{hh}" rx="14" fill="{TINT["harness"]}" stroke="{COLORS["harness"]}" stroke-width="1.5" stroke-dasharray="7 5"/>')
    b.append(f'<circle cx="{hx+22}" cy="{hy+24}" r="12" fill="{COLORS["harness"]}"/>')
    b.append(t(hx + 22, hy + 29, "4", 13, 700, "#FFFFFF", "middle"))
    b.append(t(hx + 42, hy + 29, tr("Harness: how you run, test and trust it"), 14.5, 700, INK))
    b.append(t(hx + hw - 16, hy + 29, cnt("harness"), 12.5, 600, COLORS["harness"], "end"))
    b.append(t(hx + 14, hy + hh - 18, tr("Backtest environments · simulators · benchmarks and live arenas · bias control · agent loops, evals, traces and state"), 12.5, 400, MUTED))
    # 1-3 pipeline
    bw, bh, by = 264, 168, hy + 56
    xs = [60, 348, 636]
    spec = [("data", 1, "Data", tr("what the agent sees"), [tr("Market, filing and news data"), tr("MCP data servers, datasets"), tr("Text into signals")]),
            ("agent", 2, "Agent", tr("how it thinks"), [tr("Finance LLMs and reasoners"), tr("Memory, reflection, debate"), tr("Learned (RL) policies")]),
            ("execution", 3, "Execution", tr("how it acts"), [tr("Broker and venue tools"), tr("Engines: backtest = live"), tr("Weights into orders")])]
    for x, (k, no, title, sub, lines) in zip(xs, spec):
        col = COLORS[k]
        b.append(f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="12" fill="#FFFFFF" stroke="{col}" stroke-width="1.5"/>')
        b.append(f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="12" fill="{TINT[k]}"/>')
        b.append(f'<circle cx="{x+22}" cy="{by+24}" r="12" fill="{col}"/>')
        b.append(t(x + 22, by + 29, str(no), 13, 700, "#FFFFFF", "middle"))
        b.append(t(x + 42, by + 29, tr(title), 15, 700, INK))
        b.append(t(x + 42, by + 47, tr(sub) if sub in STACK_ZH else sub, 12, 400, MUTED))
        for i, ln in enumerate(lines):
            b.append(t(x + 16, by + 78 + i * 20, "· " + (tr(ln) if ln in STACK_ZH else ln), 12.5, 400, INK))
        b.append(t(x + 16, by + bh - 14, cnt(k), 12, 600, col))
    for a_, c_ in zip(xs[:-1], xs[1:]):
        b.append(f'<path d="M{a_+bw+2} {by+bh//2} L{c_-4} {by+bh//2}" stroke="{MUTED}" stroke-width="1.8" fill="none" marker-end="url(#a)"/>')
    fy = by + bh + 26
    b.append(f'<path d="M{xs[2]+bw//2} {by+bh+2} L{xs[2]+bw//2} {fy} L{xs[0]+bw//2} {fy} L{xs[0]+bw//2} {by+bh+6}" stroke="{COLORS["harness"]}" stroke-width="1.6" stroke-dasharray="6 5" fill="none" marker-end="url(#a)"/>')
    b.append(t(w // 2, fy - 6, tr("fills and P&L are scored against what the agent knew, when"), 12, 600, COLORS["harness"], "middle"))
    return svg(w, h, "\n".join(b), tr("Five layers of an agentic trading stack"),
               tr("Data, Agent and Execution in a pipeline, wrapped by a Harness that runs, tests and verifies them, with Applications on top."))


RUNGS = [
    ("L0", "Claim", "Read it."),
    ("L1", "Runnable", "Run it and see decisions."),
    ("L2", "Disclosed backtest", "Read the protocol and table."),
    ("L3", "Replicated or out of sample", "Someone else reran it, or it holds after the cutoff."),
    ("L4", "Forward record", "Timestamped before the outcome."),
]


def ladder(projects: list[dict]) -> str:
    rows = [p for p in projects if p["kind"] != "list"]
    count = {r: sum(1 for p in rows if p["evidence"] == r) for r, *_ in RUNGS}
    other = len(rows) - sum(count.values())
    w, h = 960, 516
    shades = ["#E0E7FF", "#C7D2FE", "#A5B4FC", "#818CF8", "#4F46E5"]
    b = [f'<rect width="{w}" height="{h}" rx="16" fill="{PAPER}"/>',
         t(36, 44, "The evidence ladder", 22, 700),
         t(36, 66, "How far can someone other than the authors inspect the evidence for a project's headline claim?", 13.5, 400, MUTED)]
    base, bw, gap = 396, 164, 16
    for i, (rung, name, what) in enumerate(RUNGS):
        x = 36 + i * (bw + gap)
        hgt = 90 + i * 46
        y = base - hgt
        dark = i >= 3
        txt = "#FFFFFF" if dark else INK
        sub = "#E0E7FF" if dark else MUTED
        b.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{hgt}" rx="10" fill="{shades[i]}"/>')
        b.append(t(x + 14, y + 30, rung, 22, 800, txt))
        b.append(t(x + 14, y + 52, name if len(name) < 20 else "Replicated / OOS", 13.5, 700, txt))
        words, line, lines = what.split(), "", []
        for wd in words:
            if len(line) + len(wd) + 1 > 21:
                lines.append(line)
                line = wd
            else:
                line = (line + " " + wd).strip()
        lines.append(line)
        for j, ln in enumerate(lines[:3]):
            b.append(t(x + 14, y + 72 + j * 15, ln, 11.5, 400, sub))
        b.append(t(x + bw // 2, base + 28, str(count[rung]), 22, 800, INK, "middle"))
        b.append(t(x + bw // 2, base + 46, "catalog projects", 11.5, 400, MUTED, "middle"))
    b.append(f'<path d="M36 {base+4} L{36+5*(bw+gap)-gap} {base+4}" stroke="{LINE}" stroke-width="1.5"/>')
    b.append(t(36, 478, f"Not on the ladder: {other} projects that evaluate other systems (bench) or have no performance claim (n/a).", 12, 400, MUTED))
    b.append(t(36, 496, "The rung says what kind of evidence exists, not how good it is.", 12, 400, MUTED))
    return svg(w, h, "\n".join(b), "The evidence ladder", "Five rungs from an unchecked claim to a forward record, with the number of catalogued projects at each rung.")


def banner(c: dict) -> str:
    w, h = 1280, 300
    rows = listed(c["projects"])
    teardowns = sum(1 for p in c["projects"] if p["read"] == "teardown")
    keys = list(COLORS)
    b = [f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0B1220"/><stop offset="1" stop-color="#16294A"/></linearGradient></defs>',
         f'<rect width="{w}" height="{h}" rx="20" fill="url(#g)"/>',
         t(64, 118, "Awesome Agentic Trading", 58, 800, "#FFFFFF"),
         t(64, 166, "Repositories, papers and writing on LLM agents that research, decide and trade.", 22, 400, "#B6C4D8"),
         t(64, 204, "Data  ·  Agent  ·  Execution  ·  Harness  ·  Application", 17, 600, "#7DD3FC"),
         t(64, 252, f"{num(len(rows), 'repo')}  ·  {num(len(c['papers']), 'paper')}  ·  {num(len(c['articles']), 'article')}  ·  {num(teardowns, 'deep dive')}  ·  every entry dated, checked and given its limit", 15, 400, "#8EA2BD")]
    pts = [(1010 + i * 58, 236 - [0, 22, 14, 52, 92][i]) for i in range(5)]
    b.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in pts) + '" fill="none" stroke="#3B4F72" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    for (x, y), k in zip(pts, keys):
        b.append(f'<circle cx="{x}" cy="{y}" r="12" fill="{COLORS[k]}" stroke="#0B1220" stroke-width="3"/>')
    return svg(w, h, "\n".join(b), "Awesome Agentic Trading", "Repositories, papers and writing on LLM agents that research, decide and trade.")


def render_all() -> dict[str, str]:
    c = load_all()
    return {"banner.svg": banner(c), "stack.svg": stack(c), "stack.zh-CN.svg": stack(c, zh=True), "ladder.svg": ladder(c["projects"])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    files = render_all()
    if a.check:
        stale = [n for n, s in files.items() if not (OUT / n).exists() or (OUT / n).read_text() != s]
        if stale:
            print("error: stale assets: " + ", ".join(stale) + "; run python tools/make_assets.py", file=sys.stderr)
            return 1
        print("assets up to date")
        return 0
    OUT.mkdir(exist_ok=True)
    for n, s in files.items():
        (OUT / n).write_text(s)
    print("assets written: " + ", ".join(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
