---
name: data-contract-schema-evolution-management
description: Manage data contracts, schema registries (Avro/Protobuf/JSON-Schema), and backward-compatibility gating for evolving data-driven services. Use when designing data models, validating schema evolution, enforcing data contracts, or resolving schema-mismatch issues across service boundaries.
---

# Data Contract and Schema Evolution Management

## Purpose

Use this skill to make data exchanged across services explicit, versioned, testable, and safe to evolve. It applies to synchronous APIs, events, streams, files, and analytical datasets. Treat a contract as an owned product boundary, not only as a serialization artifact.

## Relevant Stages

- **S1 — Domain & Data Scoping:** Inventory producers, consumers, datasets, owners, sensitivity, and current schemas.
- **S2 — Architecture & TDD Planning:** Select schema technology, compatibility mode, ownership, and migration strategy.
- **S4 — Pre-Impl Gate:** Validate proposed changes against registered versions and affected consumers.
- **S5 — Core Build:** Implement schemas, serializers, migrations, contract tests, and telemetry.
- **S7 — Validation & Observability:** Detect drift, diagnose mismatches, and reconcile runtime behavior with contracts.

## When to Apply

Apply this skill when:

- A service publishes or consumes structured data.
- A field, type, enum, key, or semantic meaning changes.
- Teams need a registry or compatibility policy.
- Runtime deserialization or validation fails.
- Producer and consumer releases cannot be coordinated.
- Data lineage shows divergent definitions for the same concept.

## Workflow

### 1. Inventory the Contract Surface

1. List every producer and consumer, including batch jobs, BI tools, caches, and replay workers.
2. Record transport, subject/topic/endpoint, schema location, owner, release cadence, retention, and replay window.
3. Capture representative payloads and the latest deployed schema version.
4. Classify fields as required, optional, nullable, sensitive, key/partitioning, or derived.
5. Identify semantic invariants that syntax alone cannot express.

### 2. Define the Contract

A contract should state:

- Canonical field names, types, logical types, defaults, units, and time zones.
- Required versus optional behavior and null semantics.
- Identifier, ordering, uniqueness, and referential-integrity rules.
- Enum extensibility and unknown-value handling.
- Data classification, retention, residency, and masking requirements.
- Producer guarantees, consumer obligations, ownership, and support window.
- Examples of valid, boundary, and invalid payloads.

Store the schema in version control. Generate artifacts from one canonical source where practical; do not maintain equivalent definitions manually.

### 3. Select and Configure the Registry

Choose based on ecosystem and compatibility needs:

- **Avro:** Strong fit for event streams, compact payloads, defaults, and reader/writer schema resolution.
- **Protobuf:** Strong fit for RPC and polyglot services; preserve field numbers and reserve removed fields.
- **JSON Schema:** Strong fit for JSON APIs, documents, and rich structural validation; pin the dialect.

Registry requirements:

- Use stable subject naming tied to the logical contract, not a transient deployment.
- Require authenticated writes and read-only runtime credentials.
- Enable audit logs, immutable released versions, and environment separation.
- Configure compatibility per subject; avoid relying only on a registry-wide default.
- Attach owner, repository, classification, lifecycle status, and documentation metadata.

### 4. Set Compatibility Rules

Evaluate compatibility against all supported versions, not only the latest, when consumers lag or data is replayed.

- **Backward compatible:** New readers can consume old data. Common safe change: add an optional/defaulted field.
- **Forward compatible:** Old readers can consume new data. Requires unknown-field tolerance and careful enum handling.
- **Full compatible:** Both backward and forward compatible.
- **Breaking:** Requires migration, versioned boundary, or coordinated rollout.

Format-specific rules:

- Avro additions need defaults for backward compatibility; changing a field type is safe only under supported promotion rules.
- Protobuf field numbers must never be reused; reserve deleted names and numbers; avoid changing wire-incompatible types.
- JSON Schema tightening constraints, adding required properties, or forbidding previously allowed properties is usually breaking.

### 5. Choose an Evolution Strategy

Use the least disruptive strategy that preserves correctness:

- **Additive-only:** Add optional/defaulted fields; readers tolerate unknown fields. Default for routine evolution.
- **Migration-based:** Transform stored or in-flight data when semantics or structure must change. Make migrations resumable, observable, and reversible.
- **Dual-read/dual-write:** Temporarily support old and new forms for incompatible changes. Define source of truth, reconciliation, cutover, and removal dates.
- **Versioned contract:** Publish a new topic, endpoint, message, or subject for intentionally breaking semantics.

