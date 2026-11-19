---
name: event-driven-faas-runtime-engineering
description: Engineer stateless, cold-start-optimized, event-driven serverless functions and FaaS microservices. Use when implementing FaaS handlers, event-bus consumers, lightweight API endpoints, or optimizing serverless runtime performance.
---

# Event-Driven FaaS Runtime Engineering

## Purpose

This skill guides the design, implementation, packaging, and diagnosis of production serverless functions. It emphasizes stateless execution, explicit event contracts, bounded resource use, idempotent processing, and predictable behavior under retries and burst concurrency.

It supports S2 Architecture & TDD Planning, S5 Core Build, S6 Integration & CI/CD, and S7 Validation & Observability.

## When to Apply

Apply this skill when:

- Implementing an event consumer, webhook, scheduled job, or lightweight API handler.
- Splitting event-driven work into independently deployable functions.
- Reducing cold-start latency or package size.
- Preparing function artifacts or container images for deployment.
- Handling duplicate events under at-least-once delivery.
- Diagnosing timeouts, memory growth, concurrency saturation, or function-level defects.

Do not force unsuitable workloads into FaaS. Reconsider the runtime for long-lived connections, unbounded processing, stateful coordination, or execution beyond provider limits.

## Inputs

Collect:

- Trigger source, event schema, and delivery guarantees.
- Runtime, platform limits, regions, and deployment model.
- Latency, throughput, availability, and cost objectives.
- Downstream dependencies and their concurrency limits.
- Retry, dead-letter, ordering, and replay policies.
- Security context, secrets, network paths, and data classification.
- Build, test, packaging, observability, and rollback requirements.

## Step-by-Step Instructions

### 1. Define the Trigger Binding and Contract

Specify before writing handler logic:

- Trigger type: HTTP, queue, topic, stream, object event, schedule, or custom event bus.
- Source, destination, subscription filters, and routing keys.
- Envelope and payload schema with version and content type.
- Event identifier, producer, occurrence time, tenant identity, and trace context.
- Batch size, ordering key, partition key, and partial-batch behavior.
- Delivery semantics, retry timing, maximum attempts, and dead-letter destination.
- Authentication, signature validation, authorization, and payload size limits.

Reject malformed or unauthorized input at the boundary. Preserve enough context to diagnose failures without logging sensitive payloads.

### 2. Design a Stateless Handler

Use a thin adapter around deterministic application logic:

1. Parse the platform-specific request or event envelope.
2. Validate schema, identity, authorization, and required metadata.
3. Normalize input into an internal command or event type.
4. Invoke a use-case function that does not depend on platform globals.
5. Commit state changes through explicit repositories or clients.
6. Emit outcomes, metrics, and structured logs.
7. Translate domain outcomes into platform acknowledgments or HTTP responses.

Treat local disk as ephemeral scratch space. Never rely on one invocation running on the same instance as another. Reuse initialized clients when safe, but do not store request or tenant state in globals.

### 3. Implement Idempotent Processing

Assume an event may be delivered more than once.

1. Choose a stable deduplication key, preferably producer event ID plus consumer purpose.
2. Scope the key by tenant and operation where collisions are possible.
3. Atomically record processing state with the intended business mutation.
4. Return the previously committed outcome for known completed keys.
5. Define behavior for keys marked in progress after a worker failure.
6. Apply a retention period longer than the maximum replay window.
7. Make downstream writes idempotent using conditional updates, upserts, or idempotency tokens.

For batch consumers, report only failed records when the platform supports partial acknowledgments. Otherwise, ensure successful records tolerate replay.

### 4. Bound Execution and Failure

- Set function timeout below the trigger's visibility or acknowledgment deadline.
- Set client connection, request, and operation timeouts below the function timeout.
- Reserve time for cleanup, acknowledgment, and telemetry flushing.
- Retry only transient failures and add exponential backoff with jitter.
- Do not retry validation, authorization, or deterministic business errors.
- Route exhausted transient failures to a dead-letter or quarantine path.
- Place circuit breakers or bulkheads around unstable dependencies.
- Define compensating actions for partial side effects that cannot be atomic.

### 5. Optimize Cold Starts

Measure before and after each optimization.

#### Bundle and Dependency Size

- Package only production dependencies and required runtime files.
- Remove tests, source maps, locale packs, docs, caches, and unused binaries when safe.
- Prefer targeted imports and tree-shakable libraries.
- Avoid large framework bootstraps for narrow handlers.
- Split unrelated handlers when shared bundles create excessive initialization cost.

#### Initialization

- Keep module import work minimal.
- Move infrequently used dependencies behind lazy initialization.
- Initialize reusable clients outside the handler when thread-safe and tenant-neutral.
- Cache immutable configuration after validation.
- Defer optional feature initialization until the branch is invoked.
- Avoid network calls during startup unless required and bounded.

#### Connections

- Reuse HTTP and database connections across warm invocations.
- Configure small pools appropriate to per-instance concurrency.
- Validate stale pooled connections and reconnect safely.
- Use managed proxies when burst concurrency would exhaust database connections.
- Never cache request credentials or tenant-specific authorization globally.

### 6. Plan Concurrency and Horizontal Scaling

Calculate peak invocation concurrency from arrival rate and execution time. Include retries, batch size, and burst behavior.

Set:

- Reserved or maximum concurrency to protect downstream systems.
- Per-instance concurrency only when handler code and clients are safe for it.
- Queue visibility timeout greater than bounded execution and retry needs.
- Batch size according to payload size, processing variance, and failure granularity.
- Partition counts and ordering keys based on throughput and sequencing needs.
- Backpressure controls when downstream capacity is below event ingress.

