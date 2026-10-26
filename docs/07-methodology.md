# Methodology

How the catalog was built, what each label means, what is checked by a program and what by a person, and where the limits are. The first snapshot is **2026-10-21 (US Pacific time)**; entries checked later carry their own `checked` date.

## Scope and limits

- **Where the candidates come from.** Two sources. (1) The first catalog, built for the *Agentic Trading Atlas* (merged into this repository), started from four public lists: [LLMQuant/awesome-trading-agents](https://github.com/LLMQuant/awesome-trading-agents), [Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers](https://github.com/Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers), [bettyguo/awesome-llm-trading-agents](https://github.com/bettyguo/awesome-llm-trading-agents) and [WallStreetPete/awesome-open-source-trading](https://github.com/WallStreetPete/awesome-open-source-trading), compared in [the list audit](03-lists-compared.md). Every entry checked on 2026-10-21 is linked by at least one of the four lists or is the paper of a catalogued repository; `tools/list_audit.py --catalog` checks the multi-list floor described below. (2) Since then, maintainers' source packs and contributions: entries added this way carry their own `checked` date (2026-10-26 onward) and are verified the same way, but are not tied to the four lists.
- **Curated, not exhaustive.** The four lists alone link 584 repositories and 151 arXiv papers. A field this size has more than a page of notable work, and a project missing here is not a verdict on it.
- **What we did not do.** We did not rerun any system, and we did not contact the authors. The [claim audit](05-claim-audit.md) is a reading of papers and code at named versions.
- **Authorship.** The text was drafted with an AI assistant and then checked against the sources, by script wherever a script could do it and by reading otherwise. The method cards are machine-extracted and labelled as such.

## Inclusion rule

1. **Papers.** Every arXiv paper that two or more of the four lists link is included (13 papers; the TradingAgents paper is in all four). Others are included because a catalogued repository names them as its paper, or by the judgment in point 3.
2. **Repositories.** Every repository that two or more of the four lists link is included unless it is general quant tooling or a general list, which are named with a reason in [`catalog/excluded.toml`](../catalog/excluded.toml).
3. **Above the floor, judgment.** Further entries were chosen to give each layer of the [stack](../layers/README.md) its best-known examples, with a bias toward evaluation and harness work, because trust is the point of this list. We did not score candidates with a formula, and a different curator would choose differently. The rules above, and the admission rules in [CONTRIBUTING](../CONTRIBUTING.md#repositories), are the part you can audit.
4. **General-purpose tools** (evals, tracing, agent harnesses, data validation) are included only for a job a trading-agent builder needs, and are marked 🧰.
5. **Five deep dives.** [TradingAgents](teardowns/tradingagents.md), [FinRobot](teardowns/finrobot.md), [FinMem](teardowns/finmem.md) and [ContestTrade](teardowns/contesttrade.md) were chosen because they are widely cited and represent different decision designs (role-based firm, document-generation platform, layered-memory agent, tournament); [FinRL-X](teardowns/finrl-x.md) was added as the infrastructure counterpart, the one that owns the weights-to-orders back half the others lack.

## What a catalog entry records

| Field | Where it comes from |
|---|---|
| Paper title, first author, v1 and latest dates | arXiv API, re-checked by `tools/verify.py papers` |
| Repository stars | The GitHub page, read by hand on the snapshot date |
| License, last commit date and hash | A shallow clone on the snapshot date; `tools/verify.py projects` reports when HEAD has moved |
| Layer | Working code for the job, not a README mention ([how we tag layers](01-domain-map.md#how-we-tag-layers)) |
| Evidence rung and repro | [The evidence ladder](02-evidence-ladder.md): the highest rung a third party can inspect for the headline claim |
| Read depth | What we actually read: `teardown` (paper in full plus code at a named commit), `readme` (the README skimmed, plus the license file and the commit log), `card` (a [method card](#method-cards)); for papers `full`, `partial`, `abstract` or `card` |

Stars and activity are context, not evidence. They are dated because they go stale in weeks.

## How a teardown was done

1. Read the paper in full, noting the version (arXiv v-number and date).
2. Clone the repository at a named commit; read the code that implements each claimed component; search the tree for the code that would produce each table (backtest, metrics, data loading).
3. For every number in the headline table, ask whether the repository can regenerate it, and write down what is missing.
4. Compare the paper's tables with each other and with its prose, and list internal inconsistencies with the table and section they sit in.
5. Record what to take from the design and how to test it fairly under the [same-budget protocol](04-fair-evaluation.md).

Each teardown carries a "what we checked" table so that a reader can see which statements are quotations, which are readings of code and which are inferences.

## What is checked by program

| Check | Command | Runs |
|---|---|---|
| Schema and cross-references in the catalog | `python tools/build.py check` | every push |
| Generated tables and counts in the docs are current | `python tools/build.py tables --check` | every push |
| Statistics code against simulation | `python -m unittest discover -s tests -t .` | every push |
| arXiv titles and dates, repository reachability | `python tools/verify.py all` | on a schedule |
| Catalog against the inclusion rule | `python tools/list_audit.py --src DIR --catalog` | by hand (needs the four clones) |
| Method cards' quotes against the paper text | `python -m tools.extract verify` | by hand |

Numbers in the prose that come from the catalog (counts by rung, by layer) are generated into the documents between `<!-- gen:... -->` markers (including the directory sections of both READMEs) and fail the check when stale. Numbers that come from papers are quoted with the table or section they come from.

## Method cards

[Method cards](cards/index.md) are the machine-assisted way to deepen coverage beyond the abstract. For a paper we have only read in abstract, [`tools/extract`](../tools/extract/) fetches the full text from arXiv and asks a language model (`claude-opus-5-5`, effort medium) to fill twelve fixed fields: task, architecture, data, window, models, baselines, headline result, costs, uncertainty, leakage controls, limitations and release.

Three design choices decide what a card is worth:

- **Quote-anchored.** Every field must carry a passage copied from the paper. A program then checks that the passage occurs in the fetched text, after normalising whitespace, quotation marks and hyphenation (a looser match that ignores punctuation is recorded as such). A field whose quote is not found is withheld from the card, however plausible its gloss.
- **Absence is not a finding.** "Not found" means the model did not find the item in the text it was given. The paper may state it in a figure or appendix that the text conversion dropped. A card never supports the sentence "the paper does not state X"; only a person reading the paper does.
- **The gloss is the model's.** A verified quote shows that the paper says something; it does not show that the one-line gloss is the right reading of it. Cards are therefore labelled as machine-extracted, and a card is a lead for a teardown, not a substitute for one.

The cards store short quotes, hashes of the source text and the token counts of the run; the source text itself is not stored or redistributed.

The first run (2026-10-23, PT) covered 49 papers in 49 calls: 1.63 million input and 77 thousand output tokens, $8.08. 46 cards passed and their papers moved from `abstract` to `card`; the three that did not are surveys, for which most of the twelve fields (window, baselines, headline result) do not apply.

## Home-page lines

The short lines in the README directory (what a project does, who it suits, its key limit, in English and Chinese) are in [`catalog/briefs.toml`](../catalog/briefs.toml). They were drafted by [`tools/extract/briefs.py`](../tools/extract/briefs.py), one Claude API call per project that sees only the catalog entry and is told to add no facts, and then reviewed by hand; twelve of the limit lines were rewritten. The maintenance label is computed from the last commit date.

## Statistics

The numbers in [reading a backtest](06-reading-a-backtest.md) come from [`tools/evalkit`](../tools/evalkit/). The closed forms assume independent, roughly normal returns and are lower bounds on the data you need; the tests check them against simulation (standard-error formulas, the Sharpe-difference variance, the bootstrap) rather than against the formulas' own output.

## Dates and corrections

Everything is dated in US Pacific time. A repository snapshot names a commit; a paper names its version. If a later version or commit changes a finding in the [claim audit](05-claim-audit.md), the audit should change with a new date, not a silent edit. To report an error, open an issue with the page, the line and a source.
