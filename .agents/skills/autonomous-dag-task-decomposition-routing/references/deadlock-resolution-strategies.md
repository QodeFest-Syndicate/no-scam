# Deadlock Resolution Strategies

A stalled workflow is not always a deadlock. Distinguish deadlock (no participant can progress), livelock (participants react but make no progress), starvation (one ready task never receives resources), and an ordinary blocked dependency with a bounded owner and deadline.

## Resource-Contention Deadlock

**Pattern:** task A holds state lock X while waiting for environment Y; task B holds Y while waiting for X.

**Detection:** build a wait-for graph of task → resource and resource → holder edges. A cycle is a deadlock candidate. Alert on lock age, no-progress heartbeat, and hold-while-wait behavior.

**Resolution:** choose a victim by lowest completed cost and impact; checkpoint safe work; release/revoke leases; roll back partial mutation; reacquire resources in canonical order; revalidate state before retry.

**Prevention:** global resource ordering, acquire-all-or-none, short leases with fencing tokens, bounded lock wait, no external calls while holding locks, idempotent retry.

## Circular Dependency Deadlock

**Pattern:** API implementation waits for client code while client waits for final API behavior; two reviews each require the other’s approval.

**Detection:** topological sort fails or task wait edges form a strongly connected component. Hidden decision and artifact dependencies often cause cycles not present in the declared graph.

**Resolution:** expose the hidden edge; extract a shared contract, decision, fixture, interface stub, or discovery task as a predecessor; version the graph; invalidate only dependent evidence.

**Prevention:** interface-first planning, typed edges with exact unlock artifacts, separate approval authority, graph validation on every revision.

## Priority Inversion

**Pattern:** high-priority production fix waits for a lock held by low-priority work, while medium-priority tasks consume the holder’s capacity.

**Detection:** compare task priority with resource holder and ready-queue scheduling; flag high-priority wait time exceeding SLA while the holder is runnable but unscheduled.

**Resolution:** temporarily inherit the highest waiter priority, reserve execution capacity for the holder, preempt safe medium work, or transfer/cancel the low-priority lease after checkpoint.

**Prevention:** priority inheritance/ceiling protocols, short critical sections, hotfix capacity reservation, priority-aware queues, preemption-safe checkpoints.

## Starvation

**Pattern:** a ready task is repeatedly bypassed by newer work, scarce specialists, quotas, or retry storms.

**Detection:** ready age rises while dispatch count remains zero; queue position does not improve; allocation falls below guaranteed share.

**Resolution:** age priority, reserve a resource share, cap retrying work, apply weighted fair scheduling, or temporarily serialize competing tasks.

**Prevention:** bounded waiting, admission control, per-tenant/project quotas, aging, work-in-progress limits, and retry budgets.

## Join Deadlock and Cancelled Branches

A fan-in waits forever when an optional, failed, or superseded branch remains a required predecessor. Recalculate join prerequisites after branch cancellation. Mark inputs as required, optional, quorum-based, or mutually exclusive; never infer completion from silence.

## Distributed Lease Failures

Expired workers may continue writing after reassignment. Use monotonic fencing tokens checked by the protected resource, idempotency keys, heartbeats, and compare-and-swap state. A lease timeout alone does not prove the old worker stopped.

## Resolution Algorithm

1. Freeze new mutations in the affected resource set.
2. Capture wait graph, holders, leases, heartbeats, budgets, and partial evidence.
3. Classify deadlock, livelock, starvation, or ordinary blocking.
4. Select the smallest safe victim or extract the missing predecessor.
5. Release/revoke with fencing; compensate incomplete side effects.
6. Version the DAG and update dependencies, ownership, and joins.
7. Recalculate critical path, budgets, and ready sets.
8. Resume from a consistent checkpoint; verify invariants and audit the event.

## Operational Signals

Track task state/age, last progress, blocked reason, awaited artifact/resource, holder, lease/fencing token, retry count, priority, budget consumed, cancellation state, and next escalation. Alerts should be actionable: name the cycle or starving task and the smallest decision needed.
