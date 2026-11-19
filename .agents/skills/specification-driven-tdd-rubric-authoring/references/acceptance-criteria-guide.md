# Guide to Testable Acceptance Criteria

Acceptance criteria define externally observable pass/fail behavior. They do not prescribe private implementation unless a mandated technology or control is itself a requirement.

## INVEST User Stories

A story should be **Independent**, **Negotiable**, **Valuable**, **Estimable**, **Small**, and **Testable**. Dependencies must be explicit rather than hidden; “negotiable” means the implementation is open, not that acceptance is subjective. Split stories when actors, outcomes, risks, or release paths differ.

A useful frame is: “As a [specific actor], I need [capability], so that [measurable outcome].” Follow it with criteria that cover state, trigger, result, errors, boundaries, and recovery.

## Quantitative and Qualitative Criteria

Convert qualities into operational measures:

| Vague quality | Testable dimensions |
|---|---|
| Fast | percentile, duration, workload, region, sample window |
| Available | success ratio, exclusions, measurement window, error budget |
| Secure | actor, resource, allowed/denied action, threat and control |
| Accessible | WCAG version/level, assistive technology, target workflow |
| User-friendly | completion rate/time, error rate, task and participant cohort |

Example: replace “search is fast” with “At 200 requests/s against 10 million indexed records, p95 server latency is at most 250 ms and p99 at most 600 ms over 30 minutes.”

## Given/When/Then Construction

- **Given:** specific actor, permissions, data, dependency, clock, and starting state.
- **When:** one action or event.
- **Then:** observable output and exact threshold.
- **And:** state change, event, audit record, telemetry, or forbidden side effect.

Keep scenarios atomic. Name the environment when results depend on infrastructure.

## Boundary Value Analysis

For ordered domains, test just below, at, and just above each boundary. For a quantity allowed from 1 through 100, candidates include 0, 1, 2, 99, 100, 101, empty, null, wrong type, and maximum representation. Include time-zone boundaries, daylight-saving transitions, leap days, precision/rounding, payload size, and concurrency limits when relevant.

Do not mechanically test every number. Select values that can change control flow or violate a domain invariant.

## Equivalence Partitioning

Partition inputs whose members should behave alike, then choose a representative from each partition:

- authenticated/authorized, authenticated/forbidden, unauthenticated;
- valid, syntactically invalid, semantically invalid, unsupported version;
- new, duplicate, stale, out-of-order, concurrent;
- dependency healthy, slow, unavailable, contradictory;
- tenant-owned, other-tenant, unscoped.

Record why the representative covers the partition and add boundaries where adjacent partitions meet.

## State-Transition Criteria

Model legal states and events before writing scenarios.

| Current state | Event | Guard | Next state | Observable side effects |
|---|---|---|---|---|
| Pending | approve | approver has scope | Approved | audit event emitted once |
| Pending | cancel | requester owns item | Cancelled | work revoked |
| Approved | approve | any | Approved | no duplicate event |

Test every legal transition, prohibited transition, idempotent repeat, race, and recovery after interruption. Define whether concurrent events serialize, reject, or resolve by version.

## Anti-Patterns and Rewrites

**“The dashboard should load fast.”**

Rewrite: “Given 50 widgets and cached metadata, when an authenticated analyst opens the dashboard from the target region, then Largest Contentful Paint is at most 2.5 seconds at p75 over 1,000 sessions.”

**“The form is user-friendly.”**

Rewrite: “At least 90% of representative first-time users complete the five-field form without assistance in under three minutes; validation identifies the field and corrective action.”

**“Data must be secure.”**

Rewrite: “A tenant reader can retrieve only records whose verified tenant claim matches the record tenant; cross-tenant identifiers return 404 and emit a redacted denial audit event.”

**“Errors are handled gracefully.”**

Rewrite: “If the payment dependency times out after two seconds, the API returns `503/PAYMENT_UNAVAILABLE`, persists no order, emits one retryable failure event, and exposes no provider details.”

**“Works for all users.”**

Rewrite: enumerate roles, locales, browsers/assistive technologies, permissions, and excluded populations; define expected behavior for each.

## Review Checklist

Each criterion should have a stable ID, unambiguous actor, controlled preconditions, single trigger, visible result, exact unit/threshold/window, negative and boundary coverage, privacy-safe test data, deterministic oracle, requirement/test traceability, and evidence location. If two independent reviewers can reasonably disagree whether it passed, refine it.
