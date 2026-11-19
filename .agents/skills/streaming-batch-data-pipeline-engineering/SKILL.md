---
name: streaming-batch-data-pipeline-engineering
description: Engineer idempotent streaming and batch data pipelines including CDC, Kafka/PubSub, lakehouse ETL/ELT, and backpressure handling for zero-data-loss architectures. Use when building data ingestion pipelines, schema registries, data-access layers, or resolving data-drift and throughput anomalies.
---

# Streaming and Batch Data Pipeline Engineering

## Purpose

This skill guides the design, implementation, migration, and diagnosis of reliable data pipelines across transactional sources, event streams, object storage, warehouses, and lakehouses. It emphasizes explicit schemas, replayability, idempotency, lineage, freshness, backpressure, and evidence-based recovery from partial failure.

It supports S1 Domain & Data Scoping, S2 Architecture & TDD Planning, S4 Pre-Implementation Gate, S5 Core Build, S6 Integration & CI/CD, and S7 Validation & Observability.

## When to Apply

Apply this skill when:

- Ingesting database changes through Change Data Capture.
- Designing Kafka, Pub/Sub, or equivalent streaming topologies.
- Building batch ETL, ELT, lakehouse, or warehouse pipelines.
- Defining schemas, compatibility, lineage, or data-access layers.
- Authoring database migrations or deterministic seed data.
- Handling duplicate delivery, replay, backpressure, or late data.
- Diagnosing data drift, schema mismatch, freshness loss, or throughput anomalies.
- Establishing a zero-data-loss architecture and recovery process.

## Inputs

Collect:

- Source systems, owners, schemas, keys, volumes, and change rates.
- Consumers, datasets, transformations, and serving requirements.
- Freshness, completeness, ordering, consistency, and recovery objectives.
- Privacy, classification, residency, retention, deletion, and audit rules.
- Broker, connector, compute, storage, catalog, and orchestration constraints.
- Expected failure modes, replay windows, and maintenance events.
- Existing migrations, topic conventions, schema registry, and lineage tooling.

## Step-by-Step Instructions

### 1. Build a Source Schema Inventory

For each source, record:

- Owner, system of record, environment, and connection method.
- Tables, collections, files, APIs, topics, and event types.
- Primary keys, natural keys, foreign keys, partitions, and ordering fields.
- Column names, types, nullability, defaults, constraints, and semantics.
- Update and delete behavior, including tombstones and soft deletion.
- Volume, record size, peak change rate, and growth estimate.
- Time zone, timestamp precision, clock source, and late-arrival profile.
- Sensitive fields, tenant keys, residency, retention, and deletion obligations.
- Known quality issues, undocumented values, and ownership gaps.

Profile representative data. Do not infer uniqueness or nullability from schema declarations alone.

### 2. Define Freshness, Completeness, and Lineage

For every produced dataset, specify:

- Freshness target from source commit to consumer availability.
- Maximum tolerated staleness and the alert threshold.
- Completeness expectation and reconciliation method.
- Event-time and processing-time semantics.
- Allowed lateness and correction window.
- Lineage from source fields through transformations to outputs.
- Dataset owner, consumers, criticality tier, and escalation path.
- Recovery point and recovery time objectives.

Represent lineage at both dataset and field level for regulated or heavily transformed data.

### 3. Design CDC Ingestion

Choose a CDC pattern:

- Transaction log capture for scalable, low-impact ordered changes.
- Database-native change streams where supported.
- Trigger or outbox tables when application-managed publication is required.
- Incremental query using a reliable watermark only when log capture is unavailable.

Define:

1. Initial consistent snapshot strategy.
2. Position or offset captured with the snapshot boundary.
3. Ongoing insert, update, and delete representation.
4. Transaction metadata and ordering requirements.
5. Schema-change handling and compatibility behavior.
6. Heartbeats and source-lag measurement.
7. Connector restart, failover, and offset storage.
8. Re-snapshot criteria and duplicate handling.

Keep the raw change envelope immutable in a retained landing layer when audit and replay requirements justify it.

