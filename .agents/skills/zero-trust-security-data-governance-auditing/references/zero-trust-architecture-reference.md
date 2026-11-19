# Zero-Trust Architecture Reference

Zero trust assumes network location is not evidence of trust. Verify every access from identity, device/workload posture, resource, action, tenant, environment, context, and risk; grant the minimum permission for the shortest useful period; assume breach and contain blast radius.

## Core Architecture

- **Identity provider:** authenticates humans and workloads with phishing-resistant MFA, federation, certificate or workload identity, and short-lived credentials.
- **Policy information points:** supply identity claims, device posture, workload provenance, resource classification, threat/risk, tenant, region, time, and network context.
- **Policy decision point:** evaluates versioned deny-by-default policy and returns allow/deny plus obligations.
- **Policy enforcement point:** intercepts every protected request at API gateway, service, data, queue, administration, and deployment boundaries.
- **Telemetry plane:** records attributed decisions and continuously feeds detection and risk.

Cache decisions only within bounded lifetimes and define revocation propagation. Services must fail closed for privileged or restricted operations when policy cannot be evaluated.

## Identity-Centric Security

Use separate identities for humans, services, jobs, deployment automation, and emergency access. Prefer OIDC/SPIFFE-style workload identity or managed roles over shared/static secrets. Bind tokens to issuer, audience, subject, expiry, tenant, environment, and intended workload. Reauthorize sensitive actions rather than treating session possession as permanent trust.

Access reviews must include inherited roles, cross-account trusts, dormant identities, service principals, vendor access, privilege-escalation paths, and break-glass use. Separation of duties should cover approval, deployment, key administration, billing, and audit.

## Micro-Segmentation

Segment by trust and failure boundary, not merely subnet. Enforce authenticated service-to-service policy, namespace/account isolation, default-deny ingress and egress, tenant-aware data policy, and constrained administrative paths. Cell architectures limit incident scope by partitioning workloads, tenants, stores, keys, and queues.

Network policy complements—not replaces—application authorization. An internal source still needs authenticated identity and resource-level permission.

## Continuous Verification

Reevaluate on privilege change, device/workload posture drift, anomalous behavior, risk increase, sensitive action, token age, region change, or policy update. Continuous access evaluation needs low-latency revocation, session invalidation, derived-permission cleanup, and deterministic behavior when signals are unavailable.

## Device and Workload Attestation

Human device signals may include managed enrollment, disk encryption, patch level, screen lock, endpoint health, and phishing-resistant key presence. Workload attestation may include signed image digest, trusted builder/provenance, cluster/node identity, namespace/service account, runtime policy, and measured boot. Treat posture as time-bound evidence, not a permanent label.

## Cloud-Native Implementation Layers

| Layer | Controls |
|---|---|
| Edge | DDoS protection, TLS, identity-aware proxy, schema/rate enforcement |
| Identity | federation, MFA, workload identity, short token lifetime, access review |
| Service | mTLS, policy enforcement, tenant context, input validation, authorization |
| Data | row/object policy, classification, encryption, tenant/region binding, masking |
| Platform | namespace/account isolation, network policy, admission control, signed artifacts |
| Delivery | OIDC CI identity, least permissions, protected environments, policy/scans |
| Observability | attributed audit decisions, tamper evidence, alerts, redaction |

## Least-Privilege Lifecycle

Start from a named use case. Enumerate exact resources/actions and conditions; simulate allowed and denied paths; deploy with monitoring; compare observed use while preserving rare recovery duties; remove unused grants; assign owner and expiry. Explicit deny guardrails protect sensitive operations, regions, public exposure, and audit/security-control disablement.

## Failure Modes to Design

Cover identity-provider outage, stale policy cache, revocation delay, missing posture signal, clock skew, expired certificate, partitioned policy service, logging failure, break-glass activation, and compromised workload identity. Define fail-open exceptions narrowly with owner, compensating controls, maximum duration, and audit.

## Verification Evidence

Retain policy versions, identity/role inventory, effective-permission simulation, denied-path tests, token/certificate configuration, segmentation tests, attestation results, revocation timing, break-glass exercise, audit samples, and exceptions. A passed scanner is evidence for one control—not proof of zero trust.