Never dual-write without idempotency keys, mismatch monitoring, and an explicit convergence plan.

### 6. Automate Contract Validation

Implement CI gates that:

1. Parse and lint the schema.
2. Compare it with every supported registered version.
3. Run format-specific compatibility checks.
4. Generate or compile client bindings.
5. Validate golden valid/invalid fixtures.
6. Run producer and consumer contract tests.
7. Detect undocumented semantic changes.
8. Block release on breaking changes unless an approved migration plan is linked.

Include runtime validation at untrusted boundaries. Sample validation on high-volume trusted paths when full validation would violate latency budgets.

### 7. Align Services and Manage Versions

- Assign one accountable contract owner and named consumer contacts.
- Publish a changelog containing intent, compatibility result, rollout order, and rollback plan.
- Use semantic lifecycle labels such as draft, active, deprecated, and retired; do not assume schema IDs express business compatibility.
- Define a minimum support window based on deployment lag and data retention.
- Announce deprecation with usage evidence and a final removal date.
- Remove an old version only after traffic, registry access, and replay analysis show no remaining consumers.

### 8. Diagnose Schema Mismatches

1. Capture the failing payload safely and record producer, consumer, schema ID/version, and serializer.
2. Determine whether failure is registry lookup, wire format, syntax validation, or semantic validation.
3. Compare writer schema, reader schema, generated binding, and deployed application version.
4. Check defaults, nullability, enum values, logical types, field numbers, unknown-field behavior, and subject naming.
5. Reproduce with the exact bytes or sanitized fixture.
6. Contain impact through quarantine, fallback reader, rollback, or traffic isolation.
7. Correct the contract or implementation; do not silently discard unknown or invalid data.
8. Backfill or replay quarantined records and add a regression fixture.

## Checklists

### Pre-Implementation Gate

- [ ] Producers, consumers, owners, and replay windows are inventoried.
- [ ] Canonical schema and semantic invariants are documented.
- [ ] Compatibility mode matches deployment and retention realities.
- [ ] Registry checks pass against all supported versions.
- [ ] Breaking changes have migration, rollback, and communication plans.
- [ ] Sensitive fields include governance metadata.
- [ ] Contract tests and representative fixtures exist.

### Release and Drift Review

- [ ] Released schema is immutable and registered before deployment.
- [ ] Producer and consumer rollout order is explicit.
- [ ] Validation failures, unknown fields, and schema IDs are observable.
- [ ] Runtime payloads conform to registered contracts.
- [ ] Deprecated versions have usage evidence and retirement dates.
- [ ] Quarantined data has an owner and replay procedure.

## Key Patterns

- **Consumer-driven contracts:** Consumers publish expectations that producers verify in CI.
- **Expand–migrate–contract:** Add the new shape, migrate readers and data, then remove the old shape.
- **Schema fingerprinting:** Emit a stable schema fingerprint with telemetry for drift detection.
- **Golden fixtures:** Version representative payloads to verify bindings and semantic rules across languages.
- **Compatibility budget:** Treat every exception as time-bound debt with an owner and expiration date.

## Anti-Patterns

- Editing a released schema in place.
- Reusing Protobuf field numbers or redefining existing field meaning.
- Treating a successful registry check as proof of semantic compatibility.
- Adding required fields without defaults to retained or replayable data.
- Coordinating breaking changes only through release timing.
- Maintaining duplicate schemas in multiple repositories without generation or reconciliation.
- Logging full sensitive payloads while diagnosing validation failures.
- Keeping dual-write paths indefinitely.

## Output Format Expectations

Produce a concise **Contract Evolution Report** containing:

1. **Scope:** Contract, owner, producers, consumers, transport, and current versions.
2. **Proposed Change:** Field-level and semantic differences.
3. **Compatibility Decision:** Backward, forward, full, or breaking, with evidence.
4. **Evolution Plan:** Strategy, rollout order, migration, rollback, and deprecation dates.
5. **Validation Evidence:** Registry results, contract tests, fixtures, and observed drift.
6. **Risks and Exceptions:** Severity, owner, expiry, and mitigation.
7. **Gate Decision:** Pass, conditional pass, or block.
