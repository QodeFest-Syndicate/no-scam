# Feature Store Integration Patterns

## Online and Offline Responsibilities

### Offline Store

Holds historical feature values for training, batch scoring, backfills, and analysis. It needs event timestamps, creation timestamps, entity keys, transformation versions, and reproducible snapshots. Columnar lakehouse or warehouse storage is typical.

### Online Store

Serves the latest approved feature values at low latency. It needs bounded staleness, predictable key lookups, TTL/default behavior, high availability, and tenant-aware authorization. Key-value databases or managed online stores are typical.

The two stores represent one logical feature definition. Separate transformation implementations create training-serving skew.

## Reference Flow

```text
sources -> validated events -> feature transforms -> offline history
                                  |                     |
                                  +-> materialization -> online latest
training set <- point-in-time join --------------------+
request -> entity keys -> feature service -> model endpoint -> prediction log
```

Log feature names/versions and freshness outcomes, not unrestricted sensitive values.

## Feature Definition Contract

Every feature should define:

- stable name and semantic description;
- entity keys and tenant scope;
- event timestamp and creation timestamp;
- source and accountable owner;
- transformation code/version;
- type, range, null/default behavior;
- online/offline availability;
- freshness SLO and TTL;
- privacy, retention, and access policy;
- backfill and deprecation procedure.

Changing meaning under the same feature name is breaking even if the type remains unchanged.

## Point-in-Time Correct Joins

For each training observation at time `t`, join only feature values whose event time is at or before `t`, optionally also requiring creation time before the training cutoff. This prevents future information from leaking into training.

### Safe Procedure

1. Preserve observation event time and entity key.
2. Deduplicate feature rows by entity/event time using source version.
3. Join the latest eligible feature value per entity at or before observation time.
4. Apply TTL and missing-value policy as it would have applied online.
5. Record feature-view version and source snapshot.
6. Test with deliberately late and future-dated records.

A simple join to the current dimension table is not point-in-time correct.

## Freshness and Consistency

Distinguish:

- **missing:** no value exists for the entity;
- **late:** expected source update has not arrived;
- **stale:** value age exceeds its SLO/TTL;
- **invalid:** value violates type or quality rules;
- **version mismatch:** serving used a different feature definition.

Use event timestamps for business freshness and ingestion/materialization timestamps for operational lag. Alert by feature and entity segment; global averages hide stalled partitions.

### Consistency Models

- **Eventual online materialization:** scalable, but predictions may see older data.
- **Request-time computation:** freshest, but raises latency and dependency risk.
- **Push-through:** application writes source and online feature together; requires atomicity or reconciliation.
- **Hybrid:** materialized baseline plus request-time delta for selected features.

Choose based on prediction sensitivity to staleness, not convenience alone.

## Feature Versioning

Version transformations, not just schemas. A deployable model manifest should pin feature view, transformation code, source contract, and default policy.

Use a new version when meaning, window, source, normalization, entity scope, or missing behavior changes. Backfill the new version separately, shadow-serve it, compare online/offline values, and cut over through an alias. Retain the old version for rollback through the support window.

## Serving Architecture Patterns

### Embedded Client

The application/model process calls the online store using a library.

- **Advantages:** lowest network overhead and simple topology.
- **Risks:** language-specific clients, duplicated caching/auth logic, tight coupling to storage.
- **Use when:** one trusted runtime and strict latency dominate.

### Sidecar

A colocated process handles feature lookup, cache, auth, telemetry, and retries.

- **Advantages:** language-neutral local API, isolated release, consistent policy.
- **Risks:** per-pod resource cost, cache consistency, lifecycle coordination.
- **Use when:** several runtimes need uniform low-latency access.

### Remote Feature Service

A shared service resolves feature views and fetches online values.

- **Advantages:** centralized governance, contracts, observability, and evolution.
- **Risks:** network hop, shared blast radius, noisy neighbors, service scaling.
- **Use when:** many teams/models need standardized access and latency budget permits.

| Criterion | Embedded | Sidecar | Remote |
|---|---|---|---|
| Lowest latency | Best | Strong | Depends on network |
| Multi-language consistency | Weak | Strong | Strong |
| Central policy | Weak | Medium | Strong |
| Operational footprint | Client-heavy | Per-workload | Shared service |
| Failure isolation | Per process | Per pod | Shared dependency |

## Online/Offline Parity Test

Sample entity/time pairs and retrieve the value from the historical offline join and reconstructed online serving path. Compare value, type, timestamp, TTL/default decision, and transformation version. Segment mismatches by feature, source partition, and code version.

A high aggregate match can hide a critical low-volume feature; enforce per-feature thresholds.

## RAG and Feature Store Integration

Keep retrieval metadata and predictive features separate unless they share entity keys, freshness, retention, and access controls. Useful integrations include ranking features, personalization, query intent, document quality, and freshness scores.

Apply authorization before retrieval and feature enrichment. Do not let personalization features cross tenant boundaries or expose training-only attributes in prompts. Trace each answer to feature and retrieval version tuples.

## Reliability Checklist

- Online lookups have deadlines, bounded retries, and bulk APIs.
- Missing/stale/invalid values produce explicit telemetry and approved defaults.
- Training datasets use point-in-time joins.
- Materialization is idempotent and source positions are checkpointed.
- Online/offline parity runs continuously on samples.
- Feature releases use shadow comparison and rollback aliases.
- Sensitive values are not copied into logs, prompts, or traces.
