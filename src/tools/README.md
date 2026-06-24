# Shared Tools Integration Contracts

This document specifies the exact API contracts and usage instructions for the shared tools in Track A: `doc_retrieval` and `web_search`. These tools are designed to be consumed by the expert agents (Growth, Finance, Risk) in Track B.

---

## 1. Document Retrieval Tool

**File:** `src/tools/doc_retrieval.py`  
**Import:** `from src.tools.doc_retrieval import doc_retrieval`

### Signature
```python
def doc_retrieval(query: str, retriever: Any) -> list[str]
```

### Description
Fetches candidate context chunks from the ephemeral in-memory Chroma database built during ingestion, then reranks them using a local Cross-Encoder model.

- **Phase 1:** Retrieves top 8 chunks using cosine similarity.
- **Phase 2:** Reranks the candidates against the query using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **Phase 3:** Returns the top 4 reranked chunks.

### Behavior & Fallbacks
- **No Documents Uploaded:** If `retriever` is `None`, the tool **falls back gracefully** and returns `[]`. It will **not** raise an error or crash.
- **Empty Retrieval:** If no documents match the query, it returns `[]`.
- **Errors:** If internal queries or reranking fail, a descriptive `RuntimeError` is raised.

### Return Format
A list of strings. Each string is prefixed with its source metadata:
```python
[
    "[Source: d:/data/q1_report.pdf] Operating margin grew by 12% quarter-on-quarter...",
    "[Source: d:/data/growth_strategy.md] Expanding into the EU market will target 40M new customers..."
]
```

### Usage Example
```python
from src.tools.doc_retrieval import doc_retrieval

# Inside an agent node (e.g., finance agent)
retriever = state.retriever  # GraphState.retriever
query = f"financial projections cost structure {state.problem_statement}"

chunks = doc_retrieval(query, retriever)
if chunks:
    context_str = "\n".join(chunks)
    # Inject context_str into agent system/user prompt
else:
    # Skip retrieval logic, proceed using default LLM knowledge
```

---

## 2. Web Search Tool

**File:** `src/tools/web_search.py`  
**Import:** `from src.tools.web_search import web_search`

### Signature
```python
def web_search(query: str) -> list[dict]
```

### Description
Performs external web searches using the Tavily Search API. Returns a clean list of external web page results containing the title, URL, and page snippet.

### Behavior & Fallbacks
- **Rate-Limiting (HTTP 429):** If rate-limited, the tool will **automatically retry once** after a 2-second sleep.
- **Errors:** If the search fails or the API key is missing, it raises a descriptive `ValueError` or `RuntimeError`. The calling agent should decide how to handle this failure (e.g. fallback to no search).
- **Result Limit:** Always returns a maximum of **top 5** results.

### Return Format
A list of dicts matching the following structure:
```python
[
    {
        "title": "EU Market Expansion Risks & Frameworks",
        "url": "https://example-strategy.com/eu-expansion",
        "snippet": "Analysis of the legal and operational risks of expanding corporate structures into the EU..."
    },
    ...
]
```

### Usage Example
```python
from src.tools.web_search import web_search

# Inside an agent node (e.g., risk agent)
try:
    search_results = web_search("competitor pricing strategy 2026")
    for result in search_results:
        # Process and format search results for model context
        print(result["title"], result["url"])
except Exception as e:
    # Handle search failure gracefully
    search_results = []
```
