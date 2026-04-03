"""
Query Diversity Test

Evaluates how diverse and non-redundant agent search queries are,
using word-overlap similarity.
"""

import json


def _word_set(text: str) -> set[str]:
    """Convert text to a set of lowercase words."""
    return set(text.lower().split())


def _jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two strings based on word overlap."""
    set_a = _word_set(a)
    set_b = _word_set(b)
    intersection = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def evaluate_query_diversity(agent_outputs: dict) -> dict:
    """
    Evaluate the diversity of agent search queries.

    Args:
        agent_outputs: dict containing 'research' key with raw JSON output

    Returns:
        Dict with diversity metrics.
    """
    raw = agent_outputs.get("research", "")

    # Parse the research output
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"skipped": True, "reason": "Could not parse research output as JSON"}

    queries = parsed.get("search_queries", [])

    if not queries:
        return {"skipped": True, "reason": "No search queries found in output"}

    # Extract query strings and topics
    query_strings = [q.get("query", "") for q in queries]
    topics = [q.get("topic", "") for q in queries]
    unique_topics = list(set(topics))

    # Compute pairwise similarity between all query strings
    n = len(query_strings)
    similarities = []

    if n >= 2:
        for i in range(n):
            for j in range(i + 1, n):
                sim = _jaccard_similarity(query_strings[i], query_strings[j])
                similarities.append({
                    "query_a": query_strings[i][:80],
                    "query_b": query_strings[j][:80],
                    "similarity": round(sim, 3),
                })

    avg_similarity = (
        round(sum(s["similarity"] for s in similarities) / len(similarities), 3)
        if similarities
        else 0.0
    )

    # Diversity score: 1 - avg_similarity (higher is better)
    diversity_score = round(1 - avg_similarity, 3)

    return {
        "num_queries": n,
        "unique_topics": unique_topics,
        "num_unique_topics": len(unique_topics),
        "avg_pairwise_similarity": avg_similarity,
        "diversity_score": diversity_score,
        "pairwise_details": similarities,
    }
