# Data Contract Specification

## Contract Template

### 1. Identity and Purpose

- Contract ID and semantic version
- Lifecycle: draft, active, deprecated, retired
- Business purpose and authoritative source
- Transport, topic/endpoint/dataset, and environments
- Data classification, residency, retention, and deletion obligations

### 2. Ownership

- Accountable producer owner and escalation contact
- Schema steward and security/privacy reviewer
- Named consumer owners
- Support hours, incident path, and decision authority

### 3. Service-Level Objectives

For each SLO, define the measurement point, clock, window, objective, maximum breach, exclusions, and owner.

- **Freshness:** source commit to validated consumer availability
- **Completeness:** expected records/transactions represented
- **Accuracy:** values satisfying semantic/reconciliation rules
- **Availability:** successful reads/publications
- **Latency:** request or publication percentiles

### 4. Schema Definition

Document fields, types, logical types, requiredness, null semantics, defaults, units, timezone, identifier scope, enum behavior, sensitivity, and examples. Link one canonical Avro, Protobuf, or JSON Schema artifact and record its fingerprint.

### 5. Quality Rules

Each rule needs an ID, expression, severity, scope, evaluation cadence, threshold, owner, and failure action. Cover uniqueness, ranges, nulls, referential integrity, reconciliation, allowed values, and cross-field invariants.

### 6. Producer Guarantees

State ordering, delivery semantics, idempotency/event key, update/delete behavior, late-data policy, replay window, schema registration timing, and incident notification obligations.

### 7. Consumer Registry

For every consumer record service/team, contact, environment, schema version, purpose, criticality, release cadence, replay use, and last-observed usage. Include indirect exports and batch jobs.

### 8. Change Policy

- Compatibility mode and transitivity
- Approval roles and CI evidence
- Semantic change review
- Producer/consumer rollout order
- Breaking-change exception process
- Minimum notice and support periods

### 9. Deprecation Lifecycle

Define announce, adoption, dual-support, read-only/frozen, removal, and cleanup milestones. Retirement requires usage evidence, replay-window analysis, archived schema artifacts, and final owner approval.

## Fully Worked Example

```yaml
contract-id: commerce.order-created
version: 2.1.0
lifecycle: active
purpose: Authoritative notification that an order transaction committed.
owner:
  team: checkout-platform
  contact: checkout-oncall@example.com
transport:
  type: kafka
  subject: commerce.order-created-value
  topic: commerce.order-created.v2
classification: confidential
retention: P30D
schema-ref: schemas/order-created-2.1.0.avsc
schema-fingerprint: sha256:2c3b-example
sla:
  freshness:
    objective: 99.9% under 60 seconds over 30 days
    measurement: source_commit_time to broker_publish_time
    maximum-staleness: 10 minutes
  completeness:
    objective: 99.99% of committed orders represented
    reconciliation: hourly against order transaction ledger
  availability:
    objective: 99.95% monthly publish success
schema-semantics:
  order_id:
    type: string
    required: true
    meaning: Globally unique immutable order identifier.
    classification: internal
  occurred_at:
    type: timestamp-millis
    required: true
    timezone: UTC
    meaning: Source database commit time.
  total_minor_units:
    type: long
    required: true
    unit: ISO-4217 currency minor unit
  currency:
    type: string
    required: true
    constraints: ISO-4217 uppercase code
  customer_id:
    type: [null, string]
    default: null
    classification: confidential
quality-rules:
  - id: order-id-present
    expression: order_id is not null and order_id != ''
    severity: error
    threshold: 100%
    action: quarantine-and-page
  - id: total-nonnegative
    expression: total_minor_units >= 0
    severity: error
    threshold: 100%
    action: quarantine
  - id: ledger-reconciliation
    expression: published_order_count == committed_order_count
    cadence: hourly
    threshold: 99.99%
    action: page-and-replay
producer-guarantees:
  delivery: at-least-once
  ordering: per order_id
  idempotency-key: event_id
  deletes: not applicable; cancellations are separate events
  replay-window: P30D
  schema-registration: before producer deployment
consumers:
  - name: fulfillment-router
    owner: fulfillment-platform
    contact: fulfillment-oncall@example.com
    version: '>=2.0.0 <3.0.0'
    criticality: tier-1
    purpose: Starts warehouse allocation.
    replay: true
  - name: revenue-lakehouse
    owner: finance-data
    contact: finance-data@example.com
    version: '>=2.1.0 <3.0.0'
    criticality: tier-2
    purpose: Builds recognized revenue facts.
    replay: true
compatibility:
  mode: BACKWARD_TRANSITIVE
  semantic-review-required: true
  breaking-change-approval: architecture-council
change-policy:
  notice-period: P30D
  minimum-dual-support: P60D
  required-evidence:
    - registry compatibility result
    - producer and consumer contract tests
    - replay fixture validation
    - rollback plan
deprecation:
  previous-version: 1.8.3
  announcement-date: 2026-01-15
  end-of-support: 2026-04-15
  removal-conditions:
    - no observed v1 consumers for 30 days
    - retained v1 events are outside replay requirements
    - all tier-1 owners approve
```

## Review Checklist

- Purpose and authority are unambiguous.
- Every field has semantic meaning, not only a wire type.
- SLOs specify clocks, windows, and measurement points.
- Quality failures have deterministic actions and owners.
- All consumers, including offline and replay consumers, are registered.
- Compatibility policy matches deployment and retained-data reality.
- Sensitive data rules propagate to logs, DLQs, fixtures, and lineage.
- Deprecation has dates, evidence, and a final cleanup owner.
