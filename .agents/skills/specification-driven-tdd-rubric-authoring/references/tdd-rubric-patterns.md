# TDD Rubric Patterns

A rubric is an executable agreement: it names setup, stimulus, assertions, threshold, evidence, and the requirement being verified. Select the smallest test layer that can disprove the behavior.

## Given/When/Then Scenarios

**Use when:** behavior depends on actor, state, event, or permission and stakeholders need readable examples.

```gherkin
Scenario: AC-FR-014-02 duplicate request
  Given an authenticated tenant operator and a completed request with key K
  When the operator repeats the request with key K
  Then the API returns the original result within 500 ms
  And no second domain event is emitted
```

**Rubric fields:** scenario ID, actor, deterministic state, one trigger, observable result, side effects, forbidden effects, test layer, evidence path.

**Common pitfalls:** combining several actions in `When`; vague `Then`; omitting identity and tenant; asserting private methods; using examples without boundary or failure cases.

## Property-Based Specifications

**Use when:** an invariant must hold across a large input space, parsers have combinatorial inputs, or transformations should preserve properties.

```text
PROP-DATA-003
For every valid ledger with 1–10,000 entries and fixed seed recording,
serialize then deserialize preserves entry order, IDs, amounts, and currency;
invalid currency codes always return ERR-CURRENCY without partial persistence.
```

Define generators, validity constraints, input distribution, shrink strategy, seeds, maximum examples, timeout, and invariant. Keep a regression example for every discovered counterexample.

**Common pitfalls:** generators that rarely reach edges; discarding too many inputs; nondeterministic seeds; properties that merely restate the implementation; no shrinking budget.

## Contract Testing

**Use when:** independent components, services, events, or datasets evolve separately. Consumer-driven contracts suit known consumers; provider/spec-driven contracts suit public APIs.

```text
CONTRACT-API-007
Provider version v2 MUST accept v1 requests for the 90-day deprecation window.
Unknown optional response fields MUST be ignored by v1 consumers.
Provider CI verifies every active consumer contract before release.
```

Verify schema plus semantics: required/nullable/default behavior, authorization, errors, idempotency, ordering, units, compatibility, and deprecation. Publish contracts with version and producer commit.

**Common pitfalls:** schema-only checks; mocks diverging from provider; contracts tied to transient fields; stale consumer versions; treating provider success as end-to-end proof.

## Snapshot Testing

**Use when:** a structured, reviewable representation is the product contract—render trees, generated configuration, compiler output, or stable API examples.

A good rubric states normalization rules, volatile fields to redact, review owner, maximum snapshot size, and when updates are legitimate. Pair snapshots with semantic assertions for critical behavior.

```text
SNAP-UI-004: At 320, 768, and 1440 px, the normalized accessibility tree
matches the approved snapshot; focus order and accessible names are asserted separately.
```

**Common pitfalls:** enormous snapshots; blind update-all; timestamps and random IDs; snapshots replacing behavioral assertions; no reviewer explanation for changes.

## Chaos and Resilience Criteria

**Use when:** a system has redundancy, retry, failover, recovery, or defined availability behavior. Run only in authorized, bounded environments.

```text
CHAOS-RES-002
Given steady 100 requests/s and two healthy replicas,
when one replica is terminated for 5 minutes,
then p99 latency remains below 800 ms, errors remain below 0.5%,
and capacity returns within 2 minutes after replacement.
```

Specify steady-state hypothesis, blast radius, fault, duration, abort threshold, telemetry, recovery objective, cleanup, and approver. Prefer controlled dependency latency, process termination, resource pressure, and zone isolation over vague “break the system” exercises.

**Common pitfalls:** no baseline; no abort switch; testing production without approval; confusing injected errors with customer impact; no recovery assertion; missing evidence retention.

## Pattern Selection Matrix

| Need | Primary pattern | Complement |
|---|---|---|
| Stateful business rule | Given/When/Then | Boundary table |
| Broad data invariant | Property-based | Regression examples |
| Cross-team interface | Contract | Integration smoke test |
| Stable generated representation | Snapshot | Semantic assertions |
| Degraded/recovery behavior | Chaos | Deterministic fault-injection test |

## Minimum Rubric Gate

Every rubric entry must have a stable ID, linked requirement, layer, preconditions, controlled data, one stimulus, positive and negative assertions, exact pass threshold, reproducible command, and retained evidence. Statistical tests additionally require sample size, confidence/tolerance, and an allowed false-positive/negative policy.
