# Contributing

Corrections are the most useful contribution. In rough order of value: a link that moved or died, a finding that a later paper version or commit has fixed, a project we graded wrongly, a project that belongs in the catalog.

## Reporting an error

Open an issue with the page, the line, and a source we can check (an arXiv version, a commit hash, a table number). A claim without a source cannot be added to the [claim audit](docs/05-claim-audit.md); a claim with one will be, with a date.

## Adding or changing a catalog entry

The source of truth is `catalog/papers.toml` and `catalog/projects.toml`. Do not edit the files under `docs/catalog/` or `docs/cards/`; they are generated.

1. Add the entry. A paper needs its arXiv id, title, first author, the v1 and latest dates (arXiv UTC), one layer, a kind, a read depth and a one-sentence summary. A project needs the fields in the existing entries: repository, license, stars with the date they were read, last commit date and short hash, evidence rung, repro grade, read depth and summary. Use the [evidence ladder](docs/02-evidence-ladder.md) for the rung, and label a README skim as `readme`.
2. Say how you know. The summary must be something the source says. If you only read the abstract, set `read = "abstract"`; the page will label it so.
3. Regenerate and check:

```bash
python tools/atlas.py check
python tools/atlas.py tables
python tools/make_assets.py          # figures show counts from the catalog
python -m unittest discover -s tests -t .
python tools/verify.py all           # needs network: re-resolves every id and repository
```

A repository that two or more of the [source lists](docs/03-lists-compared.md) link has to be in `projects.toml` or, with a reason, in `catalog/excluded.toml`. See the [inclusion rule](docs/07-methodology.md#inclusion-rule).

## Writing a teardown or an audit item

- Name the version of the paper (arXiv v-number and date) and the commit of the repository you read.
- Separate what you quote, what you read in code and what you infer, as the existing teardowns do in their "what we checked" tables.
- State findings neutrally. A discrepancy is not an accusation, and many of these papers are candid about their limits.
- Do not rerun a system and report the result as an audit finding unless the run, its configuration and its cost are described well enough to repeat.

## Style

- Plain sentences, numbers with their units and their window, and a date for anything that changes.
- Code is standard library only unless a tool needs a dependency, in which case the dependency is declared next to that tool and imported lazily.
- Tests that check a formula should compare it to a simulation, not to the formula's own output.

## Never commit

API keys or tokens, credentials, personal paths, account identifiers, or text copied wholesale from a paper. `tools/privacy_lint.py` runs in CI and catches the common patterns; it is a backstop, not a substitute for looking.
