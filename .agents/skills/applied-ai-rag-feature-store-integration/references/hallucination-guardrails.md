# Hallucination Guardrails

## Defense in Depth

Hallucination risk is reduced by combining evidence quality, retrieval sufficiency, constrained generation, claim verification, citations, calibrated confidence, output validation, and safe fallback. A prompt alone is not a control boundary.

## Guardrail Decision Tree

```text
Does the task require factual grounding?
|-- no -> apply domain safety and output validation
`-- yes
    |-- Is authorized, fresh evidence available?
    |   |-- no -> abstain, ask clarification, or route to human/search
    |   `-- yes
    |       |-- Does retrieval cover all material parts of the question?
    |       |   |-- no -> rewrite/multi-step retrieve; then recheck or abstain
    |       |   `-- yes
    |       |       |-- Is risk high (medical/legal/financial/action-taking)?
    |       |       |   |-- yes -> claim verification + strict citations + human gate
    |       |       |   `-- no -> grounded generation + citation verification
    |       |       `-- Did validation pass?
    |       |           |-- no -> regenerate once with constraints, then fallback
    |       |           `-- yes -> return answer with evidence and confidence limits
```

## Retrieval Sufficiency Thresholds

Define sufficiency before generation using several signals:

- top score and margin to unrelated candidates;
- relevant-document count and source diversity;
- semantic coverage of query entities/subquestions;
- freshness and authority tier;
- contradiction/conflict detection;
- metadata and authorization filter success.

Similarity scores are model/index specific and not probabilities. Calibrate thresholds against labeled answerable and unanswerable queries. Segment by query type, language, and corpus because one global threshold often fails.

### Actions

- **High sufficiency:** generate with citations.
- **Borderline:** rewrite query, broaden retrieval, rerank, or ask clarification.
- **Low:** abstain or offer retrieval-only source links.
- **Conflicting:** present uncertainty and sources; do not silently choose.

## Grounding Checks

Break answers into atomic factual claims. For each claim, require one or more source spans that entail it. Classify:

- supported;
- partially supported;
- unsupported;
- contradicted;
- unverifiable opinion/inference.

Block or rewrite unsupported material claims. Permit clearly labeled synthesis only when the product policy allows it. Numerical, temporal, and comparative claims need exact support rather than topical similarity.

## Citation Verification

A citation is valid only if the referenced source span exists, is authorized, and supports the associated claim.

1. Preserve document ID, revision, chunk offsets, title, and access metadata through retrieval.
2. Require claim-to-citation mapping, not a source list appended to an answer.
3. Verify quoted text exactly and check numeric/date/entity agreement.
4. Reject citations to stale/deleted revisions or inaccessible sources.
5. Measure citation precision and recall on labeled examples.

Do not let the generator invent URLs or document identifiers; resolve citations from trusted retrieval metadata after generation.

## Confidence Calibration

Model self-confidence is not sufficient. Build a confidence score from calibrated observable signals such as retrieval sufficiency, reranker score, evidence coverage, verifier result, source quality, contradiction count, and out-of-distribution detection.

Use held-out labeled data to map scores to empirical correctness. Report calibration error and reliability curves. Recalibrate when embedding, reranker, generator, prompt, corpus, or index changes.

Confidence should control an action—answer, qualify, clarify, or abstain—not merely display a percentage.

## Output Validation Chains

Apply deterministic checks first, then specialized model checks only when needed:

1. schema/JSON and required-field validation;
2. length, format, allowlist, and policy constraints;
3. citation identifier and span validation;
4. entity, number, unit, and date consistency;
5. claim-evidence entailment;
6. contradiction and unsafe-action checks;
7. privacy/secret/tenant leakage checks;
8. final rendering from validated structured output.

Bound regeneration attempts. Repeatedly asking the same model to “be accurate” can produce different unsupported text without improving evidence.

## Fallback Strategies

| Failure | Preferred fallback |
|---|---|
| No relevant evidence | Explicit no-answer plus safe source/search options |
| Ambiguous query | Ask one targeted clarifying question |
| Partial evidence | Answer only supported parts and name omissions |
| Conflicting sources | Present conflict, timestamps, and authority differences |
| Verifier unavailable | Retrieval-only response or fail closed for high risk |
| Generator unavailable | Extractive snippets with citations |
| Latency budget exhausted | Cached authorized result or concise retrieval-only result |
| High-risk action | Human review/approval before execution |

Fallbacks must preserve tenant authorization and freshness. Cached answers need corpus, policy, model, and permission-aware keys.

## Prompt Injection and Evidence Isolation

Treat retrieved content as untrusted data. Delimit it from instructions, strip or flag executable markup as policy requires, and never grant tools or credentials based on document text. Tool permissions come from application policy and user authorization.

Test malicious documents that request secret disclosure, system-prompt override, cross-tenant retrieval, or unauthorized tool use. Log safe metadata and decisions rather than sensitive prompt/context contents.

## Monitoring

Track retrieval sufficiency distribution, abstention/clarification rate, unsupported-claim rate, citation precision/recall, contradiction rate, fallback reason, user corrections, and quality by corpus/query segment. Correlate with model, prompt, embedding, index, corpus watermark, and feature versions.

Alert on changes in rates and labeled quality, not only service errors. A healthy endpoint can be consistently ungrounded.

## Release Gate

- Answerable, unanswerable, stale, conflicting, adversarial, and multilingual cases are represented.
- Retrieval and generation are evaluated separately.
- Thresholds are calibrated on held-out data.
- Every factual answer can map claims to source spans.
- High-risk paths fail closed or require human approval.
- Fallbacks are tested under dependency failure and latency exhaustion.
- Tenant isolation and deletion propagation are verified.
- The full version tuple and evaluation evidence are retained for rollback.
