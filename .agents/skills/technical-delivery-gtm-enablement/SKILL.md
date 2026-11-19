---
name: technical-delivery-gtm-enablement
description: Package deployed FaaS/SaaS/PaaS platforms into sellable products with API documentation, developer portals, tenant onboarding automation, and enterprise GTM playbooks. Use when publishing API/SDK documentation, configuring developer portals, automating tenant onboarding, creating sales enablement materials, or packaging commercial offerings.
---

# Technical Delivery and GTM Enablement

## Purpose

This skill turns a working FaaS, SaaS, or PaaS platform into a product that buyers can evaluate, developers can adopt, tenants can onboard to, operators can support, and commercial teams can sell accurately. It aligns product packaging, technical documentation, onboarding, compliance evidence, SLAs, and enterprise go-to-market execution.

## When to Apply

Apply this skill when work includes:

- Publishing OpenAPI, API reference, SDK, or quickstart documentation.
- Building or configuring a developer portal.
- Automating tenant signup, verification, provisioning, and first-use activation.
- Defining product tiers, feature flags, quotas, packaging, or pricing documentation.
- Creating demos, solution briefs, objection handling, or sales engineering assets.
- Preparing an enterprise GTM playbook.
- Summarizing security, privacy, compliance, and operational evidence for buyers.
- Defining an SLA or aligning commitments with actual product scope.
- Validating buyer personas, adoption friction, and commercial viability.
- Preparing production delivery at S8.

Product claims must be supported by shipped capabilities and current evidence.

## Stage Alignment

- **S1 — Domain & Data Scoping:** identify buyer personas, urgent problems, willingness to pay, adoption constraints, and commercial viability.
- **S8 — Delivery & GTM:** package the product, publish documentation, configure portals, automate onboarding, prepare compliance and SLA materials, and enable sales and customer success.

Earlier-stage outputs may supply architecture, security, reliability, metering, and validation evidence, but this skill converts them into buyer- and developer-ready delivery artifacts.

## Core Principles

1. **Package outcomes, not internal components.** Buyers purchase resolved problems and bounded risk.
2. **Keep one source of truth.** Product behavior, API schemas, plan entitlements, and SLA metrics should generate or validate downstream materials.
3. **Make the first success fast.** A qualified developer should reach a meaningful result with minimal decisions.
4. **Automate the happy path and expose recovery.** Onboarding needs idempotency, status, retries, and support escalation.
5. **Separate public commitments from aspirations.** Roadmap items and unsupported configurations are labeled clearly.
6. **Match evidence to audience.** Developers need executable detail; security teams need controls; executives need outcomes and risk.
7. **Protect tenant boundaries from signup onward.** Identity, data, quotas, billing, and support context remain isolated.
8. **Measure activation and expansion.** Documentation and onboarding are product surfaces with conversion metrics.

## Step-by-Step Workflow

### 1. Validate Buyer and Commercial Fit

For each target persona, capture:

- Organization type, scale, and operating context.
- Economic buyer, technical buyer, champion, user, security reviewer, and procurement stakeholder.
- Trigger event and urgent job to be done.
- Current alternative and switching cost.
- Required integrations, deployment model, data residency, and support expectations.
- Success metric and expected time to value.
- Budget owner, purchasing motion, and acceptable pricing basis.
- Common objections and disqualifiers.

Validate commercial viability:

1. Confirm the problem is frequent, costly, and owned.
2. Connect product capabilities to measurable outcomes.
3. Test whether packaging reflects distinct willingness to pay.
4. Estimate delivery, infrastructure, support, compliance, and sales costs.
5. Identify a repeatable ideal customer profile rather than relying on one-off customization.
6. Define evidence that advances a buyer from interest to technical validation to purchase.

**Exit condition:** the primary persona, use case, value claim, purchasing path, and unit-economic assumptions are explicit.

### 2. Define the Product Package

Create a capability matrix by tier:

- Core workflows and included features.
- Usage allowances, quotas, rate limits, seats, regions, and retention.
- Security, identity, audit, networking, and data-governance options.
- Support channel, response target, onboarding assistance, and success services.
- SLA eligibility and exclusions.
- Integration and deployment options.
- Metering, overage, commitment, and contract rules.

Use product tiers to serve coherent customer segments, not to create arbitrary friction.

Typical pattern:

