# RBAC Dashboard Reference

## Permission Model

Represent authorization as role/permission/scope triples rather than hard-coded role names.

```text
Role: tenant-billing-admin
Permission: invoices.refund
Scope: tenant:acme
Conditions: amount <= approval_limit, mfa = true
```

A permission should identify resource, action, scope, and optional conditions. Derive tenant scope from trusted identity. Resolve effective capabilities server-side and enforce them again at the resource API.

### Scope Hierarchy

`global > tenant > workspace/environment > own resource` is not automatically inherited. Define inheritance explicitly and prevent a broad role from being assignable by a narrow administrator. Separate provider super-admin policy from tenant policy stores and interfaces.

## Role Management UI

- Show role purpose before raw permission count.
- Group permissions by resource and workflow, with search and “selected only” views.
- Explain sensitive permissions and dependent capabilities.
- Preview effective access, including inherited roles and conditions.
- Show member count and affected resources before changes.
- Require explicit confirmation for privilege elevation or last-admin removal.
- Preserve keyboard navigation, focus, and non-color status cues.
- Avoid giant checkbox grids without hierarchy or descriptions.

For custom roles, validate prohibited combinations and reserved provider permissions server-side. Version role definitions and show whether a role is built-in, custom, deprecated, or externally managed.

## Invitation Flow

1. Tenant admin enters identity and intended role/scope.
2. Backend verifies inviter capability and assignable-role boundary.
3. Create a single-use, expiring invitation tied to tenant and normalized identity.
4. Notify without exposing sensitive tenant details before authentication.
5. Invitee authenticates and proves identity binding.
6. Re-evaluate role validity and inviter authority at acceptance time.
7. Create membership atomically and invalidate invitation.
8. Emit audit events for create, resend, revoke, expire, and accept.

Handle existing members, users in another tenant, domain restrictions, SCIM-managed tenants, expired links, and invitation races. Never use possession of the link as the only identity proof for sensitive roles.

## Tenant Admin vs Super-Admin

| Capability | Tenant admin | Provider super-admin |
|---|---|---|
| Manage tenant members | Within assignable roles | Emergency/support only |
| Change tenant roles | Tenant policy boundary | Policy-governed override |
| View tenant business data | According to tenant role | Denied by default; approved access |
| Configure provider platform | No | Scoped provider role |
| Switch tenant context | Membership-based | Break-glass impersonation workflow |
| Export audit trail | Tenant events | Provider events; tenant access governed |

Provider operators should use separate identities, interfaces, and audit streams. Impersonation requires reason, approval where applicable, short expiry, visible banner, tenant notification policy, and complete action attribution. Never make super-admin a hidden extension of tenant-admin UI.

## UI Authorization States

- **Hidden:** revealing capability existence is sensitive.
- **Disabled with reason:** user can understand prerequisites or request access.
- **Read-only:** partial capability allows viewing but not mutation.
- **Approval required:** user may initiate but another principal approves.
- **Denied:** backend refusal is shown clearly without leaking protected data.

Hidden controls are not security. The backend remains authoritative.

## Audit Trail Requirements

Record immutable events for:

- Role create, update, deprecate, and delete.
- Permission and inheritance changes.
- Membership role/scope assignment and removal.
- Invitation lifecycle.
- Tenant switch and provider impersonation.
- Denied sensitive actions and policy evaluation version.
- Bulk operations, imports, SCIM synchronization, and emergency override.

Each event includes event ID, timestamp, actor identity/type, effective tenant, target, action, before/after diff or safe summary, source IP/device context where allowed, correlation ID, policy version, reason, approval, and outcome. Protect sensitive fields and define retention/export policy.

## Dangerous Change Controls

Require step-up authentication and confirmation for super-admin grants, billing ownership, identity-provider changes, audit deletion settings, API credential administration, and last-admin removal. Use two-person approval where risk requires it. Make emergency access time-bound.

## Testing Matrix

- Allowed, denied, expired, and condition-failed permissions.
- Cross-tenant role and membership identifiers.
- Stale session after role removal.
- Concurrent last-admin changes.
- Invitation replay, identity mismatch, and expiry.
- Role inheritance cycle and privilege escalation.
- Tenant admin attempting provider permission assignment.
- Impersonation attribution and expiry.
- Keyboard-only role editing and accessible permission descriptions.
- Audit event completeness, ordering expectations, and export authorization.