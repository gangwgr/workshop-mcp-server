"""Document Ingester for RAG system.

Supports ingesting:
- Markdown files (.md)
- Text files (.txt)
- PDF files (.pdf)
- Code files (.go, .py, .yaml, .json, .sh)
- Entire git repos (clones and indexes)
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

import chromadb
from chromadb.config import Settings

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()

VECTOR_STORE_PATH = os.environ.get(
    "RAG_VECTOR_STORE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "vector_store")
)

SUPPORTED_EXTENSIONS = {
    ".md", ".txt", ".rst", ".pdf",
    ".go", ".py", ".yaml", ".yml", ".json", ".sh", ".bash",
    ".js", ".ts", ".java", ".rb", ".html", ".css",
}

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def get_chroma_client() -> chromadb.ClientAPI:
    abs_path = os.path.abspath(VECTOR_STORE_PATH)
    os.makedirs(abs_path, exist_ok=True)
    return chromadb.PersistentClient(
        path=abs_path,
        settings=Settings(anonymized_telemetry=False)
    )


def get_or_create_collection(name: str = "default") -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )


def list_collections() -> List[Dict[str, any]]:
    client = get_chroma_client()
    collections = client.list_collections()
    result = []
    for col in collections:
        count = col.count()
        result.append({"name": col.name, "document_count": count})
    return result


def delete_collection(name: str) -> bool:
    client = get_chroma_client()
    try:
        client.delete_collection(name)
        return True
    except Exception:
        return False


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap

    return chunks


def _read_file(file_path: str) -> Optional[str]:
    """Read a file and return its content."""
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.warning(f"Failed to read PDF {file_path}: {e}")
            return None

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return None


def _compute_doc_id(content: str, source: str) -> str:
    """Generate a deterministic ID for deduplication."""
    return hashlib.md5(f"{source}:{content[:200]}".encode()).hexdigest()


def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed texts using Ollama's nomic-embed-text model."""
    import requests

    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    embeddings = []

    for text in texts:
        try:
            resp = requests.post(
                f"{ollama_url}/api/embed",
                json={"model": "nomic-embed-text", "input": text},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("embeddings", [[]])[0]
            if embedding:
                embeddings.append(embedding)
            else:
                embeddings.append([0.0] * 768)
        except Exception as e:
            logger.warning(f"Embedding failed: {e}")
            embeddings.append([0.0] * 768)

    return embeddings


def index_folder(
    folder_path: str,
    collection_name: str = "default",
    file_extensions: Optional[List[str]] = None,
) -> Dict[str, any]:
    """Index all supported files in a folder into ChromaDB.

    Args:
        folder_path: Path to folder containing documents
        collection_name: ChromaDB collection name
        file_extensions: Optional list of extensions to include (e.g. ['.md', '.go'])

    Returns:
        Dictionary with indexing stats
    """
    folder = Path(folder_path)
    if not folder.exists():
        return {"status": "error", "error": f"Folder not found: {folder_path}"}

    allowed_ext = set(file_extensions) if file_extensions else SUPPORTED_EXTENSIONS
    collection = get_or_create_collection(collection_name)

    stats = {"files_processed": 0, "chunks_indexed": 0, "errors": 0, "skipped": 0}
    all_chunks = []
    all_ids = []
    all_metadatas = []

    for root, dirs, files in os.walk(folder):
        # Skip hidden dirs and common noise
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in (
            "node_modules", "vendor", "__pycache__", ".git", "venv", ".venv"
        )]

        for fname in files:
            fpath = os.path.join(root, fname)
            ext = Path(fname).suffix.lower()

            if ext not in allowed_ext:
                stats["skipped"] += 1
                continue

            content = _read_file(fpath)
            if not content or len(content.strip()) < 20:
                stats["skipped"] += 1
                continue

            rel_path = os.path.relpath(fpath, folder_path)
            chunks = _chunk_text(content)

            for i, chunk in enumerate(chunks):
                doc_id = _compute_doc_id(chunk, f"{rel_path}:{i}")
                all_chunks.append(chunk)
                all_ids.append(doc_id)
                all_metadatas.append({
                    "source": rel_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "collection": collection_name,
                })

            stats["files_processed"] += 1
            stats["chunks_indexed"] += len(chunks)

    if not all_chunks:
        return {"status": "success", "message": "No documents found to index", **stats}

    # Embed and store in batches
    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i + batch_size]
        batch_ids = all_ids[i:i + batch_size]
        batch_meta = all_metadatas[i:i + batch_size]

        try:
            embeddings = _embed_texts(batch_chunks)
            collection.upsert(
                ids=batch_ids,
                documents=batch_chunks,
                embeddings=embeddings,
                metadatas=batch_meta,
            )
        except Exception as e:
            logger.error(f"Batch indexing error: {e}")
            stats["errors"] += 1

    logger.info(f"Indexed {stats['files_processed']} files, {stats['chunks_indexed']} chunks into '{collection_name}'")
    return {"status": "success", "collection": collection_name, **stats}


