"""
Simple MCP server using FastMCP.

This template provides a minimal starting point for building MCP servers
with FastMCP. All tools are defined inline for simplicity.
"""

import asyncio
from typing import Any, Dict

from fastmcp import FastMCP
from pydantic import BaseModel

from .config import get_settings

# Initialize settings and create the FastMCP server
settings = get_settings()
mcp = FastMCP(name="FastMCP Template Server")


# Input models for type safety
class CalculationInput(BaseModel):
    a: float
    b: float


class EchoInput(BaseModel):
    message: str


class FilePathInput(BaseModel):
    path: str


# Simple tools defined inline
@mcp.tool()
def hello_world() -> str:
    """A simple greeting tool."""
    return "Hello from FastMCP!"


@mcp.tool()
def calculate_sum(params: CalculationInput) -> Dict[str, Any]:
    """Add two numbers together."""
    result = params.a + params.b
    return {
        "result": result,
        "calculation": f"{params.a} + {params.b} = {result}"
    }


@mcp.tool() 
def echo_message(params: EchoInput) -> Dict[str, str]:
    """Echo back a message with metadata."""
    return {
        "original": params.message,
        "echoed": f"Echo: {params.message}",
        "length": str(len(params.message))
    }


@mcp.tool()
async def get_server_info() -> Dict[str, Any]:
    """Get information about this MCP server."""
    tools = await mcp.get_tools()
    return {
        "name": settings.server_name,
        "version": "1.0.0",
        "description": "A simple FastMCP template server",
        "tools_count": len(tools),
        "status": "running"
    }


@mcp.tool()
async def list_files(params: FilePathInput) -> Dict[str, Any]:
    """List files in a directory (async example)."""
    import os
    from pathlib import Path
    
    try:
        path = Path(params.path)
        if not path.exists():
            return {"error": f"Path does not exist: {params.path}"}
        
        if not path.is_dir():
            return {"error": f"Path is not a directory: {params.path}"}
        
        files = []
        for item in path.iterdir():
            files.append({
                "name": item.name,
                "is_file": item.is_file(),
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else None
            })
        
        return {
            "path": str(path),
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        return {"error": f"Failed to list files: {str(e)}"}


# Optional: Add a simple resource example
@mcp.resource("file://{path}")
async def read_file(path: str) -> str:
    """Read a text file and return its contents."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


# Optional: Add a simple prompt example  
@mcp.prompt()
def code_review_prompt(
    code: str,
    language: str = "python"
) -> str:
    """Generate a code review prompt."""
    return f"""Please review the following {language} code:

```{language}
{code}
```

Focus on:
- Code quality and readability
- Potential bugs or issues  
- Best practices
- Performance considerations
"""


def main():
    """Run the MCP server."""
    import argparse
    import uvicorn
    
    parser = argparse.ArgumentParser(description="FastMCP Template Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind to")
    parser.add_argument("--transport", type=str, default="stdio", 
                       choices=["stdio", "http"], help="Transport method")
    
    args = parser.parse_args()
    
    if args.transport == "stdio":
        # Run in stdio mode for MCP clients
        mcp.run()
    else:
        # Run HTTP server for testing/debugging
        uvicorn.run(
            "src.server:mcp",
            host=args.host,
            port=args.port,
            reload=True
        )


if __name__ == "__main__":
    main()