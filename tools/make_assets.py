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
    from atlas import load
except ImportError:  # imported as tools.make_assets
    from tools.atlas import load

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
FONT = "Inter, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
INK, PAPER, MUTED, LINE = "#0F172A", "#F8FAFC", "#475569", "#CBD5E1"
# one colour per layer, in map order
COLORS = {
    "data": "#0E7490", "perception": "#0891B2", "decision": "#4F46E5", "alpha": "#7C3AED",
    "portfolio": "#B45309", "execution": "#B91C1C", "evaluation": "#047857", "simulation": "#475569",
}
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


def box(x, y, w, h, key, num, title, lines):
    c = COLORS[key]
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{TINT[key]}" stroke="{c}" stroke-width="1.5"/>',
           f'<circle cx="{x+22}" cy="{y+24}" r="12" fill="{c}"/>',
           t(x + 22, y + 29, str(num), 13, 700, "#FFFFFF", "middle"),
           t(x + 42, y + 29, title, 14.5, 700, INK)]
    for i, ln in enumerate(lines):
        out.append(t(x + 14, y + 52 + i * 17, ln, 12.5, 400, MUTED))
    return "\n".join(out)


def layers() -> str:
    w, h = 960, 540
    b = [f'<rect width="{w}" height="{h}" rx="16" fill="{PAPER}"/>', arrow_defs(),
         t(36, 44, "Eight jobs every LLM trading system does", 22, 700),
         t(36, 66, "Information flows left to right in time; evaluation reads what execution did.", 13.5, 400, MUTED)]
    y, bw, bh, xs = 176, 156, 98, [36, 216, 396, 576, 756]
    b.append(box(xs[0], y, bw, bh, "data", 1, "Data", ["What did it know,", "and when?"]))
    b.append(box(xs[1], y, bw, bh, "perception", 2, "Perception", ["Text and numbers", "into signals?"]))
    b.append(box(xs[2], y, bw, bh, "decision", 3, "Decision", ["Given the signals,", "what is the call?"]))
    b.append(box(xs[3], y, bw, bh, "portfolio", 5, "Portfolio & risk", ["How much, and when", "to stand down?"]))
    b.append(box(xs[4], y, bw, bh, "execution", 6, "Execution", ["How does a decision", "become a safe fill?"]))
    b.append(box(396, 84, bw, 70, "alpha", 4, "Alpha research", ["Find signals, not trades."]))
    ymid = y + bh // 2
    for a, c in zip(xs[:-1], xs[1:]):
        b.append(f'<path d="M{a+bw+2} {ymid} L{c-4} {ymid}" stroke="{MUTED}" stroke-width="1.8" fill="none" marker-end="url(#a)"/>')
    b.append(f'<path d="M{396+bw//2} 156 L{396+bw//2} {y-4}" stroke="{MUTED}" stroke-width="1.8" fill="none" marker-end="url(#a)"/>')
    # evaluation reads execution; simulation feeds evaluation; feedback goes back to decision
    ev_y = 328
    b.append(box(576, ev_y, 336, 82, "evaluation", 7, "Evaluation", ["Is the result real? Baselines, bias control,", "uncertainty, a forward record."]))
    b.append(box(576, 440, 336, 66, "simulation", 8, "Simulation", ["Study behavior without risking capital."]))
    b.append(f'<path d="M{756+bw//2} {y+bh+2} L{756+bw//2} {ev_y-4}" stroke="{MUTED}" stroke-width="1.8" fill="none" marker-end="url(#a)"/>')
    b.append(f'<path d="M744 440 L744 {ev_y+82+4}" stroke="{MUTED}" stroke-width="1.8" fill="none" marker-end="url(#a)" transform="translate(0 0)"/>')
    b.append(f'<path d="M576 {ev_y+41} L474 {ev_y+41} L474 {y+bh+6}" stroke="{COLORS["evaluation"]}" stroke-width="1.8" stroke-dasharray="6 5" fill="none" marker-end="url(#a)"/>')
    b.append(t(462, 296, "feedback: score decisions", 12, 600, COLORS["evaluation"], "end"))
    b.append(t(462, 312, "against what happened", 12, 600, COLORS["evaluation"], "end"))
    b.append(f'<rect x="36" y="328" width="404" height="178" rx="12" fill="none" stroke="{LINE}" stroke-width="1.2" stroke-dasharray="3 4"/>')
    for i, ln in enumerate(["How to read it", "A project gets a layer when it ships working code for that job,",
                            "not when its README mentions it. Read across a row of the", "catalog to see what a project leaves to you; read down a",
                            "column to see how few cover risk and execution."]):
        b.append(t(54, 358 + i * 21, ln, 14 if i == 0 else 12.5, 700 if i == 0 else 400, INK if i == 0 else MUTED))
    return svg(w, h, "\n".join(b), "The eight layers of a trading system", "Data, perception, decision, alpha research, portfolio and risk, execution, evaluation and simulation, with the direction information flows.")


RUNGS = [
    ("L0", "Claim", "Read it."),
    ("L1", "Runnable", "Run it and see decisions."),
    ("L2", "Disclosed backtest", "Read the protocol and table."),
    ("L3", "Independent or out of sample", "Someone else reran it, or it holds after the cutoff."),
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
        b.append(t(x + 14, y + 52, name if len(name) < 20 else "Independent / OOS", 13.5, 700, txt))
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


def banner(papers: list[dict], projects: list[dict]) -> str:
    w, h = 1280, 300
    rows = [p for p in projects if p["kind"] != "list"]
    teardowns = sum(1 for p in rows if p["read"] == "teardown")
    keys = list(COLORS)
    b = [f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0B1220"/><stop offset="1" stop-color="#16294A"/></linearGradient></defs>',
         f'<rect width="{w}" height="{h}" rx="20" fill="url(#g)"/>',
         t(64, 118, "Agentic Trading Atlas", 58, 800, "#FFFFFF"),
         t(64, 166, "A verified, first-principles map of LLM and agentic trading.", 24, 400, "#B6C4D8"),
         t(64, 204, "Domain map  ·  method teardowns  ·  same-budget evaluation", 17, 600, "#7DD3FC"),
         t(64, 252, f"{len(papers)} papers  ·  {len(rows)} projects  ·  {teardowns} teardowns  ·  every link and number checked, dated, and graded", 15, 400, "#8EA2BD")]
    # a rising path through eight layer nodes
    pts = [(760 + i * 70, 215 - [0, 14, 8, 40, 32, 66, 58, 96][i]) for i in range(8)]
    b.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in pts) + '" fill="none" stroke="#3B4F72" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    for (x, y), k in zip(pts, keys):
        b.append(f'<circle cx="{x}" cy="{y}" r="11" fill="{COLORS[k]}" stroke="#0B1220" stroke-width="3"/>')
    return svg(w, h, "\n".join(b), "Agentic Trading Atlas", "A verified, first-principles map of LLM and agentic trading.")


def render_all() -> dict[str, str]:
    papers, projects = load()
    return {"banner.svg": banner(papers, projects), "layers.svg": layers(), "ladder.svg": ladder(projects)}


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
