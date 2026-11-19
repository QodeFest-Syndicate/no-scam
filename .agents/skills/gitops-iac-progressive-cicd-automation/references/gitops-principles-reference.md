# GitOps Principles and Practices

GitOps uses version-controlled declarative desired state plus automated reconciliation. A Git commit is an auditable proposal; the reconciler compares desired and observed state, applies authorized changes, and reports drift and health.

## Four Operating Principles

1. **Declarative desired state:** infrastructure, platform, application manifests, policies, and configuration describe outcomes rather than imperative steps.
2. **Versioned immutable history:** changes are reviewed, signed/protected as appropriate, and traceable to actor, reason, tests, and artifact digest.
3. **Automated reconciliation:** a controller continuously converges authorized targets and retries bounded transient failures.
4. **Observable divergence:** drift, sync status, health, policy failures, and last applied revision are measurable and alertable.

Secrets should be references to a managed secret system or encrypted declarations with controlled keys—not plaintext in Git.

## Repository and Promotion Models

Separate reusable source from environment composition. Promote the same immutable artifact digest by pull request; do not rebuild per environment. Environment differences are explicit values/policies, not copied directories with divergent structure. Choose mono- or multi-repository boundaries from ownership, authorization, blast radius, scale, and atomic-change needs.

Protect production branches/environments, require stable checks, limit direct writes, and record emergency changes. After stabilization, reconcile break-glass/runtime edits back into Git or deliberately revert them.

## Pull-Based vs Push-Based Delivery

| Dimension | Pull-based reconciler | Push-based pipeline |
|---|---|---|
| Cluster/cloud credentials | remain near target/controller | available to CI runner |
| Drift correction | continuous | usually scheduled/manual |
| Network direction | target pulls desired state | CI reaches target |
| Audit | commit plus controller status | commit plus pipeline logs |
| Failure mode | stale divergence/reconciliation loop | partial imperative deployment |
| Best fit | long-lived declarative targets | external APIs/steps without controllers |

Hybrid models are common: CI builds/signs/scans artifacts and updates desired-state references; a pull controller deploys. Avoid two writers managing the same fields/resources.

## Tooling Comparison

| Tool | Model/strength | Notable trade-offs |
|---|---|---|
| Argo CD | Kubernetes pull reconciliation, application health, UI, sync waves, multi-cluster | controller/UI footprint; Application/ApplicationSet governance and secret strategy required |
| Flux | composable Kubernetes controllers, Git/OCI sources, image automation, toolkit APIs | more controller concepts; UX often CLI/API oriented |
| Jenkins X | opinionated cloud-native CI/CD, preview environments, promotion workflows | broader platform adoption and conventions; operational complexity may exceed focused GitOps needs |

Select on target platforms, tenancy, authorization, scale, extensibility, operational ownership, ecosystem, and recovery—not feature count alone.

## Drift and Reconciliation Policy

Classify drift as expected controller defaulting, unauthorized mutation, emergency change, external-controller ownership, or nondeterministic rendering. Alert before auto-correcting destructive or safety-sensitive drift. Use server-side field ownership or equivalent to prevent controller fights. Reconciliation must have backoff, health timeout, dependency ordering, and circuit-break/pause behavior.

## Security and Supply Chain

- short-lived workload identity for source, registry, and target;
- least-privilege controller scopes and tenant/project isolation;
- immutable artifact digests, signatures, SBOM, provenance, and admission verification;
- pinned dependencies and deterministic rendering;
- protected branches, reviews, CODEOWNERS, and policy-as-code;
- redacted logs and external secret retrieval;
- auditable break-glass with expiry and post-event review.

## Operational Checklist

Verify desired-state source and precedence, repository ownership, promotion path, artifact identity, reconciliation interval, drift response, pruning policy, dependency order, health checks, rollback/revert semantics, stateful migration compatibility, disaster recovery, controller upgrades, and evidence retention. A “Synced” status is not enough: application health and business correctness need independent signals.
