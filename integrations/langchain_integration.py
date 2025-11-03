"""LangChain Integration for Workshop MCP Server.

This module provides LangChain tools and agents for interacting with Workshop MCP Server.
Works with any LLM supported by LangChain (GPT-4, Claude, Gemini, etc.)
"""

import os
import json
import requests
from typing import Dict, Any, Optional, Type
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.agents import initialize_agent, AgentType
from langchain_core.pydantic_v1 import BaseModel, Field


# ==================== Pydantic Models for Tool Inputs ====================

class CodeReviewInput(BaseModel):
    """Input for code review tool."""
    code: str = Field(description="Code to review")
    language: str = Field(default="python", description="Programming language")


class ClusterDebugInput(BaseModel):
    """Input for cluster debug tool."""
    issue_description: str = Field(description="Description of the cluster issue")
    namespace: Optional[str] = Field(None, description="Target namespace")
    component: Optional[str] = Field(None, description="Component name")


class GenerateTestInput(BaseModel):
    """Input for test generation tool."""
    feature: str = Field(description="Feature to test")
    component: str = Field(description="Component name")
    scenario: str = Field(description="Test scenario")
    test_format: str = Field(default="shell", description="Test format (gherkin, yaml, go, shell)")


class ExecuteTestInput(BaseModel):
    """Input for test execution tool."""
    feature: str = Field(description="Feature being tested")
    component: str = Field(description="Component under test")
    scenario: str = Field(description="Test scenario")
    namespace: Optional[str] = Field(None, description="Target namespace")


class MustGatherInput(BaseModel):
    """Input for must-gather analysis tool."""
    bundle_path: str = Field(description="Path to must-gather bundle directory")


# ==================== LangChain Tools ====================

