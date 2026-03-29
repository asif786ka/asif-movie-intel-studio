"""
Custom evaluation metrics for Asif Movie Intel Studio.

Metrics:
1. Citation Accuracy — percentage of citations that correctly reference source material
2. Unsupported Claim Rate — rate of claims not backed by provided context
3. Timeline Consistency — consistency of temporal references in answers
4. Source Diversity Score — diversity of sources used across answers
5. Routing Correctness — accuracy of query routing decisions

Each metric has both a single-result version and an aggregate version
that operates over a list of eval results.
"""

import re
from typing import Optional


def citation_accuracy(answer: str, sources: list[dict]) -> float:
    """Score a single answer's citation accuracy against available sources."""
    citation_pattern = r"\[Source\s*(\d+)\]"
    matches = re.findall(citation_pattern, answer)
    if not matches:
        return 1.0 if len(answer) < 200 else 0.0

    valid = 0
    for match in matches:
        idx = int(match) - 1
        if 0 <= idx < len(sources):
            valid += 1

    return valid / len(matches) if matches else 0.0


def citation_accuracy_score(results: list[dict]) -> float:
    """Aggregate citation accuracy across a list of eval results."""
    scores = []
    for r in results:
        resp = r.get("response", {})
        if not resp:
            continue
        answer = resp.get("answer", "")
        sources = resp.get("sources", [])
        if r.get("expected_citations", False):
            scores.append(citation_accuracy(answer, sources))
        else:
            scores.append(1.0)
    return sum(scores) / len(scores) if scores else 0.0


def unsupported_claim_check(answer: str, context: str) -> float:
    """Score a single answer for unsupported claims against context."""
    sentences = re.split(r"[.!?]+", answer)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if not sentences:
        return 0.0

    unsupported = 0
    context_lower = context.lower()
    common_words = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "and", "or", "but", "it", "this", "that", "with",
        "of", "by", "from", "has", "have", "had", "not", "be", "been",
        "can", "will", "its", "also", "as", "more", "than", "very",
    }

    for sentence in sentences:
        sentence_words = set(sentence.lower().split())
        meaningful_words = sentence_words - common_words
        if not meaningful_words:
            continue

        overlap = sum(1 for w in meaningful_words if w in context_lower)
        coverage = overlap / len(meaningful_words)

        if coverage < 0.2:
            unsupported += 1

    return unsupported / len(sentences) if sentences else 0.0


def unsupported_claim_rate(results: list[dict]) -> float:
    """Aggregate unsupported claim rate across eval results."""
    rates = []
    for r in results:
        resp = r.get("response", {})
        if not resp:
            continue
        answer = resp.get("answer", "")
        sources = resp.get("sources", [])
        context = " ".join(s.get("content", "") for s in sources)
        if answer and context:
            rates.append(unsupported_claim_check(answer, context))
    return sum(rates) / len(rates) if rates else 0.0


def timeline_consistency(answer: str) -> float:
    """Score timeline consistency within a single answer."""
    year_pattern = r"\b((?:19|20)\d{2})\b"
    years = [int(y) for y in re.findall(year_pattern, answer)]
    if len(years) < 2:
        return 1.0

    inconsistencies = 0
    segments = answer.split(".")

    for segment in segments:
        segment_years = [int(y) for y in re.findall(year_pattern, segment)]
        if len(segment_years) >= 2:
            seg_lower = segment.lower()
            if "before" in seg_lower or "prior to" in seg_lower:
                if segment_years[0] > segment_years[1]:
                    inconsistencies += 1
            if "after" in seg_lower or "following" in seg_lower:
                if segment_years[0] < segment_years[1]:
                    inconsistencies += 1
            if "from" in seg_lower and "to" in seg_lower:
                if segment_years[0] > segment_years[-1]:
                    inconsistencies += 1

    return max(0.0, 1.0 - (inconsistencies / max(len(years) - 1, 1)))


def timeline_consistency_score(results: list[dict]) -> float:
    """Aggregate timeline consistency across eval results."""
    scores = []
    for r in results:
        resp = r.get("response", {})
        if not resp:
            continue
        answer = resp.get("answer", "")
        if answer:
            scores.append(timeline_consistency(answer))
    return sum(scores) / len(scores) if scores else 1.0


def source_diversity(citations: list[dict]) -> float:
    """Score diversity of sources in citations for a single answer."""
    if not citations:
        return 0.0

    source_types = set()
    movie_titles = set()

    for citation in citations:
        metadata = citation.get("metadata", {})
        source_type = metadata.get("source_type", "unknown")
        movie_title = metadata.get("movie_title", "unknown")
        source_types.add(source_type)
        movie_titles.add(movie_title)

    type_diversity = len(source_types) / max(len(citations), 1)
    title_diversity = len(movie_titles) / max(len(citations), 1)

    return (type_diversity + title_diversity) / 2


def source_diversity_score(results: list[dict]) -> float:
    """Aggregate source diversity across eval results."""
    scores = []
    for r in results:
        resp = r.get("response", {})
        if not resp:
            continue
        citations = resp.get("citations", [])
        if citations:
            scores.append(source_diversity(citations))
    return sum(scores) / len(scores) if scores else 0.0


def routing_correctness(predicted_routes: list[str], expected_routes: list[str]) -> float:
    """Score routing correctness from parallel lists."""
    if not predicted_routes or not expected_routes:
        return 0.0
    if len(predicted_routes) != len(expected_routes):
        return 0.0
    correct = sum(1 for p, e in zip(predicted_routes, expected_routes) if p == e)
    return correct / len(predicted_routes)


def routing_correctness_score(results: list[dict]) -> float:
    """Aggregate routing correctness from eval results with expected_route."""
    predicted = []
    expected = []
    for r in results:
        exp_route = r.get("expected_route", "")
        resp = r.get("response", {})
        act_route = resp.get("route_type", "") if resp else ""
        if exp_route and act_route:
            predicted.append(act_route)
            expected.append(exp_route)
    return routing_correctness(predicted, expected) if predicted else 0.0


def compute_all_metrics(
    answer: str,
    context: str,
    sources: list[dict],
    citations: list[dict],
    predicted_route: Optional[str] = None,
    expected_route: Optional[str] = None,
) -> dict[str, float]:
    """Compute all metrics for a single query result."""
    metrics = {
        "citation_accuracy": citation_accuracy(answer, sources),
        "unsupported_claim_rate": unsupported_claim_check(answer, context),
        "timeline_consistency": timeline_consistency(answer),
        "source_diversity": source_diversity(citations),
    }

    if predicted_route and expected_route:
        metrics["routing_correct"] = 1.0 if predicted_route == expected_route else 0.0

    return metrics
