---
name: zero-trust-security-data-governance-auditing
description: Enforce zero-trust security policies, least-privilege IAM, encryption, PII masking, and multi-tenant data-residency rules with PDPA/GDPR/SOC2 compliance auditing. Use when conducting threat modeling, reviewing IAM policies, auditing data governance, enforcing encryption boundaries, or generating compliance attestations.
---

# Zero-Trust Security, Data Governance, and Auditing

## Purpose

Use this skill to evaluate and enforce identity-centered security, data governance, tenant isolation, and auditable compliance across application, cloud, infrastructure, container, and delivery boundaries. It produces evidence-based decisions; it does not equate a checklist with legal advice or certification.

## Relevant Stages

- **S1 — Domain & Data Scoping:** Identify regulatory obligations, data classes, residency, retention, actors, and trust boundaries.
- **S2 — Architecture & TDD Planning:** Build threat models, RBAC matrices, encryption boundaries, and security acceptance criteria.
- **S4 — Pre-Impl Gate:** Mandatory review for high-risk access, data, infrastructure, and production changes.
- **S6 — Integration & CI/CD:** Run IaC, image, dependency, secret, and policy scans with release gates.
- **S7 — Validation & Observability:** Verify penetration-test findings, audit logs, runtime controls, and remediation.
- **S8 — Delivery & GTM:** Assemble scoped compliance evidence and attestations.

## When to Apply

Apply this skill when:

- Designing or reviewing authentication, authorization, service identities, or IAM policies.
- Handling PII, sensitive business data, secrets, regulated records, or tenant data.
- Changing encryption, network, storage, residency, backup, or logging boundaries.
- Introducing infrastructure, containers, third-party services, or CI/CD credentials.
- Preparing PDPA, GDPR, or SOC 2 control evidence.
- Verifying security findings, audit anomalies, or zero-trust policy violations.

## Zero-Trust Principles

Enforce these defaults:

- Verify explicitly using identity, device/workload posture, resource, action, context, and risk.
- Grant least privilege for the shortest practical duration.
- Assume breach; isolate tenants, workloads, networks, credentials, and blast radius.
- Authenticate and authorize every request at each trust boundary.
- Prefer short-lived workload identity over static credentials.
- Continuously evaluate policy and log security-relevant decisions.
- Deny by default; fail closed for privileged or sensitive operations.

## Workflow

### 1. Establish Scope and Obligations

1. Identify systems, environments, cloud accounts, regions, tenants, data stores, pipelines, vendors, and owners.
2. Map applicable contracts and regulatory obligations by data subject and processing location.
3. Record intended processing purpose, lawful basis or authorization basis, retention, and deletion obligations.
4. Identify crown-jewel assets and unacceptable outcomes.
5. Define audit period, evidence sources, sampling method, and known exclusions.
6. Engage qualified legal or compliance owners for jurisdiction-specific interpretation.

### 2. Classify Data

Use project-specific labels, with a default four-tier model when none exists:

- **Public:** Approved for unrestricted disclosure.
- **Internal:** Non-public operational information with limited harm if exposed.
- **Confidential:** Customer, tenant, financial, proprietary, or security-sensitive information.
- **Restricted:** PII, credentials, keys, regulated data, or information with severe exposure impact.

For each dataset and field, record:

- Owner and steward.
- Purpose and lawful/authorized use.
- Data subjects and tenant.
- Source, destinations, lineage, and processors.
- Region and allowed residency/transfer locations.
- Encryption, masking, tokenization, and access requirements.
- Retention, deletion, backup, and legal-hold rules.

Default unknown data to the more restrictive classification until resolved.

### 3. Map Trust and Data Flows

- Diagram actors, workloads, entry points, identity providers, policy decision/enforcement points, networks, stores, queues, vendors, and administrative paths.
- Mark trust boundaries, tenant boundaries, regions, encryption termination, and plaintext exposure.
- Trace data through collection, processing, caching, logging, analytics, backup, export, and deletion.
- Identify bypass paths such as support tools, break-glass accounts, direct database access, and CI/CD automation.

### 4. Create and Review the Threat Model

1. Enumerate assets, adversaries, abuse goals, entry points, dependencies, and trust assumptions.
2. Apply STRIDE or the organization's approved method to every boundary and component.
3. Include cross-tenant access, privilege escalation, identity spoofing, injection, exfiltration, ransomware, supply-chain compromise, insider misuse, and denial of service.
4. Rate likelihood and impact using the project's risk matrix.
5. Map threats to preventive, detective, and recovery controls.
6. Define abuse-case tests and evidence for each material control.
7. Record residual risks, owner, approver, expiration, and treatment plan.

Revisit the threat model when identities, data classes, vendors, regions, interfaces, or deployment topology change.

### 5. Design and Verify Least-Privilege IAM

Inventory human users, service accounts, workload identities, groups, roles, policies, API keys, cross-account trusts, and emergency access.

For each principal, verify:

