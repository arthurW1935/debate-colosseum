from sentence_transformers import CrossEncoder

_reranker = None  # Lazy singleton model caching to avoid reloading on every query

def get_reranker() -> CrossEncoder:
    """Lazily loads and returns the CrossEncoder model instance."""
    global _reranker
    if _reranker is None:
        # Load local cross-encoder for ms-marco MiniLM
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker

def doc_retrieval(query: str, retriever) -> list[str]:
    """Retrieves top 8 candidates using cosine similarity, then reranks to top 4 using a cross-encoder.
    
    If retriever is None (no docs uploaded), falls back gracefully and returns an empty list.
    """
    if not retriever:
        return []
        
    try:
        from src.rag.ingest import build_vector_store
        
        # In our updated architecture, retriever is actually a list of chunks stored in GraphState
        # We rebuild the EphemeralClient collection on the fly to avoid checkpointer serialization issues
        vector_store = build_vector_store(retriever)
        
        # Cosine similarity search for top 8 candidates from Chroma vector store
        results = vector_store.query(query_texts=[query], n_results=8)
        
        # Check if results are valid and contain documents
        if not results or "documents" not in results or not results["documents"] or not results["documents"][0]:
            return []
            
        candidates = results["documents"][0]
        metadatas = results["metadatas"][0]
        
        # Load the lazy singleton cross-encoder
        reranker = get_reranker()
        
        # Run Cross-Encoder predictions
        pairs = [[query, doc] for doc in candidates]
        scores = reranker.predict(pairs)
        
        # Rank candidate documents based on cross-encoder relevancy scores in descending order
        ranked = sorted(zip(candidates, metadatas, scores), key=lambda x: x[2], reverse=True)
        top4 = ranked[:4]
        
        # Format output as specified in prompt: [Source: source_name] document_text
        return [f"[Source: {meta['source']}] {doc}" for doc, meta, score in top4]
        
    except Exception as e:
        # Re-raise descriptive exception as tools should not silently swallow errors
        raise RuntimeError(f"doc_retrieval tool failed for query '{query}': {e}") from e
