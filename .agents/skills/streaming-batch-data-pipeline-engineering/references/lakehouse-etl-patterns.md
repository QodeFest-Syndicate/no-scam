# Lakehouse ETL and ELT Patterns

## Medallion Architecture

### Bronze: Immutable Landing

Store source-aligned payloads plus ingestion time, source position, schema ID, content hash, run ID, and security classification. Preserve malformed records in quarantine rather than silently dropping them. Partition primarily by coarse ingestion time or source, not by high-cardinality business keys.

**Contract:** append-only, replayable, access-restricted, and retained for the recovery objective. Bronze is evidence, not a consumer-ready model.

### Silver: Validated and Conformed

Parse types, normalize time zones and units, deduplicate by stable identity plus source version, apply deletes, and attach quality outcomes. Resolve late arrivals deterministically and keep rejected records traceable to bronze.

**Contract:** one canonical record shape, explicit primary key, reproducible transformations, and measurable completeness. Publish only after count, uniqueness, referential, and reconciliation checks pass.

### Gold: Product-Oriented Serving

Create aggregates, dimensional models, feature tables, and domain data products optimized for consumer workloads. Define freshness, query performance, semantic ownership, and deprecation policy.

**Contract:** business semantics and SLOs matter more than source layout. Gold datasets may be rebuilt from silver without source access.

## Incremental Processing

Choose an incremental key that cannot skip valid changes:

1. **Source offset/version:** strongest for CDC and replay.
2. **Event-time watermark:** supports late data with an explicit allowed-lateness window.
3. **Updated timestamp plus tie-breaker:** acceptable only when generated reliably and indexed.
4. **Affected partition manifest:** useful for deterministic batch recomputation.
5. **Content hash:** detects changes when versions are unavailable, at higher compute cost.

Persist the input boundary and output commit atomically or make reruns idempotent. Reprocess a bounded overlap and deduplicate when commit timing can race watermark capture.

### Incremental Merge Pattern

- Read changes between stable start and end positions.
- Normalize and deduplicate within the batch.
- Stage results and validate counts/checksums.
- Merge by key with source sequence conflict handling.
- Commit output and processing position.
- Record lineage and metrics for the exact input interval.

Never let arrival order overwrite a newer source version.

## Merge-on-Read vs Copy-on-Write

| Dimension | Merge-on-read | Copy-on-write |
|---|---|---|
| Write latency | Lower; writes deltas/logs | Higher; rewrites data files |
| Read latency | Higher; merges at read/compaction | Lower; files already reconciled |
| Freshness | Strong for rapid updates | Depends on rewrite cadence |
| Operational cost | Compaction and read tuning | Write amplification |
| Best workload | High update rate, mixed freshness | Read-heavy analytics |
| Failure concern | Uncompacted log growth | Partial rewrite/publication |

Use merge-on-read when update latency dominates and readers can tolerate merge cost. Use copy-on-write when predictable query speed and simple snapshots dominate. Validate engine-specific behavior for deletes, time travel, concurrency, and schema evolution rather than relying only on format labels.

## Partition Pruning Strategy

Partition on columns commonly used in selective predicates and with bounded cardinality, such as event date and coarse region. Keep partition size large enough to avoid metadata and small-file overhead.

- Prefer day over hour until volume proves hour-level partitioning is necessary.
- Avoid user, transaction, or tenant IDs as physical partitions unless tenant isolation and scale justify it.
- Sort or cluster inside partitions for secondary predicates.
- Capture min/max statistics and ensure query predicates preserve pruning.
- Test skew: a logical partition key may still produce one dominant physical partition.
- Evolve partition specs rather than rewriting all history when the table format supports it.

A useful target file size depends on engine and object store; measure scan throughput, open cost, and concurrency. Do not hard-code a universal value.

## Compaction Scheduling

Trigger compaction using observed file counts, average size, delete/update log depth, and query degradation rather than only a clock.

### Policies

- **Continuous/lightweight:** compact hot partitions frequently with bounded resource use.
- **Scheduled:** compact daily or hourly during lower demand for predictable workloads.
- **Threshold-based:** compact when small-file count, delta ratio, or read amplification exceeds limits.
- **Tiered:** compact hot data aggressively and cold data rarely.

### Safe Compaction Procedure

1. Select a fixed table snapshot and candidate partitions.
2. Exclude files already claimed by another compactor.
3. Rewrite deterministically and preserve row-level semantics.
4. Validate counts, keys, checksums, and statistics.
5. Atomically publish the new file set.
6. Retain superseded files through the rollback/time-travel window.
7. Expire files only after reader and regulatory retention checks.

Monitor bytes rewritten, files removed/created, execution time, query latency change, and concurrent-write conflicts.

## Late Data and Corrections

Use event time for business windows and processing time for operations. Store the original event time, source version, ingestion time, and correction identity. Define:

- allowed lateness before normal publication;
- correction window for already published aggregates;
- whether late records update, append adjustment entries, or enter review;
- how downstream caches and exports receive corrections;
- when state can be safely evicted.

## Publication and Recovery

Write into staging or a transactional table snapshot, validate, then atomically publish an alias/snapshot. Record code version, schema version, input positions, table snapshot IDs, and quality results. A failed run must either be invisible or safely repeatable.

### Readiness Checklist

- Bronze can replay the stated recovery window.
- Silver keys, deletes, late data, and deduplication are deterministic.
- Gold ownership and semantic SLOs are explicit.
- Incremental boundaries cannot advance ahead of durable output.
- Partitioning is supported by real query filters and skew measurements.
- Compaction cannot race writers or delete files still visible to readers.
- Backfills use isolated capacity, checkpoints, and reconciliation.
