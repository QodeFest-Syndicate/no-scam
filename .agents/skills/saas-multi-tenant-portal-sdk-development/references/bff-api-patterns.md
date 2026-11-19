# Multi-Tenant Backend-for-Frontend API Patterns

A BFF adapts domain APIs to one experience. It owns transport, tenant/session enforcement, aggregation, and presentation shaping—not durable business rules or another copy of domain state.

## Authentication Forwarding

Prefer server-side sessions or token exchange over forwarding a browser token unchanged to every service.

```text
Browser --> BFF: session cookie + CSRF proof
BFF --> Identity: validate session / exchange token
BFF --> Service: short-lived audience-bound token + trace context
```

- Validate issuer, audience, signature, expiry, and session revocation.
- Forward only the identity claims each upstream requires.
- Never expose service credentials to the browser.
- Use secure, HTTP-only, same-site cookies where session cookies are appropriate.
- Apply CSRF defenses to state-changing cookie-authenticated requests.
- Redact authorization, cookies, and tokens from logs and traces.

## Tenant Context Injection

Derive effective tenant from verified membership or an authorized tenant-switch flow. A client-provided tenant header is a requested scope, not proof.

Canonical context should include tenant ID, user ID, environment/workspace, capabilities, entitlements, locale, region, correlation ID, and policy version. Sign or reconstruct context at each trust boundary. Reauthorize every operation.

On tenant switch, issue a newly scoped session/context, cancel old requests, re-key caches, reload permissions, and audit the switch. Never use one global server-state cache across tenants.

## Aggregation Strategies

### Parallel Read Aggregation

Call independent upstream reads concurrently with individual deadlines and a total request budget. Return a complete response only when every field is required. For optional panels, return explicit partial status and freshness metadata.

### Sequential Dependency

Use only when one response provides an identifier or authorization decision required by the next call. Propagate remaining deadline; do not reset a full timeout per hop.

### Materialized View

For expensive dashboards, build a tenant-scoped read model asynchronously. Include `asOf`, source freshness, and reconciliation status. Do not hide stale data.

### Streaming or Incremental Delivery

Use when early sections materially improve experience and the client can handle ordered partial errors. Keep authorization complete before streaming sensitive content.

## Failure Contract

Return stable machine codes plus safe messages:

```json
{
  "code": "UPSTREAM_TIMEOUT",
  "message": "Usage data is temporarily unavailable.",
  "correlationId": "req-123",
  "retryable": true,
  "details": []
}
```

Map validation to 400/422, unauthenticated to 401, denied scope to 403, absent resource to 404, conflict to 409, throttling to 429, and dependency failure to 502/503/504 as appropriate. Do not turn denied resources into empty success unless the contract explicitly prevents existence disclosure.

## Caching at the BFF Layer

Every authenticated cache key begins with effective tenant, environment, authorization scope/policy version, resource identity, query, locale, and representation version. Separate public and private cache namespaces.

| Data | Suggested policy |
|---|---|
| Permissions/entitlements | Short TTL; invalidate on policy change |
| Dashboard aggregates | Stale-while-revalidate with visible freshness |
| User preferences | Tenant + user key; write-through or explicit invalidation |
| Billing/subscription | Short TTL; webhook invalidation; never publicly cached |
| Static reference data | Longer TTL if not tenant-specific |

Prevent cache stampedes with request coalescing and bounded refresh concurrency. Never cache authorization failures across users without a correctly scoped key.

## Mutation Pattern

- Require idempotency keys for retryable mutations.
- Hash the normalized request and reject key reuse with different input.
- Forward the same idempotency key to capable upstream services.
- Return asynchronous operation resources for long-running workflows.
- Expose status, progress, timestamps, result link, and stable error code.
- Emit audit records after authorization and acceptance.

## Versioning

Prefer additive contract evolution. Version representation semantics, not every deployment. Use one of:

- URI major version for intentionally separate public contracts.
- Media-type or header negotiation when infrastructure supports it reliably.
- Operation-specific capability/version fields for gradual additions.

Maintain a compatibility window, deprecation headers, migration examples, usage telemetry, and a removal date. The BFF may shield the portal from upstream migrations, but the translation must have an owner and deletion criterion.

## Security and Reliability Checklist

- Tenant context comes from trusted identity and is checked on every upstream call.
- Upstream tokens are audience-bound, short-lived, and minimally scoped.
- Request, upstream, and total deadlines are nested.
- Retries are limited to safe/idempotent operations with jitter.
- Aggregation has explicit partial-failure semantics.
- Cache keys include tenant and authorization dimensions.
- Errors and telemetry contain correlation IDs but no secrets or sensitive payloads.
- BFF rate limits protect both tenant fairness and upstream capacity.
- OpenAPI contract documents headers, pagination, idempotency, errors, and freshness.
- Cross-tenant, expired-session, policy-change, and tenant-switch tests are automated.