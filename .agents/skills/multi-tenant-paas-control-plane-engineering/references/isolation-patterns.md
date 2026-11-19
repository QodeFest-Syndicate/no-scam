# Multi-Tenant Isolation Patterns

Isolation is a stack: identity, API authorization, compute, network, storage, secrets, observability, and operations. Selecting a compute boundary does not remove the need to design every other layer.

## Namespace per Tenant

```text
Shared Cluster
+-- Control Plane (provider only)
+-- tenant-a namespace: RBAC + quota + default-deny network + tenant identity
+-- tenant-b namespace: RBAC + quota + default-deny network + tenant identity
```

**Security guarantee:** Strong logical separation when admission controls block privileged pods, cluster-scoped mutation, unsafe host access, and cross-namespace identity. Kubernetes namespaces alone are not security boundaries without these controls.

**Cost profile:** Low to medium. Control plane and nodes are pooled; policies and per-namespace objects grow with tenant count.

**Operational requirements:** Namespace lifecycle automation, workload identity, dedicated service accounts, network policy, quotas, pod security, tenant-keyed logs/metrics, and negative cross-tenant tests.

**Migration path:** Move a tenant to a dedicated node pool, virtual cluster, or cluster while preserving platform API and identity contracts. Replicate state, fence writes, switch routing, and verify metering.

**Best fit:** Many moderate-trust tenants with standardized workloads and shared compliance requirements.

## Cluster per Tenant

```text
Provider Control Plane
+-- tenant-a account/project --> Cluster A --> tenant-a data
+-- tenant-b account/project --> Cluster B --> tenant-b data
```

**Security guarantee:** Strong compute and control-plane isolation. Cloud account/project separation can also isolate IAM, quotas, encryption keys, and network perimeters. Provider automation remains a shared high-value boundary.

**Cost profile:** High. Fixed cluster, control-plane, observability, upgrade, and idle-capacity costs apply per tenant.

**Operational requirements:** Fleet management, version skew policy, automated upgrades, conformance, regional placement, break-glass access, per-cluster monitoring, and cost allocation.

**Migration path:** Standardize tenant desired state and restore it into a newly provisioned cluster. Use portable data contracts and avoid tenant-specific platform forks.

**Best fit:** Regulated, untrusted, very large, residency-bound, or contractually dedicated tenants.

## Virtual Cluster (vCluster)

```text
Host Cluster
+-- host namespace tenant-a --> Virtual API Server A --> Tenant A workloads
+-- host namespace tenant-b --> Virtual API Server B --> Tenant B workloads
```

**Security guarantee:** Tenant control-plane objects and API surface are separated while worker nodes remain shared. Guarantee depends on synchronization rules, host admission policy, runtime isolation, and network enforcement.

**Cost profile:** Medium. More components than namespaces, substantially less fixed cost than physical clusters.

**Operational requirements:** Version compatibility, syncer policy, host-resource restrictions, virtual control-plane backup, tenant API limits, and clear responsibility for CRDs and cluster-scoped features.

**Migration path:** Export desired objects and control-plane state to another vCluster or physical cluster. Validate unsupported APIs and storage attachment semantics.

**Best fit:** Tenants need Kubernetes-like autonomy or CRD separation but do not justify dedicated physical clusters.

## Silo Model

```text
Tenant Request --> Dedicated application/runtime/data stack --> Dedicated telemetry view
```

Each tenant receives an isolated stack, which may be a namespace, cluster, account, database, or complete cell.

**Guarantees:** Small blast radius, simpler tenant-specific residency and restore, clearer cost attribution.

**Costs:** More idle capacity, fleet operations, upgrades, and configuration-drift risk.

**Migration:** Keep one product release train and declarative tenant configuration. Avoid code forks. Support controlled placement moves through the control plane.

## Pool Model

```text
Tenant Requests --> Shared services --> tenant-keyed cache/store/queue
                           +-------> per-tenant limits and telemetry
```

Tenants share runtime and data-plane resources.

**Guarantees:** Depend on authenticated tenant derivation, authorization at every layer, mandatory partition keys, row/policy enforcement, and cross-tenant testing.

**Costs:** Best utilization and simplest upgrades, but greater noisy-neighbor and broad-blast-radius risk.

**Migration:** Introduce cell boundaries and placement metadata so selected tenants can move to a silo without changing public contracts.

## Hybrid Tiering

A common product uses pool for free/pro tenants, namespace or vCluster for higher trust needs, and cluster/account silos for regulated enterprise tenants. The control-plane API, status model, metering, and lifecycle must remain consistent across placements.

## Selection Matrix

| Driver | Namespace | Cluster | Virtual cluster | Pool | Silo |
|---|---:|---:|---:|---:|---:|
| Control-plane isolation | Low | High | Medium–High | Low | Depends |
| Workload isolation | Medium | High | Medium | Low–Medium | High |
| Tenant Kubernetes autonomy | Low | High | High | Low | Depends |
| Unit cost | Low | High | Medium | Lowest | Highest |
| Fleet complexity | Medium | High | Medium–High | Low | High |
| Residency flexibility | Medium | High | Medium | Low–Medium | High |
| Noisy-neighbor resistance | Medium | High | Medium | Low | High |

## Layer-by-Layer Review

| Layer | Required question |
|---|---|
| Identity | Can one tenant mint or reuse another tenant's workload identity? |
| API | Is tenant scope derived from trusted claims and reauthorized per action? |
| Compute | Can workloads access host, privileged capabilities, or another tenant's processes? |
| Network | Is east-west and egress traffic default-denied and explicitly allowed? |
| Storage | Are volumes, snapshots, backups, and keys tenant-bound? |
| Secrets | Are credentials short-lived, scoped, rotated, and excluded from shared caches? |
| Telemetry | Can labels, searches, dashboards, or alerts cross tenant boundaries? |
| Operations | Is break-glass access time-bound, approved, and audited? |

## Migration Runbook Skeleton

1. Freeze or replicate desired state from the provider source of truth.
2. Provision target placement and validate policy before data transfer.
3. Replicate data with tenant-scoped credentials and checksums.
4. Drain writes or use a bounded dual-write protocol with reconciliation.
5. Fence the source, switch identity and routing, then verify reads and writes.
6. Rebind metering, alerts, backup, and support ownership.
7. Retain or destroy source resources according to rollback and retention policy.