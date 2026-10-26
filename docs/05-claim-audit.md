# Claim audit

We checked what we could against the primary sources: the paper text and tables, the repository at a named commit, and, where one exists, an independent rerun. This page lists what did not line up. It is not a ranking of authors. Small errors in tables are ordinary; what matters here is which claims a reader can lean on and which need a second source.

**How to read the status column.**

| Status | Meaning |
|---|---|
| **Internal contradiction** | The source disagrees with itself (abstract versus table, table versus table). |
| **Not reproducible from the repo** | The code or data needed to regenerate the headline table is not in the repository at the snapshot. |
| **Independent rerun differs** | A third party reran the method and got materially different numbers. |
| **Selection on test** | A choice that moves the headline number was made using the test window. |
| **Description mismatch** | A list or secondary source describes the project differently from its paper and code. |

Versions read: TradingAgents paper v7 (2025-06-03); FinRobot paper v2 (2024-05-27); FinMem paper v2 (2023-12-03); ContestTrade paper v5 (2026-08-20); FinRL-X paper v1 (2026-03-22); StockBench paper v2 (2026-03-02); FINSABER paper (KDD 2026 version). Repositories at the commits in each [teardown](teardowns/). A later version or commit may have fixed any of this, and we would like to know.

## Summary

| # | Subject | Finding | Status |
|---|---|---|---|
| 1 | StockBench | The abstract says most models struggle to beat buy-and-hold; the paper's own results section and Table 2 show the opposite | Internal contradiction |
| 2 | FinRL-X | The same benchmark ETFs have different Sharpe and drawdown figures in Tables 2 and 3 | Internal contradiction |
| 3 | TradingAgents | The harness behind Table 1 is not in the repository; the table has two anomalies; the Sharpe comes from three months | Not reproducible from the repo |
| 4 | FinMem | The reported result is the best of three risk settings chosen on the test window | Selection on test |
| 5 | FinMem | An independent rerun on FinMem's own window gives 19.9% and 5.3% for TSLA against 61.8% reported | Independent rerun differs |
| 6 | ContestTrade | The repository has no backtest code, so Table 1 cannot be regenerated | Not reproducible from the repo |
| 7 | ContestTrade | A curated list says one view is selected; the paper and code weight several | Description mismatch |
| 8 | FinMem | The repository ships no market data | Not reproducible from the repo |
| 9 | Trading-R1, FinCon | Listed beside runnable projects; at the snapshot neither repository contains the system | Not reproducible from the repo |
| 10 | FinRobot | Counted as a trading agent in lists; its paper reports no trading performance | Description mismatch |
| 11 | WallStreetPete/awesome-open-source-trading | Two arXiv papers are linked under titles the papers no longer carry | Description mismatch |

## Detail

### 1. StockBench: abstract versus results

The abstract (v2) says: "Surprisingly, most models struggle to outperform the simple buy-and-hold baseline", and the introduction says most agents "fail to outperform this simple baseline in terms of both cumulative return and risk-adjusted return". The results section of the same version says: "Most tested models outperform the passive buy-and-hold baseline, which achieves a modest 0.4% return with a −15.2% drawdown and a Sortino ratio of 0.0155", and "All tested models achieve lower maximum drawdowns than the baseline".

Table 2 agrees with the results section. Of 13 models, 8 have a final return above the baseline's 0.4% and 9 have a Sortino above 0.0155 (one of them, GPT-OSS-120B, by 0.0001); all 13 have a smaller maximum drawdown than the baseline's 15.2%. The window is 82 trading days (2025-03-03 to 2025-06-30); the paper's own sub-window analysis finds that every LLM agent underperformed the passive baseline in a downturn period and outperformed it in an upturn period.

*Reading.* The table and the analysis are the evidence; the abstract's framing is not what they show. The differences between the models, a few percentage points over 82 days on a book that fell 15%, are small next to the book's own volatility, and Table 2 gives point estimates (averaged over three seeds) without an interval on the ranking. *Where to look:* the abstract, the introduction, the results section and Table 2 of arXiv 2510.02209v2.

### 2. FinRL-X: two tables, two answers for SPY and QQQ

Both tables cover the same benchmark ETFs over what the paper calls 2018 to 2025.

| | Table 2 | Table 3 |
|---|---|---|
| SPY Sharpe / max drawdown | 0.84 / −23% | 0.72 / −33.7% |
| QQQ Sharpe / cumulative multiple | 0.95 / 3.61 | 0.81 / 4.02 |

Each table is internally consistent (the Calmar column follows from the return and drawdown columns). Figure 2 is titled "Mar 2018 – Oct 2025" while the setup gives January 7, 2018, which could explain different start dates, but the paper does not say so. *Reading:* a strategy from one table should not be compared with a benchmark from the other. Table 2's own message, that timing improves each allocator and none beats QQQ's Sharpe, does not depend on the discrepancy. *Where to look:* Tables 2 and 3, Figure 2 and Section 4.1 of arXiv 2603.21330.

### 3. TradingAgents: the table's harness is not in the repo

The repository's `backtest.py` states that it evaluates decision quality, "is not a portfolio simulator, and must not grow one", and a search of the tree finds no code computing a Sharpe ratio or drawdown. The paper's Table 1 reports cumulative return, annual return, Sharpe and maximum drawdown for three tickers over 2024-01-01 to 2024-03-29, and says in a footnote that only three months were run because of cost (11 LLM calls and more than 20 tool calls per prediction), that the top Sharpe is above the authors' expected range, and that they attribute it to few pullbacks.

