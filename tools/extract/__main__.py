"""Method-card extraction. Run from the repository root.

    python -m tools.extract plan   [--ids ID ...] [--exact]     # fetch sources, estimate the bill; spends nothing
    python -m tools.extract run    --max-usd N --yes [--ids ...] [--workers 3] [--redo]
    python -m tools.extract verify                              # re-check every stored quote against its source
    python -m tools.extract render [--check]                    # write docs/cards/*.md from cards/*.json
    python -m tools.extract promote                             # catalog: read=abstract -> card for passing cards

A card is a fixed set of fields about one paper. Each field carries a gloss written by the model and a quote
copied from the paper; `run` rejects any quote that is not a verbatim passage of the source text.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import client as cl
from . import sources
from .schema import FIELDS, verify_card

ROOT = Path(__file__).resolve().parent.parent.parent
CARDS = ROOT / "cards"
DOCS = ROOT / "docs" / "cards"
DATA = ROOT / "data" / "extract"
MIN_VERIFIED = 5  # a card needs at least this many verified fields to count as a read
OUT_TOKENS = (3_000, 9_000)  # assumed output tokens per paper, thinking included: an assumption, not a measurement
sys.path.insert(0, str(ROOT / "tools"))
from atlas import load  # noqa: E402


def select(ids: list[str] | None, redo: bool) -> list[dict]:
    papers, _ = load()
    if ids:
        by = {p["arxiv"]: p for p in papers}
        missing = [i for i in ids if i not in by]
        if missing:
            raise SystemExit(f"not in the catalog: {', '.join(missing)}")
        chosen = [by[i] for i in ids]
    else:
        chosen = [p for p in papers if p["read"] == "abstract" or (CARDS / f"{p['arxiv']}.json").exists()]
    if not redo:
        chosen = [p for p in chosen if not (CARDS / f"{p['arxiv']}.json").exists()]
    return chosen


def est_tokens(chars: int) -> int:
    return int(chars / 3.5) + 900  # ~3.5 characters per token for English prose and tables, plus prompt


def cmd_plan(a) -> int:
    todo = select(a.ids, a.redo)
    if not todo:
        print("nothing to do: every selected paper already has a card")
        return 0
    api = cl.make_client() if a.exact else None
    rows, tot_in = [], 0
    for p in todo:
        try:
            src = sources.fetch(p["arxiv"])
        except RuntimeError as e:
            print(f"SKIP {e}")
            continue
        n = cl.count_input_tokens(api, p["title"], src["text"]) if api else est_tokens(src["chars"])
        tot_in += n
        rows.append((p["arxiv"], src["kind"], src["chars"], n, src["truncated"]))
    for r in rows:
        print(f"{r[0]:<11} {r[1]:<6} {r[2]:>8} chars  ~{r[3]:>7,} in-tokens{'  TRUNCATED' if r[4] else ''}")
    lo = cl.cost(tot_in, OUT_TOKENS[0] * len(rows))
    hi = cl.cost(tot_in, OUT_TOKENS[1] * len(rows))
    print(f"\n{len(rows)} papers, {tot_in:,} input tokens ({'exact count_tokens' if api else 'estimate at 3.5 chars/token'})")
    print(f"model {cl.MODEL}, effort {cl.EFFORT}, ${cl.PRICE_IN*1e6:.0f}/${cl.PRICE_OUT*1e6:.0f} per million tokens in/out")
    print(f"input cost ${cl.cost(tot_in, 0):.2f}; output assumed {OUT_TOKENS[0]:,}-{OUT_TOKENS[1]:,} tokens per paper (thinking included)")
    print(f"estimated total ${lo:.2f} - ${hi:.2f}")
    return 0


def card_path(i: str) -> Path:
    return CARDS / f"{i}.json"


def build_card(p: dict, src: dict, fields: dict, usage: dict) -> dict:
    return {
        "arxiv": p["arxiv"], "title": p["title"], "published": p["published"], "updated": p["updated"],
        "source": {k: src[k] for k in ("kind", "url", "chars", "truncated", "sha256", "fetched")},
        "extraction": {
            "model": cl.MODEL, "effort": cl.EFFORT, "date": time.strftime("%Y-%m-%d", time.gmtime()),
            **usage, "cost_usd": round(cl.cost(usage["input_tokens"], usage["output_tokens"]), 4),
        },
        "fields": fields,
        "verification": verify_card(fields, src["text"]),
    }


def cmd_run(a) -> int:
    todo = select(a.ids, a.redo)
    if not todo:
        print("nothing to do: every selected paper already has a card")
        return 0
    if not a.yes:
        print(f"{len(todo)} papers would be sent to {cl.MODEL}. Run `plan` for the estimate, then add --yes to proceed.")
        return 2
    api = cl.make_client()
    ledger = cl.Ledger(max_usd=a.max_usd)
    CARDS.mkdir(exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    def work(p):
        src = sources.fetch(p["arxiv"])
        fields, usage = cl.extract_one(api, p["title"], src["text"], ledger)
        card = build_card(p, src, fields, usage)
        card_path(p["arxiv"]).write_text(json.dumps(card, indent=1, ensure_ascii=False) + "\n")
        with open(DATA / "ledger.jsonl", "a") as f:
            f.write(json.dumps({"arxiv": p["arxiv"], **usage, "cost_usd": card["extraction"]["cost_usd"]}) + "\n")
        return p["arxiv"], card

    bad = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(work, p): p for p in todo}
        for fu in as_completed(futs):
            p = futs[fu]
            try:
                i, card = fu.result()
                v = card["verification"]
                print(f"ok   {i}  verified {v['verified']}  failed {v['failed']}  not_found {v['not_found']}  ${card['extraction']['cost_usd']:.3f}")
            except cl.BudgetExceeded as e:
                print(f"STOP {p['arxiv']}: {e}")
                bad += 1
            except Exception as e:  # one paper failing must not lose the others
                print(f"FAIL {p['arxiv']}: {type(e).__name__}: {str(e)[:200]}")
                bad += 1
    print(f"\n{ledger.calls} calls, {ledger.input_tokens:,} in / {ledger.output_tokens:,} out tokens, ${ledger.spent:.2f} spent, {bad} problems")
    return 1 if bad else 0


def cmd_verify(a) -> int:
    bad = 0
    for f in sorted(CARDS.glob("*.json")):
        card = json.loads(f.read_text())
        src = sources.fetch(card["arxiv"])
        if src["sha256"] != card["source"]["sha256"]:
            print(f"NOTE {card['arxiv']}: source text changed since extraction ({card['source']['fetched']}); quotes re-checked against the new text")
        v = verify_card(card["fields"], src["text"])
        if v["failed"] or v["verified"] < MIN_VERIFIED:
            print(f"FAIL {card['arxiv']}: verified {v['verified']}, failed {v['failed']}")
            bad += 1
    print(f"cards: {len(list(CARDS.glob('*.json')))} checked, {bad} failing")
    return 1 if bad else 0


def cell(s: str) -> str:
    return re.sub(r"\s+", " ", s).replace("|", "\\|").strip()


def render_card(card: dict) -> str:
    e, s, v = card["extraction"], card["source"], card["verification"]
    lines = [
        "<!-- generated by tools/extract from cards/%s.json; do not edit by hand -->" % card["arxiv"],
        f"# {card['title']}",
        "",
        f"arXiv [{card['arxiv']}](https://arxiv.org/abs/{card['arxiv']}) · v1 {card['published']} · latest {card['updated']}",
        "",
        f"> **Machine-extracted method card.** The gloss column was written by `{e['model']}` (effort {e['effort']}) on {e['date']} from the "
        f"{s['kind']} text of the paper. Every quote was checked by a program to be a passage of that text; the gloss has not been checked by a person. "
        "\"Not found\" means the model did not find the item in the text it was given, not that the paper omits it.",
        "",
        "| Field | Gloss | Quote from the paper |",
        "|---|---|---|",
    ]
    for name, desc in FIELDS.items():
        f, d = card["fields"][name], v["detail"][name]
        if d in ("exact", "loose"):
            lines.append(f"| **{name}** | {cell(f['value'])} | “{cell(f['quote'])}” |")
        elif d == "not_found":
            lines.append(f"| **{name}** | *not found in the text provided* | |")
        else:
            lines.append(f"| **{name}** | *withheld: the model's quote was not a passage of the source* | |")
    lines += ["", f"Quotes verified: {v['verified']} of {v['verified'] + v['failed']} stated fields. Source: `{s['kind']}`, {s['chars']:,} characters"
              f"{', truncated' if s['truncated'] else ''}, sha256 `{s['sha256'][:12]}`, fetched {s['fetched']}.", ""]
    return "\n".join(lines)


def render_index(cards: list[dict]) -> str:
    lines = ["<!-- generated by tools/extract; do not edit by hand -->", "# Method cards", "",
             f"{len(cards)} machine-extracted cards. Each field has a quote that a program checked against the paper text; "
             "the glosses are the model's. See [how they are made](../07-methodology.md#method-cards).", "",
             "| Paper | First version | Verified fields | Not found |", "|---|---|---|---|"]
    for c in sorted(cards, key=lambda c: c["published"]):
        v = c["verification"]
        lines.append(f"| [{cell(c['title'])}]({c['arxiv']}.md) | {c['published']} | {v['verified']} of 12 | {v['not_found']} |")
    return "\n".join(lines) + "\n"


def cmd_render(a) -> int:
    cards = [json.loads(f.read_text()) for f in sorted(CARDS.glob("*.json"))]
    want = {f"{c['arxiv']}.md": render_card(c) for c in cards}
    want["index.md"] = render_index(cards)
    ok = True
    DOCS.mkdir(parents=True, exist_ok=True)
    for name, text in want.items():
        path = DOCS / name
        text = text.rstrip("\n") + "\n"
        if a.check:
            ok &= path.exists() and path.read_text() == text
        else:
            path.write_text(text)
    stale = [f.name for f in DOCS.glob("*.md") if f.name not in want]
    if a.check:
        ok &= not stale
        print("cards up to date" if ok else "error: docs/cards is stale; run python -m tools.extract render")
        return 0 if ok else 1
    for n in stale:
        (DOCS / n).unlink()
    print(f"rendered {len(cards)} cards")
    return 0


def promote_text(text: str, passing: set[str]) -> tuple[str, int]:
    """In the catalog text, flip read = "abstract" to "card" for the papers whose ids are in `passing`."""
    blocks = text.split("\n[[paper]]\n")
    n = 0
    for i, b in enumerate(blocks):
        m = re.search(r'^arxiv = "([^"]+)"', b, re.M)
        if m and m.group(1) in passing and 'read = "abstract"' in b:
            blocks[i] = b.replace('read = "abstract"', 'read = "card"')
            n += 1
    return "\n[[paper]]\n".join(blocks), n


def cmd_promote(a) -> int:
    path = ROOT / "catalog" / "papers.toml"
    passing = {f.stem for f in CARDS.glob("*.json")
               if json.loads(f.read_text())["verification"]["verified"] >= MIN_VERIFIED}
    text, n = promote_text(path.read_text(), passing)
    path.write_text(text)
    print(f"promoted {n} papers to read = card")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--ids", nargs="*")
    p.add_argument("--exact", action="store_true", help="use count_tokens (needs the key; free of charge)")
    p.add_argument("--redo", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("--ids", nargs="*")
    r.add_argument("--max-usd", type=float, required=True, help="stop starting new papers once this much has been spent")
    r.add_argument("--workers", type=int, default=3)
    r.add_argument("--redo", action="store_true")
    r.add_argument("--yes", action="store_true", help="confirm that you have read the estimate from `plan`")
    sub.add_parser("verify")
    rd = sub.add_parser("render")
    rd.add_argument("--check", action="store_true")
    sub.add_parser("promote")
    a = ap.parse_args(argv)
    return {"plan": cmd_plan, "run": cmd_run, "verify": cmd_verify, "render": cmd_render, "promote": cmd_promote}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
