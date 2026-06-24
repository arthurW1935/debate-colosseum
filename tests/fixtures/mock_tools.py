from langchain_core.tools import tool

@tool
def web_search(query: str) -> list[dict]:
    """Search the web for current market/risk data.
    
    Args:
        query: The search query string.
    """
    return [{"title": "Mock Search Result", "url": "http://example.com", "snippet": f"Mock snippet for {query}"}]

@tool
def doc_retrieval(query: str) -> list[str]:
    """Retrieve top context chunks.
    
    Args:
        query: The search query string.
    """
    return [f"Mock document content matching {query}"]
