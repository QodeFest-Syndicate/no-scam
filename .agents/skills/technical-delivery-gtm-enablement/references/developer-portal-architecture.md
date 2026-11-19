# Developer Portal Architecture

## User journeys

Design for discovery, first success, production readiness, maintenance, and troubleshooting. A portal is a product surface, not a document folder. Primary users include evaluating developers, implementers, tenant administrators, security reviewers, and operators.

## Information architecture

```text
Getting started
  Overview → concepts → quickstart → next steps
Guides
  Core workflows → integrations → webhooks → operations
Reference
  API → SDKs → CLI → events → errors
Operate
  Limits → status → changelog → versions → support
Account
  Applications → credentials → environments → usage
```

Use task language in navigation. Keep one canonical URL per concept and cross-link rather than duplicating. Every page should expose version, lifecycle, last review, owner, and feedback path.

## Search and navigation UX

Index titles, headings, body, operation IDs, error codes, SDK methods, and aliases. Rank current-version task pages above archived references. Provide filters by product, version, language, and content type. Measure zero-result searches, refinements, exits, and searches followed by support tickets.

Navigation should preserve location, expose neighboring tasks, and offer next production steps after quickstart. Generate API navigation from tags but review it for user meaning. Mark preview, deprecated, and archived content unmistakably.

## Interactive API explorer

A “try it” explorer should use the same validated OpenAPI source as reference docs. Default to sandbox, display environment and tenant, redact credentials, constrain request fields, and show generated curl/SDK code. Protect destructive endpoints with explicit confirmation or disable them.

Never proxy arbitrary URLs or expose long-lived secrets to analytics/logs. Apply portal authorization, API authorization, CSRF protections where relevant, rate limits, and audit logging. Explain side effects and cleanup before execution.

## SDK experience

For each SDK show package coordinates, install command, supported runtimes, current version, compatibility policy, release notes, and maintenance status. Map methods to operation IDs. Provide typed quickstarts, pagination, retries, timeouts, error handling, and credential loading.

Offer downloads through trusted registries and verify provenance/signatures where supported. Test snippets against sandbox or deterministic mocks in CI. Archived SDKs must state end-of-support.

## Version selector

The selector should distinguish API, documentation, and SDK versions rather than conflating them. Persist selection in URL and user preference, redirect safely to equivalent pages, and warn when viewing outdated content. Search must label version results. Changelog and migration guides should connect old and new versions.

## Authenticated portal surfaces

Users may manage credentials, applications, webhooks, usage, limits, invoices, members, and environments. Enforce server-side tenant authorization and roles. Reveal a secret only at creation, support rotation/revocation, and audit consequential actions. Separate sandbox and production visually and technically.

## Content platform architecture

A practical pipeline includes source-controlled Markdown/MDX, OpenAPI generation, SDK reference extraction, content linting, schema validation, snippet tests, link checking, accessibility checks, preview deployments, review ownership, and production publishing. Generated reference should be regenerated—not manually edited.

Keep product metadata (versions, lifecycle, owners, package names, status/support links) in one structured source. Fail publishing when required metadata or mandatory tests are absent.

## Feedback mechanisms

Provide page feedback, issue reporting, broken-example reporting, and support escalation with page/version context. Do not collect credentials or sensitive payloads. Route feedback to an owner and close the loop with status. Combine qualitative feedback with search and activation analytics.

## Analytics and success measures

Track with privacy controls:

- Time to first successful API call.
- Quickstart completion and drop-off step.
- Search success and zero-result rate.
- Copy/run success for examples.
- Authentication and validation error patterns.
- Documentation-linked support deflection.
- Feedback resolution time.
- Version adoption and deprecated traffic.

Avoid using raw tenant IDs, tokens, request bodies, or high-cardinality resource identifiers.

## Reliability and security

The public content portal can fail independently from authenticated account tools. Cache static documentation and provide status/support links outside the main dependency path. Protect publishing credentials, dependencies, custom MDX components, redirects, and search ingestion. Sanitize rendered content and apply CSP.

Portal status should not claim API health unless backed by the service status system. Ensure accessibility: keyboard navigation, focus states, semantic headings, contrast, descriptive links, responsive code blocks, and screen-reader labels.

## Ownership model

- Product: concepts, lifecycle, packaging.
- Engineering: contract and technical correctness.
- Developer experience: information architecture, examples, portal behavior.
- Security/legal: auth, security, privacy, compliance claims.
- Support: troubleshooting and escalation.
- Release management: versions and changelog.

Each page needs one accountable owner and review trigger. Contract changes, SDK releases, incidents, and product launches should automatically open documentation work.

## Release checklist

- Clean-room developer reaches first value using only the portal.
- OpenAPI/reference matches deployed sandbox.
- Authentication, errors, pagination, limits, and webhooks are covered.
- Examples execute and contain no secrets.
- Search finds primary tasks, operation IDs, and error codes.
- Version/lifecycle labels and migration paths are correct.
- Credential/account actions enforce role and tenant boundaries.
- Links, accessibility, responsive design, analytics, and feedback work.
- Status, support, changelog, and last-reviewed signals are current.

A portal succeeds when it reduces uncertainty from evaluation through operation—not when it merely publishes a large number of pages.