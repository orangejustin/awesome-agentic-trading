# Awesome Agentic Trading

[English](README.md) · **简体中文**

按你想完成的交易工作，找到合适的开源项目。

## 60 秒选项目

- **公司研究与报告** → [FinRobot](#finrobot)
- **多智能体决策评估** → [TradingAgents](#tradingagents)
- **模拟组合与历史回测** → [AI Hedge Fund](#ai-hedge-fund)
- **量化研究自动化** → [RD-Agent](#rd-agent)
- **券商与行情工具** → [Alpaca MCP Server](#alpaca-mcp-server)

## 项目对比

核验日期：**2026-10-23**（UTC）。已核对上游文档与代码，未在此实际运行项目。

### [FinRobot][finrobot]

**模式：** 研究 / 报告 · **许可证：** [Apache-2.0][finrobot-license] · **最近提交：** [2026-09-28][finrobot-commit]

适合搭建公司研究、估值和报告流程的分析人员。

**选择前须知：** 先分清桌面版 V2、网页版 V1 和教学版 V0。`pip install finrobot` 安装的是 V0，并非桌面系统。[FinRobot 上游文档][finrobot-source]。

### [TradingAgents][tradingagents]

**模式：** 分析 / 决策评估 · **许可证：** [Apache-2.0][tradingagents-license] · **最近提交：** [2026-10-16][tradingagents-commit]

适合研究多智能体分析、多空辩论与风险决策流程的开发者。

**选择前须知：** 它评估决策，不模拟订单成交，也没有现金账本。即使指定历史日期，新闻与社交内容仍可能变化；此处未审计历史输入的真实性与时点一致性。运行需要配置模型服务或本地模型。[TradingAgents 上游文档][tradingagents-source] · [决策评估源码][tradingagents-evaluation]。

### [AI Hedge Fund][ai-hedge-fund]

**模式：** 模拟交易 / 回测 · **许可证：** [MIT][ai-hedge-fund-license] · **最近提交：** [2026-10-19][ai-hedge-fund-commit]

适合通过模拟基金和历史回放，学习与试验投资智能体的读者。

**选择前须知：** 需要 Financial Datasets 与模型服务的 API 密钥。这是教学模拟项目，上游明确说明不会执行真实交易。[AI Hedge Fund 上游文档][ai-hedge-fund-source]。

### [RD-Agent][rd-agent]

**模式：** 研究 / 回测 · **许可证：** [MIT][rd-agent-license] · **最近提交：** [2026-09-23][rd-agent-commit]

适合借助 Qlib 自动提出因子思路、生成代码并开展因子与模型实验的量化开发者。

**选择前须知：** 上游支持 Linux，多数场景需要 Docker，还需配置对话模型与嵌入模型。[RD-Agent 上游文档][rd-agent-source]。

### [Alpaca MCP Server][alpaca-mcp]

**模式：** 连接器 / 支持模拟与实盘 · **许可证：** [MIT][alpaca-mcp-license] · **最近提交：** [2026-10-12][alpaca-mcp-commit]

适合为现有的 MCP 兼容助手接入 Alpaca 行情、账户和订单操作的开发者。

**选择前须知：** 它提供工具，不提供交易策略。需要 Alpaca 凭证；实盘配置可以发送真实订单。先使用模拟模式，并检查启用的工具集。[Alpaca MCP Server 上游文档][alpaca-mcp-source]。

## 关于这份目录

入选项目需用途明确、安装说明可读，并有可核实的许可证。收录不代表盈利能力或生产可用性。模型与数据服务可能另有费用和使用条款；代码开源并不意味着这些服务免费。

<details>
<summary>来源、维护情况与核验边界</summary>

- 已在上述日期核对 README、根目录许可证、归档状态和默认分支的最近提交。所列仓库当时均未归档；文档与许可证链接固定到对应提交。
- “最近提交”指核验时观察到的默认分支提交，其日期采用 UTC 的 committer date。它只提供维护线索，不保证支持服务或代码质量。FinRobot 对应提交修改的是文档；不以仓库更新日期、推送日期或 stars 代替维护证据。
- 未安装或执行任何项目。安装成功率、模型与数据 API 可用性、数据完整性、历史输入一致性、模拟或实盘执行、性能均未测试。公开回测属于作者报告的结果，并非此处独立验证的投资收益。
- 项目介绍根据上游来源独立撰写。各项目保留自己的许可证；本目录的 [MIT 许可证](LICENSE) 仅适用于本目录。

</details>

## 参与维护与延伸阅读

通过[贡献指南（英文）](CONTRIBUTING.md)推荐项目或纠正条目。提供仓库链接、用途和一项限制即可提 issue。无需安装依赖或运行测试；中文、英文贡献均可。

[可选论文与延伸阅读（英文）](READING.md)介绍这些项目背后的设计。

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