#### CDC Safety Rules

- Prefer stable primary keys; define behavior when keys change.
- Preserve tombstones or delete indicators through all required consumers.
- Do not advance offsets before the durable output or transaction is committed.
- Monitor source log retention against worst-case connector downtime.
- Treat snapshot plus stream handoff as one correctness boundary.
- Isolate tenant and sensitive fields according to source policy.

### 4. Design Kafka or Pub/Sub Topology

For each stream, specify:

- Topic or subscription purpose and owning domain.
- Producer and consumer contracts.
- Partition or ordering key and rationale.
- Expected throughput, payload size, retention, and replay window.
- Consumer groups or subscriptions and delivery semantics.
- Retry, dead-letter, quarantine, and poison-message paths.
- Encryption, authorization, tenant isolation, and audit requirements.

#### Partitioning

Choose keys that balance ordering and parallelism. Validate skew using production-like distributions. Avoid keys with a single hot tenant or constant value.

#### Topic Boundaries

Prefer stable business event categories or data-product contracts. Avoid one topic for unrelated payloads and avoid creating a topic for every implementation class.

#### Retry Topology

Use bounded delayed retry for transient failures. Carry original event ID, attempt count, first-seen time, schema version, and trace context. Quarantine deterministic contract or data-quality failures for controlled remediation.

### 5. Integrate a Schema Registry

- Register key and value schemas under an explicit subject strategy.
- Choose backward, forward, or full compatibility according to producer and consumer deployment order.
- Validate schema changes in CI before deployment.
- Require defaults or optionality for newly added fields where the format needs them.
- Prohibit incompatible type changes, field reuse, or semantic changes under the same identity.
- Version semantic changes even if the wire schema remains technically compatible.
- Cache schemas safely but support registry unavailability within a bounded period.
- Monitor unknown schema IDs, deserialization failures, and compatibility rejections.

A registry validates structure, not business meaning. Pair it with data-contract ownership and semantic tests.

### 6. Design Lakehouse ETL or ELT

Use layered datasets with explicit quality contracts:

- Raw or bronze: immutable source-aligned records with ingestion metadata.
- Validated or silver: normalized types, deduplicated records, resolved deletes, and quality flags.
- Curated or gold: business-ready models, aggregates, and serving datasets.

For each transformation:

1. Declare input versions and output schema.
2. Select incremental key, watermark, or affected partitions.
3. Define deterministic transformation logic.
4. Handle late, corrected, and deleted records.
5. Write to staging or transactionally managed tables.
6. Validate counts, constraints, and reconciliation totals.
7. Atomically publish or swap the output.
8. Record lineage, run metadata, code version, and input positions.

Partition according to dominant filters and write patterns. Avoid over-partitioning high-cardinality columns that creates small files.

### 7. Select Processing Semantics

#### At-Least-Once

Use when the transport may redeliver and sinks can be made idempotent. This is often the clearest reliable choice.

Requirements:

- Stable source event or record identity.
- Deduplication or idempotent sink writes.
- Offset commit after durable output.
- Replay-safe side effects.

#### Exactly-Once

Use only when the complete path supports a well-defined transactional boundary. Exactly-once processing does not guarantee that arbitrary external side effects occur once.

Validate:

- Source positions participate in the same transaction as outputs, or equivalent atomic checkpointing exists.
- Producers use transaction or fencing mechanisms correctly.
- State stores and checkpoints are durable and recoverable.
- Sinks support transactional or deterministic idempotent writes.
- Operational recovery preserves the guarantee.

Document the boundary of the claim. Prefer precise wording such as exactly-once updates to a specific managed table.

### 8. Implement Idempotent Pipelines

Choose one or more patterns:

- Upsert by stable business key and source version.
- Merge by event ID with a deduplication ledger.
- Compare-and-set using source sequence or timestamp.
- Deterministic output paths and atomic replace for batch partitions.
- Transactional sink plus offset commit.
- Immutable append followed by deterministic compaction.

Define deduplication retention beyond the maximum replay window. Include tenant scope when identifiers are not globally unique.