- **Free or developer:** rapid evaluation, constrained scale, community or self-service support.
- **Pro or team:** production use, higher limits, collaboration, standard support, and paid overage.
- **Enterprise:** governance, SSO, audit, private connectivity, negotiated scale, compliance evidence, SLA, and success plan.

Document feature dependencies and avoid selling a tier combination the provisioning system cannot enforce.

### 3. Implement Feature and Entitlement Control

- Define stable entitlement keys independent of UI labels.
- Keep plan-to-entitlement mappings versioned.
- Support tenant-specific overrides with owner, reason, approval, and expiry.
- Evaluate entitlements server-side for authoritative access control.
- Use feature flags for rollout control, not as the permanent billing ledger.
- Separate release flags, experiment flags, operational kill switches, and commercial entitlements.
- Provide an auditable view of effective tenant capabilities.
- Test upgrades, downgrades, grace periods, expired trials, and removed features.

### 4. Author the OpenAPI Contract

- Use the supported OpenAPI version and validate the document in CI.
- Define servers, authentication, security scopes, tags, operations, and stable operation IDs.
- Provide typed request, response, error, pagination, filtering, and webhook schemas.
- Include constraints, formats, enums, defaults, examples, and required fields.
- Describe idempotency, retries, rate limits, timeouts, and asynchronous behavior.
- Document versioning, compatibility, deprecation, and sunset policy.
- Avoid secrets, production identifiers, and personal data in examples.
- Generate or test server stubs, clients, mocks, and contract tests from the same schema where practical.

For every operation, answer:

- What outcome does it produce?
- Who may call it?
- What inputs and limits apply?
- What does success look like?
- Which errors are actionable and retryable?
- How is the request traced or supported?

### 5. Build Reference Documentation

Organize by user task rather than internal service layout:

1. Overview and concepts.
2. Authentication and authorization.
3. Quickstart.
4. Core workflows.
5. API or command reference.
6. Errors and troubleshooting.
7. Limits and quotas.
8. Webhooks and asynchronous events.
9. Versioning and migration.
10. Security and support.

Each reference page should state prerequisites, inputs, outputs, side effects, permissions, failure modes, and a tested example. Label preview, deprecated, and unavailable features visibly.

### 6. Document SDKs and Quickstarts

For each supported SDK:

- Publish package name, supported runtime versions, compatibility policy, and release notes.
- Show secure credential loading without hard-coded secrets.
- Provide typed examples for the primary workflow, pagination, retries, and errors.
- Document timeout and retry defaults.
- Link methods to their API operations.
- Test snippets against a sandbox or deterministic mock in CI.
- State maintenance status and support channel.

A quickstart should reach one meaningful success quickly:

1. Create or access a sandbox tenant.
2. Obtain a scoped credential.
3. Install the SDK or prepare an API request.
4. Execute the primary workflow.
5. Verify the result in API output and portal state.
6. Clean up any created resource.
7. Point to the next production-readiness steps.

Do not start with exhaustive architecture before the first successful result.

### 7. Configure the Developer Portal

The portal should provide:

- Searchable concepts, guides, API reference, SDKs, changelog, status, and support.
- Authentication-aware access to credentials, applications, webhooks, usage, limits, and environments.
- Sandbox and production separation.
- Copyable examples in supported languages.
- Clear version, lifecycle, and last-updated signals.
- Feedback and broken-example reporting.
- Analytics for search failures, drop-off, activation, and recurring errors.

Portal controls:

- Use SSO and role-based access where required.
- Never reveal full secrets after creation.
- Audit credential creation, rotation, and revocation.
- Prevent cross-tenant resource discovery.
- Apply content review, link checking, schema validation, accessibility checks, and tested snippets in publishing workflows.

### 8. Automate Tenant Onboarding

Model onboarding as a durable workflow with explicit states:

1. Signup or contract activation.
2. Email, domain, identity, or organization verification.
3. Terms, privacy, region, and data-processing choices.
4. Tenant and billing-account creation.
5. Identity roles, SSO, or invitations.
6. Namespace, database, keys, quotas, and baseline configuration.
7. Plan entitlement and feature assignment.
8. Sandbox or production credential issuance.
9. Guided integration and first successful action.
10. Activation confirmation, usage visibility, and support handoff.

Automation requirements:

