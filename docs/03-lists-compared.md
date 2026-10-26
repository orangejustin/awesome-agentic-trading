# Four lists, compared

The starting point for this project was four public lists that each claim to map LLM and agentic trading. Reading them side by side shows why a fifth list is not the answer, and what an integration library has to do differently.

| List | Stars (2026-10-21) | Last commit (PT) | Licence | Shape |
|---|---|---|---|---|
| [LLMQuant/awesome-trading-agents](https://github.com/LLMQuant/awesome-trading-agents) | 905 | 2026-07-14 | CC0-1.0 | Link list: agents, MCP servers, skills, a few papers |
| [Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers](https://github.com/Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers) | 257 | 2026-07-24 | CC-BY-4.0 | Paper list by topic, with a written curation policy |
| [bettyguo/awesome-llm-trading-agents](https://github.com/bettyguo/awesome-llm-trading-agents) | 5 | 2026-06-11 | CC0-1.0 (list), MIT (code) | Mixed list with per-entry files and a methodology guide |
| [WallStreetPete/awesome-open-source-trading](https://github.com/WallStreetPete/awesome-open-source-trading) | 6 | 2026-09-21 | CC0-1.0 | Largest list; broad open-source trading, generated from JSON |

## 1. They barely overlap

We extracted every GitHub and arXiv link from each list's files with [`tools/list_audit.py`](../tools/list_audit.py) (it counts links, so it over-counts a list that links its own repository and cannot tell a recommendation from a mention) and compared them on 2026-10-21 (PT):

| List | GitHub repos linked | arXiv papers linked | Repos found nowhere else | Papers found nowhere else |
|---|---|---|---|---|
| LLMQuant/awesome-trading-agents | 116 | 3 | 91 | 1 |
| Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers | 12 | 37 | 5 | 31 |
| bettyguo/awesome-llm-trading-agents | 37 | 33 | 14 | 24 |
| WallStreetPete/awesome-open-source-trading | 470 | 94 | 429 | 82 |

- **Repositories:** 584 distinct across the four. 539 appear in exactly one list; 45 in two or more; 6 in three or more; **none in all four**. The six that appear in three: FinRobot, DeepFund, TradingAgents, AI-Trader, and two general lists (awesome-quant and awesome-ai-in-finance).
- **Papers:** 151 distinct. 138 appear in exactly one list; 13 in two or more; 2 in three or more. **The TradingAgents paper is the only one in all four**; the other paper in three lists is AlphaAgents.

Pairwise, the lists share little. The two code-first lists, LLMQuant (116 repositories) and WallStreetPete (470), have 23 in common; LLMQuant and bettyguo (37) have 5. The paper-first lists are just as disjoint: Tom-roujiang's 37 papers and bettyguo's 33 share 3. Run `python tools/list_audit.py --src DIR` to see the full pairwise matrices.

## 2. The five projects we tore down, across the lists

| | LLMQuant | Tom-roujiang | bettyguo | WallStreetPete |
|---|---|---|---|---|
| TradingAgents | repo + paper | paper | repo + paper | repo + paper |
| FinRobot | repo + paper | | repo | repo |
| FinMem | | | repo + paper | repo + paper |
| ContestTrade | repo | repo + paper | | |
| FinRL-X (FinRL-Trading) | | | | repo |

ContestTrade appears in two lists and FinRL-X in one. FinMem, one of the most cited designs, is absent from LLMQuant's list and from the paper-first list.

## 3. What each list does well, and what we borrow

| List | Strength | What we took |
|---|---|---|
| LLMQuant | Breadth beyond papers: the MCP servers and agent skills layer, real-money experiments, prediction-market specialists | The idea that execution and tooling belong in scope |
| Tom-roujiang | A written **curation policy** (what is in and out), topics split by task (agents, benchmarks, arenas, post-training, factor mining, forecasting, surveys) | The explicit scope statement and the topic taxonomy |
| bettyguo | A **methodology guide** (look-ahead bias, overfitting, multiple testing, survivorship, gross versus net), and one YAML file per entry with a verification record (`verified_on`, sources) | The insistence that every list should teach how to read a backtest, which became [reading a backtest](06-reading-a-backtest.md), and dated verification, which became `stars_asof` and `tools/verify.py` |
| WallStreetPete | The README is **generated from data** (`data/*.json`, `scripts/build_readme.py`), with an activity legend and, for each paper, the reported return, whether costs and out-of-sample tests were included, and how to recreate it | Data first, tables generated; the activity legend |

Two reference lists set the tone we wanted: [Awesome-Generative-RecSys](https://github.com/jihoo-kim/Awesome-Generative-RecSys) organizes a field by the *problem* each paper solves, and [PaperReading](https://github.com/Doragd/PaperReading) gives every paper a dated one-line takeaway.

## 4. Where they drift

- **Description mismatches.** One list summarizes ContestTrade as agents competing before "one view is selected"; the paper and code weight several agents by predicted Sharpe ([claim audit, item 7](05-claim-audit.md)).
- **Silent retitling.** WallStreetPete/awesome-open-source-trading links two arXiv papers under titles that the papers no longer carry ([claim audit, item 11](05-claim-audit.md)).
- **Counts that depend on how you count.** That list's badges say 458 projects and 113 papers; counting distinct links gives 470 and 94. Neither is wrong, and neither can be rechecked without a stated rule.
- **Freshness.** Last commits fall between 2026-06-11 and 2026-09-21. bettyguo records a `verified_on` date and sources in each entry's YAML; WallStreetPete dates its star and activity snapshot (September 2026); LLMQuant says dates are not shown per item; we found no verification dates in Tom-roujiang's list.
- **No grade on the evidence.** A project with a 112k-star README and a project with a one-line README are rendered the same way.

## 5. What an integration library has to do differently

1. **One schema, with a grade.** Every project carries an [evidence rung](02-evidence-ladder.md), a reproducibility grade and a read depth, validated by [`tools/atlas.py`](../tools/atlas.py).
2. **Data first, tables generated.** `catalog/*.toml` is the source; the tables under `docs/catalog/` are rendered and checked for staleness in CI.
3. **Every identifier verified by script.** [`tools/verify.py`](../tools/verify.py) resolves each arXiv identifier and repository, and it is run on a schedule so drift is caught rather than inherited.
4. **Depth on a few, honest labels on the rest.** Five full [teardowns](teardowns/); everything else is labelled with how much of it we read.
5. **A way to compare.** A [same-budget protocol](04-fair-evaluation.md), because a map without a way to compare the territory just becomes a longer list.
6. **A claim audit.** What did not line up is [published](05-claim-audit.md), with the version and commit we read.

## 6. What we left out on purpose

General quant tooling (backtesting engines for non-LLM strategies, options libraries, prediction-market SDKs) is where WallStreetPete's list is deepest and where our catalog is thinnest by design: we included the engines an LLM agent is likely to call (Lean, NautilusTrader, Qlib, OpenBB, the Alpaca MCP server) and refer readers to that list for the rest. The twelve repositories that two or more lists link and that we left out (four general lists and eight general quant libraries such as backtrader and vectorbt) are named, with a reason, in [`catalog/excluded.toml`](../catalog/excluded.toml), and `tools/list_audit.py --catalog` fails if a multi-list repository is in neither place. The inclusion rules are in the [methodology](07-methodology.md).
