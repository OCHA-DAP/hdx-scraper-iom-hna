# 0004: Leave Mozambique's standard p-code columns blank

## Status

Accepted — 2026-11-13

Supersedes the MOZ part of 0003 (matching MOZ on admin names only).

## Context

IOM's reply on HDXPIPE-182 (12 Nov 2026):

> For MOZ, we checked our GIS reference and unfortunately the data in the current API can't be
> aligned with the current COD version in HDX due to versioning. Since the data was collected using
> the previous COD version, it shouldn't be aligned with the current one.
>
> On NGA, we are using the same version, except the the ISO format. We will align with ISO2 instead
> of ISO3

We compared each MOZ district in the HNA data (77 unique names across 2022, 2024 and 2025) with the
district of the same name in the current COD:

- Old boundaries are from the 2019 COD as republished by geoBoundaries (gbOpen MOZ ADM2, 159
  units). The 2019 files are no longer downloadable from `cod-ab-moz`.
- New boundaries are from the current `cod-ab-moz` shapefile (161 units).
- Overlap is intersection over union, in UTM 37S.

| Overlap | Districts |
|---|---|
| ≥ 0.95 | 55 |
| 0.90–0.95 | 5 |
| < 0.90 | 17 |
| No current COD unit with the same name | 2 (Ngauma; Nacala, which is "Nacala Porto" in the current COD) |

Examples of the largest changes: Cidade De Lichinga's current area is 12.9 times its 2019 area, Cidade De
Nampula 4.7, Ibo 2.4, Cidade De Xai-Xai 2.3 and Lago 1.8. Mecufi and Rapale are both about 0.67.

## Decision

- Countries in `no_pcode_countries` (MOZ) get blank `admin1_pcode` and `admin2_pcode` columns.
  Matching them to the current COD by name would attach rows to units with a different area.
- Their resources are set `p_coded: False`.
- IOM's original 2019 COD p-codes and names are kept unchanged, as for every country.
- NGA needs no change. When IOM switches to `NG002`-style codes, the length conversion becomes a
  no-op and its "PCode length" warnings stop.

## Consequences

- MOZ rows can't be joined to the current COD from this dataset.
- For each year of a `no_pcode_countries` country, `check_provider_pcodes` looks up IOM's admin 2
  p-codes in the current COD. If the COD name matches IOM's name for at least 90%
  (`current_cod_match_threshold`), it logs a warning to review `no_pcode_countries`. On the
  2026-11-13 MOZ data, 0 codes match (0 of 55 in 2022, 0 of 73 in 2024, 0 of 54 in 2025).
- If every year is republished against the current COD, MOZ can be removed from
  `no_pcode_countries`. If only some are, the list would need to become per year.
