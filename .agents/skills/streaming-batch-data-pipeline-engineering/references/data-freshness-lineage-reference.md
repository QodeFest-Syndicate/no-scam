# Data Freshness and Lineage Reference

## Freshness Semantics

Freshness is the age of the newest complete and usable source change represented in a dataset. Distinguish it from pipeline runtime, ingestion lag, and wall-clock age.

Define timestamps explicitly:

- **Event time:** when the business event occurred.
- **Source commit time:** when the system of record committed it.
- **Ingestion time:** when the pipeline durably accepted it.
- **Processing time:** when a transformation handled it.
- **Publication time:** when consumers could query the validated output.

For CDC, end-to-end freshness is normally `now - latest represented source commit time`. For scheduled batches, measure both expected-arrival delay and completion delay so a missing run is not mistaken for fresh empty data.

## Measurement Approaches

### High-Watermark Age

Store the maximum source offset and source commit timestamp included in each output snapshot. This is inexpensive and operationally useful, but a maximum alone can hide gaps. Pair it with completeness checks.

### Sentinel Records

Emit periodic known records at the source and observe arrival through each stage. Sentinels measure actual path latency and detect stalled low-volume pipelines. Keep them identifiable and exclude them from business aggregates.

### Source-to-Sink Reconciliation

Compare counts, key ranges, offsets, checksums, or transaction totals over closed windows. This detects missing data that timestamp-only checks miss, at higher compute cost.

### Per-Partition Freshness

Measure each Kafka partition, source shard, tenant, and destination partition. A global maximum can look healthy while one partition is stalled.

## Freshness SLO Template

| Field | Example meaning |
|---|---|
| Dataset and owner | Accountable product and team |
| Measurement point | Published gold snapshot, not job finish |
| Source clock | Database commit timestamp |
| Objective | 99.5% of 5-minute windows under 10 minutes |
| Maximum staleness | 30 minutes before critical paging |
| Exclusions | Approved source maintenance only |
| Completeness companion | 99.99% records reconciled |
| Recovery objective | Back within SLO in 60 minutes |

Use percentile/window objectives rather than an average. Track error-budget burn over short and long windows to avoid paging on harmless spikes or missing sustained degradation.

## Alert Thresholds

Use layered thresholds calibrated to the SLO:

- **Informational:** watermark age reaches 50% of the freshness objective.
- **Warning:** projected breach based on lag growth and drain capacity.
- **Critical:** objective is breached or retention/recovery margin is endangered.
- **Data-loss risk:** oldest unread position approaches source or broker retention.

Alert on oldest lag age, not only record count. Include dataset, affected partitions, last good position, source rate, processing rate, estimated drain time, recent deployment, and runbook link.

## OpenLineage Metadata

OpenLineage represents runtime lineage through events around **jobs**, **runs**, and **datasets**. Emit START, COMPLETE, FAIL, and ABORT lifecycle events with stable namespaces and names.

Useful facets include:

- schema and dataset version;
- input/output statistics;
- source code location and version;
- SQL or transformation identity, with sensitive literals removed;
- data quality assertions and results;
- nominal schedule time and parent run;
- ownership and documentation;
- processing engine and environment.

Use stable dataset identities independent of temporary paths. Include table snapshot IDs, topic/partition ranges, or object manifests so a run can be reproduced.

## Column-Level Lineage

Capture column lineage when regulated, heavily transformed, or business-critical fields require impact analysis. For each output column, record source columns and transformation class:

- direct copy/rename;
- cast or normalization;
- deterministic expression;
- aggregate/window;
- lookup/join;
- masking/tokenization;
- model-derived or non-deterministic output.

Do not claim exact column lineage from SQL parsing when dynamic SQL, user-defined functions, or external code prevents proof. Mark confidence and unresolved dependencies. Protect lineage metadata because names and expressions can reveal sensitive structure.

## Dashboard Design

### Portfolio View

Show critical datasets by SLO status, owner, freshness, completeness, last successful publication, and active incidents. Sort by consumer impact and error-budget burn, not alphabetically.

### Dataset View

Show source-to-output stage timeline, watermark by partition, input/output rates, queue age, last checkpoint, data-quality results, schema version, and current lineage graph. Overlay deployments and source maintenance.

### Investigation View

Provide exact source offsets, run IDs, table snapshots, failed assertions, retry/DLQ counts, and links to replay controls. Keep operational controls separate from read-only dashboards and require authorization for replay.

## Lineage Quality Controls

- Reject events missing stable dataset or run identity.
- Detect unknown inputs/outputs and cycles caused by naming mistakes.
- Compare declared lineage with observed reads/writes.
- Monitor event delivery completeness and late lineage events.
- Version transformation definitions and schema fingerprints.
- Retain lineage at least as long as governed data and replay evidence require.

## Implementation Checklist

1. Define source, ingestion, and publication clocks.
2. Emit per-partition watermarks and completeness metrics.
3. Set freshness SLOs with warning, breach, and retention-risk thresholds.
4. Instrument job/run/dataset lineage and reproducible input positions.
5. Add column lineage for sensitive and highly transformed outputs.
6. Correlate freshness, quality, schema, deployments, and incidents.
7. Test stalled, partial, empty, delayed, replayed, and backfilled scenarios.
