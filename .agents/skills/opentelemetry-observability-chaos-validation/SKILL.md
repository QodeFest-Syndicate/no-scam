---
name: opentelemetry-observability-chaos-validation
description: Instrument distributed tracing with OpenTelemetry, configure SLO alerting, run synthetic probes, and execute chaos injection and data-drift testing for production validation. Use when setting up observability, diagnosing latency or reliability issues, validating system resilience, or implementing chaos engineering practices.
---

# OpenTelemetry Observability and Chaos Validation

## Purpose

This skill builds evidence that a distributed system is correct, observable, and resilient after deployment. It combines OpenTelemetry signals, SLO-based alerting, synthetic probes, controlled fault injection, data-drift detection, performance benchmarking, and automated rollback criteria.

## When to Apply

Apply this skill when work includes:

- Defining measurable reliability or latency targets.
- Instrumenting services, functions, queues, databases, or gateways.
- Correlating traces, metrics, logs, and deployment metadata.
- Investigating cross-service latency, errors, or saturation.
- Building user-journey or API synthetic probes.
- Validating behavior under pod loss, latency, dependency failure, or network partition.
- Detecting changes in data quality, distributions, schemas, or model inputs.
- Automating post-deployment TDD or BDD verification.
- Designing contract regression suites and rollback triggers.
- Triaging high-volume logs and failed assertions.

Chaos experiments require explicit authorization, a bounded blast radius, and a tested abort path.

## Stage Alignment

- **S2 — Architecture & TDD Planning:** define SLIs, SLO targets, telemetry ownership, test hypotheses, and error budgets.
- **S5 — Core Build:** loop defects back into implementation, tests, contracts, and instrumentation.
- **S6 — Integration & CI/CD:** wire telemetry, publish deployment markers, and automate validation jobs.
- **S7 — Validation & Observability:** run probes, benchmarks, drift checks, chaos experiments, triage, and rollback validation.

## Core Principles

1. **Instrument boundaries first.** Observe ingress, egress, queues, storage, and asynchronous handoffs before adding internal detail.
2. **Use open semantic conventions.** Stable names and attributes make signals portable and comparable.
3. **Correlate every signal.** Trace IDs, request IDs, tenant-safe identifiers, versions, and environment metadata connect evidence.
4. **Alert on user impact.** SLO burn and symptoms outrank isolated component noise.
5. **Treat telemetry as production code.** Test it, version it, budget its cost, and review its privacy impact.
6. **Form a hypothesis before injecting failure.** Every experiment needs expected behavior and measurable steady state.
7. **Stop safely.** Abort conditions and rollback automation are defined before validation begins.
8. **Turn incidents into regression coverage.** A found defect should become a test, assertion, or detector.

## Step-by-Step Workflow

### 1. Define the Reliability Contract

- List critical user journeys, API operations, background flows, and data products.
- Choose SLIs that represent user outcomes: availability, correctness, latency, freshness, durability, or throughput.
- Define SLO targets and evaluation windows.
- Set an error-budget policy with release, escalation, and freeze behavior.
- Record recovery objectives and dependencies that can invalidate the SLO.
- Assign owners for instrumentation, dashboards, alerts, and response.

Example SLI:

- Good events: successful requests completing below the latency threshold.
- Valid events: all eligible requests excluding explicitly documented cases.
- SLI: good events divided by valid events.

**Exit condition:** each critical journey has an owner, SLI, target, window, and response policy.

### 2. Design OpenTelemetry Instrumentation

#### Traces

- Create server spans for inbound requests and consumer spans for received messages.
- Propagate W3C Trace Context and baggage only through trusted, size-bounded fields.
- Create client or producer spans around outbound dependencies.
- Record status and exceptions without duplicating stack traces excessively.
- Add events for meaningful state changes, retries, and fallback decisions.
- Use span links for batch, fan-in, fan-out, and delayed asynchronous relationships.
- Capture deployment version and stable service resource attributes.

#### Metrics

