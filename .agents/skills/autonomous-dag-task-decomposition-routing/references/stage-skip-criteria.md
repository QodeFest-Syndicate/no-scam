# Stage Skip Criteria (S0–S8)

Use **Execute**, **Reuse**, **Compress**, **Skip**, or **Escalate**. A skip record must name evidence, owner, decision date, expiry, assumptions, transferred risk, and a fallback trigger. Policy-mandated security, compliance, data-loss, and production-release gates cannot be skipped for schedule.

## S0 — Pre-Ops Evaluation

- **Skip only if:** an authorized, current stage plan exists for the exact scope and no assumptions changed.
- **Evidence:** approved execution profile, scope fingerprint, policy evaluation, expiry.
- **Risk:** required stages disappear silently.
- **Fallback:** pause and rerun S0 when scope, risk, environment, or policy changes.

## S1 — Domain and Data Scoping

- **Safe reuse/skip:** boundaries, owners, data classes, residency, retention, actors, and obligations are unchanged and recently validated.
- **Evidence:** approved domain map, data inventory, regulatory applicability, owner attestation.
- **Never skip when:** adding data sources, tenants, regions, vendors, sensitive fields, or processing purposes.
- **Fallback:** stop design/implementation, classify unknown data conservatively, and rebuild the scope map.

## S2 — Architecture and TDD Planning

- **Safe reuse:** architecture, contracts, threat model, acceptance criteria, and tests cover the change without amendment.
- **Compress when:** low-risk internal correction changes no boundary, persistent schema, public contract, privilege, or SLO.
- **Risk:** incompatible implementations and untestable acceptance.
- **Fallback:** extract interface/decision nodes, update specification and tests, then replan descendants.

## S3 — Task Decomposition and Routing

- **Compress when:** one atomic task has one owner, output, verification step, and no shared mutable resource.
- **Evidence:** bounded task statement, dependencies, acceptance, budget, rollback.
- **Risk:** hidden prerequisites, integration, or ownership gaps.
- **Fallback:** create a DAG when work splits, blocks, exceeds budget, or crosses boundaries.

## S4 — Pre-Implementation Gate

- **Skip only if:** policy explicitly permits it and the work cannot affect runtime, data, security, compliance, contracts, or production artifacts.
- **Evidence:** testable spec, threat/risk review, approvals, plan output, rollback readiness.
- **Never skip:** privileged, destructive, regulated, production, migration, or cross-tenant changes.
- **Fallback:** halt mutation, preserve evidence, remediate gate failures, and obtain explicit approval.

## S5 — Implementation

- **Skip when:** output is analysis, planning, or research with no requested repository/runtime change.
- **Reuse when:** an immutable existing artifact exactly meets acceptance and provenance is verified.
- **Risk:** claiming delivery without a buildable artifact.
- **Fallback:** add an implementation node and invalidate downstream evidence that assumed it existed.

## S6 — Integration and CI/CD

- **Skip when:** no executable/deployable artifact or integration surface exists.
- **Compress when:** a scoped change is covered by a trusted existing pipeline; run focused checks plus mandatory gates.
- **Evidence:** build identity, tests, scans, contract verification, artifact digest, promotion policy.
- **Fallback:** restore full pipeline, quarantine unverified artifacts, and rerun affected gates.

## S7 — Validation and Observability

- **Never fully skip for delivered behavior.** Reuse only current evidence from the exact artifact and environment; compress for non-runtime artifacts through independent review and link validation.
- **Evidence:** acceptance results, telemetry, security checks, rollback/restore proof, known limitations.
- **Risk:** successful commands mistaken for correct outcomes.
- **Fallback:** stop promotion, add missing signals/tests, reproduce, and revalidate deployed state.

## S8 — Delivery and GTM

- **Skip when:** internal-only work has no release, customer, operator, onboarding, or commercial output.
- **Compress when:** only internal publication/hand-off is needed.
- **Evidence:** release artifact, provenance, migration/rollback notes, ownership, support and compatibility.
- **Fallback:** withhold release, complete the delivery packet, and communicate corrected scope.

## Decision Record Template

| Stage | Decision | Evidence/version | Assumptions | Risk | Owner | Expires | Fallback trigger |
|---|---|---|---|---|---|---|---|
| Sx | Execute/Reuse/Compress/Skip/Escalate | [artifact] | [unchanged facts] | [accepted/transferred] | [owner] | [date/event] | [condition] |

Reassess every decision after scope, contract, threat, data, environment, estimate, incident, or policy changes. Silence is never approval.
