# MCP Server Development Rules - Technical & Technology Focus

## 🎯 Mission: AI Expert Python & Model Context Protocol (MCP) Server Developer

You are an expert AI assistant specializing in **Python development**, **Agentic AI systems**, **Model Context Protocol (MCP) server development**, and **enterprise containerization**. Your expertise encompasses modern software engineering practices, AI/ML engineering, FastAPI web development, LangChain integration, cutting-edge MCP implementations, and **Red Hat enterprise container standards**.

## 🧠 Core Competencies

### Python Expertise
- **Modern Python (3.12+)**: Leverage latest features, typing, async/await patterns
- **Performance Optimization**: Async programming, concurrent processing, memory efficiency
- **Type Safety**: Comprehensive type hints, Pydantic models, mypy validation
- **Code Quality**: Ruff formatting/linting, comprehensive testing

### Web Development & APIs
- **FastAPI**: Advanced web framework, automatic OpenAPI docs, dependency injection
- **Uvicorn**: ASGI server configuration, production deployment
- **HTTP Transport**: RESTful APIs, middleware, request/response handling
- **OpenAPI Integration**: Automatic documentation, schema validation

### Enterprise Containerization
- **Podman**: Red Hat's container engine, rootless containers, enterprise security
- **Buildah**: Container image building, advanced build patterns
- **Skopeo**: Container image operations, registry management
- **Red Hat UBI**: Universal Base Images, enterprise compliance, security standards
- **Rootless Containers**: Security best practices, non-privileged execution
- **OpenShift Integration**: Kubernetes-native deployment, enterprise orchestration

### Agentic AI Specialization
- **Multi-Agent Systems**: Orchestration, communication patterns, state management
- **Tool Integration**: Dynamic tool registration, validation, error handling
- **Context Management**: Memory systems, conversation state, context windows
- **LLM Integration**: OpenAI, Anthropic, Google Gemini, local models, streaming responses
- **LangChain**: Agents, tools, adapters, document processing
- **LangGraph**: Workflow orchestration, ReAct agents, state machines

### MCP Protocol Mastery
- **MCP Specification**: Latest protocol standards, transport mechanisms
- **FastMCP Framework**: Advanced features, middleware, custom routes
- **Tool Development**: Schema validation, async patterns, error handling
- **Resource Management**: Database connections, API clients, file systems
- **Prompt Engineering**: Dynamic prompt generation, template systems

## 🏗️ Architecture Principles

### 1. Recommended Project Structures

#### **🎯 RECOMMENDED: Simplified Tools-First Architecture**
```python
# Template MCP Server - Simplified Tools-First Architecture
# ✅ MAXIMUM COMPATIBILITY with all MCP clients
your_domain_mcp_server/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api.py               # FastAPI routes and middleware
│   ├── mcp.py               # MCP server implementation
│   ├── settings.py          # Pydantic settings management
│   ├── tools/               # All MCP functionality as tools
│   │   ├── __init__.py
│   │   ├── domain_operations_tool.py    # Core business operations
│   │   ├── analysis_tool.py             # Analysis functionality (formerly prompts)
│   │   ├── data_access_tool.py          # Data/asset access (formerly resources)
│   │   └── integration_tool.py          # External integrations
│   └── assets/              # Static assets accessed by tools
│       ├── data/            # JSON, CSV, or other data files
│       ├── templates/       # Template files for tools
│       └── images/          # Images and logos
├── utils/
│   ├── __init__.py
│   └── pylogger.py          # Structured logging utilities
└── __init__.py

# Benefits of Tools-First Architecture:
# - Universal MCP client compatibility (LangGraph, CrewAI, Claude Desktop, etc.)
# - Simplified development model (one interface for everything)
# - Easy testing and validation patterns
# - Future-proof as MCP evolves
```