- Specific resources and actions required for a named use case.
- Deny-by-default behavior and no unintended wildcard expansion.
- Environment and tenant boundaries.
- Conditions for region, network, device/workload identity, time, and MFA where appropriate.
- Short-lived credentials and automated rotation.
- Separation of duties for approval, deployment, key management, billing, and audit.
- Inactive, orphaned, duplicate, inherited, and privilege-escalation paths.
- Access review owner and expiry.

Use access logs and policy simulation to reduce permissions based on observed need, while accounting for infrequent recovery duties.

### 6. Build and Validate the RBAC Matrix

Create a matrix with roles as rows and resource/action pairs as columns. Include tenant scope, environment, conditions, approval, and audit requirements.

Validate:

- Every allowed action maps to a business capability.
- No role combines conflicting duties without approved compensating controls.
- Administrative actions are distinct from routine data access.
- Tenant-scoped roles cannot enumerate or access other tenants.
- Denied and unauthorized cases are tested, not only allowed paths.
- Role changes revoke cached sessions and derived permissions within a defined window.
- Break-glass access is time-bound, approved, monitored, and reviewed after use.

### 7. Enforce Encryption Boundaries

**In transit:**

- Require modern TLS for external and service-to-service traffic.
- Validate peer identity; use mTLS where workload identity and risk require it.
- Prohibit plaintext protocols across trust boundaries.
- Manage certificate issuance, rotation, revocation, and expiry monitoring.

**At rest:**

- Encrypt databases, object stores, disks, queues, logs, backups, snapshots, and exports containing confidential or restricted data.
- Use managed key services or approved HSM-backed keys.
- Separate key administration from data administration.
- Define rotation, disablement, deletion protection, recovery, and audit behavior.
- Use tenant-specific keys where contractual isolation or blast-radius requirements demand it.

Document where decryption occurs and minimize plaintext lifetime and exposure.

### 8. Mask and Protect PII

- Collect only fields necessary for the documented purpose.
- Mask restricted fields in logs, traces, analytics, support tooling, lower environments, and exports.
- Prefer tokenization or format-preserving substitutes when workflows need stable references.
- Use irreversible anonymization only when re-identification risk has been assessed.
- Restrict unmasking to explicit permissions, reason capture, and audit.
- Test structured, nested, free-text, attachment, and error-message leakage.
- Apply deletion and correction to derived stores, indexes, caches, and backups according to policy.

Do not treat hashing predictable identifiers without a protected secret as anonymization.

### 9. Enforce Multi-Tenant Residency and Isolation

1. Bind every data object, request, job, cache entry, index record, backup, and log to tenant and region metadata.
2. Derive tenant context from verified identity, never from an untrusted request field alone.
3. Enforce isolation at multiple layers: API policy, query predicates, storage policy, encryption keys, queues, and network boundaries.
4. Route processing and storage only to permitted regions and approved subprocessors.
5. Block cross-region replication, backup, telemetry, and support access unless policy permits it.
6. Test cross-tenant reads, writes, enumeration, cache collisions, background jobs, exports, restores, and administrative workflows.
7. Reconcile configured residency with actual resource, replica, backup, and vendor locations.

### 10. Audit Secrets Management

- Locate secrets in source, history, CI variables, images, manifests, logs, tickets, chat exports, and runtime configuration.
- Require a managed secret store, scoped access, short lifetimes where possible, rotation, and audit logs.
- Use workload identity to retrieve secrets at runtime; do not bake secrets into images or artifacts.
- Protect CI/CD federation with repository, branch, environment, and audience conditions.
- Verify rotation does not require unsafe downtime and revoked secrets stop working.
- Treat exposed secrets as compromised: rotate, invalidate sessions, assess access, and preserve incident evidence.

Never include secret values in audit output.

### 11. Scan IaC, Containers, and the Supply Chain

Run release-gated checks for:

- IaC misconfiguration, public exposure, weak IAM, missing encryption, unrestricted egress, and absent logging.
- Policy-as-code violations against organization and residency rules.
- Container vulnerabilities, malware, embedded secrets, root execution, writable filesystems, excess capabilities, and unsigned images.
- Dependency vulnerabilities, licenses, provenance, lockfile integrity, and malicious packages.
- Artifact signatures, SBOM generation, trusted builders, and deployment-time verification.

Triage findings by exploitability, reachability, data sensitivity, exposure, and compensating controls—not severity score alone. Exceptions require owner, rationale, compensating control, and expiry.

### 12. Review Audit Logs and Runtime Enforcement

Ensure audit records capture:

- Actor/workload identity, action, resource, tenant, region, decision, policy/rule, timestamp, correlation ID, and result.
- Authentication events, privilege changes, policy updates, secret/key operations, exports, unmasking, break-glass use, and administrative data access.

Verify logs are access-controlled, encrypted, tamper-evident, time-synchronized, retained appropriately, and monitored. Alert on denied-action bursts, unusual regions, dormant-role use, privilege escalation, bulk access, audit disablement, and policy bypass.

Do not log credentials, tokens, full restricted payloads, or unnecessary PII.

### 13. Verify Penetration-Test Findings

For each finding:

