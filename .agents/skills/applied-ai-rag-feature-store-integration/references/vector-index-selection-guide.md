# Vector Index Selection Guide

## Index Comparison

| Index | Recall@k ceiling | Build time | Query latency | Memory footprint | Update cost |
|---|---|---|---|---|---|
| Flat/brute-force | Exact | None/minimal | Linear; high at scale | Vectors only | Low |
| IVF | High with enough probes | Medium; trains centroids | Low–medium | Moderate | Medium; retraining eventually |
| HNSW | Very high when tuned | High | Very low | High graph overhead | Low–medium online |
| PQ/IVF-PQ | Lower/approximate | Medium–high; trains codebooks | Very low | Very low | Medium–high |
| ScaNN | High on supported workloads | Medium–high | Very low | Low–moderate | Often batch-oriented |
| DiskANN | High | High | Low with SSD | Low RAM, high SSD | Deployment-dependent |

These are directional comparisons. Recall and latency depend on dimension, distribution, filters, hardware, concurrency, and implementation.

## Flat / Exact Search

Compute similarity against every vector. Use it as ground truth for evaluating approximate indices.

- **Strengths:** exact recall, simple updates, no training, predictable semantics.
- **Limits:** cost grows linearly with corpus size; memory bandwidth dominates.
- **Use when:** small corpus, low query volume, heavy filtering reduces candidates sharply, or offline evaluation requires truth sets.

GPU flat search can remain competitive at surprisingly large sizes when batching is high; benchmark rather than applying a fixed cutoff.

## IVF

Cluster vectors into inverted lists; query probes only selected lists.

- **Tuning:** number of lists controls partition granularity; probes trade latency for recall.
- **Strengths:** scalable and interpretable recall/latency control.
- **Limits:** representative training sample required; distribution drift and uneven lists hurt performance.
- **Updates:** inserts are practical, but centroid quality degrades as data shifts; monitor list balance and recall.

Start with enough lists to avoid huge candidate buckets, then tune probes against exact-search truth.

## HNSW

Build a multilayer proximity graph and traverse it during search.

- **Tuning:** graph degree controls memory/connectivity; construction effort controls build quality; search effort controls recall/latency.
- **Strengths:** excellent interactive latency and recall; supports incremental insertion.
- **Limits:** graph overhead can exceed vector storage; deletes and large rebuilds need planning; filters may reduce navigability.
- **Use when:** low-latency online search, moderate-to-large corpus, and RAM is available.

Test filtered recall separately. Post-filtering can return too few authorized results; pre-filtering or filtered graph techniques may be needed.

## Product Quantization

Encode vector subvectors into compact codebook indices. PQ is often paired with IVF and optional exact reranking.

- **Strengths:** large memory reduction and cache-friendly scans.
- **Limits:** quantization error lowers recall, especially for subtle or high-precision neighborhoods.
- **Use when:** corpus size makes full vectors too expensive and reranking a candidate set with original vectors is possible.

Train codebooks on representative vectors and evaluate by language/domain/tenant. Store full vectors for reranking when quality requirements demand it.

## ScaNN

Combines partitioning, quantization/scoring, and efficient reordering, especially for maximum inner-product search.

- **Strengths:** strong throughput/latency on optimized hardware and batch workloads.
- **Limits:** deployment and online-update model are less universal than HNSW; integration capabilities vary.
- **Use when:** its supported environment matches the serving stack and benchmark results beat simpler alternatives.

## DiskANN

Keeps a navigable graph primarily on SSD with a smaller memory footprint and caching.

- **Strengths:** billion-scale potential without holding the full graph in RAM.
- **Limits:** build pipelines, SSD random-read behavior, caching, and update workflows add complexity.
- **Use when:** data exceeds economical RAM and tight online latency is still required.

Benchmark on production-equivalent SSDs, queue depth, and concurrency. Cloud storage volumes may behave very differently from local NVMe.

## Corpus-Size Guidance

| Situation | Starting candidate |
|---|---|
| Under roughly 100k vectors | Flat, then HNSW if latency/concurrency requires |
| 100k–10m, RAM available | HNSW or IVF; compare filtered recall |
| 10m–100m, memory constrained | IVF-PQ with full-vector rerank |
| Very large, SSD-rich | DiskANN or distributed IVF/PQ |
| Batch/GPU-heavy exact evaluation | Flat GPU |
| Frequent online inserts | HNSW or update-friendly managed index |

These ranges are experiment starting points, not selection rules. Vector dimension, replicas, tenant filters, and QPS can move boundaries by orders of magnitude.

## Latency-Driven Procedure

1. Build an exact-search truth set from production-like queries.
2. Define recall@k and p95/p99 latency objectives plus memory/cost limits.
3. Reproduce corpus size, dimensions, filter selectivity, update rate, and concurrency.
4. Tune each candidate across a recall/latency curve, not one configuration.
5. Measure cold and warm caches, tail latency, ingestion, deletion, and rebuild time.
6. Segment recall by language, domain, tenant, and hard-query class.
7. Include metadata filtering and reranking in end-to-end latency.
8. Choose the simplest index that meets quality and operational constraints with margin.

## Benchmark Manifest

Record embedding model/dimension/normalization, distance metric, corpus hash, index library/version, hardware, build parameters, search parameters, replicas, filter workload, update workload, concurrency, and truth-set generation. Without this manifest, benchmark numbers are not reproducible.

## Operational Checks

- Reject mixed embedding dimensions or model versions.
- Use shadow indices and alias cutover for rebuilds.
- Monitor recall on a sentinel query set, not only latency.
- Track deleted/stale vectors and compaction needs.
- Verify tenant and authorization filters before context release.
- Preserve original source IDs, revisions, and deletion propagation.