class CodeReviewTool(BaseTool):
    """Tool for reviewing code."""

    name = "code_review"
    description = """
    Reviews code for security vulnerabilities, bugs, performance issues, and best practices.
    Supports multiple programming languages including Python, Go, Java, JavaScript, etc.
    Returns detailed analysis with line-by-line recommendations.
    """
    args_schema: Type[BaseModel] = CodeReviewInput
    mcp_base_url: str = "http://127.0.0.1:8080"

    def _run(
        self,
        code: str,
        language: str = "python",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute code review."""
        try:
            response = requests.post(
                f"{self.mcp_base_url}/api/review-code",
                json={
                    "code": code,
                    "language": language,
                    "review_focus": ["security", "bugs", "performance", "best-practices"]
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()

            # Format result for LLM
            if result.get('status') == 'success':
                summary = f"Code Review Results:\n"
                summary += f"Total Issues: {result.get('issues_found', 0)}\n"
                summary += f"Summary: {result.get('summary', 'N/A')}\n\n"

                if result.get('issues'):
                    summary += "Issues Found:\n"
                    for issue in result['issues'][:10]:  # Top 10
                        summary += f"  Line {issue.get('line_number', 'N/A')}: "
                        summary += f"[{issue.get('severity', 'info').upper()}] "
                        summary += f"{issue.get('issue', 'Unknown issue')}\n"
                        summary += f"    Recommendation: {issue.get('recommendation', 'N/A')}\n"

                return summary
            else:
                return f"Error: {result.get('error', 'Unknown error')}"

        except Exception as e:
            return f"Error calling code review API: {str(e)}"


class ClusterDebugTool(BaseTool):
    """Tool for debugging OpenShift cluster issues."""

    name = "cluster_debugger"
    description = """
    Debugs OpenShift/Kubernetes cluster issues with AI-powered diagnostics.
    Analyzes cluster components, logs, events, and provides fix recommendations.
    Use this when users report cluster problems like pods crashing, API server issues, etc.
    """
    args_schema: Type[BaseModel] = ClusterDebugInput
    mcp_base_url: str = "http://127.0.0.1:8080"

    def _run(
        self,
        issue_description: str,
        namespace: Optional[str] = None,
        component: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute cluster debugging."""
        try:
            response = requests.post(
                f"{self.mcp_base_url}/api/debug-cluster",
                json={
                    "issue_description": issue_description,
                    "namespace": namespace,
                    "component": component,
                    "include_test_case": False
                },
                timeout=300
            )
            response.raise_for_status()
            result = response.json()

            # Format result
            if result.get('status') == 'success':
                summary = f"Cluster Diagnostic Results:\n\n"
                summary += f"Issue Type: {result.get('issue_analysis', {}).get('issue_type', 'unknown')}\n"
                summary += f"Severity: {result.get('issue_analysis', {}).get('severity', 'unknown')}\n\n"

                diagnostics = result.get('diagnostics', {})
                summary += f"Summary:\n{diagnostics.get('summary', 'No summary available')}\n\n"

                fix_recs = result.get('fix_recommendations', [])
                if fix_recs:
                    summary += "Fix Recommendations:\n"
                    for i, rec in enumerate(fix_recs[:5], 1):
                        summary += f"  {i}. {rec}\n"

                return summary
            else:
                return f"Error: {result.get('error', 'Unknown error')}"

        except Exception as e:
            return f"Error calling cluster debugger API: {str(e)}"


class GenerateOCPTestTool(BaseTool):
    """Tool for generating OpenShift test cases."""

    name = "generate_ocp_test"
    description = """
    Generates OpenShift test cases in various formats (Gherkin, YAML, Go, Shell).
    Use this when users need to create automated tests for OpenShift components.
    Supports testing pods, operators, nodes, networking, storage, etc.
    """
    args_schema: Type[BaseModel] = GenerateTestInput
    mcp_base_url: str = "http://127.0.0.1:8080"

    def _run(
        self,
        feature: str,
        component: str,
        scenario: str,
        test_format: str = "shell",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Generate test case."""
        try:
            response = requests.post(
                f"{self.mcp_base_url}/api/generate-ocp-test",
                json={
                    "feature": feature,
                    "component": component,
                    "scenario": scenario,
                    "format": test_format
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()

            if result.get('status') == 'success':
                return f"Generated {test_format} test:\n\n{result.get('test_case', 'No test case generated')}"
            else:
                return f"Error: {result.get('error', 'Unknown error')}"

        except Exception as e:
            return f"Error calling test generation API: {str(e)}"


class ExecuteOCPTestTool(BaseTool):
    """Tool for executing OpenShift tests."""

    name = "execute_ocp_test"
    description = """
    Executes OpenShift tests step by step with real-time progress.
    Use this to run automated tests against an OpenShift cluster.
    Returns detailed execution results for each step.
    """
    args_schema: Type[BaseModel] = ExecuteTestInput
    mcp_base_url: str = "http://127.0.0.1:8080"

    def _run(
        self,
        feature: str,
        component: str,
        scenario: str,
        namespace: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute test."""
        try:
            response = requests.post(
                f"{self.mcp_base_url}/api/execute-ocp-test",
                json={
                    "feature": feature,
                    "component": component,
                    "scenario": scenario,
                    "namespace": namespace
                },
                timeout=300
            )
            response.raise_for_status()
            result = response.json()

            if result.get('status') == 'success':
                summary = f"Test Execution Results:\n\n"
                summary += f"Total Steps: {result.get('total_steps', 0)}\n"
                summary += f"Passed: {result.get('passed_steps', 0)}\n"
                summary += f"Failed: {result.get('failed_steps', 0)}\n\n"

                steps = result.get('steps', [])
                if steps:
                    summary += "Step Details:\n"
                    for step in steps:
                        status_icon = "✅" if step.get('status') == 'passed' else "❌"
                        summary += f"  {status_icon} Step {step.get('step_number', 0)}: {step.get('description', 'N/A')}\n"

                return summary
            else:
                return f"Error: {result.get('error', 'Unknown error')}"

        except Exception as e:
            return f"Error calling test execution API: {str(e)}"


class MustGatherAnalysisTool(BaseTool):
    """Tool for analyzing must-gather bundles."""

    name = "analyze_mustgather"
    description = """
    Analyzes OpenShift must-gather bundles for cluster issues.
    Provides AI-powered cluster health assessment, anomaly detection, and SRE reports.
    Use this when analyzing diagnostic data from OpenShift clusters.
    """
    args_schema: Type[BaseModel] = MustGatherInput
    mcp_base_url: str = "http://127.0.0.1:8080"

    def _run(
        self,
        bundle_path: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Analyze must-gather bundle."""
        try:
            response = requests.post(
                f"{self.mcp_base_url}/api/analyze-mustgather",
                json={
                    "bundle_path": bundle_path,
                    "detailed_analysis": True
                },
                timeout=600
            )
            response.raise_for_status()
            result = response.json()

            if result.get('status') == 'success':
                cluster_health = result.get('cluster_health', {})
                sre_report = result.get('sre_diagnostic_report', {})

                summary = f"Must-Gather Analysis:\n\n"
                summary += f"Cluster Status: {cluster_health.get('status', 'unknown')}\n"
                summary += f"Critical Issues: {cluster_health.get('critical_issues', 0)}\n"
                summary += f"Warnings: {cluster_health.get('warnings', 0)}\n\n"
                summary += f"Primary Issue: {sre_report.get('primary_issue', 'N/A')}\n"
                summary += f"Root Cause: {sre_report.get('root_cause_summary', 'N/A')}\n\n"

                actions = sre_report.get('immediate_actions', [])
                if actions:
                    summary += "Immediate Actions:\n"
                    for i, action in enumerate(actions[:5], 1):
                        summary += f"  {i}. {action}\n"

                return summary
            else:
                return f"Error: {result.get('error', 'Unknown error')}"

        except Exception as e:
            return f"Error calling must-gather analysis API: {str(e)}"


# ==================== Agent Creation ====================

def create_mcp_agent(llm, mcp_base_url: str = "http://127.0.0.1:8080"):
    """Create a LangChain agent with MCP Server tools.

    Args:
        llm: LangChain LLM instance (GPT-4, Claude, Gemini, etc.)
        mcp_base_url: Base URL of MCP Server

    Returns:
        Initialized LangChain agent
    """
    tools = [
        CodeReviewTool(mcp_base_url=mcp_base_url),
        ClusterDebugTool(mcp_base_url=mcp_base_url),
        GenerateOCPTestTool(mcp_base_url=mcp_base_url),
        ExecuteOCPTestTool(mcp_base_url=mcp_base_url),
        MustGatherAnalysisTool(mcp_base_url=mcp_base_url),
    ]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
        max_iterations=5,
        early_stopping_method="generate"
    )

    return agent


# ==================== Example Usage ====================

def main():
    """Example usage with different LLMs."""

    print("=" * 70)
    print("LangChain Integration Examples")
    print("=" * 70)

    # Example 1: Using with GPT-4
    print("\nExample 1: GPT-4 + LangChain + MCP Server")
    print("-" * 70)

    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
        agent = create_mcp_agent(llm)

        response = agent.run(
            "Review this Python code for security issues: "
            "def login(user, pwd): "
            "query = f'SELECT * FROM users WHERE username={user} AND password={pwd}'; "
            "return db.execute(query)"
        )

        print(f"Agent Response:\n{response}")

    except ImportError:
        print("Install langchain-openai: pip install langchain-openai")

    # Example 2: Using with Gemini
    print("\n\nExample 2: Gemini + LangChain + MCP Server")
    print("-" * 70)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
        agent = create_mcp_agent(llm)

        response = agent.run(
            "My OpenShift API server pods are crashing. Can you help debug this issue?"
        )

        print(f"Agent Response:\n{response}")

    except ImportError:
        print("Install langchain-google-genai: pip install langchain-google-genai")

    # Example 3: Using with Anthropic Claude
    print("\n\nExample 3: Claude + LangChain + MCP Server")
    print("-" * 70)

    try:
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0)
        agent = create_mcp_agent(llm)

        response = agent.run(
            "Generate a shell test to verify nginx pod is running in test namespace, then execute it"
        )

        print(f"Agent Response:\n{response}")

    except ImportError:
        print("Install langchain-anthropic: pip install langchain-anthropic")


if __name__ == "__main__":
    main()