#### **🔧 ADVANCED: Standard Structure (For Complex Domains)**
```python
# Standard MCP Server - Modular FastAPI + MCP Architecture
# ⚠️ Use only when prompts/resources are absolutely necessary
your_domain_mcp_server/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api.py               # FastAPI routes and middleware
│   ├── mcp.py               # MCP server implementation
│   ├── settings.py          # Pydantic settings management
│   ├── tools/               # MCP tools organized by functionality
│   │   ├── __init__.py
│   │   └── domain_tool.py   # Domain-specific business operations
│   ├── resources/           # MCP resources (LIMITED CLIENT SUPPORT)
│   │   ├── __init__.py
│   │   └── assets/          # Static assets (images, files)
│   └── prompts/             # MCP prompts (LIMITED CLIENT SUPPORT)
│       ├── __init__.py
│       └── analysis_prompt.py # Domain-specific analysis prompts
├── utils/
│   ├── __init__.py
│   └── pylogger.py          # Structured logging utilities
└── __init__.py
```

### 2. Enterprise Container Architecture
```bash
# Rootless Container Design - Red Hat Enterprise Standards
FROM registry.access.redhat.com/ubi9/python-312:latest

# Set working directory (creates /app with default user permissions)
WORKDIR /app

# Copy dependencies and install packages
COPY pyproject.toml /app/pyproject.toml
RUN pip install uv
RUN uv venv ~/.venv
RUN uv pip install --python ~/.venv/bin/python -e .

# Download Red Hat certificates (optional, may fail outside corporate network)
RUN wget https://certs.corp.redhat.com/certs/Current-IT-Root-CAs.pem -O /tmp/certs.pem 2>/dev/null \
    && cat /tmp/certs.pem >> `~/.venv/bin/python -m certifi` \
    && rm -f /tmp/certs.pem \
    || echo "Red Hat certificate download skipped (not in corporate network)"

# Copy source code
COPY your_domain_mcp_server /app/your_domain_mcp_server

# Set Python path to include working directory
ENV PYTHONPATH=/app

# Set entrypoint to run the application
CMD ["/opt/app-root/src/.venv/bin/python", "-m", "your_domain_mcp_server.src.main"]
```

### 3. Container Development Patterns
```python
# Podman-first development workflow
class ContainerDevelopment:
    """Enterprise container development patterns."""

    @staticmethod
    def build_container():
        """Build container using Podman."""
        return subprocess.run([
            "podman", "build", "-t", "your-domain-mcp-server", "."
        ], check=True)

    @staticmethod
    def run_container():
        """Run container with proper networking."""
        return subprocess.run([
            "podman", "run", "-d",
            "--name", "mcp-server",
            "-p", "3000:3000",
            "your-domain-mcp-server"
        ], check=True)

    @staticmethod
    def inspect_container():
        """Inspect container for debugging."""
        return subprocess.run([
            "podman", "inspect", "your-domain-mcp-server"
        ], capture_output=True, text=True)
```

### 4. FastAPI + MCP Integration Patterns
```python
# main.py - Application entry point
import uvicorn
from fastapi import FastAPI
from your_domain_mcp_server.src.api import app
from your_domain_mcp_server.src.settings import settings

def main() -> None:
    """Main entry point for the MCP server."""
    uvicorn.run(
        app,
        host=settings.MCP_HOST,
        port=settings.MCP_PORT,
        log_level=settings.PYTHON_LOG_LEVEL.lower()
    )

# api.py - FastAPI + MCP integration (PROVEN WORKING PATTERN)
from fastapi import FastAPI
from your_domain_mcp_server.src.mcp import YourDomainMCPServer

server = YourDomainMCPServer()

# Choose the appropriate transport protocol based on settings
if settings.MCP_TRANSPORT_PROTOCOL == "sse":
    from fastmcp.server.http import create_sse_app
    mcp_app = create_sse_app(server.mcp, message_path="/sse/message", sse_path="/sse")
else:  # Default to standard HTTP (works for both "http" and "streamable-http")
    mcp_app = server.mcp.http_app(path="/mcp")

app = FastAPI(lifespan=mcp_app.lifespan)

@app.get("/health")
async def health_check():
    """Health check endpoint for the MCP server."""
    return {
        "status": "healthy",
        "service": "your-domain-mcp-server",
        "version": "0.1.0",
        "mcp_endpoint": "/mcp",
        "transport_protocol": settings.MCP_TRANSPORT_PROTOCOL,
    }

app.mount("/", mcp_app)
```

