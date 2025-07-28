"""Settings for the Template MCP Server."""

from fastmcp import FastMCP

# Import prompts from the prompts package
from template_mcp_server.src.prompts.code_review_prompt import (
    get_code_review_prompt,
)

# Import resources from the resources package
from template_mcp_server.src.resources.redhat_logo import (
    read_redhat_logo_content,
)

# Import tools from the tools package
from template_mcp_server.src.tools.multiply_tool import (
    multiply_numbers,
)
from template_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


class TemplateMCPServer:
    """Main Template MCP Server implementation."""

    def __init__(self):
        """Initialize the MCP server with template tools."""
        try:
            # Initialize FastMCP server
            self.mcp = FastMCP("template")

            # Register MCP tools
            self._register_mcp_tools()

            # Register MCP resources
            self._register_mcp_resources()

            # Register MCP prompts
            self._register_mcp_prompts()

            logger.info("Template MCP Server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Template MCP Server: {e}")
            raise

    def _register_mcp_tools(self) -> None:
        """Register MCP tools for template operations."""
        # Register all the imported tools
        self.mcp.tool()(multiply_numbers)

    def _register_mcp_resources(self) -> None:
        """Register MCP resources for template operations."""
        # Register all the imported resources
        self.mcp.resource("resource://redhat-logo")(read_redhat_logo_content)

    def _register_mcp_prompts(self) -> None:
        """Register MCP prompts for template operations."""
        # Register all the prompts
        self.mcp.prompt()(get_code_review_prompt)
