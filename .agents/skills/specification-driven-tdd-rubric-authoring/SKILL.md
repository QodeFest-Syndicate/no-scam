---
name: specification-driven-tdd-rubric-authoring
description: Author test-first acceptance criteria, TDD rubrics, and ARCHITECTURE.md specifications that downstream builders execute without ambiguity. Use when formalizing requirements into testable specifications, defining acceptance criteria, creating architecture documents, or establishing test-driven development contracts.
---

# Specification-Driven TDD Rubric Authoring

## Purpose

Use this skill to turn product intent into an executable agreement between planners, builders, reviewers, and operators. The specification should make expected behavior, constraints, evidence, and failure handling precise enough that an independent implementer can build the system without guessing.

## Relevant Stages

- **S2 — Architecture & TDD Planning:** Primary stage for architecture formalization, acceptance criteria, test design, and task traceability.
- **S4 — Pre-Impl Gate:** Verify that the specification is complete, consistent, testable, secure, and build-ready.
- **S7 — Validation & Observability:** Trace failures back to missing or incorrect specification and revise the contract before patching symptoms.

## When to Apply

Apply this skill when:

- Requirements must become test-first implementation guidance.
- Creating or revising an `ARCHITECTURE.md` specification.
- Multiple agents or teams need a shared behavioral contract.
- Acceptance criteria are vague, subjective, or incomplete.
- API, event, data, security, or operational expectations need formalization.
- Validation reveals a gap between intended and implemented behavior.

## Core Principles

- Specify observable outcomes, not preferred internal code, unless the constraint is architecturally necessary.
- Give every normative statement a stable identifier.
- Link each requirement to verification evidence and an implementation task.
- Separate mandatory behavior from examples and non-binding guidance.
- Define negative, boundary, degraded, and recovery behavior—not only the happy path.
- Use measurable thresholds with units, windows, scope, and environment.

Use **MUST**, **MUST NOT**, **SHOULD**, and **MAY** consistently. Explain every SHOULD or document the allowed exception.

## ARCHITECTURE.md Structure

Use this structure unless the repository has a stronger convention:

1. **Document Control** — status, owners, approvers, version, date, and related decisions.
2. **Context and Goals** — problem, users, business outcome, and success metrics.
3. **Scope** — in-scope, out-of-scope, assumptions, constraints, and dependencies.
4. **System Context** — actors, external systems, trust boundaries, and data flows.
5. **Architecture** — components, responsibilities, interfaces, storage, and deployment topology.
6. **Behavioral Requirements** — numbered functional requirements and invariants.
7. **API and Data Contracts** — schemas, semantics, examples, versioning, and compatibility.
8. **Quality Attributes** — performance, availability, consistency, scalability, and cost budgets.
9. **Security and Privacy** — threat model, controls, sensitive data, residency, retention, and audit.
10. **Failure and Recovery** — timeouts, retries, idempotency, degradation, reconciliation, backup, and restore.
11. **Observability** — metrics, logs, traces, alerts, dashboards, and SLOs.
12. **Testing Strategy and TDD Rubric** — test layers, fixtures, environments, gates, and evidence.
13. **Delivery and Migration** — rollout, compatibility, migration, rollback, and feature flags.
14. **Traceability Matrix** — requirement-to-test-to-task-to-evidence mapping.
15. **Risks, Decisions, and Open Questions** — owner and due date for each unresolved item.

Keep diagrams subordinate to written contracts. Every diagram element that affects behavior should be named in the text.

## Workflow

### 1. Normalize Inputs

1. Gather product requirements, constraints, domain vocabulary, existing interfaces, incidents, and compliance obligations.
2. Identify conflicts, unstated assumptions, undefined terms, and decisions disguised as requirements.
3. Build a glossary for terms that could have multiple meanings.
4. Mark unknowns as explicit open questions with an owner and decision deadline.
5. Do not invent business policy; surface it for resolution.

