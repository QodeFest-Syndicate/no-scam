# Release Documentation Standards

Release documentation is an operational contract, not a commit dump. Describe user/operator impact, compatibility, migration, rollout, rollback constraints, security relevance, and support ownership.

## CHANGELOG.md — Keep a Changelog

Maintain an `Unreleased` section and dated semantic versions. Use consistent groups:

```markdown
## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [2.4.0] - 2026-11-19
### Added
- Tenant-scoped export with auditable approval.
```

Entries should be concise complete phrases from the consumer perspective. Link versions to repository diffs and issues/decisions where useful. Call out breaking changes, required migrations, data/backfill impact, feature flags, configuration changes, deprecations, and rollback limits. Security entries may delay exploit detail until remediation is broadly available.

Generated drafts from Conventional Commits or labels require editorial review: squash mechanics, refactors, and internal chores rarely belong unless they change operation.

## Semantic Versioning

Given `MAJOR.MINOR.PATCH`:

- **MAJOR:** incompatible public API/contract, configuration, data, operational, or behavior change.
- **MINOR:** backward-compatible capability.
- **PATCH:** backward-compatible correction.

Pre-release identifiers (`2.0.0-rc.1`) do not guarantee production stability. Define the public compatibility surface for libraries, services, CLIs, events, schemas, IaC modules, and operator procedures. A hidden but depended-on behavior may need migration even if not intended as public.

## README.md Structure

### Open-source project

1. Purpose and status/badges with meaningful links.
2. Supported versions/platforms and compatibility policy.
3. Minimal installation and verified quick start.
4. Configuration reference with safe examples; never plaintext secrets.
5. Common use, tests, build, release, and troubleshooting.
6. Architecture/operational links versioned with code.
7. Contribution, security reporting, code of conduct, license, maintainers/support.

### Internal service/project

1. Purpose, users, SLO/tier, owner and on-call path.
2. Architecture, dependencies, data class/tenant/region boundaries.
3. Reproducible local setup and verification.
4. Environments, configuration, deployment, promotion, and rollback.
5. Dashboards, alerts, logs, runbooks, incident/escalation paths.
6. Access request, secrets, backup/restore, compatibility, and decommission policy.

Test commands from a clean environment. Remove stale mutable-version examples and undocumented prerequisites.

## Migration Guide Template

```markdown
# Migration: v1 to v2
## Who must migrate
## Compatibility and deadline
## Prerequisites and backup
## Before-you-start validation
## Step-by-step changes
## Data/schema migration and duration
## Verification with expected results
## Rollback/forward-fix and irreversible points
## Known issues and support
```

State exact source/target versions, estimated duration, downtime, permission needs, retained old behavior, expand-contract phases, observability, and recovery. Never promise rollback for destructive data change without restore proof.

## Deprecation Notices

A notice must name deprecated surface, replacement, reason, first deprecated version/date, support end, removal version/date, migration link, detection method, owner, and exceptions. Emit notices where users act: docs, changelog, compiler/runtime warning, API headers, dashboards, and direct communication for high-impact users. Track remaining use and do not remove until policy and migration gates pass.

## Release Packet Checklist

- Version, date, source commit, immutable artifact digest, SBOM/signature/provenance.
- Scope and user/operator impact.
- Added/changed/deprecated/removed/fixed/security entries.
- Compatibility and migration with tested commands.
- Infrastructure/configuration/schema differences.
- Deployment strategy, health gates, feature flags, and approvals.
- Rollback trigger/steps, data constraints, backup/restore evidence.
- Known issues, residual risks, owner, support, and evidence retention.
- Links checked and instructions verified from a clean environment.
