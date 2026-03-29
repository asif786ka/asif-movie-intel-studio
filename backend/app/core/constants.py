QUERY_TYPE_STRUCTURED = "structured_only"
QUERY_TYPE_RAG = "rag_only"
QUERY_TYPE_HYBRID = "hybrid"
QUERY_TYPES = [QUERY_TYPE_STRUCTURED, QUERY_TYPE_RAG, QUERY_TYPE_HYBRID]

SOURCE_TYPES = [
    "review",
    "plot_summary",
    "critic_article",
    "interview",
    "franchise_notes",
    "award_writeup",
    "timeline",
    "analysis",
    "biography",
]

SUPPORTED_UPLOAD_EXTENSIONS = [".txt", ".md"]

EVIDENCE_SUFFICIENT_THRESHOLD = 0.3
MAX_RETRIES_EVIDENCE = 1

SAFE_REFUSAL_MESSAGE = (
    "I don't have sufficient evidence to provide a reliable answer to this question. "
    "Please try uploading relevant documents or refining your query."
)

GROUNDED_ANSWER_POLICY = (
    "You must only provide information that is directly supported by the provided context. "
    "Do not fabricate facts, awards, controversies, or rumors. "
    "If the context does not contain enough information, clearly state that."
)
