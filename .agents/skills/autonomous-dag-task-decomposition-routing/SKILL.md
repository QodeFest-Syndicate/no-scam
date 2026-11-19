---
name: autonomous-dag-task-decomposition-routing
description: Decompose complex workflows into directed acyclic graph (DAG) execution plans with pre-ops necessity evaluation, stage skipping, and parallel scheduling. Use when constructing execution DAGs, assigning task budgets, evaluating stage necessity, resolving cross-task deadlocks, or optimizing parallel swarm scheduling.
---

# Autonomous DAG Task Decomposition and Routing

## Purpose

Use this skill to transform a complex objective into an executable, observable directed acyclic graph. The graph should expose dependencies, safe parallelism, gates, budgets, ownership, skip decisions, and recovery paths so any capable agent can execute work without role-specific assumptions.

## Relevant Stages

- **S0 — Pre-Ops Evaluation:** Determine which stages are necessary and which may be skipped safely.
- **S3 — Task Decomposition & Routing:** Primary stage for graph construction, budgeting, assignment, and scheduling.
- **S4 — Pre-Impl Gate:** Confirm prerequisites, acceptance criteria, and risk controls before build nodes run.

## When to Apply

Apply this skill when:

- Work spans multiple stages, systems, repositories, or agents.
- Tasks can run in parallel but share dependencies or mutable resources.
- Time, token, compute, cost, or specialist attention is limited.
- A workflow needs autonomous progression against an SLA.
- Work is blocked by circular waits, unclear ownership, or hidden prerequisites.
- New evidence requires replanning an active execution graph.

## DAG Invariants

Every graph must satisfy:

- Each node produces one verifiable outcome.
- Every dependency edge has a reason and a concrete artifact or condition.
- The graph is acyclic; iteration occurs through a controlled replan, not a back edge.
- Gates have explicit pass, conditional-pass, and fail behavior.
- Parallel nodes do not mutate the same resource without serialization or coordination.
- Every terminal path reaches delivery, a documented stop, or an escalation outcome.

## Workflow

### 1. Run Pre-Ops Necessity Evaluation

Evaluate each candidate stage against evidence rather than habit.

For each stage, ask:

1. Does it produce an artifact required by a later node?
2. Does it reduce material correctness, security, compliance, operational, or cost risk?
3. Is equivalent, current, validated evidence already available?
4. Is the change large or uncertain enough to justify the stage?
5. Does policy make the stage mandatory?
6. What is the consequence of skipping it?

Record one decision:

- **Execute:** Required output or risk control is missing.
- **Reuse:** Existing artifact is current, scoped correctly, and validated.
- **Compress:** Stage is needed, but a bounded lightweight version is sufficient.
- **Skip:** No required output or meaningful risk reduction; skip evidence is documented.
- **Escalate:** Necessity cannot be decided within authority or available evidence.

Never skip mandatory security, compliance, data-loss, or production-release gates solely to meet schedule.

### 2. Define the Objective and Exit Conditions

- State the desired outcome and business deadline.
- Define in-scope and out-of-scope work.
- List immutable constraints and acceptable trade-offs.
- Define global acceptance criteria and required evidence.
- Name stop conditions: budget exhaustion, risk threshold, blocked decision, or failed mandatory gate.

### 3. Identify Deliverables and Work Backward

1. Start from final deliverables and gate evidence.
2. Identify direct prerequisites for each deliverable.
3. Repeat until every leaf node can start from available inputs.
4. Separate discovery from implementation when discovery can invalidate design.
5. Separate implementation from verification; the same outcome must not self-certify where independence matters.
6. Add integration, rollback, and delivery nodes explicitly rather than treating them as implicit finish work.

### 4. Define Atomic Task Nodes

Each node should include:

- **ID and title:** Stable and action-oriented.
- **Purpose:** Why the node exists.
- **Inputs:** Artifacts, decisions, credentials, environments, and assumptions.
- **Output:** One primary verifiable artifact or state change.
- **Acceptance:** Objective pass/fail criteria.
- **Owner/capability:** Required expertise or tool access; assignment remains role-agnostic.
- **Estimate and budget:** Duration, compute, token, cost, and retry allowance as applicable.
- **Resources:** Files, services, environments, locks, or quotas touched.
- **Risk:** Failure impact and containment.
- **Retry/escalation:** Maximum attempts and next action.
- **Observability:** Status signal, evidence location, and heartbeat expectation.

