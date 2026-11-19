# Compliance Framework Matrix

This engineering crosswalk supports scoping and evidence collection; it is not legal advice, a definitive control mapping, or certification. PDPA obligations vary by jurisdiction. Confirm scope with qualified privacy, compliance, and legal owners.

## Shared-Control Crosswalk

| Control domain | PDPA | GDPR | SOC 2 | HIPAA | Typical evidence | Frequency |
|---|---|---|---|---|---|---|
| Governance/risk | accountability and protection | accountability, risk/DPIA | CC1–CC4 risk/governance | risk analysis/management | scope, policies, risk register, approvals | annual and on material change |
| Data inventory/purpose | notification/consent/purpose | records, lawful basis, transparency | privacy/confidentiality scope | PHI inventory, permitted use | data map, ROPA, purpose/lawful-basis record | continuous/quarterly review |
| Access control | reasonable security | Art. 32 security | logical access criteria | unique user, access control, minimum necessary | IAM/RBAC, reviews, MFA, revocation samples | quarterly and event-driven |
| Encryption/key management | protection safeguards | risk-appropriate security | confidentiality/security controls | addressable encryption safeguards | configs, key policy, rotation/decryption tests | continuous/annual review |
| Rights/requests | access/correction and local rights | access, correction, erasure, restriction, portability, objection | privacy criteria if scoped | access/amendment/accounting rights | workflow tests, identity checks, request samples | per request/quarterly sampling |
| Retention/deletion | retention limitation where applicable | storage limitation and erasure | privacy/confidentiality retention | required retention and secure disposal | schedule, deletion jobs, backup handling | monthly/annual policy review |
| Vendors/transfers | data intermediary/transfer duties | processors, SCCs/adequacy/TIA | vendor risk controls | BAAs and business associates | contracts, due diligence, transfer/BAA inventory | before onboarding/annual |
| Incidents/breach | notification duties vary | supervisory notice within applicable window | incident response/communication | breach notification requirements | plan, exercise, timeline, incident samples | annual exercise/per incident |
| Logging/monitoring | security evidence | accountability/security | monitoring criteria | audit controls | immutable logs, alerts, review records | continuous |
| Change management | security/accountability | privacy/security by design | change-management criteria | integrity/security risk management | tickets, approvals, tests, deployment evidence | every change |

## Framework-Specific Emphasis

### PDPA

Determine the exact jurisdiction and role. Validate notice, consent or other permitted processing basis, purpose limitation, accuracy, protection, retention, access/correction, breach obligations, data-intermediary duties, and overseas transfer controls. Do not treat one country’s PDPA requirements as universal.

### GDPR

Record controller/processor roles, lawful basis, transparency, records of processing, data-subject rights, privacy by design/default, DPIA triggers, DPO/representative requirements, processors/subprocessors, international transfer mechanism and TIA, special-category/children’s data, and 72-hour supervisory notification analysis where applicable.

### SOC 2

Define system boundary, audit period, Trust Services Categories in scope, control owner, population, sample, and design versus operating-effectiveness evidence. Security is required; availability, processing integrity, confidentiality, and privacy are scoped based on commitments. Evidence must show operation over time, not policy existence alone.

### HIPAA

Determine covered-entity/business-associate status and PHI/ePHI scope. Address Privacy, Security, and Breach Notification requirements: minimum necessary, authorizations, individual rights, risk analysis, workforce/security management, physical safeguards, access/audit/integrity/transmission controls, contingency planning, BAAs, and breach risk assessment.

## Common Non-Conformities and Remediation

| Finding | Why it fails | Remediation/evidence |
|---|---|---|
| Inventory omits logs/backups/analytics | lifecycle and scope incomplete | automated lineage plus owner attestation; deletion/restore tests |
| Broad or stale privileged access | least privilege and accountability weak | role redesign, expiry, review, revocation and denied-path test |
| Policy exists but operation unproved | design evidence is not effectiveness | population, representative samples, timestamps, independent review |
| Vendor list differs from data flows | processors/transfers/BAAs missed | reconcile procurement, network, IAM, billing, and data maps |
| Encryption without key governance | confidentiality depends on uncontrolled keys | separation of duties, rotation, disable/recovery tests, key audit logs |
| Rights deletion misses derived stores | request remains partially unfulfilled | lineage-aware deletion across caches, indexes, exports, and backups |
| Breach plan has no timed exercise | notification feasibility unknown | scenario exercise with decision timeline and preserved evidence |

## Evidence Record

For every mapped control record framework citation, internal control ID, system/tenant/region, owner, frequency, test method, population/sample, immutable evidence ID, result, exception, compensating control, remediation date, and reviewer. An `N/A` result needs documented scope rationale and approval.
