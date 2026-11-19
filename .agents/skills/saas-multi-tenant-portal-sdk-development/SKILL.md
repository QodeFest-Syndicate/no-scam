---
name: saas-multi-tenant-portal-sdk-development
description: Develop multi-tenant SaaS portals, RBAC dashboards, interactive data visualizations, BFF APIs, and client SDKs. Use when building SaaS web applications, tenant admin consoles, onboarding flows, billing portals, or client-facing SDKs.
---

# SaaS Multi-Tenant Portal and SDK Development

## Purpose

This skill guides the delivery of secure, accessible, and operable SaaS portals plus the BFF APIs and client SDKs that support them. It makes tenant identity, authorization, state, visualization, onboarding, billing, and edge delivery explicit architectural concerns.

It supports S1 Domain & Data Scoping for wireframes, S2 Architecture & TDD Planning, S5 Core Build, S6 Integration & CI/CD, S7 Validation & Observability, and S8 Delivery & GTM.

## When to Apply

Apply this skill when:

- Building a tenant-facing web application or administrator console.
- Implementing RBAC-aware navigation, dashboards, or workflows.
- Designing a Backend-for-Frontend API.
- Adding interactive charts, tables, maps, or operational analytics.
- Publishing a client SDK for customer or partner integrations.
- Creating tenant onboarding, subscription, invoice, or billing experiences.
- Resolving UI defects, cross-tenant state leaks, accessibility issues, or edge-routing failures.

## Inputs

Collect:

- Personas, jobs, tenant roles, permissions, and critical workflows.
- Wireframes, content, design-system constraints, and supported devices.
- Tenant model, identity provider, session model, and authorization source.
- Backend APIs, events, data freshness, and consistency behavior.
- Visualization datasets, units, time zones, and aggregation rules.
- SDK target languages, compatibility policy, and distribution channels.
- CDN, domains, regions, asset budgets, and deployment environments.
- Onboarding, plan, entitlement, payment, tax, and invoice requirements.

## Step-by-Step Instructions

### 1. Define the Portal Architecture

Choose a rendering and deployment model according to content, security, latency, and personalization:

- Server rendering for fast personalized first views and controlled data access.
- Static generation for public or slowly changing content.
- Client rendering for highly interactive authenticated workspaces.
- Hybrid routing where public, authenticated, and data-heavy routes differ.

Separate:

- Presentation components and design tokens.
- Route-level features and workflow orchestration.
- Server-derived identity, tenant, and entitlement context.
- BFF calls and normalized client data access.
- Local interaction state from server and URL state.
- Telemetry, feature flags, and release configuration.

Do not make tenant selection a visual-only filter. Every request must be authorized for the effective tenant.

### 2. Model Tenant Context

Define a canonical tenant context containing:

- Tenant ID from verified identity or an authorized tenant switch.
- User ID, role bindings, entitlements, locale, and time zone.
- Environment or workspace where the product supports subscopes.
- Correlation and session identifiers.
- Data residency or regional routing hints when required.

On tenant switch:

1. Verify membership and requested scope server-side.
2. Issue or derive a newly scoped context.
3. Cancel in-flight requests from the old tenant.
4. Clear or re-key caches, state stores, subscriptions, and persisted data.
5. Replace tenant-bound route state.
6. Reload permissions, entitlements, and tenant branding.
7. Record an audit event when policy requires it.

### 3. Design and Implement RBAC Dashboards

Build authorization from capabilities rather than role-name checks scattered through components.

1. Define resources, actions, scopes, and conditions.
2. Map roles to capabilities in an authoritative policy source.
3. Resolve effective permissions through the BFF or policy service.
4. Use permissions to shape navigation and explain unavailable actions.
5. Enforce authorization again at every backend operation.
6. Handle permission changes during active sessions.
7. Test allowed, denied, expired, and cross-tenant cases.

UI behavior should distinguish:

- Hidden capabilities that disclose sensitive existence.
- Disabled controls that help users understand prerequisites.
- Read-only states for partial privileges.
- Approval-required actions with visible workflow status.

Never rely on hidden buttons as an access-control mechanism.

### 4. Define BFF API Contracts

Use a BFF to adapt backend capabilities to portal workflows, not to duplicate the entire domain.

For each endpoint specify:

- Method, route, purpose, tenant scope, and required capability.
- Request and response schema with versioning behavior.
- Aggregated upstream calls and timeout budget.
- Validation, pagination, filtering, sorting, and field selection.
- Error code, user-safe message, retryability, and correlation ID.
- Caching, revalidation, consistency, and stale-data behavior.
- Idempotency requirements for mutations.

BFF responsibilities may include:

- Session and tenant-context enforcement.
- Response shaping and aggregation for a specific experience.
- Server-side secret use and token exchange.
- Anti-forgery protection, request limits, and audit emission.
- Incremental delivery or streaming where it improves the workflow.

