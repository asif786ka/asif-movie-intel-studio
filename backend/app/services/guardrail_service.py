"""
GuardrailService — Multi-layer safety enforcement for the RAG pipeline.

Architecture Note (Senior AI Architect):
  This service implements defense-in-depth safety for the RAG pipeline:

  Layer 1 — Input Guardrails (check_input):
    Prompt injection detection using regex patterns from core/security.py.
    Blocks queries before they reach the LLM, preventing:
    - System prompt override attempts ("ignore previous instructions")
    - Role hijacking ("you are now a different AI")
    - Information exfiltration ("reveal your system prompt")

  Layer 2 — Evidence Sufficiency (check_evidence_sufficiency):
    Prevents hallucination by measuring query-context overlap.
    If retrieved context doesn't cover enough query terms, the pipeline
    either retries retrieval or refuses to answer.

  Layer 3 — Output Guardrails (check_output):
    Post-generation fabrication detection using compiled regex patterns.
    Catches unsupported award claims, fabricated controversies,
    unverified financial figures, and speculative statements.
    Each match is verified against the actual context — if the claim
    can't be found in context, the answer is rejected.

  Scalability Considerations:
    - Regex patterns are pre-compiled at module load time
    - Evidence scoring uses simple word overlap (no LLM call needed)
    - Output checking is O(n * m) where n=patterns, m=answer length
"""

import re
from typing import Optional
from app.core.logging import get_logger
from app.core.security import detect_prompt_injection
from app.core.constants import SAFE_REFUSAL_MESSAGE, GROUNDED_ANSWER_POLICY
from app.services.bedrock_service import llm_provider

logger = get_logger(__name__)

# Pre-compiled regex patterns for detecting potentially fabricated claims.
# These patterns catch common hallucination categories in movie-domain answers:
#   - Award claims (Oscar, Golden Globe, BAFTA, Emmy, Palme d'Or)
#   - Financial claims (grossed/earned $X billion/million)
#   - Controversy/scandal references
#   - Rumor-based statements
#   - Hedged assertions ("it is widely known/believed")
UNSUPPORTED_PATTERNS = [
    r"(?:won|received|awarded)\s+(?:the\s+)?(?:Oscar|Academy Award|Golden Globe|BAFTA|Emmy|Palme)",
    r"(?:grossed|earned|made)\s+\$[\d,.]+\s*(?:billion|million)",
    r"controversy\s+(?:surrounding|around|about)",
    r"scandal\s+(?:involving|about|surrounding)",
    r"rumor(?:ed|s)?\s+(?:that|to\s+be)",
    r"allegedly\s+",
    r"it\s+is\s+(?:widely\s+)?(?:known|believed|rumored)\s+that",
]

_compiled_unsupported = [re.compile(p, re.IGNORECASE) for p in UNSUPPORTED_PATTERNS]


class GuardrailService:
    """Central safety service enforcing input validation, evidence grading, and output verification."""

    async def check_input(self, query: str) -> tuple[bool, Optional[str]]:
        """Layer 1: Check user input for prompt injection attacks.

        Returns:
            (is_safe, reason): If not safe, reason contains the user-facing refusal message.
        """
        is_injection, matched = detect_prompt_injection(query)
        if is_injection:
            logger.warning(f"Prompt injection blocked: {matched}")
            return False, "Your query was blocked by our safety filters. Please rephrase your question about movies."
        return True, None

    async def check_output(self, answer: str, context: str) -> tuple[bool, Optional[str], list[str]]:
        """Layer 3: Scan generated answer for fabricated or unsupported claims.

        Each regex match is verified against the provided context.
        If > 50% of claim words appear in context, the claim is considered supported.

        Returns:
            (is_safe, reason, issues): List of specific issues found.
        """
        issues = []

        for pattern in _compiled_unsupported:
            matches = pattern.findall(answer)
            for match in matches:
                match_str = match if isinstance(match, str) else match[0]
                if not self._verify_claim_in_context(match_str, context):
                    issues.append(f"Potentially unsupported claim: '{match_str}'")

        if issues:
            logger.warning(f"Guardrail issues found: {issues}")
            return False, "Some claims in the response could not be verified against available sources.", issues

        return True, None, []

    def _verify_claim_in_context(self, claim: str, context: str) -> bool:
        """Check whether a specific claim has supporting evidence in the context.

        Uses word-level overlap: if more than 50% of claim words appear
        in the context, the claim is considered supported.
        """
        claim_words = set(claim.lower().split())
        context_lower = context.lower()
        matched = sum(1 for w in claim_words if w in context_lower)
        return matched / max(len(claim_words), 1) > 0.5

    async def check_evidence_sufficiency(self, query: str, context: str) -> tuple[bool, float]:
        """Layer 2: Evaluate whether retrieved context is sufficient to answer the query.

        Scoring Formula:
          score = (query_term_coverage * 0.6) + (context_length_score * 0.4)

        Where:
          - query_term_coverage = overlap(query_terms, context_terms) / len(query_terms)
          - context_length_score = min(word_count / 200, 1.0)

        Threshold: score >= 0.3 is considered sufficient (partial evidence is OK).

        Returns:
            (is_sufficient, score): Boolean sufficiency flag and numeric score.
        """
        if not context or len(context.strip()) < 50:
            return False, 0.0

        query_terms = set(query.lower().split())
        context_terms = set(context.lower().split())
        overlap = len(query_terms & context_terms)
        coverage = overlap / max(len(query_terms), 1)

        # Very low coverage means context is completely off-topic
        if coverage < 0.2:
            return False, coverage

        # Combine term coverage with context volume
        word_count = len(context.split())
        length_score = min(word_count / 200, 1.0)

        score = (coverage * 0.6) + (length_score * 0.4)
        return score >= 0.3, score

    def get_safe_refusal(self, reason: Optional[str] = None) -> str:
        """Generate a safe, user-friendly refusal message."""
        if reason:
            return f"{SAFE_REFUSAL_MESSAGE} Reason: {reason}"
        return SAFE_REFUSAL_MESSAGE


guardrail_service = GuardrailService()
