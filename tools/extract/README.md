# Method-card extraction

Turns the catalogued papers we have only read in abstract into **method cards**: twelve fixed fields (task, architecture, data, window, models, baselines, headline result, costs, uncertainty, leakage controls, limitations, release), each with a short gloss and a quote copied from the paper. A program then checks that every quote is a passage of the paper text; a field whose quote is not found is dropped from the card, whatever the gloss says.

What this does and does not guarantee is written down in [the methodology](../../docs/07-methodology.md#method-cards).

## Steps

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r tools/extract/requirements.txt

python -m tools.extract plan               # fetches the papers, estimates the bill; spends nothing
python -m tools.extract plan --exact       # exact input-token counts via count_tokens (needs the key; free of charge)
python -m tools.extract run --max-usd 20 --yes     # paid: model claude-opus-5-5, effort medium
python -m tools.extract verify             # re-check every stored quote against its source
python -m tools.extract render             # write docs/cards/*.md
python -m tools.extract promote            # catalog: read = abstract -> card where the card passed
python tools/atlas.py tables               # regenerate the catalog tables
```

`run` refuses to spend without `--yes` and stops starting new papers once `--max-usd` is reached. Rerunning skips papers that already have a card (`--redo` forces one).

## The API key

The key is never written to a file in this repository, printed, logged or stored in a card. Provide it one of two ways:

1. Set `ANTHROPIC_API_KEY` in the environment of the process that runs the command.
2. Copy `local.example.toml` to `tools/extract/local.toml` (git-ignored) and give it a `key_command` that prints the key, for example a lookup in your operating system's secret store. The command's output is read in memory only, and its error output is not shown.

Tests use a fake local server and a fake key (`python -m unittest tests.test_extract`).

## Request shape

One Messages API call per paper through the official `anthropic` SDK: `model="claude-opus-5-5"`, `output_config={"effort": "medium", "format": {json_schema}}`, thinking left at the model default (always on), no prefill, no sampling parameters. A `refusal` or `max_tokens` stop is reported and still counted in the ledger. The paper text is wrapped in `<paper>` tags and the system prompt tells the model to treat it as data.

## Files

| Path | In git | Content |
|---|---|---|
| `cards/ID.json` | yes | The card: fields, verification result, source hash, model, token counts, cost |
| `docs/cards/ID.md`, `docs/cards/index.md` | yes | Rendered cards (generated) |
| `data/extract/sources/` | no | Fetched paper text, kept so quotes can be re-checked; not redistributed |
| `data/extract/ledger.jsonl` | no | One line per call with tokens and cost |
