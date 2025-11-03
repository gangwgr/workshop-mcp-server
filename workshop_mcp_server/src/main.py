#!/usr/bin/env python3
"""
Polarion QA Assistant MCP Server

An AI-powered MCP server that helps QE, SRE, and Developers search, retrieve, 
and summarize test cases from Polarion ALM.
"""

import asyncio
import logging
from typing import Any

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server
app = FastMCP("Polarion QA Assistant")

# Import and register Polarion tools
try:
    from workshop_mcp_server.src.tools.polarion_search_tool import (
        search_test_cases,
        get_test_case_details, 
        query_polarion_api
    )
    
    # Register tools with the app
    app.tool(search_test_cases)
    app.tool(get_test_case_details)
    app.tool(query_polarion_api)
    
    logger.info("✅ Polarion tools loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load Polarion tools: {e}")

# Import and register Jira Manager tools
try:
    from workshop_mcp_server.src.tools.jira_manager_tool import (
        test_jira_connection,
        get_jira_projects,
        fetch_all_jira_issues,
        get_issue,
        search_issues,
        get_high_priority_bugs,
        get_team_issues,
        generate_test_cases_from_jira,
        generate_test_plan_from_jira
    )
    
    # Register Jira tools with the app
    app.tool(test_jira_connection)
    app.tool(get_jira_projects)
    app.tool(fetch_all_jira_issues)
    app.tool(get_issue)
    app.tool(search_issues)
    app.tool(get_high_priority_bugs)
    app.tool(get_team_issues)
    app.tool(generate_test_cases_from_jira)
    app.tool(generate_test_plan_from_jira)
    
    logger.info("✅ Jira Manager tools loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load Jira Manager tools: {e}")

# Import and register Code Review tools
try:
    from workshop_mcp_server.src.tools.line_by_line_code_reviewer_tool import review_code_line_by_line
    app.tool(review_code_line_by_line)
    logger.info("✅ Code reviewer tool registered")
except Exception as e:
    logger.warning(f"⚠️  Code reviewer tool not available: {e}")

try:
    from workshop_mcp_server.src.tools.github_pr_commenter_tool import post_pr_review_comments
    app.tool(post_pr_review_comments)
    logger.info("✅ GitHub PR commenter tool registered")
except Exception as e:
    logger.warning(f"⚠️  GitHub PR commenter tool not available: {e}")

# Import and register OpenShift testing tools
try:
    from workshop_mcp_server.src.tools.ocp_test_case_generator_tool import generate_ocp_test_case
    from workshop_mcp_server.src.tools.ocp_oc_cli_test_generator_tool import generate_oc_cli_test
    from workshop_mcp_server.src.tools.ocp_step_by_step_executor_tool import execute_ocp_test_step_by_step
    from workshop_mcp_server.src.tools.ocp_test_debugger_tool import debug_ocp_test_failure
    from workshop_mcp_server.src.tools.ocp_test_validator_tool import validate_ocp_test_input
    app.tool(generate_ocp_test_case)
    app.tool(generate_oc_cli_test)
    app.tool(execute_ocp_test_step_by_step)
    app.tool(debug_ocp_test_failure)
    app.tool(validate_ocp_test_input)
    logger.info("✅ OpenShift test tools registered")
except Exception as e:
    logger.warning(f"⚠️  OpenShift test tools not available: {e}")

# Import and register Must-Gather analyzer
try:
    from workshop_mcp_server.src.tools.mustgather_analyzer_tool import analyze_mustgather_bundle
    app.tool(analyze_mustgather_bundle)
    logger.info("✅ Must-Gather analyzer tool registered")
except Exception as e:
    logger.warning(f"⚠️  Must-Gather analyzer tool not available: {e}")

# Import and register Cluster Debugger
try:
    from workshop_mcp_server.src.tools.ocp_cluster_debugger_agent_tool import debug_openshift_cluster
    app.tool(debug_openshift_cluster)
    logger.info("✅ Cluster debugger tool registered")
except Exception as e:
    logger.warning(f"⚠️  Cluster debugger tool not available: {e}")

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
        """Switch the LLM backend between ollama (local), claude (API), or template (rules).

        Args:
            mode: Backend to use - 'ollama', 'claude', or 'template'
            model: Optional model name (e.g. 'llama3:latest', 'mistral:latest', 'claude-sonnet-4-20250514')

        Returns:
            Dictionary with updated configuration
        """
        if mode not in ("ollama", "claude", "template"):
            return {"status": "error", "error": "mode must be 'ollama', 'claude', or 'template'"}
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
        logger.info("Starting Polarion QA Assistant MCP Server...")
        logger.info("Available tools:")
        logger.info("  🔍 Polarion Test Case Search")
        logger.info("  📋 Test Case Details Retrieval") 
        logger.info("  🔧 Code Review & PR Analysis")
        logger.info("  🧪 OpenShift Test Generation & Execution")
        logger.info("  🔍 Must-Gather Analysis")
        logger.info("  🚨 Cluster Debugging")
        
        # Run the server
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()