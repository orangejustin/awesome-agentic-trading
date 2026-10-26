# Same-budget fair evaluation

> Compare systems on the same inputs, through the same interface, at the same cost, and report how performance changes as cost changes. Then say how sure you are.

Take the most-copied design in the field, [TradingAgents](teardowns/tradingagents.md). The agent gets a frontier model, eleven or more calls per decision and a news feed; its baselines (buy-and-hold, MACD, KDJ+RSI, ZMR, SMA) get a price series. If the agent wins, the result is a mixture of the architecture, the model, the data and the spend, and nobody can say which. This page is the design that separates them. The statistics behind it are in [reading a backtest](06-reading-a-backtest.md); the code is in [`tools/evalkit`](../tools/evalkit/).

## 1. Nine rules

1. **Freeze the world.** One point-in-time snapshot of prices, filings and news, with a record of when each item became public. Every system reads from it; none fetches live data inside a run.
2. **Freeze the interface.** Every system reduces to one decision per (asset, decision time) on a five-tier scale (Buy, Overweight, Hold, Underweight, Sell). A fixed table turns ratings into weights. Systems that already emit weights enter at the weight level.
3. **Charge the same costs.** One cost model for all systems, on one-way turnover, plus a stated assumption for spread and borrow where relevant.
4. **Cap the spend.** Tokens, dollars, model calls, tool calls and wall-clock time per decision, enforced by a ledger that raises on breach.
5. **Control the backbone.** The same model snapshot in every system and every tier. When a system wants a strong and a cheap model, map both roles onto the same two models for everyone.
6. **Require baselines.** At least a single-call baseline (same model, same data, one call), a passive baseline, a simple rule, and a random-rating null with the system's own rating frequencies.
7. **Control contamination.** A window after the latest cutoff of every model in the run, plus a masked arm and a look-ahead probe.
8. **Quantify uncertainty.** A paired block-bootstrap interval on the Sharpe difference against the single-call baseline, a deflated Sharpe if more than one configuration was tried, and a refusal to rank when the window is shorter than the [minimum record length](06-reading-a-backtest.md#how-long-is-long-enough).
9. **Publish the report card.** A fixed set of fields ([`report_card.py`](../tools/evalkit/report_card.py)); no complete card, no ranking.

## 2. The frozen world

- **Point-in-time store.** Every record carries `published_at`. A fundamental figure enters on the date the filing was accepted, not the period end; a news item on its first public timestamp; a revised statistic as a new record, not an overwrite.
- **Tool replay cache.** Wrap every tool a system can call. The cache key is the tool name, canonical arguments and the decision timestamp. The first system to ask records the response (from the frozen store); later systems get the identical bytes. A tool that returns different data on a second call (live feeds, ranked search) is replaced by a frozen equivalent before the benchmark starts.
- **Decision time.** Decide after the close of day t using records published by then; the position earns the return of day t+1. `evalkit.ratings.net_returns` assumes exactly this: the weights for day t+1 are fixed with information up to t.
- **Universe.** Point-in-time membership of an index or a fixed list chosen before the window opens. State the count; state how delistings and symbol changes are handled.

## 3. Budget tiers

Let **B** be the measured per-decision spend of the single-call baseline: input tokens, output tokens, dollars at the provider's published prices on the day of the run, zero tool calls, and latency. Tiers are multiples of B:

| Tier | Cap | What it tests |
|---|---|---|
| 1× | B | Whether structure helps when it cannot spend more than one call |
| 4× | 4B | A little room for tools or one extra pass |
| 16× | 16B | Room for a small debate or a few tool calls |
| Native | as published | The system as its authors run it, with its measured multiple of B reported |

Each system is configured to the richest setting that fits the tier (debate rounds, number of analysts, retrieval top-k, tool rounds) and runs behind a `BudgetLedger`. A decision that would breach the cap is recorded as an abstention to cash and counted, never silently dropped; a system whose abstention rate climbs is telling you the tier is too small for it. The deliverable is a curve of net Sharpe (with interval) against dollars per decision, one line per system, not a single leaderboard number.

**Planning arithmetic (illustrative, not a result).** Assume the strong model lists at $4 per million input tokens and $20 per million output tokens (the rate for the model we use for extraction, checked 2026-10-21; check it again before you run). A single-call baseline with a 6,000-token data pack and an 800-token answer costs about 6,000 × $4/1e6 + 800 × $20/1e6 = $0.040 per decision. A 20-stock daily universe for one year is 5,040 decisions, about $200 at 1×, about $3,200 at 16×. A role-based pipeline of 11 calls at 8,000 input and 1,000 output tokens each is about 88,000 in and 11,000 out, roughly $0.57 per decision, about 14× the baseline. A fair benchmark is feasible; it is not free, and the paper that reports only returns hides which side of that bill it paid.

## 4. The decision interface

[`evalkit.ratings`](../tools/evalkit/ratings.py) fixes the mapping:

| Rating | Long/short weight | Long-only weight |
|---|---|---|
| Buy | +1.0 | +1.0 |
| Overweight | +0.5 | +0.5 |
| Hold | 0 | 0 |
| Underweight | −0.5 | 0 |
| Sell | −1.0 | 0 |

Weights are divided equally across assets and capped at a gross exposure of 1. An unreadable rating raises an error; it never defaults to Hold (the [TradingAgents](teardowns/tradingagents.md) `REVIEW` rule). A system that emits direction plus conviction maps conviction to the same five tiers by fixed thresholds chosen before the run. A system that emits weights directly (the [FinRL-X](teardowns/finrl-x.md) contract) is scored on its weights, and also on the rating-mapped version of its own signs, so the interface itself does not decide the winner.

## 5. Baselines and ablations

| Baseline | Why it is there |
|---|---|
| **Single call** | Same model, same cached data pack, one structured-output call. The comparison that decides whether any structure earns its cost. |
| **Passive** | Equal-weight buy-and-hold of the universe. Separates market exposure from skill. |
| **Simple rule** | For example 12-1 month momentum or a moving-average cross. Any LLM system should beat a rule that costs nothing. |
| **Random rating** | Draw ratings at the system's own marginal rating frequencies, many times. Gives a null Sharpe distribution that already includes the system's turnover and cost drag. |
| **Ablations** | Debate off, memory off, tools off, one analyst at a time. Each removes one source of cost and one hypothesis. |

## 6. Contamination controls

A model that has read the future will appear to predict it. Three independent defenses, all reported:

1. **Post-cutoff window.** The test window starts after the latest *published* training cutoff of every model in the run, with a margin of at least six months, because published cutoffs are lower bounds on what the model has seen. Name the exact snapshot of each model; a family name is not enough.
2. **Masked arm.** Rerun the same decisions with tickers replaced by codes, dates replaced by relative days, and absolute price levels normalized (the approach of [KTD-Fin](https://arxiv.org/abs/2605.28359), which also attributes returns to market, style and selection). The gap between the clear and masked arms is a contamination estimate.
3. **Look-ahead probe.** For each model, give it only a date and ask what happened (the Lookahead Propensity test of [Gao et al.](https://arxiv.org/abs/2512.23847)). A model that recalls the outcome from the date alone cannot be tested on that date.

If an older window is unavoidable, run it twice, before and after the cutoff, and publish both. The difference is a measurement of how much memory helped.

## 7. Statistics and attribution

- **Primary metric:** net annualized Sharpe ratio per system and tier, with a paired circular block-bootstrap 95% interval; secondary metrics are maximum drawdown, turnover and the abstention rate.
- **Primary comparison:** each system against the single-call baseline at the same tier; the bootstrap is on the Sharpe *difference*, with both series resampled together.
- **Multiple configurations:** if you tried N settings and report the best, apply the deflated Sharpe ratio and state N.
- **Attribution:** regress daily net returns on the market (and, if data allow, size, value and momentum factors). Report the intercept and its t-statistic next to the raw return. A result that is all beta is not alpha.
- **Refuse to rank** when the window is shorter than the record length the gap would need; print "unresolved" and the years required.

## 8. The report card

Run `python -m tools.evalkit card-template` for the blank card and `python -m tools.evalkit check-card FILE` to validate one. The card records the window and whether it is after the latest model cutoff, the universe and whether it is point in time, the data vendors and the frozen snapshot id, each model's snapshot id and stated cutoff, the rating scale and weight table, the cost model, the budget tier with caps and measured per-decision spend, the baselines, the number of decisions and repeats, the results with their interval and method, and the results of the masked arm and the look-ahead probe.

## 9. Building on what exists

We would not build this from nothing. [StockBench](https://arxiv.org/abs/2510.02209) uses a window chosen after most model cutoffs with a minimal shared workflow and three-seed averaging; [Agent Market Arena](https://arxiv.org/abs/2510.11695) compares architectures across backbones live; [FINSABER](https://arxiv.org/abs/2505.07078) is the model for bias-aware long-horizon backtesting; [KTD-Fin](https://arxiv.org/abs/2605.28359) supplies masking and attribution; [CLQT](https://arxiv.org/abs/2606.29771) supplies a point-in-time gate, institutional costs and a scorecard. What none of them adds, as far as their abstracts and the parts we read show, is a **dollar budget per decision** as a controlled variable. That is the gap this design fills.

## 10. What this does not settle

A frozen-world backtest still understates live frictions (fills, latency, market impact, outages). The last rung of the [evidence ladder](02-evidence-ladder.md) is a forward record: commit the configuration hash before the period starts, run the frozen system on live data, timestamp every decision, and publish it. Everything on this page is the cheaper step that tells you which systems deserve that.
