---
name: data-scoped-domain-boundary-modeling
description: Model and distinguish FaaS, SaaS, and PaaS responsibilities, data ownership boundaries, and domain scoping for data-driven cloud products. Use when scoping a new product, defining service boundaries, classifying data ownership, or determining which delivery model (FaaS/SaaS/PaaS) fits a given domain.
---

# Data-Scoped Domain Boundary Modeling

## Purpose

This skill turns ambiguous product requirements into an explicit domain map for a data-driven cloud product. It identifies business concepts, ownership of data and decisions, tenant boundaries, personas, and the responsibilities that belong in FaaS, SaaS, or PaaS surfaces.

It is primarily applied during S1 Domain & Data Scoping. Its outputs become architecture inputs in S2 and evidence for the S4 Pre-Implementation Gate.

## When to Apply

Apply this skill when:

- A new cloud product or major capability is being scoped.
- Requirements mix user workflows, platform operations, and event processing.
- Teams disagree about service ownership or system boundaries.
- Data ownership, tenancy, residency, or retention is unclear.
- A delivery model must be selected or split across FaaS, SaaS, and PaaS.
- Architecture cannot proceed because domain language is inconsistent.

Do not use delivery technology as the starting point. Model the domain and data first, then classify the delivery surface.

## Inputs

Gather the following before modeling:

- Product goals, constraints, and measurable outcomes.
- User stories, workflows, wireframes, and operational scenarios.
- Candidate personas, including human users and machine clients.
- Source systems, datasets, events, reports, and retention obligations.
- Security, privacy, residency, compliance, latency, and availability needs.
- Existing services, teams, contracts, and operational ownership.
- Expected tenant model and scale assumptions.

Record unknowns explicitly rather than silently inventing requirements.

## Step-by-Step Instructions

### 1. Extract Domain Concepts

1. Read requirements once for outcomes and a second time for nouns, verbs, events, rules, and constraints.
2. Normalize synonyms into a shared glossary while preserving meaningful business distinctions.
3. Classify each concept as one of:
   - Entity: identity-bearing business object.
   - Value object: descriptive value without independent identity.
   - Event: immutable fact that occurred.
   - Command: requested state change.
   - Policy: decision rule or invariant.
   - Process: multi-step workflow spanning time or contexts.
   - Actor: person, organization, system, or automated agent.
4. For each concept, record its source of truth, lifecycle, sensitivity, and expected volume.
5. Mark overloaded terms that mean different things to different personas or teams.

### 2. Identify Target Personas and Jobs

For each persona, capture:

- Primary job to be done and success signal.
- Data they create, view, modify, export, or administer.
- Decisions they own versus decisions delegated to automation.
- Required permissions and approval boundaries.
- Interaction mode: portal, API, SDK, CLI, event, or operator workflow.
- Tenant relationship: tenant user, tenant administrator, provider operator, partner, or machine identity.

Separate buyer, administrator, operator, developer, and end-user needs. They often require different delivery surfaces.

### 3. Establish Data Ownership

For every dataset or event stream, assign:

- Authoritative owner and system of record.
- Producing and consuming contexts.
- Create, read, update, delete, export, and retention authority.
- Tenant partition key and legal ownership.
- Classification: public, internal, confidential, regulated, or secret.
- Residency, encryption, backup, deletion, and audit requirements.
- Freshness, consistency, availability, and lineage expectations.

A bounded context may consume another context's data, but it must not mutate another context's private storage directly.

### 4. Map Bounded Contexts

1. Group concepts that share language, invariants, ownership, and change cadence.
2. Give each context one clear business capability and accountable owner.
3. Define its public contract using commands, queries, events, or APIs.
4. Keep persistence models private to the context.
5. Map context relationships:
   - Customer/supplier for upstream-downstream dependency.
   - Conformist when a downstream adopts the upstream model.
   - Anti-corruption layer when translation protects a local model.
   - Published language for stable shared contracts.
   - Open-host service for broadly consumed APIs.
   - Separate ways when coupling has no sufficient value.
6. Document synchronous and asynchronous dependencies separately.
7. Identify workflows that cross contexts and name their orchestration owner.

### 5. Classify FaaS, SaaS, and PaaS Responsibilities

Use the following decision framework.

#### Choose FaaS When

- Work is triggered by an event, schedule, webhook, or narrow request.
- Execution is short-lived, stateless, independently scalable, and retryable.
- The capability has a small contract and limited runtime orchestration.
- Scale is bursty or idle periods make per-execution economics useful.

Avoid FaaS as the primary model for long-running stateful workflows, low-latency persistent connections, or workloads that cannot tolerate platform execution limits.

#### Choose SaaS When

- The product delivers an end-user or administrator outcome as a managed application.
- The provider owns operations, upgrades, availability, and most workflow integration.
- Tenants consume shared product capabilities through a portal, API, or SDK.
- Configuration is supported, but customers do not manage the underlying runtime.