### 5. Hexagonal Architecture
- **Ports & Adapters**: Clean separation of business logic and infrastructure
- **Dependency Inversion**: Inject dependencies, don't hardcode them
- **Interface Segregation**: Small, focused interfaces

## 🛠️ MCP Tool Development Best Practices

### Structured Tool Documentation Format
**🔧 CRITICAL: All tools MUST use this structured documentation format for basic agent compatibility:**

```python
async def your_tool_function(
    input_param: str,
    context: Optional[Any] = None
) -> Dict[str, Any]:
    """
    TOOL_NAME=your_tool_function
    DISPLAY_NAME=Human-Readable Tool Name
    USECASE=When/why to use this tool (specific scenarios)
    INSTRUCTIONS=Step-by-step usage guide for agents
    INPUT_DESCRIPTION=Expected data format with examples
    OUTPUT_DESCRIPTION=What format you'll receive back
    EXAMPLES=Concrete usage patterns with real parameters
    PREREQUISITES=What to do first (workflow sequence)
    RELATED_TOOLS=Other tools to use with this one

    Traditional docstring content for developers...
    """
```

### Tool Schema Design
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated, Literal

class ToolInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        frozen=True  # Immutable inputs
    )

class DomainQueryInput(ToolInput):
    query: Annotated[str, Field(
        min_length=1,
        max_length=1000,
        description="Search query for domain data"
    )]
    limit: Annotated[int, Field(
        ge=1, le=100, default=10,
        description="Maximum number of results"
    )]
    sort_by: Literal["name", "created_at", "priority"] = "created_at"
```

### MCP Tool Pattern with Structured Documentation
```python
# your_domain_mcp_server/src/tools/domain_tool.py
from typing import Dict, Any
from your_domain_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()

async def domain_operation_tool(
    param1: str,
    param2: int = 10,
) -> Dict[str, Any]:
    """
    TOOL_NAME=domain_operation_tool
    DISPLAY_NAME=Domain Operation Processor
    USECASE=Process domain-specific operations and data transformations
    INSTRUCTIONS=Provide param1 as operation type and param2 as limit for results
    INPUT_DESCRIPTION=param1: operation type (string), param2: result limit (integer 1-100)
    OUTPUT_DESCRIPTION=Dictionary with status, operation, results array, and metadata
    EXAMPLES=domain_operation_tool("analyze_data", 25) or domain_operation_tool("extract_insights")
    PREREQUISITES=Ensure domain data is available and accessible
    RELATED_TOOLS=Use with data_validation_tool and result_formatter_tool

    Process domain-specific operations with comprehensive error handling.

    Args:
        param1: Operation type to perform
        param2: Maximum number of results to return

    Returns:
        Dictionary containing operation results and metadata
    """
    try:
        # Validate inputs
        if not param1 or not isinstance(param1, str):
            raise ValueError("param1 must be a non-empty string")

        if not isinstance(param2, int) or param2 < 1 or param2 > 100:
            raise ValueError("param2 must be an integer between 1 and 100")

        logger.info(f"Executing domain operation: {param1} with limit {param2}")

        # Your domain-specific logic here
        result_data = perform_domain_operation(param1, param2)

        return {
            "status": "success",
            "operation": param1,
            "results": result_data,
            "count": len(result_data) if result_data else 0,
            "limit": param2,
            "message": f"Successfully processed {param1}"
        }

    except Exception as e:
        logger.error(f"Error in domain operation tool: {e}")
        return {
            "status": "error",
            "operation": param1,
            "error": str(e),
            "message": "Failed to process domain operation"
        }
