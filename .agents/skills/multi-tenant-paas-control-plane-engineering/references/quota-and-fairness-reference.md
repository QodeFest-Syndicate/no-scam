# Quota and Fairness Reference

Quotas protect platform safety and encode commercial entitlements. Fairness controls determine how scarce capacity is shared before hard limits are reached. Use both; a hard quota alone does not stop a tenant from monopolizing a shared dependency.

## Quota Hierarchy

```text
Platform/Region Capacity
  +-- Cell or Cluster Budget
      +-- Tenant Plan Allocation
          +-- Environment/Namespace Quota
              +-- Workload Requests and Limits
```

At every level, reserve headroom for system workloads, failover, upgrades, and measurement error. Child allocations must not exceed an enforceable parent budget.

## Hard Limits

Use hard limits for safety and contractual caps:

- CPU, memory, ephemeral and persistent storage.
- Pods, jobs, replicas, functions, and concurrent executions.
- Public endpoints, databases, topics, secrets, and certificates.
- API requests, build minutes, egress, connections, and event throughput.

Validate at admission when possible and at runtime when usage emerges later. Version plan defaults and audit overrides.

## Requests and Limits

Requests drive scheduling and reserved capacity; limits cap maximum use. Require defaults or reject unbounded workloads. Avoid extreme CPU overcommit for latency-sensitive tiers. Memory limits cause termination rather than graceful throttling, so pair them with realistic requests, application backpressure, and alerts.

## Burst Capacity

Bursting is a temporary loan, not a new entitlement. Define:

- Base allocation and maximum burst ceiling.
- Token refill rate or burst time window.
- Eligible resources and tenant tiers.
- Preemption/throttling behavior when capacity tightens.
- Billing, alerting, and customer-visible usage.
- Cooldown and repeated-burst policy.

Never sell the same guaranteed capacity to multiple tenants. Bursts consume explicitly uncommitted headroom.

## Priority Classes

Use few well-defined classes:

1. Platform-critical control-plane and recovery work.
2. Contractual interactive tenant workloads.
3. Standard tenant workloads.
4. Batch, replay, and best-effort work.

Restrict who can request high priority. Configure preemption deliberately, protect control-plane dependencies, and ensure low-priority work eventually progresses. Priority is not authorization to exceed tenant quota.

## Noisy-Neighbor Detection

Use multiple signals over windows rather than one threshold:

- Tenant share of CPU throttling, memory pressure, I/O wait, and network egress.
- API concurrency, queue depth/age, and request rejection rate.
- Database active sessions, lock time, query CPU, scanned bytes, and cache churn.
- Cache hit rate and eviction contribution by tenant.
- Per-tenant p95 latency versus platform saturation.
- Requested-to-used resource ratio and sustained burst duration.

A practical impact score:

\[
I_t = \sum_r w_r \times \max\left(0, \frac{u_{t,r}}{C_r} - s_{t,r}\right)
\]

where \(u_{t,r}\) is tenant usage of resource \(r\), \(C_r\) is usable shared capacity, \(s_{t,r}\) is the tenant's fair share, and \(w_r\) reflects current scarcity. Use this for investigation and controlled response, not opaque billing.

## Response Ladder

1. Notify and expose usage near soft thresholds.
2. Apply queueing or token-bucket rate limits.
3. Reduce burst allowance while preserving base entitlement.
4. Cap per-tenant concurrency and connection pools.
5. Shift best-effort work to another window or cell.
6. Recommend plan change or workload optimization.
7. Move sustained high-impact tenants to dedicated placement.

Emergency throttling must be auditable, time-bound, and reversible.

## Quota Reclamation Algorithms

### Lease-Based Allocation

Capacity allocations expire unless renewed. Useful for ephemeral environments and build workers. Persist owner, amount, expiry, and fencing token. Reclaim only after grace and liveness checks.

### Idle Reclamation

Recover soft allocation after usage remains below a threshold for a review window. Preserve contractual hard entitlement; reclaim only reserved burst or unused shared capacity. Use hysteresis to prevent oscillation.

### Proportional Fair Sharing

When demand exceeds capacity, allocate in proportion to plan weights while enforcing minimum guarantees and maximum caps. Recalculate on a bounded interval and smooth changes.

### Dominant Resource Fairness

Compare each tenant by its largest share of any constrained resource. Prefer allocations that equalize dominant shares, which helps when workloads consume different CPU/memory/storage mixes.

### Preemptible Pool

Offer discounted best-effort capacity that can be reclaimed. Workloads must checkpoint, tolerate termination, and have no hidden dependency on uninterrupted execution.

## Reclamation Safety

- Never reclaim stateful storage solely from low activity.
- Distinguish allocation from actual consumption.
- Protect in-flight operations with leases and fencing.
- Send warnings before non-emergency reclamation.
- Preserve audit, metering, and customer-visible reason codes.
- Test clock skew, controller restart, duplicate reclaim, and recovery.

## Capacity Accounting

Usable capacity equals physical capacity minus system reserve, failure-domain reserve, upgrade surge, and policy headroom. Track allocated, requested, limited, actual, and burst usage separately. Reconcile admission records against runtime and billing data.

## Validation Checklist

- No quota is negative or greater than enforceable parent capacity.
- Tier defaults match published SLA and entitlement contracts.
- System and failover reserves are excluded from sellable capacity.
- Every runtime dimension has an enforcement owner.
- Overrides carry reason, approver, expiry, and rollback.
- Throttling responses preserve platform and control-plane recovery.
- Tenant-level telemetry is cardinality-controlled and privacy-reviewed.
- Reclamation is idempotent, fenced, and tested under failure.