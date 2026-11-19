---
name: multi-tenant-paas-control-plane-engineering
description: Engineer self-service PaaS control planes, tenant provisioning engines, and runtime sandboxes with multi-tenant isolation. Use when building control-plane operators, namespace/tenant provisioners, quota controllers, or integrating PaaS surfaces with cloud IAM and networking.
---

# Multi-Tenant PaaS Control Plane Engineering

## Purpose

This skill guides the engineering of secure, self-service control planes that provision and govern tenant runtimes. It treats tenancy, reconciliation, quotas, identity, networking, metering, and remediation as one lifecycle rather than unrelated infrastructure features.

It applies across S2 Architecture & TDD Planning, S4 Pre-Implementation Gate, S5 Core Build, S6 Integration & CI/CD, S7 Validation & Observability, and S8 Delivery & GTM.

## When to Apply

Apply this skill when:

- Building tenant, project, workspace, or namespace provisioning.
- Implementing Kubernetes operators or other reconciliation controllers.
- Exposing self-service platform APIs, CLI commands, or portal actions.
- Defining multi-tenant runtime isolation and sandboxing.
- Enforcing quota, policy, identity, networking, or usage controls.
- Integrating tenant workloads with CI/CD runners or cloud services.
- Resolving noisy-neighbor, provisioning, failover, or tenant-lifecycle defects.

## Inputs

Collect:

- Tenant types, trust levels, compliance tiers, and expected scale.
- Workload types, runtime requirements, and extensibility model.
- Isolation, availability, recovery, residency, and performance objectives.
- Cloud accounts, clusters, regions, IAM, network, and secret-management constraints.
- Provisioning, suspension, deletion, restore, and migration workflows.
- Resource pricing, quotas, metering dimensions, and billing integration.
- Existing platform APIs, operators, pipelines, and observability stack.

## Step-by-Step Instructions

### 1. Choose an Isolation Model

Evaluate each layer independently: identity, API, compute, network, storage, secrets, observability, and control-plane state.

#### Namespace per Tenant

Use when tenants can share a cluster but require strong logical separation.

- Bind one tenant identity boundary to one or more namespaces.
- Apply default-deny network policies, workload identity, quotas, and admission policy.
- Scope secrets, service accounts, dashboards, and logs to the tenant.
- Protect cluster-scoped resources from tenant mutation.

#### Shared Resources with RBAC

Use for trusted or low-risk tenants and highly shared services.

- Require tenant keys in all control-plane and data-plane records.
- Derive tenant context from authenticated identity, not request input alone.
- Enforce authorization in APIs, controllers, queries, caches, and telemetry.
- Test cross-tenant access as a first-class security property.

#### Hybrid Isolation

Use when cost and risk differ by tenant or workload.

- Share the control plane while selecting shared namespaces, dedicated namespaces, clusters, accounts, or regions by tier.
- Keep APIs and lifecycle semantics consistent across placement types.
- Record placement decisions and support controlled migration.
- Avoid hidden feature divergence between shared and dedicated tiers.

Document residual risks, operational cost, and escape path for each pattern.

### 2. Define the Tenant Lifecycle

Model explicit states such as requested, provisioning, active, degraded, suspended, deleting, deleted, and failed.

For each transition, define:

- Authorized initiator and approval policy.
- Preconditions and idempotency key.
- Resources created, updated, retained, or destroyed.
- Retry, timeout, compensation, and manual intervention behavior.
- Audit events and customer-visible status.
- Recovery point if the transition fails midway.

Make deletion asynchronous, observable, and policy-aware. Separate access suspension from irreversible data destruction.

### 3. Design Resource Quotas

Define quota dimensions at tenant, environment, namespace, workload, and platform levels:

- CPU, memory, accelerators, ephemeral storage, and persistent storage.
- Workload count, replicas, jobs, functions, and concurrent executions.
- API requests, build minutes, network egress, connections, and event throughput.
- Databases, topics, secrets, certificates, public endpoints, and other managed resources.

Apply:

1. Hard limits for safety or contractual caps.
2. Soft thresholds for alerts and upgrade prompts.
3. Default requests and limits to prevent unbounded workloads.
4. Admission-time validation for immediate feedback.
5. Runtime enforcement for usage that cannot be known at admission.
6. Hierarchical allocation so child environments cannot exceed tenant capacity.
7. Controlled burst capacity with clear duration and billing rules.

Version quota plans and preserve an audit trail for overrides.

### 4. Implement a Reconciliation Controller

For Kubernetes operators or equivalent controllers:

