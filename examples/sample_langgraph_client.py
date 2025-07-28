"""LangGraph MCP Client Example - Template MCP Server Integration.

This example demonstrates how to create a LangGraph agent that connects to the
template MCP server and uses its available tools for mathematical operations.

The example shows:
- Setting up a LangGraph ReAct agent with Google's Gemini model
- Connecting to the template MCP server via HTTP transport
- Using MCP tools for mathematical calculations
- Handling tool calls and responses in a conversational context

Prerequisites:
- Template MCP server must be running on http://0.0.0.0:4000
- Google Generative AI credentials must be configured via
    GEMINI_API_KEY environment variable or
    GOOGLE_APPLICATION_CREDENTIALS environment variable
- All required Python packages must be installed
- Required dependencies: langchain-google-genai, langchain-mcp-adapters, langgraph

Note:
- LangGraph's create_react_agent only supports MCP tools, not MCP resources or prompts
- It's recommended to stick to MCP tools when using LangGraph agents
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

current_date = datetime.now().strftime("%B %d, %Y")


system_prompt = f"""
    You are an Agent, a helpful assistant with the ability to use specialized tools.

    Today's date is {current_date}.

    A few things to remember:
    - **Always use the same language as the user.**
    - **Please include markdown-formatted links to any citations used in your response.** Only include one or two citations per response unless more are needed. ONLY USE LINKS RETURNED BY THE TOOLS.
    - **Only use the tools you are given to answer the user's question.** Do not answer directly from internal knowledge.
    - **You must always reason before acting.**
    - **Every Final Answer must be grounded in tool observations.**
    - **Always make sure your answer is *FORMATTED WELL*.**
    """


@asynccontextmanager
async def get_agent_redhat():
    """Create and yield a fully initialized LangGraph agent with MCP integration.

    This function sets up a LangGraph ReAct agent that connects to the template
    MCP server and uses Google's Gemini model for reasoning and tool usage.

    The agent is configured with:
    - Google Generative AI (Gemini 2.0 Flash) as the language model
    - Tools from the template MCP server (e.g., multiply_numbers)
    - A system prompt that guides tool usage and response formatting

    Note:
    - LangGraph agents only support MCP tools, not MCP resources or prompts
    - For resources and prompts, use MultiServerMCPClient directly
    - This example focuses on tool usage which is the recommended approach

    Yields:
        A configured LangGraph agent that can use MCP tools for calculations
        and other operations provided by the template MCP server.

    Example:
        async with get_agent_redhat() as agent:
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": "What is 5 * 3?"}]
            })
    """
    # Initialize MCP client and get tools
    client = MultiServerMCPClient(
        {
            "template_mcp_server": {
                "url": "http://0.0.0.0:4000/mcp/",
                "transport": "streamable_http",
            },
        }
    )

    tools = await client.get_tools()
    # resources = await client.get_resources(tools)

    agent_redhat = create_react_agent(
        model=ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.5,
        ),
        prompt=system_prompt,
        tools=tools,
    )
    yield agent_redhat


async def demonstrate_tool_calls():
    """Demonstrate MCP tool calls using the LangGraph agent.

    This function shows how the LangGraph agent can use tools from the template
    MCP server to perform mathematical operations. It demonstrates:

    1. Tool Selection: How the agent decides which tool to use
    2. Parameter Formatting: How the agent formats tool parameters
    3. Response Processing: How the agent interprets tool responses
    4. Final Answer Generation: How the agent provides user-friendly responses

    The example uses the multiply_numbers tool to perform calculations
    and shows the complete conversation flow including tool calls.
    """
    print("\n" + "=" * 60)
    print("🔧 Tool Call Examples")
    print("=" * 60)

    async with get_agent_redhat() as agent:
        # Example 1: Mathematical operation
        print("\n📊 Example 1: Mathematical Operation")
        print("Question: What is 15 multiplied by 7?")

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "What is 15 multiplied by 7?"}]}
        )
        print(f"Agent Response: {result}")


async def main():
    """Run the complete LangGraph MCP client demonstration.

    This main function orchestrates all the demonstration examples and provides
    a comprehensive overview of LangGraph integration with the template MCP server.

    The demonstration includes:
    - Tool call examples showing mathematical operations
    - Error handling for connection issues
    - Summary of demonstrated capabilities

    Raises:
        Exception: If the MCP server is not accessible or other connection issues occur
    """
    print("🚀 LangGraph MCP Client Examples")
    print("=" * 60)
    print("This demonstrates various capabilities of the LangGraph agent")
    print("connected to the template MCP server.")

    try:
        # Run all examples
        await demonstrate_tool_calls()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        print("\nThis demonstrates:")
        print("- 🔧 Tool calls for mathematical operations")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Make sure the template MCP server is running on http://0.0.0.0:4000")


if __name__ == "__main__":
    asyncio.run(main())
