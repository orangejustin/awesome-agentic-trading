# First principles

Before comparing systems, strip the problem down to what has to be true for any trading system, with or without an LLM, to make money. Everything else in this atlas (the [map](01-domain-map.md), the [grades](02-evidence-ladder.md), the [evaluation design](04-fair-evaluation.md)) follows from the seven statements below.

## 1. A trade is a bet that a price will differ from what it is priced at

A price already contains what the market knows. Making money means holding a view that is *different from the price*, *right more often than chance*, and *large enough to survive costs*. So a trading system is useful only if it adds information, or acts on public information faster or more cheaply than others, and only until others do the same.

An LLM changes none of this. It is not a faster data feed and it has no private information. Whatever it adds has to come from how it **reads, combines or tests** public information.

## 2. The accounting identity

For any strategy, in any period:

> **net return = Σ (weight × asset return) − trading costs − model spend**

- **Weight** is the decision: how much of each asset to hold, decided with only the information available at the time.
- **Trading costs** are commissions, spread, market impact and borrow, charged on turnover. They do not shrink when a model gets smarter.
- **Model spend** is what the LLM calls cost, per decision. A debate of eleven calls is a real line in this equation, and it scales with the number of decisions.

Gross edge is competed away. Costs and spend are not. That is why a small, honest edge needs cheap, infrequent decisions, and why a system that produces a large *gross* number from many expensive calls deserves a second look at the net.

## 3. Where an LLM could plausibly help, and where it cannot

| Where | The claim | What would count as evidence |
|---|---|---|
| **Reading** | Turns filings, transcripts, news and tables into structured, checkable features faster than a person | Extracted fields match a hand-labelled sample; downstream signal improves out of sample |
| **Synthesis** | Combines many weak, heterogeneous signals into one rating with reasons | Beats a single-call baseline *at equal cost* on a held-out window |
| **Research automation** | Proposes, codes and tests hypotheses (factors, features) at a scale a person cannot | Held-out information coefficient after counting every trial |
| **Operations** | Calls tools, monitors, reconciles, reports | Fewer errors than the script it replaced |
| **Not an edge:** | Knowing the future, a faster feed, risk control by instruction | A model that "knows" an outcome has probably read it ([contamination](04-fair-evaluation.md#6-contamination-controls)) |

These are hypotheses, not findings. The [catalog](catalog/projects.md) shows how little independent evidence exists for any of them.

## 4. Time is the whole game

A decision may use only what was known when it was made. Three leaks break this, and each of them makes a strategy look better than it is:

- **Data leaks.** A restated fundamental overwrites the original; a news item carries its crawl time, not its publication time; the stock universe includes only the survivors.
- **Model leaks.** An LLM's weights are a data store with no timestamps. Ask it about a date inside its training data and it may simply remember. This looks exactly like skill.
- **Selection leaks.** The configuration was chosen after seeing the test window. Try three settings, report the best, and some of the "edge" is the best of three coin flips ([worked numbers](06-reading-a-backtest.md#2-selection-inflates-the-winner)).

The practical rule: freeze the data with a record of when each item became public, name the model snapshot, and decide the configuration before the test window opens.

## 5. You cannot see an edge in a short window

The Sharpe ratio is an estimate with an error bar of about 1 / √years. Three months of data leaves an error of about ±2; a good strategy with a true Sharpe of 1 needs close to three years of record before it separates from zero. Daily decisions across twenty stocks are not 5,000 independent bets a year, because stocks move together and an agent's decisions on adjacent days are correlated.

Two consequences. First, a headline number from a quarter or half-year says mostly what the market did in that window. Second, the useful unit of progress is not a better number but a **longer, settled record**: decisions timestamped before the outcome, scored later against a fixed rule. Details and tables: [reading a backtest](06-reading-a-backtest.md).

## 6. Compare at equal cost, against one call

If a system makes eleven model calls per decision and its baseline makes none, the comparison measures spend, not architecture. The control is simple: give the same model the same data in a **single call**, then ask whether each added piece of structure (debate, memory, tools, extra analysts) improves net results enough to pay for itself. Report results as a curve of performance against dollars per decision. This is the [same-budget protocol](04-fair-evaluation.md). In [TradingAgents](teardowns/tradingagents.md), the most copied design in the field, the paper has no single-call ablation with the same data pack and model.

## 7. Limits belong in code, not in prompts

A prompt is a request; a guard is a program. "Be risk-aware" does not cap a position. The systems we took apart show the difference: [FinRL-X](teardowns/finrl-x.md) drops orders above a value limit and scales down excess turnover in the executor, while in TradingAgents the risk debate is three prompts arguing about one proposal and the code enforces no exposure limit, volatility target or stop. If an agent can reach an order tool, the exposure cap, the loss limit and the kill switch must live in code the agent cannot edit.

## The loop that works: score decisions against what happened

Four of the five teardowns contain some form of the same mechanism, in different strengths: a [settled memory log](teardowns/tradingagents.md) that scores each decision after a holding window, [delayed realized scores](teardowns/contesttrade.md) that weight agents by results, [realized return fed into memory importance](teardowns/finmem.md), and a [hit-rate roll-up](teardowns/finrobot.md). It is the cheapest honest feedback loop in the field, and the same log is the raw material for a forward record.

## What follows: a minimal honest stack

1. **Freeze the data**, with publication timestamps and a record of what was fetched.
2. **Start with a single call** that returns a rating on a fixed scale, and a fixed table that turns ratings into weights.
3. **Log every decision**, with the model snapshot, the inputs and the cost, before the outcome is known.
4. **Settle the log** against a passive baseline after a fixed window.
5. **Add structure one piece at a time**, each behind an ablation and each charged to the budget.
6. **Put limits in code.**
7. **Report with an error bar**, and say how many things you tried.

The rest of the atlas is the evidence for why each step is there, and the tools to do it: [`tools/evalkit`](../tools/evalkit/) turns the rating, budget, statistics and report-card steps into tested code.
