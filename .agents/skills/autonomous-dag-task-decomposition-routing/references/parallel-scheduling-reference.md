# Parallel Scheduling Reference

Maximize completed critical-path value, not worker utilization. A task is ready only when every required dependency has produced accepted evidence, policy gates pass, budget remains, and requested resources do not conflict.

## Dependency Analysis

1. Validate acyclicity and missing references.
2. Topologically sort and compute earliest start/finish from weighted durations.
3. Compute latest start/finish from the terminal deadline; zero-slack tasks form critical paths.
4. Group ready nodes into waves, then remove pairs with shared mutable resources or incompatible environments.
5. Add explicit join/reconciliation nodes; classify inputs as required, optional, quorum, or exclusive branch.

Edges should represent data, decision, control, resource, or environment constraints. Chronological preference alone is not an edge.

## Resource Constraint Modeling

For each task declare capability, agent attention, CPU/memory, API quota, environment, files/state touched, locks, cost, and concurrency class. Use renewable resources (workers, CPU) differently from consumable budgets (tokens, money) and unary mutable resources (state file, deployment target).

Safe options for shared state are partitioning, immutable outputs plus merge, lease/lock with fencing, or serialization. Optimistic concurrency needs version checks and a defined conflict resolver.

## Work-Stealing

Workers maintain local ready queues and steal from others when idle. Prefer stealing tasks with few locality constraints and enough estimated work to offset transfer cost. Never transfer credentials or ownership implicitly; revalidate capability, authorization, artifact access, and lease state.

Useful controls:

- preserve specialist and environment affinity;
- cap steals/reassignments to prevent thrashing;
- checkpoint before transfer;
- keep critical-path tasks visible to the global dispatcher;
- use idempotency keys for retried work.

## Priority-Based Dispatch

A practical score combines:

```text
priority = criticality + deadline urgency + downstream unlock value
           + risk reduction + ready age - resource scarcity cost
```

Hard policy gates override scores. Apply aging so low-priority work cannot starve. Reserve capacity for integration, review, incident response, and rollback; launching every build task can block the join that makes them useful.

## Dynamic Rebalancing

On early completion, pull forward compatible critical/low-slack work or use capacity for review—not unplanned scope. On late completion:

1. update remaining estimate and confidence;
2. recompute critical path and slack;
3. split transferable remainder if coordination cost is justified;
4. add capacity only where the task is parallelizable;
5. defer non-critical optional work;
6. escalate before hard budget/deadline breach.

Preserve valid completed evidence. Rebalance only from a consistent graph version and notify consumers whose input timing or version changed.

## Backpressure and WIP Limits

Limit active work at integration/review bottlenecks. Stop upstream dispatch when completed outputs queue faster than they can be verified or merged. Admission control should account for queue time, retry load, external quotas, and cleanup capacity.

## Failure and Retry Scheduling

Classify deterministic, transient, capacity, policy, and ambiguous failures. Retry only transient failures with bounded attempts, exponential backoff, jitter, and a total retry budget. Deterministic failures return to remediation; policy failures wait for explicit resolution; ambiguous outputs pause descendants.

## Scheduler Telemetry

Measure ready/running/blocked age, queue time, execution estimate error, critical-path drift, slack, resource saturation, lock wait, steals, retries, cancellations, join wait, budget burn, and deadline forecast. Replanning triggers should be numeric and declared before execution.

## Dispatch Checklist

- Accepted prerequisite artifacts and exact versions exist.
- Actor has required capability and least-privilege access.
- No conflicting resource lease or unsafe concurrent writer exists.
- Budget, timeout, retry, heartbeat, and evidence location are set.
- Cancellation and compensation behavior are known.
- Join and downstream consumers recognize branch status.
- Critical path and deadline forecast remain current.
