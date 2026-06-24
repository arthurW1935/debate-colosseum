import pytest
from src.schemas import GraphState
from src.rag.ingest import ingest_context

def test_ingest_context_node_empty():
    # Setup initial state with no context documents
    state = GraphState(
        problem_statement="Should we expand the business?",
        run_id="test-run-123",
        context_docs=[]
    )
    
    # Run node — now returns a partial dict
    result = ingest_context(state)
    
    # Assert retriever is None
    assert isinstance(result, dict)
    assert result["retriever"] is None
    # Assert context_docs is NOT in the returned dict (prevents doubling)
    assert "context_docs" not in result

def test_ingest_context_node_with_docs(tmp_path):
    # Create test documents
    doc1 = tmp_path / "doc1.txt"
    doc1.write_text("Company revenue is $10M.", encoding="utf-8")
    
    doc2 = tmp_path / "doc2.md"
    doc2.write_text("# Market\nMarket size is growing by 5% annually.", encoding="utf-8")
    
    # Setup state
    state = GraphState(
        problem_statement="Analyze growth and finance",
        run_id="test-run-456",
        context_docs=[str(doc1), str(doc2)]
    )
    
    # Run node — now returns a partial dict
    result = ingest_context(state)
    
    # Assert retriever is populated (as raw chunks list)
    assert isinstance(result, dict)
    assert result["retriever"] is not None
    assert isinstance(result["retriever"], list)
    assert len(result["retriever"]) > 0
    # Assert context_docs is NOT in the returned dict (prevents doubling)
    assert "context_docs" not in result

