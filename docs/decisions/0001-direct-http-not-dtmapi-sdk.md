# 0001: Direct HTTP rather than the dtmapi SDK

## Status

Accepted — 2026-11-02

## Context

IOM publishes the `dtmapi` Python package, which wraps the HNA API (`dtmapi.iom.int/HNA/v1`). The
API itself is plain REST with an `Ocp-Apim-Subscription-Key` header. `hdx-scraper-iom-dtm` calls the
DTM displacement API on the same host directly.

## Decision

Call the API with `hdx.utilities` `Download`/`Retrieve`, sending the key only on HNA requests.

## Consequences

- Tests replay saved responses with `Retrieve(use_saved=True)`. An SDK would need mocking instead.
- No `dtmapi` dependency, and the same pattern as `hdx-scraper-iom-dtm`.
- Response handling (the `result` envelope, `isSuccess`, paging on `hasNextPage`) lives in
  `pipeline.py`. If IOM changes the response shape, we update the pipeline ourselves rather than
  upgrading an SDK.
