"""RAG Query Tool - Ask questions against indexed documents.

Uses ChromaDB for retrieval and Ollama/Claude for generation.
Supports internal code repos, OpenShift docs, and custom Q&A pairs.
"""

import os
from typing import Dict, List, Optional

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


def _embed_query(query: str) -> List[float]:
    """Embed a single query using Ollama nomic-embed-text."""
    import requests

    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        resp = requests.post(
            f"{ollama_url}/api/embed",
            json={"model": "nomic-embed-text", "input": query},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("embeddings", [[]])[0]
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        return [0.0] * 768


def _generate_answer(question: str, context: str, sources: List[str]) -> str:
    """Generate answer using the active LLM backend."""
    from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config

    if not is_available():
        return f"LLM not available. Context found:\n\n{context}\n\nSources: {', '.join(sources)}"

    config = get_config()
    system = """You are an expert assistant answering questions based on provided documentation.
Rules:
- ONLY use the provided context to answer. If the context doesn't contain the answer, say so.
- Cite the source file when referencing specific information.
- Be concise and technical.
- Format code examples in markdown code blocks.
- If the context contains code, explain what it does."""

    prompt = f"""Context from indexed documents:
---
{context}
---

Sources: {', '.join(sources)}

Question: {question}

Answer based ONLY on the context above:"""

    result = generate(prompt, system=system)
    if result:
        source_list = "\n".join([f"- {s}" for s in set(sources)])
        return f"{result}\n\n---\n**Sources:**\n{source_list}\n**Model:** {config['model']}"
    return f"Generation failed. Raw context:\n{context}"


def ask_docs(
    question: str,
    collection: str = "default",
    top_k: int = 5,
) -> Dict[str, any]:
    """Ask a question against your indexed documents (RAG).

    Searches the vector store for relevant chunks, then uses the LLM
    to generate an answer grounded in your documentation.

    Args:
        question: Your question about the indexed docs
        collection: Which collection to search (default: 'default')
        top_k: Number of relevant chunks to retrieve (default: 5)

    Returns:
        Dictionary with the answer, sources, and metadata
    """
    from workshop_mcp_server.src.tools.rag.doc_ingester import get_or_create_collection

    try:
        col = get_or_create_collection(collection)
        count = col.count()

        if count == 0:
            return {
                "status": "error",
                "error": f"Collection '{collection}' is empty. Index some documents first.",
                "hint": "Use index_docs() to add documents to the collection.",
            }

        query_embedding = _embed_query(question)

        results = col.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not documents:
            return {
                "status": "success",
                "answer": "No relevant documents found for your question.",
                "sources": [],
            }

        context = "\n\n---\n\n".join([
            f"[Source: {m.get('source', 'unknown')}]\n{doc}"
            for doc, m in zip(documents, metadatas)
        ])

        sources = [m.get("source", "unknown") for m in metadatas]
        relevance_scores = [round(1 - d, 3) for d in distances]

        answer = _generate_answer(question, context, sources)

        return {
            "status": "success",
            "answer": answer,
            "sources": [
                {"file": s, "relevance": r}
                for s, r in zip(sources, relevance_scores)
            ],
            "collection": collection,
            "chunks_retrieved": len(documents),
        }

    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return {"status": "error", "error": str(e)}


def index_docs(
    folder_path: str,
    collection: str = "default",
    include_code: bool = True,
) -> Dict[str, any]:
    """Index documents from a folder into the RAG vector store.

    Supports markdown, text, PDF, and code files (.go, .py, .yaml, .sh, etc.)
    This includes internal code repos - just point it at the repo folder.

    Args:
        folder_path: Path to folder with documents or code
        collection: Collection name for organizing docs (default: 'default')
        include_code: Whether to include code files (.go, .py, etc.)

    Returns:
        Dictionary with indexing statistics
    """
    from workshop_mcp_server.src.tools.rag.doc_ingester import index_folder, SUPPORTED_EXTENSIONS

    extensions = None
    if not include_code:
        extensions = [".md", ".txt", ".rst", ".pdf"]

    return index_folder(folder_path, collection, extensions)


def index_repo(
    repo_url: str,
    collection: str = "default",
    branch: str = "main",
) -> Dict[str, any]:
    """Clone and index a git repository into the RAG vector store.

    Use this to index internal code repos so you can ask questions about them.

    Args:
        repo_url: Git repository URL (e.g. https://github.com/openshift/api)
        collection: Collection name (default: 'default')
        branch: Branch to index (default: 'main')

    Returns:
        Dictionary with indexing statistics
    """
    from workshop_mcp_server.src.tools.rag.doc_ingester import index_git_repo
    return index_git_repo(repo_url, collection, branch)


def index_web(
    url: str,
    collection: str = "default",
    crawl: bool = False,
) -> Dict[str, any]:
    """Fetch and index a documentation web page (or crawl linked pages).

    Use this for indexing online docs like OpenShift, Kubernetes, etc.

    Args:
        url: Web URL (e.g., https://docs.openshift.com/container-platform/4.14/operators/index.html)
        collection: Collection name (default: 'default')
        crawl: If True, also crawls linked pages on same domain (max 20)

    Returns:
        Dictionary with indexing statistics
    """
    from workshop_mcp_server.src.tools.rag.doc_ingester import index_web_url
    return index_web_url(url, collection, crawl)


def list_knowledge_bases() -> Dict[str, any]:
    """List all indexed knowledge base collections.

    Returns:
        Dictionary with all collections and their document counts
    """
    from workshop_mcp_server.src.tools.rag.doc_ingester import list_collections
    collections = list_collections()
    return {
        "status": "success",
        "collections": collections,
        "total_collections": len(collections),
    }


def delete_knowledge_base(collection: str) -> Dict[str, any]:
    """Delete an indexed knowledge base collection.

    Args:
        collection: Name of the collection to delete

    Returns:
        Dictionary with deletion status
    """
    from workshop_mcp_server.src.tools.rag.doc_ingester import delete_collection
    success = delete_collection(collection)
    if success:
        return {"status": "success", "message": f"Deleted collection '{collection}'"}
    return {"status": "error", "error": f"Failed to delete collection '{collection}'"}
