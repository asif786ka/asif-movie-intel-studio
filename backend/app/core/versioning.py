from dataclasses import dataclass


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


PROMPT_VERSIONS = PromptVersions()
PIPELINE_VERSIONS = PipelineVersions()


def get_all_versions() -> dict:
    return {
        "prompts": {
            "system_prompt": PROMPT_VERSIONS.system_prompt,
            "query_classifier": PROMPT_VERSIONS.query_classifier,
            "answer_generation": PROMPT_VERSIONS.answer_generation,
            "evidence_grading": PROMPT_VERSIONS.evidence_grading,
            "guardrail_check": PROMPT_VERSIONS.guardrail_check,
            "comparison": PROMPT_VERSIONS.comparison,
        },
        "pipeline": {
            "chunking": PIPELINE_VERSIONS.chunking,
            "embedding_model": PIPELINE_VERSIONS.embedding_model,
            "reranker": PIPELINE_VERSIONS.reranker,
            "retrieval": PIPELINE_VERSIONS.retrieval,
        },
    }