- Use idempotency keys and resumable steps.
- Persist workflow status and failure reason.
- Retry transient failures with bounded backoff.
- Compensate or quarantine partial provisioning.
- Avoid sending credentials through email or logs.
- Enforce regional, tenancy, and naming policy at creation.
- Emit audit events and activation analytics.
- Provide operator retry, cancel, and escalation controls.
- Test duplicate signup, delayed payment, failed verification, downgrade, and deletion flows.

### 9. Align the SLA with Product Scope

Define:

- Covered service and eligible plans.
- Availability or performance metric and calculation formula.
- Measurement point, data source, and reporting timezone.
- Commitment period and target.
- Exclusions, maintenance policy, and force-majeure treatment.
- Incident notification and support response targets.
- Claim process, evidence, deadlines, and service-credit schedule.
- Maximum liability or credit limits as approved by legal and finance.
- Relationship to internal SLOs and error-budget policy.

The public SLA must not exceed architecture, support coverage, provider dependencies, disaster recovery, or observed operational capability. Keep internal SLOs stricter than external commitments where practical.

### 10. Prepare Compliance Attestation Summaries

Create a concise evidence-backed summary covering applicable areas:

- Security governance and control ownership.
- Identity, access, least privilege, and review cadence.
- Encryption in transit and at rest.
- Tenant isolation and data-flow boundaries.
- Data classification, retention, deletion, residency, and subprocessors.
- Secure development, dependency management, and vulnerability response.
- Logging, monitoring, incident response, and business continuity.
- Independent attestations, certifications, reports, and validity dates.
- Customer responsibilities and shared-responsibility boundaries.
- Evidence access process, NDA requirements, and security contact.

Distinguish certified, audited, implemented, planned, and not applicable. Do not imply that cloud-provider compliance automatically certifies the product.

### 11. Generate the Sales Enablement Kit

Include:

- One-sentence positioning and category.
- Ideal customer profile and persona cards.
- Problem, impact, and trigger-event narrative.
- Capability-to-outcome map with proof.
- Tier and pricing overview.
- Discovery questions and qualification criteria.
- Demo script with setup, storyline, expected output, and recovery path.
- Competitive alternatives and truthful differentiation.
- Common objections with evidence-backed responses.
- Security, architecture, integration, SLA, and procurement FAQ.
- Reference architecture and implementation timeline.
- Approved claims, prohibited claims, and escalation contacts.

Keep collateral versioned with product releases and assign owners and review dates.

### 12. Structure the Enterprise GTM Playbook

Use the following flow:

1. **Market focus:** ideal customer profile, excluded segments, regions, and verticals.
2. **Buying committee:** economic, technical, security, legal, procurement, and user stakeholders.
3. **Qualification:** pain, authority, urgency, budget, technical fit, and risk.
4. **Discovery:** current state, desired outcomes, data, integrations, governance, and timeline.
5. **Solution mapping:** capabilities, gaps, responsibilities, and success criteria.
6. **Technical validation:** demo, workshop, sandbox, proof of value, or pilot.
7. **Security and compliance:** questionnaire, evidence room, architecture review, and remediation path.
8. **Commercial process:** package, usage assumptions, proposal, negotiation, and approvals.
9. **Procurement and legal:** terms, DPA, SLA, subprocessors, and vendor setup.
10. **Implementation:** onboarding owner, milestones, dependencies, acceptance, and enablement.
11. **Adoption and expansion:** activation, health, business review, renewal, and growth signals.

Define entry and exit criteria, owner, standard artifacts, expected duration, and escalation path for every stage.

### 13. Validate Delivery End to End

Run a clean-room evaluation with participants who did not build the system:

- A developer completes the quickstart using only published material.
- An administrator creates users, roles, credentials, and integrations.
- A tenant sees correct plan features, limits, usage, and support path.
- A seller runs the approved demo and answers common objections.
- A security reviewer finds current evidence and shared responsibilities.
- An operator observes and repairs a failed onboarding step.
- Customer success can identify activation and adoption state.
- Finance can connect packaging to metering and billing behavior.

Record time to first value, completion rate, failure points, support requests, inaccurate claims, and manual interventions. Fix the highest-friction steps before broad launch.

## Checklists

### Documentation Readiness