1. Confirm scope, affected version, exploit preconditions, and evidence.
2. Reproduce safely in an authorized environment.
3. Identify root cause and all equivalent exposure paths.
4. Implement the control and add a regression or abuse-case test.
5. Retest the original exploit and likely bypasses.
6. Confirm telemetry detects attempted exploitation.
7. Record remediation evidence, residual risk, and independent verifier.
8. Close only when the deployed target is verified; code changes alone are insufficient.

### 14. Audit PDPA, GDPR, and SOC 2 Controls

Tailor with compliance owners. At minimum assess:

**PDPA/GDPR privacy controls**

- Purpose limitation, data minimization, notice/consent or other lawful basis.
- Data-subject access, correction, portability where applicable, objection, and deletion workflows.
- Processor/subprocessor governance and cross-border transfer safeguards.
- Retention, breach response, privacy by design, and records of processing.
- Protection of sensitive/special-category data and children's data where applicable.

**SOC 2 trust services controls**

- Security governance, risk assessment, access control, change management, vulnerability management, incident response, vendor management, and monitoring.
- Availability, confidentiality, processing integrity, and privacy controls when included in scope.
- Evidence of control design and operating effectiveness over the audit period.

Map obligations to named controls, owners, systems, evidence, frequency, test method, exceptions, and remediation.

### 15. Generate the Compliance Attestation

An attestation must be scoped and evidence-backed. Include:

- System boundary, period, criteria/framework, environments, and exclusions.
- Control mapping and evidence identifiers.
- Testing method, sample, and result.
- Exceptions, residual risks, compensating controls, owners, and target dates.
- Management approval and independent review where required.

Use precise language such as “evidence reviewed for the stated scope and period.” Do not claim certification, universal compliance, or legal adequacy unless an authorized body has established it.

## Mandatory Gate Checklist

- [ ] Scope, data classes, tenants, regions, vendors, and obligations are identified.
- [ ] Threat model covers current architecture and material abuse cases.
- [ ] IAM and RBAC are deny-by-default, least-privilege, and tested for escalation.
- [ ] Encryption covers data at rest, in transit, backups, and key lifecycle.
- [ ] PII minimization, masking, unmasking, retention, and deletion are enforced.
- [ ] Tenant isolation and residency are tested across application and data layers.
- [ ] Secrets are managed, rotated, scanned, and absent from artifacts and logs.
- [ ] IaC, images, dependencies, SBOM, signatures, and policy checks pass.
- [ ] Audit logs capture security decisions without leaking restricted data.
- [ ] Critical/high findings are remediated or have approved time-bound exceptions.
- [ ] Rollback and incident response preserve evidence and containment.

## Operational Audit Checklist

- [ ] Access reviews cover human, service, vendor, and break-glass identities.
- [ ] Runtime policy matches declared IAM, RBAC, residency, and encryption design.
- [ ] Key, certificate, token, and secret expiry/rotation are monitored.
- [ ] Backups and restores preserve tenant, residency, encryption, and deletion rules.
- [ ] Penetration-test fixes are verified on deployed targets.
- [ ] Compliance evidence is complete, immutable, time-bounded, and owned.
- [ ] Exceptions have expiry, compensating controls, and remediation status.

## Key Patterns

- **Policy decision/enforcement split:** Centralize policy logic while enforcing it at every relevant boundary.
- **Short-lived workload identity:** Federate trusted workload claims instead of distributing static keys.
- **Tenant-context propagation:** Carry verified tenant and region claims through requests, events, jobs, stores, and telemetry.
- **Cell-based isolation:** Limit blast radius by partitioning tenants and workloads into independently controlled cells.
- **Evidence-as-code:** Generate repeatable control evidence from versioned policy, configuration, scans, and tests.
- **Time-bound exception:** Require owner, rationale, compensating control, expiry, and review.

## Anti-Patterns

- Trusting requests because they originate inside a private network.
- Granting wildcard permissions for convenience or future use.
- Using shared service accounts without workload attribution.
- Accepting client-provided tenant IDs as authorization.
- Encrypting primary storage while leaving logs, snapshots, caches, or exports exposed.
- Masking UI output while retaining unrestricted raw PII in analytics or support tools.
- Treating a passed scanner as proof of security.
- Closing findings after a source-code fix without deployed verification.
- Storing long-lived cloud credentials in CI/CD.
- Claiming compliance without scope, period, criteria, and evidence.

## Output Format Expectations

Produce a **Zero-Trust and Governance Audit Package** containing:

1. **Scope and Obligations:** Systems, period, data classes, tenants, regions, frameworks, and exclusions.
2. **Trust/Data Flow and Threat Model:** Assets, boundaries, threats, controls, tests, and residual risks.
3. **IAM/RBAC Review:** Principals, effective permissions, escalation paths, findings, and remediation.
4. **Data Protection Review:** Encryption, keys, masking, retention, residency, isolation, and deletion.
5. **Delivery Security Results:** IaC, container, dependency, secret, SBOM, signature, and policy evidence.
6. **Runtime and Pen-Test Verification:** Audit-log findings, reproduced issues, fixes, bypass tests, and deployed proof.
7. **Compliance Control Matrix:** Requirement, control, owner, evidence, frequency, result, and exception.
8. **Attestation:** Scoped conclusion, limitations, residual risks, approvals, and gate decision.
