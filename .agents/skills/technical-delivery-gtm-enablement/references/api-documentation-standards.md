# API Documentation Standards

## OpenAPI 3.1 contract

Use OpenAPI 3.1 as the source of truth when tooling supports it. Declare `openapi`, complete `info`, environment-safe `servers`, reusable tags, security schemes, and stable `operationId` values. Validate in CI and compare the contract with deployed behavior.

Every operation should define purpose, permissions, parameters, request body, success response, actionable errors, idempotency, limits, timeout/retry behavior, and side effects. Schemas need required fields, types, formats, enum, bounds, defaults, examples, and descriptions. Do not place real secrets, personal data, or production identifiers in examples.

## Information architecture

1. Overview and core concepts.
2. Authentication and authorization.
3. Five-minute quickstart.
4. Task-oriented guides.
5. Endpoint reference grouped by user domain/tag.
6. Webhooks and asynchronous operations.
7. Errors and troubleshooting.
8. Pagination, filtering, sorting, and expansion.
9. Limits, quotas, and rate limiting.
10. Versioning, deprecation, changelog, security, and support.

Reference states what exists; guides explain how to accomplish an outcome. Avoid organizing public docs by internal microservice layout.

## Authentication patterns

Document how credentials are created, displayed, scoped, stored, rotated, revoked, and separated by environment. State header or exchange format, token lifetime, required scopes per operation, and clock-skew rules. Include safe environment-variable examples—not hard-coded tokens.

Explain `401` versus `403`, tenant/account selection, service accounts, OAuth authorization flows, PKCE where applicable, and webhook signature verification. Never imply that an API key supplied in a query string is safe.

## Endpoint reference template

- Outcome and prerequisites.
- Method, path, lifecycle, and operation ID.
- Required scope/role and tenant context.
- Path/query/header fields with constraints.
- Request schema and sanitized example.
- Response schema, status, headers, and example.
- Side effects, idempotency, and async behavior.
- Error codes with customer actions.
- Rate/quota cost, timeout, and retry guidance.
- Related guide, SDK methods, and changelog.

## Code examples

Provide curl plus officially supported SDKs. All examples should be copyable, formatted, tested against a sandbox/mock, and pinned to supported API/SDK versions. Load credentials from environment variables. Show one primary success before advanced options.

For write operations, include idempotency key and cleanup. For pagination, process more than one page. For retries, use exponential backoff with jitter, honor server guidance, and retry only safe/idempotent operations. Show error parsing and correlation ID capture.

## Error catalog

Use a stable machine code separate from human message and HTTP status. A useful envelope contains `code`, `message`, `request_id` or correlation ID, field-level details, and documentation URL. Do not expose stack traces or internal identifiers.

For each error document HTTP status, stable code, trigger, customer action, retryability, and support evidence. Distinguish authentication, authorization, validation, conflict, idempotency mismatch, quota, rate limit, dependency, and internal errors.

## Pagination

State pagination model, stable ordering, default/max page size, cursor lifetime, mutation behavior, and end condition. Cursor pagination is generally safer for changing datasets. Clients must treat cursors as opaque. Document whether filters/order must remain unchanged between pages and how duplicates/missing items are prevented or tolerated.

For offset pagination, disclose consistency limitations and maximum offset. Examples must loop until completion rather than fetching only page one.

## Rate limits and quotas

Document subject (credential, tenant, endpoint, or resource), algorithm/window, limit, burst allowance, operation cost, response headers, `429` body, reset semantics, and increase path. Explain quota versus short-term rate limiting. If limits vary by plan, link to authoritative entitlement information.

Clients should avoid synchronized retries, honor `Retry-After`, and cap retry duration. Do not promise exact limits when enforcement is approximate.

## Webhooks

Document event types, schema/version, delivery attempts, signature creation/verification, timestamp tolerance, endpoint response timeout, retries, duplicate and ordering semantics, replay, test events, IP guidance, and secret rotation. Instruct consumers to verify the raw body, persist event ID, acknowledge after durable receipt, and process asynchronously.

## Asynchronous operations

For `202 Accepted`, document operation resource/location, state machine, polling cadence, terminal outcomes, cancellation, expiry, idempotency, webhook alternative, and result retrieval. Do not represent acceptance as completion.

## Versioning and deprecation

State compatibility policy, version selection, release cadence, preview labeling, deprecation notice period, sunset headers, migration guide, and changelog. Keep old-version docs discoverable with an unmistakable version banner. Breaking semantic changes need version treatment even when schema syntax is unchanged.

## Quality gates

- OpenAPI validates and lints.
- Examples use no secrets and execute in CI.
- Links, anchors, navigation, and search index pass.
- Documented responses match contract tests.
- Every operation has owner and lifecycle.
- Accessibility and responsive layout pass.
- Last-reviewed version/date is visible.
- Preview/deprecated content is labeled.
- Clean-room user completes quickstart.

## Review checklist

Ask whether a developer can discover the correct operation, understand permissions, make a safe request, interpret every response, retry correctly, stay within limits, debug with a correlation ID, and know where to get support. If any answer depends on tribal knowledge, the documentation is incomplete.