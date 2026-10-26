"""Command line front end:  python -m tools.evalkit --help"""
from __future__ import annotations

import argparse
import json
import sys

from . import report_card, stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.evalkit", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("se", help="standard error of an annualized Sharpe ratio measured over some years")
    p.add_argument("--sr", type=float, required=True)
    p.add_argument("--years", type=float, required=True)

    p = sub.add_parser("min-record", help="years of data before a Sharpe ratio separates from a benchmark")
    p.add_argument("--sr", type=float, required=True)
    p.add_argument("--sr0", type=float, default=0.0)
    p.add_argument("--confidence", type=float, default=0.95, help="one-sided")
    p.add_argument("--skew", type=float, default=0.0)
    p.add_argument("--kurt", type=float, default=3.0)

    p = sub.add_parser("diff-years", help="years needed for a Sharpe difference between two correlated strategies")
    p.add_argument("--delta", type=float, required=True, help="annualized Sharpe difference to detect")
    p.add_argument("--sr-low", type=float, required=True, help="annualized Sharpe of the weaker strategy")
    p.add_argument("--rho", type=float, required=True, help="correlation of the two return series")
    p.add_argument("--confidence", type=float, default=0.95, help="two-sided")

    sub.add_parser("card-template", help="print the blank report card as JSON")
    p = sub.add_parser("check-card", help="validate a filled report card")
    p.add_argument("path")

    a = ap.parse_args(argv)
    if a.cmd == "se":
        print(f"{stats.sharpe_se_annual(a.sr, a.years):.2f}")
    elif a.cmd == "min-record":
        y = stats.min_track_record_years(a.sr, a.sr0, confidence=a.confidence, skew=a.skew, kurt=a.kurt)
        print(f"{y:.2f} years")
    elif a.cmd == "diff-years":
        y = stats.years_to_resolve_sharpe_diff(a.delta, a.sr_low, a.rho, confidence=a.confidence)
        print(f"{y:.2f} years")
    elif a.cmd == "card-template":
        print(json.dumps(report_card.TEMPLATE, indent=2))
    elif a.cmd == "check-card":
        with open(a.path) as f:
            problems = report_card.validate(json.load(f))
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