### 2. Define Scope and Outcomes

- State the user or system outcome in observable terms.
- Name actors and permission levels.
- Define system boundary and excluded responsibilities.
- Record measurable success and guardrail metrics.
- State environmental assumptions such as region, scale, availability tier, and dependency guarantees.

### 3. Write Atomic Requirements

Assign stable IDs such as `FR-001`, `NFR-LAT-001`, `SEC-001`, and `DATA-001`.

Each requirement should contain:

- One obligation.
- Trigger or precondition.
- Observable behavior.
- Constraints and units.
- Error or fallback behavior.
- Verification method.

Prefer: “For authenticated tenant users, the service MUST return only records belonging to that tenant.”

Avoid: “The service should securely return data quickly.”

### 4. Translate Requirements into Acceptance Criteria

Use Given/When/Then for scenario behavior:

```text
AC-FR-001-01
Given [initial state and actor]
And [relevant dependency or data state]
When [one action or event occurs]
Then [observable result]
And [side effect, audit, or invariant]
```

Cover:

- Happy path.
- Invalid input and unauthorized access.
- Boundary values and empty states.
- Duplicate, concurrent, delayed, and out-of-order operations.
- Dependency timeout, partial failure, retry, and recovery.
- Compatibility and migration behavior.

Use property-based criteria for broad invariants:

```text
PROP-DATA-001
For all [generated inputs satisfying preconditions],
[operation] preserves [invariant],
and violations produce [defined outcome].
```

Name generators, shrink strategy, validity constraints, and reproducibility seed policy.

### 5. Author the TDD Rubric

For every requirement, define tests before implementation:

1. **Test ID and layer:** unit, contract, component, integration, end-to-end, security, performance, or resilience.
2. **Behavior under test:** linked requirement and criterion IDs.
3. **Setup:** state, identities, dependency behavior, clock, and configuration.
4. **Test data:** fixture/generator and privacy classification.
5. **Stimulus:** action, event, request, or fault injection.
6. **Assertions:** outputs, state transitions, side effects, telemetry, and absence of forbidden behavior.
7. **Threshold:** exact pass/fail condition and measurement window.
8. **Evidence:** report, log, trace, benchmark, scan, or artifact location.

Order work in red–green–refactor increments. Tests must fail for the intended reason before implementation and remain deterministic unless explicitly statistical.

### 6. Specify API and Data Contracts

For each API, event, or dataset, define:

- Operation/topic/subject, actor, authorization, and idempotency behavior.
- Request/message and response schemas with required, optional, nullable, default, and unknown-field rules.
- Field semantics, units, time zones, identifiers, ordering, and enum behavior.
- Success, validation, authentication, authorization, conflict, throttling, and dependency-error outcomes.
- Pagination, filtering, rate limits, timeouts, retries, and correlation IDs.
- Versioning, backward/forward compatibility, deprecation, and migration policy.
- Valid, invalid, minimum, maximum, and compatibility examples.

Do not use examples as substitutes for schemas or normative behavior.

### 7. Specify Test Data

- Define minimal deterministic fixtures for core behavior.
- Define synthetic generators for volume, distributions, relationships, edge cases, and invalid cases.
- Preserve referential integrity and domain invariants.
- Use fixed seeds or record seeds for reproducibility.
- Prohibit production PII unless explicitly approved and protected.
- Specify tenant separation, clock control, IDs, and cleanup behavior.
- Include dataset size and shape for performance tests.

### 8. Integrate the Threat Model

1. Identify assets, actors, entry points, data flows, dependencies, and trust boundaries.
2. Enumerate threats using STRIDE or the project's chosen method.
3. Link each threat to a control requirement and abuse-case test.
4. Cover authentication, authorization, tenant isolation, injection, secrets, encryption, logging, supply chain, and availability abuse.
5. Record residual risk, owner, approval, and review date.
6. Require security criteria to pass the same pre-implementation and release gates as functional criteria.

