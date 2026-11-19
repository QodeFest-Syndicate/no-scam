# Chaos Engineering Playbook

## Objective and guardrails

Chaos engineering is controlled hypothesis testing for resilience, not random breakage. Every experiment requires authorization, measurable steady state, a bounded target, automated abort conditions where possible, and a tested recovery path. Start in an isolated environment and expand only when evidence supports the next step.

Never run a new production experiment during an incident, freeze, high-risk business window, or when telemetry is impaired. Stateful partitions require explicit data-owner review.

## Experiment design method

1. **Choose a critical journey.** Name the user outcome and SLO.
2. **Measure steady state.** Record success rate, tail latency, throughput, backlog, saturation, and correctness.
3. **State a falsifiable hypothesis.** Example: “Checkout remains above 99.9% while one payment-worker replica is unavailable for five minutes.”
4. **Select the smallest meaningful fault.** One instance, dependency direction, zone, or bounded error percentage.
5. **Map blast radius.** Count instances, users, regions, dependencies, and data at risk.
6. **Set preconditions.** Healthy redundancy, backups, on-call coverage, no conflicting change, and verified observability.
7. **Define abort thresholds.** User impact, SLO burn, saturation, integrity uncertainty, or recovery time.
8. **Prepare rollback.** Stop injection, restore policy, replace capacity, drain backlog, and verify synthetics.
9. **Run and observe.** Keep an exact timeline and avoid changing multiple variables.
10. **Decide and learn.** Pass, fail, abort, or inconclusive; assign remediation and a repeat condition.

## Failure-injection catalog

### Network

Inject latency, jitter, loss, bandwidth constraint, connection reset, or one-way partition. Verify timeouts, deadline propagation, cancellation, retry budgets, circuit breakers, load shedding, and recovery. Watch for synchronized retries and connection-pool exhaustion.

### Compute

Terminate one replica, constrain CPU, pressure memory, pause a process, or exhaust worker threads. Verify redundancy, readiness, autoscaling, rescheduling, graceful termination, queue control, and state restoration. Never exceed quorum or minimum serving capacity.

### Storage

Add latency, reject writes, return capacity errors, make a replica unavailable, or simulate restore. Verify durability, idempotency, backpressure, cache behavior, read-only modes, and recovery-point/recovery-time objectives. Use disposable or safely replicated data for destructive tests.

### DNS and service discovery

Return lookup failures, stale answers, delayed resolution, or endpoint churn. Verify caching TTLs, connection reuse, fallback, retry bounds, and recovery. A DNS test can affect more clients than the nominal service target; model that shared blast radius.

### Dependency and application

Return bounded 4xx/5xx responses, corrupt a non-sensitive fixture, slow a downstream API, expire credentials in a sandbox, or disable a feature. Verify classification, graceful degradation, user messaging, fail-open/fail-closed behavior, and reconciliation.

## Tool decision matrix

| Tool | Best fit | Strengths | Watch-outs |
|---|---|---|---|
| Chaos Monkey | Instance termination on cloud workloads | Simple, proven continuous termination | Narrow fault model; needs surrounding safety controls |
| LitmusChaos | Kubernetes experiments and CI workflows | Open source, declarative, broad experiment hub | CRD/RBAC operational overhead |
| Chaos Mesh | Kubernetes network, pod, stress, and I/O faults | Rich fault types and scheduling | Powerful privileges require strict scope and admission controls |
| Gremlin | Managed cross-platform program | Polished safety controls, scenarios, reporting | Commercial dependency and agent governance |

Choose based on target platforms, required fault types, authorization model, audit evidence, rollback controls, and operator familiarity—not catalog size.

## Blast-radius levels

| Level | Scope | Promotion requirement |
|---|---|---|
| 0 | Local test or simulation | Unit/contract tests pass |
| 1 | Disposable environment, one target | Fault and rollback verified |
| 2 | Staging journey, representative load | SLO telemetry and abort automation proven |
| 3 | Production canary or one replica | Change approval and staffed response |
| 4 | One zone or bounded customer cohort | Prior smaller experiments passed repeatedly |

Promotion is not automatic. High-criticality systems may intentionally stop at a lower level.

## Abort and recovery template

Abort immediately if any of these occur:

- Fast-burn SLO alert or contractual threshold breach.
- Healthy capacity drops below the redundancy target.
- Error or latency exceeds the approved ceiling for the observation period.
- Data integrity, tenant isolation, security, or billing correctness is uncertain.
- Telemetry, experiment control, or rollback control is lost.
- An unrelated incident begins.

Recovery sequence: stop the injector; confirm control-plane acknowledgment; restore network/resource settings; replace unhealthy instances; verify readiness; measure backlog drain; run critical synthetics; reconcile data; keep the incident open until steady state remains stable.

## Game day planning

### Two weeks before

Select scenario and owners; review architecture and past incidents; approve fault and blast radius; create experiment, rollback, communications, and evidence plans. Test tooling and access in a disposable environment.

### One day before

Confirm freeze calendar, participants, on-call schedule, dashboards, alerts, credentials, backups, and customer-impact policy. Record a go/no-go checklist and exact abort authority. Do not make last-minute scope expansions.

### During

Assign experiment commander, injector, observer, service owner, safety officer, and scribe. Announce start, capture baseline, inject one fault, narrate observations, stop on abort, recover, and announce end. The safety officer can halt without debate.

### After

Classify outcome; preserve timeline, telemetry, and configuration; compare observed behavior with hypothesis; create owned actions with due dates; convert defects into tests or detectors; schedule a repeat only after remediation. Share learning without blaming operators.

## Experiment record template

- ID, date, environment, owner, approver.
- Journey, SLO, architecture version, hypothesis.
- Target, fault parameters, duration, blast radius.
- Preconditions, steady-state measurements, abort conditions.
- Expected detection, response, degradation, and recovery.
- Actual timeline and evidence links.
- Result: pass, fail, aborted, or inconclusive.
- Findings, remediation owners, deadlines, and repeat criteria.

A passed experiment proves only the stated conditions, version, load, and scope. It is not a permanent certificate of resilience.