- Use counters for cumulative events, histograms for latency or size, and gauges only for observable current state.
- Prefer OpenTelemetry semantic metric names and consistent units.
- Publish request count, error count, latency, saturation, queue age, retry count, and work completion where applicable.
- Define histogram boundaries around meaningful SLO thresholds.
- Avoid labels with unbounded values such as request IDs, raw URLs, emails, or stack traces.

#### Logs

- Emit structured logs with timestamp, severity, service, environment, version, event name, and safe context.
- Include trace and span identifiers for correlation.
- Preserve one canonical error record and link related retries or summaries.
- Redact or hash sensitive fields according to policy.
- Keep assertion messages machine-filterable and specific about expected versus observed behavior.

### 3. Configure the Telemetry Pipeline

- Send application signals through an OpenTelemetry Collector when central policy, batching, retries, or routing is required.
- Separate receiver, processor, exporter, and connector responsibilities.
- Use memory limiting before batching to protect the collector.
- Apply attribute filtering and redaction before export.
- Route production and non-production data intentionally.
- Configure bounded queues, retry limits, and dead-letter or failure visibility.
- Monitor collector drops, refused data, queue use, export latency, and backend rejection.
- Protect telemetry endpoints with encryption and scoped authentication.
- Estimate signal volume, retention, sampling, and cost before launch.

### 4. Establish Distributed Trace Correlation

- Validate propagation across HTTP, RPC, messaging, scheduled tasks, and functions.
- Confirm sampling decisions propagate consistently.
- Use head sampling for predictable cost and tail sampling for rare errors or slow traces when infrastructure supports it.
- Preserve exemplars so metric spikes link to representative traces.
- Add deployment, region, availability zone, and runtime attributes with bounded cardinality.
- Represent tenant context only through policy-approved identifiers; never place secrets or personal data in baggage.
- Test missing, malformed, and conflicting trace headers.

A useful trace should answer:

- Which version handled the request?
- Where was time spent?
- Which dependency failed or retried?
- Which asynchronous work followed?
- Which logs and metric exemplars belong to the same execution?

### 5. Define SLO Alerting and Burn Rates

- Derive alerts from error-budget consumption rather than raw error counts alone.
- Pair a fast-burn, short-window alert with a slow-burn, long-window alert.
- Require both a short and long window for each alert class to reduce transient noise.
- Route urgent alerts to responders and slower budget warnings to planned remediation.
- Include SLO, current burn rate, impacted journey, relevant deploys, dashboards, and runbook in alert context.
- Test alert queries against known good and bad periods.
- Track alert precision, actionability, and time to acknowledge.

Typical policy shape:

- Fast burn: pages when a large portion of the budget will be exhausted quickly.
- Slow burn: creates urgent work before sustained degradation consumes the budget.
- Budget exhausted: freezes risky changes unless explicitly waived.

Tune numerical thresholds to the SLO and operating model; do not copy them blindly.

### 6. Build Synthetic Probes

- Select probes for availability, authentication, core transactions, data freshness, and external dependency reachability.
- Make each probe deterministic, idempotent, and safe to repeat.
- Use dedicated synthetic accounts and tagged test data.
- Run from locations that represent user and dependency paths.
- Set explicit DNS, connection, request, and end-to-end timeouts.
- Validate content and state transitions, not only HTTP status.
- Clean up created data or use expiring fixtures.
- Emit metrics and traces with a stable probe identifier.
- Alert after a defined number or duration of failures to balance speed and noise.

Deploy deep probes less frequently than lightweight probes if cost or mutation risk is high.

### 7. Create a Performance Benchmark

- State the hypothesis, workload model, dataset, environment, and acceptance thresholds.
- Separate warm-up, steady-state, stress, spike, and soak phases.
- Control concurrency, arrival rate, payload distribution, cache state, and dependency behavior.
- Record throughput, latency percentiles, errors, saturation, queueing, and resource use.
- Compare against an approved baseline using the same methodology.
- Preserve test configuration, artifact version, raw results, and environment metadata.
- Reject averages as the sole latency measure; evaluate tail behavior and correctness.
- Distinguish client-side queuing from server response time.

### 8. Design Chaos Experiments

For each experiment, write:

