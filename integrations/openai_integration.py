"""OpenAI (GPT-4) Integration for Workshop MCP Server.

This module provides integration with OpenAI's GPT-4 to use Workshop MCP Server tools.
Supports function calling and assistants API.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from openai import OpenAI


class OpenAIMCPClient:
    """Client for integrating OpenAI GPT-4 with Workshop MCP Server."""

    def __init__(
        self,
        mcp_base_url: str = "http://127.0.0.1:8080",
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview"
    ):
        """Initialize OpenAI MCP Client.

        Args:
            mcp_base_url: Base URL of the Workshop MCP Server
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: OpenAI model to use
        """
        self.base_url = mcp_base_url.rstrip('/')
        self.model = model

        # Initialize OpenAI client
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")

        self.client = OpenAI(api_key=api_key)

        # Define function tools
        self.tools = self._create_function_tools()

    def _create_function_tools(self) -> List[Dict[str, Any]]:
        """Create function tool definitions for OpenAI."""

        return [
            {
                "type": "function",
                "function": {
                    "name": "review_code",
                    "description": "Review code for security vulnerabilities, bugs, and best practices",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The code to review"
                            },
                            "language": {
                                "type": "string",
                                "description": "Programming language (python, go, java, javascript, etc.)",
                                "enum": ["python", "go", "java", "javascript", "typescript", "bash", "yaml"]
                            },
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "debug_cluster",
                    "description": "Debug OpenShift/Kubernetes cluster issues with AI-powered diagnostics",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_description": {
                                "type": "string",
                                "description": "Description of the cluster issue"
                            },
                            "namespace": {
                                "type": "string",
                                "description": "Target namespace (optional)"
                            },
                            "component": {
                                "type": "string",
                                "description": "Component name like pod, operator, node (optional)"
                            },
                        },
                        "required": ["issue_description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_ocp_test",
                    "description": "Generate OpenShift test cases in various formats (Gherkin, YAML, Go, Shell)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "feature": {
                                "type": "string",
                                "description": "Feature to test"
                            },
                            "component": {
                                "type": "string",
                                "description": "Component name"
                            },
                            "scenario": {
                                "type": "string",
                                "description": "Test scenario description"
                            },
                            "test_format": {
                                "type": "string",
                                "description": "Test format",
                                "enum": ["gherkin", "yaml", "go", "shell"]
                            },
                            "namespace": {
                                "type": "string",
                                "description": "Target namespace (optional)"
                            },
                        },
                        "required": ["feature", "component", "scenario"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_ocp_test",
                    "description": "Execute OpenShift test step by step with real-time progress",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "feature": {
                                "type": "string",
                                "description": "Feature being tested"
                            },
                            "component": {
                                "type": "string",
                                "description": "Component under test"
                            },
                            "scenario": {
                                "type": "string",
                                "description": "Test scenario"
                            },
                            "namespace": {
                                "type": "string",
                                "description": "Target namespace (optional)"
                            },
                        },
                        "required": ["feature", "component", "scenario"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_mustgather",
                    "description": "Analyze OpenShift must-gather bundle for cluster issues with AI",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "bundle_path": {
                                "type": "string",
                                "description": "Full path to must-gather bundle directory"
                            },
                        },
                        "required": ["bundle_path"]
                    }
                }
            },
        ]

    def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute function against MCP Server.

        Args:
            function_name: Name of the function
            arguments: Function arguments

        Returns:
            Function execution result
        """
        # Map to API endpoints
        endpoint_map = {
            "review_code": "/api/review-code",
            "debug_cluster": "/api/debug-cluster",
            "generate_ocp_test": "/api/generate-ocp-test",
            "execute_ocp_test": "/api/execute-ocp-test",
            "analyze_mustgather": "/api/analyze-mustgather",
        }

        # Prepare payload
        payload = {}

        if function_name == "review_code":
            payload = {
                "code": arguments.get("code"),
                "language": arguments.get("language", "python"),
                "review_focus": ["security", "bugs", "performance", "best-practices"]
            }

        elif function_name == "debug_cluster":
            payload = {
                "issue_description": arguments.get("issue_description"),
                "namespace": arguments.get("namespace"),
                "component": arguments.get("component"),
                "include_test_case": False
            }

        elif function_name == "generate_ocp_test":
            payload = {
                "feature": arguments.get("feature"),
                "component": arguments.get("component"),
                "scenario": arguments.get("scenario"),
                "format": arguments.get("test_format", "shell"),
                "namespace": arguments.get("namespace")
            }

        elif function_name == "execute_ocp_test":
            payload = {
                "feature": arguments.get("feature"),
                "component": arguments.get("component"),
                "scenario": arguments.get("scenario"),
                "namespace": arguments.get("namespace")
            }

        elif function_name == "analyze_mustgather":
            payload = {
                "bundle_path": arguments.get("bundle_path"),
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

    def chat(self, message: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """Chat with GPT-4 with function calling.

        Args:
            message: User message
            conversation_history: Previous conversation messages

        Returns:
            GPT-4's response
        """
        messages = conversation_history or []

        # Add system message if this is the start
        if not messages:
            messages.append({
                "role": "system",
                "content": """You are an AI assistant helping with OpenShift/Kubernetes operations.
                You have access to tools for code review, cluster debugging, test generation,
                test execution, and must-gather analysis. Use these tools to help users."""
            })

        # Add user message
        messages.append({"role": "user", "content": message})

        # Call OpenAI with function calling
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Handle function calls
        if response_message.tool_calls:
            # Add assistant's response to messages
            messages.append(response_message)

            # Execute each function call
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"\n🔧 Calling function: {function_name}")
                print(f"   Arguments: {function_args}")

                # Execute function
                result = self._execute_function(function_name, function_args)

                print(f"   ✅ Status: {result.get('status', 'unknown')}")

                # Add function result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(result)
                })

            # Get final response from GPT-4
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            return second_response.choices[0].message.content

        return response_message.content

    def interactive_session(self):
        """Start an interactive session with GPT-4."""
        print("=" * 70)
        print("GPT-4 + Workshop MCP Server - Interactive Mode")
        print("=" * 70)
        print("\nYou can ask GPT-4 to:")
        print("  - Review code for security and bugs")
        print("  - Debug OpenShift cluster issues")
        print("  - Generate and execute tests")
        print("  - Analyze must-gather bundles")
        print("\nType 'exit' to quit, 'clear' to reset conversation\n")

        messages = []

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ['exit', 'quit']:
                    print("\nGoodbye!")
                    break

                if user_input.lower() == 'clear':
                    messages = []
                    print("\n✨ Conversation cleared!")
                    continue

                if not user_input:
                    continue

                # Get response
                response = self.chat(user_input, messages)

                print(f"\nGPT-4: {response}")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")


# ==================== Example Usage ====================

def main():
    """Example usage of OpenAI MCP Client."""

    client = OpenAIMCPClient()

    print("=" * 70)
    print("Example 1: Code Review with GPT-4")
    print("=" * 70)

    response = client.chat("""
    Review this code for SQL injection vulnerabilities:

    ```python
    def get_user(user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        return cursor.fetchone()
    ```
    """)

    print(f"\nGPT-4: {response}")

    print("\n" + "=" * 70)
    print("Example 2: Cluster Debugging")
    print("=" * 70)

    response = client.chat(
        "My OpenShift API server pods are crashing. Can you help debug this?"
    )

    print(f"\nGPT-4: {response}")

    print("\n" + "=" * 70)
    print("Example 3: Test Generation")
    print("=" * 70)

    response = client.chat(
        "Generate a shell script test to verify nginx pod is running in production namespace"
    )

    print(f"\nGPT-4: {response}")

    # Start interactive mode
    print("\n" + "=" * 70)
    print("Starting Interactive Session")
    print("=" * 70)

    client.interactive_session()


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set OPENAI_API_KEY environment variable:")
        print("export OPENAI_API_KEY='sk-...'")
