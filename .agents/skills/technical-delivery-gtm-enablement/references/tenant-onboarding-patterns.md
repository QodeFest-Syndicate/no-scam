# Tenant Onboarding Patterns

## Outcome and state model

Onboarding ends at verified customer value, not account creation. Model it as a durable state machine: requested, identity verified, policy accepted, tenant provisioned, integration configured, first success verified, activated, and supported. Persist step status, attempt, input version, evidence, failure reason, and owner.

## Self-service onboarding

Best for standardized products with low integration risk. Automate signup, verification, region/plan selection, tenant/billing creation, baseline roles, sandbox credentials, guided integration, and activation.

**Advantages:** low marginal cost and fast time to value. **Requirements:** idempotent provisioning, excellent guidance, safe defaults, observable failure, and operator repair. **Risks:** abandonment, misconfiguration, abuse, and hidden enterprise blockers.

## White-glove onboarding

Use for complex enterprise identity, networking, migration, governance, or change management. Assign customer and vendor owners, milestones, dependencies, acceptance criteria, and escalation. Keep the technical workflow automated even when coordination is human-led.

**Advantages:** handles complexity and builds confidence. **Risks:** expensive bespoke work, unclear responsibility, and non-repeatable launch. Productize recurring manual tasks rather than treating every customer as unique.

## Progressive onboarding

Ask only for information required for the next meaningful outcome. A common sequence:

1. Minimal tenant and secure sandbox.
2. One scoped credential and primary workflow.
3. Result verification.
4. Production identity, roles, and secret management.
5. Integrations, webhooks, data import, and observability.
6. Governance, billing, resilience, and launch review.

Show progress, why each step matters, prerequisites, estimated effort, and recovery. Do not put architecture education before first success.

## Verification gates

Every consequential step needs an observable gate:

- Domain/email/organization control verified.
- Terms, privacy, DPA, region, and data choices recorded.
- Tenant isolation and naming policy validated.
- Identity roles and SSO tested with break-glass path.
- Credentials scoped and a test call succeeds.
- Webhook signature and retry behavior tested.
- Data import counts and integrity reconcile.
- Entitlements/limits match the sold package.
- Billing account and payer are confirmed.
- Production readiness and support ownership accepted.

A checkbox is not evidence; capture machine result, time, version, and responsible actor.

## Sandbox environments

A sandbox should be safe, disposable, representative, and clearly separated from production. Document data retention, rate limits, unsupported features, reset behavior, test identities, and simulated external effects. Use non-production credentials and synthetic data. Provide reset/cleanup without support intervention.

Avoid a sandbox so different that integration defects appear only in production. Contract, auth, error, and webhook semantics should match whenever possible.

## Data migration assistance

Start with discovery: sources, owners, volume, formats, quality, PII, residency, retention, downtime, and reconciliation requirements. Define mapping, validation rules, dry run, reject handling, cutover, delta sync, rollback, and acceptance totals.

Use encrypted transfer, least privilege, checksums, immutable source snapshots, and tenant-scoped staging. Never silently coerce or drop records. Report accepted, transformed, rejected, duplicate, and unresolved counts. Delete staging data according to agreed retention.

## Resumable automation

Each step should have stable idempotency key, explicit dependencies, bounded retries for transient failure, compensating action where safe, timeout, and manual repair. Do not email or log credentials. Quarantine partial provisioning when automatic compensation could destroy valid state.

Operator tools should show workflow graph, current state, sanitized inputs, attempts, failure, next safe actions, audit trail, and customer-visible status. Retry one step without repeating completed effects.

## Failure recovery patterns

| Failure | Safe response |
|---|---|
| Duplicate signup | Return existing workflow or deterministic conflict |
| Payment delay | Hold paid entitlement; preserve verified tenant state |
| Identity setup fails | Keep least-privilege local admin recovery path |
| Provisioning partial | Resume/repair from durable step state |
| Integration verification fails | Show diagnostic and permit retest |
| Migration mismatch | Stop cutover, reconcile, rerun idempotently |
| Customer inactivity | Remind, preserve state, expire secrets by policy |

## Success metrics

- Time to first value: request to verified primary outcome.
- Activation rate: qualified tenants reaching the activation definition.
- Step completion and abandonment.
- Median/p95 step duration and retry count.
- Manual intervention rate.
- Provisioning failure and recovery time.
- Integration verification success.
- Support contacts by step/reason.
- Production conversion and 30/90-day retained use.
- Security/compliance review cycle time for enterprise tenants.

Segment by persona, plan, integration, region, and channel without exposing personal data. Optimize the highest-impact friction, not merely the easiest step.

## Customer and internal handoff

At activation provide tenant configuration summary, owners, environments, credentials/rotation instructions, integrations, limits, billing, status/support links, runbooks, outstanding risks, and next milestones. Customer success should see activation evidence and adoption health. Support should see configuration and correlation context without secrets.

## Readiness checklist

- Happy path is idempotent, resumable, observable, and audited.
- Duplicate, retry, timeout, cancellation, and deletion are tested.
- Tenant, identity, region, data, billing, and entitlement boundaries are enforced.
- Sandbox reaches meaningful value quickly.
- Production differences and prerequisites are explicit.
- Migration includes control totals and rollback.
- Operators can repair without database improvisation.
- Metrics measure value, friction, and manual cost.

The preferred onboarding model is the least intensive one that safely handles the customer’s actual complexity; it can combine self-service product steps with white-glove coordination.