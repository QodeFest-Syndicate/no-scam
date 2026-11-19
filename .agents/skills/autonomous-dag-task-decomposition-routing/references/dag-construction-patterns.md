# DAG Construction Patterns

Every edge must name an artifact, decision, control, resource, or environment condition. Iteration is represented by a bounded graph revision—not a back edge.

## Linear Pipeline

```text
A Discover → B Design → C Build → D Verify → E Deliver
```

**Use case:** each result is wholly required by the next task and parallel work adds no value. **Scheduling:** latency equals the sum of durations; every node is critical. **Recovery:** retry only transient failures; resume from the last valid artifact. Split a node when a partial result can unlock independent work.

## Fan-Out / Fan-In

```text
             ┌→ B API ─────┐
A Contract ──┼→ C UI ──────┼→ E Integrate → F Verify
             └→ D Data ────┘
```

**Use case:** independent implementations share a stable predecessor contract. **Scheduling:** execute B/C/D concurrently; E waits for all non-cancelled required branches. Capacity must cover the fan-out without starving integration. **Recovery:** retry one failed branch; cancel descendants invalidated by a contract change; never leave a join waiting on a cancelled optional branch.

## Diamond Dependency

```text
      ┌→ B Policy ─┐
A ────┤             ├→ D Decision
      └→ C Evidence┘
```

**Use case:** a decision needs independent evidence or controls. **Scheduling:** B and C can run concurrently if they do not mutate shared state. **Recovery:** preserve the valid branch; rerun only the failed or invalidated branch; D records input versions.

## Conditional Branching

```text
A Assess → G Gate ──pass──→ B Standard rollout
                 └─risk───→ C Harden → D Approval → E Controlled rollout
```

**Use case:** evidence selects one mutually exclusive path. Model the gate output and branch predicate explicitly. **Scheduling:** do not speculatively mutate state on both branches; discovery work may be speculative when cheap and isolated. **Recovery:** re-evaluate the gate if its evidence expires; cancel obsolete descendants and update joins.

## Iterative Refinement

```text
Revision 1: A Draft → B Review → C Gate
Revision 2: A2 Amend(from C evidence) → B2 Recheck → D Approve
```

**Use case:** review or experiments can require revision. A DAG cannot contain `C → A`; create a new version with bounded attempt count and preserved evidence. **Scheduling:** reserve retry budget and define stop/escalation conditions. **Recovery:** state why prior evidence remains valid or is invalidated; never loop indefinitely.

## Hybrid Topology

```text
A Scope → B Contract → {C1,C2,C3} → D Integrate → {E Security,E Performance} → F Gate → G Deliver
```

**Use case:** real delivery combining serial decisions, parallel builds, and parallel assurance. **Scheduling:** compute the weighted critical path, cap work in progress, reserve review/integration capacity, and model mutable-resource locks. **Recovery:** contain failures to a branch, then replan downstream nodes whose inputs changed.

## Interface-First Split

```text
A Interface + fixtures → B Provider
                       → C Consumer
                       → D Contract tests
B + C + D → E Integration
```

Use when separate teams or agents can build against a stable contract. The predecessor must include schemas, semantics, errors, versioning, fixtures, and ownership. Contract ambiguity is a gate failure, not a parallelizable implementation detail.

## Construction Checklist

- One verifiable primary output per node.
- Stable ID, owner/capability, inputs, acceptance, budget, resources, risk, retries, and evidence.
- Typed edges with exact unlock conditions.
- Explicit roots, terminals, gates, integration, rollback, and delivery.
- No missing references, self-dependencies, cycles, isolated nodes, or joins blocked by optional work.
- Shared mutable resources partitioned, leased, locked, or serialized.
- Critical path and slack recalculated after material changes.
- Revision log records added, removed, split, merged, and invalidated nodes.
