"""Complete Example: Using Workshop MCP Server with Multiple AI Systems.

This example demonstrates how to use the same MCP Server tools with different AI systems.
"""

import os
from typing import Optional


def example_gemini_direct():
    """Example using Gemini with direct API integration."""
    print("\n" + "=" * 70)
    print("Example 1: Gemini Direct Integration")
    print("=" * 70)

    try:
        from gemini_integration import GeminiMCPClient

        client = GeminiMCPClient()

        # Code review with Gemini analysis
        code = """
def process_payment(card_number, amount):
    query = f"INSERT INTO payments VALUES ('{card_number}', {amount})"
    db.execute(query)
    return True
"""

        print("\n📝 Reviewing code for security issues...")
        result = client.review_code(
            code=code,
            language="python",
            with_gemini_analysis=True
        )

        print(f"\n✅ Issues Found: {result.get('issues_found', 0)}")
        print("\n🤖 Gemini's Analysis:")
        print(result.get('gemini_analysis', 'N/A'))

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Set GOOGLE_API_KEY environment variable")


def example_gemini_function_calling():
    """Example using Gemini with native function calling."""
    print("\n" + "=" * 70)
    print("Example 2: Gemini Function Calling")
    print("=" * 70)

    try:
        from gemini_function_calling import GeminiFunctionCaller

        client = GeminiFunctionCaller()

        print("\n💬 Asking Gemini to debug cluster issue...")
        response = client.chat(
            "My OpenShift API server is not responding. Can you debug it?"
        )

        print("\n🤖 Gemini's Response:")
        print(response)

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Set GOOGLE_API_KEY environment variable")


def example_openai():
    """Example using OpenAI GPT-4."""
    print("\n" + "=" * 70)
    print("Example 3: OpenAI GPT-4 Integration")
    print("=" * 70)

    try:
        from openai_integration import OpenAIMCPClient

        client = OpenAIMCPClient()

        print("\n💬 Asking GPT-4 to generate and explain a test...")
        response = client.chat(
            "Generate a shell test to verify nginx pod is running in test namespace. "
            "Explain what each step does."
        )

        print("\n🤖 GPT-4's Response:")
        print(response)

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Set OPENAI_API_KEY environment variable")


def example_langchain_gemini():
    """Example using LangChain with Gemini."""
    print("\n" + "=" * 70)
    print("Example 4: LangChain + Gemini")
    print("=" * 70)

    try:
        from langchain_integration import create_mcp_agent
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
        agent = create_mcp_agent(llm)

        print("\n🤖 LangChain Agent (powered by Gemini) running...")
        response = agent.run(
            "Review this code and tell me the security issues: "
            "def login(u, p): return db.query(f'SELECT * FROM users WHERE user={u} AND pass={p}')"
        )

        print("\n✅ Agent Response:")
        print(response)

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Install: pip install langchain-google-genai")


def example_langchain_openai():
    """Example using LangChain with OpenAI."""
    print("\n" + "=" * 70)
    print("Example 5: LangChain + OpenAI GPT-4")
    print("=" * 70)

    try:
        from langchain_integration import create_mcp_agent
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
        agent = create_mcp_agent(llm)

        print("\n🤖 LangChain Agent (powered by GPT-4) running...")
        response = agent.run(
            "Debug this cluster issue: pods in openshift-etcd namespace are crashing with OOMKilled"
        )

        print("\n✅ Agent Response:")
        print(response)

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Install: pip install langchain-openai")


def example_langchain_claude():
    """Example using LangChain with Anthropic Claude."""
    print("\n" + "=" * 70)
    print("Example 6: LangChain + Anthropic Claude")
    print("=" * 70)

    try:
        from langchain_integration import create_mcp_agent
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0)
        agent = create_mcp_agent(llm)

        print("\n🤖 LangChain Agent (powered by Claude) running...")
        response = agent.run(
            "Generate a Go test case to verify nginx deployment in production namespace"
        )

        print("\n✅ Agent Response:")
        print(response)

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Install: pip install langchain-anthropic")


def comparison_demo():
    """Compare how different AI systems handle the same task."""
    print("\n" + "=" * 70)
    print("COMPARISON: Same Task, Different AI Systems")
    print("=" * 70)

    task = "Review this code for security: def get_user(id): return db.execute(f'SELECT * FROM users WHERE id={id}')"

    print(f"\n📋 Task: {task}\n")

    # Try Gemini
    try:
        from gemini_integration import GeminiMCPClient
        client = GeminiMCPClient()

        print("\n🟢 GEMINI's Analysis:")
        result = client.review_code(
            code=task.split(': ')[1],
            language="python",
            with_gemini_analysis=True
        )
        print(result.get('gemini_analysis', 'N/A')[:500] + "...")

    except Exception as e:
        print(f"❌ Gemini not available: {e}")

    # Try GPT-4
    try:
        from openai_integration import OpenAIMCPClient
        client = OpenAIMCPClient()

        print("\n🔵 GPT-4's Analysis:")
        response = client.chat(task)
        print(response[:500] + "...")

    except Exception as e:
        print(f"❌ GPT-4 not available: {e}")


