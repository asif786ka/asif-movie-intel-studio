# Prompt Versioning — Asif Movie Intel Studio

## Strategy

All prompts used by the LangGraph pipeline are centralized, version-tracked, and auditable. This enables controlled iteration on prompt quality without risking regressions.

## Version Registry

Versions are managed via frozen dataclasses in `backend/app/core/versioning.py`:

```python
@dataclass(frozen=True)
class PromptVersions:
    system_prompt: str = "1.0.0"
    query_classifier: str = "1.0.0"
    answer_generation: str = "1.0.0"
    evidence_grading: str = "1.0.0"
    guardrail_check: str = "1.0.0"
    comparison: str = "1.0.0"

@dataclass(frozen=True)
class PipelineVersions:
    chunking: str = "1.0.0"
    embedding_model: str = "text-embedding-3-small"
    reranker: str = "1.0.0"
    retrieval: str = "1.0.0"
```

Using `frozen=True` ensures versions cannot be accidentally mutated at runtime.

## Prompt Catalog

| Prompt | Purpose | Version |
|--------|---------|---------|
| SYSTEM_PROMPT | Base instructions and citation rules for the assistant | 1.0.0 |
| QUERY_CLASSIFIER_PROMPT | Classifies queries into structured_only, rag_only, or hybrid | 1.0.0 |
| ANSWER_GENERATION_PROMPT | Generates grounded answers from merged context | 1.0.0 |
| EVIDENCE_GRADING_PROMPT | Scores evidence sufficiency (0.0-1.0) | 1.0.0 |
| GUARDRAIL_CHECK_PROMPT | Validates answers against context for fabrication | 1.0.0 |
| COMPARISON_PROMPT | Generates structured movie comparisons | 1.0.0 |

## Version Tracking Flow

1. All prompts live in `backend/app/core/prompts.py` as module-level constants
2. Version numbers are tracked in `backend/app/core/versioning.py`
3. The `get_all_versions()` function returns the current state for the admin dashboard
4. Each trace records the prompt version used (`prompt_version` field in GraphState)

## Changing a Prompt

To update a prompt:

1. Modify the prompt text in `prompts.py`
2. Bump the corresponding version in `versioning.py` (follow semver)
3. Run the evaluation suite to measure impact: `python eval/ragas_runner.py --all`
4. Compare metrics with the previous run's results in `eval/results/`
5. If metrics regress, revert or iterate

## Dashboard Integration

The admin dashboard displays current prompt versions in the "Prompt Versions" card, showing each prompt name and its version number. Pipeline versions (chunking strategy, embedding model, reranker, retrieval) are also tracked.

## Future Enhancements

- Prompt version history stored in a database for rollback
- A/B testing framework for comparing prompt variants on the same eval dataset
- Automated regression detection in CI pipeline