Use queue age, throttles, active instances, downstream saturation, and error rate together. Scaling the function faster can make a dependency outage worse.

### 7. Package the Artifact

#### Archive Packages

- Lock dependencies and build reproducibly.
- Compile for the target runtime and architecture.
- Include only the handler, runtime dependencies, and required assets.
- Verify handler path, file permissions, and native library compatibility.
- Generate an artifact checksum and software bill of materials when required.

#### Container Images

- Use a small supported runtime base or minimal multi-stage build.
- Pin base images and dependencies by immutable version or digest.
- Copy only runtime output into the final stage.
- Run as a non-root user when supported.
- Remove package-manager caches and build tools.
- Add no daemon, shell loop, or background service that bypasses the runtime contract.
- Scan the final image and record its digest.

### 8. Test the Function

Cover:

- Valid event or request and expected side effects.
- Schema, authorization, and signature failures.
- Duplicate delivery and replay after completion.
- Failure between side effect and acknowledgment.
- Partial-batch failure and poison messages.
- Dependency timeout, throttle, and transient failure.
- Maximum payload, batch, memory, and execution duration.
- Concurrent invocations with shared dependencies.
- Cold and warm invocation behavior.

Use platform emulation sparingly. Contract tests and a deployed non-production invocation are needed for trigger bindings and identity integration.

### 9. Diagnose Runtime Defects

#### Timeout Regressions

1. Compare initialization duration with handler duration.
2. Inspect dependency latency, DNS, connection setup, and network path changes.
3. Check retries hidden inside SDKs.
4. Correlate timeout growth with payload size, batch size, or cold-start rate.
5. Confirm timeout hierarchy from client to function to queue visibility.
6. Patch the bottleneck; do not only raise the function timeout.

#### Memory Leaks or Growth

1. Graph peak memory by warm-instance invocation count.
2. Inspect global arrays, caches, listeners, buffers, and unclosed streams.
3. Bound caches and clear request-scoped references.
4. Stream large payloads rather than loading full objects.
5. Verify client libraries do not accumulate telemetry or sockets.
6. Reproduce with repeated invocations in one process.

#### Function-Level Bugs

- Reproduce using the exact event envelope and configuration version.
- Correlate event ID, request ID, trace ID, deployment version, and tenant.
- Distinguish poison input from transient infrastructure failure.
- Quarantine unsafe events before replay.
- Patch with a regression test and verify replay behavior.

## Implementation Checklist

### Contract and Safety

- [ ] Trigger, schema version, filtering, and routing are explicit.
- [ ] Tenant and identity context are verified at the boundary.
- [ ] Handler state is invocation-scoped.
- [ ] Deduplication key and retention exceed replay requirements.
- [ ] Side effects are atomic or safely repeatable.
- [ ] Error classes map to retry, reject, or dead-letter behavior.

### Performance and Scaling

- [ ] Cold-start and warm latency are measured separately.
- [ ] Bundle or image excludes unnecessary content.
- [ ] Initialization and connection reuse are safe.
- [ ] Timeouts are nested and leave acknowledgment headroom.
- [ ] Concurrency protects downstream limits.
- [ ] Batch and partition settings have load-test evidence.

### Delivery and Operations

- [ ] Artifact is reproducible, scanned, and traceable.
- [ ] Logs, metrics, and traces include deployment and correlation fields.
- [ ] Alerts cover errors, throttles, duration, queue age, and dead letters.
- [ ] Replay and quarantine procedures are tested.
- [ ] Rollback does not break event-schema compatibility.
- [ ] S2, S5, S6, and S7 evidence is linked to the function release.

## Key Patterns

### Thin Handler, Explicit Use Case

Keep platform parsing and acknowledgment separate from domain logic. This enables deterministic tests and runtime migration.

### Idempotency Ledger

Store deduplication key, status, timestamps, result reference, and expiry. Couple the ledger transition to the business write when possible.

### Transactional Outbox

Write domain state and an outgoing event record in one transaction. Publish the outbox asynchronously and deduplicate at consumers.

### Quarantine and Replay

Move poison or contract-invalid events to a controlled store with reason, schema version, and correlation metadata. Replay only after correction and authorization.

## Anti-Patterns

- Storing cross-invocation business state in memory or temporary files.
- Acknowledging an event before required side effects are durable.
- Retrying every error, including invalid input and denied access.
- Generating a new deduplication key inside the consumer.
- Opening a new database connection for every invocation without limits.
- Setting unbounded function concurrency against a bounded database.
- Importing a full application framework for a tiny handler without evidence.
- Logging full event payloads, credentials, or regulated data.
- Raising memory or timeout settings instead of diagnosing regressions.
- Deploying a mutable container tag without recording the image digest.

## Output Format Expectations

Produce:

1. Function responsibility and non-goals.
2. Trigger-binding specification and versioned payload contract.
3. Handler flow and dependency diagram or structured outline.
4. Idempotency, retry, acknowledgment, dead-letter, and replay policy.
5. Concurrency, timeout, memory, batch, and scaling budget.
6. Artifact packaging and security specification.
7. Test matrix covering normal, duplicate, failure, and load paths.
8. Observability fields, dashboards, alerts, and diagnostic runbook.
9. Stage evidence for architecture, build, packaging, and validation.

Outputs must state platform assumptions, quantify limits, and distinguish measured values from estimates.