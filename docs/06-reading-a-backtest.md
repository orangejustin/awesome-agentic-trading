# Reading a backtest

A backtest is a measurement, and a measurement without an error bar is an anecdote. Most LLM-trading papers report a Sharpe ratio from a few months of data with no interval. This page gives you the four numbers that tell you how much to believe one, with the formulas, the assumptions behind them, and a command to reproduce each table. Everything is computed by [`tools/evalkit`](../tools/evalkit/), which has tests (including simulations that check the formulas).

**Assumptions, stated once.** The closed forms below assume returns are independent, identically distributed and roughly normal. Real daily trading returns are fat-tailed, skewed and autocorrelated, so treat every closed-form number as a *lower bound* on the data you need. When you have the return series, use the paired block bootstrap in `evalkit.stats.bootstrap_sharpe_diff` instead.

## 1. The error bar on one Sharpe ratio

The Sharpe ratio is estimated, not observed. For a per-period Sharpe ratio measured over N periods, Lo (2002) gives a variance of (1 + SR²/2) / N. Annualizing multiplies the estimator by √252 for daily data and leaves

> SE(annual Sharpe) ≈ √( (1 + SR²/504) / years ) ≈ 1 / √years

The standard error depends almost only on how many years you have. A Sharpe measured over one year is uncertain by about ±1 (one standard error), over four years by about ±0.5.

Applied to the numbers in the papers we took apart:

| Result | Reported Sharpe | Window | Std. error | 95% interval |
|---|---|---|---|---|
| [TradingAgents](teardowns/tradingagents.md), AAPL | 8.21 | 3 months | 2.1 | 4.0 – 12.4 |
| TradingAgents, AMZN (buy-and-hold in the same window: 3.53) | 5.60 | 3 months | 2.1 | 1.6 – 9.6 |
| [FinMem](teardowns/finmem.md), TSLA | 2.68 | 6 months | 1.4 | −0.1 – 5.5 |
| [ContestTrade](teardowns/contesttrade.md) | 3.12 | 6 months | 1.4 | 0.3 – 5.9 |
| [FinRL-X](teardowns/finrl-x.md) paper trading | 1.96 | 19.6 weeks | 1.6 | −1.3 – 5.2 |

These intervals only account for sampling noise in a window that is taken as given. They say nothing about whether the *window* was friendly, which is usually the bigger problem: TradingAgents' AAPL result sits next to a buy-and-hold Sharpe of −1.29 in the same three months, and its AMZN result next to +3.53. A short window mostly measures the market that happened to occur in it.

Reproduce: `python -m tools.evalkit se --sr 5.6 --years 0.25`

## How long is long enough

Two different questions need two different record lengths.

**(a) Is the Sharpe ratio above zero?** The minimum track record length (Bailey and López de Prado, 2012) is the number of years before an observed Sharpe separates from a benchmark at a chosen confidence. To first order it is (z / SR)² years, with z = 1.645 for 95% one-sided; skewness and kurtosis lengthen it.

| True annual Sharpe | Years needed (95%, one-sided, vs zero) | With fat tails (skew −0.5, kurtosis 6) |
|---|---|---|
| 0.5 | 10.8 | 11.0 |
| 0.75 | 4.8 | 4.9 |
| 1.0 | 2.7 | 2.8 |
| 1.5 | 1.2 | 1.3 |
| 2.0 | 0.7 | 0.7 |
| 3.0 | 0.3 | 0.35 |

A strategy with a real Sharpe of 1, which is a very good strategy, needs nearly three years before its record excludes "no skill".

