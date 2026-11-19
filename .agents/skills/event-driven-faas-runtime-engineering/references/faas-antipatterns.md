# FaaS Anti-Patterns and Failure Modes

## Synchronous Fan-Out

**Shape:** One invocation calls dozens or hundreds of downstream functions or APIs and waits for all results.

**Failure mode:** Burst concurrency multiplies downstream traffic, tail latency dominates the parent timeout, partial failures trigger broad replay, and one dependency outage becomes a timeout cascade.

**Safer pattern:** Publish work to a queue or event bus, cap consumer concurrency, persist aggregation state, and expose asynchronous status. For bounded small fan-out, use strict parallelism limits and per-call deadlines.

**Detection:** Downstream calls per invocation, concurrent socket count, p99 child latency, parent timeout rate, and retry-amplified request volume.

## Unbounded Connection Creation

**Shape:** Every invocation opens a new database or HTTP connection with no pool, proxy, or concurrency budget.

**Failure mode:** A scale-out burst exhausts database sessions, ephemeral ports, DNS, or TLS capacity. Retries create more connections and prolong recovery.

**Safer pattern:** Reuse safe clients across warm invocations, use small bounded pools, configure stale-connection recovery, cap function concurrency, and add a managed database proxy when appropriate.

**Detection:** Connections per invocation, connection setup latency, refused connections, active sessions versus reserved concurrency, and socket errors.

## Large Response Payloads

**Shape:** A function returns or transports large datasets, reports, or binary objects through a synchronous gateway.

**Failure mode:** Provider payload limits are exceeded, memory usage doubles during serialization, latency and transfer cost increase, and clients retry interrupted responses.

**Safer pattern:** Store large results in object storage, return a short-lived authorized reference, paginate records, stream only where the platform supports bounded streaming, and compress appropriate content.

**Detection:** Response-size percentiles, serialization duration, peak memory, gateway limit errors, and client disconnects.

## Global Mutable State

**Shape:** Request, tenant, cache, or accumulator data is stored in module-level mutable variables.

**Failure mode:** Warm invocations observe stale or cross-tenant values, concurrent requests race, memory grows with instance age, and behavior differs between cold and warm execution.

**Safer pattern:** Keep request state local. Cache only immutable or tenant-neutral configuration. Bound caches, include full tenant/authorization scope in keys, and synchronize truly shared client initialization.

**Detection:** Memory by warm invocation count, stateful globals in static analysis, concurrency tests, tenant-switch tests, and differing cold/warm results.

## Missing Dead-Letter Configuration

**Shape:** Asynchronous events retry until expiry or disappear without a controlled failure destination.

**Failure mode:** Poison messages consume concurrency, ordered partitions stall, data is silently lost after retention, and operators cannot safely inspect or replay failures.

**Safer pattern:** Configure maximum attempts/age and a DLQ or quarantine store. Include event ID, schema, source, failure class, and correlation metadata. Alarm on arrivals and test authorized redrive.

**Detection:** Oldest-message age, receive count, retry rate, discarded-event metrics, and absence of DLQ alarms or replay ownership.

## Timeout Cascades

**Shape:** Function, client, queue visibility, and upstream deadlines are equal or incorrectly nested.

**Failure mode:** The outer timeout occurs first, work continues after callers give up, queue messages reappear while processing is active, and layered retries multiply traffic.

**Safer pattern:** Set connect and operation timeouts below function timeout; reserve cleanup and acknowledgment headroom; keep function timeout below visibility/lease deadlines; retry only transient failures with jitter and a total budget.

**Detection:** Duration clustered at configured timeouts, overlapping processing of one event, retry storms, queue visibility expirations, and downstream work after caller cancellation.

## Acknowledge Before Durability

**Shape:** The event is acknowledged or offset committed before required state and outgoing effects are durable.

**Failure mode:** A crash after acknowledgment loses work permanently.

**Safer pattern:** Commit business state and an outbox atomically, then acknowledge. If atomicity is impossible, define idempotent compensation and reconciliation.

## Retrying Deterministic Errors

**Shape:** Validation, authorization, schema, and business-rule errors use the same retry path as transient infrastructure failures.

**Failure mode:** Invalid events consume capacity, inflate costs, delay valid work, and eventually reach a DLQ without useful classification.

**Safer pattern:** Classify errors. Reject or quarantine deterministic input safely; retry bounded transient failures; surface stable reason codes.

## Random Idempotency Keys

**Shape:** The consumer generates a UUID for every delivery and treats it as a deduplication key.

**Failure mode:** Every retry appears new, so charges, notifications, and inserts repeat.

**Safer pattern:** Use a producer event ID or stable business operation key scoped by tenant and consumer purpose. Store request hash, status, result, and expiry atomically.

## Hidden SDK Retries

**Shape:** Cloud or HTTP clients retry internally while the handler also retries, without one total attempt/deadline budget.

**Failure mode:** Execution exceeds timeout, traffic multiplies, and latency is difficult to attribute.

**Safer pattern:** Configure SDK attempts explicitly, expose retry telemetry, nest deadlines, and choose one layer to own retries for each failure class.

## Review Matrix

| Anti-pattern | Primary signal | Required control |
|---|---|---|
| Synchronous fan-out | Calls per invocation | Queue and concurrency cap |
| Connection creation | New connections/second | Reuse, pool, proxy, reserved concurrency |
| Large payload | Payload p95/p99 | Object reference or pagination |
| Global state | Memory by warm age | Invocation-scoped state |
| Missing DLQ | Exhausted retries | DLQ alarm and replay runbook |
| Timeout cascade | Timeout-clustered duration | Nested deadlines and jitter |
| Early acknowledgment | Missing outcomes | Transaction/outbox |
| Deterministic retries | Repeated same error | Error classification |

Every remediation should include a duplicate-delivery test, dependency-failure test, maximum-payload test, and cold-versus-warm behavior check.