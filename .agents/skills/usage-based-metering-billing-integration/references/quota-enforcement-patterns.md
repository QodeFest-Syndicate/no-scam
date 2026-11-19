# Quota Enforcement Patterns

## Decision dimensions

Choose per metric based on whether overspend is reversible, decision latency, concurrent writers, acceptable staleness, user experience, and cost of denial. Entitlement policy, current consumption, reservation state, and invoice state are separate concerns.

## Pattern matrix

| Pattern | Decision point | Latency impact | Accuracy | Consistency |
|---|---|---:|---|---|
| Synchronous pre-check | Before work | Network/cache lookup | High with authority | Strong or bounded-stale |
| Asynchronous post-check | After aggregation | None on request | Delayed overshoot | Eventual |
| Token bucket | Before request | In-memory/remote atomic op | Burst-aware | Per bucket authority |
| Leaky bucket | Admission queue | Queue delay | Smooth rate | Per queue authority |
| Sliding window counter | Before request | Multiple counters/query | Good rolling accuracy | Depends on atomic store |
| Reservation/commit/release | Before and after work | Two or three writes | Highest for costly units | Strong per subject |

## Synchronous pre-request check

The service requests an allow/deny/conditional decision before expensive work. Request fields include trusted tenant, metric/feature, quantity, idempotency key, and context. Response includes decision, reason, policy version, expiry, and reservation ID when relevant.

Use for hard contractual, security, resource, or spend limits. Set a strict timeout and explicit fail-open/fail-closed behavior. Cache versioned policy, but do not cache mutable consumption beyond tolerated overshoot. A quota-service outage must not become an undefined product state.

## Asynchronous post-aggregation check

Accept work, meter it, aggregate usage, then warn, throttle future work, or bill overage. This minimizes request latency and availability coupling but permits overshoot proportional to aggregation and propagation delay.

Use for soft limits, reversible work, and paid overage. Communicate provisional usage and forecast. Do not market a hard limit if enforcement is asynchronous.

## Token bucket

Tokens refill at a fixed rate up to capacity. Each action atomically consumes tokens. Capacity controls bursts; refill controls sustained rate. Define precision, clock source, idle behavior, and whether a request may consume multiple tokens.

Distributed implementation needs one authority per bucket or atomic scripts/transactions. Sharded local buckets increase availability but allow aggregate overshoot. Allocate sub-budgets explicitly if using local enforcement.

## Leaky bucket

Requests enter a bounded queue drained at a fixed rate. This smooths bursts rather than merely counting them. Define queue capacity, maximum wait, cancellation, fairness, and rejection behavior. Use for protecting a fixed-throughput downstream dependency. It may be unsuitable when delayed work is worse than immediate rejection.

## Sliding window counter

Estimate or count events during the previous duration. Exact logs are accurate but expensive; fixed-window combinations are cheaper but approximate boundaries. Atomic current/previous counters with weighted interpolation are common.

Test boundary bursts, clock skew, retry identity, and distributed concurrency. State whether the published limit is exact or an approximation.

## Reservation, commit, release

Reserve expected units atomically before work, commit actual usage on success, and release unused units on failure/timeout. Every transition is idempotent. Reservations have owner, quantity, expiry, state, and policy version.

Use for concurrent expensive jobs, seats, inventory-like units, prepaid credits, or spend caps. Reconcile expired and orphaned reservations. Commit may adjust quantity under a documented rule; never silently lose the difference.

## Distributed coordination options

| Approach | Availability | Overshoot risk | Operational cost |
|---|---|---|---|
| Single authoritative store | Lower across partitions | Lowest | Hot-key and regional latency |
| Regional authority by tenant | High | Low if routing stable | Rebalancing and failover |
| Escrow/sub-budget allocation | High | Bounded by allocation | Refill and stranded capacity |
| Local cache plus async sync | Highest | Potentially high | Reconciliation and customer ambiguity |

For global hard limits, choose consistency or explicitly bounded escrow. No design can guarantee zero overshoot while accepting writes independently through a partition.

## Webhook and event behavior

Emit warning, exceeded, recovered, reservation-expired, and policy-changed events with stable event IDs. Sign payloads, retry with bounded backoff, deduplicate at receivers, and preserve ordering metadata without promising ordered delivery. Webhook delivery must not be the authoritative enforcement mechanism.

## Failure policy

- **Fail closed:** appropriate when work creates unacceptable cost, data risk, or contractual breach. Provide retry guidance and support override.
- **Fail open:** appropriate when availability impact outweighs bounded overshoot. Record debt for later reconciliation.
- **Fail conditional:** permit a small emergency allowance, low-cost operation, read-only behavior, or cached decision.

Document policy by feature and dependency failure, not globally.

## User experience

Expose limit, usage, remaining allowance, reset time/timezone, freshness, and whether values are provisional. Notify at useful thresholds such as 50%, 80%, and 100%, tuned to consumption patterns. Give administrators spend controls and an upgrade path before denial. Avoid revealing negotiated rates to unauthorized users.

## Validation scenarios

- Exact threshold, one below, one above.
- Concurrent requests racing for final units.
- Duplicate reserve, commit, and release.
- Reservation expiration during work.
- Region partition and authority failover.
- Policy upgrade/downgrade with in-flight requests.
- Delayed usage and correction after reset.
- Zero/unlimited limit semantics.
- Clock skew and period boundary.
- Quota service timeout under fail-open/closed modes.

## Decision record template

Record subject, metric, limit/window, enforcement pattern, authority, consistency, maximum overshoot, cache TTL, failure mode, warning thresholds, reset semantics, reservation lifecycle, webhook behavior, observability, customer communication, and owner.

A quota implementation is correct only when its consistency guarantee and possible overshoot match what the customer was promised.