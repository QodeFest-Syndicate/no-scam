---
name: applied-ai-rag-feature-store-integration
description: Integrate RAG pipelines, vector indices, feature stores, and model-serving endpoints into data-scoped cloud products with latency and hallucination guardrails. Use when implementing semantic search, embedding pipelines, inference endpoints, vector retrieval, evaluation harnesses, or diagnosing accuracy degradation and embedding drift.
---

# Applied AI, RAG, and Feature Store Integration

## Purpose

Use this skill to design, ship, and operate grounded AI capabilities as measurable product systems. It joins retrieval, embeddings, feature management, prompt/model versions, inference serving, evaluation, safety controls, latency budgets, and production diagnosis.

## Relevant Stages

- **S1 — Domain & Data Scoping:** Define user jobs, corpus boundaries, permissions, freshness, quality targets, and AI suitability.
- **S2 — Architecture & TDD Planning:** Design ingestion, retrieval, serving, evaluation, and guardrail architecture.
- **S5 — Core Build:** Implement pipelines, indices, feature access, inference, citations, and tests.
- **S6 — Integration & CI/CD:** Deploy models and indices, automate promotion, and configure autoscaling.
- **S7 — Validation & Observability:** Diagnose latency, hallucination, retrieval failure, accuracy loss, and drift.

## When to Apply

Apply this skill when:

- Building semantic search, question answering, recommendations, or agentic retrieval.
- Creating chunking, embedding, indexing, reranking, or feature pipelines.
- Deploying CPU/GPU inference endpoints.
- Defining offline and online AI evaluation.
- Investigating poor answers, stale context, embedding drift, or latency regressions.
- Connecting model inputs to an online/offline feature store.

## Workflow

### 1. Scope the AI Capability

1. Define the user decision or action the feature supports.
2. Establish allowed sources, tenant boundaries, freshness requirements, and citation obligations.
3. Identify failure cost and specify abstention or human-review behavior.
4. Define baseline quality, latency, availability, throughput, and cost targets.
5. Confirm a deterministic or lexical baseline; AI should outperform a simpler approach on the target workload.
6. Classify prompt, corpus, features, outputs, and feedback for privacy and retention.

### 2. Design the RAG Pipeline

Use an explicit pipeline:

`source → parse → normalize → authorize → chunk → embed → index → retrieve → filter → rerank → assemble context → generate → verify → cite`

For every stage, record inputs, outputs, owner, version, failure policy, and telemetry.

- Preserve source IDs, revisions, access-control metadata, timestamps, and content hashes.
- Make ingestion idempotent and support deletion propagation.
- Separate retrieval from generation so each can be evaluated independently.
- Apply authorization before context reaches the model, not after generation.
- Return citations linked to exact source spans when grounded claims are required.

### 3. Select and Configure the Vector Index

Choose with measured data rather than popularity:

- **HNSW:** Strong low-latency recall and online updates; memory intensive. Tune graph degree, construction effort, and search effort.
- **IVF:** Efficient at larger scale; requires representative training and tuning of clusters/probes. Consider product quantization for memory reduction.
- **Flat/exact:** Best recall and simplest behavior for small corpora or evaluation ground truth.
- **Hybrid retrieval:** Combine dense vectors with BM25 or structured filters when exact terms, identifiers, or rare entities matter.

Benchmark candidates using production-like corpus size, dimensionality, filter selectivity, update rate, concurrency, and hardware. Measure recall@k, MRR/nDCG, p50/p95/p99 latency, memory, ingestion rate, and cost.

### 4. Build the Embedding Pipeline

1. Normalize supported formats without erasing meaningful structure.
2. Chunk by semantic boundaries; tune size and overlap by evaluation, not fixed folklore.
3. Attach metadata for authorization, filtering, freshness, lineage, and reconstruction.
4. Batch embedding requests within provider limits and retry with bounded backoff.
5. Cache by content hash plus embedding model/version and preprocessing version.
6. Validate dimension, finite values, normalization policy, and language coverage.
7. Version model, tokenizer, chunker, preprocessing, and index configuration together.
8. Reindex through a shadow index before cutover; retain rollback capability.

### 5. Integrate a Feature Store

- Define each feature's entity key, event timestamp, source, owner, transformation, freshness, and default behavior.
- Reuse equivalent transformations for offline training and online inference to prevent training-serving skew.
- Use point-in-time-correct joins for training datasets.
- Validate online/offline parity with sampled comparisons.
- Set freshness SLOs and distinguish missing, late, stale, and invalid features.
- Keep retrieval metadata and predictive features separate unless their lifecycle and access controls truly match.
- Log feature versions used for inference without exposing sensitive values.

### 6. Deploy Model-Serving Endpoints

- Package model, runtime, tokenizer, adapters, and configuration as one immutable release.
- Benchmark precision, quantization, batching, sequence lengths, and concurrency on target hardware.
- Configure GPU autoscaling using queue depth, concurrency, and token throughput—not CPU alone.
- Set bounded queues, admission control, request deadlines, cancellation, and load shedding.
- Warm replicas and model weights before receiving traffic.
- Use canary or shadow traffic with automatic rollback on quality, safety, latency, or error regression.
- Provide a degraded path: smaller model, retrieval-only response, cached answer, asynchronous completion, or explicit unavailability.

### 7. Enforce Latency and Reliability Guardrails

Allocate an end-to-end budget across query processing, embedding, retrieval, reranking, context assembly, generation, and verification.

