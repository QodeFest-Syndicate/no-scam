---
name: usage-based-metering-billing-integration
description: Implement event metering pipelines, quota webhooks, and tiered SaaS/FaaS entitlement systems for usage-based billing. Use when configuring usage tracking, billing tier logic, metering APIs, quota enforcement, or integrating with payment/subscription platforms.
---

# Usage-Based Metering and Billing Integration

## Purpose

This skill converts product consumption into accurate, auditable usage records, entitlement decisions, invoices, and tenant-facing reports. It connects commercial pricing metrics to technical events while protecting customers from duplicate charges, stale quota decisions, and opaque reconciliation.

## When to Apply

Apply this skill when work includes:

- Selecting or validating billable usage metrics.
- Designing collection, aggregation, rating, or reconciliation pipelines.
- Implementing usage ingestion APIs or event schemas.
- Enforcing plan entitlements, quotas, limits, or overages.
- Integrating Stripe or another subscription and payment platform.
- Building free, pro, enterprise, pay-per-use, or hybrid plans.
- Tracking SaaS seats, storage, API calls, jobs, or feature consumption.
- Tracking FaaS invocations, execution time, memory, egress, or provisioned capacity.
- Testing billing webhooks and invoice accuracy.
- Producing tenant usage dashboards, statements, or exports.

Use financial precision, explicit time semantics, and immutable audit evidence throughout.

## Stage Alignment

- **S1 — Domain & Data Scoping:** validate pricing metrics, customer value, unit economics, and data availability.
- **S5 — Core Build:** implement usage events, aggregation, entitlement, quota, rating, and billing integration.
- **S7 — Validation & Observability:** verify completeness, deduplication, totals, webhook behavior, and reconciliation.
- **S8 — Delivery & GTM:** package plans, connect subscriptions, expose usage reporting, and operationalize billing.

## Core Principles

1. **Meter value, not implementation accidents.** A pricing metric should be understandable, controllable, and aligned with customer benefit.
2. **Raw events are immutable evidence.** Corrections append adjustments rather than silently rewriting history.
3. **Every event is idempotent.** Retries and replays must not create duplicate charges.
4. **Event time and processing time are distinct.** Late and out-of-order events follow a documented policy.
5. **Entitlement is not invoice state.** Access decisions, measured usage, rated charges, and payment collection are separate concerns.
6. **Money uses exact arithmetic.** Use integer minor units or fixed-precision decimals with explicit currency and rounding rules.
7. **Tenant isolation is mandatory.** Authentication cannot choose an arbitrary billing subject.
8. **Reconciliation is a product capability.** Internal totals, provider totals, invoices, credits, and customer reports must be explainable.

## Step-by-Step Workflow

### 1. Validate the Pricing Metric

For each candidate metric, determine:

- What customer value it represents.
- Whether customers can forecast and control it.
- Whether it can be measured completely and consistently.
- Whether marginal price supports infrastructure cost, support cost, and target margin.
- Whether optimization would create harmful product behavior.
- Whether the metric is contractually and legally explainable.
- Whether free allowance, minimum commitment, cap, credit, or volume discount is required.

Evaluate commercial viability with representative tenants:

1. Model low, median, high, bursty, and seasonal consumption.
2. Estimate revenue, direct cost, gross margin, and invoice volatility.
3. Compare price with customer value and credible alternatives.
4. Stress-test discounts, credits, free tiers, and enterprise commitments.
5. Reject metrics whose measurement error or infrastructure coupling makes invoices hard to defend.

**Exit condition:** every priced dimension has a definition, source, unit, owner, cost model, and customer explanation.

### 2. Define the Metering Contract

A usage event should include:

- Globally unique event identifier.
- Schema and producer version.
- Tenant and billing-account identifiers derived from trusted context.
- Meter name and unit.
- Quantity as an exact numeric value.
- Event timestamp and ingestion timestamp.
- Resource or feature identifier where needed.
- Idempotency or deduplication key.
- Source service, region, environment, and correlation identifier.
- Adjustment or reversal reference when applicable.
- Non-sensitive dimensions needed for rating and reporting.

Specify:

- Accepted units and conversion rules.
- Timestamp precision and billing timezone.
- Maximum lateness and correction window.
- Deduplication scope and retention.
- Validation behavior for unknown meters or plans.
- Schema compatibility and deprecation policy.
- Privacy classification and retention policy.

### 3. Build the Event Metering Pipeline

Use explicit stages:

1. **Capture:** the product emits usage at the authoritative completion point.
2. **Authenticate:** the edge verifies producer identity and derives tenant scope.
3. **Validate:** schema, unit, range, timestamp, and entitlement context are checked.
4. **Persist raw evidence:** append the original accepted event to durable storage.
5. **Deduplicate:** reject or collapse repeated event identifiers deterministically.
6. **Enrich:** attach versioned plan, account, region, or pricing context without mutating the raw event.
7. **Aggregate:** roll up by tenant, meter, time window, and required dimensions.
8. **Rate:** apply the correct price version, allowance, tier, discount, and rounding rule.
9. **Export:** send provider usage records or generate internal invoice line items.
10. **Reconcile:** compare source events, aggregates, rated amounts, provider state, invoices, and reports.

Prefer an outbox or transactional event pattern when business completion and usage emission must remain atomic. Route poison events to a reviewable dead-letter path without silently dropping them.

### 4. Implement Collection and Aggregation

- Emit events only after the billable action reaches its defined success state.
- Distinguish attempts, successful work, retries, cache hits, cancellations, and customer-caused failures.
- Preserve producer sequence or source offsets where useful for gap detection.
- Use watermarking for late data and publish provisional versus final totals.
- Keep aggregation windows and timezone boundaries explicit.
- Recompute aggregates from immutable events when practical.
- Version aggregation logic and retain lineage to raw inputs.
- Make backfills replay-safe and isolate them from real-time alerting.
- Use compensating adjustment events for corrections.

For high volume, partition by a stable tenant or account key while guarding against hot tenants and uneven meter distribution.

### 5. Model Plans and Entitlements

Represent entitlements as versioned policy rather than scattered conditional code.

#### Free / Pro / Enterprise

- Free: bounded allowance, limited features, and clear upgrade behavior.
- Pro: larger allowance, paid overage or fixed limits, and self-service management.
- Enterprise: negotiated limits, commitments, discounts, regions, support, and contractual overrides.

#### Pay-Per-Use

- Rate each approved unit without a recurring allowance, or combine it with minimum spend.
- Expose near-real-time usage and configurable spend controls.
- Define treatment for late usage after invoice finalization.

#### Hybrid

- Combine subscription fee, included allowance, tiered overage, seats, feature access, or prepaid credits.
- Specify the order of operations: allowance, credits, discounts, minimums, taxes, and rounding.

Entitlement decisions should include:

- Subject and tenant.
- Feature or meter.
- Allowed action and limit.
- Consumption snapshot and reservation state.
- Policy or plan version.
- Decision reason and expiry.

### 6. Design Quota Enforcement and Webhooks

Choose an enforcement mode per feature:

- **Hard limit:** deny when the authoritative limit is reached.
- **Soft limit:** allow but warn, throttle, or create overage.
- **Reservation:** reserve units before expensive work and commit or release afterward.
- **Rate limit:** constrain consumption over a short rolling window.
- **Spend limit:** stop or require approval when projected cost crosses a threshold.

A quota webhook should:

- Authenticate and verify the caller.
- Derive tenant and subject from trusted credentials.
- Accept an idempotency key and requested quantity.
- Return allow, deny, or conditional decision with reason and policy version.
- Return remaining or reserved quantity only when safe and useful.
- Use a strict timeout and defined fail-open or fail-closed policy.
- Log a decision record without exposing sensitive commercial terms.
- Support commit and release for reservations.

Cache entitlement policy cautiously. Include version and expiry, and invalidate on subscription or contract change. Do not rely on asynchronous billing-provider webhooks for millisecond quota decisions.

### 7. Integrate Billing Platforms

#### Stripe Pattern