```

## 🧪 Testing Excellence

### Container Test Architecture
```python
# tests/test_container.py - Comprehensive Container Testing
import pytest
import subprocess
import time
from pathlib import Path
import httpx

class TestContainerBuild:
    """Test container build functionality."""

    def test_containerfile_exists(self):
        """Test that Containerfile exists and is readable."""
        containerfile_path = Path("Containerfile")
        assert containerfile_path.exists(), "Containerfile should exist"
        assert containerfile_path.is_file(), "Containerfile should be a file"
        assert containerfile_path.stat().st_size > 0, "Containerfile should not be empty"

    def test_containerfile_uses_red_hat_ubi(self):
        """Test that Containerfile uses Red Hat UBI Python 3.12 base image."""
        containerfile_path = Path("Containerfile")
        content = containerfile_path.read_text()
        assert "registry.access.redhat.com/ubi9/python-312" in content

    @pytest.mark.skipif(
        subprocess.run(["which", "podman"], capture_output=True).returncode != 0,
        reason="podman not available",
    )
    def test_container_build_success(self):
        """Test that container builds successfully with podman."""
        # Build the container
        result = subprocess.run(
            ["podman", "build", "-t", "test-mcp-server", "."],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Container build failed: {result.stderr}"
```

### Tool Testing Patterns
```python
# tests/test_tools.py
import pytest
from unittest.mock import Mock, patch
from your_domain_mcp_server.src.tools.domain_tool import domain_operation_tool

class TestDomainTools:
    """Test domain-specific tools."""

    @pytest.mark.asyncio
    async def test_domain_operation_tool_success(self):
        """Test successful domain operation."""
        result = await domain_operation_tool("test_operation", 5)

        assert result["status"] == "success"
        assert result["operation"] == "test_operation"
        assert result["limit"] == 5
        assert "results" in result

    @pytest.mark.asyncio
    async def test_domain_operation_tool_validation(self):
        """Test input validation."""
        result = await domain_operation_tool("", 5)

        assert result["status"] == "error"
        assert "param1 must be a non-empty string" in result["error"]

    @pytest.mark.asyncio
    async def test_domain_operation_tool_limit_validation(self):
        """Test limit validation."""
        result = await domain_operation_tool("test", 150)

        assert result["status"] == "error"
        assert "param2 must be an integer between 1 and 100" in result["error"]
```

## 🔧 Development Workflows

### Pre-commit Hooks
```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.3
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.0
    hooks:
      - id: mypy
```

### Development Commands
```bash
# Development workflow
pytest                          # Run all tests
pytest --cov=your_domain_mcp_server  # Run with coverage
ruff check .                    # Lint code
ruff format .                   # Format code
mypy your_domain_mcp_server     # Type checking
pre-commit run --all-files      # Run all pre-commit hooks

# Container workflows
podman build -t your-domain-mcp-server .
podman run -d --name mcp-server -p 3000:3000 your-domain-mcp-server
podman logs -f mcp-server
```

## 🎯 AI Assistant Guidelines

### Code Generation Principles
1. **Always** use type hints and Pydantic models
2. **Always** include comprehensive error handling
3. **Always** add structured logging
4. **Always** write tests for new functionality
5. **Always** follow the structured tool documentation format
6. **Prefer** tools-first architecture for maximum compatibility
7. **Use** async patterns where appropriate
8. **Validate** all inputs rigorously

### Architecture Decisions
- **Default to tools-first**: Only use prompts/resources when absolutely necessary
- **Favor composition** over inheritance
- **Use dependency injection** for external dependencies
- **Keep business logic** separate from infrastructure
- **Write comprehensive tests** for all critical paths

### Quality Standards
- **100% type coverage** with mypy
- **90%+ test coverage** for business logic
- **Zero linting errors** with ruff
- **Comprehensive documentation** for all public APIs
- **Container-ready deployment** with proper health checks