Split a node when it has multiple unrelated outputs, different owners, independently testable portions, or partial completion that benefits downstream work. Do not split so finely that coordination exceeds execution cost.

### 5. Add Dependency Edges

Use typed edges:

- **Data:** Downstream node consumes an artifact.
- **Decision:** Downstream node needs an approved choice.
- **Control:** Policy or gate must pass first.
- **Resource:** Shared mutable resource requires ordering.
- **Environment:** Infrastructure or access must exist.

Do not add an edge merely because one task was listed earlier. For each edge, name the exact condition that unlocks the child.

### 6. Validate Acyclicity and Completeness

- Run a topological-sort check.
- Confirm all non-root nodes have satisfied or planned prerequisites.
- Confirm every output has a consumer or is a final deliverable.
- Find orphan, duplicate, unreachable, and permanently blocked nodes.
- Replace circular dependencies by extracting the shared decision, contract, interface stub, or discovery task into an earlier node.
- Model iterative feedback as a new graph revision with bounded retries.

### 7. Allocate Budgets and Assign Work

Allocate more budget to nodes with high uncertainty, critical-path impact, expensive failure, or scarce resources.

For each node:

1. Estimate optimistic, likely, and worst-case effort.
2. Set a hard budget and a warning threshold.
3. Reserve contingency for critical-path nodes, not uniformly across the graph.
4. Match required capabilities, permissions, and availability to an agent.
5. Limit work in progress to preserve review and integration capacity.
6. Avoid assigning one agent to simultaneous nodes that require continuous attention.

Route by capability and current load, not by permanent role labels.

### 8. Identify Safe Parallelism

Nodes may run concurrently when:

- Their prerequisites are satisfied.
- Neither consumes incomplete output from the other.
- They do not write the same files, infrastructure state, schema, or deployment target.
- Combined resource demand stays within quotas.
- Their independent results can be integrated through a defined contract.

Create explicit join nodes for integration and reconciliation. If two nodes share a mutable resource, partition it, introduce a lock/lease, or serialize them.

### 9. Analyze the Critical Path

1. Compute the longest dependency-weighted path to the terminal milestone.
2. Identify zero-slack and low-slack nodes.
3. Prioritize prerequisite resolution, assignment, and monitoring on that path.
4. Shorten it by splitting work, precomputing inputs, reusing validated artifacts, or increasing capacity.
5. Do not accelerate non-critical nodes if doing so creates integration congestion.
6. Recompute after material estimate, dependency, or failure changes.

### 10. Configure SLA-Driven Autopilot

Define progression rules before execution:

- Start a ready node automatically when prerequisites pass, budget is available, and no resource conflict exists.
- Emit heartbeat and evidence at a specified interval.
- Warn at budget or SLA-consumption thresholds.
- Retry only classified transient failures with bounded attempts and backoff.
- Pause on ambiguous output, policy failure, repeated error, unexpected scope expansion, or missing authority.
- Escalate with evidence, impact, options, and decision deadline.
- Cancel obsolete descendants when an upstream decision invalidates them.
- Never infer gate approval from silence.

### 11. Detect and Resolve Deadlocks

Detect:

- Nodes waiting on each other's output.
- Agents holding resources while waiting for another resource.
- Reviews whose approver depends on the reviewed task.
- Hidden environment, credential, or quota dependencies.
- Join nodes waiting for cancelled or superseded branches.
- Repeated reassignment without a capability match.

Resolve in order:

1. Make the hidden dependency explicit.
2. Release unnecessary locks and cancel obsolete work.
3. Extract a shared interface, decision, or minimal stub into a predecessor node.
4. Reassign ownership or add missing capability/access.
5. Serialize conflicting mutations.
6. Replan affected descendants and recalculate the critical path.
7. Escalate only the smallest decision that cannot be resolved autonomously.

