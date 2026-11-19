# Control-Plane Operator Patterns

A Kubernetes operator is a level-triggered control loop: any event is a hint to compare desired and observed state. Correctness must not depend on receiving every event once or in order.

## Reconciliation Loop Design

1. Fetch the latest custom resource.
2. If absent, finish without error.
3. Validate generation-dependent invariants.
4. Handle deletion and finalizers before normal provisioning.
5. Fetch actual owned and external resources.
6. Compute the smallest convergent change.
7. Apply idempotently with field ownership and stable labels.
8. Update status from observation, not from intended writes.
9. Requeue only for a concrete watch, deadline, or transient recovery.

```text
Watch Hint --> Read Desired + Actual --> Plan --> Apply One Convergent Step
                    ^                                 |
                    +---------- Requeue/Watch --------+
```

Do not encode a one-pass create script inside reconciliation. The loop must recover from controller restart, duplicate events, partial writes, deleted children, and out-of-band drift.

## Error Classification

| Class | Behavior | Status |
|---|---|---|
| Invalid specification | Stop until generation changes | `Ready=False, Reason=InvalidSpec` |
| Policy denial | Stop; provide safe remediation | `Ready=False, Reason=PolicyDenied` |
| Conflict/optimistic lock | Refetch and retry quickly | Usually no user condition |
| Dependency throttle/outage | Exponential backoff with jitter | `Progressing=True` or degraded condition |
| Partial external creation | Discover by stable idempotency key | `Progressing=True` |
| Irrecoverable cleanup | Retain finalizer; alert/manual path | `Deleting=True, Reason=CleanupBlocked` |

## Status Subresource

Status should include:

- `observedGeneration` only after that generation has been evaluated.
- Stable conditions with `type`, `status`, `reason`, `message`, and `lastTransitionTime`.
- Provider/resource identifiers needed to observe, not credentials.
- Current phase for presentation only; automation should prefer conditions.
- Placement, endpoints, quota allocation, and operation progress where safe.

Use condition types such as `Ready`, `Progressing`, `Degraded`, and `Deleting`. Update transition time only when condition status changes. Keep messages actionable and free of secrets.

## Finalizers

Add a finalizer before creating external resources. On deletion:

1. Observe external resources by stable identity.
2. Revoke ingress and new workload access if policy requires fencing.
3. Trigger idempotent deletion or retention transfer.
4. Wait for required deletion evidence.
5. Record auditable completion.
6. Remove the finalizer only when contractual cleanup is complete.

Never use finalizers for resources Kubernetes already garbage-collects safely. Define escape procedures for unavailable providers, legal holds, and abandoned resources; silent finalizer removal can leak billable or sensitive assets.

## Leader Election

Use lease-based leader election when replicas share work and cannot reconcile the same key concurrently. Requirements:

- Unique identity per replica.
- Lease duration greater than renew deadline greater than retry period.
- Prompt cancellation of in-flight work when leadership is lost.
- Idempotency despite brief overlap during network partitions.
- Health endpoints that distinguish process health from leadership.

Prefer sharding or per-key serialization when one leader limits scale. Leader election does not replace optimistic concurrency on resources.

## Custom Resource Versioning

- Serve a stable storage version and declare conversion for served versions.
- Add fields with safe defaults and preserve unknown fields only deliberately.
- Treat field removal, enum narrowing, semantic default changes, and list-map changes as breaking.
- Use conversion webhooks for structural transformations, not external lookups.
- Test old object storage, upgrade, downgrade boundaries, backup restore, and mixed controller versions.
- Migrate stored versions before removing an old API version.

### Version Migration Sequence

1. Add new served version and conversion.
2. Deploy controllers that understand old and new shapes.
3. Make the new version the storage version.
4. Rewrite stored objects and verify status.
5. Stop serving the old version after clients migrate.
6. Remove conversion paths only after rollback expiry.

## Admission Webhooks

Use validating admission for invariants that must fail before persistence: immutable tenant identity, unsafe isolation combinations, quota ceilings, and forbidden references. Use mutating admission sparingly for stable, visible defaults.

Operational rules:

- Keep latency low and set explicit timeouts.
- Avoid dependency calls on the admission path.
- Define fail-open versus fail-closed from risk, not convenience.
- Scope rules narrowly by group, version, resource, operation, and namespace.
- Exclude the webhook's own recovery path where necessary.
- Version certificates and rehearse rotation.
- Return precise field errors and stable policy reasons.

## Ownership and Drift

Set owner references for namespaced children where lifecycle matches. Use labels for lookup and stable external IDs for cloud resources. Choose server-side apply field managers deliberately; do not fight other controllers for the same field. Surface unauthorized drift rather than blindly overwriting high-risk resources.

## Controller Security

- Scope RBAC to watched and reconciled resources.
- Separate read permissions from mutation permissions.
- Avoid wildcard verbs/resources and unnecessary secret reads.
- Use workload identity with short-lived credentials.
- Validate tenant scope before using custom-resource values in external calls.
- Strip secrets and sensitive provider responses from events and status.
- Audit manual overrides and controller impersonation.

## Testing Matrix

| Scenario | Expected evidence |
|---|---|
| Duplicate reconcile | No duplicate external resource |
| Restart after create | Resource discovered by stable identity |
| Child deleted | Recreated or accepted according to policy |
| Invalid generation | Stable condition; no hot loop |
| Provider timeout | Bounded backoff; no duplicate request |
| Delete during provisioning | Fenced, then cleaned in order |
| Lost leadership | Work canceled; successor converges |
| Old API object | Conversion and reconcile succeed |
| Webhook unavailable | Documented fail policy observed |
| Status conflict | Spec remains untouched; retry succeeds |

## Readiness Gate

Ship only when reconciliation is demonstrably idempotent, conditions are machine-usable, finalizers have an operational escape path, version migration is rehearsed, webhook failure behavior is tested, and operator RBAC has no unexplained wildcard.