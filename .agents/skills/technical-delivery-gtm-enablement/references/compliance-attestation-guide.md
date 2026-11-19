# Compliance Attestation Package Guide

## Claims policy

Distinguish **certified**, **independently audited**, **internally implemented**, **planned**, and **not applicable**. State scope, legal entity, product/environment, period, auditor, report date, and expiry. A cloud provider’s certification does not certify the product. Legal and qualified compliance professionals should review contractual templates.

## Package index

Maintain an evidence register with artifact, control/domain, scope, owner, issue date, expiry/review date, confidentiality, NDA requirement, storage location, and approved audience. Use access-controlled sharing and log downloads. Never distribute a full restricted report when a summary or auditor portal is required.

## SOC 2 Type II summary

A customer-facing summary should include:

- Audited entity and system scope.
- Trust Services Criteria covered.
- Review period and independent auditor.
- Opinion type stated accurately.
- Complementary user-entity controls.
- Subservice organizations and carve-in/carve-out method.
- Exceptions summarized with approved language and remediation status.
- Report availability, NDA, request process, and validity date.

Do not paraphrase the auditor’s opinion in a way that changes meaning. Type I addresses design at a point in time; Type II covers design and operating effectiveness over a period.

## GDPR Data Processing Agreement template outline

1. Parties, roles (controller/processor), scope, duration, and subject matter.
2. Processing nature/purpose, data categories, and data-subject categories.
3. Documented instructions and confidentiality.
4. Article 32 security measures and evidence.
5. Subprocessor authorization, list, notice, and flow-down terms.
6. International transfer mechanism and supplementary measures.
7. Data-subject request assistance.
8. Breach notification and cooperation.
9. DPIA/regulator assistance.
10. Return/deletion and backup lifecycle.
11. Audit/information rights.
12. Contact, precedence, liability linkage, and termination.
13. Annexes: processing details, technical/organizational measures, subprocessors, transfer terms.

Tailor to actual roles, jurisdictions, data flows, residency, and service model. Do not publish a generic template as executed legal advice.

## Security whitepaper structure

- Executive scope and shared-responsibility model.
- Architecture, tenancy, trust boundaries, and data flow.
- Governance, risk, policies, training, and control ownership.
- Identity, least privilege, SSO/MFA, access reviews, and privileged access.
- Encryption in transit/at rest and key management.
- Tenant isolation and network controls.
- Secure development, reviews, testing, dependency/supply-chain security.
- Vulnerability management and penetration testing.
- Logging, detection, response, notification, and forensics.
- Availability, backup, disaster recovery, and tested objectives.
- Data classification, retention, deletion, residency, and subprocessors.
- Compliance scope and independent assurance.
- Customer responsibilities and secure configuration.
- Document version, evidence date, owner, and contact.

Use architecture-approved facts and avoid absolutes such as “fully secure” or “never.”

## Penetration test summary

Include test provider and independence, scope/assets/environment, dates, methodology/standards, constraints/exclusions, severity method, findings by severity, high-level categories, remediation state, retest date/result, residual risk acceptance, and full-report access process.

Do not publish exploit steps, sensitive architecture, target identifiers, or unresolved detail broadly. “No critical findings” is meaningful only with scope and date. Separate automated scanning from penetration testing.

## Vendor security questionnaire preparation

Build an approved answer library linked to evidence and owners. Normalize recurring domains: governance, IAM, encryption, application security, infrastructure, tenant isolation, vulnerability management, logging/incident response, continuity, privacy, data lifecycle, subprocessors, compliance, personnel, and AI where applicable.

For each answer record product/deployment scope, standard response, evidence, reviewer, last review, expiry, and escalation. Answer the actual customer question; do not copy an adjacent control. Mark customer-configurable or shared responsibilities.

## Evidence-room access tiers

| Tier | Examples | Access |
|---|---|---|
| Public | Security page, subprocessor list, trust overview | Open |
| Customer | Whitepaper, policy summaries, certificates | Authenticated customer |
| NDA | SOC 2 report, pen-test executive report, detailed architecture | Approved requester |
| Restricted | Raw findings, configs, internal policies, incident evidence | Need-to-know review only |

Apply watermarking, expiry, download restrictions where suitable, and a revocation process. Protect secrets and personal data regardless of tier.

## Shared responsibility

For every control clarify provider responsibility, customer responsibility, configurable options, defaults, and evidence. Common customer duties include identity lifecycle, role assignment, credential security, lawful data, retention configuration, endpoint/webhook security, monitoring their integrations, and incident contacts.

## Freshness and change triggers

Review evidence on schedule and when architecture, cloud region, subprocessor, legal entity, encryption, data category, deployment model, incident process, certification scope, or audit result changes. Remove superseded versions from general distribution while retaining records according to policy.

## Response workflow

1. Qualify requester, opportunity/customer, scope, deadline, NDA, and required framework.
2. Reuse approved current answers and evidence.
3. Route gaps to named security, privacy, legal, engineering, or operations owners.
4. Label planned controls with target and approval; never present them as implemented.
5. Review for product/deployment accuracy and confidential data.
6. Deliver through approved channel and record version/access.
7. Capture new reusable questions after approval.

## Attestation quality checklist

- Scope and dates are explicit.
- Product claims match deployed behavior.
- Auditor/certification language is exact.
- Exceptions and gaps are not hidden.
- Evidence is current, owned, and access-controlled.
- DPA terms match actual data flows and subprocessors.
- Security summaries include customer responsibilities.
- Pen-test claims state scope and retest status.
- Questionnaire answers link to evidence and expiry.
- Sales teams know approved and prohibited claims.

A strong package accelerates trust by making bounded, current evidence easy to evaluate—not by maximizing the number of compliance logos.