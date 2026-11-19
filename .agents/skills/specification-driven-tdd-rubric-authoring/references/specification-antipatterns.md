# Specification Anti-Patterns

Use this catalog during architecture review and pre-implementation gates. A defect is not fixed until the normative contract, its test, and traceability links agree.

## Specification by Wishful Thinking

**Signal:** outcomes such as “highly available,” “real-time,” or “handles scale” appear without workload, metric, threshold, environment, cost, or failure behavior.

**Consequence:** builders optimize different targets and reviewers cannot decide pass/fail.

**Repair:** define actor and workload, metric and unit, percentile/window, environment, excluded errors, degraded behavior, and verification evidence. Convert aspirations into NFR IDs.

## Implicit Knowledge Trap

**Signal:** “as usual,” undocumented acronyms, tribal business rules, examples that only insiders understand, or dependency behavior assumed but not stated.

**Consequence:** new implementers guess; mocks encode folklore; incidents expose conflicting interpretations.

**Repair:** create a glossary, decision table, explicit invariants, external contract, ownership, and open-question register. Interview operators and support teams; turn examples into normative rules only after confirmation.

## Over-Specification

**Signal:** requirements prescribe class names, helper methods, database queries, library choices, or internal call order without an architectural constraint.

**Consequence:** harmless refactors fail acceptance, solutions cannot improve, and behavior is obscured by implementation detail.

**Repair:** specify observable behavior, compatibility, security, cost, and quality constraints. Keep mandatory technology only when required by policy, interoperability, operations, or a recorded decision; state the rationale and expiry condition.

## Under-Specification

**Signal:** schemas omit required/null/default rules; APIs list only success; permissions say “authorized user”; retries, ordering, units, and versioning are absent.

**Consequence:** independently correct components disagree at boundaries and edge cases become production policy by accident.

**Repair:** define actors, preconditions, schema semantics, error taxonomy, timeouts, idempotency, concurrency, boundaries, negative cases, recovery, compatibility, and exact acceptance thresholds.

## Moving Target Without Versioning

**Signal:** requirements are edited in place after implementation begins; approvals, baselines, change reasons, and impact analysis are missing.

**Consequence:** tests appear stale, completed work is repeatedly invalidated, and no one knows which contract a release satisfies.

**Repair:** version the specification, record status and approvers, maintain a revision log, freeze release baselines, and trace each change to impacted requirements, tests, tasks, migrations, and rollout plans. Define deprecation windows for external contracts.

## Orphaned Specifications

**Signal:** requirements have no test, task, owner, evidence, consumer, or release gate; tests reference IDs absent from the current spec.

**Consequence:** documents decay into commentary and passing pipelines do not prove intended behavior.

**Repair:** assign stable IDs and maintain requirement → criterion → test → task → evidence links. Fail the pre-implementation gate for mandatory untested requirements and flag tests with missing/stale references.

## Contradictory Authorities

**Signal:** diagram, API schema, ticket, runbook, and prose define different behavior; no source has precedence.

**Consequence:** teams select whichever source supports their implementation.

**Repair:** declare normative sources and precedence. Generate derived artifacts where possible; validate schemas/examples; record unresolved conflicts as owned blockers.

## Happy-Path Monoculture

**Signal:** criteria cover only successful requests under healthy dependencies.

**Consequence:** authorization, duplicates, races, timeouts, partial failure, recovery, and migration are designed during incidents.

**Repair:** require negative, boundary, unauthorized, concurrent, degraded, retry, reconciliation, rollback, and compatibility scenarios based on risk.

## Example-as-Contract

**Signal:** one JSON sample or sequence diagram is treated as the complete schema and semantics.

**Consequence:** omitted fields, unknown values, ordering, precision, and invalid cases remain undefined.

**Repair:** pair examples with machine-validatable schemas and prose semantics. Include minimum, maximum, invalid, compatibility, and error examples.

## Unowned Ambiguity

**Signal:** TODOs and “TBD” items have no owner or decision date, yet downstream work proceeds.

**Consequence:** assumptions silently harden into incompatible implementations.

**Repair:** record each unknown, material impact, options, decision owner, deadline, temporary assumption, and invalidation trigger. Block work when the answer can change safety, contract, or architecture.

## Detection Checklist

- Can an independent builder identify every actor, state, boundary, contract, and failure outcome?
- Can a tester write deterministic tests before implementation?
- Does every quality claim have units, threshold, scope, and window?
- Are normative rules distinguishable from examples and guidance?
- Are security threats linked to controls and abuse-case tests?
- Does every requirement have an owner, test, task, evidence, and version?
- Can change impact be computed without relying on memory?

A specification passes only when remaining questions cannot materially change implementation, safety, compatibility, operations, or acceptance.