### 9. Handle Backpressure and Flow Control

Observe pressure at every boundary: source, broker, processor, sink, and serving layer.

Controls include:

- Consumer pull limits, prefetch, and batch size.
- Maximum in-flight records or bytes.
- Partition-level pause and resume.
- Bounded internal queues.
- Adaptive concurrency based on sink latency and error rate.
- Producer quotas and publish rate limits.
- Spill-to-disk or durable buffering where data-loss risk requires it.
- Load shedding only for explicitly disposable data classes.

When lag rises:

1. Confirm source ingress rate and backlog age.
2. Identify the saturated stage rather than scaling every stage.
3. Check key skew, slow partitions, retries, and poison records.
4. Reduce pressure on the constrained sink.
5. Scale only within downstream capacity.
6. Estimate drain time and verify retention exceeds it.

### 10. Implement the Data-Access Layer

Provide a stable interface between domain logic and storage or analytical engines.

- Expose domain-oriented queries and writes, not storage-driver details.
- Require tenant and authorization context where data is multi-tenant.
- Use parameterized queries and allowlisted sort or filter fields.
- Define transaction ownership and consistency behavior.
- Enforce timeouts, pagination, result limits, and cancellation.
- Map storage errors into stable application errors.
- Instrument latency, rows scanned, result size, and query identity without sensitive values.
- Support schema evolution through adapters or versioned models.
- Prevent N+1 access and unbounded scans.

### 11. Author Migrations and Seed Data

#### Migrations

- Make each migration ordered, reviewable, and immutable after release.
- Separate expand, backfill, cutover, and contract phases for breaking changes.
- Keep old and new application versions compatible during rolling deployment.
- Batch backfills with checkpoints and rate limits.
- Measure locks, write amplification, storage growth, and replication lag.
- Add validation queries and an explicit rollback or forward-fix strategy.
- Never assume a schema rollback can restore discarded data.

#### Seeding

- Use deterministic identifiers and repeatable upserts.
- Separate required reference data from optional demo data.
- Keep secrets and environment credentials out of seed files.
- Version seed data with the schema or application contract.
- Verify tenant ownership and avoid cross-environment production data copies.

### 12. Wire Pipelines to Environments

- Parameterize endpoints, identities, storage paths, topics, and registry locations.
- Use workload identity or managed credentials instead of embedded keys.
- Create infrastructure, ACLs, schemas, and retention through versioned automation.
- Validate connectivity and authorization before enabling production flow.
- Use environment-specific consumer groups and output locations.
- Prevent non-production consumers from acknowledging production streams.
- Promote immutable artifacts and record configuration plus schema versions.

### 13. Detect and Resolve Data Drift

Monitor:

- Null, uniqueness, range, distribution, category, and referential-integrity changes.
- Record counts, delete rates, duplicate rates, and reconciliation totals.
- Field-level schema and semantic changes.
- Freshness, completeness, and lineage gaps.

Resolution process:

1. Confirm whether drift is expected business change or defect.
2. Find the first affected source position, partition, or batch.
3. Quarantine unsafe outputs without destroying raw data.
4. Correct source contract, schema, or transformation.
5. Replay deterministically from a known position.
6. Reconcile corrected outputs before publication.
7. Record impact, root cause, and prevention.

### 14. Resolve Schema Mismatches

- Capture schema ID, producer version, consumer version, and failing field.
- Distinguish wire incompatibility from semantic incompatibility.
- Verify subject naming and key/value registration.
- Deploy tolerant readers before producers when compatibility requires it.
- Use an adapter or versioned stream for incompatible changes.
- Do not silently coerce values that alter business meaning.
- Replay quarantined records after the compatible consumer is active.

### 15. Diagnose Throughput Anomalies

Inspect in order:

1. Source rate and source-side latency.
2. Broker publish latency, throttles, partition skew, and retention.
3. Consumer lag by partition, rebalance frequency, and processing time.
4. Retry amplification and poison-message loops.
5. Serialization, compression, network, and payload-size changes.
6. State-store, database, object-store, or warehouse saturation.
7. Small-file growth, compaction, checkpoint, or garbage-collection overhead.
8. Recent code, schema, configuration, or infrastructure changes.

