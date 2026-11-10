from collections.abc import Sequence


def precision_at_k(ranked_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    if k < 1:
        raise ValueError("k must be at least 1")
    selected = ranked_ids[:k]
    return sum(item in relevant_ids for item in selected) / k


def recall_at_k(ranked_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    if k < 1:
        raise ValueError("k must be at least 1")
    if not relevant_ids:
        return 0.0
    return sum(item in relevant_ids for item in ranked_ids[:k]) / len(relevant_ids)


def mean_reciprocal_rank(ranked_lists: Sequence[Sequence[str]], relevant_sets: Sequence[set[str]]) -> float:
    if len(ranked_lists) != len(relevant_sets):
        raise ValueError("One relevant ID set is required per ranked list")
    if not ranked_lists:
        return 0.0
    total = 0.0
    for ranked_ids, relevant_ids in zip(ranked_lists, relevant_sets):
        rank = next((index for index, item in enumerate(ranked_ids, start=1) if item in relevant_ids), None)
        if rank:
            total += 1 / rank
    return total / len(ranked_lists)
