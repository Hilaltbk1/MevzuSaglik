"""Sorudan topic tahmini (kural tabanlı, LLM yok)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from backend.utils.categories import TOPIC_KEYWORDS


@dataclass
class TopicRoute:
    topics: List[str]
    confidence: float
    reason: str


def classify_topics(question: str, top_k: int = 2) -> TopicRoute:
    q = (question or "").lower()
    if not q.strip():
        return TopicRoute(topics=[], confidence=0.0, reason="empty")

    scores = {}
    for slug, words in TOPIC_KEYWORDS.items():
        if slug == "genel":
            continue
        hit = sum(1 for w in words if w in q)
        if hit:
            scores[slug] = hit

    if not scores:
        return TopicRoute(topics=[], confidence=0.0, reason="no_keyword_hit")

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    topics = [s for s, _ in ranked[:top_k]]
    best = ranked[0][1]
    # 1 hit → 0.75 (filtre açılsın), 2+ → 0.95
    confidence = min(0.95, 0.55 + 0.20 * best)

    return TopicRoute(topics=topics, confidence=confidence, reason=f"hits={dict(ranked[:3])}")


def should_apply_topic_filter(route: TopicRoute, min_confidence: float = 0.70) -> bool:
    if route.confidence < min_confidence:
        return False
    if not route.topics:
        return False
    if route.topics == ["genel"]:
        return False
    return True
