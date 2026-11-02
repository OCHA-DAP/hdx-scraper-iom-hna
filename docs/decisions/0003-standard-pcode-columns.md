# 0003: Add standard p-code columns matched to the current COD

## Status

Accepted — 2026-11-02

## Context

IOM's p-codes (checked 2026-11-02 against global p-codes):

| Country | IOM p-codes |
|---|---|
| SDN, SSD | Valid, apart from Abyei Administrative Area in SSD, which is blank |
| MOZ | From the pre-2025 COD. MZ01 is Cabo Delgado in IOM's data but Niassa in the current COD. 66 of 88 codes are valid but point to a different unit, and 22 don't exist. |
| NGA | `NGA002`-style rather than the COD's `NG002`, so all 62 are invalid |

`complete_admins` trusts a provider p-code whenever it exists in the COD, so MOZ's codes would pass
through unchanged.

## Decision

- Keep IOM's columns unchanged.
- Add `admin1_pcode` and `admin2_pcode`, filled by `complete_admins` against the global p-codes
  dataset. COD names are not added: on 2026-11-02 data they differ from IOM's names in only 2 cases
  (MOZ "Nacala" vs "Nacala Porto" and "Cidade De Xai-Xai" vs "Xai-Xai"), apart from case and
  accents. This matches `hdx-scraper-eve`.
- Countries in `ignore_provider_pcodes` (MOZ) are matched on admin names only.
- Rows whose admin 2 name is in `no_pcode_admin_names` (Abyei Administrative Area) are left blank,
  rather than given an SDN p-code. SD19 is in the SDN COD, and using it would take a side on Abyei's
  status.

## Consequences

- On 2026-11-02 data, every row except the 12 Abyei rows gets an admin 2 p-code. NGA's codes are
  converted by length, which logs a "PCode length" warning per code.
- If IOM updates MOZ to the current COD, MOZ can be removed from `ignore_provider_pcodes`.
- Names that fail to match log a "No admin 2 p-code" warning.
