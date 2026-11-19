# SaaS Portal Accessibility Checklist

Target WCAG 2.1 AA as a baseline. Automated checks find only a subset; combine static analysis, browser automation, keyboard review, screen-reader testing, zoom/reflow checks, and user research.

## Global Requirements

- One descriptive page title and one visible primary heading.
- Semantic landmarks for header, navigation, main, complementary, and footer regions.
- Skip link reaches main content and becomes visible on focus.
- Logical DOM and focus order matches the visual workflow.
- Every interactive element works by keyboard without traps.
- Visible focus meets contrast and is not obscured.
- Text contrast is at least 4.5:1; large text at least 3:1.
- UI components, states, and meaningful graphics meet 3:1 non-text contrast.
- Color is never the only carrier of meaning.
- Content reflows at 320 CSS pixels and works at 200% zoom.
- Motion respects reduced-motion preference and has pause/stop controls where required.
- Language, abbreviations, and unusual terms are identified appropriately.

## Navigation

- Current location is programmatically indicated (`aria-current` where suitable).
- Repeated navigation order remains consistent.
- Menus use buttons for disclosure and links for navigation.
- Mobile drawers trap focus only while modal, close on Escape, and restore focus.
- Tenant switchers announce the effective tenant and reset stale scoped state.
- Permission-hidden routes still return an accessible denied/not-found experience server-side.

## Forms

- Every control has a persistent programmatic label.
- Required state, format, units, and constraints appear before submission.
- Instructions do not depend only on position, shape, or color.
- Errors identify the field, explain correction, and are associated using description/error semantics.
- Submission moves focus to an error summary or announces success/failure.
- Valid input is preserved after recoverable errors.
- Autocomplete tokens are used for recognized personal-data fields.
- Destructive and financial actions have confirmation and reversal where possible.
- Timeouts warn users and allow extension unless security prevents it.

## Data Tables

- Use native table semantics for tabular data.
- Provide a caption or nearby accessible name and summary.
- Associate header cells with rows/columns; identify sortable state.
- Sorting, filtering, selection, expansion, and pagination work by keyboard.
- Virtualized rows preserve meaningful position/count announcements where feasible.
- Responsive alternatives retain headers and relationships.
- Empty, loading, stale, partial, and error states are announced.
- Bulk actions identify selection count and scope.

## Modals and Dialogs

- Use a dialog element or correct dialog role, label, and modal state.
- Move focus to a meaningful initial element after open.
- Keep keyboard focus inside only while modal.
- Escape closes when safe; irreversible progress explains why it cannot.
- Close controls have accessible names.
- Background content is inert, not merely visually covered.
- Restore focus to the triggering element or a logical successor.
- Nested dialogs are avoided or rigorously managed.

## Notifications and Async Status

- Use polite live regions for non-urgent updates and alerts only for urgent interruptions.
- Do not place live regions around large changing containers.
- Toasts remain long enough, can be paused/dismissed, and are available in a notification history for critical outcomes.
- Loading indicators have accessible text and do not repeatedly announce minor progress.
- Background job status exposes state, progress, result, and recovery action.
- Validation messages are not announced twice.

## Charts and Visualizations

- State the question, metric, units, time range, timezone, and freshness.
- Provide synchronized table, list, or textual summary.
- Use labels, patterns, or shapes in addition to color.
- Tooltips are keyboard and pointer accessible, dismissible, hoverable, and persistent enough.
- Canvas/SVG has an accessible name and summary; individual points are focusable only when useful.
- Avoid forcing keyboard users through hundreds of marks; provide grouping and skip mechanisms.
- Disclose downsampling, approximation, missing data, and stale values.

## Authentication and RBAC

- Authentication does not rely on a cognitive-function test without an alternative.
- MFA flows expose labels, countdowns, resend state, and paste support.
- Permission-denied states explain next steps without exposing protected data.
- Disabled actions explain prerequisites and remain discoverable when appropriate.
- Impersonation and effective tenant are persistently and non-visually indicated.
- Session expiry warning is announced and operable.

## Testing Tools

| Layer | Suggested tools | Purpose |
|---|---|---|
| Static | eslint-plugin-jsx-a11y, framework compiler | Catch semantic JSX patterns |
| Component | Testing Library + jest-axe/axe-core | Assert names, roles, and common violations |
| Browser | Playwright/Cypress + axe | Test rendered routes and workflows |
| Manual keyboard | Browser only | Focus order, traps, shortcuts, restoration |
| Screen reader | VoiceOver/Safari, NVDA/Firefox or Chrome, JAWS/Chrome | Real announcements and navigation |
| Contrast/zoom | Browser devtools, contrast analyzer | Visual criteria and reflow |

## CI Integration

1. Lint changed components with accessibility rules.
2. Run axe against stable component states: loading, empty, error, denied, success, modal open.
3. Run critical keyboard workflows in a real browser.
4. Fail on new serious/critical violations; track approved exceptions with owner and expiry.
5. Store route, role, tenant, viewport, locale, and browser with results.
6. Avoid suppressing a rule globally; fix semantics or scope a reviewed exception.
7. Schedule broader scans, but keep manual audits at release gates.

## Manual Release Gate

- Complete core workflow without pointer.
- Verify focus after navigation, dialogs, deletion, validation, and tenant switch.
- Test at 200% and 400% zoom/reflow where applicable.
- Test high contrast/forced colors and reduced motion.
- Listen with at least one screen reader on each supported platform family.
- Confirm long localized text and error states.
- Confirm charts have equivalent information.
- Document blockers, owner, severity, workaround, and remediation date.