1. Define a declarative desired-state resource with a versioned schema.
2. Validate immutable fields and reject unsafe combinations early.
3. Watch the primary resource and owned or dependent resources.
4. Fetch current state without assuming prior reconciliation succeeded.
5. Compute the minimal convergent change.
6. Apply changes idempotently with stable ownership metadata.
7. Record conditions, observed generation, status, and actionable reasons.
8. Requeue on transient errors with bounded exponential backoff and jitter.
9. Stop or quarantine deterministic policy errors until input changes.
10. Use finalizers for ordered external cleanup.

Reconciliation must converge after duplicate events, controller restarts, partial writes, and out-of-order observations.

### 5. Automate Tenant Provisioning

Build provisioning as an orchestrated, resumable workflow:

- Reserve tenant identity and canonical tenant ID.
- Select region, cluster, account, namespace, or isolation tier.
- Create IAM roles, service identities, and least-privilege bindings.
- Establish network segments, policies, DNS, certificates, and ingress.
- Create storage, encryption keys, secrets, quotas, and baseline policies.
- Register metering, audit, observability, and billing dimensions.
- Seed approved templates or examples without embedding secrets.
- Run readiness checks and publish endpoint plus status.

Every step needs an idempotency key, persisted state, retry classification, and compensation decision.

### 6. Expose Self-Service APIs

Provide consistent tenant lifecycle and platform-resource APIs.

Recommended capabilities:

- Create, inspect, update, suspend, resume, migrate, and delete tenants.
- Request environments, runtimes, databases, routes, credentials, and integrations.
- View quota allocation, current usage, provisioning progress, and incidents.
- Rotate credentials and manage tenant members or service accounts.
- Retrieve audit events and usage exports.

API requirements:

- Authenticate callers and bind tenant scope from trusted claims.
- Authorize action, resource, environment, and tenant.
- Require idempotency keys for mutating requests.
- Return asynchronous operation resources for long-running work.
- Use stable error codes, correlation IDs, pagination, and versioning.
- Emit audit and metering events for accepted changes.

### 7. Engineer Runtime Sandboxes

Layer defenses according to workload trust:

- Run as non-root with restricted capabilities and read-only filesystems where possible.
- Apply seccomp, mandatory access controls, and workload security standards.
- Use runtime classes, microVMs, user namespaces, or dedicated nodes for higher-risk code.
- Restrict host paths, privileged modes, host networking, and unsafe device access.
- Limit network egress and metadata-service access.
- Isolate secrets and issue short-lived workload credentials.
- Enforce image provenance, signature, vulnerability, and policy checks.
- Cap process, file, storage, memory, CPU, and execution duration.

Treat sandbox escape and cross-tenant access as critical security scenarios with tested containment and revocation procedures.

### 8. Integrate Cloud IAM and Networking

#### IAM

- Map tenant roles to platform permissions and cloud identities.
- Prefer workload identity federation over static cloud keys.
- Separate control-plane privileges from tenant workload privileges.
- Scope operator permissions to the resources it reconciles.
- Support emergency revocation and complete audit trails.

#### Networking

- Start with default deny between tenants and from workloads to control-plane internals.
- Separate management, ingress, egress, and service traffic when risk requires it.
- Define DNS, certificate, public endpoint, private connectivity, and egress policies.
- Make network policy part of provisioning, not a post-provisioning patch.
- Test policy behavior across upgrades and different network plugins.

### 9. Integrate CI/CD Runners

- Bind build and deployment actions to tenant and environment identity.
- Use ephemeral runners for untrusted builds when possible.
- Isolate caches and artifacts by tenant; verify cache keys cannot cross boundaries.
- Issue short-lived deployment credentials with narrow audience and scope.
- Enforce artifact provenance, signing, policy, and environment promotion rules.
- Record actor, source revision, artifact digest, target, and policy decision.
- Limit runner concurrency, network access, compute, and secret exposure.

### 10. Implement Metering

Define billable and operational dimensions with stable identifiers:

- Tenant, account, plan, region, environment, resource, and time window.
- Provisioned capacity and actual consumption.
- Requests, runtime duration, storage, egress, build minutes, seats, or feature usage.

Metering events should be immutable, deduplicable, versioned, timestamped, and traceable to a source. Reconcile raw usage with aggregates and billing exports. Keep metering failure from silently granting unlimited resource use or double charging.

### 11. Mitigate Noisy Neighbors

Use multiple layers:

