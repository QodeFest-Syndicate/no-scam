# Client SDK Development Guidelines

Treat an SDK as a versioned product interface, not generated HTTP plumbing. Generated types may begin the implementation, but release quality requires idiomatic naming, stable errors, lifecycle behavior, and compatibility tests.

## Versioning Strategy

Follow semantic versioning for the SDK surface:

- **Patch:** bug fixes with no documented behavior break.
- **Minor:** additive methods, optional parameters, fields, and capabilities.
- **Major:** removals, renames, required inputs, changed defaults, or error behavior.

Server evolution and SDK version are distinct. Publish a compatibility matrix showing SDK versions, supported API versions, language/runtime versions, and support dates. Deprecate with runtime/compile-time warnings where idiomatic, migration guidance, telemetry, and a removal release.

## Error Type Hierarchy

```text
SdkError
+-- ConfigurationError
+-- AuthenticationError
+-- ValidationError
+-- ApiError
    +-- AuthorizationError
    +-- NotFoundError
    +-- ConflictError
    +-- RateLimitError
    +-- ServerError
+-- TransportError
+-- TimeoutError
```

Preserve HTTP status, stable service code, safe message, correlation/request ID, retryability, retry-after, validation details, and original cause. Do not require callers to parse strings. Never put tokens or sensitive response bodies into errors.

## Retry and Backoff

Retry only when the operation is safe:

- Reads are usually retryable unless expensive or non-repeatable.
- Mutations require a stable idempotency key and server support.
- Retry connection resets, selected timeouts, 429, and transient 5xx according to contract.
- Do not retry validation, authentication, authorization, or deterministic conflicts automatically.

Use exponential backoff with full jitter, honor `Retry-After`, cap attempts and total elapsed time, and expose hooks/telemetry. Avoid nested retries across caller, SDK, proxy, and service without one budget.

## Authentication Token Lifecycle

Accept a token provider callback rather than a static token where possible. The provider owns refresh and secure storage; the SDK requests a token near each operation. Coalesce concurrent refreshes, handle clock skew, and retry once after a confirmed refresh only when safe. Never log tokens or place them in URLs.

Tenant-aware SDKs require explicit tenant configuration or an authorized per-call scope. Changing tenants should create a new client or clear all scoped caches; do not mutate shared global tenant state.

## Pagination Helpers

Expose both page-level and iterator abstractions:

```text
page = client.items.list(cursor, page_size)
for await item in client.items.iterate(page_size): ...
```

Preserve opaque cursors. Do not synthesize offsets from cursors. Iterator cancellation must stop network work. Define maximum pages/items, partial progress on error, prefetch policy, and rate-limit behavior. Keep original page metadata accessible.

## Timeouts and Cancellation

Configure a finite default and allow per-call override. Distinguish connect, request, and total operation timeout when the language supports it. Propagate cancellation/abort signals. A timed-out mutation may have committed; surface uncertainty and preserve its idempotency key for status lookup or retry.

## Request Construction

- Set a stable SDK user agent with version and runtime.
- Send tenant, correlation, idempotency, and API-version headers explicitly.
- Encode paths and query values correctly; never concatenate untrusted values.
- Omit undefined fields but preserve explicit null according to schema.
- Use deterministic serialization when request hashing or signing.
- Bound response size and streaming buffers.

## Documentation from Types

Generate reference pages from public types and doc comments, but hand-author task-oriented examples for authentication, tenant selection, pagination, retries, errors, cancellation, idempotent mutation, and cleanup. Compile examples in CI so they cannot drift.

Type documentation should state units, timezone, nullability, mutability, defaults, constraints, freshness, and sensitive-data handling. Avoid exposing internal transport models as public domain types.

## Release Pipeline

1. Validate the authoritative OpenAPI contract.
2. Generate or check types reproducibly.
3. Format, lint, compile, and run unit tests.
4. Run contract tests against supported server versions.
5. Test retries, cancellation, pagination, and error decoding.
6. Scan dependencies and generated artifacts.
7. Verify package contents and provenance.
8. Sign and publish through protected automation.
9. Test installation from the public registry.
10. Record compatibility and deprecation changes.

## Compatibility Tests

- Old SDK against new compatible server.
- New SDK against oldest supported server.
- Unknown additive response fields.
- Missing optional and nullable fields.
- Stable error decoding with unknown codes.
- Rate-limit and retry-after behavior.
- Expired token with concurrent requests.
- Tenant header isolation between clients.
- Pagination termination and cancellation.
- Idempotent mutation retry after ambiguous timeout.

## Quality Checklist

- Public API is idiomatic and minimal.
- Configuration validates endpoint, credentials, tenant, and timeout.
- Error types are structured and correlation-friendly.
- Retries have safety rules, jitter, attempt cap, and elapsed-time cap.
- Tokens refresh safely and never appear in logs.
- Pagination supports pages and lazy iteration.
- Cancellation releases network resources.
- Examples compile and exercise supported workflows.
- Generated output is reproducible and reviewed for breaking changes.
- Package publication is signed, traceable, and rollback-ready.