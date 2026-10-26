"""The shared interface that makes different agents comparable: rating -> weight -> net return.

Every system under test is reduced to one decision per (asset, date) on a five-tier scale. A fixed
table maps that decision to a target weight, a common cost model charges for the turnover it
causes, and the resulting daily return series is what gets compared. Systems that already emit
weights (for example a weight-centric pipeline) skip the table and enter at `net_returns`.
"""
from __future__ import annotations

TIERS = ("Buy", "Overweight", "Hold", "Underweight", "Sell")

# Symmetric long/short table, gross exposure per asset capped at 1.
LONG_SHORT = {"Buy": 1.0, "Overweight": 0.5, "Hold": 0.0, "Underweight": -0.5, "Sell": -1.0}
# Long-only variant for accounts that cannot short; sells go to cash.
LONG_ONLY = {"Buy": 1.0, "Overweight": 0.5, "Hold": 0.0, "Underweight": 0.0, "Sell": 0.0}


def normalize_rating(text: str) -> str:
    """Map a free-text rating onto the five tiers; unreadable input raises instead of defaulting to Hold."""
    t = text.strip().strip("*_ ").lower()
    for tier in TIERS:
        if t == tier.lower():
            return tier
    raise ValueError(f"unreadable rating: {text!r}")


def weights_from_ratings(ratings: dict[str, str], table: dict[str, float] = LONG_SHORT,
                         max_gross: float = 1.0) -> dict[str, float]:
    """Equal-risk-budget weights: each asset gets table[rating] / n, then gross exposure is capped at `max_gross`."""
    if not ratings:
        return {}
    n = len(ratings)
    w = {k: table[normalize_rating(v)] / n for k, v in ratings.items()}
    gross = sum(abs(x) for x in w.values())
    if gross > max_gross:
        w = {k: x * max_gross / gross for k, x in w.items()}
    return w


def net_returns(weights_by_date: list[dict[str, float]], asset_returns_by_date: list[dict[str, float]],
                cost_bps: float = 10.0) -> list[float]:
    """Daily portfolio returns net of a proportional cost on one-way turnover.

    `weights_by_date[t]` is the target held over day t (decided with information up to t - 1);
    `asset_returns_by_date[t]` are the close-to-close returns realized on day t. Turnover is the
    sum of absolute weight changes versus the previous day's target, starting from cash.
    """
    if len(weights_by_date) != len(asset_returns_by_date):
        raise ValueError("weights and returns must be aligned by date")
    out: list[float] = []
    prev: dict[str, float] = {}
    for w, r in zip(weights_by_date, asset_returns_by_date):
        gross_ret = sum(w.get(k, 0.0) * r.get(k, 0.0) for k in set(w) | set(r))
        assets = set(w) | set(prev)
        turnover = sum(abs(w.get(k, 0.0) - prev.get(k, 0.0)) for k in assets)
        out.append(gross_ret - turnover * cost_bps / 10_000)
        prev = w
    return out