def index_web_url(
    url: str,
    collection_name: str = "default",
    crawl: bool = False,
    max_pages: int = 20,
) -> Dict[str, any]:
    """Fetch a web page (or crawl linked pages) and index the text content.

    Args:
        url: Web URL to fetch (e.g., docs page)
        collection_name: ChromaDB collection name
        crawl: Whether to follow links on the same domain
        max_pages: Max pages to crawl if crawl=True

    Returns:
        Dictionary with indexing stats
    """
    import requests
    from urllib.parse import urljoin, urlparse

    def _extract_text(html: str) -> str:
        """Strip HTML tags to get plain text."""
        import re
        text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html)
        text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_links(html: str, base_url: str, domain: str) -> List[str]:
        """Extract same-domain links."""
        import re
        links = set()
        for href in re.findall(r'href=["\']([^"\']+)["\']', html):
            full = urljoin(base_url, href)
            if urlparse(full).netloc == domain and full.endswith(('.html', '/')):
                links.add(full.split('#')[0])
        return list(links)[:max_pages]

    collection = get_or_create_collection(collection_name)
    domain = urlparse(url).netloc
    visited = set()
    to_visit = [url]
    all_chunks = []
    all_ids = []
    all_metadatas = []
    pages_indexed = 0

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            resp = requests.get(current_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.warning(f"Failed to fetch {current_url}: {e}")
            continue

        text = _extract_text(html)
        if len(text) < 50:
            continue

        if crawl:
            new_links = _extract_links(html, current_url, domain)
            for link in new_links:
                if link not in visited:
                    to_visit.append(link)

        chunks = _chunk_text(text)
        for i, chunk in enumerate(chunks):
            doc_id = _compute_doc_id(chunk, f"{current_url}:{i}")
            all_chunks.append(chunk)
            all_ids.append(doc_id)
            all_metadatas.append({
                "source": current_url,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "collection": collection_name,
            })
        pages_indexed += 1

    if not all_chunks:
        return {"status": "error", "error": "No content could be extracted from the URL"}

    batch_size = 50
    errors = 0
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i + batch_size]
        batch_ids = all_ids[i:i + batch_size]
        batch_meta = all_metadatas[i:i + batch_size]
        try:
            embeddings = _embed_texts(batch_chunks)
            collection.upsert(
                ids=batch_ids,
                documents=batch_chunks,
                embeddings=embeddings,
                metadatas=batch_meta,
            )
        except Exception as e:
            logger.error(f"Batch indexing error: {e}")
            errors += 1

    return {
        "status": "success",
        "collection": collection_name,
        "pages_indexed": pages_indexed,
        "chunks_indexed": len(all_chunks),
        "urls_visited": list(visited),
        "errors": errors,
    }


def index_git_repo(
    repo_url: str,
    collection_name: str = "default",
    branch: str = "main",
    file_extensions: Optional[List[str]] = None,
) -> Dict[str, any]:
    """Clone a git repo and index its contents.

    Args:
        repo_url: Git repository URL (https or ssh)
        collection_name: ChromaDB collection name
        branch: Branch to clone
        file_extensions: Optional extensions filter

    Returns:
        Dictionary with indexing stats
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        clone_path = os.path.join(tmpdir, "repo")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", branch, repo_url, clone_path],
                capture_output=True, text=True, timeout=120,
            )
        except Exception as e:
            return {"status": "error", "error": f"Git clone failed: {e}"}

        if not os.path.exists(clone_path):
            return {"status": "error", "error": "Clone produced no output"}

        result = index_folder(clone_path, collection_name, file_extensions)
        result["source_repo"] = repo_url
        result["branch"] = branch
        return result


# ============================================================
# Review Feedback Learning
# ============================================================

FEEDBACK_COLLECTION = "review_feedback"


def store_review_feedback(
    issue_description: str,
    author_explanation: str,
    category: str = "general",
    file_context: str = "",
    pr_url: str = "",
) -> Dict[str, any]:
    """Store accepted review feedback for future learning.

    When a PR author's explanation is accepted, store it so the reviewer
    avoids flagging the same pattern in future reviews.
    """
    try:
        collection = get_or_create_collection(FEEDBACK_COLLECTION)

        doc_id = hashlib.md5(
            f"{issue_description}:{author_explanation}".encode()
        ).hexdigest()

        document = (
            f"REVIEW FEEDBACK — Category: {category}\n"
            f"Issue flagged: {issue_description}\n"
            f"Author explanation (ACCEPTED): {author_explanation}\n"
            f"Context: {file_context}\n"
            f"Lesson: Do NOT flag this pattern in future reviews. "
            f"The author's justification is valid."
        )

        embeddings = _embed_texts([document])

        collection.upsert(
            ids=[doc_id],
            documents=[document],
            embeddings=embeddings,
            metadatas=[{
                "type": "review_feedback",
                "category": category,
                "pr_url": pr_url,
                "source": "pr_author_reply",
            }]
        )

        return {"status": "success", "doc_id": doc_id}
    except Exception as e:
        logger.warning(f"Failed to store review feedback: {e}")
        return {"status": "error", "error": str(e)}


def get_review_feedback(query: str, top_k: int = 3) -> str:
    """Retrieve relevant past feedback to avoid repeating false positives."""
    try:
        collection = get_or_create_collection(FEEDBACK_COLLECTION)
        if collection.count() == 0:
            return ""

        embeddings = _embed_texts([query])
        results = collection.query(
            query_embeddings=embeddings,
            n_results=min(top_k, collection.count()),
        )

        if results and results.get("documents") and results["documents"][0]:
            feedback_items = results["documents"][0]
            return "\n\n---\n".join(feedback_items)
        return ""
    except Exception:
        return ""
