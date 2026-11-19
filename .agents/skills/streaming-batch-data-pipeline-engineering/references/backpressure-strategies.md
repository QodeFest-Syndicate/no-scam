# Backpressure Strategies

## Pressure Model

Backpressure is a control signal from a constrained downstream stage to upstream producers. Measure it with queue age, records/bytes in flight, broker lag, processing latency, retry rate, sink saturation, checkpoint duration, and time-to-retention-loss. Scale only after locating the bottleneck.

A safe design defines bounded memory, a durable overflow path, admission behavior, retry budgets, and recovery order. Unbounded queues defer failure while increasing recovery time.

## Strategy Matrix

| Strategy | Best when | Main trade-off | Kafka hint | Flink hint | Spark hint |
|---|---|---|---|---|---|
| Rate limiting | Ingress can be shaped | Adds producer latency | Producer/client quotas | Async I/O capacity, source rate limit | Trigger interval, max offsets |
| Durable buffering | Bursts exceed steady capacity | Storage cost and delayed failure | Retained topic | Durable checkpoints/savepoints | Kafka/object-store landing |
| Consumer throttling | Sink needs protection | Lag grows upstream | Pause/resume partitions | Backpressure propagates through operators | Limit input rows per batch |
| Partition flow control | Skew or isolated hot keys | Ordering and fairness complexity | Pause individual partitions | Keyed operator capacity | Repartition and skew handling |
| Dead-letter routing | Deterministic poison records | Separate remediation lifecycle | Retry/DLQ topics | Side outputs | Error/quarantine tables |
| Circuit breaker | Dependency is failing | Temporary unavailability | Stop consumption or publishing | Guard async sink calls | Abort/retry bounded batches |

## Rate Limiting

Use token-bucket or leaky-bucket controls when producers can slow down without violating correctness. Budget by both records and bytes because payload growth can saturate networks before event rate changes.

- **When to use:** shared brokers, expensive APIs, warehouse load windows, or tenant fairness.
- **Trade-offs:** protects capacity but increases end-to-end latency; local limiters need coordination for global limits.
- **Implementation:** set a sustainable baseline below measured sink capacity, permit bounded bursts, return retry-after signals, and expose rejected/delayed counts.
- **Kafka:** combine broker quotas with client-side pacing; avoid retries that amplify traffic.
- **Flink:** rate-limit sources or async requests rather than sleeping operator threads.
- **Spark:** cap `maxOffsetsPerTrigger` and tune the trigger interval from observed batch completion time.

## Buffering with Spillover

Use memory only for small transient jitter. Spill overflow to a durable broker, local disk with recovery metadata, or object storage when loss is unacceptable.

- **When to use:** bursty sources with adequate long-term drain capacity.
- **Trade-offs:** absorbs bursts but can hide chronic under-capacity; spill replay complicates ordering and deduplication.
- **Implementation:** define byte/record/age limits, disk quotas, checksums, segment lifecycle, and high-water alerts. Preserve event IDs and original ordering metadata.
- **Kafka:** retention is the primary durable buffer; calculate retention from peak lag growth and recovery time.
- **Flink:** prefer managed state and checkpointing over ad hoc process-local queues.
- **Spark:** land immutable input before transformation and make each micro-batch replayable.

## Consumer Throttling

Reduce polling, prefetch, batch size, or concurrency when downstream latency or error rate crosses a threshold.

- **When to use:** databases and APIs whose latency sharply degrades near saturation.
- **Trade-offs:** broker lag increases; overreactive controllers oscillate.
- **Implementation:** use additive increase/multiplicative decrease, hysteresis, and minimum hold periods. Commit offsets only after durable sink writes.
- **Kafka:** retain heartbeats while partitions are paused; respect `max.poll.interval.ms` and avoid rebalance loops.
- **Flink:** tune network buffers and asynchronous I/O concurrency; inspect task-level busy/backpressured/idle time.
- **Spark:** keep processing time below trigger cadence or intentionally accept bounded catch-up mode.

## Partition-Based Flow Control

Pause only hot or blocked partitions while healthy partitions continue.

- **When to use:** per-key ordering matters and pressure is localized.
- **Trade-offs:** global event-time progress may stall; paused partitions can exceed retention.
- **Implementation:** track lag and oldest age per partition, apply fair scheduling, and resume with bounded batches.
- **Kafka:** use consumer pause/resume without dropping assignment; store per-partition progress.
- **Flink:** fix key skew with salting or two-stage aggregation when business ordering permits.
- **Spark:** repartition using a measured key distribution; isolate exceptional tenants or keys.

## Dead-Letter and Quarantine Routing

Route records that fail deterministic validation or exceed a bounded retry budget out of the main flow.

- **When to use:** malformed schemas, constraint violations, unsupported values, and poison records.
- **Trade-offs:** maintains throughput but creates a second correctness workflow; a DLQ is not disposal.
- **Implementation:** include original payload or secure pointer, source position, schema version, error class, attempts, first/last failure time, trace ID, and remediation owner.
- **Kafka:** separate delayed-retry topics from terminal DLQ topics; do not loop a DLQ directly to the source topic.
- **Flink:** use side outputs and checkpoint their sink consistently.
- **Spark:** write quarantine rows transactionally with batch/run identity.

## Circuit Breakers

Open the circuit after a threshold of dependency failures, fail fast during a cool-down period, and probe recovery in half-open state.

- **When to use:** dependencies fail slowly or retries worsen an outage.
- **Trade-offs:** deliberate temporary unavailability; state must be coordinated across workers when a shared dependency is protected.
- **Implementation:** classify retryable failures, cap total retry time, add jitter, and preserve input durably before acknowledging it.
- **Kafka:** pause affected partitions or consumer groups while maintaining membership.
- **Flink:** wrap async sinks with bounded retries and surface breaker state as metrics.
- **Spark:** fail a batch rather than partially commit when atomicity is required; use idempotent retry after recovery.

## Control Threshold Template

| Signal | Warning | Critical | Automated action |
|---|---:|---:|---|
| Capacity utilization | 70% | 85% | Reduce ingress or scale within sink limits |
| Oldest lag age | 50% freshness SLO | 80% freshness SLO | Page owner and enter catch-up mode |
| In-flight bytes | 60% bound | 85% bound | Pause intake and spill durably |
| Sink p95 latency | 1.5× baseline | 2× baseline | Reduce concurrency/open breaker |
| Retry amplification | 1.2× input | 1.5× input | Quarantine poison records |

Calibrate thresholds with load tests and error budgets; fixed examples are not production defaults.

## Failure Drill

1. Saturate the sink and verify upstream pressure propagates without memory exhaustion.
2. Confirm lag remains within retention and freshness recovery objectives.
3. Inject poison records and prove bounded retry plus quarantine.
4. Restart processors and verify checkpoints, queue state, and idempotent outputs.
5. Measure drain time after recovery and compare it with the capacity estimate.
