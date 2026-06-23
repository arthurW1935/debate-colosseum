import os
import time
import requests

def web_search(query: str) -> list[dict]:
    """Search Tavily for the given query and return at most 5 results.
    
    Output format: list of dicts with keys {"title", "url", "snippet"}.
    Raises:
        ValueError: If TAVILY_API_KEY environment variable is not set.
        RuntimeError: If the search API request fails after retries.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set")
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 5
    }
    
    # Retry once on HTTP 429 or transient error
    for attempt in range(2):
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 429:
                if attempt == 0:
                    time.sleep(2)
                    continue
                else:
                    response.raise_for_status()
                    
            response.raise_for_status()
            data = response.json()
            
            # Map results to expected output schema: title, url, snippet
            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")
                })
            return results[:5]
            
        except Exception as e:
            if attempt == 1:
                raise RuntimeError(f"web_search failed for query '{query}': {e}") from e
            time.sleep(2)
            
    # Fallback return in case flow falls through (should not happen due to raises)
    raise RuntimeError(f"web_search failed for query '{query}': Unknown error")
