"""Per-decision spend accounting for the same-budget protocol.

A ledger is opened for each decision. Every model call and tool call is recorded against it, and a
cap that is crossed raises, so a system cannot quietly spend ten times its rival's budget. Prices are
passed in (dollars per million tokens) and should be copied from the provider's price list on the
day of the run, with that date recorded in the report card.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class Caps:
    input_tokens: int | None = None
    output_tokens: int | None = None
    dollars: float | None = None
    model_calls: int | None = None
    tool_calls: int | None = None
    seconds: float | None = None


@dataclass
class BudgetLedger:
    caps: Caps
    price_in_per_mtok: float
    price_out_per_mtok: float
    input_tokens: int = 0
    output_tokens: int = 0
    model_calls: int = 0
    tool_calls: int = 0
    started: float = field(default_factory=time.monotonic)

    @property
    def dollars(self) -> float:
        return (self.input_tokens * self.price_in_per_mtok + self.output_tokens * self.price_out_per_mtok) / 1_000_000

    @property
    def seconds(self) -> float:
        return time.monotonic() - self.started

    def _check(self) -> None:
        c = self.caps
        checks = [
            ("input_tokens", self.input_tokens, c.input_tokens),
            ("output_tokens", self.output_tokens, c.output_tokens),
            ("dollars", self.dollars, c.dollars),
            ("model_calls", self.model_calls, c.model_calls),
            ("tool_calls", self.tool_calls, c.tool_calls),
            ("seconds", self.seconds, c.seconds),
        ]
        for name, used, cap in checks:
            if cap is not None and used > cap:
                raise BudgetExceeded(f"{name} {used:.4g} exceeds cap {cap:.4g}")

    def record_model_call(self, input_tokens: int, output_tokens: int) -> None:
        self.model_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self._check()

    def record_tool_call(self) -> None:
        self.tool_calls += 1
        self._check()

    def summary(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "dollars": round(self.dollars, 6),
            "seconds": round(self.seconds, 3),
        }


def scale_caps(base: Caps, factor: float) -> Caps:
    """Budget tiers are multiples of the single-call baseline's measured spend."""
    def s(x):
        return None if x is None else x * factor
    return Caps(*(s(getattr(base, f)) for f in
                  ("input_tokens", "output_tokens", "dollars", "model_calls", "tool_calls", "seconds")))