Avoid embedding durable business rules that belong to domain services.

### 5. Design Frontend State

Classify state before choosing a library:

- URL state: filters, pagination, selected resource, and shareable view.
- Server state: remote records, freshness, errors, and mutations.
- Session state: verified user, effective tenant, capabilities, and entitlements.
- Form state: draft input, validation, dirty state, and submission result.
- Local UI state: expansion, focus, temporary selection, and disclosure.
- Persisted preference state: density, saved view, or dismissed guidance.

Rules:

- Key all server caches by tenant and relevant authorization scope.
- Prefer URL state for reproducible navigation.
- Avoid duplicating server records into multiple mutable stores.
- Use optimistic updates only with a rollback and conflict strategy.
- Cancel stale requests and guard out-of-order responses.
- Version persisted state and exclude secrets or sensitive records.
- Reset tenant-scoped state on logout and tenant switch.

### 6. Integrate Interactive Data Visualizations

Start with the question the visualization must answer.

1. Define metric semantics, units, dimensions, time range, time zone, and freshness.
2. Choose a visual encoding that supports comparison, trend, distribution, composition, or relationship.
3. Aggregate on the server when raw volume or authorization makes client aggregation unsafe.
4. Provide loading, empty, partial, stale, and error states.
5. Add filtering, zooming, brushing, drill-down, or cross-highlighting only when useful.
6. Preserve a tabular or textual equivalent.
7. Use color plus shape, label, or pattern for meaning.
8. Format numbers and dates consistently with locale and business definitions.
9. Virtualize or downsample large datasets while disclosing approximation.
10. Track visualization interactions without collecting sensitive values.

Do not let chart defaults define business metrics. Document every derived value.

### 7. Develop Client SDKs

Design the SDK as a stable product interface.

- Mirror domain concepts, not raw transport details.
- Require explicit configuration for endpoint, credentials, tenant, and timeout.
- Provide safe defaults for retries, pagination, user agent, and telemetry.
- Expose structured errors with status, code, correlation ID, and retryability.
- Support idempotency keys for mutating operations.
- Handle rate-limit headers and exponential backoff with jitter.
- Provide sync or async conventions idiomatic to the target language.
- Make resource cleanup and connection ownership explicit.
- Avoid logging credentials or full sensitive payloads.

For releases:

1. Generate or validate types from the authoritative API contract.
2. Test against supported server versions.
3. Follow semantic versioning and publish a compatibility matrix.
4. Deprecate with warnings and a removal timeline.
5. Sign packages and protect the publishing pipeline.
6. Include executable examples for authentication, pagination, errors, and retries.

### 8. Specify Component Tests

For each component or feature, cover as applicable:

- Expected rendering for common inputs.
- Loading, empty, stale, partial, success, and failure states.
- Keyboard operation, focus order, and focus restoration.
- Accessible name, role, state, validation message, and live announcement.
- Allowed, denied, and read-only permission variants.
- Tenant-context change and cache isolation.
- Responsive layouts and long or localized content.
- User interactions and emitted callbacks.
- Network success, timeout, conflict, validation, and retry behavior.

Favor behavior and accessible queries over implementation details. Use visual regression only for stable, meaningful states.

### 9. Bundle and Deliver Through CDN or Edge

- Set performance budgets for JavaScript, CSS, fonts, images, and route chunks.
- Split by route or feature without creating excessive request waterfalls.
- Remove unused code and keep server-only secrets out of client bundles.
- Fingerprint immutable assets and cache them for a long duration.
- Keep HTML or route manifests short-lived and safely revalidated.
- Configure compression, content types, source-map access, and security headers.
- Route authenticated or residency-bound traffic through approved regions.
- Define SPA fallback narrowly so asset and API errors are not masked as HTML.
- Invalidate only mutable entry points during deployment.
- Use atomic releases and preserve a tested rollback artifact.

Measure real-user performance by route, device, region, and release.

### 10. Resolve UI, UX, and Accessibility Defects

1. Reproduce with route, tenant role, browser, viewport, locale, and feature flags.
2. Determine whether the defect is visual, state-related, contract-related, authorization-related, or accessibility-related.
3. Capture expected behavior from requirements or design-system rules.
4. Patch the smallest correct layer.
5. Add a regression test at the layer that failed.
6. Verify keyboard, screen-reader, zoom, high-contrast, and reduced-motion behavior when relevant.
7. Check nearby states and responsive breakpoints.
8. Confirm analytics and errors contain no sensitive data.

Accessibility baseline:

- Semantic structure and landmarks.
- Keyboard access without traps.
- Visible focus and logical focus order.
- Programmatic labels, descriptions, and error association.
- Sufficient contrast and non-color cues.
- Reduced-motion support.
- Zoom and reflow without loss of function.
- Announced asynchronous status changes.

