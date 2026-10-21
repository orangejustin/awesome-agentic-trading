# Methodology

How the catalog was built, what each label means, what is checked by a program and what by a person, and where the limits are. Snapshot date for everything: **2026-10-21 (US Pacific time)**.

## Scope and limits

- **Where the candidates come from.** Four public lists: [LLMQuant/awesome-trading-agents](https://github.com/LLMQuant/awesome-trading-agents), [Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers](https://github.com/Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers), [bettyguo/awesome-llm-trading-agents](https://github.com/bettyguo/awesome-llm-trading-agents) and [WallStreetPete/awesome-open-source-trading](https://github.com/WallStreetPete/awesome-open-source-trading), compared in [the list audit](03-lists-compared.md). We did not search outside them. Every catalogued paper and repository is linked by at least one of the four lists, or is the paper of a catalogued repository; `tools/list_audit.py --catalog` checks this.
- **Curated, not exhaustive.** The lists together link 584 repositories and 151 arXiv papers. The catalog holds 57 papers and 45 repositories (six of them lists). A field this size has more than a page of notable work, and a project missing here is not a verdict on it.
- **What we did not do.** We did not rerun any system, and we did not contact the authors. The [claim audit](05-claim-audit.md) is a reading of papers and code at named versions.
- **Authorship.** The text was drafted with an AI assistant and then checked against the sources, by script wherever a script could do it and by reading otherwise. The method cards below are machine-extracted and labelled as such.

## Inclusion rule

1. **Papers.** Every arXiv paper that two or more lists link is included. Of the catalogued papers, 13 meet this (the TradingAgents paper is in all four lists). A further 43 are linked by one list, and one is included because a catalogued repository names it as its paper.
2. **Repositories.** Every repository that two or more lists link is included unless it is general quant tooling or a general list, which are named with a reason in [`catalog/excluded.toml`](../catalog/excluded.toml) (twelve entries). Of the 39 catalogued non-list repositories, 32 are linked by two or more lists and 7 by one.
3. **Above the floor, judgment.** The 43 single-list papers and 7 single-list repositories were chosen to give each layer of the [domain map](01-domain-map.md) its best-known examples, with a bias toward evaluation work, because that layer is the point of this atlas. We did not score candidates with a formula, and a different curator would choose differently. The rules above are the part you can audit.
4. **Five deep dives.** [TradingAgents](teardowns/tradingagents.md), [FinRobot](teardowns/finrobot.md), [FinMem](teardowns/finmem.md) and [ContestTrade](teardowns/contesttrade.md) were chosen because they are widely cited and represent different decision designs (role-based firm, document-generation platform, layered-memory agent, tournament); [FinRL-X](teardowns/finrl-x.md) was added as the infrastructure counterpart, the one that owns the weights-to-orders back half the others lack.

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
| Schema and cross-references in the catalog | `python tools/atlas.py check` | every push |
| Generated tables and counts in the docs are current | `python tools/atlas.py tables --check` | every push |
| Statistics code against simulation | `python -m unittest discover -s tests -t .` | every push |
| arXiv titles and dates, repository reachability | `python tools/verify.py all` | on a schedule |
| Catalog against the inclusion rule | `python tools/list_audit.py --src DIR --catalog` | by hand (needs the four clones) |
| Method cards' quotes against the paper text | `python -m tools.extract verify` | by hand |

Numbers in the prose that come from the catalog (counts by rung, by layer) are generated into the documents between `<!-- atlas:... -->` markers and fail the check when stale. Numbers that come from papers are quoted with the table or section they come from.

## Method cards

[Method cards](cards/index.md) are the machine-assisted way to deepen coverage beyond the abstract. For a paper we have only read in abstract, [`tools/extract`](../tools/extract/) fetches the full text from arXiv and asks a language model (`claude-opus-5-5`, effort medium) to fill twelve fixed fields: task, architecture, data, window, models, baselines, headline result, costs, uncertainty, leakage controls, limitations and release.

Three design choices decide what a card is worth:

- **Quote-anchored.** Every field must carry a passage copied from the paper. A program then checks that the passage occurs in the fetched text, after normalising whitespace, quotation marks and hyphenation (a looser match that ignores punctuation is recorded as such). A field whose quote is not found is withheld from the card, however plausible its gloss.
- **Absence is not a finding.** "Not found" means the model did not find the item in the text it was given. The paper may state it in a figure or appendix that the text conversion dropped. A card never supports the sentence "the paper does not state X"; only a person reading the paper does.
- **The gloss is the model's.** A verified quote shows that the paper says something; it does not show that the one-line gloss is the right reading of it. Cards are therefore labelled as machine-extracted, and a card is a lead for a teardown, not a substitute for one.

The cards store short quotes, hashes of the source text and the token counts of the run; the source text itself is not stored or redistributed.

## Statistics

The numbers in [reading a backtest](06-reading-a-backtest.md) come from [`tools/evalkit`](../tools/evalkit/). The closed forms assume independent, roughly normal returns and are lower bounds on the data you need; the tests check them against simulation (standard-error formulas, the Sharpe-difference variance, the bootstrap) rather than against the formulas' own output.

## Dates and corrections

Everything is dated in US Pacific time. A repository snapshot names a commit; a paper names its version. If a later version or commit changes a finding in the [claim audit](05-claim-audit.md), the audit should change with a new date, not a silent edit. To report an error, open an issue with the page, the line and a source.