Two anomalies in the table: the GOOGL row for ZMR reads cumulative return −0.58, annual return 0.58, Sharpe 2.12, maximum drawdown 2.34, and the SMA row for GOOGL shares the Sharpe of 2.12 and drawdown of 2.34 with a cumulative return of 6.23; the MACD row for AMZN is blank. The setup text names five stocks and the table reports three. The paper does not state transaction costs, slippage, sizing, sampling temperature, seeds or the number of repeated runs. *Where to look:* Section 5.1, Table 1 and its footnote in arXiv 2412.20138v7; `tradingagents/backtest.py` at `e8f5503`.

### 4 and 5. FinMem: selection on test, and a rerun

The paper states: "We ran FinMem using each of the three available risk inclination settings. The reported performance outcomes are based on the setting that achieved the highest cumulative return during the testing phase." The comparison agents had no equivalent choice. With three settings and a six-month window, luck alone is worth a Sharpe of up to about 1.2 for the best of three independent trials ([selection inflates the winner](06-reading-a-backtest.md#2-selection-inflates-the-winner)); the three settings are correlated, so the true inflation is smaller, but it is not zero.

FINSABER reran FinMem on FinMem's own test window (2022-10-06 to 2023-04-10) with GPT-4o-mini and GPT-4o as backbones (the original used GPT-4-Turbo, so this is a rerun on different models, not an exact reproduction), and printed the original published values next to its own:

| Ticker | FinMem reported | Rerun, GPT-4o-mini | Rerun, GPT-4o |
|---|---|---|---|
| TSLA cumulative return / Sharpe | 61.8% / 2.68 | 19.9% / 0.93 | 5.3% / 0.40 |
| NFLX cumulative return | 36.4% | 32.5% | 16.2% |
| AMZN cumulative return | 4.9% | 2.8% | −20.1% |
| MSFT cumulative return | 23.3% | −7.1% | 12.8% |

FINSABER's broader finding, over two decades and more than 100 symbols, is that previously reported LLM advantages deteriorate and that the strategies are too conservative in bull markets and too aggressive in bear ones. The rerun does not prove the original wrong (different backbones, different implementation details), but it shows the headline does not survive a change of model, which is the property a method claim needs. *Where to look:* FinMem Section 5.1; FINSABER's table headed "FinMem Selection (2022-10-06 to 2023-04-10)", arXiv 2505.07078.

### 6 and 7. ContestTrade

The README's roadmap lists "Visual backtesting and analysis interface" as an unchecked future item, and the word "backtest" appears nowhere in the repository's Python code, so Table 1 (52.80% return, Sharpe 3.12, maximum drawdown 12.41% over January to June 2025) cannot be regenerated from it. The paper is unusually explicit about its limits: "a single controlled backtest", no confidence intervals, six months, one market. The LLMQuant list describes the project as agents competing "before one view is selected for the final decision"; the paper and `research_weight_optimizer.py` weight every agent whose predicted Sharpe is positive, in proportion, so the portfolio is an ensemble, not a single selected view. *Where to look:* `README_en.md` roadmap; the Conclusion of arXiv 2508.00554v5; the list entry in LLMQuant/awesome-trading-agents at the time of our snapshot.

### 8. FinMem: no data

The data folders in the repository hold only placeholders, and the one sample archive is named `Fake-Sample-Data.zip`. The pipeline is there; the dataset behind the paper is not. The repository was last updated on 2024-08-17.

### 9. Trading-R1 and FinCon

Both appear in lists next to runnable projects. At our snapshot the Trading-R1 repository contains one file, a two-line README ("Releasing soon: Trading-R1 Terminal"). The FinCon repository contains a license and a README that says the full system is not yet released because its data agent depends on commercial APIs, and points to the authors' single-agent projects instead.

### 10. FinRobot

The FinRobot paper's evaluation section is two demonstrations, a market-forecasting agent shown on one US and one Chinese stock, and report generation, with no return or accuracy table. The V2 desktop application is an equity-research tool. Lists that group it with trading agents are not wrong to include it, but a reader looking for a trading result will not find one. See the [teardown](teardowns/finrobot.md).

### 11. Retitled papers in a curated list

Two arXiv identifiers linked from WallStreetPete/awesome-open-source-trading carry different titles on arXiv (checked 2026-10-21): 2512.11913 is linked as "Not All Factors Crowd Equally: Modeling, Measuring, and Trading on Alpha Decay" and is titled "Return-Decay Residuals and Tail-Risk Forecasting: …" on arXiv; 2605.01954 is linked as "Moira: Language-Driven Hierarchical Reinforcement Learning for Pair Trading" and is titled "MOIRA: Policy Memory and Belief Revision for Language-Model Agents in Non-Stationary …" on arXiv. We compared the link text of 196 titled arXiv links across the four lists with the current arXiv titles by word overlap; these two papers are the only retitled ones, and the other low-overlap links were abbreviations of the same title. The point is that a link list drifts silently when authors retitle, and the catalog here resolves every identifier against the arXiv API with `tools/verify.py`.

## What this audit does not claim

- We did not rerun any system. Everything above is a reading of the sources.
- A discrepancy is not an accusation. Several of these papers are candid about their limits (ContestTrade's limitations paragraph is a model of the form), and some of the repositories are research code released as is.
- We read the versions named at the top. If a later version resolves an item, tell us and we will update this page and the date.
