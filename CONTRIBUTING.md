# Contributing

Two things help most: telling us about a project that belongs here, and correcting something we got wrong.

## Suggest a project or report an error

Open an issue on this repository with a link and one sentence. That is enough; we read the project, grade it and add it. For an error, add a source we can check (a commit, an arXiv version, a table number).

## Add a project yourself

1. Copy an existing `[[project]]` entry in `catalog/projects.toml` and fill in what you know: name, repository, license, last commit date, and a one-sentence summary that the project's own README supports. If you are unsure about the grades, leave `evidence = "L0"`, `repro = "unverified"` and `read = "readme"`; we will review them.
2. Add three short lines for the home page in `catalog/briefs.toml` (what it does, who it suits, its key limit), in English and Chinese. Keep them short and add no facts the project does not state.
3. Run `python tools/atlas.py tables` to regenerate the tables, and open a pull request. CI runs the remaining checks.

Do not edit `docs/catalog/` or `docs/cards/` by hand; they are generated.

## Writing a deep dive or an audit item

Name the paper version and the commit you read, separate what you quote from what you infer, and state findings neutrally. The existing [deep dives](docs/teardowns/) show the format. More detail on grades is in the [evidence ladder](docs/02-evidence-ladder.md) and the [methodology](docs/07-methodology.md).

## Never commit

API keys, tokens, credentials, personal paths or account identifiers, or text copied wholesale from a paper. `tools/privacy_lint.py` runs in CI as a backstop.
