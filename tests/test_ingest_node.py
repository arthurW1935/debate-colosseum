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
    
    # Run node
    new_state = ingest_context(state)
    
    # Assert retriever is None and other fields are unchanged
    assert new_state.retriever is None
    assert new_state.problem_statement == state.problem_statement
    assert new_state.run_id == state.run_id
    # Assert non-destructive update (id of state is different)
    assert id(new_state) != id(state)

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
    
    # Run node
    new_state = ingest_context(state)
    
    # Assert retriever is populated
    assert new_state.retriever is not None
    assert new_state.problem_statement == state.problem_statement
    assert new_state.run_id == state.run_id
    
    # Query retriever
    results = new_state.retriever.query(query_texts=["revenue"], n_results=1)
    assert "revenue is $10M" in results["documents"][0][0]
    
    results_market = new_state.retriever.query(query_texts=["market growth"], n_results=1)
    assert "Market size" in results_market["documents"][0][0]
