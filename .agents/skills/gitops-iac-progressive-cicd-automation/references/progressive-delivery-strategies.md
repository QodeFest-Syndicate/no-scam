# Progressive Delivery Strategies

Progressive delivery separates deployment from exposure and advances only when predefined technical and business evidence passes. Build once, promote the same immutable artifact, and design database changes for coexistence and rollback.

## Decision Criteria

| Constraint | Canary | Blue-green | Rolling | Recreate |
|---|---|---|---|---|
| Traffic segmentation | required | optional | optional | none |
| Duplicate full capacity | no | yes | no | no |
| Fast traffic rollback | strong | strongest | moderate | weak |
| Representative telemetry | essential | important | important | post-deploy only |
| Stateful compatibility | old/new coexist | old/new coexist | old/new coexist | downtime can simplify |
| Typical risk | analysis false confidence | cost/config divergence | mixed-version defects | downtime and slow recovery |

## Canary Analysis

Deploy a small representative cohort, observe minimum duration **and** sample size, compare with a concurrent baseline, then increase exposure through fixed steps. Define before deployment:

- segmentation key and representativeness;
- 1/5/25/50/100% or context-specific steps;
- error, latency, saturation, dependency, correctness, and business KPIs;
- query, aggregation, baseline, threshold, window, and minimum traffic;
- automatic abort, pause-on-missing-data, and maximum rollout duration;
- owner/approval for ambiguous signals.

Use statistical guardrails appropriate to volume; a zero-error low-traffic canary proves little. Watch cross-version caches, queues, sessions, and database schemas. Tools include Argo Rollouts, Flagger, service meshes, ingress/load balancers, and cloud deployment services.

## Blue-Green

Prepare the idle environment with the target artifact, configuration, migrations, capacity, certificates, and dependencies. Run contract, smoke, synthetic, security, and capacity checks; warm safely; switch traffic atomically or progressively; retain the old environment for the rollback window.

Strong for fast reversion and major runtime changes. Costs include duplicate capacity, state synchronization, external side effects, and hidden environment drift. Database rollback still requires expand-contract design; traffic reversion cannot undo incompatible writes.

## Rolling Update

Replace instances gradually with readiness/startup gates and controlled `maxUnavailable`/`maxSurge`. It is capacity-efficient but runs mixed versions, so requests, sessions, events, caches, and schemas must remain compatible. Define progress deadline and automatic rollback/stop behavior. Avoid when only one replica exists or mixed versions are unsafe.

## Recreate

Stop old capacity, migrate, and start the new version in a maintenance window. Appropriate for low-criticality systems, single-writer constraints, or changes that cannot coexist—only when downtime is accepted and restore is rehearsed. Require backup, communication, smoke checks, timeout, and rollback artifact.

## Feature Flags vs Traffic Splitting

Traffic splitting chooses who receives a deployment/version. Feature flags choose behavior inside a version and can target users, tenants, roles, or cohorts. Flags support kill switches and decouple release from deployment, but create combinatorial states and long-lived debt. Record owner, default, fail behavior, dependencies, telemetry, expiry, and removal task. Protect server-side authorization regardless of UI flags.

## Dark Launches

Run new computation or mirrored traffic without user-visible output. Use for capacity and result comparison. Prevent duplicate side effects, payments, notifications, writes, and audit events; sanitize mirrored sensitive data and honor residency. Compare correctness and performance with explicit mismatch budgets.

## A/B Testing

A/B tests optimize product outcomes, not deployment safety. Require stable random assignment, experiment identity, exposure logging, power/sample calculation, guardrails, novelty/duration handling, and privacy/consent review. Do not keep a harmful variant running for statistical purity; safety aborts override experiment goals.

## Promotion and Rollback Contract

Every strategy needs immutable artifact identity; migration compatibility; health/business queries; thresholds/windows/sample size; telemetry-loss behavior; approvals; max duration; automatic abort; application rollback; data recovery/forward-fix plan; verification after rollback; and retained evidence. Rehearse permissions and paths before production.

## Tool Selection

Select orchestration from platform fit, metric-provider integration, routing precision, tenancy, audit, rollback behavior, and operational ownership. Kubernetes options include Argo Rollouts and Flagger; cloud-native deployment services offer managed traffic shifts; LaunchDarkly/OpenFeature-style ecosystems manage flags. Tooling does not replace metric design or schema compatibility.
