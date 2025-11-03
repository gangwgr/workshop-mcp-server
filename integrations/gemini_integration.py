"""Gemini Integration for Workshop MCP Server.

This module provides integration with Google's Gemini AI to use the Workshop MCP Server tools.
Supports both direct API calls and function calling.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
import google.generativeai as genai


class GeminiMCPClient:
    """Client for integrating Gemini with Workshop MCP Server."""

    def __init__(
        self,
        mcp_base_url: str = "http://127.0.0.1:8080",
        api_key: Optional[str] = None,
        model_name: str = "gemini-pro"
    ):
        """Initialize Gemini MCP Client.

        Args:
            mcp_base_url: Base URL of the Workshop MCP Server web GUI
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            model_name: Gemini model to use (gemini-pro, gemini-1.5-pro, etc.)
        """
        self.base_url = mcp_base_url.rstrip('/')

        # Configure Gemini
        api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def _call_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP Server API endpoint.

        Args:
            endpoint: API endpoint (e.g., '/api/debug-cluster')
            data: Request payload

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=data, timeout=300)
        response.raise_for_status()
        return response.json()

    # ==================== Code Review ====================

    def review_code(
        self,
        code: str,
        language: str = "python",
        focus_areas: Optional[List[str]] = None,
        with_gemini_analysis: bool = True
    ) -> Dict[str, Any]:
        """Review code and optionally get Gemini's analysis.

        Args:
            code: Code to review
            language: Programming language
            focus_areas: Review focus areas (security, bugs, performance, etc.)
            with_gemini_analysis: Whether to get Gemini's natural language analysis

        Returns:
            Dictionary with review results and optional Gemini analysis
        """
        # Call MCP server
        result = self._call_api('/api/review-code', {
            'code': code,
            'language': language,
            'review_focus': focus_areas or ['security', 'bugs', 'performance']
        })

        if with_gemini_analysis and result.get('status') == 'success':
            # Get Gemini's interpretation
            prompt = f"""
            Code review results for {language} code:

            Total Issues: {result.get('issues_found', 0)}
            Summary: {result.get('summary', 'N/A')}

            Issues:
            {json.dumps(result.get('issues', []), indent=2)}

            Provide:
            1. A brief summary of the most critical issues
            2. Prioritized recommendations for fixing them
            3. Overall code quality assessment
            """

            analysis = self.model.generate_content(prompt)
            result['gemini_analysis'] = analysis.text

        return result

    # ==================== PR Review ====================

    def review_pr(
        self,
        pr_url: str,
        code: Optional[str] = None,
        with_gemini_summary: bool = True
    ) -> Dict[str, Any]:
        """Review GitHub Pull Request.

        Args:
            pr_url: GitHub PR URL
            code: Code to review (if not fetching from GitHub)
            with_gemini_summary: Whether to generate Gemini summary

        Returns:
            Dictionary with PR review results and optional Gemini summary
        """
        payload = {'pr_url': pr_url}
        if code:
            payload['code'] = code

        result = self._call_api('/api/review-pr', payload)

        if with_gemini_summary and result.get('status') == 'success':
            prompt = f"""
            Pull Request Review Results:

            {json.dumps(result, indent=2)}

            Provide:
            1. Executive summary of the PR quality
            2. Should this PR be merged? Why or why not?
            3. Top 3 action items for the developer
            """

            analysis = self.model.generate_content(prompt)
            result['gemini_summary'] = analysis.text

        return result

    # ==================== OpenShift Testing ====================

    def generate_ocp_test(
        self,
        feature: str,
        component: str,
        scenario: str,
        test_format: str = "shell",
        namespace: Optional[str] = None,
        with_gemini_explanation: bool = True
    ) -> Dict[str, Any]:
        """Generate OpenShift test case.

        Args:
            feature: Feature description
            component: Component name
            scenario: Test scenario
            test_format: Format (gherkin, yaml, go, shell)
            namespace: Target namespace
            with_gemini_explanation: Whether to get Gemini's explanation

        Returns:
            Dictionary with test case and optional explanation
        """
        result = self._call_api('/api/generate-ocp-test', {
            'feature': feature,
            'component': component,
            'scenario': scenario,
            'format': test_format,
            'namespace': namespace
        })

        if with_gemini_explanation and result.get('status') == 'success':
            prompt = f"""
            Generated {test_format} test case:

            {result.get('test_case', '')}

            Explain:
            1. What this test validates
            2. How to run it
            3. What success looks like
            4. Common failure scenarios
            """

            explanation = self.model.generate_content(prompt)
            result['gemini_explanation'] = explanation.text

        return result

    def execute_ocp_test(
        self,
        feature: str,
        component: str,
        scenario: str,
        namespace: Optional[str] = None,
        with_gemini_analysis: bool = True
    ) -> Dict[str, Any]:
        """Execute OpenShift test step by step.

        Args:
            feature: Feature being tested
            component: Component under test
            scenario: Test scenario
            namespace: Target namespace
            with_gemini_analysis: Whether to analyze results with Gemini

        Returns:
            Dictionary with execution results and optional analysis
        """
        result = self._call_api('/api/execute-ocp-test', {
            'feature': feature,
            'component': component,
            'scenario': scenario,
            'namespace': namespace
        })

        if with_gemini_analysis and result.get('status') == 'success':
            prompt = f"""
            Test Execution Results:

            Total Steps: {result.get('total_steps', 0)}
            Passed: {result.get('passed_steps', 0)}
            Failed: {result.get('failed_steps', 0)}

            Steps:
            {json.dumps(result.get('steps', []), indent=2)}

            Analyze:
            1. Did the test pass or fail?
            2. If failed, what went wrong?
            3. What should be done to fix it?
            """

            analysis = self.model.generate_content(prompt)
            result['gemini_analysis'] = analysis.text

        return result

    # ==================== Must-Gather Analysis ====================

    def analyze_mustgather(
        self,
        bundle_path: str,
        with_gemini_insights: bool = True
    ) -> Dict[str, Any]:
        """Analyze must-gather bundle.

        Args:
            bundle_path: Path to must-gather bundle
            with_gemini_insights: Whether to get Gemini insights

        Returns:
            Dictionary with analysis results and optional insights
        """
        result = self._call_api('/api/analyze-mustgather', {
            'bundle_path': bundle_path,
            'detailed_analysis': True
        })

        if with_gemini_insights and result.get('status') == 'success':
            cluster_health = result.get('cluster_health', {})
            sre_report = result.get('sre_diagnostic_report', {})

            prompt = f"""
            Must-Gather Analysis Results:

            Cluster Status: {cluster_health.get('status', 'unknown')}
            Critical Issues: {cluster_health.get('critical_issues', 0)}
            Primary Issue: {sre_report.get('primary_issue', 'N/A')}
            Root Cause: {sre_report.get('root_cause_summary', 'N/A')}

            Issues:
            {json.dumps(result.get('issues', [])[:10], indent=2)}

            Provide:
            1. Executive summary for management
            2. Immediate actions required (in order of priority)
            3. Long-term recommendations
            4. Estimated time to resolution
            """

            insights = self.model.generate_content(prompt)
            result['gemini_insights'] = insights.text

        return result

    # ==================== Cluster Debugger ====================

    def debug_cluster(
        self,
        issue_description: str,
        namespace: Optional[str] = None,
        component: Optional[str] = None,
        with_gemini_guidance: bool = True
    ) -> Dict[str, Any]:
        """Debug OpenShift cluster issue.

        Args:
            issue_description: Description of the cluster issue
            namespace: Target namespace
            component: Component name
            with_gemini_guidance: Whether to get Gemini's step-by-step guidance

        Returns:
            Dictionary with diagnostics and optional guidance
        """
        result = self._call_api('/api/debug-cluster', {
            'issue_description': issue_description,
            'namespace': namespace,
            'component': component,
            'include_test_case': False
        })

        if with_gemini_guidance and result.get('status') == 'success':
            diagnostics = result.get('diagnostics', {})
            fix_recs = result.get('fix_recommendations', [])

            prompt = f"""
            Cluster Diagnostic Results:

            Issue: {issue_description}
            Issue Type: {result.get('issue_analysis', {}).get('issue_type', 'unknown')}
            Severity: {result.get('issue_analysis', {}).get('severity', 'unknown')}

            Summary:
            {diagnostics.get('summary', '')}

            Fix Recommendations:
            {json.dumps(fix_recs, indent=2)}

            Provide:
            1. Step-by-step troubleshooting guide (for someone new to OpenShift)
            2. What each command does and why
            3. Expected output at each step
            4. How to verify the issue is resolved
            """

            guidance = self.model.generate_content(prompt)
            result['gemini_guidance'] = guidance.text

        return result

    # ==================== Conversational Interface ====================

    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Chat with Gemini about MCP Server capabilities.

        Args:
            message: User message
            context: Optional context from previous operations

        Returns:
            Gemini's response
        """
        system_prompt = """
        You are an AI assistant helping users interact with the Workshop MCP Server.

        The server provides:
        1. Code review (line-by-line analysis)
        2. GitHub PR review automation
        3. OpenShift test generation and execution
        4. Must-gather bundle analysis
        5. Cluster debugging with diagnostics

        Available methods:
        - review_code(code, language)
        - review_pr(pr_url)
        - generate_ocp_test(feature, component, scenario)
        - execute_ocp_test(feature, component, scenario)
        - analyze_mustgather(bundle_path)
        - debug_cluster(issue_description)

        Help the user understand what they can do and guide them.
        """

        full_prompt = system_prompt + "\n\n"

        if context:
            full_prompt += f"Context from previous operation:\n{json.dumps(context, indent=2)}\n\n"

        full_prompt += f"User: {message}\n\nAssistant:"

        response = self.model.generate_content(full_prompt)
        return response.text


