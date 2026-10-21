<p align="center"><img src="assets/banner.svg" alt="Agentic Trading Atlas" width="100%"></p>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b></p>

**Agentic Trading Atlas（智能体交易图谱）**从第一性原理出发，梳理 LLM 与智能体交易：一个交易系统必须做对什么，已发表的系统在哪里做对、在哪里做错，以及怎样公平地比较它们。它不是又一份更长的链接清单。每篇论文、每个仓库都有评级、日期，并由脚本核对；五个系统被拆解到代码层面；声明与来源对不上的地方也一并公开。

<!-- atlas:headline-zh -->57 篇论文、39 个项目、5 个深度拆解<!-- /atlas:headline-zh -->，一套同预算公平评测设计，一套统计工具包。快照日期：2026-10-21（美国太平洋时间）。

> 仅供研究和教育。这里的内容不是投资建议，也不会下任何订单。
>
> 说明：深度文档（`docs/`）目前为英文；本页是导览。

## 三个问题

| 问题 | 在哪里回答 |
|---|---|
| **现在有什么，各自在做什么？** | [领域地图](docs/01-domain-map.md)：每个系统都要做的八件事，以及哪个项目做了哪几件。[目录](docs/catalog/projects.md)：每篇论文、每个项目都有证据评级。 |
| **它到底怎么运作，证据说明了什么？** | [五个深度拆解](docs/teardowns/)（架构、数据、决策回路、风控、评估、局限）、[声明审计](docs/05-claim-audit.md)、[怎么读回测](docs/06-reading-a-backtest.md)。 |
| **怎样公平地比较？** | [同预算评测](docs/04-fair-evaluation.md)：同样的数据、同样的模型、同样的成本、一个单次调用基线、一个误差范围。代码在 [`tools/evalkit`](tools/evalkit/)。 |

![交易系统的八个层](assets/layers.svg)

## 我们发现了什么

- **四份来源合集几乎不重叠。** 合起来共链接 584 个仓库、151 篇 arXiv 论文；没有任何仓库同时出现在四份里，只有一篇论文（TradingAgents）做到。读不同合集的人看到的是不同的领域。[详情](docs/03-lists-compared.md)。
- **没有任何一个头条结果被独立复现。** 目录里没有项目在其主要声明上达到[证据阶梯](docs/02-evidence-ladder.md)的第三级。我们读过的三个发表了交易结果表的智能体系统（TradingAgents、FinMem、ContestTrade），仓库里都缺少重现该表所需的代码或数据（[审计第 3、6、8 条](docs/05-claim-audit.md)）。
- **头条夏普比率来自几个月的数据。** 三个月的夏普比率标准误约为 2，六个月约为 1.4；真实夏普为 1 的策略，要接近三年的记录才能与零区分开。[数字在这里](docs/06-reading-a-backtest.md)。
- **有些结果一核对就变了。** 摘要与自己的表格矛盾；头条数字取自测试窗口上三种设置里最好的一个；换一个底座模型重跑，原文 61.8% 的结果只剩 19.9%。[声明审计](docs/05-claim-audit.md)，每一条都写明所读的版本和提交。
- **架构比较很少控制花费。** TradingAgents 每次决策调用模型十一次以上，对照的是规则型基线，而不是同一个模型的一次调用；在相同模型和价格下，这条流水线的成本约是单次调用的十四倍（示意性算术，见[第 3 节](docs/04-fair-evaluation.md#3-budget-tiers)）。同预算设计加上单次调用对照可以解决这个问题。
- **实盘记录稀少，而且让人清醒。** 目录里有前向记录的项目都是作者自己运行的，时间也短；其中一个项目公布了自己的结论：55 笔前向结算交易上没有测得优势。

## 阅读顺序

| | 页面 | 一句话 |
|---|---|---|
| 0 | [第一性原理](docs/00-first-principles.md) | 任何交易系统（不论是否用 LLM）都要满足的七条陈述。 |
| 1 | [领域地图](docs/01-domain-map.md) | 八个层，谁做了什么。 |
| 2 | [证据阶梯](docs/02-evidence-ladder.md) | L0 到 L4：别人能在多大程度上检验一个声明。 |
| 3 | [合集对比](docs/03-lists-compared.md) | 为什么第五份清单不是答案。 |
| 4 | [公平评测](docs/04-fair-evaluation.md) | 冻结的世界、相同预算、单次调用基线、报告卡。 |
| 5 | [声明审计](docs/05-claim-audit.md) | 哪些地方对不上，用中立的方式陈述。 |
| 6 | [怎么读回测](docs/06-reading-a-backtest.md) | 误差范围、记录长度、选择偏差。 |
| 7 | [方法说明](docs/07-methodology.md) | 目录怎么建的，哪些由程序检查。 |
| | [深度拆解](docs/teardowns/) | [TradingAgents](docs/teardowns/tradingagents.md) · [FinRobot](docs/teardowns/finrobot.md) · [FinMem](docs/teardowns/finmem.md) · [ContestTrade](docs/teardowns/contesttrade.md) · [FinRL-X](docs/teardowns/finrl-x.md) |
| | 目录 | [论文](docs/catalog/papers.md) · [项目](docs/catalog/projects.md) · [方法卡片](docs/cards/index.md) |

## 使用工具

需要 Python 3.11 及以上。除卡片抽取外，其余都只用标准库。

```bash
python -m unittest discover -s tests -t .       # 测试，包含用模拟检验统计公式的测试
python tools/atlas.py check                     # 校验目录
python tools/verify.py all                      # 重新核对每个 arXiv 编号和仓库（需要联网）

python -m tools.evalkit se --sr 5.6 --years 0.25            # 已发表夏普比率的标准误
python -m tools.evalkit min-record --sr 1.0                 # 夏普比率与零区分开所需的年数
python -m tools.evalkit diff-years --delta 0.5 --sr-low 0.5 --rho 0.9   # 区分两个智能体需要的年数
python -m tools.evalkit card-template                       # 每份评测都应公布的报告卡
```

方法卡片由 [`tools/extract`](tools/extract/) 生成：每篇论文调用一次 Claude API，只保留那些引文能被程序在论文原文里找到的字段。

## 仓库结构

```
catalog/    papers.toml、projects.toml、excluded.toml：唯一的数据来源
docs/       上面的各页；docs/catalog 和 docs/cards 由程序生成
cards/      机器抽取的方法卡片（JSON）
tools/      atlas.py（校验和渲染）、verify.py、list_audit.py、evalkit/、extract/
tests/      单元测试和文档链接检查
assets/     图，由 tools/make_assets.py 生成
```

## 贡献与勘误

最有用的贡献是勘误：失效的链接、后续版本已经修复的结论、我们评错级的项目。见 [CONTRIBUTING.md](CONTRIBUTING.md)。审计里的每一条都写明了所读的版本或提交，可以重新核对。

## 许可证

MIT，见 [LICENSE](LICENSE)。文中链接的论文和仓库保留各自的许可证；方法卡片只存短引文和哈希，不存论文原文。
