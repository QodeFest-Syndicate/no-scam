# OpenTelemetry Instrumentation Guide

## Instrumentation contract

Treat telemetry names, units, attributes, and privacy classifications as versioned interfaces. Every service should set `service.name`, `service.version`, `deployment.environment.name`, and a stable instance identifier. Prefer OpenTelemetry semantic conventions; custom attributes should use an organization namespace. Never attach secrets, request bodies, email addresses, or unbounded identifiers.

Instrument boundaries first: inbound HTTP/RPC, outbound dependencies, message production and consumption, database calls, and scheduled work. Add internal spans only when they answer an operational question.

## SDK setup

### Python

Install `opentelemetry-sdk`, the OTLP exporter, and relevant instrumentation packages. Create a `TracerProvider` with a `Resource`, use a batch span processor, and register an OTLP exporter. In production, send signals to a local or regional Collector rather than directly to a vendor. Initialize before importing auto-instrumented frameworks.

Auto-instrument with `opentelemetry-instrument python app.py`. Pin instrumentation versions and explicitly exclude health endpoints. For manual work:

```python
with tracer.start_as_current_span("orders.validate") as span:
    span.set_attribute("order.item_count", len(items))
    try:
        validate(items)
    except Exception as exc:
        span.record_exception(exc)
        span.set_status(Status(StatusCode.ERROR))
        raise
```

### Node.js

Install `@opentelemetry/sdk-node`, auto-instrumentations, and an OTLP exporter. Start the SDK in a preload module before application modules load. Use `tracer.startActiveSpan()` for manual spans and always close the span in `finally`. Avoid losing context through callback libraries; verify `AsyncLocalStorage` propagation under real concurrency.

### Go

Create an `sdktrace.TracerProvider` with resource, sampler, batcher, and OTLP exporter. Set it globally and call `Shutdown` with a bounded context. Pass `context.Context` through every instrumented boundary. Use `tracer.Start(ctx, name)` and defer `span.End()`. Never replace a received context with `context.Background()` inside a request path.

### Java

The Java agent is the fastest baseline: start with `-javaagent:opentelemetry-javaagent.jar` and configure exporters through environment variables. Add `opentelemetry-api` for manual spans or business attributes. For Spring and executor work, verify that context crosses custom thread pools. Use the SDK directly only when agent configuration cannot express the required controls.

## Context propagation

Use W3C Trace Context (`traceparent`, `tracestate`) across HTTP and an approved propagator for messaging metadata. Baggage is not a general payload channel: allowlist keys, cap sizes, and treat inbound baggage as untrusted. Consumers should create `CONSUMER` spans; producers create `PRODUCER` spans. Use span links for batch, fan-in, replay, and delayed processing where a single parent is misleading.

Propagation verification checklist:

- Trace ID remains stable across every synchronous hop.
- Producer and consumer relationships are visible for queues.
- Sampling flags propagate consistently.
- Invalid headers produce a new trace without failing the request.
- Background tasks capture context before the request scope ends.
- Logs inside spans include the correct trace and span IDs.

## Metrics

- **Counter:** cumulative monotonic events such as requests, errors, retries, and bytes sent.
- **Up-down counter:** active work, connections, or queue consumers that can rise and fall.
- **Histogram:** latency, payload size, queue age, and batch size. Choose boundaries around SLOs and operational decisions.
- **Observable gauge:** current state sampled through a callback, such as temperature or queue depth. Do not use a gauge for events.

Keep attribute cardinality bounded. Route templates are safe; raw URLs are not. Record units using UCUM conventions. Histograms should preserve distributions rather than publishing client-calculated percentiles that cannot be aggregated.

## Log correlation

Emit structured logs with timestamp, severity, event name, service, environment, and version. Enable trace/span ID injection through the language logging integration. Record an exception once at its authoritative handling boundary; downstream summaries should reference its error code. Redact before export, and test redaction with representative nested payloads.

## Exporters and Collector

### OTLP

OTLP/gRPC is efficient for stable internal networks; OTLP/HTTP is convenient through proxies and serverless gateways. Configure endpoint, TLS, authentication headers, compression, timeouts, and retry policy. Export asynchronously and bound queues to avoid application memory exhaustion.

### Jaeger

Prefer OTLP from applications to a Collector, then export to Jaeger. Direct legacy Jaeger exporters reduce portability. Map service resources consistently and validate clock synchronization before diagnosing span ordering.

### Prometheus

Expose or translate OpenTelemetry metrics through a Collector Prometheus exporter/receiver. Prometheus pulls metrics, while OTLP commonly pushes them; choose a single ownership path to avoid double counting. Review cumulative-to-delta conversion and histogram compatibility.

## Collector baseline

A production pipeline generally uses receivers, `memory_limiter`, filtering/redaction, batching, and one or more exporters. Add tail sampling only after sizing its state and failure behavior. Monitor accepted, refused, dropped, queued, retried, and failed telemetry. A healthy application with a blind Collector is not observable.

## Sampling

Head sampling gives predictable cost but cannot know final trace outcome. Parent-based sampling keeps a distributed decision coherent. Tail sampling can retain errors and slow traces but needs complete traces, memory, and decision latency. Preserve an unbiased baseline sample alongside policy samples so rates remain statistically interpretable.

## Validation and rollout

1. Capture a golden request across all boundaries.
2. Confirm names, kinds, timestamps, statuses, and parentage.
3. Force an error, timeout, retry, and asynchronous path.
4. Confirm metrics reconcile with request logs.
5. Measure telemetry CPU, memory, network, and storage cost.
6. Test exporter outage and queue saturation.
7. Deploy progressively and compare signal continuity by version.

Instrumentation is complete only when operators can move from an SLO symptom to a representative trace, correlated logs, the responsible deployment, and an actionable owner.