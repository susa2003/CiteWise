from collections import Counter
import math
import re
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of",
    "on", "or", "that", "the", "this", "to", "was", "were", "what", "which", "with",
}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text) if token.lower() not in STOP_WORDS]


def rank_bm25(query: str, chunks: list[Any], limit: int = 20, k1: float = 1.5, b: float = 0.75) -> list[tuple[Any, float]]:
    """Small BM25 implementation so keyword retrieval has no model dependency."""
    query_terms = list(dict.fromkeys(tokenize(query)))
    if not chunks or not query_terms:
        return []

    tokenized = [tokenize(chunk.content) for chunk in chunks]
    lengths = [len(item) for item in tokenized]
    average_length = sum(lengths) / len(lengths) if lengths else 0.0
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))

    scored: list[tuple[Any, float]] = []
    total = len(chunks)
    for chunk, tokens, length in zip(chunks, tokenized, lengths):
        frequencies = Counter(tokens)
        score = 0.0
        for term in query_terms:
            frequency = frequencies[term]
            if not frequency:
                continue
            doc_freq = document_frequency[term]
            inverse_frequency = math.log(1 + (total - doc_freq + 0.5) / (doc_freq + 0.5))
            denominator = frequency + k1 * (1 - b + b * (length / average_length if average_length else 0))
            score += inverse_frequency * frequency * (k1 + 1) / denominator
        if score > 0:
            scored.append((chunk, score))
    scored.sort(key=lambda item: (-item[1], item[0].id))
    return scored[:limit]