- Track p50, p95, and p99 by tenant, model, prompt, index, and route.
- Limit retrieved candidates, rerank depth, context tokens, output tokens, and tool iterations.
- Propagate deadlines across every downstream call.
- Cache only where authorization, freshness, and version keys are correct.
- Alert on SLO burn rate rather than isolated spikes.
- Include quality and cost in release gates; a fast but ungrounded response does not pass.

### 8. Mitigate Hallucination

Layer controls:

1. Retrieve only authorized, high-quality, sufficiently fresh evidence.
2. Require the model to distinguish evidence from instructions embedded in documents.
3. Constrain responses to supplied evidence for grounded tasks.
4. Require citations for verifiable claims and validate citation support.
5. Detect low retrieval confidence, conflicting evidence, unsupported claims, and missing coverage.
6. Abstain, ask a clarifying question, or escalate when evidence is insufficient.
7. Red-team prompt injection, data exfiltration, cross-tenant leakage, and persuasive unsupported answers.

Do not rely on a system prompt as the only hallucination or security control.

### 9. Build the Evaluation Harness

Maintain versioned datasets containing representative, difficult, multilingual, stale, adversarial, and no-answer cases.

Evaluate separately:

- **Retrieval:** recall@k, precision@k, MRR, nDCG, filter correctness, and source freshness.
- **Generation:** groundedness, answer correctness, completeness, citation precision/recall, refusal quality, and safety.
- **Serving:** latency percentiles, availability, throughput, token use, GPU utilization, and cost per successful outcome.
- **Product:** task completion, escalation, correction, and user-rated usefulness.

Use deterministic checks where possible, expert labels for ambiguous cases, and model judges only after calibrating them against human judgments. Gate promotion on non-regression thresholds and confidence intervals.

### 10. Manage Prompt and Model Versions

- Store prompt templates, tool schemas, model settings, safety policies, and expected outputs in a registry.
- Assign immutable versions and link each release to evaluation evidence.
- Record model/provider revision, embedding version, index snapshot, feature view, and corpus watermark.
- Promote through development, staging, canary, and production with approval rules proportional to risk.
- Support immediate rollback of prompts, models, adapters, and index aliases.

### 11. Diagnose Accuracy Loss and Drift

1. Segment the regression by query class, tenant, language, source, time, model, prompt, and index version.
2. Re-run the same evaluation set against old and new pipeline components.
3. Inspect retrieval misses before modifying prompts or generators.
4. Compare corpus freshness, chunk distributions, vector norms, nearest-neighbor similarity, and metadata filters.
5. Check embedding model changes, preprocessing differences, dimensionality, truncation, and mixed-version indices.
6. Verify feature freshness and online/offline parity.
7. Use shadow re-embedding or a sampled dual-index comparison to quantify drift.
8. Roll back the failing component, repair data, then add regression cases.

## Checklists

### Architecture and Build

- [ ] Use case, baseline, failure cost, and abstention path are defined.
- [ ] Corpus lineage, access controls, deletion, and freshness are enforceable.
- [ ] Index choice is supported by representative benchmarks.
- [ ] Embedding and chunking configurations are versioned.
- [ ] Feature joins are point-in-time correct and parity-tested.
- [ ] Retrieval and generation have independent tests.
- [ ] Prompt injection and tenant-isolation controls are tested.

### Deployment and Operations

- [ ] Quality, latency, availability, and cost SLOs have release gates.
- [ ] GPU scaling, warm-up, queues, deadlines, and load shedding are configured.
- [ ] Canary and rollback cover model, prompt, features, and index aliases.
- [ ] Evaluation datasets include adversarial and no-answer cases.
- [ ] Traces link each response to component versions and source citations.
- [ ] Drift and freshness alerts have owners and runbooks.

## Key Patterns

- **Two-stage retrieval:** Broad candidate retrieval followed by a precise reranker.
- **Hybrid search:** Dense semantic retrieval plus lexical matching and structured filters.
- **Shadow index:** Build and evaluate a new embedding/index version without serving it.
- **Version tuple:** Trace each answer to prompt, model, embedding, index, corpus, and feature versions.
- **Abstention-first:** Prefer a transparent no-answer outcome over unsupported confidence.
- **Golden query suite:** Replay stable benchmark queries on every pipeline change.

## Anti-Patterns

- Choosing chunk size, index type, or top-k without measurement.
- Mixing embeddings from incompatible models in one index.
- Filtering tenant access after retrieval or generation.
- Evaluating only fluent answer quality while ignoring retrieval and citations.
- Autoscaling GPU inference from CPU utilization alone.
- Re-embedding production data in place without a shadow index and rollback.
- Using model judges as the sole source of truth.
- Masking accuracy regressions with prompt changes before identifying retrieval or data faults.
- Logging prompts, context, or features without privacy controls.

## Output Format Expectations

Produce an **Applied AI Integration Report** containing:

1. **Use Case and SLOs:** User outcome, baseline, quality, latency, availability, and cost targets.
2. **Architecture:** Pipeline stages, stores, endpoints, authorization, and failure paths.
3. **Version Manifest:** Model, prompt, embedding, chunker, index, corpus, and feature versions.
4. **Evaluation Evidence:** Dataset composition, metrics, thresholds, and comparison to baseline.
5. **Deployment Plan:** Capacity, autoscaling, canary, rollback, and degraded mode.
6. **Guardrails:** Hallucination, injection, privacy, citations, abstention, and monitoring.
7. **Diagnosis or Decision:** Findings, selected configuration, risks, owners, and next action.
