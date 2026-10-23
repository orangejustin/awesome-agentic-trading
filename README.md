# Awesome Agentic Trading

Find a project for the part of the trading workflow you want to build. A small, curated guide to open-source agents and their tools.

中文：按用途选项目 → 看运行模式与限制 → 打开上游仓库。阅读和贡献都无需安装依赖。

## Choose in 60 seconds

| I want to… | Start with |
| --- | --- |
| Research a company and produce a report | [FinRobot](#finrobot) |
| Study how analysts, researchers and risk agents reach a decision | [TradingAgents](#tradingagents) |
| Try a simulated AI fund over market days or historical data | [AI Hedge Fund](#ai-hedge-fund) |
| Automate factor and model research | [RD-Agent](#rd-agent) |
| Give an existing assistant access to market data and order tools | [Alpaca MCP Server](#alpaca-mcp-server) |

**Checked: 2026-10-23 (UTC).** Capabilities below are documented upstream, not run-tested here. “Commit” is the latest default-branch commit observed, not a quality score or support guarantee. All listed repositories were unarchived when checked.

## Compare the projects

### FinRobot

[Open repository][finrobot] · For analysts building company research, valuation and report workflows.<br>
**Mode:** research/reporting · **License:** [Apache-2.0][finrobot-license] · **Commit:** [2026-09-28][finrobot-commit]<br>
**Main caveat:** choose the right codebase: desktop V2, web V1 or educational V0. `pip install finrobot` installs V0, not the desktop system. [Source][finrobot-source].

### TradingAgents

[Open repository][tradingagents] · For developers studying multi-agent analysis, bull/bear debate and risk-aware decisions.<br>
**Mode:** analysis/backtesting · **License:** [Apache-2.0][tradingagents-license] · **Commit:** [2026-10-16][tradingagents-commit]<br>
**Main caveat:** its reproducibility notes warn that news/social inputs can change even for historical dates; historical-input fidelity has not been audited here. Requires a configured model provider or local model. [Source][tradingagents-source].

### AI Hedge Fund

[Open repository][ai-hedge-fund] · For learners experimenting with investor agents through a simulated fund and historical replay.<br>
**Mode:** paper trading/backtesting · **License:** [MIT][ai-hedge-fund-license] · **Commit:** [2026-10-19][ai-hedge-fund-commit]<br>
**Main caveat:** requires Financial Datasets and model API keys. It is an educational simulation; the project explicitly says it does not make real trades. [Source][ai-hedge-fund-source].

### RD-Agent

[Open repository][rd-agent] · For quant developers automating factor proposals, code generation and factor/model experiments with Qlib.<br>
**Mode:** research/backtesting · **License:** [MIT][rd-agent-license] · **Commit:** [2026-09-23][rd-agent-commit]<br>
**Main caveat:** upstream supports Linux and requires Docker for most scenarios, plus chat and embedding model configuration. Setup is heavier than a single-agent demo. [Source][rd-agent-source].

### Alpaca MCP Server

[Open repository][alpaca-mcp] · For developers connecting an existing MCP-compatible assistant to Alpaca data, accounts and order operations.<br>
**Mode:** connector; paper/live capable · **License:** [MIT][alpaca-mcp-license] · **Commit:** [2026-10-12][alpaca-mcp-commit]<br>
**Main caveat:** supplies tools, not a trading strategy. Requires Alpaca credentials; live configuration can place real orders. Start with paper mode and review the enabled toolsets. [Source][alpaca-mcp-source].

## How to use this list

Pick by the output you need: a report, a decision, a simulated portfolio, research code or a broker connection. Model and data services may have separate costs and terms; an open-source license does not make those services free.

Inclusion means the repository has a distinct use, readable setup guidance and a verifiable license. It does not establish profitability or production readiness. Published backtests are authors’ results, not independently verified investment returns.

[Optional papers and deeper reading](READING.md) · [Suggest or fix an entry](CONTRIBUTING.md)

<details>
<summary>What was verified?</summary>

The repository, README, root license, archive flag and latest default-branch commit were checked through GitHub on the date above. Each entry links its README and license at that exact commit. Maintenance uses the commit's UTC committer date, not repository `updated_at`, `pushed_at` or stars.

No project was installed or executed. API availability, installation success, data completeness, paper/live execution and performance remain untested. FinRobot's cited commit edits documentation; a recent commit alone does not show current code health.

Descriptions are original summaries of the linked upstream sources. Each project retains its own license; this guide's [MIT license](LICENSE) covers only this guide.

</details>

[finrobot]: https://github.com/AI4Finance-Foundation/FinRobot
[finrobot-source]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/README.md
[finrobot-license]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/LICENSE
[finrobot-commit]: https://github.com/AI4Finance-Foundation/FinRobot/commit/2717499b8e30f242640af08c4ad9afd1113c2d45
[tradingagents]: https://github.com/TauricResearch/TradingAgents
[tradingagents-source]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/README.md
[tradingagents-license]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/LICENSE
[tradingagents-commit]: https://github.com/TauricResearch/TradingAgents/commit/e8f5503e9b86d5c2710b0c76b1f686703968c9df
[ai-hedge-fund]: https://github.com/virattt/ai-hedge-fund
[ai-hedge-fund-source]: https://github.com/virattt/ai-hedge-fund/blob/4e1657ddc689e3939c481a8f0955444b10f02dc9/README.md
[ai-hedge-fund-license]: https://github.com/virattt/ai-hedge-fund/blob/4e1657ddc689e3939c481a8f0955444b10f02dc9/LICENSE
[ai-hedge-fund-commit]: https://github.com/virattt/ai-hedge-fund/commit/4e1657ddc689e3939c481a8f0955444b10f02dc9
[rd-agent]: https://github.com/microsoft/RD-Agent
[rd-agent-source]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/README.md
[rd-agent-license]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/LICENSE
[rd-agent-commit]: https://github.com/microsoft/RD-Agent/commit/484776c211e4fbbeef03e0ec00d6bbee7362a4f4
[alpaca-mcp]: https://github.com/alpacahq/alpaca-mcp-server
[alpaca-mcp-source]: https://github.com/alpacahq/alpaca-mcp-server/blob/2a973a046607c42742bf141184b71f1990fa1809/README.md
[alpaca-mcp-license]: https://github.com/alpacahq/alpaca-mcp-server/blob/2a973a046607c42742bf141184b71f1990fa1809/LICENSE
[alpaca-mcp-commit]: https://github.com/alpacahq/alpaca-mcp-server/commit/2a973a046607c42742bf141184b71f1990fa1809
