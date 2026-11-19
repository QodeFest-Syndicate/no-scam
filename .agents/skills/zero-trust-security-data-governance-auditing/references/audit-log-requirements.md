# Audit Log Requirements

Audit logs must explain security-relevant decisions without becoming a secondary source of credentials or PII. Separate security audit events from debug/application logs and define authoritative producers.

## Events to Capture

- authentication success/failure, MFA, token/session issuance and revocation;
- authorization allow/deny for privileged or restricted actions;
- role, group, policy, trust, and service-account changes;
- secret, certificate, and key create/read/rotate/disable/delete-policy events;
- restricted-data reads, writes, deletes, exports, unmasking, and bulk access;
- tenant/region/residency policy decisions and cross-boundary attempts;
- administrative/support actions, impersonation, break-glass, and direct data access;
- configuration, deployment, security-control, audit, backup, and restore changes;
- workflow approvals, exceptions, incident actions, and evidence access.

Do not log passwords, tokens, private keys, session cookies, full restricted payloads, unnecessary PII, or unredacted connection strings.

## Event Schema

At minimum include event ID and schema version; UTC event time and ingest time; actor/workload identity and authentication context; action; resource type/ID; tenant and region; source and target; policy/rule/version; decision and reason code; result/error class; correlation/trace/request ID; environment; producer; and integrity metadata.

Use normalized schemas such as OCSF for cross-product analytics or CEF for SIEM interchange when they fit. Preserve original vendor events alongside normalized fields when normalization can lose semantics. Define required/null/unknown behavior and backward compatibility.

## Identity and Time Integrity

Attribute service actions to workload identity and originating actor where delegation occurs. Shared accounts are unacceptable without compensating attribution. Synchronize clocks, monitor drift, preserve source timezone when supplied, and distinguish event occurrence from collection delay.

## Immutability and Access

Send events off the originating system promptly. Use append-only/WORM or equivalent protected storage, object lock where appropriate, encryption, least-privilege write/read roles, separate log administrators, integrity hashes/signatures, and monitored deletion/retention-policy changes. Producers should not be able to alter retained records.

Audit access to audit logs. Break-glass access is time-bound, approved, monitored, and reviewed.

## Availability and Failure Behavior

Define queueing, backpressure, local buffering, sequence IDs, deduplication, and recovery when the sink is unavailable. Privileged or regulated actions may need to fail closed when authoritative audit cannot be recorded; lower-risk actions may buffer with explicit limits and alerts. Test loss, duplication, delay, reordering, and replay.

## Retention and Privacy

Set retention by event category, regulatory/contract need, investigation window, litigation hold, storage cost, and data minimization. Document hot/searchable and archive periods, residency, backup, legal hold, deletion approval, and destruction evidence. Apply rights/retention handling to unnecessary personal data without destroying records that must legally be retained; involve qualified owners.

## Detection and Incident Response

Alert on denied-action bursts, impossible travel or unusual regions, dormant identity use, privilege escalation, new trust relationships, bulk access/export, key/secret operations, audit disablement, retention changes, log gaps, clock drift, break-glass use, cross-tenant access, and repeated policy bypass.

For each alert define query, threshold/window, minimum volume, severity, owner, triage context, false-positive handling, containment action, evidence retention, and validation cadence. Link audit events across identity, application, cloud, data, and delivery planes using stable correlation identifiers.

## Quality and Coverage Controls

Measure expected-versus-received producers/events, schema rejection, parse failure, duplicates, late arrival, timestamp drift, redaction failures, storage lag, query availability, retention compliance, and alert exercise results. Maintain canary audit events and end-to-end synthetic checks.

## Review Checklist

- Threat model maps material actions and controls to events.
- Required fields have stable semantics and schema versions.
- Sensitive values are redacted at source and tested in errors/free text.
- Logs are encrypted, access-controlled, tamper-evident, and off-host.
- Outage behavior, buffering, loss detection, and replay are tested.
- Retention, residency, legal hold, and destruction are owned.
- Detection rules are exercised and tied to response playbooks.
- Evidence identifies exact scope, period, producer, query, and reviewer.
