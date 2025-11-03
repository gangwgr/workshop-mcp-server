"""Gemini Function Calling Integration for Workshop MCP Server.

This module demonstrates how to use Gemini's native function calling capability
to interact with Workshop MCP Server tools.
"""

import os
import json
import requests
from typing import Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool, Schema, Type


class GeminiFunctionCaller:
    """Gemini Function Calling integration for Workshop MCP Server."""

    def __init__(
        self,
        mcp_base_url: str = "http://127.0.0.1:8080",
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro"
    ):
        """Initialize Gemini Function Caller.

        Args:
            mcp_base_url: Base URL of the Workshop MCP Server
            api_key: Google API key
            model_name: Gemini model (must support function calling)
        """
        self.base_url = mcp_base_url.rstrip('/')

        # Configure Gemini
        api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")

        genai.configure(api_key=api_key)

        # Define function schemas
        self.functions = self._create_function_schemas()

        # Create model with function calling
        self.model = genai.GenerativeModel(
            model_name,
            tools=[Tool(function_declarations=list(self.functions.values()))]
        )

    def _create_function_schemas(self) -> Dict[str, FunctionDeclaration]:
        """Create function schemas for all MCP Server tools."""

        return {
            "review_code": FunctionDeclaration(
                name="review_code",
                description="Review code for security, bugs, and best practices",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "code": Schema(
                            type=Type.STRING,
                            description="Code to review"
                        ),
                        "language": Schema(
                            type=Type.STRING,
                            description="Programming language (python, go, java, etc.)"
                        ),
                    },
                    required=["code"]
                )
            ),

            "debug_cluster": FunctionDeclaration(
                name="debug_cluster",
                description="Debug OpenShift cluster issues with AI diagnostics",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "issue_description": Schema(
                            type=Type.STRING,
                            description="Description of the cluster issue"
                        ),
                        "namespace": Schema(
                            type=Type.STRING,
                            description="Target namespace (optional)"
                        ),
                        "component": Schema(
                            type=Type.STRING,
                            description="Component name (optional)"
                        ),
                    },
                    required=["issue_description"]
                )
            ),

            "generate_ocp_test": FunctionDeclaration(
                name="generate_ocp_test",
                description="Generate OpenShift test cases in various formats",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "feature": Schema(
                            type=Type.STRING,
                            description="Feature to test"
                        ),
                        "component": Schema(
                            type=Type.STRING,
                            description="Component name"
                        ),
                        "scenario": Schema(
                            type=Type.STRING,
                            description="Test scenario"
                        ),
                        "test_format": Schema(
                            type=Type.STRING,
                            description="Format: gherkin, yaml, go, or shell"
                        ),
                    },
                    required=["feature", "component", "scenario"]
                )
            ),

            "execute_ocp_test": FunctionDeclaration(
                name="execute_ocp_test",
                description="Execute OpenShift test step by step",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "feature": Schema(
                            type=Type.STRING,
                            description="Feature being tested"
                        ),
                        "component": Schema(
                            type=Type.STRING,
                            description="Component under test"
                        ),
                        "scenario": Schema(
                            type=Type.STRING,
                            description="Test scenario"
                        ),
                        "namespace": Schema(
                            type=Type.STRING,
                            description="Target namespace (optional)"
                        ),
                    },
                    required=["feature", "component", "scenario"]
                )
            ),

            "analyze_mustgather": FunctionDeclaration(
                name="analyze_mustgather",
                description="Analyze must-gather bundle for cluster issues",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "bundle_path": Schema(
                            type=Type.STRING,
                            description="Path to must-gather bundle directory"
                        ),
                    },
                    required=["bundle_path"]
                )
            ),
        }

    def _execute_function(self, function_call) -> Dict[str, Any]:
        """Execute function call against MCP Server.

        Args:
            function_call: Gemini function call object

        Returns:
            Function execution result
        """
        function_name = function_call.name
        args = dict(function_call.args)

        # Map function names to API endpoints
        endpoint_map = {
            "review_code": "/api/review-code",
            "debug_cluster": "/api/debug-cluster",
            "generate_ocp_test": "/api/generate-ocp-test",
            "execute_ocp_test": "/api/execute-ocp-test",
            "analyze_mustgather": "/api/analyze-mustgather",
        }

        # Prepare payload based on function
        payload = {}

        if function_name == "review_code":
            payload = {
                "code": args.get("code"),
                "language": args.get("language", "python"),
                "review_focus": ["security", "bugs", "performance", "best-practices"]
            }

        elif function_name == "debug_cluster":
            payload = {
                "issue_description": args.get("issue_description"),
                "namespace": args.get("namespace"),
                "component": args.get("component"),
                "include_test_case": False
            }

        elif function_name == "generate_ocp_test":
            payload = {
                "feature": args.get("feature"),
                "component": args.get("component"),
                "scenario": args.get("scenario"),
                "format": args.get("test_format", "shell")
            }

        elif function_name == "execute_ocp_test":
            payload = {
                "feature": args.get("feature"),
                "component": args.get("component"),
                "scenario": args.get("scenario"),
                "namespace": args.get("namespace")
            }

        elif function_name == "analyze_mustgather":
            payload = {
                "bundle_path": args.get("bundle_path"),
                "detailed_analysis": True
            }

        # Call API
        endpoint = endpoint_map.get(function_name)
        if not endpoint:
            return {"error": f"Unknown function: {function_name}"}

        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def chat(self, message: str) -> str:
        """Chat with Gemini, automatically calling MCP Server functions.

        Args:
            message: User message

        Returns:
            Gemini's response after function execution
        """
        chat = self.model.start_chat()

        # Send initial message
        response = chat.send_message(message)

        # Process function calls
        while True:
            # Check if Gemini wants to call a function
            parts = response.candidates[0].content.parts

            # Find function calls
            function_calls = [
                part.function_call
                for part in parts
                if hasattr(part, 'function_call') and part.function_call
            ]

            if not function_calls:
                # No more function calls, return final response
                return response.text

            # Execute all function calls
            for function_call in function_calls:
                print(f"\n🔧 Calling function: {function_call.name}")
                print(f"   Arguments: {dict(function_call.args)}")

                # Execute function
                result = self._execute_function(function_call)

                print(f"   ✅ Result: {result.get('status', 'unknown')}")

                # Send result back to Gemini
                response = chat.send_message(
                    genai.protos.Content(
                        parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=function_call.name,
                                response=result
                            )
                        )]
                    )
                )

    def multi_turn_conversation(self):
        """Interactive multi-turn conversation with function calling."""
        print("=" * 70)
        print("Gemini Function Calling - Interactive Mode")
        print("=" * 70)
        print("\nYou can ask Gemini to:")
        print("  - Review code")
        print("  - Debug cluster issues")
        print("  - Generate OpenShift tests")
        print("  - Execute tests")
        print("  - Analyze must-gather bundles")
        print("\nType 'exit' to quit\n")

        chat = self.model.start_chat()

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ['exit', 'quit']:
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue

                # Send message and handle function calls
                response = chat.send_message(user_input)

                # Process function calls in a loop
                while True:
                    parts = response.candidates[0].content.parts

                    function_calls = [
                        part.function_call
                        for part in parts
                        if hasattr(part, 'function_call') and part.function_call
                    ]

                    if not function_calls:
                        # No more function calls, show response
                        print(f"\nGemini: {response.text}")
                        break

                    # Execute function calls
                    for function_call in function_calls:
                        print(f"\n  🔧 Calling: {function_call.name}({dict(function_call.args)})")

                        result = self._execute_function(function_call)

                        # Send result back
                        response = chat.send_message(
                            genai.protos.Content(
                                parts=[genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_call.name,
                                        response=result
                                    )
                                )]
                            )
                        )

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")


# ==================== Example Usage ====================

def main():
    """Example usage of Gemini Function Calling."""

    client = GeminiFunctionCaller()

    print("\n" + "=" * 70)
    print("Example 1: Code Review via Function Calling")
    print("=" * 70)

    response = client.chat("""
    Can you review this Python code for security issues?

    ```python
    def get_user(user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        return cursor.fetchone()
    ```
    """)

    print(f"\nGemini's Analysis:\n{response}")

    print("\n" + "=" * 70)
    print("Example 2: Cluster Debugging via Function Calling")
    print("=" * 70)

    response = client.chat(
        "My OpenShift API server is not responding. Can you help debug it?"
    )

    print(f"\nGemini's Guidance:\n{response}")

    print("\n" + "=" * 70)
    print("Example 3: Test Generation via Function Calling")
    print("=" * 70)

    response = client.chat(
        "Generate a shell test to verify an nginx pod is running in the test namespace"
    )

    print(f"\nGemini's Response:\n{response}")

    # Interactive mode
    print("\n" + "=" * 70)
    print("Starting Interactive Mode")
    print("=" * 70)

    client.multi_turn_conversation()


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set GOOGLE_API_KEY environment variable:")
        print("export GOOGLE_API_KEY='your-google-api-key'")
