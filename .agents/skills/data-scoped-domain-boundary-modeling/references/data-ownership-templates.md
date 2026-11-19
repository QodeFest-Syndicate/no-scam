# Data Ownership YAML Templates

Copy the relevant templates into a domain specification and replace every placeholder. Keep identifiers stable so lineage, policy, and audit records can refer to them.

## Domain Entity Inventory

```yaml
schema_version: "1.0"
domain: billing
owner:
  team: revenue-platform
  contact: revenue-platform@example.invalid
entities:
  - id: invoice
    description: Immutable commercial statement for a billing period
    system_of_record: billing-ledger
    legal_owner: tenant
    operational_owner: revenue-platform
    lifecycle: draft-to-issued-to-settled-or-void
    tenant_key: tenant_id
    identifiers:
      primary: invoice_id
      natural: [tenant_id, invoice_number]
    producers: [billing-ledger]
    consumers: [customer-portal, finance-export]
    mutation_authority: [billing-ledger]
    contract: contracts/invoice-v2.json
    volume:
      expected_daily: 100000
      peak_multiplier: 4
    availability_slo: "99.95%"
    consistency: strong-within-ledger
```

Required fields are `id`, `system_of_record`, legal and operational owners, tenant key, producers, consumers, mutation authority, and contract.

## Data Classification Tiers

```yaml
classification_policy:
  version: "2026-01"
  tiers:
    public:
      description: Approved for unrestricted disclosure
      controls: [integrity-monitoring]
      examples: [published-pricing]
    internal:
      description: Non-public operational information
      controls: [workforce-authentication, least-privilege]
      examples: [service-health-detail]
    confidential:
      description: Customer or business data with material disclosure impact
      controls: [encryption-at-rest, encryption-in-transit, audit-access, dlp]
      examples: [tenant-usage, contracts]
    restricted:
      description: Regulated, secret, credential, or high-impact identity data
      controls:
        - field-level-encryption
        - privileged-access-workflow
        - immutable-audit
        - residency-enforcement
        - masked-nonproduction-data
      examples: [authentication-secret, payment-token, government-id]
assets:
  - asset_id: invoice-line-items
    classification: confidential
    rationale: Contains tenant commercial activity
    fields:
      - name: payment_token
        classification: restricted
        storage: token-reference-only
    approved_purposes: [billing, tenant-reporting]
    prohibited_uses: [advertising]
    policy_owner: security-governance
    review_interval_days: 180
```

Classification follows the highest-impact field unless an approved transformation creates a separately governed product.

## Lineage Mapping

```yaml
lineage:
  - lineage_id: usage-to-invoice
    owner: revenue-platform
    source:
      asset: metering.raw_usage
      domain: metering
      contract_version: "3.1"
    transformations:
      - id: validate-and-deduplicate
        code_owner: metering-platform
        input_keys: [tenant_id, event_id]
        output: metering.validated_usage
        quality_rules:
          - event_id_is_unique_per_tenant
          - occurred_at_is_within_open_window
      - id: aggregate-billing-period
        code_owner: revenue-platform
        input: metering.validated_usage
        output: billing.usage_charges
        logic_reference: policy/charge-calculation-v4
    destination:
      asset: billing.invoice
      domain: billing
      system_of_record: billing-ledger
    transfer:
      mode: event
      contract: usage-charge-v3
      freshness_slo: PT15M
      replay_window: P35D
    controls:
      encryption: provider-managed-key
      residency: inherit-tenant-home-region
      reconciliation: daily-source-to-ledger
    contacts:
      producer: metering-oncall
      consumer: revenue-oncall
```

Lineage must describe semantic transformations, not only physical table movement. Record correction, replay, and deletion propagation.

## Retention Policy

```yaml
retention_policies:
  - policy_id: issued-invoice-retention
    asset: billing.invoice
    owner: revenue-platform
    classification: confidential
    legal_basis: commercial-record-obligation
    jurisdiction_rules:
      default:
        retain_for: P7Y
      eu:
        retain_for: P10Y
        storage_regions: [eu-west, eu-central]
    lifecycle:
      active_store: P2Y
      archive_after: P2Y
      delete_after: jurisdiction-rule
    deletion:
      method: cryptographic-erasure-and-object-expiry
      verification: deletion-certificate
      maximum_completion: P30D
      downstream_propagation: [analytics-warehouse, support-search]
    holds:
      supported: true
      authority: legal
      audit_required: true
    backups:
      maximum_age: P35D
      restore_reapplies_deletion_ledger: true
    review_interval_days: 365
```

## Ownership Review Template

```yaml
review:
  reviewed_at: "2026-11-19"
  reviewers:
    product: product-owner
    domain: domain-owner
    security: security-owner
    privacy: privacy-owner
    operations: operations-owner
  assertions:
    one_system_of_record_per_fact: true
    cross_context_mutations_use_contracts: true
    tenant_partitioning_tested: true
    deletion_propagation_tested: true
    residency_enforced: true
  open_risks:
    - id: RISK-001
      description: Replace with a concrete unresolved risk
      owner: accountable-owner
      due_at: "2027-01-15"
```

## Validation Rules

- Do not use “shared” or “platform” as an owner; name an accountable team.
- Distinguish legal ownership, operational ownership, and mutation authority.
- Bind tenant keys to authenticated identity at service boundaries.
- Version contracts and state compatibility and deprecation periods.
- Ensure retention includes backups, derived stores, caches, and exports.
- Treat unknown residency or classification as a release-blocking gap for sensitive assets.