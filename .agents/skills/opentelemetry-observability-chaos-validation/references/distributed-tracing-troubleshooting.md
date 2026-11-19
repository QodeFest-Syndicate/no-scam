# Distributed Tracing Troubleshooting

## Triage sequence

1. Confirm applications are creating spans.
2. Confirm exporters accept and queue them.
3. Confirm the Collector receives, processes, and exports them.
4. Confirm the backend ingests and indexes them.
5. Confirm queries use the right time range, environment, service, and tenant-safe scope.

At each hop compare accepted, dropped, retried, rejected, and exported counts. Do not tune sampling until transport loss is excluded.

## Missing spans

### No trace at all

Check SDK initialization order, exporter endpoint and protocol, TLS/authentication, resource configuration, process shutdown flushing, and backend time filters. Auto-instrumentation must load before framework libraries. In short-lived jobs, explicitly force flush or shut down with a bounded timeout.

### Partial traces

Common causes include:

- Sampling decisions not propagated or parent-based sampling disabled.
- A process exits before the batch processor flushes.
- Collector queue overflow, memory limiter refusal, or exporter retry exhaustion.
- Tail sampler deciding before all spans arrive.
- Backend span limits, timestamp rejection, or retention differences.
- Async work detached from captured context.

Compare expected boundary spans against actual service topology. Search raw Collector debug output in a safe non-production environment. Verify clocks; spans outside accepted time bounds can appear missing.

### Missing parent gap

If a span names a parent ID that is absent, determine whether the parent was sampled, dropped, or exported elsewhere. Ensure propagators agree on W3C Trace Context. Proxies must forward `traceparent`; message clients must inject into and extract from carrier metadata. Do not create a new root when valid remote context exists.

## Broken context propagation

Symptoms include a new trace per service, logs with empty trace IDs, or consumers unrelated to producers.

- **HTTP:** confirm case-insensitive header forwarding and no gateway allowlist strips trace headers.
- **gRPC:** inject/extract metadata and preserve context through interceptors.
- **Messaging:** use producer/consumer semantic conventions; represent batch relationships with links when multiple parents exist.
- **Executors:** capture context before submitting work and attach/detach it around execution.
- **Promises/callbacks:** verify runtime context manager compatibility under concurrency.
- **Retries:** child attempts should remain under the logical operation and record retry events/attributes.

Build one synthetic golden path and assert one trace ID across each expected hop after every framework or proxy upgrade.

## Incorrect durations or ordering

Negative or implausible durations usually indicate clock skew, mixed timestamp units, spans ended twice, or a span created after work completed. Synchronize hosts and prefer monotonic clocks inside SDKs. Parent spans may finish before asynchronous children legitimately; model detached work with links when lifecycle parentage is misleading.

## Error status problems

OpenTelemetry status should represent operation outcome, not merely HTTP class. Instrumentation may leave status unset for success. Record exceptions and set error status at the authoritative span; avoid marking every ancestor error without added information. Validate framework mappings for canceled requests, expected 4xx responses, and retries that ultimately succeed.

## Sampling strategy tuning

### Head sampling

Decision occurs at trace start. It is cheap, predictable, and easy to propagate, but cannot know final latency or error. Use parent-based probabilistic sampling and keep a stable unbiased rate. Force-sampling every endpoint independently breaks trace coherence.

### Tail sampling

Decision occurs after collecting spans. It can retain errors, high latency, or selected attributes, but needs memory, complete trace routing, and a wait period. Size by concurrent traces and worst-case spans, not average traffic. Route all spans for a trace to the same decision point. Monitor late spans and policy overlap.

### Practical policy

Retain all rare critical errors, a high fraction of slow traces, targeted debug cohorts with strict expiry, and an unbiased baseline. Cap each policy to prevent an outage from multiplying telemetry cost. Record effective sampling probability when using traces for rate estimation.

## Trace storage optimization

- Drop low-value span events and redundant attributes before export.
- Normalize route templates and reject high-cardinality raw URLs.
- Sample health checks and routine successful polling aggressively.
- Shorten retention for verbose traces; preserve derived metrics longer.
- Use tail policies only for questions worth their state and cost.
- Apply per-service span limits and detect truncation.
- Separate searchable indexed attributes from stored payload attributes.
- Estimate bytes per trace × traces per second × retention before launch.

Never solve cost solely by removing all successful traces; that destroys baseline comparison and capacity analysis.

## Correlating traces, logs, and metrics

Use the same service, environment, version, region, and stable resource attributes across signals. Inject trace and span IDs into structured logs. Configure histogram exemplars so a latency or error bucket links to representative traces. Annotate dashboards with deployments and feature changes.

Investigation flow:

1. Start from user-impacting SLI and identify time and failure domain.
2. Open an exemplar or search representative trace.
3. Find the slow/error span and inspect dependency timing.
4. Pivot to logs using trace ID, not broad text alone.
5. Compare saturation, queue, and dependency metrics.
6. Check deployment version and configuration change.
7. Preserve a trace/log/query link in the incident timeline.

## Collector diagnostics

Monitor receiver accepted/refused items, processor drops, batch size, memory limiter actions, queue occupancy, send failures, retries, and backend rejection. Use persistent queues where loss tolerance and environment justify them. A retry queue must be bounded; otherwise a backend outage can exhaust Collector memory or disk.

## Symptom matrix

| Symptom | Likely causes | First checks |
|---|---|---|
| One service absent | SDK load order, exporter config, filter | SDK self-diagnostics and Collector receiver counts |
| Trace splits at gateway | Header stripping, propagator mismatch | Capture sanitized inbound/outbound `traceparent` |
| Consumers are roots | Carrier extraction absent | Messaging instrumentation and span links |
| Errors not retained | Head sampling or tail policy mismatch | Sampling flags and policy metrics |
| Spans arrive late | Batch/export queue, clock, tail wait | Queue age and timestamps |
| Search cost is high | Cardinality, verbose spans, retention | Attribute and bytes-per-trace inventory |

## Verification checklist

- Golden path includes every expected boundary.
- Error, timeout, retry, cancellation, and async cases are represented.
- Parentage and links match execution semantics.
- Sampling is coherent and measurable.
- Exporter outage does not break the application.
- Collector loss and backend rejection alert before traces disappear silently.
- Logs and metric exemplars pivot to the same trace.
- Sensitive data and unbounded attributes are absent.

Treat a missing span as a data-pipeline failure with a source, transport, processing, and storage path—not only as an application instrumentation bug.