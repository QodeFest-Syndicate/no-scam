# Schema Evolution Strategies

## Compatibility Vocabulary

- **Backward:** new readers consume data written with old schemas.
- **Forward:** old readers consume data written with new schemas.
- **Full:** both directions are supported.
- **Transitive:** compatibility is checked against every supported historical version, not only the latest.

Wire compatibility does not prove semantic compatibility. A field may retain its type while changing unit, meaning, timezone, or identifier scope; treat that as a breaking contract change.

## Strategy Matrix

| Strategy | Producer/consumer coordination | Rollback risk | Runtime cost | Best fit |
|---|---|---|---|---|
| Additive-only | Low | Low | Low | Routine evolution |
| Migration-based | Medium–high | High after destructive cutover | Backfill compute/storage | Stored data and semantic changes |
| Dual-write/dual-read | Medium | Medium until convergence | Highest temporary complexity | Live incompatible migrations |
| Schema-on-read | Low at ingestion | Defers risk to every reader | Repeated parsing/normalization | Raw lakes, exploratory inputs |
| Versioned endpoints/topics | Low across versions | Low, if versions isolated | Parallel operations/support | Intentional semantic breaks |

## Additive-Only Evolution

Add optional/defaulted fields and preserve existing names, types, enum values, and semantics. Readers ignore unknown fields and define behavior for absent values.

- **Compatibility:** usually backward; forward depends on reader unknown-field behavior.
- **Rollback:** straightforward while producers do not rely on new fields.
- **Performance:** minimal overhead; payload and generated-model size grow over time.
- **Use when:** the new concept can be represented without removing or redefining existing data.

**Avro:** add a field with a valid default in the reader schema.

```json
{"name":"currency","type":"string","default":"USD"}
```

**Protobuf:** add a new uniquely numbered optional field; never reuse numbers.

```protobuf
optional string currency = 8;
```

**JSON Schema:** add a property without adding it to `required`, and keep `additionalProperties` behavior compatible.

## Migration-Based Evolution

Transform retained data or in-flight messages into a new representation. Use expand → backfill → validate → cutover → contract.

- **Compatibility:** provided by migration adapters or a temporary superset schema.
- **Rollback:** difficult after old information is discarded; retain source snapshots and reversible mappings.
- **Performance:** backfills consume I/O, compute, and write capacity; throttle around production SLOs.
- **Use when:** keys, units, normalization, encryption, or structure must change across stored history.

Make migrations idempotent, partitioned, checkpointed, observable, and resumable. Record source version and migration code version on each output.

**Example:** change cents integer to decimal amount. Add `amount_decimal`, backfill exactly from cents, migrate readers, switch writers, verify parity, then deprecate cents. Do not overwrite the original field in place.

## Dual-Write and Dual-Read

Writers temporarily emit old and new forms; readers compare or prefer one with fallback to the other.

- **Compatibility:** supports uncoordinated migration when both paths are maintained.
- **Rollback:** possible before old writes stop; ambiguous if paths diverge.
- **Performance:** doubles writes, storage, validation, and operational surfaces.
- **Use when:** incompatible changes must cross continuously available systems.

Define one source of truth, a shared idempotency key, write ordering, mismatch alerts, reconciliation, cutover criteria, and removal date. Avoid independent writes that can partially succeed; use an outbox or durable repair queue.

## Schema-on-Read

Store raw data with source metadata and interpret it at consumption time.

- **Compatibility:** ingestion accepts broad change, but each reader owns version handling.
- **Rollback:** raw immutable inputs simplify reprocessing.
- **Performance:** repeated parsing and conversion increase read cost; query behavior may vary across versions.
- **Use when:** source variability is unavoidable and immediate canonicalization would lose evidence.

Maintain a schema catalog, parser version, quarantine path, and canonical promoted layer. Schema-on-read is not schema-free.

## Versioned Endpoints, Topics, or Messages

Publish an independent contract identity such as `/v2`, `orders.v2`, or a new Protobuf message.

- **Compatibility:** versions are isolated; adapters may bridge them.
- **Rollback:** route traffic back while old capacity and data paths remain available.
- **Performance:** duplicate infrastructure and transformations during support overlap.
- **Use when:** semantics, keys, authorization, or required structure intentionally break.

Track consumers by version and retire only after usage, replay windows, and retained data prove the old version is unnecessary.

## Format-Specific Compatibility

| Change | Avro | Protobuf | JSON Schema |
|---|---|---|---|
| Add optional/defaulted field | Usually backward | Usually safe with new number | Usually backward |
| Add required field without default | Breaking | Avoid required semantics | Breaking |
| Remove field | Reader/writer dependent | Reserve name and number | Can break old readers |
| Numeric widening | Limited promotions | Wire-type dependent | Depends on constraints |
| Rename | Alias may help Avro resolution | New field; old number reserved | Usually remove + add |
| Add enum symbol | Reader handling required | Old clients may see unknown | Constraint expansion may be forward-risky |
| Tighten validation | Breaking for existing data | Semantic break | Usually breaking |

## Decision Procedure

1. Identify every producer, consumer, retained payload, and replay window.
2. Separate structural changes from semantic changes.
3. Simulate producer-first and consumer-first deployment orders.
4. Prefer additive-only when meaning can remain stable.
5. Choose migration or dual support when history or live traffic must transform.
6. Choose a versioned boundary for intentional semantic incompatibility.
7. Gate against all supported versions and test serialized golden fixtures.
8. Define rollback before destructive cleanup begins.
