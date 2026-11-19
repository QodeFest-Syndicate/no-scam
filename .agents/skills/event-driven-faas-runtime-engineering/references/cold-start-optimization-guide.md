# Cold-Start Optimization Guide

A cold start includes platform provisioning, runtime bootstrap, dependency loading, and application initialization before handler work begins. Optimize only after separating cold INIT time from handler duration and validating the target percentile under realistic memory, architecture, networking, and concurrency settings.

## Measurement Method

1. Define a representative event and deployment artifact.
2. Record artifact compressed/uncompressed size, runtime, architecture, memory, region, network mode, and deployment version.
3. Force or identify cold instances using platform telemetry rather than adding production-only behavior.
4. Capture at least 100 cold and 1,000 warm invocations per variant.
5. Compare p50, p95, and p99 INIT, handler, and total duration.
6. Track errors, peak memory, CPU allocation, downstream connection time, and cost.
7. Change one variable per experiment and preserve raw evidence.

For AWS Lambda, parse `INIT_REPORT` where available and distinguish suppressed init after failures. For Java SnapStart, measure restore duration and post-restore hook work separately.

## Cross-Runtime Priorities

| Technique | Primary benefit | Risk |
|---|---|---|
| Remove unused dependencies | Less download and initialization | Accidental removal of dynamic assets |
| Lazy-load optional paths | Faster common-path init | First use becomes slower; concurrency safety |
| Reuse initialized clients | Avoid repeated handshakes | Stale connections or tenant credential leakage |
| Increase memory/CPU | Faster bootstrap | Higher configured cost |
| Provisioned concurrency | Predictable latency | Idle cost and scaling configuration |
| Smaller architecture-native artifacts | Faster load | Build matrix complexity |
| Avoid startup network calls | Removes variable latency | Configuration may need another delivery path |

## Python

- Package only imported modules and required native libraries.
- Prefer targeted imports over importing broad framework namespaces.
- Move optional scientific, image, or browser libraries inside the branch that uses them.
- Avoid module-level discovery, large configuration parsing, and eager ORM model registration.
- Initialize tenant-neutral SDK clients outside the handler, with bounded pools and timeouts.
- Remove tests, bytecode caches, package metadata, docs, and unused shared objects only after import tests.
- Consider layers only for governance or sharing; extra mount/import paths do not inherently reduce initialization.
- Compile native wheels for the exact runtime, OS, and architecture.

Measure import time with `python -X importtime` in a matching container, then confirm on the provider.

## Node.js

- Bundle each handler with tree-shaking and production conditions.
- Prefer modular service clients and direct module entry points.
- Exclude dev dependencies, source maps where policy allows, tests, and unused locales.
- Avoid eagerly importing browser automation, image processing, or entire cloud SDK suites.
- Keep top-level await bounded and avoid network access during module evaluation.
- Reuse safe HTTP agents and clients; cap sockets per execution environment.
- Compare CommonJS and ESM only with real runtime measurements; module format alone is not a guarantee.
- Audit dynamic `require`/import patterns because they can defeat tree-shaking.

Use bundle metafiles to identify unexpectedly retained modules and duplicate versions.

## Go

- Build one small binary for the target architecture with reproducible flags.
- Remove debug symbol data only when operational symbolication requirements remain satisfied.
- Avoid expensive `init()` functions, large embedded assets, and eager configuration discovery.
- Reuse clients initialized with safe timeouts; keep request and tenant state local.
- Inspect binary contributors using `go tool nm` and dependency graphs using `go mod graph`.
- Avoid CGo unless required; it increases build and runtime compatibility complexity.
- Go often has fast bootstrap, so prioritize network initialization and artifact transfer evidence.

## Java

- Minimize classpath size and framework auto-configuration.
- Use class-data sharing, ahead-of-time processing, or native images when compatibility and build cost justify them.
- For AWS Lambda SnapStart, initialize stable resources before snapshot and refresh unique, expiring, random, network, and credential state after restore.
- Register before-checkpoint and after-restore hooks deliberately.
- Never snapshot request state, tenant credentials, unique IDs, or open connections without a restore strategy.
- Tune JVM memory for the provider allocation and verify garbage-collector behavior.
- Provisioned concurrency may be simpler than deep framework changes for a small latency-sensitive fleet.

### SnapStart Verification

Test uniqueness of random values, DNS refresh, TLS sessions, credential expiry, database reconnection, and time-sensitive caches after restore. Compare publish-time snapshot failures, restore duration, and first-handler duration.

## Connection Pooling

- Initialize pools outside handlers only when thread-safe and tenant-neutral.
- Size pools per execution environment, not from total service traffic.
- Set connect, read, operation, and idle timeouts below function timeout.
- Validate stale sockets and retry connection establishment only for transient failures.
- Use managed database proxies when burst concurrency can exhaust server connections.
- Never cache tenant authorization decisions or request credentials globally.

## Provisioned Concurrency Decision

Use provisioned concurrency when a measured cold tail violates a user-facing SLO and optimization alone is insufficient. Determine the minimum warm capacity from steady arrival rate, execution duration, burst profile, and scaling lag. Alert on spillover invocations and utilization. Schedule capacity for predictable peaks and include idle cost in the decision.

## Artifact Pruning Checklist

- Production dependencies only.
- One version of each dependency where possible.
- No tests, examples, docs, caches, or local tooling.
- Required certificates, timezone data, schemas, and native libraries preserved.
- Dynamic imports exercised in packaging tests.
- Artifact checksum and dependency inventory recorded.
- Cold and warm smoke invocations pass after pruning.

## Exit Criteria

An optimization is accepted only when it improves the target percentile without increasing error rate, correctness risk, memory failures, downstream saturation, or operational complexity beyond the agreed budget.