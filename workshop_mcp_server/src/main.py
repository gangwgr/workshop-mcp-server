#!/usr/bin/env python3
"""
Workshop MCP Server

An AI-powered MCP server for development assistance with code review, 
GitHub PR automation, OpenShift test generation & execution, 
must-gather analysis, and cluster debugging capabilities.
"""

import logging
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server
app = FastMCP("Workshop MCP Server")

# Import and register OpenShift testing tools
try:
    from workshop_mcp_server.src.tools.ocp_cluster_debugger_agent_tool import debug_openshift_cluster
    app.tool(debug_openshift_cluster)
    logger.info("✅ OpenShift Cluster Debugger tool registered")
except Exception as e:
    logger.warning(f"⚠️  OpenShift Cluster Debugger tool not available: {e}")

# Import and register Must-Gather analyzer
try:
    from workshop_mcp_server.src.tools.mustgather_analyzer_tool import analyze_mustgather_bundle
    app.tool(analyze_mustgather_bundle)
    logger.info("✅ Must-Gather Analyzer tool registered")
except Exception as e:
    logger.warning(f"⚠️  Must-Gather Analyzer tool not available: {e}")

# Register LLM-powered tools (local Ollama / Claude)
try:
    from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config, set_mode, set_model

    @app.tool
    def ask_local_llm(prompt: str, system: str = "", task_type: str = "general") -> dict:
        """Ask the local LLM (Ollama/llama3) or Claude a question directly.

        Use this tool to get AI-powered analysis, code generation, debugging help,
        or any question answered by the configured LLM backend.

        Args:
            prompt: Your question or task description
            system: Optional system prompt to guide the response
            task_type: Type of task - 'general', 'code_review', 'test_gen', 'debug', 'explain'

        Returns:
            Dictionary with the LLM response and model info
        """
        config = get_config()

        if not is_available():
            return {
                "status": "error",
                "error": f"LLM not available. Mode: {config['mode']}, Model: {config['model']}",
                "hint": "Start 'ollama serve' or set ANTHROPIC_API_KEY for Claude mode",
            }

        system_prompts = {
            "general": "You are a helpful AI assistant. Be concise and accurate.",
            "code_review": "You are an expert code reviewer for Go/Python/Kubernetes. Provide structured feedback with severity levels.",
            "test_gen": "You are an expert QA engineer. Generate complete, production-ready test cases.",
            "debug": "You are an expert OpenShift/Kubernetes SRE. Provide root cause analysis and oc commands.",
            "explain": "You are a technical educator. Explain concepts clearly with examples.",
        }

        final_system = system or system_prompts.get(task_type, system_prompts["general"])
        result = generate(prompt, system=final_system)

        if result:
            return {
                "status": "success",
                "response": result,
                "mode": config["mode"],
                "model": config["model"],
            }
        return {
            "status": "error",
            "error": "LLM returned no response",
            "mode": config["mode"],
            "model": config["model"],
        }

    @app.tool
    def switch_llm_mode(mode: str = "ollama", model: str = "") -> dict:
        """Switch the LLM backend between ollama (local), claude (API), cursor (agent), or template (rules).

        Args:
            mode: Backend to use - 'ollama', 'claude', 'cursor', or 'template'
            model: Optional model name (e.g. 'llama3:latest', 'composer-2.5')

        Returns:
            Dictionary with updated configuration
        """
        if mode not in ("ollama", "claude", "cursor", "template"):
            return {"status": "error", "error": "mode must be 'ollama', 'claude', 'cursor', or 'template'"}
        set_mode(mode)
        if model:
            set_model(model)
        config = get_config()
        available = is_available()
        return {
            "status": "success",
            "mode": config["mode"],
            "model": config["model"],
            "available": available,
            "message": f"Switched to {config['mode']} ({config['model']})",
        }

    logger.info("✅ LLM tools registered (ask_local_llm, switch_llm_mode)")
except Exception as e:
    logger.warning(f"⚠️  LLM tools not available: {e}")

# Register RAG (Retrieval-Augmented Generation) tools
try:
    from workshop_mcp_server.src.tools.rag.rag_tool import (
        ask_docs, index_docs, index_repo, index_web, list_knowledge_bases, delete_knowledge_base
    )
    app.tool(ask_docs)
    app.tool(index_docs)
    app.tool(index_repo)
    app.tool(index_web)
    app.tool(list_knowledge_bases)
    app.tool(delete_knowledge_base)
    logger.info("✅ RAG tools registered (ask_docs, index_docs, index_repo, index_web, list/delete_knowledge_bases)")
except Exception as e:
    logger.warning(f"⚠️  RAG tools not available: {e}")


def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting Workshop MCP Server...")
        logger.info("Available tools:")
        logger.info("  🚨 OpenShift Cluster Debugger - Intelligent cluster issue analysis")
        logger.info("  🔍 Must-Gather Analyzer - Cluster health diagnostics")
        logger.info("  💬 Local LLM / Claude - AI-powered analysis")
        logger.info("  📚 RAG (Retrieval-Augmented Generation) - Knowledge base tools")
        
        # Run the server
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()