**(b) Is strategy A better than strategy B?** This is the question an architecture paper asks, and it is harder. The variance of a Sharpe *difference* depends on how correlated the two return series are (Jobson and Korkie, 1981, with Memmel's 2003 correction):

> T · Var(SR_A − SR_B) = 2(1 − ρ) + ½(SR_A² + SR_B² − 2·SR_A·SR_B·ρ²), in per-period units.

Agents built on the same model and the same data are usually highly correlated, which makes the difference *easier* to resolve than if they were independent, but only if the difference is real. Years of data needed for a two-sided 95% test, when the weaker strategy has a Sharpe of 0.5:

| Correlation ρ | Gap of 0.25 | Gap of 0.5 | Gap of 1.0 |
|---|---|---|---|
| 0.0 | 123 | 31 | 7.7 |
| 0.5 | 62 | 15 | 3.9 |
| 0.8 | 25 | 6.2 | 1.5 |
| 0.9 | 12 | 3.1 | 0.8 |
| 0.95 | 6.2 | 1.5 | 0.4 |

Read the 0.9 row: two agents that are 90% correlated and differ by half a Sharpe point need about three years of daily data to be told apart. A benchmark with six months of data cannot rank the architectures it compares unless the gaps are enormous, and then it is mostly measuring the window.

Reproduce: `python -m tools.evalkit min-record --sr 1.0` and `python -m tools.evalkit diff-years --delta 0.5 --sr-low 0.5 --rho 0.9`

## 2. Selection inflates the winner

If you try N configurations and report the best, the best is biased upward even when none has skill. Bailey and López de Prado (2014) give the expected maximum Sharpe of N unskilled trials. With a true Sharpe of zero, the expected best annualized Sharpe among N *independent* trials is:

| Window | N = 3 | N = 10 | N = 30 | N = 100 |
|---|---|---|---|---|
| 6 months | 1.2 | 2.2 | 2.9 | 3.6 |
| 1 year | 0.85 | 1.6 | 2.1 | 2.5 |
| 3 years | 0.5 | 0.9 | 1.2 | 1.5 |

These are upper bounds, because real alternatives (three risk personas of one agent, ten prompt variants) are correlated and so behave like fewer independent trials. The right habit is still to count every configuration you looked at, state the number, and use the deflated Sharpe ratio (`evalkit.stats.dsr`) rather than the raw one. [FinMem's](teardowns/finmem.md) published result is the best of three risk settings chosen on the test window, over six months, which is the 6-month, N = 3 cell of this table.

## 3. The window decides more than the strategy

- **Beta versus alpha.** Compare with a passive portfolio over the *same* window, and ask what part of the return a long-only index position would have produced. TradingAgents' own Table 1 shows buy-and-hold Sharpe ratios from −1.29 to +3.53 across three tickers in a single quarter.
- **Regime.** [FINSABER](https://arxiv.org/abs/2505.07078) ran LLM strategies over two decades and more than 100 symbols and found that earlier advantages shrank, that the strategies were too conservative in bull markets and too aggressive in bear markets. A single bull-market quarter cannot show that.
- **Costs.** Always net. A flat 10 basis points per side is a floor, not an estimate; add spread and impact for anything not a mega-cap, and borrow for shorts.
- **Turnover.** Report it. A strategy that trades daily on LLM output pays a cost that a monthly one does not.

## 4. LLM-specific traps

- **The model may know the future.** If the test window is before or near the model's training cutoff, the model may have seen what happened. A paper that names "GPT-4-Turbo" without a snapshot cannot be checked. Use a window after the latest cutoff of every model in the run, mask names and dates in a second arm, and run a look-ahead probe (see [contamination controls](04-fair-evaluation.md#6-contamination-controls)).
- **Non-determinism.** The same prompt can yield different decisions on different runs. Report the number of repeats, or fix seeds where the API allows, and put the spread in the table. [StockBench](https://arxiv.org/abs/2510.02209) averages three seeds per model; most papers report one run.
- **Prompt and tool drift.** A tool that returns different data on a re-fetch (news feeds, revised fundamentals) makes a run unrepeatable. Freeze the data (see [fair evaluation](04-fair-evaluation.md)).

## 5. A checklist for any result you are about to cite

1. How many years, and how many independent decisions? (Under about two years: treat the Sharpe as a story.)
2. What did a passive portfolio do in the same window?
3. Is there an interval, and how was it computed?
4. How many configurations were tried, and was the reported one chosen on the test window?
5. Are costs and turnover reported, and are they realistic for the asset?
6. Is the window after the model's training cutoff, and is the snapshot named?
7. Was there a single-call baseline with the same data and model?
8. Is the code that produced the table in the repository?
9. Has anyone outside the authors rerun it?
10. Are the paper's own tables consistent with each other and with its prose?

The [claim audit](05-claim-audit.md) applies these ten questions to published results.