- Map internal billing accounts to Stripe customers using an immutable link.
- Map internal price versions to Stripe products and prices; never infer meaning from display names.
- Create subscriptions with idempotency keys and persist provider object IDs.
- Send usage using the provider's current meter or usage-record model.
- Verify webhook signatures against the raw request body.
- Deduplicate webhook event IDs before applying side effects.
- Handle events asynchronously and return success only after durable receipt.
- Fetch current provider state when event ordering is ambiguous.
- Separate invoice creation, payment status, access policy, and collections workflows.
- Test with provider clocks or equivalent time controls where available.

#### Custom Rating Pattern

- Version rate cards with effective intervals.
- Resolve the price version using event time and contract context.
- Use deterministic tier calculation and exact arithmetic.
- Generate immutable invoice line items with source aggregate references.
- Apply credits and adjustments as explicit ledger entries.
- Finalize invoices only after lateness and reconciliation policy passes.

### 8. Address SaaS and FaaS Metering

#### SaaS Considerations

- Define seat semantics: assigned, active, peak, average, or concurrent.
- Distinguish stored bytes from transferred bytes and logical from physical storage.
- Decide whether automated, admin, and internal operations are billable.
- Handle shared resources and parent-child organizations explicitly.
- Align feature usage with plan entitlements and feature flags.

#### FaaS Considerations

- Distinguish invocation attempts, successful invocations, retries, and platform-generated calls.
- Define duration boundaries and rounding increments.
- Include allocated memory, CPU, accelerator, or architecture where pricing depends on them.
- Meter provisioned concurrency separately from execution where applicable.
- Define treatment for cold starts, timeouts, cancellations, and asynchronous retries.
- Measure network egress with source, destination class, and unit rules.
- Prevent duplicate billing when a platform retries delivery.

### 9. Build Tenant Usage Reporting

- Provide current period, finalized periods, allowance, overage, credits, and forecast.
- State timezone, freshness, finalization status, and unit definitions.
- Let tenants filter or export by approved dimensions.
- Keep reports consistent with invoice line items and provider totals.
- Mark provisional data and explain late-event adjustments.
- Apply tenant authorization at query time and storage boundaries.
- Avoid exposing internal costs, negotiated data from other tenants, or high-cardinality raw events by default.

### 10. Verify Metering Accuracy

Test invariants such as:

- Accepted unique events equal persisted unique raw events.
- Aggregate quantities equal the sum of included raw quantities plus adjustments.
- No event contributes to more than one mutually exclusive bucket.
- Rated line items reference a valid price and aggregate version.
- Provider-reported usage matches exported usage within defined timing tolerance.
- Tenant reports and invoice quantities derive from the same finalized ledger.

Run:

- Duplicate, replay, and out-of-order tests.
- Late-arrival and correction-window tests.
- Boundary tests at tier, allowance, period, currency, and rounding transitions.
- Partial-failure and retry tests across every integration boundary.
- High-volume and hot-tenant tests.
- Clock-skew, daylight-saving, leap-day, and month-end tests where relevant.
- Backfill and disaster-recovery replay tests.

### 11. Test Billing Webhook Accuracy

For each provider event:

- Verify signature rejection, timestamp tolerance, and raw-body handling.
- Deliver duplicates and confirm one durable side effect.
- Reorder related events and confirm convergence to provider truth.
- Delay delivery and verify eventual state without accidental service loss.
- Simulate handler failure after receipt and before side effect.
- Verify unknown object and deleted object behavior.
- Confirm invoice, payment, dispute, subscription, and refund transitions as applicable.
- Correlate receipt, processing, side effect, and acknowledgment.

Do not assume webhook delivery is ordered or exactly once.

### 12. Reconcile and Operate

Run reconciliation at event, aggregate, invoice, and cash-collection levels.

- Compare producer counts with ingestion counts.
- Compare raw events with aggregates by partition and period.
- Compare rated totals with exported provider usage.
- Compare provider invoices with internal statements.
- Track unresolved variance by amount, tenant count, age, and root cause.
- Create auditable adjustment workflows with approval thresholds.
- Freeze finalization or collection when variance exceeds policy.
- Notify affected tenants with clear correction evidence when required.

## Checklists

### Metric and Contract Readiness