def interactive_menu():
    """Interactive menu to choose which example to run."""
    print("\n" + "=" * 70)
    print("Workshop MCP Server - AI Integration Examples")
    print("=" * 70)
    print("\nChoose an example to run:")
    print("  1. Gemini Direct Integration")
    print("  2. Gemini Function Calling")
    print("  3. OpenAI GPT-4 Integration")
    print("  4. LangChain + Gemini")
    print("  5. LangChain + OpenAI")
    print("  6. LangChain + Claude")
    print("  7. Comparison Demo (Gemini vs GPT-4)")
    print("  8. Run All Examples")
    print("  9. Exit")

    choice = input("\nEnter choice (1-9): ").strip()

    examples = {
        "1": example_gemini_direct,
        "2": example_gemini_function_calling,
        "3": example_openai,
        "4": example_langchain_gemini,
        "5": example_langchain_openai,
        "6": example_langchain_claude,
        "7": comparison_demo,
        "8": lambda: run_all_examples(),
    }

    if choice == "9":
        print("\nGoodbye! 👋")
        return

    example_func = examples.get(choice)
    if example_func:
        example_func()
    else:
        print("\n❌ Invalid choice. Please try again.")

    # Ask to continue
    if input("\nRun another example? (y/n): ").lower() == 'y':
        interactive_menu()


def run_all_examples():
    """Run all examples sequentially."""
    print("\n🚀 Running all integration examples...")

    example_gemini_direct()
    input("\n⏸️  Press Enter to continue to next example...")

    example_gemini_function_calling()
    input("\n⏸️  Press Enter to continue to next example...")

    example_openai()
    input("\n⏸️  Press Enter to continue to next example...")

    example_langchain_gemini()
    input("\n⏸️  Press Enter to continue to next example...")

    example_langchain_openai()
    input("\n⏸️  Press Enter to continue to next example...")

    example_langchain_claude()
    input("\n⏸️  Press Enter to continue to comparison...")

    comparison_demo()

    print("\n✅ All examples completed!")


def check_prerequisites():
    """Check if prerequisites are met."""
    print("\n🔍 Checking prerequisites...")

    issues = []

    # Check API keys
    if not os.getenv('GOOGLE_API_KEY'):
        issues.append("⚠️  GOOGLE_API_KEY not set (needed for Gemini examples)")

    if not os.getenv('OPENAI_API_KEY'):
        issues.append("⚠️  OPENAI_API_KEY not set (needed for OpenAI examples)")

    if not os.getenv('ANTHROPIC_API_KEY'):
        issues.append("⚠️  ANTHROPIC_API_KEY not set (needed for Claude examples)")

    # Check if MCP Server is running
    try:
        import requests
        response = requests.get("http://127.0.0.1:8080", timeout=2)
        print("✅ MCP Server is running")
    except:
        issues.append("❌ MCP Server is NOT running at http://127.0.0.1:8080")
        issues.append("   Run: cd ../web_gui && python app.py")

    # Check packages
    try:
        import google.generativeai
        print("✅ google-generativeai installed")
    except ImportError:
        issues.append("⚠️  google-generativeai not installed (pip install google-generativeai)")

    try:
        import openai
        print("✅ openai installed")
    except ImportError:
        issues.append("⚠️  openai not installed (pip install openai)")

    try:
        import langchain
        print("✅ langchain installed")
    except ImportError:
        issues.append("⚠️  langchain not installed (pip install langchain)")

    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"   {issue}")
        print("\n💡 Some examples may not work. Fix issues above to run all examples.")
    else:
        print("\n✅ All prerequisites met! You can run all examples.")

    return len(issues) == 0


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("Workshop MCP Server - Complete Integration Examples")
    print("=" * 70)
    print("\nThis demonstrates using MCP Server with:")
    print("  • Google Gemini (Direct API + Function Calling)")
    print("  • OpenAI GPT-4 (Function Calling)")
    print("  • LangChain (Universal - works with ANY LLM)")
    print("=" * 70)

    # Check prerequisites
    all_good = check_prerequisites()

    if not all_good:
        if input("\nContinue anyway? (y/n): ").lower() != 'y':
            print("\nExiting. Please fix prerequisites and try again.")
            return

    # Show menu
    interactive_menu()


if __name__ == "__main__":
    main()