Use per-stage rates and queue age to find the bottleneck. Average throughput can hide one stalled partition.

## Implementation Checklist

### Inventory and Contracts

- [ ] Sources, owners, keys, schemas, volumes, and sensitivity are inventoried.
- [ ] Freshness, completeness, ordering, lineage, and recovery targets are explicit.
- [ ] CDC snapshot and stream handoff are defined.
- [ ] Topic ownership, partitioning, retention, and retries are documented.
- [ ] Schema compatibility and semantic versioning are enforced in CI.

### Correctness and Recovery

- [ ] Delivery semantics are named for the complete path.
- [ ] Deduplication keys and retention cover replay windows.
- [ ] Offsets advance only after durable output.
- [ ] Deletes, late data, and corrections reach required consumers.
- [ ] Raw or recoverable inputs are retained for the stated objective.
- [ ] Replay and reconciliation are tested.

### Performance and Operations

- [ ] Backpressure controls are bounded at every stage.
- [ ] Partition skew and sink capacity are load-tested.
- [ ] Data quality, lag, freshness, schema, and throughput are observable.
- [ ] Migrations use expand/backfill/cutover/contract when required.
- [ ] Environment identities and ACLs are automated and isolated.
- [ ] Runbooks cover drift, mismatch, backlog, replay, and data loss.

### Stage Readiness

- [ ] S1 has source inventory, ownership, freshness, and lineage needs.
- [ ] S2 defines topology, contracts, semantics, and capacity.
- [ ] S4 validates source access, schemas, replay, and risk assumptions.
- [ ] S5 implements connectors, transforms, access, migrations, and tests.
- [ ] S6 wires identity, topics, storage, registry, and deployment.
- [ ] S7 verifies quality, drift, freshness, throughput, and recovery.

## Key Patterns

### Snapshot Plus Ordered Change Stream

Create a consistent baseline and resume from the exact source position associated with it. Deduplicate any overlap.

### Raw Immutable Landing Zone

Retain source-aligned data and ingestion metadata so corrected transformations can replay without returning to the source.

### Watermark with Allowed Lateness

Track event-time progress while retaining a bounded window for late records and correction updates.

### Transactional Outbox

Commit business changes and publish intent in the same source transaction, then relay and deduplicate downstream.

### Data Contract

Version schema, semantics, quality expectations, ownership, service objectives, and change procedure as one consumer-facing contract.

## Anti-Patterns

- Polling on an update timestamp that is nullable, mutable, or non-unique.
- Claiming exactly-once semantics without naming the transactional boundary.
- Committing source offsets before sink durability.
- Dropping delete events or late records without an explicit policy.
- Using processing time where event time defines correctness.
- Choosing a partition key without testing real distribution.
- Retrying poison records indefinitely in the main stream.
- Treating schema-registry compatibility as semantic compatibility.
- Updating released migrations in place.
- Seeding random identifiers that create duplicates on rerun.
- Scaling consumers while the sink is already saturated.
- Repairing curated outputs without preserving lineage or replay evidence.

## Output Format Expectations

Produce:

1. Source schema inventory and ownership matrix.
2. Freshness, completeness, lineage, retention, and recovery requirements.
3. CDC snapshot, offset, delete, and restart specification.
4. Streaming topology with topics, keys, partitions, retries, and quarantine.
5. Schema-registry compatibility and contract-change policy.
6. Lakehouse layer, incremental transformation, and publication design.
7. End-to-end delivery semantics and idempotency boundary.
8. Backpressure, capacity, and throughput model.
9. Data-access, migration, and seeding plan.
10. Test, reconciliation, observability, drift, mismatch, and replay runbook.
11. Evidence mapped to S1, S2, S4, S5, S6, and S7.

Outputs must identify authoritative sources, quantify freshness and capacity, state the exact correctness boundary, and provide a tested recovery path for duplicate, late, missing, and incompatible data.