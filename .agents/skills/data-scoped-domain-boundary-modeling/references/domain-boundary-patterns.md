# Domain Boundary Pattern Catalog

Patterns are starting points, not substitutes for an ownership decision. For every pattern, document the system of record, tenant key, mutation authority, contract, and failure behavior.

## Bounded Context per Tenant

### Context

Regulated, high-value, or highly customized tenants require strong logical or physical separation. Tenant data has different residency, release, or retention obligations.

### Problem

A shared context makes policy variation and blast-radius control difficult, while tenant-specific forks make upgrades unsustainable.

### Solution

Instantiate the same bounded-context contract per tenant while retaining one versioned product model. Route using authenticated tenant identity. Keep placement metadata in a provider-owned control plane. Automate lifecycle, schema migration, backup, deletion, and conformance checks.

```text
Control Plane
  +-- placement(tenant A) --> Context Instance A --> Data Store A
  +-- placement(tenant B) --> Context Instance B --> Data Store B
```

### Trade-offs

- Strong isolation, residency control, and tenant-specific recovery.
- Higher provisioning, fleet management, migration, and observability cost.
- Schema and behavior drift unless releases are centrally controlled.
- Cross-tenant analytics requires an explicit, privacy-reviewed export path.

### When to Use

Use for dedicated tiers, strict residency, custom encryption keys, large noisy tenants, or contractual isolation. Avoid when tenant count is very high and risk does not justify per-tenant infrastructure.

## Shared Kernel with Tenant Scoping

### Context

Many tenants use the same product language, rules, and release cadence. Cost efficiency and rapid product evolution matter.

### Problem

Duplicated models fragment behavior, but unscoped shared state can leak data across tenants.

### Solution

Maintain one carefully governed shared kernel for stable concepts. Add tenant scope to every record, cache key, query, event, and authorization check. Derive tenant identity from trusted claims. Expose repository APIs that require tenant scope rather than relying on optional filters.

```text
Tenant Request --> Identity Boundary --> Shared Domain Service
                                         |-- tenant-keyed cache
                                         +-- tenant-keyed store
```

### Trade-offs

- Lowest unit cost and simplest coordinated upgrades.
- A missed scope predicate can cause a severe cross-tenant breach.
- Shared schema limits per-tenant customization.
- Large tenants can create noisy-neighbor pressure.

### When to Use

Use for standardized SaaS capabilities with uniform compliance needs. Pair with row-level security where supported, negative cross-tenant tests, tenant-aware telemetry, and per-tenant limits.

## Event-Driven Boundary Bridge

### Context

Two bounded contexts must exchange facts but use different language, ownership, or persistence models.

### Problem

Direct database access couples schemas and mutation authority. Synchronous APIs can spread outages and force temporal coupling.

### Solution

Publish versioned domain events from an outbox. Translate them in a bridge or anti-corruption layer into the downstream context's language. Consumers deduplicate, preserve source IDs, and track replay checkpoints.

```text
Upstream Context --> Outbox --> Event Contract --> Translator --> Downstream Context
       owns source fact                                  owns local projection
```

### Trade-offs

- Preserves autonomy and supports replay and independent scaling.
- Introduces eventual consistency, duplicate delivery, and schema governance.
- Debugging requires correlation and lineage across boundaries.
- Corrections and deletions need explicit event semantics.

### When to Use

Use for independent change cadence, fan-out, audit history, or resilience. Avoid for invariants that require one atomic transaction; keep those within one context or use an explicit coordinator.

## Data Mesh Domain Ownership

### Context

Multiple business domains produce analytical data for broad reuse. A central data team cannot own semantics for every source.

### Problem

A centralized lake becomes a poorly understood dumping ground, while isolated domain marts duplicate governance and tooling.

### Solution

Assign data products to domain owners. Each product publishes a discoverable contract covering schema, semantics, quality SLOs, lineage, classification, access policy, and deprecation. A federated platform supplies common identity, catalog, policy, storage, and observability capabilities.

```text
Domain A Data Product --+
Domain B Data Product --+--> Federated Catalog and Policy --> Authorized Consumers
Domain C Data Product --+
```

### Trade-offs

- Semantics and quality remain close to source expertise.
- Requires mature product ownership and federated governance.
- Common tooling must not erase legitimate domain differences.
- Distributed costs and incident ownership must be visible.

### When to Use

Use when autonomous domains already own operational sources and analytical consumers need governed reuse. Do not use merely to rename unmanaged datasets as products.

## Pattern Selection Matrix

| Driver | Per Tenant | Shared Kernel | Event Bridge | Data Mesh |
|---|---:|---:|---:|---:|
| Strong tenant isolation | High | Medium | Depends on endpoints | Medium |
| Lowest operating cost | Low | High | Medium | Medium |
| Independent domain evolution | Medium | Low | High | High |
| Synchronous consistency | High within instance | High within kernel | Low | Low |
| Cross-domain analytics | Low | Medium | Medium | High |
| Residency customization | High | Low–Medium | Medium | High |

## Review Checklist

- One authoritative owner exists for every fact.
- Consumers cannot mutate private storage across a boundary.
- Tenant identity is trusted, propagated, and logged.
- Contracts define versions, retries, deletion, and deprecation.
- Operational escalation follows ownership.
- Failure, replay, migration, and exit paths are tested.