- Requests, limits, quotas, priority classes, and fair scheduling.
- API rate limits and per-tenant concurrency controls.
- Queue partitioning, connection pools, cache partitioning, and database workload management.
- Egress and storage I/O controls.
- Dedicated placement for sustained high-impact workloads.

Alert on saturation and tenant-level contribution. Throttle gracefully before broad platform failure.

### 12. Remediate Failures

For provisioning or reconciliation failures:

1. Identify tenant, desired generation, controller version, and operation ID.
2. Distinguish transient dependency failure from invalid desired state.
3. Inspect partial resources and ownership metadata.
4. Repair the cause, then let reconciliation converge.
5. Avoid manual edits that the controller will immediately reverse.
6. Record manual overrides with expiry and rollback steps.

For regional or cluster failover:

- Define source of truth for tenant placement and desired state.
- Replicate required control-plane and tenant data according to recovery objectives.
- Fence the failed location before activating a replacement when split brain is possible.
- Rebind identities, routes, secrets, and metering without creating duplicate resources.
- Verify customer-visible state and reconcile after recovery.

## Implementation Checklist

### Isolation and Security

- [ ] Isolation is defined for every platform layer.
- [ ] Tenant context comes from authenticated and authorized identity.
- [ ] Network policy defaults to deny where tenants share infrastructure.
- [ ] Workload credentials are short-lived and tenant-scoped.
- [ ] Sandbox controls match workload trust level.
- [ ] Cross-tenant tests cover APIs, storage, caches, logs, and metrics.

### Lifecycle and Control Plane

- [ ] Tenant states and transitions are explicit.
- [ ] Provisioning steps are resumable and idempotent.
- [ ] Reconciliation converges after restart and partial failure.
- [ ] Finalizers protect required external cleanup.
- [ ] Long-running API operations expose progress and errors.
- [ ] Manual overrides are audited and temporary.

### Quotas, Metering, and Reliability

- [ ] Quota dimensions and hierarchy are versioned.
- [ ] Admission and runtime enforcement are both covered.
- [ ] Metering events are deduplicable and reconcilable.
- [ ] Noisy-neighbor signals identify tenant contribution.
- [ ] Failover meets stated recovery objectives.
- [ ] Tenant onboarding exposes usage, quotas, support, and status.

### Stage Readiness

- [ ] S2 documents isolation, lifecycle, contracts, and failure models.
- [ ] S4 validates security boundaries and high-risk assumptions.
- [ ] S5 implements controllers, APIs, policy, and provisioning.
- [ ] S6 integrates cloud, network, runner, and release automation.
- [ ] S7 verifies isolation, load, failover, metering, and remediation.
- [ ] S8 provides onboarding, usage, billing, and operational handoff.

## Key Patterns

### Declarative Desired State

Persist tenant intent independently from runtime resources. Controllers compare desired and actual state until they converge.

### Asynchronous Operation Resource

Return an operation ID for long-running changes. Expose state, progress, timestamps, error code, and result link.

### Cell-Based Platform

Place bounded tenant groups into independent cells with their own runtime dependencies. Limit blast radius and scale by adding cells.

### Policy as Code

Version, test, review, and audit admission, identity, network, and placement policy alongside platform releases.

## Anti-Patterns

- Trusting a tenant ID supplied in a request body without identity binding.
- Giving tenant workloads cluster-admin or shared static cloud credentials.
- Building provisioning as an untracked chain of scripts.
- Assuming namespace isolation alone covers network, storage, and identity.
- Reconciliation that only handles the successful create path.
- Unbounded retries on invalid desired state.
- Per-tenant custom forks that cannot receive platform upgrades.
- Billing from mutable aggregates without durable raw usage records.
- Global caches, runner caches, or dashboards without tenant partitioning.
- Solving noisy neighbors only by adding cluster capacity.

## Output Format Expectations

Produce:

1. Tenant model, trust tiers, lifecycle, and responsibility matrix.
2. Layer-by-layer isolation and threat model.
3. Placement, quota, and noisy-neighbor policy.
4. Control-plane resource schemas and reconciliation contract.
5. Provisioning workflow with idempotency, compensation, and status behavior.
6. Self-service and usage-metering API contracts.
7. IAM, networking, sandbox, and CI/CD runner integration design.
8. Test plan for cross-tenant access, scale, recovery, and upgrades.
9. Operational dashboards, alerts, remediation, and failover procedures.
10. Evidence mapped to S2, S4, S5, S6, S7, and S8 gates.

Outputs must separate desired state from observed state, name every isolation boundary, and quantify quotas, recovery targets, and platform limits.