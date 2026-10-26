"""Claude API access for the extraction run: key lookup, one call, spend accounting.

The key is never printed, logged, written to a card or put in an exception message. It comes from the
ANTHROPIC_API_KEY (or ATLAS_ANTHROPIC_API_KEY) environment variable, or from the output of a command named in the git-ignored
tools/extract/local.toml (for example a lookup in the operating system's secret store). See tools/extract/README.md.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .schema import SCHEMA, SYSTEM, user_prompt

MODEL = "claude-opus-5-5"
EFFORT = "medium"
PRICE_IN = 4.00 / 1_000_000    # USD per input token (checked 2026-10-21; verify before a large run)
PRICE_OUT = 20.00 / 1_000_000  # USD per output token, thinking tokens included
MAX_TOKENS = 16_000
LOCAL = Path(__file__).resolve().parent / "local.toml"


class Refused(RuntimeError):
    pass


class Truncated(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


def cost(input_tokens: int, output_tokens: int) -> float:
    return input_tokens * PRICE_IN + output_tokens * PRICE_OUT


KEY_ENVS = ("ANTHROPIC_API_KEY", "ATLAS_ANTHROPIC_API_KEY")
WORKSPACE_ENV = "ATLAS_ANTHROPIC_WORKSPACE"  # optional: sent as the anthropic-workspace-id header


def get_api_key() -> str:
    for name in KEY_ENVS:
        key = os.environ.get(name, "").strip()
        if key:
            return key
    if LOCAL.exists():
        cmd = tomllib.loads(LOCAL.read_text()).get("key_command")
        if cmd:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
            # stderr is deliberately not shown: it may name the secret store
            raise RuntimeError(f"key_command in {LOCAL.name} failed (exit {r.returncode})")
    raise RuntimeError("no API key: set ANTHROPIC_API_KEY or create tools/extract/local.toml (see tools/extract/README.md)")


def make_client():
    try:
        import anthropic
    except ImportError as e:
        raise SystemExit("the anthropic package is required for `plan --exact` and `run`: pip install -r tools/extract/requirements.txt") from e
    headers = {}
    workspace = os.environ.get(WORKSPACE_ENV, "").strip()
    if workspace:
        headers["anthropic-workspace-id"] = workspace
    return anthropic.Anthropic(api_key=get_api_key(), max_retries=4, timeout=600.0, default_headers=headers or None)


@dataclass
class Ledger:
    """Running spend. Thread-safe; refuses new work once the cap is reached."""
    max_usd: float
    spent: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    def __post_init__(self):
        self._lock = threading.Lock()

    def check(self) -> None:
        with self._lock:
            if self.spent >= self.max_usd:
                raise BudgetExceeded(f"spend ${self.spent:.2f} reached the cap ${self.max_usd:.2f}")

    def add(self, input_tokens: int, output_tokens: int) -> float:
        c = cost(input_tokens, output_tokens)
        with self._lock:
            self.spent += c
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.calls += 1
        return c


def extract_one(client, title: str, text: str, ledger: Ledger, model: str = MODEL, effort: str = EFFORT) -> tuple[dict, dict]:
    """One Messages call. Returns (fields, usage). Raises Refused, Truncated or BudgetExceeded."""
    ledger.check()
    resp = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_prompt(title, text)}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": SCHEMA}},
    )
    usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
    ledger.add(usage["input_tokens"], usage["output_tokens"])  # a refused or truncated call is still billed
    if resp.stop_reason == "refusal":
        raise Refused(f"model refused ({getattr(getattr(resp, 'stop_details', None), 'category', None)})")
    if resp.stop_reason == "max_tokens":
        raise Truncated("hit max_tokens before finishing the card")
    body = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return json.loads(body), usage


def count_input_tokens(client, title: str, text: str, model: str = MODEL) -> int:
    r = client.messages.count_tokens(model=model, system=SYSTEM, messages=[{"role": "user", "content": user_prompt(title, text)}])
    return r.input_tokens