1. Hypothesis.
2. Steady-state indicators.
3. Fault and target.
4. Blast radius.
5. Preconditions.
6. Observation window.
7. Abort thresholds.
8. Recovery and rollback steps.
9. Evidence to retain.

#### Pod or Instance Kill

- Target a small percentage or one replica.
- Verify redundancy, rescheduling, readiness, retry behavior, and state recovery.
- Abort if healthy capacity, queue age, or error budget crosses the limit.

#### Latency Injection

- Inject bounded latency into a specific dependency path.
- Verify timeouts, deadlines, cancellation, circuit breakers, fallback, and queue control.
- Watch for retry storms and connection-pool exhaustion.

#### Network Partition

- Partition one direction and dependency at a time where possible.
- Verify leader election, quorum behavior, consistency guarantees, and recovery.
- Do not partition stateful systems without understanding split-brain and data-loss risks.

Start in isolated environments, then increase realism and scope only after evidence supports it. Never run unbounded experiments during active incidents or high-risk change windows.

### 9. Validate Data Drift

Define drift relative to a versioned baseline and an operational consequence.

- Check schema, type, nullability, range, uniqueness, referential integrity, and freshness.
- Compare distributions using fit-for-purpose measures such as population stability, divergence, distance, or domain thresholds.
- Segment by source, tenant, region, product tier, and time where permitted.
- Separate source drift, pipeline defects, concept drift, and seasonal behavior.
- Require minimum sample sizes and account for multiple comparisons.
- Quarantine, warn, degrade, retrain, or roll back according to impact.
- Store baseline version, detector configuration, observed values, and decision.

A drift alert should identify the changed feature or contract, affected scope, baseline, magnitude, likely impact, and next action.

### 10. Automate Post-Deployment Verification

- Map TDD tests to APIs, contracts, migrations, and failure behavior that can run safely after deployment.
- Express BDD scenarios around business-visible outcomes and critical journeys.
- Run smoke checks immediately, then deeper suites during the observation window.
- Validate old and new clients against backward-compatible interfaces.
- Tag tests by environment safety, mutation, duration, owner, and rollback relevance.
- Publish machine-readable and human-readable results tied to artifact and deployment IDs.
- Block promotion when mandatory tests are skipped, flaky, or inconclusive.

### 11. Build a Data-Contract Regression Suite

Cover:

- Schema compatibility and required fields.
- Type, enum, unit, timezone, and semantic changes.
- Ordering, duplication, idempotency, and replay behavior.
- Null, boundary, malformed, and oversized values.
- Producer and consumer version combinations.
- Serialization and deserialization across supported languages.
- Freshness, completeness, and volume thresholds.
- PII classification and access constraints.

Use consumer-driven contracts where ownership is distributed, and retain representative sanitized fixtures with explicit versions.

### 12. Configure Automated Rollback Triggers

- Select decisive signals tied to user impact and correctness.
- Require a minimum observation duration and data volume.
- Account for known telemetry delay.
- Combine deployment-specific and system-wide views to avoid blaming unrelated incidents.
- Trigger rollback only when the previous version is compatible with current data and infrastructure.
- Halt promotion when telemetry is missing.
- Notify responders with the threshold, evidence, action, and current system state.
- Run post-rollback verification and preserve the incident timeline.

If rollback is unsafe, automate traffic isolation, feature disablement, or forward remediation instead.

### 13. Triage Logs and Assertions at Scale

- Normalize event names, error codes, and assertion identifiers.
- Group by fingerprint, service, version, environment, and trace.
- Compare failure rates before and after deployment.
- Rank clusters by affected requests, tenants, SLO impact, and novelty.
- Sample repeated events while preserving counts and first/last occurrence.
- Pivot from an alert to exemplar trace, correlated logs, metrics, deployment marker, and source version.
- Record a minimal reproduction and convert confirmed defects into regression tests.

## Checklists

### Instrumentation Readiness

