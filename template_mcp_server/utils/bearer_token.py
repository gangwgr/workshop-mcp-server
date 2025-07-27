"""Bearer token utilities for the template MCP server."""

from fastmcp import Context

from template_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


def get_bearer_token(ctx: Context) -> str:
    """Extract Bearer token from HTTP request headers.

    Parses the Authorization header to extract the OAuth access token
    for Snowflake authentication.

    Args:
        ctx (Context): MCP context containing HTTP request with headers.

    Returns:
        str: Extracted access token from the Authorization header.

    Raises:
        ValueError: If Authorization header is missing or malformed.
        RuntimeError: If context or request is invalid.
    """
    try:
        # Validate context
        if not ctx:
            raise ValueError("Context is required")

        request = ctx.get_http_request()
        if not request:
            raise ValueError("HTTP request not available in context")

        headers = request.headers
        if not headers:
            raise ValueError("Request headers not available")

        authorization_header = headers.get("Authorization")

        if not authorization_header:
            raise ValueError("Authorization header missing")

        # Validate header format
        parts = authorization_header.split()
        if len(parts) != 2:
            raise ValueError(
                "Invalid Authorization header format. Expected: 'Bearer <token>'"
            )

        if parts[0] != "Bearer":
            raise ValueError("Invalid Authorization scheme. Expected: 'Bearer <token>'")

        token = parts[1].strip()
        if not token:
            raise ValueError("Access token cannot be empty")

        logger.debug("Bearer token extracted successfully")
        return token

    except AttributeError as e:
        raise RuntimeError(f"Invalid context structure: {e}") from e
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Unexpected error extracting bearer token: {e}") from e
