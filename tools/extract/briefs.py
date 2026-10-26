"""Draft the short per-project lines shown on the home page (catalog/briefs.toml).

    python -m tools.extract.briefs --yes [--ids ID ...]

One Claude API call per project. The model sees only the catalog entry (and, for a teardown, its opening
summary) and is told to add no facts. The output is a draft: catalog/briefs.toml is reviewed by hand before it
is committed, and `tools/atlas.py check` requires an entry for every non-list project.
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

from .client import EFFORT, MODEL, Ledger, cost, make_client

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "catalog" / "briefs.toml"

FIELDS = ["tagline", "audience", "limit", "tagline_zh", "audience_zh", "limit_zh"]
SCHEMA = {
    "type": "object",
    "properties": {f: {"type": "string"} for f in FIELDS},
    "required": FIELDS,
    "additionalProperties": False,
}
SYSTEM = (
    "You write very short catalog lines for an open-source directory of LLM and agentic trading projects. "
    "Use only facts present in the entry you are given; never add numbers, features, judgements or claims that are not in it. "
    "Neutral tone, no marketing words, no exclamation marks, no emoji. "
    "tagline: what the project is and does, at most 12 English words, no trailing period. "
    "audience: who it suits, at most 10 English words, starting with a noun phrase such as 'Researchers who' or 'Developers building'; "
    "infer only from what the project is (kind, layers, summary). "
    "limit: the single most important limitation, at most 14 English words, taken from the caveat or the evidence and repro grades; "
    "if there is no caveat, state what the grades imply (for example that results are not regenerable from the repo). "
    "The _zh fields are natural Simplified Chinese versions of the same three lines (tagline_zh at most 24 characters, "
    "audience_zh at most 20, limit_zh at most 30), keeping project and product names in English."
)

GRADES = (
    "Evidence rungs: L0 claim only, L1 runnable code, L2 disclosed backtest, L3 independent or out-of-sample, L4 forward record; "
    "bench = evaluates other systems; n/a = infrastructure or no performance claim. "
    "Repro: full, partial, none, unverified (README and code read, not rerun), n/a."
)


def entry_text(p: dict) -> str:
    keep = {k: p.get(k) for k in ("name", "repo", "kind", "layers", "license", "last_commit", "evidence", "repro", "read", "summary", "caveat")}
    text = json.dumps(keep, ensure_ascii=False, indent=1)
    td = ROOT / "docs" / "teardowns" / f"{p['id']}.md"
    if td.exists():
        lead = [l[2:] for l in td.read_text().splitlines() if l.startswith("> ")]
        if lead:
            text += "\n\nOpening summary of our teardown:\n" + " ".join(lead)
    return text


def toml_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="required: the calls are paid")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--max-usd", type=float, default=3.0)
    a = ap.parse_args(argv)
    if not a.yes:
        print("refusing to spend without --yes", file=sys.stderr)
        return 2
    projects = [p for p in tomllib.loads((ROOT / "catalog" / "projects.toml").read_text())["project"] if p["kind"] != "list"]
    if a.ids:
        projects = [p for p in projects if p["id"] in a.ids]
    client, ledger, out = make_client(), Ledger(a.max_usd), []
    for p in projects:
        ledger.check()
        r = client.messages.create(
            model=MODEL, max_tokens=4000, system=SYSTEM,
            messages=[{"role": "user", "content": f"{GRADES}\n\n<entry>\n{entry_text(p)}\n</entry>"}],
            output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": SCHEMA}},
        )
        ledger.add(r.usage.input_tokens, r.usage.output_tokens)
        if r.stop_reason != "end_turn":
            print(f"{p['id']}: stop_reason {r.stop_reason}, skipped", file=sys.stderr)
            continue
        d = json.loads("".join(b.text for b in r.content if b.type == "text"))
        out.append((p["id"], d))
        print(f"{p['id']}: {d['tagline']}")
    lines = ["# Short home-page lines per project, drafted with tools/extract/briefs.py (Claude API) from the catalog",
             "# entry only, then reviewed by hand. tools/atlas.py check requires one entry per non-list project.", ""]
    for pid, d in out:
        lines.append(f"[{pid}]")
        lines += [f"{f} = {toml_str(d[f])}" for f in FIELDS]
        lines.append("")
    OUT.write_text("\n".join(lines))
    print(f"{len(out)} drafts -> {OUT.relative_to(ROOT)}; {ledger.calls} calls, ${ledger.spent:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