- [ ] Critical boundaries emit traces, metrics, and structured logs.
- [ ] Context propagates across synchronous and asynchronous hops.
- [ ] Names, units, attributes, and resource metadata follow stable conventions.
- [ ] Cardinality and sensitive-data controls are enforced.
- [ ] Collector loss, backpressure, and export failures are observable.
- [ ] Telemetry volume, sampling, retention, and cost are budgeted.

### SLO and Probe Readiness

- [ ] Every critical journey has an SLI, SLO, window, owner, and error-budget policy.
- [ ] Fast- and slow-burn alerts are tested and actionable.
- [ ] Synthetic probes verify content or state, not status alone.
- [ ] Probe identities, data lifecycle, locations, and timeouts are controlled.
- [ ] Dashboards and runbooks link directly from alerts.

### Chaos Readiness

- [ ] The hypothesis and steady state are measurable.
- [ ] Authorization, scope, duration, and blast radius are explicit.
- [ ] Abort conditions are automated where possible.
- [ ] Recovery and rollback paths are tested before injection.
- [ ] Responders know the schedule and can stop the experiment.
- [ ] Evidence and follow-up actions have owners.

### Validation Readiness

- [ ] Benchmarks are reproducible and compared with a valid baseline.
- [ ] Drift detectors have versioned baselines and minimum sample sizes.
- [ ] Contract suites cover compatibility and data-quality boundaries.
- [ ] Post-deployment tests are safe, deterministic, and deployment-linked.
- [ ] Rollback triggers account for telemetry delay and data compatibility.

## Key Patterns

- **Golden signals plus domain signals:** latency, traffic, errors, and saturation are paired with correctness and business outcomes.
- **Telemetry contract:** signal names, attributes, units, privacy, and ownership are versioned interfaces.
- **Exemplar navigation:** a metric anomaly leads directly to a representative trace and correlated logs.
- **Multi-window burn alert:** urgency reflects both current severity and sustained budget consumption.
- **Steady-state hypothesis:** chaos validates a declared resilience behavior, not random breakage.
- **Progressive experiment:** fault scope expands only after each smaller experiment passes.
- **Versioned drift baseline:** every drift decision records what comparison standard was used.
- **Defect feedback loop:** S7 evidence creates S5 fixes and permanent regression coverage.

## Anti-Patterns

- Adding spans everywhere without a question, naming standard, or cost budget.
- Using request IDs, user IDs, raw URLs, or errors as metric labels.
- Logging secrets, payloads, or unrestricted baggage.
- Sampling away all errors or slow traces without understanding the decision point.
- Paging on every component threshold regardless of user impact.
- Treating dashboards as a substitute for alerts and runbooks.
- Running synthetics that mutate production without cleanup or ownership.
- Injecting faults without authorization, abort criteria, or a recovery path.
- Declaring drift from tiny samples or natural seasonality.
- Comparing benchmarks from different workloads or environments.
- Rolling back automatically when schema or data changes are incompatible.
- Retrying failed assertions until validation appears green.

## Output Format Expectations

When applying this skill, produce a validation packet with:

1. **Scope:** critical journeys, architecture boundaries, environment, owners, and assumptions.
2. **Reliability contract:** SLIs, SLOs, windows, error budget, and response policy.
3. **Instrumentation map:** services, spans, metrics, logs, attributes, propagation, and sampling.
4. **Telemetry pipeline:** collectors, processors, exporters, security, loss controls, retention, and cost.
5. **Dashboards and alerts:** queries, thresholds, burn windows, routing, and runbook links.
6. **Synthetic plan:** probe flows, locations, frequency, identities, assertions, and cleanup.
7. **Benchmark plan:** workload, phases, baseline, environment, thresholds, and retained results.
8. **Chaos plan:** hypothesis, fault, blast radius, steady state, abort criteria, and recovery.
9. **Drift and contract plan:** baselines, detectors, segmentation, compatibility matrix, and actions.
10. **Post-deployment gate:** test suites, deployment linkage, decision rules, and rollback triggers.
11. **Evidence summary:** results, anomalies, trace or dashboard links, decision, defects, and owners.

State whether the outcome is pass, fail, rollback, halt, or inconclusive. Never convert missing telemetry or insufficient samples into a pass.
