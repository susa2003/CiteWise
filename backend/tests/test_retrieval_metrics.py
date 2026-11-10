import pytest

from backend.app.services.retrieval.evaluation import mean_reciprocal_rank, precision_at_k, recall_at_k


def test_retrieval_metrics_are_deterministic() -> None:
    ranking = ["irrelevant", "relevant-a", "relevant-b"]
    assert precision_at_k(ranking, {"relevant-a", "relevant-b"}, 2) == 0.5
    assert recall_at_k(ranking, {"relevant-a", "relevant-b"}, 2) == 0.5
    assert mean_reciprocal_rank([ranking, ["relevant-b"]], [{"relevant-a"}, {"relevant-b"}]) == 0.75


def test_retrieval_metrics_reject_invalid_k_and_mismatched_queries() -> None:
    with pytest.raises(ValueError):
        precision_at_k([], set(), 0)
    with pytest.raises(ValueError):
        mean_reciprocal_rank([["a"]], [])
