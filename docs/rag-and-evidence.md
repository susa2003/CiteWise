# RAG and evidence policy

## Retrieval

The baseline computes BM25 over stored page-bound chunks. Semantic embeddings use Sentence Transformers and a persistent ChromaDB collection when `CITEWISE_EMBEDDING_PROVIDER=sentence_transformers` and the optional packages are installed. Hybrid results are merged with reciprocal rank fusion. Document filters are applied to both retrieval paths; if the optional semantic packages fail to load, the API reports a keyword fallback.

## Grounded generation

The OpenAI-compatible adapter sends only selected source excerpts and bounded recent chat history. Factual claims must refer to exact retrieved chunk IDs. The backend discards each claim with an unknown citation ID, then builds filename, page, and excerpt values from its own stored records. This verifies citation identity and page provenance; it does not mathematically prove that a paraphrase entails its excerpt, so source excerpts remain visible for reader review.

## Abstention and research gaps

When evidence does not answer the question, return an explicit insufficient-evidence message. Author-stated limitations and inferred opportunities are distinct categories. A possible direction is not proof of novelty; claims of novelty require literature verification outside the uploaded corpus.

## Evaluation

The retrieval service includes Precision@K, Recall@K, and MRR helpers. The automated suite checks these formulas and exercises search/citation paths with generated PDF fixtures. A representative research-paper retrieval benchmark and measured quality report still need to be assembled before publishing retrieval-quality claims. Answer checks cover citation existence, page correctness, and behavior when a requested fact is absent. Never report metrics that have not been measured.
