"""The report card every evaluation run must fill in, and the check that it is complete.

An evaluation that omits any of these fields cannot be compared with another one. The validator
returns a list of problems, empty when the card is complete; it checks presence and shape, not truth.
"""
from __future__ import annotations

REQUIRED = {
    "window": ["start", "end", "after_latest_model_cutoff"],
    "universe": ["description", "point_in_time", "n_assets"],
    "data": ["vendors", "frozen_snapshot", "as_of_rule"],
    "models": ["list"],            # each: name, snapshot_id, stated_cutoff
    "decision_interface": ["rating_scale", "weight_table", "rebalance"],
    "costs": ["model", "bps_one_way"],
    "budget": ["tier", "caps", "measured_per_decision"],
    "baselines": ["list"],         # must include a single-call baseline and a passive baseline
    "runs": ["n_decisions", "n_seeds_or_repeats"],
    "results": ["net_sharpe", "interval", "interval_method", "max_drawdown", "turnover"],
    "contamination": ["masked_arm", "lookahead_probe"],
}
REQUIRED_BASELINE_KINDS = {"single_call", "passive"}


def validate(card: dict) -> list[str]:
    problems: list[str] = []
    for section, keys in REQUIRED.items():
        block = card.get(section)
        if not isinstance(block, dict):
            problems.append(f"missing section: {section}")
            continue
        for k in keys:
            if k not in block or block[k] in (None, "", []):
                problems.append(f"missing field: {section}.{k}")
    models = card.get("models", {}).get("list", []) if isinstance(card.get("models"), dict) else []
    for i, m in enumerate(models):
        for k in ("name", "snapshot_id", "stated_cutoff"):
            if not m.get(k):
                problems.append(f"models.list[{i}] missing {k}")
    baselines = card.get("baselines", {}).get("list", []) if isinstance(card.get("baselines"), dict) else []
    kinds = {b.get("kind") for b in baselines if isinstance(b, dict)}
    for kind in sorted(REQUIRED_BASELINE_KINDS - kinds):
        problems.append(f"baselines.list must include a '{kind}' baseline")
    res = card.get("results")
    if isinstance(res, dict) and isinstance(res.get("interval"), (list, tuple)) and len(res["interval"]) != 2:
        problems.append("results.interval must be [low, high]")
    return problems


TEMPLATE = {
    "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "after_latest_model_cutoff": True},
    "universe": {"description": "", "point_in_time": True, "n_assets": 0},
    "data": {"vendors": [], "frozen_snapshot": "id or hash", "as_of_rule": "records usable only if published before the decision time"},
    "models": {"list": [{"name": "", "snapshot_id": "", "stated_cutoff": "YYYY-MM"}]},
    "decision_interface": {"rating_scale": "5-tier", "weight_table": "LONG_SHORT", "rebalance": "daily"},
    "costs": {"model": "proportional on one-way turnover", "bps_one_way": 10},
    "budget": {"tier": "1x", "caps": {}, "measured_per_decision": {}},
    "baselines": {"list": [{"kind": "single_call"}, {"kind": "passive"}, {"kind": "rule"}, {"kind": "random_rating"}]},
    "runs": {"n_decisions": 0, "n_seeds_or_repeats": 0},
    "results": {"net_sharpe": 0.0, "interval": [0.0, 0.0], "interval_method": "paired circular block bootstrap", "max_drawdown": 0.0, "turnover": 0.0},
    "contamination": {"masked_arm": "result of the name-and-date-masked run", "lookahead_probe": "result of the date-only recall probe"},
}
