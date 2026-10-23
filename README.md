# Awesome Agentic Trading

**English** · [简体中文](README.zh-CN.md)

Find the right open-source project for the trading workflow you want to build.

## Choose in 60 seconds

- **Company reports** → [FinRobot](#finrobot)
- **Multi-agent decisions** → [TradingAgents](#tradingagents)
- **Paper portfolios** → [AI Hedge Fund](#ai-hedge-fund)
- **Quant research automation** → [RD-Agent](#rd-agent)
- **Broker and market-data tools** → [Alpaca MCP Server](#alpaca-mcp-server)

## Compare the projects

Checked **2026-10-23 (UTC)** against upstream documentation and code. No project was run-tested here.

### [FinRobot][finrobot]

**Mode:** research / reporting · **License:** [Apache-2.0][finrobot-license] · **Last commit:** [2026-09-28][finrobot-commit]

For analysts building company research, valuation and report workflows.

**Before choosing:** select the right codebase: desktop V2, web V1 or educational V0. `pip install finrobot` installs V0, not the desktop system. [FinRobot documentation][finrobot-source].

### [TradingAgents][tradingagents]

**Mode:** analysis / decision evaluation · **License:** [Apache-2.0][tradingagents-license] · **Last commit:** [2026-10-16][tradingagents-commit]

For developers studying multi-agent analysis, bull/bear debate and risk-aware decisions.

**Before choosing:** evaluates decisions without order fills or a cash ledger. News/social inputs can change for historical dates; historical-input fidelity has not been audited here. Requires a model provider or local model. [TradingAgents documentation][tradingagents-source] · [Decision evaluation code][tradingagents-evaluation].

### [AI Hedge Fund][ai-hedge-fund]

**Mode:** paper trading / backtesting · **License:** [MIT][ai-hedge-fund-license] · **Last commit:** [2026-10-19][ai-hedge-fund-commit]

For learners experimenting with investor agents through a simulated fund and historical replay.

**Before choosing:** requires Financial Datasets and model API keys. It is an educational simulation; the project explicitly says it does not make real trades. [AI Hedge Fund documentation][ai-hedge-fund-source].

### [RD-Agent][rd-agent]

**Mode:** research / backtesting · **License:** [MIT][rd-agent-license] · **Last commit:** [2026-09-23][rd-agent-commit]

For quant developers automating factor proposals, code generation and factor/model experiments with Qlib.

**Before choosing:** upstream supports Linux and requires Docker for most scenarios, plus chat and embedding model configuration. [RD-Agent documentation][rd-agent-source].

### [Alpaca MCP Server][alpaca-mcp]

**Mode:** connector / paper and live capable · **License:** [MIT][alpaca-mcp-license] · **Last commit:** [2026-10-12][alpaca-mcp-commit]

For developers connecting an existing MCP-compatible assistant to Alpaca data, accounts and order operations.

**Before choosing:** supplies tools, not a trading strategy. Requires Alpaca credentials; live configuration can place real orders. Start with paper mode and review the enabled toolsets. [Alpaca MCP Server documentation][alpaca-mcp-source].

## About this list

Projects earn a place through a distinct use, readable setup guidance and a verifiable license. Inclusion does not establish profitability or production readiness. Model and data services may have separate costs and terms; an open-source license does not make them free.

<details>
<summary>Sources, maintenance and verification limits</summary>

- README, root license, archive status and the latest default-branch commit were checked on the date above. All listed repositories were unarchived. Documentation and license links are pinned to the cited commits.
- “Last commit” is the observed default-branch commit's UTC committer date. It is a maintenance signal, not a support guarantee or quality score. FinRobot's cited commit edits documentation. Repository update/push dates and stars are not used as substitutes.
- No project was installed or executed. Installation, model/data API availability, data completeness, historical-input fidelity, paper/live execution and performance remain untested. Published backtests are authors' results, not independently verified investment returns.
- Descriptions are original summaries of upstream sources. Projects retain their own licenses; this guide's [MIT license](LICENSE) covers only this guide.

</details>

## Contribute or read more

[Suggest a project or correct an entry](CONTRIBUTING.md). A repository URL, use case and limitation are enough to open an issue. No installation or test command is required; contributions in either language are welcome.

[Optional papers and deeper reading](READING.md) explain the designs behind the projects.

[finrobot]: https://github.com/AI4Finance-Foundation/FinRobot
[finrobot-source]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/README.md
[finrobot-license]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/LICENSE
[finrobot-commit]: https://github.com/AI4Finance-Foundation/FinRobot/commit/2717499b8e30f242640af08c4ad9afd1113c2d45
[tradingagents]: https://github.com/TauricResearch/TradingAgents
[tradingagents-source]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/README.md
[tradingagents-evaluation]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/backtest.py
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
