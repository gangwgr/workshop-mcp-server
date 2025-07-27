"""Settings for the Template MCP Server."""

import asyncio
import time
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

from template_mcp_server.src.settings import settings

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

            logger.info("Template MCP Server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Template MCP Server: {e}")
            raise

    def _register_mcp_tools(self) -> None:
        """Register MCP tools for template operations."""
        # Register all the imported tools
        self.mcp.tool()(multiply_numbers)

        @self.mcp.custom_route("/health", methods=["GET"])
        async def health_check(request: Request) -> JSONResponse:
            """Enhanced health check endpoint.

            Returns JSON with details about the MCP and its dependencies.
            Responds with HTTP 200 if all checks pass; otherwise, HTTP 503.
            """
            start_time = time.time()
            health_status: Dict[str, Any] = {
                "status": "ok",
                "checks": {"mcp_initialized": self.mcp is not None},
                "uptime_seconds": round(time.time() - start_time, 2),
            }

            # Determine HTTP status based on checks
            checks: Dict[str, bool] = health_status["checks"]
            if not all(checks.values()):
                health_status["status"] = "error"
                return JSONResponse(content=health_status, status_code=503)

            return JSONResponse(content=health_status)

    def start(self) -> None:
        """Start the MCP server.

        Starts the FastMCP server with streamable HTTP transport on the
        configured host and port. This is a blocking call.

        Raises:
            RuntimeError: If server startup fails.
        """
        try:
            logger.info(
                "Starting Template MCP Server",
                host=settings.MCP_HOST,
                port=settings.MCP_PORT,
            )

            # Start the FastMCP server with streamable HTTP transport
            asyncio.run(self._start_async())

        except KeyboardInterrupt:
            logger.info("Server startup interrupted by user")
            raise
        except Exception as e:
            logger.error(f"Failed to start server: {e}", exc_info=True)
            raise RuntimeError(f"Server startup failed: {e}") from e

    async def _start_async(self) -> None:
        """Async method to start the MCP server.

        Raises:
            RuntimeError: If async server startup fails.
        """
        try:
            uvicorn_config = {}
            if settings.MCP_SSL_KEYFILE and settings.MCP_SSL_CERTFILE:
                uvicorn_config["ssl_keyfile"] = settings.MCP_SSL_KEYFILE
                uvicorn_config["ssl_certfile"] = settings.MCP_SSL_CERTFILE
                logger.info(
                    "Starting server with SSL",
                    ssl_keyfile=settings.MCP_SSL_KEYFILE,
                    ssl_certfile=settings.MCP_SSL_CERTFILE,
                )
            await self.mcp.run_http_async(
                transport=settings.MCP_TRANSPORT_PROTOCOL,
                host=settings.MCP_HOST,
                port=settings.MCP_PORT,
                uvicorn_config=uvicorn_config if uvicorn_config else None,
            )
        except Exception as e:
            logger.error(f"Async server startup failed: {e}", exc_info=True)
            raise RuntimeError(f"Async server startup failed: {e}") from e
