"""
Prompt Catalog — All LLM prompts used by the RAG pipeline.

Architecture Note (Senior AI Architect):
  Every prompt in the system is defined here as a module-level constant.
  This centralization enables:
    1. Version tracking via core/versioning.py
    2. Easy A/B testing by swapping prompt variants
    3. Auditable prompt history through version control
    4. Consistent citation and safety rules across all prompts

  Prompt Design Principles:
    - System prompt enforces grounded-answer policies globally
    - Classification prompt uses few-shot examples for accuracy
    - Evidence grading uses numeric output for programmatic thresholds
    - Guardrail prompt checks 5 specific fabrication categories
    - All prompts use {variable} substitution (Python str.format)

  Safety: The system prompt's 7 rules are the foundation of the entire
  safety architecture. They are reinforced by guardrail_service.py's
  regex-based output checking and evidence sufficiency scoring.
"""

# ===========================================================================
# SYSTEM PROMPT (v1.0.0)
# Applied as the system message in every LLM call during answer generation.
# The 7 rules form the backbone of the grounded-answer safety policy.
# ===========================================================================

SYSTEM_PROMPT = """You are Asif Movie Intel Studio, an expert movie research assistant. 
You provide grounded, well-cited answers about movies, directors, actors, franchises, and the film industry.

RULES:
1. Only use information from the provided context (TMDB data and/or retrieved documents).
2. Always cite your sources using [Source N] format where N corresponds to the source index.
3. Never fabricate facts, awards, controversies, rumors, or unsupported claims.
4. If the evidence is insufficient, clearly state that rather than guessing.
5. Be concise but thorough. Structure your answers with clear sections when appropriate.
6. For comparisons, provide balanced analysis across all requested dimensions.
7. Distinguish between structured data (from TMDB) and unstructured analysis (from documents).
"""

# ===========================================================================
# QUERY CLASSIFIER PROMPT (v1.0.0)
# Determines the retrieval path: structured_only | rag_only | hybrid.
# Uses few-shot examples for reliable classification.
# ===========================================================================

QUERY_CLASSIFIER_PROMPT = """Classify the following user query into one of three categories:
- "structured_only": The query can be answered purely with structured movie metadata (titles, dates, ratings, cast, crew, genres, similar movies, box office data).
- "rag_only": The query requires analysis, reviews, thematic discussion, interviews, timeline explanations, or other unstructured content.
- "hybrid": The query needs both structured metadata AND unstructured analysis/reviews.

Examples:
- "List top Nolan sci-fi movies" -> structured_only
- "What are the highest rated movies of 2023?" -> structured_only
- "Find movies similar to Inception" -> structured_only
- "Explain philosophical themes in Interstellar" -> rag_only
- "Summarize critic reviews of Oppenheimer" -> rag_only
- "What recurring themes appear in Denis Villeneuve films?" -> rag_only
- "Compare Interstellar and Dune by themes and reception" -> hybrid
- "Which Christopher Nolan sci-fi films had the strongest critical reception and why?" -> hybrid
- "Show movies similar to Arrival and explain thematic connections" -> hybrid

Query: {query}

Respond with ONLY the classification: structured_only, rag_only, or hybrid"""

# ===========================================================================
# ANSWER GENERATION PROMPT (v1.0.0)
# Generates the grounded answer from merged context.
# ===========================================================================

ANSWER_GENERATION_PROMPT = """Based on the following context, answer the user's question.
Follow the system rules strictly — cite sources, never fabricate, and state when evidence is insufficient.

CONTEXT:
{context}

USER QUESTION: {query}

Provide a well-structured answer with citations in [Source N] format."""

# ===========================================================================
# EVIDENCE GRADING PROMPT (v1.0.0)
# Scores evidence sufficiency on a 0.0-1.0 scale.
# Numeric-only output enables programmatic threshold checking.
# ===========================================================================

EVIDENCE_GRADING_PROMPT = """Evaluate whether the following context provides sufficient evidence to answer the query.
Consider: relevance, completeness, and reliability of the evidence.

QUERY: {query}
CONTEXT: {context}

Rate the evidence sufficiency from 0.0 to 1.0 where:
- 0.0-0.3: Insufficient — cannot reliably answer
- 0.3-0.6: Partial — can answer with caveats
- 0.6-1.0: Sufficient — can provide a grounded answer

Respond with ONLY a number between 0.0 and 1.0."""

# ===========================================================================
# GUARDRAIL CHECK PROMPT (v1.0.0)
# Post-generation safety check for 5 fabrication categories.
# Binary PASS/FAIL output for simple programmatic handling.
# ===========================================================================

GUARDRAIL_CHECK_PROMPT = """Review the following answer for compliance with grounded-answer policies.

Check for:
1. Fabricated facts not supported by the provided context
2. Unsupported award claims
3. Fabricated controversies or rumors
4. Claims that go beyond the provided evidence
5. Speculative statements presented as fact

CONTEXT PROVIDED: {context}
ANSWER TO CHECK: {answer}

If the answer is compliant, respond with: PASS
If there are issues, respond with: FAIL: [brief description of issues]"""

# ===========================================================================
# COMPARISON PROMPT (v1.0.0)
# Generates structured multi-movie comparisons.
# 7-section format ensures consistent, balanced analysis.
# ===========================================================================

COMPARISON_PROMPT = """Compare the following movies based on the provided context.
Structure your comparison with these sections:
1. Summary — brief overview of each movie
2. Themes — thematic comparison
3. Critical Reception — critic reviews and scores
4. Audience Reception — audience ratings and reception
5. Awards — award nominations and wins
6. Timeline — release timeline and production context
7. Cast & Director — key talent comparison

Use only information from the provided context. Cite sources using [Source N] format.

CONTEXT:
{context}

MOVIES TO COMPARE: {movies}

Provide a structured comparison."""
