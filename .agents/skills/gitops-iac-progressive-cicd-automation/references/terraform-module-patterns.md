# Terraform Module Patterns

A module should expose one cohesive capability through a small, stable contract. Root modules compose environments; reusable child modules must not embed environment names, backend configuration, or caller-specific provider credentials.

## Recommended Structure

```text
module/
├── main.tf          # cohesive resources and local composition
├── variables.tf     # typed, described, validated inputs
├── outputs.tf       # stable consumer contract
├── versions.tf      # Terraform/provider constraints
├── README.md        # purpose, examples, compatibility, migration
├── examples/basic/  # runnable composition
└── tests/           # terraform test and/or integration fixtures
```

Split files further by capability only when it improves navigation; Terraform merges files in a directory.

## Input Contract

Every variable needs type, description, safe default only when one exists, nullable/sensitive settings, and validation for bounded values. Prefer structured objects with optional attributes to parallel loosely related variables. Avoid “configuration bags” of `map(any)` that bypass validation. Do not pass secrets when workload identity or runtime retrieval can avoid state exposure.

Use `for_each` with stable semantic keys for collections whose order changes. Changing `count` indices can replace unrelated resources.

## Output Contract

Export consumer needs—not entire resource objects. Describe meaning, stability, sensitivity, and when values are unknown until apply. Treat output removal/type change as breaking. Sensitive output suppresses display but does not remove the value from state.

## Provider Configuration

Root modules configure providers, aliases, accounts, and regions, then pass them explicitly. Child modules declare required providers and version compatibility but should not configure credentials. Pin provider and module versions with intentional ranges; commit dependency locks where appropriate to the workflow.

## State Management

Use remote encrypted state, locking, versioning/backups, least-privilege access, and separate blast-radius boundaries. State contains sensitive metadata and sometimes secrets. Never use one enormous state solely for convenience. Cross-stack dependencies should consume stable published outputs or a deliberate contract rather than unrestricted state reads.

Backend configuration belongs to roots/automation and is initialized separately because backend blocks cannot use ordinary variables. Plan before apply; bind reviewed plans to commit, variables, providers, and target workspace.

## Lifecycle and Refactoring

Use `prevent_destroy` selectively for critical persistent resources; it is a guard, not recovery. Explain `ignore_changes` and keep its scope narrow—broad ignores conceal drift. Prefer `moved` blocks for address refactors and `import` blocks/workflows for adoption. Test replacement, upgrade, migration, and rollback implications.

## Testing Layers

- `terraform fmt` and `validate` for syntax/schema;
- lint/security/policy checks for organization rules;
- `terraform test` for native assertions and mocked/real providers as appropriate;
- plan snapshots/assertions for resource intent, reviewed carefully;
- Terratest or equivalent integration for provision/use/destroy behavior;
- upgrade tests from supported prior module versions;
- failure tests for invalid inputs, denied policy, and destructive changes.

Integration tests need isolated accounts/projects, unique names, budgets, timeouts, cleanup evidence, and no production data.

## Anti-Patterns

- **Mega-module:** unrelated network, database, runtime, and observability share one release/state; split by lifecycle/ownership and publish contracts.
- **Version-pinning gap:** floating providers/modules make plans non-reproducible; constrain and automate reviewed updates.
- **Copied environment modules:** fixes diverge; compose the same module with explicit values.
- **Hidden provider:** child module assumes account/region or credentials; pass aliases explicitly.
- **Secret variable defaults:** value enters source/state; use managed secret retrieval.
- **Broad `ignore_changes`:** drift becomes invisible; define ownership instead.
- **Untyped map escape hatch:** interface cannot be validated or evolved safely.
- **Output everything:** internal implementation becomes a permanent consumer dependency.

## Release Checklist

Confirm cohesive scope, typed/validated inputs, stable/sensitive outputs, compatibility constraints, provider ownership, state/migration plan, tags/labels, least privilege, encryption/logging, replacement impact, examples, tests, semantic version, changelog/migration notes, and a deprecation window for breaking contracts.
