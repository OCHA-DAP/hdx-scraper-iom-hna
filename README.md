# Collector for IOM DTM Household Needs Assessment Datasets
[![Build Status](https://github.com/OCHA-DAP/hdx-scraper-iom-hna/actions/workflows/run-python-tests.yaml/badge.svg)](https://github.com/OCHA-DAP/hdx-scraper-iom-hna/actions/workflows/run-python-tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-scraper-iom-hna/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-scraper-iom-hna?branch=main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This script downloads IOM Displacement Tracking Matrix (DTM) Household Needs
Assessment (HNA) results from the
[DTM HNA API](https://dtm-apim-portal.iom.int/) and publishes one HDX dataset
per country (currently MOZ, NGA, SDN and SSD). Each dataset has one CSV
resource per assessment year, with indicators by admin 2 and population group,
plus a data dictionary from the API's catalog endpoint.

IOM's columns are kept unchanged. Standard `admin1_pcode`, `admin1_name`,
`admin2_pcode` and `admin2_name` columns are added from the current COD in the
[Global P-Codes dataset](https://data.humdata.org/dataset/global-pcodes), along
with `reference_period_start` and `reference_period_end` from the assessment
year. Country-specific p-code handling is set in
`src/hdx/scraper/iom_hna/config/project_configuration.yaml`.

The datasets are published to HDX stage until partner and HDX sign-off.

## Development

### Environment

Development is currently done using Python 3.13. The environment can be created with:

```shell
    uv sync
```

This creates a .venv folder with the versions specified in the project's uv.lock file.

### Installing and running

For the script to run, you will need to have a file called
.hdx_configuration.yaml in your home directory containing your HDX key, e.g.:

    hdx_key: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    hdx_read_only: false
    hdx_site: prod

 You will also need to supply the universal .useragents.yaml file in your home
 directory as specified in the parameter *user_agent_config_yaml* passed to
 facade in run.py. The collector reads the key
 **hdx-scraper-iom-hna** as specified in the parameter
 *user_agent_lookup*.

 Alternatively, you can set up environment variables: `USER_AGENT`, `HDX_KEY`,
`HDX_SITE`, `EXTRA_PARAMS`, `TEMP_DIR`, and `LOG_FILE_ONLY`.

The HNA API needs its own subscription key (the DTM displacement API key does not
work). Set it in the `DTM_HNA_KEY` environment variable or pass it with
`--dtm-hna-key`. It is stored in Bitwarden and as the `DTM_HNA_KEY` GitHub Actions
secret. The API returns 403 for the default `python-requests` user agent, so the
user agent must come from `.useragents.yaml` or `USER_AGENT`.

To run against HDX stage, execute:

```shell
    uv run python -m hdx.scraper.iom_hna --hdx-site stage
```

Add `--save` to save the API responses to `saved_data/` and `--use-saved` to
rerun from them.

### Pre-commit

pre-commit will be installed when syncing uv. It is run every time you make a git
commit if you call it like this:

```shell
    pre-commit install
```

With pre-commit, all code is formatted according to
[ruff](https://docs.astral.sh/ruff/) guidelines.

To check if your changes pass pre-commit without committing, run:

```shell
    pre-commit run --all-files
```

## Packages

[uv](https://github.com/astral-sh/uv) is used for package management.  If
you’ve introduced a new package to the source code (i.e. anywhere in `src/`),
please add it to the `project.dependencies` section of `pyproject.toml` with
any known version constraints.

To add packages required only for testing, add them to the
`[dependency-groups]`.

Any changes to the dependencies will be automatically reflected in
`uv.lock` with `pre-commit`, but you can re-generate the files without committing by
executing:

```shell
    uv lock --upgrade
```

## Project

[uv](https://github.com/astral-sh/uv) is used for project management. The project can be
built using:

```shell
    uv build
```

Linting and syntax checking can be run with:

```shell
    uv run ruff check
```

To run the tests and view coverage, execute:

```shell
    uv run pytest
```
