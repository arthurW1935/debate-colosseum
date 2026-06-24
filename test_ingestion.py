import glob
from src.rag.ingest import ingest_context
from src.schemas import GraphState

def main():
    print("Starting manual ingestion test...")
    
    # Load markdown files from synthetic_docs
    docs = glob.glob("synthetic_docs/*.md")
    docs = [d for d in docs if "README.md" not in d]
    
    if not docs:
        print("No documents found in synthetic_docs!")
        return
        
    print(f"Found {len(docs)} documents to ingest.")
    
    # Create a dummy state to pass to ingest_context
    dummy_state = GraphState(
        problem_statement="Testing Ingestion",
        run_id="test_run",
        current_turn=1,
        context_docs=docs
    )
    
    print("Ingesting context into Chroma DB...")
    new_state = ingest_context(dummy_state)
    
    print("Ingestion complete!")
    print(f"Retriever initialized: {new_state.retriever}")
    
    print("\nTesting a sample query for 'financial projections'...")
    results = new_state.retriever.query(query_texts=["financial projections"], n_results=1)
    
    if results and "documents" in results and results["documents"]:
        print("\nTop matched snippet:")
        print(f"{results['documents'][0][0][:300]}...")
        print(f"Source: {results['metadatas'][0][0]['source']}")
    else:
        print("No documents matched the query.")

if __name__ == "__main__":
    main()
