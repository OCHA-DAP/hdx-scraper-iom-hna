# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Publishes IOM DTM Household Needs Assessment (HNA) results (HDXPIPE-182) from the HNA API
(`https://dtmapi.iom.int/HNA/v1`, `Ocp-Apim-Subscription-Key` header from `DTM_HNA_KEY`). The HNA API
key is separate from the DTM displacement API key. The API returns 403 for the `python-requests`
user agent.

Output: one HDX dataset per country (`{iso3}-iom-dtm-household-needs-assessment`), with one CSV per
assessment year, newest first, then `iom_dtm_hna_data_dictionary.csv` from the `catalog` endpoint.
Published to HDX stage (repo variable `HDX_SITE=stage`, read by the run workflow) until partner and HDX sign-off.

## Commands

Environment setup (Python 3.13, managed with `uv`):

```shell
uv sync
```

Run the pipeline (requires `~/.hdx_configuration.yaml` with an HDX key, `~/.useragents.yaml`
with a `hdx-scraper-iom-hna` entry, and `DTM_HNA_KEY` — see README.md):

```shell
uv run python -m hdx.scraper.iom_hna --hdx-site stage
```

Run all tests (with coverage, configured in `pyproject.toml`):

```shell
uv run pytest
```

Lint and format:

```shell
uv run ruff check
uv run ruff format
```

Pre-commit (runs ruff on every commit once installed):

```shell
pre-commit install
pre-commit run --all-files
```

Build:

```shell
uv build
```

Adding a dependency: add it to `project.dependencies` in `pyproject.toml` (or `[dependency-groups]`
for test-only deps), then run `uv lock --upgrade` to refresh `uv.lock` (pre-commit also does this
automatically on commit).

## Architecture

- `__main__.py`: reads the key, sets up `Retrieve` and `HDXErrorHandler`, and loops over the
  countries from `country-list`. A failing country is logged and skipped, so it doesn't stop the run.
- `pipeline.py` (`Pipeline`):
  - `get_country_years`: `country-list` returns `{"result": [...]}` with `years` as a
    comma-separated string.
  - `get_admin2_data`: pages through `admin2` until `hasNextPage` is false. A response with
    `isSuccess` false logs an error and drops the whole year. No data comes back as `isSuccess`
    true with empty `data`.
  - `process_row`: keeps IOM's columns and inserts the standard admin and
    `reference_period_start`/`_end` columns after `m0304_meta_adm2_pcode`.
  - `get_standard_admins`: uses `complete_admins` against global p-codes. MOZ is matched on names
    only, and Abyei is left blank. See `docs/decisions/0003-standard-pcode-columns.md`.
  - `check_columns`: logs differences between the data columns and the catalog.
- `config/project_configuration.yaml`: URLs, tags, column names and country-specific p-code
  handling.
- `config/hdx_dataset_static.yaml`: licence (IOM `hdx-other`), org, maintainer, caveats and notes.
- Tests replay real responses saved in `tests/fixtures/input/`: MOZ 2022 (exactly 100 rows on one
  page), MOZ 2025, SSD 2025 (2 pages, with Abyei), NGA 2025 (no data) and XXX 2025 (an error
  body).

## Code Style

- Formatted with `ruff` via pre-commit hooks. After changing any Python code, run:

```bash
pre-commit run --all-files
```

- Python ≥ 3.13

## Collaboration Style

- Be objective, not agreeable. Act as a partner, not a sycophant. Push back when you disagree, flag
  tradeoffs honestly, and don't sugarcoat problems.
- Keep explanations brief and to the point.
- Don't rely on recalled knowledge for facts that could be stale (API behaviour, library versions,
  external systems). Search or read the actual source first. If you lack verified information, say
  so rather than speculate.

## Scope of Changes

When fixing a bug or addressing PR feedback, change only what is necessary to resolve the specific
issue. Do not refactor surrounding code, rename variables, adjust formatting, or make improvements
in the same commit unless they are directly required by the fix. Unrelated changes obscure the
intent of the fix and complicate review and blame.

## Decision Records

Non-trivial design decisions are recorded in `docs/decisions/` (see `docs/decisions/README.md`) —
the distilled decision, not the full planning narrative, belongs here.
