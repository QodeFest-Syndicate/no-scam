---
name: gitops-iac-progressive-cicd-automation
description: Automate GitOps workflows, declarative IaC (Terraform/Pulumi), GitHub Actions CI/CD pipelines, canary/blue-green rollouts, and release documentation (README.md/CHANGELOG.md) hygiene. Use when building CI/CD pipelines, provisioning infrastructure, configuring progressive delivery, or maintaining release documentation.
---

# GitOps, IaC, and Progressive CI/CD Automation

## Purpose

This skill turns infrastructure and delivery requirements into reproducible, reviewable automation. It keeps Git as the desired-state source, provisions environments from declarative code, moves tested artifacts through progressive rollout gates, and leaves an auditable release trail.

## When to Apply

Apply this skill when work includes:

- Designing deployment topology, SLO-aware rollout policy, or environment boundaries.
- Authoring or refactoring Terraform or Pulumi modules.
- Creating or optimizing GitHub Actions workflows.
- Selecting canary, blue-green, rolling, or recreate deployment behavior.
- Estimating hosted or self-hosted runner capacity.
- Wiring automated quality, security, and operational gates into delivery.
- Packaging deployable artifacts and publishing deployment manifests.
- Automating rollback based on health signals.
- Provisioning production or maintaining release documentation.

Do not use it to conceal manual infrastructure changes. Import or reconcile those resources first.

## Stage Alignment

- **S2 — Architecture & TDD Planning:** define topology, environment boundaries, SLOs, deployment constraints, and rollback objectives.
- **S3 — Task Decomposition & Routing:** estimate workflow concurrency, runner capacity, critical paths, and ownership boundaries.
- **S6 — Integration & CI/CD:** implement IaC, pipelines, artifact publication, promotion, and progressive delivery.
- **S7 — Validation & Observability:** monitor rollout health, enforce telemetry gates, rehearse rollback, and preserve evidence.
- **S8 — Delivery & GTM:** provision production, publish release artifacts, and complete operator-facing release documentation.

## Core Principles

1. **Git defines desired state.** Every persistent infrastructure or delivery change is reviewable and traceable to a commit.
2. **Build once, promote many.** The same immutable artifact moves across environments; only configuration and policy vary.
3. **Plans precede applies.** Review machine-generated diffs before mutating shared environments.
4. **Credentials are short-lived.** Prefer workload identity federation and scoped roles over static secrets.
5. **Environments remain structurally alike.** Differences are explicit inputs, not divergent implementations.
6. **Delivery is observable.** Promotions and rollback decisions use defined health signals and time windows.
7. **Rollback is executable.** A rollback procedure is automated, permissioned, and regularly tested.
8. **Generated state is protected.** Lock state, encrypt it, restrict access, and back it up.

## Step-by-Step Workflow

### 1. Establish Delivery Inputs

- Identify services, jobs, data stores, queues, external dependencies, and deployment units.
- Record availability and latency SLOs, recovery objectives, change windows, and compliance constraints.
- Define environments, accounts or projects, regions, tenancy boundaries, and promotion order.
- Choose artifact types: container image, function bundle, package, chart, or signed manifest.
- Define evidence required at every gate: test results, scan reports, approvals, telemetry, and change record.

**Exit condition:** topology, ownership, promotion path, and rollback targets are explicit.

### 2. Model Declarative Infrastructure

- Separate reusable modules or components from environment composition.
- Keep provider configuration and backend configuration outside reusable modules.
- Expose intentional inputs with descriptions, types, validation, and safe defaults.
- Export stable outputs needed by other stacks; avoid leaking implementation details.
- Pin providers, plugins, modules, and automation tool versions.
- Store state remotely with encryption, locking, versioning, and least-privilege access.
- Run formatting, validation, linting, policy checks, and security scans before planning.
- Generate a plan for pull requests; apply only the reviewed plan or an equivalent commit-bound plan.

#### Terraform Module Pattern

A module should contain one cohesive capability, such as a network, service runtime, or observability foundation. It should:

- Declare `required_version` and constrained provider versions.
- Type every variable and validate bounded values.
- Avoid environment names inside resource logic.
- Use `for_each` with stable keys instead of index-sensitive resource identity.
- Mark sensitive outputs and avoid secrets in state where possible.
- Include examples or fixtures that exercise the public interface.
- Test upgrades and destructive changes before publishing a new module version.

#### Pulumi Component Pattern

A component should:

- Wrap related resources behind a typed input and output contract.
- parent all child resources to preserve hierarchy and aliases.
- Pass providers explicitly when crossing accounts, regions, or clusters.
- Use stack configuration for environment values and a secret provider for sensitive values.
- Register outputs only after dependency relationships are defined.
- Add aliases before renaming resources to prevent unintended replacement.

