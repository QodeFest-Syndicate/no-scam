# Breaking Schema Change Playbook

## Entry Criteria

Use this playbook when automated checks or semantic review find that supported producers, consumers, retained data, or replay paths cannot safely use the proposed contract. Do not treat coordinated deployment timing alone as compatibility.

## Phase 1: Impact Assessment

1. Freeze the proposal and assign a migration owner and decision authority.
2. Produce a field-level structural and semantic diff.
3. Inventory direct and indirect consumers, generated clients, exports, caches, replayers, batch jobs, and retained payloads.
4. Record deployed versions, release cadence, criticality, owner, last observed use, and rollback ability.
5. Determine data volume, replay window, retention, backfill cost, and privacy constraints.
6. Simulate producer-first, consumer-first, rollback, delayed-consumer, and old-data replay scenarios.
7. Classify impact: data loss, deserialization failure, semantic error, degraded function, or operational-only.

### Decision Record

Capture contract/subject, old and proposed versions, why additive evolution is insufficient, affected consumers, chosen strategy, risks, approvals, dates, and evidence links.

## Phase 2: Consumer Notification

Notify accountable contacts through a tracked channel. Include:

- exact structural and semantic changes;
- examples of old, transitional, and final payloads;
- impact by consumer and required action;
- test endpoint/topic/artifact and migration tooling;
- dual-support start/end dates;
- dashboards and mismatch/error signals;
- escalation, exception, and rollback process.

Require explicit acknowledgement from tier-1 owners. Non-response is not approval. Publish updates when scope or dates change.

## Phase 3: Choose a Migration Shape

| Situation | Preferred approach |
|---|---|
| New meaning can coexist | Expand–migrate–contract |
| Live traffic needs incompatible representation | Versioned topic/endpoint with adapter |
| Storage must transform | Checkpointed idempotent backfill |
| Writers/readers cannot move together | Bounded dual-write/dual-read |
| Very old consumers cannot change | Compatibility facade with retirement owner |

Define one authoritative representation during transition. Every duplicate path needs idempotency, reconciliation, and an expiration date.

## Phase 4: Build Migration Tooling

Tooling should support dry run, partition/range selection, rate limits, checkpoints, idempotent reruns, progress metrics, error quarantine, and validation-only mode. It must record source version, output version, code version, and exact processed boundaries.

Test with:

- valid and invalid golden fixtures;
- minimum/maximum/null/unknown enum values;
- historical payload versions;
- duplicate and out-of-order events;
- partial failure and restart;
- rollback while mixed versions exist.

## Phase 5: Dual-Version Support

A safe rollout normally follows:

1. Register the new contract under a new versioned identity or compatible expansion.
2. Deploy tolerant readers/adapters.
3. Start shadow conversion and compare outputs without serving them.
4. Enable dual-write or versioned publication for a small cohort.
5. Reconcile counts, keys, values, latency, and error rates.
6. Expand traffic while watching old/new consumer usage.
7. Switch source of truth only after acceptance thresholds hold.
8. Retain the old path for the agreed rollback/support window.

### Acceptance Gates

- compatibility and contract tests pass;
- no unexplained old/new mismatches;
- backfill reconciliation meets completeness/accuracy targets;
- tier-1 consumers confirm production behavior;
- lag, latency, and cost remain within budgets;
- rollback drill succeeds from current migration state.

## Rollback Procedures

Rollback is a designed path, not “redeploy the old version.” Define:

- traffic/alias/topic routing switch;
- whether old writers still receive every required field;
- how new-only writes are converted or preserved;
- how partial backfill outputs are isolated;
- how offsets and checkpoints return without duplication or gaps;
- who authorizes rollback and what signal triggers it.

Before destructive cleanup, rollback may route readers/writers to the old version and replay buffered changes. After information is discarded or old writes stop, use forward-fix unless a verified reverse migration exists.

## Backfill and Reconciliation

Partition by stable keys or time ranges. Publish progress as scanned, converted, validated, failed, and remaining counts. Reconcile:

- total and per-partition counts;
- key sets and duplicate rates;
- checksums or semantic aggregates;
- null/default/enum distributions;
- deletes and tombstones;
- consumer-visible behavior.

Quarantine failures with secure pointers and reasons. Do not advance the completion checkpoint past unaccounted records.

## Phase 6: Cutover

During the change window:

1. Confirm owners, dashboards, rollback operator, and freeze boundaries.
2. Verify latest compatibility, fixtures, and consumer acknowledgements.
3. Record starting offsets, schema IDs, versions, and data snapshots.
4. Shift traffic in bounded increments.
5. Observe deserialization failures, unknown versions, mismatch rate, SLOs, and business invariants.
6. Announce completion only after the soak period and reconciliation gate.

## Phase 7: Post-Migration Cleanup

Cleanup is a separate approved change:

- disable old writes, then old reads;
- verify zero old-version use over the evidence window;
- confirm retained/replay data no longer requires the old reader;
- reserve removed Protobuf numbers and names;
- archive schemas, adapters, fixtures, decisions, and migration evidence;
- remove compatibility exceptions, feature flags, duplicate storage, and alerts;
- update consumer registry and lineage;
- conduct a review of mismatches, incidents, and actual migration cost.

Never delete registry versions solely to make compatibility checks pass.

## Emergency Checklist

If a breaking producer is already live:

1. Stop or roll back incompatible publication if safe.
2. Preserve failing payloads securely and record schema IDs/offsets.
3. Quarantine rather than discard unreadable data.
4. Deploy a compatibility adapter or tolerant reader.
5. Replay from the first affected position and reconcile.
6. Notify consumers with scope, mitigation, and recovery progress.
7. Add the exact payload as a permanent regression fixture.