### 9. Link Specs to Tasks

Every implementation task should reference requirement and test IDs. Maintain a traceability matrix:

| Requirement | Acceptance Criteria | Tests | Task | Evidence | Status |
|---|---|---|---|---|---|
| FR-001 | AC-FR-001-01 | CT-001, E2E-003 | TASK-012 | report path | Planned |

Reject orphan requirements, unlinked tests, and tasks with no acceptance criterion.

### 10. Run the Completeness Gate

Review the document with a builder, tester, security reviewer, and operator perspective. A specification passes only when unresolved questions cannot materially change implementation, safety, or acceptance.

If S7 reveals a specification gap:

1. Reproduce the failure and identify the absent or incorrect rule.
2. Update the normative requirement and acceptance criterion.
3. Add or amend the failing test.
4. Re-evaluate impacted tasks and contracts.
5. Record the specification revision and reason.

## Checklists

### Specification Completeness

- [ ] Goals, non-goals, actors, scope, assumptions, and glossary are explicit.
- [ ] Components, ownership, dependencies, trust boundaries, and data flows are defined.
- [ ] Requirements are atomic, identified, measurable, and verifiable.
- [ ] APIs and data contracts cover errors, compatibility, and examples.
- [ ] Acceptance criteria include negative, boundary, concurrency, and degraded cases.
- [ ] Test data, environments, fixtures, generators, and seeds are specified.
- [ ] Performance, reliability, security, privacy, observability, and cost are measurable.
- [ ] Migration, rollout, rollback, and recovery behavior are defined.
- [ ] Threats map to controls and abuse-case tests.
- [ ] Every requirement maps to tests, tasks, and expected evidence.
- [ ] Open questions have owners and due dates; no build-blocking unknown remains.

### TDD Rubric Quality

- [ ] Tests can be written before implementation.
- [ ] Pass/fail conditions do not require subjective interpretation.
- [ ] Test layers avoid unnecessary duplication.
- [ ] Mocks preserve relevant dependency semantics.
- [ ] Assertions include state, side effects, and observability where relevant.
- [ ] Statistical tests define sample size, tolerance, and confidence.
- [ ] Flaky timing and external dependencies are controlled.

## Key Patterns

- **Requirement ID chain:** Stable links from intent through criterion, test, task, and evidence.
- **Example plus invariant:** Concrete scenarios explain behavior; properties cover the larger input space.
- **Contract-first boundary:** Define interfaces and compatibility before internal implementation.
- **Decision table:** Represent combinations of permissions, states, or policies without prose ambiguity.
- **Error taxonomy:** Standardize error classes, retryability, exposure, and observability.
- **Spec feedback loop:** Validation failures update the contract and tests before implementation fixes.

## Anti-Patterns

- Using “fast,” “secure,” “robust,” or “user-friendly” without measurable definitions.
- Writing criteria that assert internal method names instead of observable behavior.
- Treating mock success as integration proof.
- Specifying only the happy path.
- Embedding undecided choices as facts.
- Over-specifying local implementation details that do not protect a requirement or quality attribute.
- Creating one giant end-to-end test for many independent requirements.
- Copying production data into test environments without governance.
- Letting diagrams, examples, or tickets contradict the normative specification.

## Output Format Expectations

Produce a **Specification Package** containing:

1. **Architecture Specification:** Structured sections above with stable requirement IDs.
2. **Acceptance Criteria Catalog:** Given/When/Then scenarios and property-based invariants.
3. **TDD Rubric:** Test IDs, layers, setup, data, assertions, thresholds, and evidence.
4. **Threat Model:** Assets, boundaries, threats, controls, abuse tests, and residual risks.
5. **Traceability Matrix:** Requirement-to-criterion-to-test-to-task-to-evidence links.
6. **Completeness Decision:** Pass, conditional pass, or block, with owned gaps and due dates.
