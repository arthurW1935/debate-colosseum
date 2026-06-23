import os
import PyPDF2
import chromadb
from chromadb.utils import embedding_functions
from src.schemas import GraphState

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitters import RecursiveCharacterTextSplitter

def extract_text(file_path: str, file_type: str) -> str:
    """Extracts raw text from a PDF, txt, or md file.
    
    Raises:
        ValueError: If file_type is unsupported.
        FileNotFoundError: If the file does not exist.
        RuntimeError: If text extraction fails due to formatting/corruption.
    """
    normalized_type = file_type.lower().strip(".")
    if normalized_type not in ("pdf", "txt", "md"):
        raise ValueError(f"Unsupported file type: {file_type}")
        
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if normalized_type == "pdf":
        try:
            pages_text = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                    else:
                        # Append an empty string if page text cannot be extracted
                        pages_text.append("")
            # Join with double newlines so page breaks are clean
            return "\n\n".join(pages_text)
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF '{file_path}': {e}") from e
            
    elif normalized_type in ("txt", "md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read text file '{file_path}': {e}") from e
            
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def chunk_text(text: str, source: str) -> list[dict]:
    """Splits a body of text into overlapping chunks of 600 tokens (approximated via characters/words) with 80 tokens overlap.
    
    Returns a list of dicts: {"text": chunk, "source": source, "chunk_index": idx}
    """
    # 1 token is roughly 4 characters or ~0.75 words.
    # To split by characters, we configure chunk_size/overlap directly on character splitter.
    # Standard approximation: 600 tokens ~ 2400 characters, 80 tokens ~ 320 characters.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        length_function=len
    )
    chunks = splitter.split_text(text)
    return [{"text": c, "source": source, "chunk_index": i} for i, c in enumerate(chunks)]

def build_vector_store(chunks: list[dict]):
    """Builds a fresh, in-memory Chroma collection for the document chunks.
    
    Uses sentence-transformers/all-MiniLM-L6-v2 locally for embeddings.
    """
    import uuid
    # Use EphemeralClient for in-memory, session-scoped Chroma
    client = chromadb.EphemeralClient()
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # We use a unique collection name per run to prevent collection clash in parallel/repeated tests
    collection_name = f"run_{uuid.uuid4().hex}"
    collection = client.get_or_create_collection(name=collection_name, embedding_function=ef)
    
    if chunks:
        documents = [c["text"] for c in chunks]
        metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]
        ids = [f"{c['source']}_{c['chunk_index']}" for c in chunks]
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    return collection

def ingest_context(state: GraphState) -> GraphState:
    """LangGraph node function to extract and index context documents.
    
    Updates GraphState by populating the 'retriever' attribute.
    """
    # Verify INSTRUCTIONS.md: don't mutate state in-place, use state.model_copy()
    new_state = state.model_copy()
    
    if not state.context_docs:
        new_state.retriever = None
        return new_state

    all_chunks = []
    for doc_path in state.context_docs:
        file_type = doc_path.split(".")[-1]
        try:
            text = extract_text(doc_path, file_type)
            all_chunks.extend(chunk_text(text, source=doc_path))
        except Exception as e:
            # Re-raise the exception per instructions: tools raise, don't silently ignore
            raise RuntimeError(f"Error ingesting document '{doc_path}': {e}") from e

    vector_store = build_vector_store(all_chunks)
    new_state.retriever = vector_store
    return new_state
