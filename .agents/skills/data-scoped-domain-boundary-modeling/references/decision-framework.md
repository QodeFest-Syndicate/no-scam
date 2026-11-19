# FaaS, SaaS, and PaaS Decision Framework

Use this framework per capability or bounded context, not once for an entire portfolio. A hybrid result is often correct when a managed workflow, developer platform, and event workers coexist.

## Decision Matrix

Score each axis from 0 to 3 for every candidate model. Use 0 for incompatible, 1 for weak fit, 2 for acceptable fit, and 3 for defining fit. Multiply by the weight and retain the evidence behind every score.

| Criterion | Weight | FaaS signal | SaaS signal | PaaS signal |
|---|---:|---|---|---|
| Statelessness | 3 | Short, retryable, stateless execution | State hidden behind managed workflows | Tenant workloads may be stateful within guardrails |
| Trigger shape | 2 | Event, queue, webhook, or schedule | Human/API workflow | Provision, deploy, configure, or operate |
| Tenancy model | 3 | Tenant context passed per invocation | Shared managed product with isolated tenant data | Tenant-controlled runtimes/resources |
| Self-service | 3 | Invoke a narrow function contract | Configure product features | Create and manage platform resources |
| Billing granularity | 2 | Invocation, duration, or resources consumed | Seat, plan, feature, or business outcome | Allocated capacity plus metered platform use |
| Data ownership | 3 | Usually transient; authoritative state is external | Provider operates product stores for tenant data | Tenant owns workload data; provider owns platform metadata |
| Data residency | 2 | Function placement follows event/data region | Provider routes and stores tenant data by policy | Placement is exposed as a governed platform choice |
| Operational ownership | 3 | Provider runs runtime; team owns function code | Provider owns application lifecycle end to end | Provider owns platform; tenant owns deployed workloads |
| Customizability | 2 | Code/config at deployment | Product configuration and extensions | Runtime, services, policies, and deployment choices |
| Execution lifetime | 2 | Bounded by function timeout | Workflow duration hidden by application | Long-running tenant workloads supported |

### Interpretation

1. Calculate weighted totals.
2. Reject a model if any non-negotiable constraint is incompatible, regardless of score.
3. A lead of 20% or more is a strong classification.
4. A smaller lead indicates a hybrid or an unresolved requirement.
5. Split capabilities when different personas or operational owners drive different results.

## Fast Decision Tree

1. Is the primary value a managed outcome for an end user? Start with **SaaS**.
2. Is the primary value a self-service runtime or deployment primitive? Start with **PaaS**.
3. Is the unit independently triggered, bounded, stateless, and retryable? Treat that unit as **FaaS**.
4. If two answers are yes, define their contract and classify each boundary separately.

## Responsibility Matrix

| Responsibility | FaaS | SaaS | PaaS |
|---|---|---|---|
| Runtime patching | Provider | Provider | Provider |
| Application upgrades | Function owner | SaaS provider | Tenant workload owner |
| Tenant workflow | Calling product | Provider | Tenant-built application |
| Capacity control | Concurrency settings | Provider product operations | Quotas plus tenant requests/limits |
| Data deletion | Function and source-system contract | Provider product workflow | Shared provider/tenant contract |
| Incident response | Function owner + cloud provider | SaaS provider | Platform provider + tenant operator |

## Worked Example: FaaS

**Capability:** Resize uploaded images after object-created events.

- Statelessness: 3 — each invocation derives output from one immutable object.
- Trigger: 3 — object event with at-least-once delivery.
- Tenancy: 2 — tenant ID is part of the object prefix and event metadata.
- Billing: 3 — duration and memory per invocation reflect cost.
- Data ownership: 1 — source and generated objects remain owned by the media domain.
- Operational ownership: 2 — the team owns code; the cloud provider owns the runtime.

**Decision:** FaaS. Require deterministic output keys, duplicate-event handling, bounded image sizes, and a dead-letter path.

## Worked Example: SaaS

**Capability:** Subscription analytics portal for customer administrators.

- Statelessness: 1 — persistent accounts, dashboards, and saved views exist.
- Tenancy: 3 — many organizations share a managed application.
- Self-service: 1 — customers configure dashboards but cannot manage runtimes.
- Billing: 3 — plan and seat pricing represent product value.
- Data ownership: 3 — the provider governs application records on the tenant's behalf.
- Operational ownership: 3 — the provider owns availability, upgrades, and workflows.

**Decision:** SaaS. Isolate tenant data, enforce backend authorization, define retention, and make tenant switching auditable.

## Worked Example: PaaS

**Capability:** Customer platform for deploying containerized data jobs.

- Statelessness: 1 — workloads may be long-running or stateful.
- Self-service: 3 — developers provision jobs, secrets, routes, and storage.
- Billing: 3 — allocated CPU, memory, storage, and execution are metered.
- Data ownership: 2 — tenants own workload data; provider owns platform metadata.
- Operational ownership: 3 — provider runs control plane; tenant operates workload behavior.
- Customizability: 3 — runtime settings exist within policy guardrails.

**Decision:** PaaS. Define isolation, quotas, admission policy, workload identity, lifecycle status, and shared responsibility.

## Worked Example: Hybrid

A document automation product exposes a managed review portal (**SaaS**), a tenant extension runtime (**PaaS**), and OCR workers triggered by uploads (**FaaS**). Keep three contracts explicit:

- SaaS to PaaS: authenticated tenant configuration and deployment status.
- SaaS to FaaS: event command and durable job status.
- PaaS to FaaS: governed event subscriptions without direct database sharing.

## Required Decision Record

Record capability, chosen model, score, constraints, provider responsibilities, tenant responsibilities, data owner, tenancy key, residency, billing unit, rejected alternatives, review date, and accountable owner.