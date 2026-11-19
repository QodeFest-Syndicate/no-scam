# Change Data Capture Patterns Catalog

## Design Baseline

A CDC design is complete only when it defines the initial snapshot boundary, ordering key, delete representation, schema-change policy, offset durability, replay window, and reconciliation procedure. Preserve source transaction metadata whenever downstream consumers need transaction-consistent views.

## Log-Based Capture

**Architecture:** database transaction log or WAL → connector (for example Debezium or AWS DMS) → durable broker → idempotent consumers. A consistent snapshot is paired with the exact log position from which streaming resumes.

- **Latency:** commonly sub-second to several seconds.
- **Consistency:** strongest general-purpose option; preserves commit order per log partition and can preserve transaction boundaries.
- **Source impact:** low steady-state query load, but snapshots and log retention require capacity.
- **Failure modes:** expired source logs, offset corruption, connector split-brain, snapshot/stream gaps, schema history loss, and connector lag exceeding retention.
- **Recovery:** stop competing writers, restore offsets and schema history, resume from a retained position, or take a new consistent snapshot. Deduplicate overlap by stable key plus source position.
- **Implementation notes:** monitor log head distance, oldest retained position, heartbeat age, transaction size, and connector task ownership. Commit broker offsets only after durable publication.

**Debezium:** best when Kafka-compatible envelopes, broad database support, and explicit before/after images are useful. Retain the schema history topic and connector offsets as production state.

**AWS DMS:** useful for managed AWS replication and heterogeneous migrations. Validate LOB handling, DDL coverage, task restart position, and CloudWatch lag semantics before relying on it as the only recovery signal.

## Trigger-Based Capture

**Architecture:** database triggers write change rows into an outbox/audit table in the same transaction; a relay publishes and marks or removes delivered rows.

- **Latency:** low seconds, driven by relay polling or notifications.
- **Consistency:** atomic with the source transaction when the trigger and business write share a transaction.
- **Source impact:** write amplification, additional locks, table growth, and trigger execution latency.
- **Failure modes:** disabled or bypassed triggers, recursive triggers, outbox growth, relay duplicate publication, trigger drift after DDL, and incomplete bulk-load behavior.
- **Recovery:** replay unacknowledged outbox rows; reconcile source and outbox by transaction/key ranges. Relay publication must be idempotent because publish-then-mark can repeat.
- **Implementation notes:** keep trigger logic minimal, index relay predicates, partition or archive the outbox, and alert on oldest unpublished row age.

Use an application transactional outbox instead of generic triggers when event semantics should be owned by domain code rather than inferred from row changes.

## Timestamp/Watermark Capture

**Architecture:** periodically query rows where `(updated_at, tie_breaker)` is greater than the stored watermark, then persist output and the next watermark atomically.

- **Latency:** polling interval plus query and sink time; usually seconds to minutes.
- **Consistency:** at-least-once with a composite stable watermark and overlap window. Deletes are invisible unless represented by soft-delete fields or tombstone tables.
- **Source impact:** indexed range scans; poor indexes can degrade the primary workload.
- **Failure modes:** clock skew, equal timestamps, mutable timestamps, precision truncation, late commits, missed deletes, and watermark advancement before sink durability.
- **Recovery:** rewind the watermark by a bounded overlap and deduplicate downstream. Rebuild from a full snapshot when the safe overlap is unknown.
- **Implementation notes:** use database-generated commit/update time, a deterministic tie-breaker, half-open ranges, and an overlap larger than maximum transaction delay.

This is a fallback when log access is unavailable, not a substitute for log capture when complete delete and ordering semantics are required.

## Diff-Based Capture

**Architecture:** periodically snapshot source state, compare hashes or keyed records against the previous snapshot, and emit inserts, updates, and deletes.

- **Latency:** snapshot interval plus comparison time; typically minutes to hours.
- **Consistency:** reflects differences between snapshots, not intermediate transitions. A transactionally consistent snapshot is required for reliable point-in-time comparison.
- **Source impact:** potentially high full-table read, network, storage, and compute costs.
- **Failure modes:** inconsistent snapshots, hash collisions, normalization differences, missed transient changes, partition inventory gaps, and large delete storms from incomplete input.
- **Recovery:** retain both snapshots and comparison manifests; rerun affected partitions deterministically. Quarantine suspicious delete ratios.
- **Implementation notes:** partition snapshots, canonicalize values before hashing, store counts and checksums, and require completeness checks before applying deletes.

## Decision Matrix

| Criterion | Log-based | Trigger/outbox | Timestamp | Diff-based |
|---|---|---|---|---|
| Typical latency | Sub-second–seconds | Seconds | Seconds–minutes | Minutes–hours |
| Inserts/updates/deletes | Complete | Complete if designed | Deletes need explicit marker | Complete between snapshots |
| Transaction ordering | Strong | Strong at write boundary | Limited | None between snapshots |
| Source privileges | Log/replication access | DDL and trigger access | Read access | Broad read access |
| Source overhead | Low steady state | Write amplification | Query load | High scan load |
| Schema evolution | Connector-dependent | Trigger maintenance | Query maintenance | Comparator maintenance |
| Replay | From retained log | From retained outbox | Watermark rewind | Snapshot rerun |
| Best fit | Production streams | Domain events or restricted logs | Simple incremental extracts | Legacy/no-watermark sources |

## Selection Procedure

1. Require complete deletes, low latency, and ordered changes: choose log-based capture.
2. Require domain-authored events atomically with writes: choose transactional outbox.
3. Lack log/trigger access but have a trustworthy immutable watermark: choose timestamp capture.
4. Lack reliable change metadata and can tolerate batch latency: choose diff-based capture.
5. Reject any option whose worst-case outage exceeds its retained replay history.
6. Prove snapshot-to-stream handoff, duplicate handling, and reconciliation in a failure test.

## Recovery Checklist

- Record source position, connector version, schema version, and output offsets.
- Stop or fence duplicate connector instances before restoring state.
- Confirm retained source history covers the restart position.
- Replay into an idempotent sink or isolated recovery topic.
- Reconcile counts, key ranges, deletes, and checksums before cutover.
- Document any interval that cannot be reconstructed and its consumer impact.