- [ ] The metric aligns with customer value and viable unit economics.
- [ ] Unit, success state, dimensions, time semantics, and exclusions are defined.
- [ ] Event identity, tenant derivation, schema version, and correction rules are explicit.
- [ ] Privacy, retention, and audit requirements are approved.
- [ ] Representative tenant scenarios produce explainable charges.

### Pipeline Readiness

- [ ] Raw accepted events are durable and immutable.
- [ ] Deduplication, replay, late data, and poison events have tested behavior.
- [ ] Aggregation and rating logic are versioned and traceable.
- [ ] Backfills cannot double charge or pollute current alerts.
- [ ] End-to-end completeness and latency are observable.

### Entitlement and Quota Readiness

- [ ] Plans and overrides are versioned policies.
- [ ] Hard, soft, reservation, rate, and spend limits are intentionally selected.
- [ ] Fail-open or fail-closed behavior is documented per decision point.
- [ ] Cached decisions include version, expiry, and invalidation behavior.
- [ ] Concurrency cannot overspend reservations beyond accepted tolerance.

### Billing Launch Readiness

- [ ] Provider objects map immutably to internal accounts and price versions.
- [ ] Webhook signatures, deduplication, ordering, and retries are tested.
- [ ] Exact arithmetic, currency, tier, discount, and rounding rules are verified.
- [ ] Tenant reports reconcile with finalized invoice quantities.
- [ ] Adjustment, refund, dispute, and support workflows are operational.
- [ ] Reconciliation thresholds and finalization holds are configured.

## Key Patterns

- **Transactional outbox:** business completion and usage emission cannot diverge silently.
- **Immutable raw ledger:** accepted events remain source evidence for replay and dispute resolution.
- **Idempotent consumer:** repeated delivery converges to one logical effect.
- **Versioned rate card:** event-time pricing remains reproducible after commercial changes.
- **Reservation, commit, release:** concurrent expensive work cannot oversubscribe quota unchecked.
- **Provisional then final:** recent totals remain responsive while late data is still admitted.
- **Control plane and data plane split:** plan management is isolated from high-volume usage processing.
- **Provider as integration, not domain model:** internal billing concepts remain stable across vendors.

## Anti-Patterns

- Pricing a metric because it is easy to count rather than valuable to customers.
- Using floating-point arithmetic for charge calculation.
- Trusting a request-supplied tenant identifier without authorization binding.
- Counting attempts and retries as distinct billable successes unintentionally.
- Updating totals in place without raw event evidence.
- Assuming queues or webhooks provide exactly-once, ordered delivery.
- Enforcing real-time quota from a delayed invoice provider.
- Embedding plan logic across application conditionals.
- Applying the current price to historical late events.
- Hiding provisional data or unexplained adjustments in tenant reports.
- Finalizing invoices while reconciliation variance is unresolved.
- Disabling access immediately after a single ambiguous payment event.

## Output Format Expectations

When applying this skill, produce a metering and billing packet with:

1. **Commercial model:** personas, value metric, plans, allowances, overages, commitments, and viability analysis.
2. **Meter catalog:** names, units, success states, sources, dimensions, exclusions, and owners.
3. **Event contract:** schema, identity, tenancy, timestamps, idempotency, privacy, and evolution policy.
4. **Pipeline design:** capture, persistence, deduplication, enrichment, aggregation, rating, export, and recovery.
5. **Entitlement model:** features, limits, overrides, policy versions, and decision behavior.
6. **Quota API or webhook:** authentication, request, response, timeout, cache, reservation, and failure policy.
7. **Billing integration:** object mappings, price versions, webhook handling, invoice lifecycle, and exact arithmetic.
8. **Reporting design:** freshness, provisional state, forecast, export, authorization, and invoice linkage.
9. **Verification plan:** invariants, fixtures, boundary cases, performance, replay, and provider tests.
10. **Reconciliation runbook:** comparisons, tolerances, holds, adjustments, escalation, and evidence retention.
11. **Launch decision:** passed checks, open variances, risks, owners, and go/no-go status.

Include worked examples for tier boundaries, late events, retries, credits, and period close. Clearly distinguish measured quantity, entitled quantity, rated amount, invoiced amount, and collected amount.