### 11. Implement Embedded Onboarding

Build onboarding as resumable product state, not a one-time overlay sequence.

- Tailor steps by persona, role, plan, and existing configuration.
- Lead users to a meaningful first outcome.
- Persist progress server-side where users cross devices.
- Allow skip, resume, restart, and dismissal.
- Anchor guidance to stable semantic selectors.
- Avoid blocking critical navigation or assistive technology.
- Instrument completion and drop-off without recording sensitive inputs.
- Keep help content available after the initial tour.

### 12. Integrate Billing Portals

- Obtain customer, subscription, and invoice context from the server.
- Verify tenant billing-admin permission for every action.
- Use provider-hosted payment collection when it reduces compliance scope.
- Never expose payment-provider secrets to the browser.
- Show plan, entitlements, billing period, usage freshness, tax, credits, and invoice status clearly.
- Use idempotency for checkout and subscription mutations.
- Treat billing webhooks as asynchronous, signed, and replayable events.
- Handle payment pending, failed, disputed, canceled, and grace-period states.
- Preserve audit history for plan and billing-account changes.

## Implementation Checklist

### Tenant and Security

- [ ] Tenant context is verified and propagated server-side.
- [ ] All caches and persisted state are tenant-keyed.
- [ ] Backend operations enforce RBAC independently of the UI.
- [ ] Tenant switching clears stale requests and state.
- [ ] Sensitive fields are excluded from bundles, logs, analytics, and errors.

### Experience and Accessibility

- [ ] Critical workflows cover loading, empty, error, and recovery states.
- [ ] Dashboard metrics have documented semantics and freshness.
- [ ] Interactive visualizations have accessible alternatives.
- [ ] Keyboard, focus, contrast, zoom, and announcements are verified.
- [ ] Onboarding is resumable, dismissible, and role-aware.
- [ ] Billing states and required permissions are explicit.

### Contracts and Delivery

- [ ] BFF contracts include errors, timeouts, caching, and version behavior.
- [ ] SDK compatibility, deprecation, retries, and errors are documented.
- [ ] Component tests cover permission and tenant boundaries.
- [ ] Asset budgets and cache policy are enforced in CI/CD.
- [ ] Edge routing respects authentication and residency constraints.
- [ ] Release and rollback artifacts are immutable and tested.

### Stage Readiness

- [ ] S1 wireframes identify personas, states, and core workflows.
- [ ] S2 defines frontend, BFF, state, RBAC, and SDK architecture.
- [ ] S5 implements portal, visualization, contracts, and tests.
- [ ] S6 validates bundles, edge routes, SDK publishing, and rollback.
- [ ] S7 closes UI, UX, accessibility, and performance defects.
- [ ] S8 validates onboarding, billing, support, and adoption telemetry.

## Key Patterns

### Capability-Based UI

Components receive resolved capabilities and render intentional allowed, denied, read-only, or approval states. Backend policy remains authoritative.

### Tenant-Keyed Server State

Every cache key begins with authenticated tenant and environment scope before resource identity and query parameters.

### Strangler BFF

Introduce workflow-focused BFF endpoints while migrating from unsuitable general APIs. Keep ownership and decommission criteria explicit.

### Accessible Visualization Pair

Provide an interactive visual view and a synchronized table or summary that communicates the same facts.

## Anti-Patterns

- Treating tenant selection as a client-side query filter only.
- Scattering hard-coded role-name checks across UI components.
- Putting domain rules in the BFF solely for presentation convenience.
- Using one global client cache across tenant switches.
- Hiding authorization failures behind generic empty states.
- Shipping charts without metric definitions, empty states, or text equivalents.
- Publishing an SDK that exposes raw HTTP details as its primary abstraction.
- Storing tokens, payment details, or sensitive records in browser persistence.
- Caching authenticated HTML publicly at the CDN.
- Building onboarding as a mandatory, non-resumable tooltip chain.
- Fixing accessibility defects only with ARIA when semantic elements exist.

## Output Format Expectations

Produce:

1. Persona, workflow, tenant, and permission matrix.
2. Portal route and rendering architecture.
3. Tenant-context and frontend-state model.
4. Versioned BFF contract with authorization, errors, and caching behavior.
5. Visualization specification with metric semantics and accessibility alternative.
6. SDK surface, compatibility, release, and example plan.
7. Component, integration, accessibility, and performance test matrix.
8. CDN, edge-routing, asset-budget, release, and rollback specification.
9. Onboarding and billing state flows.
10. Defect triage and observability expectations mapped to S1, S2, S5, S6, S7, and S8.

Outputs must distinguish UI affordance from backend authorization, keep tenant scope explicit, and define failure and recovery states for every critical workflow.