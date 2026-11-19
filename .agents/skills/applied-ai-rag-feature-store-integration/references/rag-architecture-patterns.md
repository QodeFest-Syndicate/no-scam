# RAG Architecture Patterns

## Comparison

| Pattern | Typical latency | Accuracy potential | Operational complexity | Best fit |
|---|---|---|---|---|
| Naive RAG | Low | Baseline | Low | Narrow, clean corpora |
| Advanced RAG | Medium | High on ambiguous queries | Medium | Production QA/search |
| Modular RAG | Medium–high | High and tunable | High | Multiple domains/models |
| GraphRAG | High | High for relationship questions | High | Entity-rich connected knowledge |
| Agentic RAG | Variable/high | High on multi-step tasks | Very high | Bounded research/workflows |

Latency ranges must be measured on the target corpus, model, filters, and hardware. Each additional model call increases tail latency, cost, and failure probability.

## Naive RAG

```text
query -> embed -> vector search -> top-k chunks -> prompt -> generator -> answer
                 index/filter metadata                 citations
```

**Profile:** one query embedding, one retrieval call, one generation. Common interactive latency is dominated by generation; retrieval should normally remain a small fraction of the budget.

**Accuracy trade-offs:** simple and inspectable, but literal identifiers, ambiguous queries, poor chunk boundaries, and redundant results reduce recall or context precision.

**Use when:** one domain, consistent terminology, moderate corpus, clean permissions, and a strong baseline is needed quickly.

**Controls:** hybrid dense/lexical retrieval, metadata authorization before retrieval output, deduplication, calibrated top-k, source-span citations, and explicit abstention.

## Advanced RAG

```text
query -> classify -> rewrite/expand -> parallel dense + lexical retrieval
                                     -> fuse -> rerank -> context assemble
query -> HyDE hypothetical document -----^                 |
                                                            v
                                                   generate -> verify
```

### Query Rewriting and Expansion

Normalize acronyms, resolve conversation references, or generate alternate formulations. Preserve the original query and constrain rewrites so they cannot broaden authorization scope.

### HyDE

Generate a hypothetical answer/document and embed it for retrieval. It can bridge vocabulary gaps but may bias retrieval toward an invented premise. Use original-query retrieval in parallel and fuse results.

### Multi-Step Retrieval

Retrieve initial evidence, extract entities/subquestions, then retrieve again. This improves compositional questions but adds model calls and error propagation. Cap steps and expose evidence per step.

**Profile:** typically adds one or more inference calls plus reranking. Budget and trace every stage separately.

**Use when:** baseline misses synonyms, context-dependent questions, or multi-hop evidence, and evaluation proves the added stages improve outcomes.

## Modular RAG

```text
                         +-> policy/manual retriever --+
query -> router ---------+-> product/catalog retriever +-> fusion/reranker
         |               +-> incident/log retriever ---+        |
         +-> no-retrieval/tool route                            v
                                                        context builder
                                                               |
                                  validator <- generator <- prompt registry
```

Modules expose versioned inputs/outputs: router, retrievers, filters, rerankers, context builders, generators, and validators. Components can be promoted independently only when the evaluation manifest records the entire version tuple.

**Profile:** routing and remote modules add network/tail latency, but specialized indices can reduce candidate work.

**Accuracy trade-offs:** domain specialization and fallbacks improve precision; routing mistakes can eliminate relevant evidence before retrieval.

**Use when:** several corpora, modalities, tenants, retrieval engines, or answer policies need different paths.

**Operational requirements:** route-level SLOs, trace propagation, deterministic fallback, module contract tests, per-route evaluation sets, and circuit breakers.

## GraphRAG

```text
sources -> entity/relation extraction -> graph + community summaries
                                               |
query -> entity linking -> subgraph traversal -+-> evidence/summaries
                                                    -> generator
```

GraphRAG retrieves entities, relations, paths, neighborhoods, or hierarchical community summaries. Keep source-span provenance on every node and edge; extracted relations are model outputs, not unquestionable facts.

**Profile:** graph traversal may be fast, but graph construction, entity resolution, and summary generation are expensive. Global/community questions can require multiple levels of retrieval.

**Accuracy trade-offs:** strong for “how are these related?” and corpus-wide synthesis; weak entity resolution or stale summaries can create convincing false connections.

**Use when:** relationships and cross-document synthesis are central, not merely because the corpus is large.

**Controls:** relation confidence, temporal validity, provenance, entity ambiguity handling, graph-version lineage, and raw-source verification before answering.

## Agentic RAG

```text
user goal -> planner -> retrieve/tool -> inspect evidence -> decide next action
                ^                                            |
                +----- bounded loop / stop policy -----------+
                                      |
                               synthesize -> verify -> answer
```

An agent chooses searches, tools, and follow-up queries dynamically. Treat retrieved documents and tool results as untrusted data, not instructions.

**Profile:** variable latency and cost from iterative calls. Enforce wall-clock, step, token, and tool budgets; propagate cancellation.

**Accuracy trade-offs:** can decompose complex research and recover from weak first retrieval, but planning errors, loops, prompt injection, and unsupported synthesis increase risk.

**Use when:** tasks genuinely require adaptive multi-step investigation and a fixed DAG is insufficient.

**Controls:** allowlisted tools, least privilege, tenant-scoped retrieval, immutable audit trail, stop criteria, evidence coverage checks, human approval for side effects, and retrieval-only fallback.

## Pattern Selection

1. Establish naive hybrid RAG as the measurable baseline.
2. Diagnose retrieval misses separately from answer failures.
3. Add rewriting, reranking, or multi-step retrieval only for demonstrated error classes.
4. Use modular routing when domains have materially different corpora or policies.
5. Use GraphRAG when relationship traversal is a tested requirement.
6. Use agentic RAG only with bounded autonomy and adversarial evaluation.

## Evaluation by Stage

- **Router:** route accuracy, fallback rate, policy violations.
- **Retriever:** recall@k, precision@k, MRR/nDCG, filter correctness.
- **Reranker:** relevant-document lift and latency.
- **Context builder:** evidence coverage, duplication, token use.
- **Generator:** correctness, completeness, groundedness, citation precision/recall.
- **System:** p50/p95/p99 latency, cost, abstention quality, and task completion.
