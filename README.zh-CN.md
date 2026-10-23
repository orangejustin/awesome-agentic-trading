<p align="center"><img src="assets/banner.svg" alt="Agentic Trading Atlas" width="100%"></p>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b></p>

**Agentic Trading Atlas（智能体交易图谱）** 是一份经过核对的 LLM 与智能体交易项目目录。下面每个项目都写明做什么、适合谁、是否还在维护、许可证和最关键的限制，一分钟内就能找到你要的项目。目录背后还有带评级的论文、五个系统的深度拆解，以及一套公平比较它们的设计。

<!-- atlas:headline-zh -->57 篇论文、39 个项目、5 个深度拆解<!-- /atlas:headline-zh -->。快照日期：2026-10-21（美国太平洋时间）。

> 仅供研究和教育。这里的内容不是投资建议，也不会下任何订单。
>
> 说明：深度文档（`docs/`）目前为英文。

## 按需求找项目

| 你想要 | 从这里开始 |
|---|---|
| 跑一个会辩论、给股票评级的多智能体“交易公司” | [TradingAgents](https://github.com/TauricResearch/TradingAgents)、[AI Hedge Fund](https://github.com/virattt/ai-hedge-fund)、[ContestTrade](https://github.com/FinStep-AI/ContestTrade) |
| 研究带记忆的单智能体 | [FinMem](https://github.com/pipiku915/FinMem-LLM-StockTrading) |
| 写股票研究报告，数字由代码算、不由 LLM 编 | [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) |
| 挖因子、自动化量化研究 | [Qlib](https://github.com/microsoft/qlib)、[RD-Agent](https://github.com/microsoft/RD-Agent)、[QuantaAlpha](https://github.com/QuantaAlpha/QuantaAlpha)、[AlphaGen](https://github.com/RL-MLDM/alphagen) |
| 用强化学习做组合，或把目标权重从回测送到券商 | [FinRL](https://github.com/AI4Finance-Foundation/FinRL)、[FinRL-X](https://github.com/AI4Finance-Foundation/FinRL-Trading) |
| 给智能体接行情数据 | [OpenBB](https://github.com/OpenBB-finance/OpenBB)、[Yahoo Finance MCP](https://github.com/Alex2Yang97/yahoo-finance-mcp)、[Massive MCP Server](https://github.com/massive-com/mcp_massive)、[Financial Datasets MCP Server](https://github.com/financial-datasets/mcp-server) |
| 用成熟引擎回测和实盘 | [LEAN](https://github.com/QuantConnect/Lean)、[NautilusTrader](https://github.com/nautechsystems/nautilus_trader) |
| 评测或压力测试交易智能体 | [DeepFund](https://github.com/HKUSTDial/DeepFund)、[Live Trade Bench](https://github.com/ulab-uiuc/live-trade-bench)、[AI-Trader](https://github.com/HKUDS/AI-Trader)、[TradeTrap](https://github.com/Yanlewen/TradeTrap)、[PIXIU / FinBen](https://github.com/The-FinAI/PIXIU) |
| 交易预测市场 | [Kalshi AI Trading Bot](https://github.com/ryanfrigo/kalshi-ai-trading-bot)、[Oracle3](https://github.com/YichengYang-Ethan/oracle3)、[polymarket-paper-trader](https://github.com/agent-next/polymarket-paper-trader) |
| 看真实的前向记录（无论好坏） | [Kalshi AI Trading Bot](https://github.com/ryanfrigo/kalshi-ai-trading-bot)（公布了自己“未测得优势”的结论）、[LLM Trading Lab](https://github.com/LuckyOne7777/LLM-Trading-Lab) |

能让智能体直接下单的工具（Alpaca MCP Server、Polymarket MCP Server、fintool 等）在下面的目录里；请先在模拟账户上用。

## 五个代表性系统对比

来自我们的[深度拆解](docs/teardowns/)，每个都读到了指定提交的代码层面。

| | [TradingAgents](docs/teardowns/tradingagents.md) | [FinMem](docs/teardowns/finmem.md) | [ContestTrade](docs/teardowns/contesttrade.md) | [FinRobot](docs/teardowns/finrobot.md) | [FinRL-X](docs/teardowns/finrl-x.md) |
|---|---|---|---|---|---|
| 形态 | 分析师、多空辩论、交易员、风控辩论、组合经理 | 单智能体、分层记忆、风险人设 | 多个智能体团队竞争，按预测夏普加权 | 研究工作台：代码算数，LLM 写字 | 从回测到券商的权重流水线 |
| 风控是否写在代码里 | 否：风控团队是三段提示词 | 否：风险只是人设提示词 | 部分：预测夏普不为正则权重为零；无敞口上限 | 不是交易系统 | 是：单笔金额上限和换手缩放 |
| 论文头条结果能否用仓库重现 | 否 | 否：没附市场数据 | 否：缺回测代码 | 无交易声明 | 我们未重跑 |
| 维护（2026-10-21） | 活跃 | 2024-08 起停更 | 放缓 | 活跃 | 活跃 |
| 适合 | 构建多智能体决策流程的开发者 | 研究智能体记忆的研究者 | 研究智能体竞争的研究者 | 需要可审计研究数字的开发者 | 把回测接到券商的开发者 |

## 全部项目

按每个项目首要承担的工作分组。“维护”按最后一次提交距快照日期的天数：90 天内为活跃，一年内为放缓，超过一年为停更。每行刻意写短；[完整目录](docs/catalog/projects.md)有星数、证据评级和更长的说明（英文）。

<!-- atlas:directory-zh -->
### 决策架构（多智能体、单智能体）

| 项目 | 做什么 | 适合谁 | 维护 | 许可证 | 关键限制 |
|---|---|---|---|---|---|
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) · [拆解](docs/teardowns/tradingagents.md) | 基于 LangGraph 的多智能体交易公司，输出五级评级 | 构建多智能体 LLM 交易决策流程的开发者 | 活跃 | Apache-2.0 | 仅评估决策质量，无组合模拟、Sharpe 代码及论文评测框架 |
| [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund) | LLM投资者智能体执行基金策略并回测历史 | 探索多智能体LLM投资决策的学习者 | 活跃 | MIT | 作者声明仅供教育用途，不下单交易，结果未经复现 |
| [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | 为AI agent提供交易能力的工具包，支持API与MCP | 构建交易决策与执行agent的开发者 | 活跃 | MIT | 给智能体下单通道，未核对表现声明 |
| [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) | 面向A股的TradingAgents社区衍生框架 | 构建A股多智能体交易工具的开发者 | 活跃 | Apache-2.0 core + proprietary app layer | 混合许可：应用层仅源码可见，并非开源 |
| [QuantAgent / QuantHarness](https://github.com/Y-Research-SBU/QuantAgent) | LangGraph多智能体短线技术分析系统 | 构建多智能体技术分析交易系统的开发者 | 活跃 | MIT | 论文回测未重跑，短周期结果需长记录验证 |
| [FinMem](https://github.com/pipiku915/FinMem-LLM-StockTrading) · [拆解](docs/teardowns/finmem.md) | 带风险画像与三层衰减记忆的单一交易智能体 | 研究LLM交易智能体记忆设计的研究者 | 停更 | MIT | 仓库不含市场数据，仅有占位文件和伪造样例压缩包 |
| [Agentic Trading Lab](https://github.com/Open-Finance-Lab/AgenticTrading) | 构建、回测与模拟交易LLM交易智能体的研究平台 | 构建并分析LLM交易智能体的研究者 | 活跃 | OpenMDW-1.0 | 采用不常见的OpenMDW-1.0许可证，复用前需阅读 |
| [ContestTrade](https://github.com/FinStep-AI/ContestTrade) · [拆解](docs/teardowns/contesttrade.md) | 多智能体竞赛框架，按预测Sharpe分配权重 | 研究竞争式多智能体交易决策的研究者 | 放缓 | Apache-2.0 | 仓库无回测代码，无法复现论文Table 1结果 |
| [Kalshi AI Trading Bot](https://github.com/ryanfrigo/kalshi-ai-trading-bot) | 带边际审计、MCP server 与代理工具的 Kalshi 交易工具包 | 为 Kalshi 预测市场构建或审计代理的开发者 | 活跃 | MIT | 其自身 55 笔前向交易的结论为无可测边际，账户含人工交易 |
| [Trading-R1](https://github.com/TauricResearch/Trading-R1) | 经SFT与RL训练、生成投资论点的推理模型 | 关注投资决策推理模型的研究者 | 停更 | 未找到 | 仓库仅有两行README，尚未发布模型或代码 |
| [Oracle3](https://github.com/YichengYang-Ethan/oracle3) | Kalshi与Polymarket预测市场代理工具包 | 构建预测市场交易代理的开发者 | 活跃 | Apache-2.0 | 只有声明，没有公开回测或记录 |
| [Kalshi Trading Bot CLI](https://github.com/OctagonAI/kalshi-trading-bot-cli) | 估算Kalshi市场概率并以分数Kelly定仓的CLI | 构建LLM预测市场交易工具的开发者 | 活跃 | MIT | 未公布业绩记录；概率估算可能依赖供应商研究API |
| [FinCon](https://github.com/The-FinAI/FinCon) | 带风控自我批评的经理-分析师智能体层级框架 | 研究层级多智能体交易决策的研究者 | 活跃 | MIT | 代码未发布，仓库仅含许可证和README |

### 感知（文本和数字变信号）

| 项目 | 做什么 | 适合谁 | 维护 | 许可证 | 关键限制 |
|---|---|---|---|---|---|
| [FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) | 开源金融LLM项目，含数据管道与LoRA微调方案 | 为金融NLP任务微调LLM的研究者 | 活跃 | MIT | 模型与数据项目，未核对交易表现 |
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) · [拆解](docs/teardowns/finrobot.md) | 代码算数、LLM写叙述的股票研究智能体平台 | 构建数字可审计的LLM研究工具的开发者 | 活跃 | Apache-2.0 | 属于股票研究工作站而非交易系统，无可检验的交易业绩声明 |
| [PIXIU / FinBen](https://github.com/The-FinAI/PIXIU) | 开源金融LLM FinMA及FinBen评测套件 | 评估LLM金融语言与推理能力的研究者 | 活跃 | MIT | 任务高分难以反映实际交易表现 |
| [Qwen DianJin](https://github.com/aliyun/qwen-dianjin) | 阿里云金融推理模型、数据与基准合集 | 评测或构建金融大模型的研究者 | 活跃 | MIT (sub-projects under Apache-2.0 in LICENSES/) | 属研究合集而非交易系统，各子项目文档与许可证独立 |

### 因子与研究自动化

| 项目 | 做什么 | 适合谁 | 维护 | 许可证 | 关键限制 |
|---|---|---|---|---|---|
| [RD-Agent](https://github.com/microsoft/RD-Agent) | 提出、实现并评估量化因子与模型的智能体循环 | 希望自动化因子与模型研究的研究者 | 活跃 | MIT | 未核对头条结果，因子收益需留出样本检验 |
| [QuantaAlpha](https://github.com/QuantaAlpha/QuantaAlpha) | LLM驱动的进化式因子挖掘框架 | 研究LLM自动挖掘alpha因子的研究者 | 放缓 | MIT (README badge) | 仓库无LICENSE文件，MIT仅见于README徽章 |
| [AlphaGen](https://github.com/RL-MLDM/alphagen) | 基于Qlib的强化学习公式化因子生成框架 | 挖掘公式化Alpha因子的量化研究者 | 放缓 | 未找到 | 仓库无LICENSE文件；核心为强化学习，LLM模块为后加 |

### 组合、风控与强化学习

| 项目 | 做什么 | 适合谁 | 维护 | 许可证 | 关键限制 |
|---|---|---|---|---|---|
| [FinRL](https://github.com/AI4Finance-Foundation/FinRL) | 面向股票交易环境的深度强化学习库与教程 | 将深度强化学习用于组合交易模拟的研究者 | 活跃 | MIT | 偏教学的 RL 环境，未核对其头条结果 |
| [FinRL-X (FinRL-Trading)](https://github.com/AI4Finance-Foundation/FinRL-Trading) · [拆解](docs/teardowns/finrl-x.md) | 以目标权重为核心的回测与券商下单管线 | 需要回测与下单统一接口的开发者 | 活跃 | Apache-2.0 | RL 配置仅略胜等权，无择时时均不及 QQQ |

### 数据与时点访问

| 项目 | 做什么 | 适合谁 | 维护 | 许可证 | 关键限制 |
|---|---|---|---|---|---|
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) | 面向Python与AI智能体的开放金融数据集成平台 | 需要市场数据的应用与智能体开发者 | 活跃 | Apache-2.0 | 只管取数，时点正确性需自己保证 |
| [Qlib](https://github.com/microsoft/qlib) | 含数据层、ML模型库与回测工具的量化研究平台 | 构建ML因子模型与回测流程的研究者 | 活跃 | MIT | 通用量化平台，LLM 智能体部分需自建 |
| [Financial Datasets MCP Server](https://github.com/financial-datasets/mcp-server) | 提供 Financial Datasets API 财务、价格与新闻的 MCP 服务器 | 为 LLM 智能体接入金融数据的开发者 | 停更 | MIT | 需要 Financial Datasets API 密钥；最后提交于 2025-06-05 |
| [Massive MCP Server](https://github.com/massive-com/mcp_massive) | Massive（原 Polygon.io）行情 API 的官方 MCP 服务器 | 将 LLM 智能体接入 Massive 数据的开发者 | 活跃 | MIT | 作者标注为实验性，且需要 API 密钥 |
| [Yahoo Finance MCP](https://github.com/Alex2Yang97/yahoo-finance-mcp) | 为LLM客户端提供Yahoo Finance数据的MCP服务器 | 为LLM客户端接入免费行情数据的开发者 | 活跃 | MIT | 基于yfinance当前数据而非时点存档，不适合回测 |

### 执行与基础设施

| 项目 | 做什么 | 适合谁 | 维护 | 许可证 | 关键限制 |
|---|---|---|---|---|---|
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) | 同一策略代码可用于回测与实盘的事件驱动引擎 | 需同时回测与实盘执行策略的开发者 | 活跃 | LGPL-3.0 | 通用引擎，非 LLM 专用，智能体接入需自建 |
| [LEAN](https://github.com/QuantConnect/Lean) | 用于研究、回测与实盘交易的事件驱动交易引擎 | 需回测并经券商实盘交易的策略开发者 | 活跃 | Apache-2.0 | 通用引擎，非 LLM 专用，智能体接入需自建 |
| [Alpaca MCP Server](https://github.com/alpacahq/alpaca-mcp-server) | 让LLM客户端查询行情并通过Alpaca下单的MCP服务器 | 将LLM智能体接入Alpaca账户的开发者 | 活跃 | MIT | 赋予智能体下单权限，应先在模拟账户上运行 |
| [Polymarket MCP Server](https://github.com/caiovicentino/polymarket-mcp-server) | 提供45个Polymarket交易与监控工具的MCP服务器 | 将LLM客户端接入Polymarket交易的开发者 | 活跃 | MIT | LLM客户端可动用真实资金下单，应先用模拟账户测试 |
| [fintool](https://github.com/second-state/fintool) | 为智能体提供分交易所交易与行情的 Rust CLI 套件 | 构建加密与预测市场交易智能体的开发者 | 放缓 | MIT | 可在真实交易所下单，建议先用小仓位或测试网 |

### 评测、基准与偏差控制

| 项目 | 做什么 | 适合谁 | 维护 | 许可证 | 关键限制 |
|---|---|---|---|---|---|
| [AI-Trader](https://github.com/HKUDS/AI-Trader) | 外部AI智能体注册交易的平台与实时排行榜 | 在实盘环境中评测AI交易智能体的研究者 | 放缓 | MIT (README badge) | 仓库根目录无LICENSE文件，仅README徽章标注MIT |
| [LLM Trading Lab](https://github.com/LuckyOne7777/LLM-Trading-Lab) | ChatGPT管理真实资金微盘股组合的六个月实盘记录 | 研究LLM实盘组合管理行为的研究者 | 放缓 | 未找到 | 仅六个月单次运行且由作者自评，不足以证明能力 |
| [DeepFund](https://github.com/HKUSTDial/DeepFund) | 在截止日后数据上评测LLM基金经理的实时竞技场 | 评估LLM交易智能体的研究者 | 放缓 | MIT | 竞技场结果取决于较短的实盘窗口 |
| [Live Trade Bench](https://github.com/ulab-uiuc/live-trade-bench) | 在美股与Polymarket上实盘运行并监控LLM交易智能体 | 实盘评估LLM交易智能体的研究者 | 放缓 | PolyForm Noncommercial 1.0.0 | 采用非商业许可，复用前需核查条款 |
| [TradeTrap](https://github.com/Yanlewen/TradeTrap) | 面向LLM交易智能体的故障注入测试工具 | 测试LLM交易智能体鲁棒性的研究者 | 放缓 | Apache-2.0 | 测的是鲁棒性，不是盈利能力 |

### 模拟

| 项目 | 做什么 | 适合谁 | 维护 | 许可证 | 关键限制 |
|---|---|---|---|---|---|
| [StockAgent](https://github.com/MingyuJ666/Stockagent) | LLM投资者在模拟股票交易所中交易 | 研究外部因素如何影响交易行为的研究者 | 放缓 | 未找到 | 仓库中没有LICENSE文件，使用条款不明确 |
| [polymarket-paper-trader](https://github.com/agent-next/polymarket-paper-trader) | 基于 Polymarket 实时订单簿的智能体模拟交易环境 | 构建和评测预测市场交易智能体的开发者 | 活跃 | MIT | 仅限预测市场而非股票，成交逼真度为作者自述 |
<!-- /atlas:directory-zh -->

## 我们发现了什么

- **没有任何一个头条结果被独立复现。** 我们读过的三个发表了交易结果表的智能体系统（TradingAgents、FinMem、ContestTrade），仓库里都缺少重现该表所需的代码或数据（[声明审计](docs/05-claim-audit.md)）。
- **头条夏普比率来自几个月的数据。** 三个月的数据会让夏普比率有约 ±2 的误差；真实夏普为 1 的策略，要接近三年的记录才能与零区分开（[怎么读回测](docs/06-reading-a-backtest.md)）。
- **架构比较很少控制花费。** TradingAgents 每次决策调用模型十一次以上，对照的是规则型基线，而不是同一个模型的一次调用（[公平评测](docs/04-fair-evaluation.md)）。
- **来源合集几乎不重叠。** 四份热门合集共链接 584 个仓库，没有一个同时出现在四份里（[合集对比](docs/03-lists-compared.md)）。

## 选读

想了解评级背后的理由，可以读这些（英文）。

| 页面 | 一句话 |
|---|---|
| [第一性原理](docs/00-first-principles.md) | 任何交易系统（不论是否用 LLM）都要满足的七条陈述。 |
| [领域地图](docs/01-domain-map.md) | 交易系统的八个层，谁做了什么。 |
| [证据阶梯](docs/02-evidence-ladder.md) | L0 到 L4：别人能在多大程度上检验一个声明。 |
| [合集对比](docs/03-lists-compared.md) | 四份热门合集覆盖了什么、漏了什么。 |
| [公平评测](docs/04-fair-evaluation.md) | 同样的数据、模型和预算，加一个单次调用基线。 |
| [声明审计](docs/05-claim-audit.md) | 论文和仓库对不上的地方，写明版本。 |
| [怎么读回测](docs/06-reading-a-backtest.md) | 误差范围、记录长度、选择偏差。 |
| [方法说明](docs/07-methodology.md) | 目录怎么建的，哪些由程序检查。 |
| [深度拆解](docs/teardowns/) | [TradingAgents](docs/teardowns/tradingagents.md) · [FinRobot](docs/teardowns/finrobot.md) · [FinMem](docs/teardowns/finmem.md) · [ContestTrade](docs/teardowns/contesttrade.md) · [FinRL-X](docs/teardowns/finrl-x.md) |
| [论文](docs/catalog/papers.md) | 57 篇论文按层分组，每篇一句话要点。 |
| [方法卡片](docs/cards/index.md) | 49 篇论文的机器抽取摘要；每个字段都有程序在原文里找到的引文作支撑。 |

## 实验区

自己核对声明用的工具。需要 Python 3.11 及以上；除卡片抽取外只用标准库。

```bash
python -m tools.evalkit se --sr 5.6 --years 0.25            # 已发表夏普比率的标准误
python -m tools.evalkit min-record --sr 1.0                 # 夏普比率与零区分开所需的年数
python -m tools.evalkit diff-years --delta 0.5 --sr-low 0.5 --rho 0.9   # 区分两个智能体需要的年数
python -m tools.evalkit card-template                       # 一份评测应公布的报告卡
python tools/verify.py all                                  # 重新核对每个 arXiv 编号和仓库（需要联网）
```

- [`tools/evalkit`](tools/evalkit/)：夏普误差范围、最短记录长度、紧缩夏普、配对自助法、预算账本。
- [`tools/extract`](tools/extract/)：生成方法卡片，每篇论文调用一次 Claude API；引文在原文里找不到的字段会被程序丢弃。

## 贡献

欢迎勘误和新项目，见 [CONTRIBUTING.md](CONTRIBUTING.md)。最简单的方式是开一个带链接的 issue。

## 许可证

MIT，见 [LICENSE](LICENSE)。文中链接的论文和仓库保留各自的许可证。
