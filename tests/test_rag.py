import os
import pytest
from unittest.mock import MagicMock, patch
from src.rag.ingest import extract_text, chunk_text, build_vector_store
from src.tools.doc_retrieval import doc_retrieval

# Minimal valid PDF content for testing extraction
MINIMAL_PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << >> /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
72 712 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000056 00000 n 
0000000111 00000 n 
0000000212 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
306
%%EOF"""

def test_extract_text_txt(tmp_path):
    # Test reading from plain txt
    txt_file = tmp_path / "test.txt"
    content = "Hello, this is a plain text file content for testing RAG ingestion."
    txt_file.write_text(content, encoding="utf-8")
    
    extracted = extract_text(str(txt_file), "txt")
    assert extracted == content

def test_extract_text_md(tmp_path):
    # Test reading from markdown
    md_file = tmp_path / "test.md"
    content = "# Markdown Header\nThis is a markdown content."
    md_file.write_text(content, encoding="utf-8")
    
    extracted = extract_text(str(md_file), "md")
    assert extracted == content

def test_extract_text_pdf(tmp_path):
    # Test reading from PDF
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(MINIMAL_PDF_BYTES)
    
    extracted = extract_text(str(pdf_file), "pdf")
    # Assert output is string and does not crash
    assert isinstance(extracted, str)

def test_extract_text_unsupported():
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text("dummy.png", "png")

def test_extract_text_missing():
    with pytest.raises(FileNotFoundError):
        extract_text("nonexistent_file_path.txt", "txt")

def test_extract_text_corrupt_pdf(tmp_path):
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"invalid pdf header and dummy content")
    with pytest.raises(RuntimeError):
        extract_text(str(corrupt_pdf), "pdf")

def test_chunk_text():
    text = "This is a word. " * 100  # Creates a text of 400 words
    chunks = chunk_text(text, source="doc.txt")
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["source"] == "doc.txt"
        assert "text" in chunk
        assert "chunk_index" in chunk
    assert chunks[0]["chunk_index"] == 0

def test_build_vector_store():
    chunks = [
        {"text": "Apple is a fruit.", "source": "apples.txt", "chunk_index": 0},
        {"text": "Microsoft makes software.", "source": "msft.txt", "chunk_index": 0},
    ]
    collection = build_vector_store(chunks)
    assert collection is not None
    
    # Query Chroma
    results = collection.query(query_texts=["fruit"], n_results=1)
    assert len(results["documents"][0]) == 1
    assert "Apple" in results["documents"][0][0]
    assert results["metadatas"][0][0]["source"] == "apples.txt"

@patch("src.tools.doc_retrieval.get_reranker")
def test_doc_retrieval_with_rerank(mock_get_reranker):
    # Mock cross-encoder predict to return static scores: [0.9, 0.1]
    mock_encoder = MagicMock()
    mock_encoder.predict.return_value = [0.1, 0.9]
    mock_get_reranker.return_value = mock_encoder
    
    # Setup collection
    chunks = [
        {"text": "Apple is a fruit.", "source": "apples.txt", "chunk_index": 0},
        {"text": "Banana is also a fruit.", "source": "bananas.txt", "chunk_index": 0},
    ]
    # Cosine query will get candidates. We mock reranking scores so that
    # the second candidate gets scored 0.9, while the first gets 0.1.
    # Therefore, the second candidate (Banana) should rank first.
    results = doc_retrieval("Which fruit is yellow?", chunks)
    
    assert len(results) == 2
    # banana should rank first because its mock rerank score is 0.9
    assert "[Source: bananas.txt]" in results[0]
    assert "[Source: apples.txt]" in results[1]

def test_doc_retrieval_fallback():
    # Graceful fallback: return empty list if retriever is None
    assert doc_retrieval("search query", None) == []
