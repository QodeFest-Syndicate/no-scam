# Entitlement Management Reference

## Entitlements versus feature flags

An entitlement is a commercial or contractual right: access, limit, region, retention, support level, or configuration. A feature flag controls release, experiment, or operational behavior. One feature may require both an entitlement and a rollout flag, but flags must not become the billing ledger.

| Concern | Entitlement | Feature flag |
|---|---|---|
| Source | Plan/contract/approved override | Release or experimentation system |
| Lifetime | Subscription/contract interval | Usually temporary |
| Audit need | Financial and access evidence | Engineering change evidence |
| Failure default | Contract-specific | Operational safety-specific |
| Tenant visibility | Often visible | Usually internal |

## Plan-based access

Map plan versions to stable entitlement keys. Example keys might represent `audit.export`, `retention.days`, or `api.calls.monthly`. UI labels can change without changing keys. A tenant’s effective plan includes base plan, contract amendments, trials, promotions, and approved overrides.

Plan-based policy is simple and explainable. It becomes brittle if every exception creates another plan. Keep overrides first-class with owner, reason, approval, effective interval, and expiry.

## Attribute-based access

Evaluate policy from tenant, user role, region, data classification, contract, resource, and action. Use when access cannot be represented by a plan alone. Keep attributes authoritative and bounded; do not trust a client-supplied tenant or plan.

Attribute-based systems are expressive but harder to explain, cache, test, and audit. Return a decision reason and policy version. Separate authorization attributes from commercial entitlement where possible.

## Effective entitlement resolution

A deterministic order might be:

1. Validate tenant and account state.
2. Resolve plan/contract version for current time.
3. Load base entitlements.
4. Apply approved tenant overrides.
5. Apply trial or grace policy.
6. Apply security/legal restrictions that cannot be overridden.
7. Combine with current usage/reservations for a quota decision.
8. Return decision, reason, source, version, and expiry.

Document merge semantics for booleans, numbers, sets, and regional constraints. “Most permissive wins” is unsafe as a universal rule.

## Caching and propagation

Cache immutable policy versions by tenant and include expiry. Invalidate on subscription, contract, override, trial, region, or security-policy change. Events should carry tenant, old/new version, effective time, event ID, and reason. Consumers deduplicate and reject stale versions.

For hard access decisions, use bounded-stale cache with authoritative fallback or short-lived signed snapshots. Define behavior when the policy service is unavailable. Monitor cache age and propagation lag by version.

## Grace periods

Grace periods can apply to payment failure, trial expiry, temporary overage, downgrade, or propagation delays. Define start event, duration, allowed capabilities, notifications, data behavior, and end action. Preserve administrative access and data export where policy requires.

Grace is policy—not an ad hoc support toggle. Record extensions and approvals. Never let indefinite retries silently create an unlimited grace period.

## Overage handling

- **Hard deny:** reject new consumption at limit.
- **Soft warning:** continue while notifying administrators.
- **Paid overage:** meter and rate above allowance.
- **Throttle:** reduce rate or concurrency.
- **Read-only:** preserve visibility while blocking mutation.
- **Reservation:** hold capacity before work and commit/release afterward.

Expose usage freshness, reset semantics, and provisional state. Match actual consistency/overshoot to product claims.

## Upgrade flow

1. Preview price, proration, feature, and quota changes.
2. Authorize payer and capture idempotency key.
3. Create/update provider subscription durably.
4. Resolve new entitlement version and effective time.
5. Propagate policy and verify critical features.
6. Notify tenant and retain audit evidence.

Upgrades are commonly immediate, but provider failure must not leave payment and entitlement permanently divergent. Use a resumable workflow and reconciliation.

## Downgrade flow

Before confirmation, show resources or usage that exceed the target plan. Define whether change is immediate or period-end and what happens to excess seats, data, keys, retention, regions, and scheduled jobs. Prefer preserving data with restricted mutation over destructive automatic deletion.

At effective time, version policy, notify consumers, verify state, and schedule any retention action with a recoverable grace period. Test downgrade/upgrade races and cancellation before effective time.

## Self-service controls

Administrators should see current plan/version, features, limits, usage, pending change, effective time, overage policy, invoices, and support path. Require appropriate role and step-up authentication for sensitive commercial changes. Confirm consequential changes and emit an audit event.

## Decision response schema

A useful response includes tenant/subject, feature or metric, allowed boolean, limit and remaining quantity where appropriate, reason code, policy version, source plan/override, effective/expiry times, reservation ID, and correlation ID. Do not expose confidential contract rates in a generic authorization response.

## Testing matrix

- New tenant and no policy.
- Every plan/version and feature combination.
- Tenant override precedence and expiry.
- Trial start, expiry, conversion, and extension.
- Payment grace and restoration.
- Exact limit, overage, reset, and late usage.
- Concurrent reservation oversubscription.
- Upgrade/downgrade with in-flight work.
- Cache staleness and out-of-order policy events.
- Region/security restriction precedence.
- Deleted/suspended tenant and data export.

## Observability and audit

Measure decision count/latency, allow/deny by bounded reason, cache hit/age, policy propagation lag, version mismatch, overrides nearing expiry, grace population, and reconciliation variance. Audit policy edits and consequential decisions with actor, reason, before/after, approval, and correlation—without logging secrets or unrelated personal data.

The entitlement service should answer not only “may this action proceed?” but also “which current, auditable policy produced that answer?”