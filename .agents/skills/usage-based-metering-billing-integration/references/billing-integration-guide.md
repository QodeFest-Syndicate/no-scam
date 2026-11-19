# Billing Platform Integration Guide

## Integration boundary

Keep internal tenant, entitlement, meter, aggregate, rate-card, and ledger models authoritative. A billing platform is an integration and collection system, not the only copy of commercial truth. Persist immutable mappings between internal billing accounts and provider customers, prices, subscriptions, meters, invoices, and webhook events.

## Common event-delivery contract

Every exported usage record should include stable idempotency key, provider customer/subscription target, meter mapping, exact quantity, event timestamp, internal aggregate version, and correlation ID. Persist request hash, provider response/ID, attempt count, and final disposition. Retry only with the same idempotency identity.

Use a durable outbox for provider calls. Rate-limit per provider/account, apply jittered backoff, and classify retryable versus terminal errors. Reconciliation—not repeated blind retries—resolves ambiguous timeouts.

## Stripe metering pattern

- Map internal meter and rate-card versions to Stripe meter/product/price IDs explicitly.
- Create customers and subscriptions with idempotency keys.
- Send usage using the current Stripe meter-event model supported by the account/API version.
- Preserve Stripe’s identifier and internal aggregate reference.
- Pin and test API versions before upgrade.
- Verify webhook signatures against the untouched raw body.
- Durably record webhook event ID before asynchronous processing.
- Retrieve current object state when event ordering is ambiguous.

Do not infer commercial meaning from Stripe display names. Do not grant/revoke access directly from one invoice webhook; converge subscription/payment state, internal policy, grace period, and contract exceptions.

## AWS Marketplace Metering pattern

Model the customer identifier/product code, dimension, quantity, usage timestamp, and deduplication semantics required by the selected Marketplace API. Register/resolve customers as required by the listing flow. Batch dimensions carefully, retain request/response evidence, and reconcile accepted versus unprocessed records.

Marketplace dimensions and contract terms constrain what may be reported. Define treatment for late usage, account closure, refunds, entitlement changes, and regional endpoint failure. Test with the provider’s sandbox/test facilities and current documentation because API requirements vary by product type.

## Custom billing engine

A custom engine needs versioned rate cards, effective intervals, exact arithmetic, allowance/tier/discount ordering, immutable invoice lines, tax integration boundary, credit ledger, finalization state machine, and approval-controlled adjustments. Generate invoices from finalized aggregates, never ad hoc mutable totals.

Invoice states typically include draft, pending reconciliation, finalized, issued, paid, past due, void, and credited. State transitions should be auditable and idempotent.

## Invoice generation flow

1. Close event-time admission according to lateness policy.
2. Reconcile raw events and period aggregates.
3. Resolve contract and price version effective at event time.
4. Rate quantities with exact decimal/minor-unit arithmetic.
5. Apply allowances, discounts, credits, minimums, caps, and tax in the documented order.
6. Generate immutable line items with source references.
7. Compare internal totals with provider draft.
8. Hold material variance; otherwise finalize and issue.
9. Publish a tenant statement from the same ledger.

## Idempotency and ordering

Scope keys to logical effects, not individual attempts. Store key, request fingerprint, result, and retention. Reusing a key with a different payload must fail. Webhooks and queues are at-least-once and unordered; handlers must deduplicate and converge by fetching provider state or applying monotonic version rules.

Test failure after durable receipt but before side effect, after side effect but before acknowledgment, duplicate delivery, reordering, delayed delivery, unknown object, and replay after retention boundaries.

## Dunning workflow

Separate failed payment from immediate entitlement loss. A typical sequence is payment retry, customer notification, administrator visibility, grace period, progressive restriction, human escalation, and eventual suspension. Contract, jurisdiction, and customer criticality may alter this.

Record every attempt, notification, promise-to-pay, override, and access decision. Preserve read/export access where policy requires. Restore service idempotently after recovery.

## Proration

Define whether upgrade/downgrade is immediate or next period, which quantities prorate, timezone, unused credit behavior, taxes, and rounding. Preview the amount before user confirmation. Persist old/new plan, effective instant, provider proration lines, and internal entitlement transition. Test month-end, leap day, daylight-saving, annual/monthly switches, and multiple changes in one period.

## Audit requirements

Retain according to policy:

- Raw accepted usage and adjustment events.
- Deduplication decisions and schema versions.
- Aggregates and source lineage.
- Rate card/contract versions.
- Provider requests, responses, IDs, and errors.
- Webhook raw-body hash, signature result, receipt, and processing state.
- Invoice lines, credits, refunds, disputes, and approvals.
- Tenant-visible statements and access decisions.

Protect financial and personal data with scoped access, encryption, retention, deletion rules, and tamper-evident audit logging.

## Reconciliation layers

| Layer | Compare | Typical variance |
|---|---|---|
| Capture | Business completions vs usage events | Missing outbox/event |
| Ledger | Accepted unique events vs persisted events | Duplicate or loss |
| Aggregate | Event sums vs period totals | Window/late-data defect |
| Export | Rated/exported vs provider accepted | Mapping or API failure |
| Invoice | Internal lines vs provider invoice | Rate, rounding, tax, proration |
| Cash | Invoice balance vs payment/refund | Collection or settlement timing |

Use amount and count thresholds. Assign owner, due date, and finalization hold behavior for every variance class.

## Security controls

Use least-privilege provider keys, secret rotation, environment separation, signature verification, outbound allowlisting where practical, and no secrets in logs. Bind tenant mappings server-side. Administrative adjustments require authentication, authorization, reason, evidence, and approval thresholds.

## Launch checklist

- Provider objects map immutably to internal versions.
- Idempotency, retries, timeout ambiguity, and rate limiting are tested.
- Duplicate/reordered webhooks converge correctly.
- Tier, rounding, currency, tax, proration, credit, and refund fixtures pass.
- Tenant statements reconcile to invoice quantities.
- Dunning and service-restoration paths are tested.
- Period-close reconciliation and hold policies are operational.
- Support can reproduce a charge from evidence without production database improvisation.

Provider documentation and APIs evolve; pin the integration version and revalidate these controls against the current provider contract before each upgrade.