### 3. Design the GitHub Actions Workflow

- Trigger pull-request verification separately from protected-environment deployment.
- Grant minimal `permissions`; default unspecified permissions to none.
- Pin third-party actions to immutable commit SHAs and track updates deliberately.
- Use OIDC for cloud access and environment protection rules for privileged jobs.
- Set `concurrency` groups to prevent overlapping deployment or state mutation.
- Use reusable workflows for shared policy and composite actions for repeated local steps.
- Cache only deterministic dependency inputs; never cache credentials or mutable deployment state.
- Set job timeouts and artifact retention explicitly.
- Cancel superseded pull-request runs, but do not cancel an active production apply without a recovery path.
- Emit a job summary containing artifact identity, environment, checks, plan link, and outcome.

Recommended job order:

1. Metadata and change detection.
2. Format, lint, schema, and policy checks.
3. Unit and contract tests.
4. Build once and compute an artifact digest.
5. Dependency, secret, IaC, and artifact scans.
6. Integration and end-to-end tests.
7. Publish signed artifact and attestations.
8. Plan infrastructure or render manifests.
9. Deploy to a protected environment.
10. Verify telemetry and promote or roll back.

### 4. Plan Runner Capacity

- Measure queue time, setup time, execution time, cache hit rate, and peak concurrency.
- Partition trusted and untrusted workloads; never run fork code on privileged persistent runners.
- Prefer ephemeral self-hosted runners for private-network or specialized workloads.
- Size capacity from arrival rate, average job duration, burst factor, and target queue time.
- Use matrices only when parallelism provides useful feedback; cap `max-parallel` to protect dependencies.
- Reserve capacity for hotfixes and production rollback workflows.
- Validate storage, network egress, image-pull, and API-rate-limit bottlenecks, not only CPU.

### 5. Integrate Automated Test Gates

At minimum, gate deployment on applicable checks:

- Formatting, static analysis, and compilation.
- Unit, component, contract, migration, and integration tests.
- IaC validation, policy-as-code, and destructive-change review.
- Dependency, secret, license, container, and supply-chain scans.
- Performance or load thresholds for critical paths.
- Deployment smoke tests and SLO health checks.

Use required checks with stable names. Fail closed when evidence is absent. Time-bound manual approvals and record the approver without replacing automated evidence.

### 6. Publish Artifacts and Deployment Manifests

- Assign a unique version and capture the source commit.
- Produce immutable artifacts with checksums or digests.
- Generate an SBOM and provenance attestation where supported.
- Sign artifacts and verify signatures before deployment.
- Render or package manifests using artifact digests rather than mutable tags.
- Publish artifacts, manifests, test evidence, and release metadata to retained repositories.
- Promote references to the existing artifact; do not rebuild per environment.

### 7. Choose a Progressive Rollout

#### Canary

Use canary when traffic can be segmented and telemetry can compare populations.

1. Deploy to a small representative cohort.
2. Hold for a minimum observation window.
3. Compare error rate, latency, saturation, business KPIs, and correctness signals.
4. Increase traffic through predefined steps.
5. Pause on inconclusive data; roll back on threshold breach.
6. Complete rollout only after every gate passes.

Avoid canaries that mix irreversible schema changes with old application versions.

#### Blue-Green

Use blue-green when fast cutover and fast reversion outweigh duplicate-environment cost.

1. Provision or update the idle environment.
2. Run smoke, contract, migration compatibility, and synthetic tests.
3. Warm caches and validate capacity.
4. Switch traffic atomically or in controlled percentages.
5. Observe health before decommissioning the former environment.
6. Preserve the former environment for the rollback window.

Design database changes with expand-and-contract migration so both versions remain compatible.

### 8. Automate Monitoring and Rollback

- Define rollout queries before deployment begins.
- Include technical and business correctness signals.
- Set minimum traffic or sample-size requirements to avoid false confidence.
- Configure automated abort and rollback for decisive threshold breaches.
- Freeze promotion when telemetry is unavailable or contradictory.
- Roll back the application separately from data; never assume destructive data changes are reversible.
- Verify rollback health and record the triggering evidence.
- Test rollback permissions and paths in non-production and through scheduled production-safe drills.

### 9. Maintain Environment Parity

- Compose every environment from the same modules and manifest templates.
- Express differences through versioned variables and policy.
- Detect drift on a schedule and report it without silently overwriting emergency changes.
- Reconcile emergency changes into Git immediately after stabilization.
- Use production-like data shape and traffic characteristics without copying restricted data.
- Test quotas, autoscaling, certificates, DNS, identity, and network policy before production.

### 10. Complete Release Documentation

