# 0002: One dataset per country, one resource per year

## Status

Accepted — 2026-11-02

## Context

The HNA API has one assessment round per country per year: 11 country-years across MOZ, NGA, SDN and
SSD as of 2026-11-02. All of them share the same 113 columns. The options were one global dataset,
one dataset per country, or one per country-year.

## Decision

Publish one dataset per country (`{iso3}-iom-dtm-household-needs-assessment`), with one CSV per
year (`{iso3}_iom_dtm_hna_{year}.csv`, newest first) followed by the data dictionary
(`iom_dtm_hna_data_dictionary.csv`, from the `catalog` endpoint).

## Consequences

- A new round becomes a new resource on an existing dataset, with no new dataset slug.
- Each run rebuilds every dataset in full (`remove_additional_resources=True`).
- Countries with no recent round (NGA, last round 2022) show as out of date on HDX. This is accepted.