### 12. Adjust the DAG Dynamically

Trigger a graph revision when scope, evidence, estimates, failures, risk, or external dependencies change materially.

- Preserve completed evidence; do not redo work without a stated invalidation reason.
- Version the graph and log added, removed, split, merged, or reordered nodes.
- Revalidate acyclicity, budgets, resource conflicts, gates, and terminal coverage.
- Reassess previously skipped stages if assumptions changed.
- Notify owners of invalidated inputs or cancelled descendants.
- Resume only from a consistent graph version.

## Stage Skip Criteria

A stage may be skipped only when all are true:

- Its required artifact is not needed, or an equivalent validated artifact exists.
- No policy, contract, or mandatory gate requires execution.
- Inputs and assumptions have not materially changed since the reusable evidence was produced.
- Skipping does not hide unacceptable risk or transfer it unknowingly downstream.
- The decision, evidence, owner, and expiry condition are recorded.

Examples:

- Reuse S1 domain scope when boundaries and data classifications are unchanged and recently validated.
- Compress S2 for a low-risk internal correction that does not alter architecture or contracts.
- Skip S6 deployment work for a research-only artifact that cannot reach a runtime environment.
- Never skip S4 for a high-risk production, security, compliance, or destructive data change.

## Checklists

### Graph Quality

- [ ] Objective, scope, deadline, constraints, and exit conditions are explicit.
- [ ] Every node has one output and objective acceptance criteria.
- [ ] Every edge names a real dependency and unlock condition.
- [ ] Acyclicity, reachability, and terminal coverage are verified.
- [ ] Integration, validation, rollback, and delivery are explicit nodes.
- [ ] Resource conflicts and environment dependencies are modeled.
- [ ] Critical path, slack, budgets, and contingency are calculated.

### Autonomous Execution

- [ ] Stage execute/reuse/compress/skip decisions include evidence.
- [ ] Ready-node and resource-conflict rules are defined.
- [ ] Retry, timeout, cancellation, and escalation rules are bounded.
- [ ] Mandatory gates require explicit approval.
- [ ] Heartbeats and evidence locations are observable.
- [ ] Deadlock detection covers resource and dependency waits.
- [ ] Replanning preserves completed valid work and versions changes.

## Key Patterns

- **Fan-out/fan-in:** Run independent work in parallel, then reconcile through one integration node.
- **Interface-first split:** Define a stable contract before parallel implementations begin.
- **Risk-first discovery:** Resolve high-impact uncertainty before expensive downstream work.
- **Capability routing:** Assign by required skills, access, and load rather than fixed roles.
- **Evidence-bearing edges:** A child unlocks only when the required artifact passes acceptance.
- **Bounded replan:** Replace loops with versioned graph revisions and retry limits.

## Anti-Patterns

- Treating a checklist as a DAG without dependencies.
- Creating edges from chronology rather than necessity.
- Assigning tasks by role title alone.
- Parallelizing writes to the same mutable resource.
- Hiding integration and validation inside build nodes.
- Skipping stages without evidence or expiry conditions.
- Allowing indefinite retries or waiting for silent approval.
- Keeping cancelled branches as unresolved join dependencies.
- Rebuilding completed valid artifacts after every replan.
- Optimizing utilization while the critical path remains blocked.

## Output Format Expectations

Produce an **Execution DAG Package** containing:

1. **Objective and Exit Conditions:** Scope, deadline, constraints, success, and stop rules.
2. **Pre-Ops Decision Table:** Stage, decision, evidence, risk, owner, and expiry.
3. **Node Table:** ID, output, owner/capability, budget, acceptance, resources, and status.
4. **Edge List:** Parent, child, dependency type, and unlock condition.
5. **Schedule:** Ready sets, parallel waves, join nodes, critical path, and slack.
6. **Autopilot Policy:** Start, retry, timeout, pause, cancel, and escalation rules.
7. **Risk and Deadlock Register:** Signals, impact, mitigation, and owner.
8. **Revision Log:** Graph version, changes, invalidated assumptions, and preserved evidence.