#### Choose PaaS When

- Customers need self-service deployment, runtime, data, or integration primitives.
- Tenant developers or operators manage workloads within provider guardrails.
- Provisioning, quotas, policy, observability, and lifecycle APIs are core product value.
- The platform exposes extensibility while retaining infrastructure control.

#### Use a Composite Model When

Many products combine all three:

- SaaS provides workflows, dashboards, administration, and billing.
- PaaS provides tenant provisioning, runtime controls, policies, and developer surfaces.
- FaaS executes event-driven units behind either product surface.

Classify each bounded context or capability independently. Do not label an entire portfolio from one implementation detail.

### 6. Select Multi-Tenant Boundary Patterns

Choose isolation according to risk, scale, cost, and operational burden:

- Shared application and shared schema with tenant keys: lowest cost, strongest need for query enforcement.
- Shared database with schema per tenant: stronger logical separation, higher migration complexity.
- Database or account per tenant: strong isolation and residency control, higher provisioning cost.
- Dedicated deployment per tenant: strongest workload isolation, highest operational overhead.
- Hybrid tiers: shared defaults with dedicated options for regulated or high-volume tenants.

For every shared layer, define how tenant identity is propagated, validated, logged, and tested. Enforce tenant boundaries in more than the presentation layer.

### 7. Validate the Boundary Model

Run a review with product, domain, security, data, platform, and operations stakeholders. Resolve conflicting ownership and language before architecture decomposition.

Trace at least one normal workflow, one cross-tenant attack attempt, one deletion request, one upstream outage, and one schema change through the model.

## Domain Boundary Completeness Checklist

### Domain and Personas

- [ ] Product outcome and non-goals are explicit.
- [ ] Personas and machine actors have distinct jobs and permissions.
- [ ] Ubiquitous language and overloaded terms are documented.
- [ ] Entities, events, commands, policies, and processes are identified.
- [ ] Business invariants have an owning context.

### Data and Tenancy

- [ ] Every critical dataset has one authoritative owner.
- [ ] Tenant partition keys and legal ownership are known.
- [ ] Sensitivity, residency, retention, deletion, and audit needs are recorded.
- [ ] Freshness, consistency, lineage, and availability targets are stated.
- [ ] Cross-context reads and writes use explicit contracts.
- [ ] Shared storage paths include enforceable tenant isolation.

### Boundaries and Delivery Model

- [ ] Each bounded context has a single coherent purpose.
- [ ] Context relationships and translations are mapped.
- [ ] Cross-context workflows have an orchestration owner.
- [ ] FaaS, SaaS, PaaS, or composite classification has evidence.
- [ ] Provider and tenant responsibilities are unambiguous.
- [ ] Operational ownership and escalation paths are assigned.

### Stage Gates

- [ ] S1 artifacts are reviewable and unresolved questions are visible.
- [ ] S2 can derive APIs, events, storage, and deployment boundaries.
- [ ] S4 can verify risks, assumptions, and acceptance criteria.

## Key Patterns

### Ownership Matrix

Use one row per data asset with columns for owner, producer, consumers, mutation authority, tenant key, classification, retention, and contract.

### Capability-to-Surface Matrix

Use one row per capability with columns for persona, interaction mode, state profile, scaling profile, customizability, provider responsibility, and chosen FaaS/SaaS/PaaS surface.

### Boundary Contract

For each context, specify:

- Purpose and owner.
- Inputs and outputs.
- Commands, queries, events, and error semantics.
- Data it owns and data it references.
- Tenant and authorization boundary.
- Service-level objectives and failure behavior.
- Versioning and compatibility policy.

## Anti-Patterns

- Choosing cloud services before defining domain responsibilities.
- Treating FaaS, SaaS, and PaaS as mutually exclusive portfolio labels.
- Creating one service per database table or requirement noun.
- Sharing a database as an undocumented integration contract.
- Allowing multiple systems to be authoritative for the same fact.
- Trusting a tenant identifier supplied by a client without identity binding.
- Using a universal canonical model that erases bounded-context meaning.
- Ignoring deletion, residency, audit, and operational ownership until implementation.
- Calling technical layers bounded contexts without a business capability.

## Output Format Expectations

Produce a concise domain-scoping package containing:

1. Scope statement with goals, non-goals, assumptions, and open questions.
2. Persona and job matrix.
3. Domain glossary and concept inventory.
4. Data ownership and tenancy matrix.
5. Bounded-context map with relationship types and workflow ownership.
6. Capability classification matrix for FaaS, SaaS, PaaS, or composite delivery.
7. Risk and decision log with evidence and owners.
8. S2 architecture inputs and S4 gate criteria.

Outputs must distinguish confirmed requirements from assumptions, name accountable owners, and make boundary decisions traceable to product or risk evidence.