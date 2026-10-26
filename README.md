<p align="center"><img src="assets/banner.svg" alt="Agentic Trading Atlas" width="100%"></p>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a></p>

**Agentic Trading Atlas** is a checked directory of LLM and agentic trading projects. Every project below says what it does, who it suits, whether it is maintained, its license and its most important limit, so you can find the one you want in a minute. Behind the directory sit graded papers, deep dives into five systems, and a design for comparing them fairly.

<!-- atlas:headline -->57 papers, 39 projects, 5 teardowns<!-- /atlas:headline -->. Snapshot: 2026-10-21 (US Pacific time).

> Research and education only. Nothing here is financial advice, and nothing here places an order.

## Find a project by what you need

| You want to | Start with |
|---|---|
| Run a multi-agent "trading firm" that debates and rates a stock | [TradingAgents](https://github.com/TauricResearch/TradingAgents), [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund), [ContestTrade](https://github.com/FinStep-AI/ContestTrade) |
| Study a single agent with memory | [FinMem](https://github.com/pipiku915/FinMem-LLM-StockTrading) |
| Write equity research where the numbers come from code, not the LLM | [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) |
| Mine factors or automate quant research | [Qlib](https://github.com/microsoft/qlib), [RD-Agent](https://github.com/microsoft/RD-Agent), [QuantaAlpha](https://github.com/QuantaAlpha/QuantaAlpha), [AlphaGen](https://github.com/RL-MLDM/alphagen) |
| Allocate a portfolio with RL, or carry target weights from backtest to a broker | [FinRL](https://github.com/AI4Finance-Foundation/FinRL), [FinRL-X](https://github.com/AI4Finance-Foundation/FinRL-Trading) |
| Give an agent market data | [OpenBB](https://github.com/OpenBB-finance/OpenBB), [Yahoo Finance MCP](https://github.com/Alex2Yang97/yahoo-finance-mcp), [Massive MCP Server](https://github.com/massive-com/mcp_massive), [Financial Datasets MCP Server](https://github.com/financial-datasets/mcp-server) |
| Backtest and trade with a mature engine | [LEAN](https://github.com/QuantConnect/Lean), [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) |
| Benchmark or stress-test trading agents | [DeepFund](https://github.com/HKUSTDial/DeepFund), [Live Trade Bench](https://github.com/ulab-uiuc/live-trade-bench), [AI-Trader](https://github.com/HKUDS/AI-Trader), [TradeTrap](https://github.com/Yanlewen/TradeTrap), [PIXIU / FinBen](https://github.com/The-FinAI/PIXIU) |
| Trade prediction markets | [Kalshi AI Trading Bot](https://github.com/ryanfrigo/kalshi-ai-trading-bot), [Oracle3](https://github.com/YichengYang-Ethan/oracle3), [polymarket-paper-trader](https://github.com/agent-next/polymarket-paper-trader) |
| See a real forward record, good or bad | [Kalshi AI Trading Bot](https://github.com/ryanfrigo/kalshi-ai-trading-bot) (publishes its own "no measured edge" verdict), [LLM Trading Lab](https://github.com/LuckyOne7777/LLM-Trading-Lab) |

Tools that let an agent place orders (Alpaca MCP Server, Polymarket MCP Server, fintool and others) are in the directory below; start them on a paper account.

## Five flagship systems, side by side

From our [deep dives](docs/teardowns/), each read down to the code at a named commit.

| | [TradingAgents](docs/teardowns/tradingagents.md) | [FinMem](docs/teardowns/finmem.md) | [ContestTrade](docs/teardowns/contesttrade.md) | [FinRobot](docs/teardowns/finrobot.md) | [FinRL-X](docs/teardowns/finrl-x.md) |
|---|---|---|---|---|---|
| Shape | Analysts, bull/bear debate, trader, risk debate, portfolio manager | One agent, layered memory, risk persona | Competing agent teams, weighted by predicted Sharpe | Research workstation; code computes, LLM writes | Weight pipeline from backtest to broker |
| Risk limits enforced in code | No: the risk team is three prompts | No: risk is a persona prompt | Partly: zero weight below zero predicted Sharpe; no exposure cap | Not a trading system | Yes: order value limit and turnover scaling |
| Paper's headline table regenerable from the repo | No | No: no market data shipped | No: backtest code missing | No trading claim | Not rerun by us |
| Maintained (2026-10-21) | Active | Dormant since 2024-08 | Slowing | Active | Active |
| Suits | Developers building multi-agent decision pipelines | Researchers studying agent memory | Researchers studying competing agents | Developers who want auditable research numbers | Developers wiring backtests to brokers |

## All projects

Grouped by the job each project does first. "Maintained" counts days from the last commit to the snapshot date: active is within 90 days, slowing within a year, dormant beyond. The lines are short by design; the [full catalog](docs/catalog/projects.md) adds stars, evidence grades and longer notes.

<!-- atlas:directory -->
### Decision architectures

| Project | What it does | Suits | Maintained | License | Key limit |
|---|---|---|---|---|---|
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) · [deep dive](docs/teardowns/tradingagents.md) | LangGraph multi-agent trading firm whose analyst and risk debates yield five-tier ratings | Developers building multi-agent LLM trading decision pipelines | active | Apache-2.0 | Evaluates decision quality only; no portfolio simulator, Sharpe code or paper harness |
| [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund) | LLM investor agents run a fund mandate with historical backtest replay | Learners exploring multi-agent LLM investment decision workflows | active | MIT | Educational only per author's disclaimer; places no trades, results not rerun |
| [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | Toolkit giving an AI agent trading capabilities, with API and MCP access | Developers building AI agents that make and execute trades | active | MIT | Gives an agent order paths; no performance claim checked |
| [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) | Chinese A-share derivative of TradingAgents with web app, screening and paper trading | Developers building multi-agent trading tools for Chinese A-shares | active | Apache-2.0 core + proprietary app layer | Hybrid license: application layer is source-available, not open source |
| [QuantAgent / QuantHarness](https://github.com/Y-Research-SBU/QuantAgent) | LangGraph multi-agent technical-analysis system for short-horizon trading with web UI | Developers building multi-agent technical-analysis trading systems | active | MIT | Paper backtest not rerun; short-horizon results need long records |
| [FinMem](https://github.com/pipiku915/FinMem-LLM-StockTrading) · [deep dive](docs/teardowns/finmem.md) | Single LLM trading agent with risk persona and three-layer decaying memory | Researchers studying memory design for LLM trading agents | dormant | MIT | Repo ships no market data, only placeholders and a fake sample zip |
| [Agentic Trading Lab](https://github.com/Open-Finance-Lab/AgenticTrading) | Research platform to build, backtest and paper-trade LLM trading agents | Researchers who build and inspect LLM trading agents | active | OpenMDW-1.0 | Uses the uncommon OpenMDW-1.0 license; read it before reuse |
| [ContestTrade](https://github.com/FinStep-AI/ContestTrade) · [deep dive](docs/teardowns/contesttrade.md) | Multi-agent framework where competing teams build text factors and trades, weighted by predicted Sharpe | Researchers studying competitive multi-agent trading decision systems | slowing | Apache-2.0 | Repo lacks backtest code, so the paper's Table 1 cannot be regenerated |
| [Kalshi AI Trading Bot](https://github.com/ryanfrigo/kalshi-ai-trading-bot) | Kalshi trading toolkit with an edge audit, MCP server and agent tools | Developers building or auditing agents for Kalshi prediction markets | active | MIT | Own forward verdict over 55 trades reports no measured edge |
| [Trading-R1](https://github.com/TauricResearch/Trading-R1) | Reasoning model trained with SFT and RL to produce investment theses | Researchers who follow LLM reasoning models for investment decisions | dormant | none found | Repo holds only a two-line README; no model or code released |
| [Oracle3](https://github.com/YichengYang-Ethan/oracle3) | Prediction-market agent toolkit for Kalshi and Polymarket with paper and live execution | Developers building agents that trade Kalshi and Polymarket contracts | active | Apache-2.0 | Claims only; no backtest or record disclosed |
| [Kalshi Trading Bot CLI](https://github.com/OctagonAI/kalshi-trading-bot-cli) | CLI that estimates Kalshi market probabilities and sizes trades with fractional Kelly | Developers building LLM-driven prediction market trading tools | active | MIT | No performance record published; estimates may rely on the vendor's research API |
| [FinCon](https://github.com/The-FinAI/FinCon) | Manager-analyst agent hierarchy with risk-control agent triggering self-critique | Researchers studying hierarchical multi-agent trading decision frameworks | active | MIT | Code not released; repo holds only a license and README |

### Perception (text and numbers into signals)

| Project | What it does | Suits | Maintained | License | Key limit |
|---|---|---|---|---|---|
| [FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) | Open financial LLM project with data pipelines and LoRA fine-tuning recipes | Researchers fine-tuning LLMs for finance NLP tasks | active | MIT | A model and data project; no trading-performance claim checked |
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) · [deep dive](docs/teardowns/finrobot.md) | Equity-research agent platform where code computes figures and LLMs write narrative | Developers building LLM research tools with auditable numbers | active | Apache-2.0 | Research workstation, not a trading system; no trading-performance claim to test |
| [PIXIU / FinBen](https://github.com/The-FinAI/PIXIU) | Open financial LLM FinMA with instruction data and FinBen evaluation suite | Researchers evaluating LLMs on financial language and reasoning tasks | active | MIT | High scores on these tasks say little about trading performance |
| [Qwen DianJin](https://github.com/aliyun/qwen-dianjin) | Alibaba Cloud hub for finance reasoning models, datasets and benchmarks | Researchers evaluating or building LLMs for financial tasks | active | MIT (sub-projects under Apache-2.0 in LICENSES/) | A research hub, not a trading system; sub-projects have separate READMEs and licenses |

### Alpha and research automation

| Project | What it does | Suits | Maintained | License | Key limit |
|---|---|---|---|---|---|
| [RD-Agent](https://github.com/microsoft/RD-Agent) | Agent loop that proposes, implements and evaluates quant factor and model ideas | Researchers who automate alpha factor and model research | active | MIT | No headline result checked; factor gains need held-out testing |
| [QuantaAlpha](https://github.com/QuantaAlpha/QuantaAlpha) | LLM-driven evolutionary factor mining from research direction to backtested factors | Researchers exploring automated alpha factor discovery with LLMs | slowing | MIT (README badge) | No LICENSE file; MIT appears only on a README badge |
| [AlphaGen](https://github.com/RL-MLDM/alphagen) | RL agent generating formulaic alpha factor sets on Qlib, with LLM module | Quant researchers who mine formulaic alpha factors | slowing | none found | No LICENSE file in the repository; reinforcement learning core, LLM module added later |

### Portfolio, risk and RL

| Project | What it does | Suits | Maintained | License | Key limit |
|---|---|---|---|---|---|
| [FinRL](https://github.com/AI4Finance-Foundation/FinRL) | Deep reinforcement learning library and tutorials for stock trading environments | Researchers applying deep RL to portfolio trading simulations | active | MIT | Teaching-oriented RL environments; no headline result checked here |
| [FinRL-X (FinRL-Trading)](https://github.com/AI4Finance-Foundation/FinRL-Trading) · [deep dive](docs/teardowns/finrl-x.md) | Weight-centric pipeline that backtests target weights and sends them to a broker | Developers building trading systems needing shared backtest-to-broker interfaces | active | Apache-2.0 | RL allocator barely beats equal-weight; both trail QQQ without timing overlay |

### Data and point-in-time access

| Project | What it does | Suits | Maintained | License | Key limit |
|---|---|---|---|---|---|
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) | Open data-integration platform serving market and economic data to Python and agents | Developers building apps or AI agents needing market data | active | Apache-2.0 | Data access only; point-in-time correctness is up to you |
| [Qlib](https://github.com/microsoft/qlib) | Quant research platform with data layer, ML model zoo and backtest tooling | Researchers building ML alpha models and backtest workflows | active | MIT | General quant platform; the LLM agent layer is up to you |
| [Financial Datasets MCP Server](https://github.com/financial-datasets/mcp-server) | MCP server exposing Financial Datasets API financials, prices and company news | Developers connecting LLM agents to financial statement and price data | dormant | MIT | Requires a Financial Datasets API key; last commit 2025-06-05 |
| [Massive MCP Server](https://github.com/massive-com/mcp_massive) | First-party MCP server exposing the Massive (formerly Polygon.io) market-data API | Developers connecting LLM agents to Massive market data | active | MIT | Marked experimental by its authors and requires a Massive API key |
| [Yahoo Finance MCP](https://github.com/Alex2Yang97/yahoo-finance-mcp) | MCP server giving LLM clients Yahoo Finance prices, statements, options and news | Developers connecting LLM clients to free market data | active | MIT | Wraps yfinance current data, not point-in-time; unsuitable for backtesting |

### Execution and infrastructure

| Project | What it does | Suits | Maintained | License | Key limit |
|---|---|---|---|---|---|
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) | Event-driven engine running the same strategy code in backtest and live | Developers building strategies for both backtesting and live execution | active | LGPL-3.0 | General engine, not LLM-specific; agent integration is up to you |
| [LEAN](https://github.com/QuantConnect/Lean) | Event-driven algorithmic trading engine for research, backtesting and live trading | Developers building strategies to backtest and trade live via brokers | active | Apache-2.0 | General engine, not LLM-specific; agent integration is up to you |
| [Alpaca MCP Server](https://github.com/alpacahq/alpaca-mcp-server) | MCP server letting LLM clients query market data and place Alpaca orders | Developers connecting LLM agents to Alpaca brokerage accounts | active | MIT | Gives an agent order authority; run on a paper account first |
| [Polymarket MCP Server](https://github.com/caiovicentino/polymarket-mcp-server) | MCP server exposing 45 tools for Polymarket discovery, trading and monitoring | Developers connecting LLM clients to Polymarket trading | active | MIT | Grants an LLM client order authority over real funds; test on paper first |
| [fintool](https://github.com/second-state/fintool) | Rust CLI suite giving agents per-venue trading binaries plus market data | Developers building agents that trade on crypto and prediction venues | slowing | MIT | Holds order authority on live venues; start with small size or testnet |

### Evaluation, benchmarks and bias control

| Project | What it does | Suits | Maintained | License | Key limit |
|---|---|---|---|---|---|
| [AI-Trader](https://github.com/HKUDS/AI-Trader) | Agent-native trading platform and live leaderboard where outside AI agents trade | Researchers who benchmark AI trading agents in live settings | slowing | MIT (README badge) | No LICENSE file at repo root; MIT stated only in README badge |
| [LLM Trading Lab](https://github.com/LuckyOne7777/LLM-Trading-Lab) | Logged six-month live experiment of ChatGPT managing a real-money micro-cap portfolio | Researchers who study live LLM portfolio management behavior | slowing | none found | Single six-month run with author-run evaluation; too short to prove skill |
| [DeepFund](https://github.com/HKUSTDial/DeepFund) | Live arena benchmarking LLM fund managers on post-cutoff market data | Researchers who evaluate LLM trading agents | slowing | MIT | Arena results depend on a short live window |
| [Live Trade Bench](https://github.com/ulab-uiuc/live-trade-bench) | FastAPI platform running and monitoring LLM trading agents live on stocks and Polymarket | Researchers who evaluate LLM trading agents under live conditions | slowing | PolyForm Noncommercial 1.0.0 | Noncommercial license restricts reuse; check terms before adopting |
| [TradeTrap](https://github.com/Yanlewen/TradeTrap) | Fault-injection toolkit testing LLM trading agents against attacks and data manipulation | Researchers who stress-test the robustness of LLM trading agents | slowing | Apache-2.0 | Measures robustness, not profitability |

### Simulation

| Project | What it does | Suits | Maintained | License | Key limit |
|---|---|---|---|---|---|
| [StockAgent](https://github.com/MingyuJ666/Stockagent) | Simulated stock exchange where LLM investors trade under external factors | Researchers studying how external factors shape LLM trading behavior | slowing | none found | No LICENSE file in the repo, so reuse terms are unclear |
| [polymarket-paper-trader](https://github.com/agent-next/polymarket-paper-trader) | Paper-trading gym for agents on live Polymarket order books with MCP server | Developers building and benchmarking prediction-market trading agents | active | MIT | Prediction markets only, not equities; fill-fidelity claim is the author's own |
<!-- /atlas:directory -->

## What we found

- **No headline result has been independently reproduced.** In all three agentic systems we read that publish a trading table (TradingAgents, FinMem, ContestTrade), the code or data needed to regenerate it is missing from the repository ([claim audit](docs/05-claim-audit.md)).
- **Headline Sharpe ratios come from a few months.** Three months of data leaves an error of about ±2 on a Sharpe ratio; a strategy with a true Sharpe of 1 needs close to three years to separate from zero ([reading a backtest](docs/06-reading-a-backtest.md)).
- **Architecture comparisons rarely control for spend.** TradingAgents makes eleven or more model calls per decision and is compared with rule-based baselines, not with one call to the same model ([fair evaluation](docs/04-fair-evaluation.md)).
- **The source lists barely overlap.** Four popular lists link 584 repositories between them, and none appears in all four ([lists compared](docs/03-lists-compared.md)).

## Optional reading

For readers who want the reasoning behind the grades.

| Page | One line |
|---|---|
| [First principles](docs/00-first-principles.md) | Seven statements any trading system, LLM or not, has to satisfy. |
| [Domain map](docs/01-domain-map.md) | Eight layers of a trading system, and who does what. |
| [Evidence ladder](docs/02-evidence-ladder.md) | L0 to L4: how far someone else can inspect a claim. |
| [Lists compared](docs/03-lists-compared.md) | What four popular lists cover, and what they miss. |
| [Fair evaluation](docs/04-fair-evaluation.md) | Same data, same model, same budget, a single-call baseline. |
| [Claim audit](docs/05-claim-audit.md) | Where papers and repositories did not line up, with versions. |
| [Reading a backtest](docs/06-reading-a-backtest.md) | Error bars, record length, selection bias. |
| [Methodology](docs/07-methodology.md) | How the catalog was built and what a program checks. |
| [Deep dives](docs/teardowns/) | [TradingAgents](docs/teardowns/tradingagents.md) · [FinRobot](docs/teardowns/finrobot.md) · [FinMem](docs/teardowns/finmem.md) · [ContestTrade](docs/teardowns/contesttrade.md) · [FinRL-X](docs/teardowns/finrl-x.md) |
| [Papers](docs/catalog/papers.md) | 57 papers by layer, each with a one-line takeaway. |
| [Method cards](docs/cards/index.md) | Machine-extracted summaries of 49 papers; every field is backed by a quote that a program found in the paper. |

## Lab (experimental)

Tools for checking claims yourself. Python 3.11 or newer; everything except the card extraction uses only the standard library.

```bash
python -m tools.evalkit se --sr 5.6 --years 0.25            # standard error of a reported Sharpe
python -m tools.evalkit min-record --sr 1.0                 # years of record before a Sharpe separates from zero
python -m tools.evalkit diff-years --delta 0.5 --sr-low 0.5 --rho 0.9   # years to tell two agents apart
python -m tools.evalkit card-template                       # the report card an evaluation should publish
python tools/verify.py all                                  # re-resolve every arXiv id and repository (needs network)
```

- [`tools/evalkit`](tools/evalkit/): Sharpe error bars, minimum record length, deflated Sharpe, paired bootstrap, budget ledger.
- [`tools/extract`](tools/extract/): makes the method cards, one Claude API call per paper; a program drops any field whose quote is not in the paper.

## Contributing

Corrections and new projects are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). The shortest path is an issue with a link.

## License

MIT, see [LICENSE](LICENSE). Linked papers and repositories keep their own licenses.