# ==================== Example Usage ====================

def main():
    """Example usage of Gemini MCP Client."""

    # Initialize client
    client = GeminiMCPClient()

    print("=" * 60)
    print("Gemini + Workshop MCP Server Integration Examples")
    print("=" * 60)

    # Example 1: Code Review with Gemini Analysis
    print("\n1. Code Review with Gemini Analysis")
    print("-" * 60)

    code_to_review = """
def process_user_data(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchall()
"""

    result = client.review_code(
        code=code_to_review,
        language="python",
        with_gemini_analysis=True
    )

    print(f"Issues Found: {result.get('issues_found', 0)}")
    print(f"\nGemini's Analysis:\n{result.get('gemini_analysis', 'N/A')}")

    # Example 2: Cluster Debugging with Gemini Guidance
    print("\n\n2. Cluster Debugging with Gemini Guidance")
    print("-" * 60)

    result = client.debug_cluster(
        issue_description="API server pods are crashing",
        namespace="openshift-kube-apiserver",
        with_gemini_guidance=True
    )

    print(f"Issue Type: {result.get('issue_analysis', {}).get('issue_type', 'N/A')}")
    print(f"Severity: {result.get('issue_analysis', {}).get('severity', 'N/A')}")
    print(f"\nGemini's Step-by-Step Guidance:\n{result.get('gemini_guidance', 'N/A')}")

    # Example 3: Conversational Interface
    print("\n\n3. Conversational Interface")
    print("-" * 60)

    response = client.chat("How can I debug an OpenShift cluster issue?")
    print(f"Gemini: {response}")


if __name__ == "__main__":
    # Set your API key first:
    # export GOOGLE_API_KEY="your-api-key"

    try:
        main()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set GOOGLE_API_KEY environment variable:")
        print("export GOOGLE_API_KEY='your-google-api-key'")
