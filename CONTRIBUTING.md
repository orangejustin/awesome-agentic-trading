# Contributing

Thank you for helping. Three things help most: a project, paper or post that belongs here; a correction; and the removal of something stale. Contributions in English or Chinese are both welcome (欢迎用中文提交).

**The shortest path:** [open an issue](https://github.com/orangejustin/awesome-agentic-trading/issues/new/choose) with a link and one sentence on what it is for. Maintainers do the rest: verify, grade, translate and place it.

## Contents

- [What belongs here](#what-belongs-here)
- [Repositories](#repositories)
- [Papers](#papers)
- [Articles and posts](#articles-and-posts)
- [Corrections and removals](#corrections-and-removals)
- [Opening a pull request](#opening-a-pull-request)
- [Maintenance](#maintenance)
- [Never commit](#never-commit)

## What belongs here

In scope: open-source work where an LLM or agent researches, decides or trades, and the data, execution and harness infrastructure such systems are built on. Every entry has one primary layer:

| Layer | Belongs here when its main job is… |
|---|---|
| [1. Data](layers/data.md) | getting market, filing, news or social data to an agent, or turning text into signals |
| [2. Agent](layers/agent.md) | how a decision is made: models, memory, multi-agent designs, learned policies |
| [3. Execution](layers/execution.md) | turning a decision into orders: broker and venue tools, engines, weight-to-order pipelines |
| [4. Harness](layers/harness.md) | running, testing and trusting agents: backtests, simulators, benchmarks, bias control, loops, evals, traces, durable state |
| [5. Application](layers/application.md) | an end-to-end job for a user: research desks, funds, alpha factories, prediction-market bots |

Out of scope: general quant libraries with no agent interface (send them to [awesome-quant](https://github.com/wilsonfreitas/awesome-quant)), closed products without an open repository, signal or course selling, affiliate links. General-purpose agent tooling (evals, tracing, harnesses) is in only when it does a harness job a trading-agent builder needs; it is marked 🧰.

Stars, return claims and follower counts are never a reason to include something.

## Repositories

**Admission.** All of these, checked on a named date:

1. Public repository with **released code** (not only a README or a paper link). Announced-but-empty repositories go on the layer page's watchlist instead.
2. A README that says how to set it up.
3. A **root license file**, read as text, not inferred from a badge. A missing file is allowed but is shown as such.
4. A **distinct use**: not a near-duplicate of an entry already listed. Forks are listed only when the original is abandoned; otherwise the fork is named in the original's limit line.
5. One **concrete limit**: setup needs, data or API keys, simulation-only behaviour, order authority, an unusual license, unverified claims.

Disclose any affiliation with a project you suggest.

**Entry template.** Add a block to [`catalog/projects.toml`](catalog/projects.toml) and three short lines in both languages to [`catalog/briefs.toml`](catalog/briefs.toml). Layers and categories are listed in [`catalog/layers.toml`](catalog/layers.toml).

```toml
[[project]]
id = "short-id"
name = "Display name"
repo = "owner/name"
kind = "framework"            # framework | platform | library | model | tool | benchmark | simulator | backtester | data | execution | experiment
layer = "harness"             # data | agent | execution | harness | application
category = "harness-bench"    # one of that layer's categories
also = ["execution"]          # optional: other layers it ships working code for
orders = "paper"              # optional: live | paper | none, only if the README states it
general = true                # optional: general-purpose tool used for this job
license = "MIT"               # from the LICENSE file text; "" if there is none
last_commit = "2026-10-26"    # committer date of HEAD on the default branch
last_sha = "abcdef1"
checked = "2026-10-26"        # the day you checked the facts above
evidence = "n/a"              # see docs/02-evidence-ladder.md; leave "L0" if unsure
repro = "unverified"
read = "readme"
summary = "One or two sentences the README supports."
caveat = "The limit that would change a reader's decision."
```

```toml
[short-id]
tagline = "What it does, in under 20 words"
audience = "Who it suits"
limit = "Its key limit, in under 20 words"
tagline_zh = "…"
audience_zh = "…"
limit_zh = "…"
```

Write in your own words, keep lines short, and add no fact the project does not state. If you cannot write the Chinese lines, leave a note in the pull request and a maintainer will.

## Papers

A paper is in when it is about LLM or agentic trading, or is the paper of a listed repository. Link the arXiv abstract page (or the publisher's page), never a copied PDF. Record what you actually read: `full`, `partial`, `abstract`, or `card` (a machine-extracted [method card](docs/cards/index.md)). Collected is not read, and the label must say which.

```toml
[[paper]]
arxiv = "2412.20138"
title = "Exact title from arXiv"
first_author = "First Author"
n_authors = 7
published = "2024-12-28"      # arXiv v1 date
updated = "2025-06-03"        # latest version date
layer = "agent"
category = "agent-multi"
kind = "system"               # system | model | method | dataset | benchmark | study | survey | platform | library | infrastructure | simulator
read = "abstract"
summary = "One line: what it does and what it reports."
```

Papers marked `essential = true` appear on the home page and need a `summary_zh`. A new essential paper should say, in the pull request, why it matters: what changed after it.

## Articles and posts

Blog posts, documentation pages, podcasts and X (Twitter) posts are welcome when they carry an idea a builder can use. Add a block to [`catalog/articles.toml`](catalog/articles.toml):

```toml
[[article]]
title = "Title as published"
author = "Person or organisation (@handle for X)"
url = "https://…"             # the canonical public URL
source = "x"                  # x | blog | docs | news | newsletter | podcast | talk | paper | tool-page
date = "2026-10-25"           # publication date; for an undated page use the check date and add date_note
layer = "data"
why = "One sentence: what a builder takes from it, and its main caveat."
checked = "2026-10-26"
```

Not accepted: private workspace links (Slack, Notion, Feishu and the like), posts behind a login wall, posts whose substance is an unverifiable profit claim or a referral link, and copies of paywalled text. A post that only points to a repository is better submitted as the repository.

## Corrections and removals

Open an issue with the page, the line and a source we can check (a commit, a file, an arXiv version, a table number). Archived projects, repositories with no commits for over a year and broken links are flagged automatically (⚪ dormant) or by the weekly check; propose removal when a project's setup no longer works.

## Opening a pull request

1. Edit the TOML files in [`catalog/`](catalog/). Do not edit the READMEs' directory sections, [`layers/`](layers/) or [`docs/catalog/`](docs/catalog/) by hand; they are generated.
2. Run the checks (Python 3.11+, standard library only):

   ```bash
   python tools/build.py tables    # regenerate README.md, README.zh-CN.md, layers/ and docs/catalog/
   python tools/make_assets.py     # regenerate the figures (counts change)
   python -m unittest discover -s tests -t .
   ```

3. Fill in the pull request template. CI runs the same checks plus a privacy lint.

## Maintenance

- **Weekly:** `tools/verify.py` re-resolves every arXiv id and repository and reports moved or missing ones.
- **Each refresh:** update `last_commit`, `last_sha` and `checked` for the entries you re-checked. Status (🟢 🟡 ⚪) is computed from those dates, so it never needs editing by hand.
- **Neutral wording.** State what a source says and what you checked; separate quotation from inference; do not grade people.

## Never commit

API keys, tokens, credentials, personal paths, account identifiers, private chat or workspace links, real brokerage statements, or text copied wholesale from a paper. [`tools/privacy_lint.py`](tools/privacy_lint.py) runs in CI as a backstop.
