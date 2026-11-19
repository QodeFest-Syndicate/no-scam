# Pricing Model Reference

## Selection criteria

A pricing metric should correlate with customer value, be forecastable and controllable by the customer, be measured accurately, support healthy unit economics, and remain explainable on an invoice. Simulate low, median, high, bursty, and seasonal tenants before launch.

| Model | Implementation | Customer perception | Revenue predictability | Metering need |
|---|---|---|---|---|
| Flat rate | Low | Simple, may feel unfair across usage | High | Subscription state only |
| Per unit | Medium | Transparent but variable | Medium | Exact billable units |
| Graduated tiers | High | Rewards scale gradually | Medium | Exact period aggregate |
| Volume tiers | Medium-high | Cliff effects near thresholds | Medium | Exact period aggregate |
| Freemium | Medium | Easy evaluation | Low until conversion | Allowance and feature use |
| Credits | High | Flexible but abstract | Medium | Credit ledger and expiry |
| Hybrid | Highest | Can align value and predictability | High if well designed | Multiple meters and order of operations |

## Flat-rate pricing

Charge one recurring amount for a defined package. This works when marginal cost and usage variance are modest or when simplicity is the product advantage. Define included features, fair-use boundaries, seats, environments, support, and upgrade triggers.

**Strengths:** predictable invoices and simple sales. **Risks:** heavy users destroy margin; light users feel overcharged; hidden limits create distrust. Meter enough usage to observe economics even if it is not invoiced.

## Per-unit pricing

Charge `quantity × unit price`, optionally after an allowance or minimum. Good units are stable, customer-understandable outcomes such as processed documents or successful transactions—not internal retries.

Define success state, unit conversion, rounding, minimum charge, late events, retries, refunds, and period timezone. Use decimal or integer minor-unit arithmetic. Expose near-real-time usage and forecast.

## Graduated tiering

Each band has its own price. For 25,000 units with first 10,000 at $0.10 and the remainder at $0.07, charge $1,000 + $1,050 = $2,050. The marginal unit gets cheaper while prior units retain their price.

Implementation must split quantity deterministically across bands and test exact boundaries. Customers often need a calculator because invoice lines are less intuitive.

## Volume tiering

One price applies to all units based on total volume. At 9,999 units the price may be $0.10 each; at 10,000, $0.07 each. This can make a larger quantity cost less in total, creating a cliff. Use only if the commercial intent accepts that behavior, or add minimum charges to preserve monotonic totals.

## Freemium

Combine zero price with constrained features, usage, retention, collaboration, or support. Design the free boundary around genuine evaluation and a natural expansion trigger. Track activation, recurring value, limit encounters, upgrade conversion, support cost, abuse, and infrastructure cost.

Do not surprise users with data loss at upgrade boundaries. State what happens at limit: deny, queue, throttle, preserve read access, or start paid overage.

## Credit-based pricing

Customers buy or receive credits consumed by heterogeneous actions. A credit ledger must record grant, purchase, reservation, commit, release, refund, expiry, and adjustment. Publish conversion rates and protect customers from silent rate changes. Define grant-consumption ordering and whether purchased credits expire.

Credits simplify packaging across metrics but can obscure value and complicate revenue recognition, taxation, and disputes.

## Hybrid models

Common combinations:

- Subscription fee plus included allowance plus overage.
- Seats plus usage.
- Minimum annual commitment drawn down by consumption.
- Platform fee plus graduated usage and premium features.
- Prepaid credits with on-demand overage.

Specify order of operations: raw quantity, exclusions, allowance, tier rating, contractual discount, credits, minimum, cap, tax, and rounding. Version every rate card with effective intervals.

## Model evaluation scorecard

Score each 1–5:

1. Alignment to measurable customer value.
2. Customer ability to predict and control spend.
3. Measurement completeness and dispute defensibility.
4. Gross margin across usage percentiles.
5. Sales and procurement simplicity.
6. Product incentive quality.
7. International tax and currency feasibility.
8. Operational complexity and provider compatibility.

Reject a model with a critical weakness even if the total score is high.

## Metering requirements

Every billable metric needs name, unit, authoritative source, success state, dimensions, exclusions, tenant derivation, event-time policy, idempotency scope, lateness window, correction procedure, retention, and owner. Keep quantity, rated charge, invoice amount, credit, tax, and collected cash as separate fields and states.

## Revenue and margin simulation

For each representative tenant calculate recurring fees, billable quantity after allowance, tier charge, discounts, credits, direct infrastructure cost, support cost, provider fee, gross profit, and invoice volatility. Stress:

- 2× and 10× bursts.
- Seasonal peaks and quiet months.
- Discount and commitment scenarios.
- Retry or duplicate defects.
- Late data after invoice finalization.
- Currency and rounding boundaries.
- Tenants clustered just below or above a tier.

Breakeven analysis should use contribution margin, not gross revenue. Separate shared fixed cost from metric-specific variable cost.

## Customer communication

A pricing page and invoice should use identical units and tier terminology. Provide worked examples, calculator assumptions, freshness, timezone, provisional/final status, overage behavior, and spend controls. Enterprise exceptions require explicit contract/version identifiers, not salesperson notes.

## Change management

Grandfather or migrate plans explicitly. Store effective start/end, customer contract, currency, tax behavior, and rounding with the rate version. Preview new pricing against historical sanitized usage before activation. Notify customers and obtain consent where required. Never apply today’s rate to historical late events unless the contract says so.

A good pricing model is commercially viable only when engineering can reproduce every charge and customers can connect it to received value.