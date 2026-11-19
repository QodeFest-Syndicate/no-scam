# SLO-Based Alerting Reference

## Core model

An SLI is the ratio of good events to valid events. An SLO states the required ratio over a window. For a 99.9% SLO, the allowed bad-event fraction is 0.001. Error budget is the allowed bad events minus observed bad events. Burn rate is:

\[
\text{burn rate}=\frac{\text{observed bad-event ratio}}{1-\text{SLO target}}
\]

A burn rate of 1 consumes the budget exactly across the evaluation window. A burn rate of 10 consumes it ten times faster. Define eligibility and exclusions before writing queries; otherwise teams can improve the SLO by hiding traffic.

## Error-budget policy

| Remaining budget | Default action | Approval |
|---|---|---|
| Above 50% | Normal release policy | Service owner |
| 25–50% | Review risky releases and top error contributors | Engineering lead |
| 0–25% | Reliability work prioritized; progressive rollout required | Reliability owner |
| Exhausted | Freeze unrelated risky changes; incident review | Executive exception for release |

Policies should account for low traffic, telemetry gaps, planned maintenance only if contractually excluded, and events outside team control. Missing telemetry is not good traffic.

## Multi-window, multi-burn-rate alerts

Require both windows in a row to breach. The long window measures material budget consumption; the short window proves the condition is still active.

| Alert | Long window | Short window | Burn threshold | Approximate 30-day budget consumed | Route |
|---|---:|---:|---:|---:|---|
| Fast page | 1 hour | 5 minutes | 14.4 | 2% | Primary on-call |
| Sustained page | 6 hours | 30 minutes | 6 | 5% | Primary on-call |
| Slow ticket | 3 days | 6 hours | 1 | 10% | Service owner |

Use logical OR between alert classes and logical AND between windows within a class. Add minimum event volume or confidence handling for sparse services. Test alert queries against historical incidents and known healthy periods.

## Worked example: API availability

A service has a 99.9% target over 30 days and receives 10,000,000 eligible requests. It may have 10,000 bad requests. After 12 days it has observed 6,000 errors in 4,000,000 requests:

- Availability: 99.85%.
- Observed bad ratio: 0.15%.
- Burn rate: 0.15% / 0.1% = 1.5.
- Remaining budget at the current observed volume: 4,000 errors.
- At 500 errors/day, the currently computed budget is exhausted in 8 days.

This should not automatically page on the aggregate alone. Evaluate independent 6-hour/30-minute and 3-day/6-hour windows. If both halves of the 3-day class exceed 1, create urgent reliability work.

## Worked example: fast burn

A 99.95% checkout SLO permits a 0.05% error ratio. During the last hour, 720 of 100,000 checkouts failed: 0.72%. Burn rate is 14.4. In the last five minutes, 90 of 10,000 failed: 0.9%, a burn rate of 18. Both fast-page windows breach, so page immediately. Include the deployment marker, regional split, exemplar traces, and rollback action.

## Alert payload

Every notification should contain:

- SLO and impacted user journey.
- Current SLI, target, both window values, and burn rate.
- Estimated budget consumed and remaining.
- Affected region, version, tenant-safe segment, or dependency.
- Dashboard, query, exemplar trace, runbook, and recent deployment links.
- Owner, acknowledgment target, escalation path, and suggested containment.

Avoid alerts whose only action is “look at dashboard.”

## Routing and escalation

**Page** when immediate action can prevent meaningful budget loss. Notify primary on-call; escalate to secondary after the acknowledgment target and to incident command when blast radius or burn persists. **Ticket** sustained non-urgent burn with a due date before projected exhaustion. **Notify** product and customer teams when contract scope, customer-visible status, or communications thresholds are crossed.

Deduplicate by SLO and failure domain. Group only alerts that share one remediation. Silence a symptom only when an incident is actively owned and the underlying SLO remains visible.

## Dashboard design

A useful SLO dashboard shows:

1. SLI and target over the contractual window.
2. Error budget remaining as quantity and percentage.
3. Burn rate for every alert window.
4. Good, bad, excluded, and unknown event counts.
5. Failure reasons split by bounded operational dimensions.
6. Latency distribution, traffic, saturation, and dependency health.
7. Deployments, feature changes, and incident annotations.
8. Alert state, owner, and links to traces and logs.

Do not plot only an availability percentage near 100%; use budget and burn visualizations that make small but important changes visible.

## Budget exhaustion response

1. Declare ownership and validate the SLI query.
2. Stop active harm through rollback, traffic shift, feature disablement, or capacity action.
3. Freeze unrelated risky releases according to policy.
4. Identify dominant bad-event classes and affected scope.
5. Communicate customer impact using verified evidence.
6. Restore budget consumption below 1 and confirm sustained recovery.
7. Create regression coverage and assign reliability work.
8. Record any policy exception with approver, expiry, and risk.

## Query and policy validation

- Reconcile SLI event counts with independent logs or business records.
- Test no-traffic, partial telemetry, reset, delayed data, and duplicate-event behavior.
- Confirm ratios aggregate from counts, not averages of percentages.
- Verify windows and timezone boundaries.
- Replay known incidents and compare page timing.
- Review alert precision, recall, acknowledgment time, and actionable rate quarterly.

An SLO alert is successful when it brings the right responder at the right urgency with enough context to reduce user harm—not merely when a threshold changes state.