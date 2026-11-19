# Data Quality Testing Patterns

## Test contract

A useful data-quality rule names the dataset and field, business meaning, scope, evaluation window, minimum sample, threshold, severity, owner, and action. Version rules with schemas and pipelines. Quarantine or fail closed only when the consequence of bad data justifies delayed availability.

## Assertion catalog

### Completeness and nullability

Assert that required fields are present and that optional-field null rates stay within a baseline band. Great Expectations-style form:

```yaml
expectation: column_values_to_not_be_null
column: tenant_id
mostly: 1.0
severity: critical
```

For optional fields, alert on absolute null-rate increase, not only raw count. Typical starting thresholds: warning at +5 percentage points and critical at +15, tuned to business impact and sample size.

### Type, domain, and range

Validate physical type plus semantic constraints: enum membership, numeric range, regex, timezone, unit, currency, and allowed transitions. Reject impossible values immediately; report unusual but valid values as drift. Include boundary fixtures and distinguish zero from null.

### Uniqueness

Check primary keys and business idempotency keys within the correct scope and retention window. Approximate distinct counts are useful for monitoring, but financial or compliance gates need exact reconciliation. Alert on any duplicate for hard keys; use a rate threshold for soft identifiers.

### Referential integrity

Validate child keys against the authoritative parent snapshot with compatible effective times. Report orphan rate, sample keys, source partitions, and whether parents may arrive late. Use a grace window for asynchronous domains; after it expires, quarantine or repair explicitly rather than silently dropping records.

### Cross-field and aggregate invariants

Examples: `start_time <= end_time`; subtotal plus tax equals total under the declared rounding rule; accepted events equal successful plus rejected; allocation percentages sum to 100%. These often detect defects that column checks miss.

## Statistical distribution tests

### Numeric summary comparison

Track mean, standard deviation, quantiles, minimum, maximum, zero rate, and outlier rate. Relative changes work when baselines are away from zero; use absolute differences otherwise. Segment distributions by stable, relevant dimensions so mix shifts do not hide local drift.

### Population Stability Index

Bucket baseline values, calculate current proportions in the same buckets, and sum `(current - baseline) × ln(current / baseline)`. A common starting interpretation is below 0.1 stable, 0.1–0.25 investigate, above 0.25 material drift. Smooth empty bins and require sufficient samples. PSI is a heuristic, not universal proof.

### Categorical distribution

Compare top categories, unseen-category rate, entropy, and divergence. Alert when an unknown category violates a contract immediately; use Jensen–Shannon divergence or a domain threshold for allowed categories whose mix changes.

### Statistical significance

Kolmogorov–Smirnov, chi-square, or other tests can identify unlikely differences, but huge samples make trivial changes significant. Gate on both statistical confidence and effect size. Correct for multiple comparisons and record baseline version and seasonality.

## Freshness monitoring

Measure source event time, ingestion time, transformation completion, and publish time separately. Freshness rules should include expected cadence, allowed lateness, timezone, business calendar, and no-data semantics.

| Dataset cadence | Warning | Critical |
|---|---:|---:|
| Continuous stream | 2× expected inter-arrival | User-facing freshness SLO breached |
| Hourly batch | 15 minutes late | 45 minutes late |
| Daily batch | 1 hour late | Downstream deadline at risk |

Use domain-specific thresholds rather than copying this table. Distinguish quiet source behavior from pipeline failure using source heartbeat or control totals.

## Volume anomaly detection

Track row/event counts by partition and compare with matched historical periods. Useful methods include fixed bounds, rolling median with median absolute deviation, and forecast intervals for seasonal series. Suppress percentage alerts when the baseline is near zero; enforce absolute minimum changes. Detect both drops and spikes because duplicates are quality failures too.

## Schema drift

Compare field names, types, required status, enums, constraints, defaults, and nested structure. Classify changes:

- Add optional field: usually compatible, but check strict consumers.
- Add required field without default: breaking.
- Remove or rename field: breaking.
- Widen numeric type: conditionally compatible.
- Narrow range or enum: breaking for existing values.
- Change unit, timezone, or semantics: breaking even if syntax is unchanged.

Gate breaking changes in CI and monitor actual payloads for producer violations after deployment.

## Reference implementation flow

1. Read a versioned expectation suite.
2. Validate schema before row-level rules.
3. Compute control totals and quality metrics once.
4. Evaluate rules with minimum sample and lateness policy.
5. Emit machine-readable results with observed/expected values.
6. Quarantine only affected partitions where safe.
7. Alert an owner with impact, evidence, and remediation.
8. Persist results, baseline version, and pipeline version.

## Severity and action matrix

| Severity | Example | Default action |
|---|---|---|
| Info | New optional column | Record and review ownership |
| Warning | Moderate distribution shift | Continue, notify owner, inspect segments |
| High | Freshness or volume near SLO | Hold dependent publish if risk warrants |
| Critical | Missing key, tenant leakage, invoice mismatch | Stop/quarantine, page, reconcile |

## Alert payload

Include rule ID, dataset/version, field, partition, evaluation time, observed and expected values, sample size, baseline, affected downstream products, representative sanitized examples, owner, and action. Do not put raw personal data in alerts.

## Testing the tests

- Seed violations and confirm detection.
- Verify valid boundary values pass.
- Test empty, tiny, late, duplicated, and reordered input.
- Validate timezone and period transitions.
- Confirm quarantined data can be repaired and replayed idempotently.
- Measure false positives across seasonal periods.
- Reconcile quality metrics with independent control totals.

A quality check without an owner and operational response is only a statistic. A hard gate without tested recovery can become a reliability incident.