#### README.md Hygiene

Keep the README focused on current operation:

- Purpose, supported deployment model, and prerequisites.
- Reproducible setup, verification, deployment, and rollback commands.
- Configuration reference with safe examples and secret-handling guidance.
- Architecture or operational links that are versioned with the repository.
- Ownership, support path, and compatibility policy.

Remove stale commands, mutable-version examples, and undocumented prerequisites.

#### CHANGELOG.md Hygiene

- Use a consistent structure such as Keep a Changelog.
- Maintain an `Unreleased` section.
- Group entries by Added, Changed, Deprecated, Removed, Fixed, and Security.
- Describe user and operator impact rather than commit mechanics.
- Link versions to diffs and include release dates.
- Call out breaking changes, migrations, rollback constraints, and security fixes.
- Generate drafts from labels if useful, but require editorial review.

## Checklists

### IaC Review

- [ ] Desired state is represented in version control.
- [ ] State is remote, encrypted, locked, backed up, and access-controlled.
- [ ] Versions are pinned and module interfaces are typed and validated.
- [ ] Plan output is attached to the review and destructive changes are explicit.
- [ ] Policy, lint, security, and upgrade checks pass.
- [ ] Import, migration, and rollback behavior is documented and tested.

### Pipeline Review

- [ ] The artifact is built once and promoted by digest.
- [ ] Workflow permissions and cloud roles are least privilege.
- [ ] Untrusted code cannot reach secrets or privileged runners.
- [ ] Required test and security gates fail closed.
- [ ] Concurrency, timeouts, retries, retention, and runner capacity are intentional.
- [ ] Deployments use protected environments and emit auditable summaries.

### Progressive Delivery Review

- [ ] Strategy and traffic steps match architecture and risk.
- [ ] Health metrics, thresholds, observation windows, and sample sizes are predefined.
- [ ] Schema changes are backward compatible through the rollback window.
- [ ] Automatic abort and rollback paths are tested.
- [ ] Telemetry loss halts promotion.
- [ ] Former capacity remains available until rollback risk expires.

### Release Readiness

- [ ] Artifacts, manifests, SBOM, signatures, and provenance are published.
- [ ] README instructions work from a clean environment.
- [ ] CHANGELOG entries describe impact and migration requirements.
- [ ] Production provisioning is reproducible and drift-free.
- [ ] Release and rollback evidence has a defined retention period.

## Key Patterns

- **Plan on pull request, apply after merge:** reviewers see the infrastructure impact before mutation.
- **Immutable promotion:** artifact digests connect source, tests, attestation, and deployment.
- **Expand and contract:** databases remain compatible across progressive rollout and rollback.
- **Reconciliation loop:** a controller continuously converges runtime state toward Git state.
- **Policy as code:** identity, cost, security, and topology rules are checked consistently.
- **Telemetry-gated promotion:** rollout steps advance only when objective signals pass.
- **Reusable workflow contract:** inputs, secrets, permissions, and outputs form a stable delivery API.

## Anti-Patterns

- Applying infrastructure locally from an unreviewed working tree.
- Maintaining copied environment directories that drift structurally.
- Using mutable image tags such as `latest` for promotion.
- Giving workflows broad write permissions or long-lived cloud keys.
- Rebuilding artifacts for staging and production.
- Retrying nondeterministic tests until a pipeline turns green.
- Treating a successful deployment command as proof of service health.
- Running canaries without minimum traffic, comparison baselines, or rollback thresholds.
- Coupling application rollback to an irreversible database migration.
- Generating release notes directly from commit subjects without impact editing.
- Allowing emergency console changes to remain outside Git.

## Output Format Expectations

When applying this skill, produce a delivery packet with:

1. **Scope and assumptions:** services, environments, constraints, SLOs, and ownership.
2. **Topology:** accounts, regions, networks, runtimes, dependencies, and promotion path.
3. **IaC design:** module boundaries, state strategy, inputs, outputs, policies, and migration plan.
4. **Pipeline design:** triggers, jobs, dependencies, permissions, runner plan, and test gates.
5. **Artifact contract:** version, digest, registry, manifest, SBOM, signature, and retention.
6. **Rollout policy:** strategy, traffic steps, health queries, thresholds, timing, and approvals.
7. **Rollback plan:** automated triggers, actions, data constraints, verification, and owner.
8. **Parity and drift plan:** shared composition, explicit differences, detection, and reconciliation.
9. **Release documentation changes:** README and CHANGELOG updates with user impact.
10. **Verification evidence:** plan output, test results, scan results, deployment result, and telemetry links.

Use concrete repository paths, workflow names, environment names, and commands when the target system is known. Mark assumptions and unresolved risks explicitly; do not present them as completed work.
