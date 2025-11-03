"""Knowledge Base Context Helper.

Provides a simple function for all tools to fetch relevant KB context
before making LLM calls. This enriches tool responses with documentation
and internal code knowledge.
"""

import os
from typing import Optional, List

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()

RAG_ENABLED = os.environ.get("RAG_ENABLED", "true").lower() in ("true", "1", "yes")


def get_kb_context(
    query: str,
    collections: Optional[List[str]] = None,
    top_k: int = 3,
    max_chars: int = 2000,
) -> str:
    """Fetch relevant context from the Knowledge Base for any tool.

    This is the single integration point - any tool can call this to get
    RAG-enriched context from indexed docs/code repos.

    Args:
        query: The search query (e.g., issue description, code topic)
        collections: Which collections to search (None = search all)
        top_k: Number of chunks to retrieve per collection
        max_chars: Max total characters to return

    Returns:
        Formatted context string, or empty string if no results/disabled
    """
    if not RAG_ENABLED:
        return ""

    try:
        from workshop_mcp_server.src.tools.rag.doc_ingester import (
            get_chroma_client, _embed_texts
        )

        client = get_chroma_client()
        all_collections = client.list_collections()

        if not all_collections:
            return ""

        if collections:
            target_cols = [c for c in all_collections if c.name in collections]
        else:
            target_cols = all_collections

        if not target_cols:
            return ""

        query_embedding = _embed_texts([query])[0]
        if not query_embedding or all(v == 0.0 for v in query_embedding):
            return ""

        all_results = []

        for col in target_cols:
            if col.count() == 0:
                continue
            try:
                results = col.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, col.count()),
                    include=["documents", "metadatas", "distances"],
                )
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                dists = results.get("distances", [[]])[0]

                for doc, meta, dist in zip(docs, metas, dists):
                    relevance = 1 - dist
                    if relevance > 0.4:
                        all_results.append({
                            "text": doc,
                            "source": meta.get("source", "unknown"),
                            "collection": col.name,
                            "relevance": relevance,
                        })
            except Exception as e:
                logger.debug(f"KB search error in {col.name}: {e}")

        if not all_results:
            return ""

        all_results.sort(key=lambda x: x["relevance"], reverse=True)
        all_results = all_results[:top_k]

        context_parts = ["[Knowledge Base Context]"]
        total_chars = 0
        for r in all_results:
            chunk = f"\n--- [{r['collection']}] {r['source']} (relevance: {r['relevance']:.0%}) ---\n{r['text']}"
            if total_chars + len(chunk) > max_chars:
                break
            context_parts.append(chunk)
            total_chars += len(chunk)

        return "\n".join(context_parts)

    except Exception as e:
        logger.debug(f"KB context fetch failed: {e}")
        return ""