- [ ] OpenAPI validates and matches deployed behavior.
- [ ] Authentication, errors, limits, retries, versioning, and deprecation are documented.
- [ ] Quickstarts and SDK snippets pass automated tests.
- [ ] Examples contain no secrets or tenant-specific data.
- [ ] Search, navigation, accessibility, links, and feedback paths work.
- [ ] Preview and deprecated features are labeled consistently.

### Onboarding Readiness

- [ ] Provisioning is idempotent, resumable, observable, and auditable.
- [ ] Tenant, region, identity, entitlement, billing, and data boundaries are enforced.
- [ ] Partial failure, duplicate request, retry, cancellation, and cleanup are tested.
- [ ] Credentials are scoped, displayed safely, and rotatable.
- [ ] First value and production-readiness steps are measurable.
- [ ] Operators can inspect and repair failed workflows.

### Commercial Package Readiness

- [ ] Tiers map to coherent personas, entitlements, limits, support, and billing.
- [ ] Feature flags and provisioning can enforce sold packages.
- [ ] Pricing units and usage assumptions are understandable and viable.
- [ ] Upgrades, downgrades, trials, grace periods, and overrides are defined.
- [ ] Public claims match deployed and supported capabilities.

### Enterprise Readiness

- [ ] SLA scope and calculations align with internal SLOs and operational evidence.
- [ ] Compliance summaries distinguish attestations from unverified claims.
- [ ] Sales, security, legal, procurement, onboarding, and support handoffs have owners.
- [ ] Demo, proof-of-value, and implementation paths have success criteria.
- [ ] Collateral versions and review dates are visible.
- [ ] Launch risks, exceptions, and unsupported configurations are explicit.

## Key Patterns

- **Schema-first documentation:** validated API contracts generate reference material and tests.
- **Executable quickstart:** every critical example runs against a sandbox or deterministic mock.
- **Resumable onboarding saga:** durable steps and compensations recover from partial provisioning.
- **Entitlement matrix:** one versioned mapping connects tiers, flags, quotas, docs, and sales claims.
- **Evidence-backed claim:** every security, reliability, or performance statement links to current proof.
- **Progressive disclosure:** first success is simple; production depth is available when needed.
- **Stage-gated enterprise motion:** each GTM stage has owner, evidence, and exit criteria.
- **Closed-loop activation:** portal and onboarding analytics drive prioritized product improvements.

## Anti-Patterns

- Publishing API reference that is manually copied from implementation and drifts.
- Describing only happy paths while omitting errors, limits, and retries.
- Requiring sales or support to repair every tenant signup manually.
- Using feature flags as the only source of commercial entitlement truth.
- Creating arbitrary tiers that do not map to buyer needs or delivery cost.
- Promising roadmap features as available capabilities.
- Claiming compliance based solely on an infrastructure provider.
- Setting an SLA without a precise formula, evidence source, or eligible scope.
- Starting quickstarts with lengthy architecture and no working result.
- Sending long-lived credentials through email, chat, examples, or logs.
- Building a developer portal without search, ownership, or freshness signals.
- Producing generic sales collateral with no persona, proof, or qualification guidance.
- Treating signed contract as completion rather than the start of activation and adoption.

## Output Format Expectations

When applying this skill, produce a delivery and GTM packet with:

1. **Commercial thesis:** target personas, urgent problem, value, alternatives, viability, and assumptions.
2. **Packaging matrix:** tiers, capabilities, limits, entitlements, support, SLA, billing, and exceptions.
3. **Documentation inventory:** OpenAPI, guides, references, SDKs, quickstarts, changelog, and owners.
4. **Developer portal plan:** information architecture, authenticated tools, publishing controls, and analytics.
5. **Onboarding workflow:** states, inputs, automation, retries, compensation, audit, and support path.
6. **SLA definition:** scope, formula, target, source, exclusions, claims, credits, and internal alignment.
7. **Compliance summary:** controls, attestations, dates, evidence access, gaps, and shared responsibility.
8. **Sales enablement kit:** positioning, personas, discovery, demo, differentiation, objections, and FAQs.
9. **Enterprise GTM playbook:** stages, owners, artifacts, entry and exit criteria, and escalation.
10. **Validation results:** clean-room outcomes, time to value, failure points, claim review, and fixes.
11. **Launch decision:** readiness by function, unresolved risks, exceptions, owner, and go/no-go status.

Write public-facing material in customer language and operational material in precise implementation language. Label source-of-truth systems, owners, versions, evidence dates, and unvalidated assumptions.
