# PII Masking and Anonymization Patterns

Choose controls from purpose, adversary, linkage need, reversibility, data utility, residency, and performance. Masking a UI does not protect raw data in logs, exports, analytics, backups, or support tooling. Confirm regulatory interpretation with privacy/legal owners.

## Data Minimization

Collect, derive, retain, expose, and replicate only fields necessary for a documented purpose. Prefer coarse or derived values (age band rather than birth date) when precise data is unnecessary. This is the highest-value control because removed data cannot be leaked.

**Reversibility:** none because data is not collected. **Performance:** usually positive. **Applicability:** broadly required/expected across privacy frameworks.

## Redaction and Partial Masking

Remove values or expose limited fragments, such as `•••• 1234`. Apply at the serialization/logging boundary and default unknown sensitive fields to redacted. Keep raw access in a separate permissioned path with purpose capture and audit.

**Reversibility:** original remains in protected source. **Performance:** low cost. **Risk:** length/pattern/last digits can enable linkage; free text and nested payloads are frequently missed.

## Tokenization

Replace PII/payment values with random tokens stored in a segregated vault. Use scoped tokens so the same value does not correlate across tenants, purposes, or environments. Protect detokenization with explicit permission, reason, short-lived identity, rate limits, and audit.

**Reversibility:** controlled through vault. **Performance:** network/cache overhead and high availability needs. **Best for:** payment identifiers and workflows requiring stable references.

## Format-Preserving Encryption

Produces ciphertext in the source alphabet/length for legacy systems. It preserves structure and may leak format, equality, or distribution depending on mode. Scope tweaks/context by tenant and field; use approved standards and key management.

**Reversibility:** yes with key. **Performance:** moderate crypto overhead. **Use only when:** interface constraints genuinely require format and tokenization is unsuitable.

## Pseudonymization

Replace direct identifiers while retaining separately protected re-linking information. Use random identifiers or keyed constructions with strong secret management. Unsalted hashes of predictable email/phone/IDs are easily reversed and are not anonymization.

**Reversibility:** possible through key/table. **Regulatory effect:** reduces risk but generally remains personal data when re-identification is possible. **Performance:** low to moderate.

## k-Anonymity and Extensions

Generalize/suppress quasi-identifiers until each released row is indistinguishable from at least `k-1` others. Add l-diversity/t-closeness considerations to reduce sensitive-attribute inference.

**Reversibility:** intended to be irreversible in release. **Performance/utility:** generalization reduces analytical precision; recompute as datasets change. **Pitfalls:** background knowledge, sparse/high-dimensional data, and repeated releases enable re-identification.

## Differential Privacy

Adds calibrated noise and tracks a privacy budget (epsilon/delta) across queries/releases. Define adjacency, sensitivity, clipping, composition, budget owner, and prohibited joins. Central and local models have different trust assumptions.

**Reversibility:** no direct reversal, but poor parameters leak information. **Performance/utility:** computation and accuracy trade-off; strongest for aggregate statistics and model training/measurement with expert governance.

## Synthetic Data

Generate records from rules/models without copying individuals. Validate memorization, nearest-neighbor similarity, rare-category leakage, and membership inference. Synthetic does not automatically mean anonymous.

**Reversibility:** should be none. **Utility:** validate domain relationships and edge cases. **Use:** lower environments, demos, and analytics after disclosure-risk testing.

## Decision Matrix

| Need | Preferred pattern | Avoid |
|---|---|---|
| No business need | Minimize/delete | collecting “for later” |
| Stable operational reference | scoped tokenization | global deterministic token |
| Legacy fixed format | FPE after threat review | home-grown substitution |
| Lower-environment fixtures | generated synthetic data | production copies |
| Public aggregate statistics | differential privacy | small-cell raw aggregates |
| Support display | partial mask + audited unmask | full value in client/log |
| Research microdata | generalization/suppression plus risk review | relying on removed names only |

## Verification

Test structured/nested/free text, errors, logs/traces, analytics, caches, exports, screenshots, attachments, search indexes, backups, and deletion. Verify tenant/purpose scoping, authorized unmasking, rate limits, key/vault outage behavior, rotation, re-identification risk, latency/capacity, and audit without logging the sensitive value.
