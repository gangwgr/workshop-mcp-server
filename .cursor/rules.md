# Cursor Rules for Expert MCP Server Development

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

### 1. Current Project Structure
```python
# Template MCP Server - Modular FastAPI + MCP Architecture
template_mcp_server/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api.py               # FastAPI routes and middleware
│   ├── mcp.py               # MCP server implementation
│   ├── settings.py          # Pydantic settings management
│   ├── tools/               # MCP tools organized by functionality
│   │   ├── __init__.py
│   │   └── multiply_tool.py # Example: mathematical operations
│   ├── resources/           # MCP resources (files, assets, data)
│   │   ├── __init__.py
│   │   ├── assets/          # Static assets (images, files)
│   │   └── redhat_logo.py   # Example: base64 encoded resources
│   └── prompts/             # MCP prompts for LLM interactions
│       ├── __init__.py
│       └── code_review_prompt.py # Example: code analysis prompts
├── utils/
│   ├── __init__.py
│   └── pylogger.py          # Structured logging utilities
└── __init__.py

examples/                    # Client integration examples
├── fastmcp_client.py        # Direct FastMCP client usage
└── langgraph_client.py      # LangGraph agent integration

tests/                       # Comprehensive test suite
├── conftest.py              # Test configuration and fixtures
├── test_api.py              # FastAPI endpoint tests
├── test_tools.py            # MCP tool tests
├── test_resources.py        # MCP resource tests
├── test_prompts.py          # MCP prompt tests
├── test_container.py        # Container build and execution tests
└── test_integration.py      # End-to-end integration tests

openshift/                   # Kubernetes/OpenShift deployment
├── deployment.yaml          # Production deployment configuration
├── service.yaml             # Service definitions
└── route.yaml               # External access routes

# Enterprise Container Configuration
├── Containerfile            # Podman/Buildah container definition
├── .containerignore         # Container build optimization
└── compose.yaml             # Container compose configuration
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
RUN uv pip install --python ~/.venv/bin/python -r pyproject.toml

# Download Red Hat certificates (optional, may fail outside corporate network)
RUN wget https://certs.corp.redhat.com/certs/Current-IT-Root-CAs.pem -O /tmp/certs.pem 2>/dev/null \
    && cat /tmp/certs.pem >> `~/.venv/bin/python -m certifi` \
    && rm -f /tmp/certs.pem \
    || echo "Red Hat certificate download skipped (not in corporate network)"

# Copy source code
COPY template_mcp_server /app/template_mcp_server

# Set Python path to include working directory
ENV PYTHONPATH=/app

# Set entrypoint to run the application
CMD ["/opt/app-root/src/.venv/bin/python", "-m", "template_mcp_server.src.main"]
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
            "podman", "build", "-t", "template-mcp-server", "."
        ], check=True)

    @staticmethod
    def run_container():
        """Run container with proper networking."""
        return subprocess.run([
            "podman", "run", "-d",
            "--name", "mcp-server",
            "-p", "3000:3000",
            "template-mcp-server"
        ], check=True)

    @staticmethod
    def inspect_container():
        """Inspect container for debugging."""
        return subprocess.run([
            "podman", "inspect", "template-mcp-server"
        ], capture_output=True, text=True)
```

### 4. Domain-Driven MCP Design
```python
# Organize MCP capabilities by business domains
template_mcp_server/src/
├── tools/                   # Business logic as MCP tools
│   ├── analytics/           # Analytics and reporting tools
│   ├── data/               # Data processing and transformation tools
│   ├── integrations/       # External API integration tools
│   └── math/               # Mathematical operation tools
├── resources/              # Data and asset access
│   ├── documents/          # Document retrieval and search
│   ├── databases/          # Database query resources
│   └── apis/               # API data resources
└── prompts/                # LLM interaction templates
    ├── analysis/           # Data analysis prompts
    ├── generation/         # Content generation prompts
    └── review/             # Code/content review prompts
```

### 5. FastAPI + MCP Integration Patterns
```python
# main.py - Application entry point
import uvicorn
from fastapi import FastAPI
from template_mcp_server.src.api import app
from template_mcp_server.src.settings import settings

def main() -> None:
    """Main entry point for the MCP server."""
    uvicorn.run(
        app,
        host=settings.MCP_HOST,
        port=settings.MCP_PORT,
        log_level=settings.PYTHON_LOG_LEVEL.lower()
    )

# api.py - FastAPI + MCP integration
from fastapi import FastAPI
from template_mcp_server.src.mcp import TemplateMCPServer

server = TemplateMCPServer()

# Choose transport protocol based on settings
if settings.MCP_TRANSPORT_PROTOCOL == "sse":
    from fastmcp.server.http import create_sse_app
    mcp_app = create_sse_app(server.mcp, message_path="/sse/message", sse_path="/sse")
else:
    mcp_app = server.mcp.http_app(path="/mcp")

app = FastAPI(lifespan=mcp_app.lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "template-mcp-server"}
```

### 6. Hexagonal Architecture
- **Ports & Adapters**: Clean separation of business logic and infrastructure
- **Dependency Inversion**: Inject dependencies, don't hardcode them
- **Interface Segregation**: Small, focused interfaces

### 7. Event-Driven Patterns
```python
from typing import Protocol
from abc import abstractmethod

class EventHandler(Protocol):
    @abstractmethod
    async def handle(self, event: Event) -> None: ...

class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler):
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: Event):
        handlers = self._handlers.get(event.type, [])
        await asyncio.gather(*[h.handle(event) for h in handlers])
```

## 🛠️ MCP Tool Development Best Practices

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

class UserQueryInput(ToolInput):
    query: Annotated[str, Field(
        min_length=1,
        max_length=1000,
        description="Search query for users"
    )]
    limit: Annotated[int, Field(
        ge=1, le=100, default=10,
        description="Maximum number of results"
    )]
    sort_by: Literal["name", "created_at", "email"] = "created_at"
```

### Advanced Tool Registration
```python
from functools import wraps
from typing import TypeVar, Callable, Any

T = TypeVar('T', bound=Callable[..., Any])

def mcp_tool(
    name: str | None = None,
    description: str | None = None,
    input_schema: type[BaseModel] | None = None,
    output_schema: type[BaseModel] | None = None,
    rate_limit: int | None = None,
    requires_auth: bool = False,
    cache_ttl: int | None = None
) -> Callable[[T], T]:
    """Advanced tool decorator with validation and metadata."""
    def decorator(func: T) -> T:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Input validation
            if input_schema:
                validated_input = input_schema(**kwargs)
                kwargs = validated_input.model_dump()

            # Rate limiting check
            if rate_limit:
                await check_rate_limit(func.__name__, rate_limit)

            # Authentication check
            if requires_auth:
                await validate_auth_context()

            # Cache check
            if cache_ttl:
                cached = await get_cached_result(func.__name__, kwargs)
                if cached:
                    return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Output validation
            if output_schema:
                validated_output = output_schema(**result)
                result = validated_output.model_dump()

            # Cache result
            if cache_ttl:
                await cache_result(func.__name__, kwargs, result, cache_ttl)

            return result

        # Store metadata
        wrapper._mcp_metadata = {
            "name": name or func.__name__,
            "description": description or func.__doc__,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "rate_limit": rate_limit,
            "requires_auth": requires_auth,
            "cache_ttl": cache_ttl
        }

        return wrapper
    return decorator

# Usage
@mcp_tool(
    name="query_users",
    description="Search and retrieve user information",
    input_schema=UserQueryInput,
    output_schema=UserQueryOutput,
    rate_limit=100,
    cache_ttl=300
)
async def query_users(query: str, limit: int = 10) -> dict:
    # Implementation
    pass
```

### Template MCP Server Tool Pattern
```python
# template_mcp_server/src/tools/example_tool.py
from typing import Dict, Any
from template_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()

def example_tool(
    param1: str,
    param2: int = 10,
) -> Dict[str, Any]:
    """Example tool following template patterns.

    Args:
        param1: Description of parameter
        param2: Optional parameter with default

    Returns:
        Dictionary containing operation results

    Raises:
        ValueError: If validation fails
    """
    try:
        logger.info(f"Executing example_tool with param1={param1}, param2={param2}")

        # Input validation
        if not param1 or not param1.strip():
            raise ValueError("param1 cannot be empty")

        # Business logic
        result = {
            "status": "success",
            "operation": "example",
            "input": {"param1": param1, "param2": param2},
            "result": f"Processed {param1} with factor {param2}",
            "message": f"Successfully processed {param1}"
        }

        logger.info(f"Tool execution successful: {result['message']}")
        return result

    except Exception as e:
        error_msg = f"Error in example_tool: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "operation": "example",
            "error": error_msg,
            "input": {"param1": param1, "param2": param2}
        }
```

### FastAPI + MCP Integration Patterns
```python
# template_mcp_server/src/mcp.py
from fastmcp import FastMCP
from template_mcp_server.src.tools.multiply_tool import multiply_numbers
from template_mcp_server.src.resources.redhat_logo import read_redhat_logo_content
from template_mcp_server.src.prompts.code_review_prompt import get_code_review_prompt

class TemplateMCPServer:
    """Main Template MCP Server implementation."""

    def __init__(self):
        """Initialize the MCP server with template tools."""
        self.mcp = FastMCP("template")

        # Register MCP capabilities
        self._register_mcp_tools()
        self._register_mcp_resources()
        self._register_mcp_prompts()

    def _register_mcp_tools(self):
        """Register all MCP tools."""
        self.mcp.tool()(multiply_numbers)

    def _register_mcp_resources(self):
        """Register all MCP resources."""
        self.mcp.resource("redhat-logo")(read_redhat_logo_content)

    def _register_mcp_prompts(self):
        """Register all MCP prompts."""
        self.mcp.prompt()(get_code_review_prompt)
```

### LangChain Integration Patterns
```python
# examples/langgraph_client.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

async def create_langgraph_agent():
    """Create LangGraph agent with MCP server integration."""

    # Configure LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )

    # Connect to MCP server
    async with MultiServerMCPClient() as client:
        await client.add_server(
            name="template_mcp_server",
            url="http://0.0.0.0:3000/mcp"
        )

        # Get MCP tools as LangChain tools
        tools = await client.get_tools()

        # Create ReAct agent
        agent = create_react_agent(llm, tools)

        return agent, client
```

## 🔧 Enterprise Container Testing Excellence

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
        image_name = "template-mcp-server-test"
        build_cmd = ["podman", "build", "-t", image_name, "."]
        cleanup_cmd = ["podman", "rmi", image_name]

        try:
            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            assert result.returncode == 0, f"Build failed: {result.stderr}"
        finally:
            subprocess.run(cleanup_cmd, capture_output=True)


class TestContainerExecution:
    """Test container execution and functionality."""

    @pytest.mark.skipif(
        subprocess.run(["which", "podman"], capture_output=True).returncode != 0,
        reason="podman not available",
    )
    def test_container_startup_and_health(self):
        """Test that container starts and responds to HTTP requests."""
        image_name = "template-mcp-server-test"
        container_name = "template-mcp-test-container"
        build_cmd = ["podman", "build", "-t", image_name, "."]
        run_cmd = [
            "podman", "run", "-d", "--name", container_name,
            "-p", "3001:3000", image_name,
        ]
        stop_cmd = ["podman", "stop", container_name]
        rm_cmd = ["podman", "rm", container_name]
        cleanup_img_cmd = ["podman", "rmi", image_name]

        try:
            # Build container
            build_result = subprocess.run(
                build_cmd, capture_output=True, text=True, timeout=300
            )
            assert build_result.returncode == 0, f"Build failed: {build_result.stderr}"

            # Start container
            run_result = subprocess.run(run_cmd, capture_output=True, text=True)
            assert run_result.returncode == 0, f"Container start failed: {run_result.stderr}"

            # Wait for container to start
            time.sleep(5)

            # Test that container is responding
            with httpx.Client() as client:
                response = client.get("http://localhost:3001/", timeout=10)
                assert response.status_code >= 200, f"Server not responding: {response.status_code}"

        finally:
            subprocess.run(stop_cmd, capture_output=True)
            subprocess.run(rm_cmd, capture_output=True)
            subprocess.run(cleanup_img_cmd, capture_output=True)


class TestContainerConfiguration:
    """Test container configuration and setup."""

    def test_containerfile_uses_virtual_environment(self):
        """Test that container uses Python virtual environment."""
        containerfile_path = Path("Containerfile")
        content = containerfile_path.read_text()

        assert "uv venv" in content, "Should create virtual environment"
        assert "/opt/app-root/src/.venv/bin/python" in content, "Should use virtual environment Python"

    def test_containerfile_includes_red_hat_certificates(self):
        """Test that container includes Red Hat certificate handling."""
        containerfile_path = Path("Containerfile")
        content = containerfile_path.read_text()

        assert "Current-IT-Root-CAs.pem" in content, "Should include Red Hat certificates"
        assert "certifi" in content, "Should update certificate bundle"

    def test_container_pythonpath_configuration(self):
        """Test that container sets PYTHONPATH correctly."""
        containerfile_path = Path("Containerfile")
        content = containerfile_path.read_text()

        assert "ENV PYTHONPATH=/app" in content, "Should set PYTHONPATH to /app"


class TestProductionDeployment:
    """Test production deployment readiness."""

    def test_containerfile_optimized_for_production(self):
        """Test that Containerfile follows production best practices."""
        containerfile_path = Path("Containerfile")
        content = containerfile_path.read_text()

        # Multi-stage or optimized dependency installation
        assert "uv" in content, "Should use uv for fast dependency installation"

        # Dependencies installed before source code copy
        copy_lines = [i for i, line in enumerate(content.split("\n")) if "COPY" in line]
        assert len(copy_lines) >= 2, "Should have separate dependency and source copy steps"

    @pytest.mark.skipif(
        subprocess.run(["which", "podman"], capture_output=True).returncode != 0,
        reason="podman not available",
    )
    def test_container_resource_usage(self):
        """Test container resource usage and startup time."""
        image_name = "template-mcp-server-test"
        build_cmd = ["podman", "build", "-t", image_name, "."]
        inspect_cmd = ["podman", "inspect", image_name]
        cleanup_cmd = ["podman", "rmi", image_name]

        try:
            build_result = subprocess.run(
                build_cmd, capture_output=True, text=True, timeout=300
            )
            assert build_result.returncode == 0, f"Build failed: {build_result.stderr}"

            inspect_result = subprocess.run(inspect_cmd, capture_output=True, text=True)
            assert inspect_result.returncode == 0, "Container inspect should succeed"
            assert len(inspect_result.stdout) > 100, "Inspect output should contain meaningful data"

        finally:
            subprocess.run(cleanup_cmd, capture_output=True)
```

### Container Development Commands
```bash
# Essential Podman Commands for Development

# Build container
podman build -t template-mcp-server .

# Run container
podman run -d --name mcp-server -p 3000:3000 template-mcp-server

# View logs
podman logs -f mcp-server

# Stop and cleanup
podman stop mcp-server && podman rm mcp-server

# Inspect container
podman inspect template-mcp-server

# Test container build and execution
pytest tests/test_container.py -v
```

## 🧪 Testing Excellence

### Test Architecture
```python
import pytest
import respx
from unittest.mock import AsyncMock
from httpx import Response

class TestFixtures:
    @pytest.fixture
    async def mcp_server(self):
        """Configured MCP server for testing."""
        from template_mcp_server.src.mcp import TemplateMCPServer
        return TemplateMCPServer()

    @pytest.fixture
    async def mock_database(self):
        """Mock database with test data."""
        db = AsyncMock()
        db.execute.return_value.fetchall.return_value = [
            {"id": 1, "name": "Test User", "email": "test@example.com"}
        ]
        return db

    @pytest.fixture
    def mock_external_api(self):
        """Mock external API responses."""
        with respx.mock:
            respx.get("https://api.example.com/users").mock(
                return_value=Response(200, json={"users": []})
            )
            yield

# Tool-specific tests
class TestUserTools(TestFixtures):
    @pytest.mark.asyncio
    async def test_query_users_success(self, mcp_server, mock_database):
        """Test successful user query."""
        result = await mcp_server.call_tool("query_users", {
            "query": "john",
            "limit": 10
        })

        assert result["success"] is True
        assert len(result["data"]["users"]) > 0

    @pytest.mark.asyncio
    async def test_query_users_validation_error(self, mcp_server):
        """Test input validation error handling."""
        result = await mcp_server.call_tool("query_users", {
            "query": "",  # Invalid empty query
            "limit": 10
        })

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"

# Integration tests
class TestMCPIntegration(TestFixtures):
    @pytest.mark.asyncio
    async def test_tool_chaining(self, mcp_server, mock_external_api):
        """Test complex tool chains."""
        # First tool call
        users = await mcp_server.call_tool("query_users", {"query": "test"})

        # Second tool call using first result
        user_id = users["data"]["users"][0]["id"]
        profile = await mcp_server.call_tool("get_user_profile", {"user_id": user_id})

        assert profile["success"] is True
        assert profile["data"]["user_id"] == user_id

# Property-based testing
from hypothesis import given, strategies as st

class TestPropertyBased:
    @given(
        query=st.text(min_size=1, max_size=100),
        limit=st.integers(min_value=1, max_value=100)
    )
    @pytest.mark.asyncio
    async def test_query_users_properties(self, query, limit, mcp_server):
        """Property-based test for user queries."""
        result = await mcp_server.call_tool("query_users", {
            "query": query,
            "limit": limit
        })

        # Properties that should always hold
        assert isinstance(result, dict)
        assert "success" in result
        if result["success"]:
            assert len(result["data"]["users"]) <= limit
```

### Template MCP Server Testing Patterns
```python
# tests/test_tools.py - Testing MCP tools
import pytest
from template_mcp_server.src.tools.multiply_tool import multiply_numbers

class TestMultiplyTool:
    def test_multiply_numbers_success(self):
        """Test successful multiplication."""
        result = multiply_numbers(5.0, 3.0)

        assert result["status"] == "success"
        assert result["operation"] == "multiplication"
        assert result["result"] == 15.0
        assert "message" in result

    def test_multiply_numbers_validation_error(self):
        """Test input validation error handling."""
        result = multiply_numbers("invalid", 3.0)

        assert result["status"] == "error"
        assert "error" in result

# tests/test_api.py - Testing FastAPI endpoints
import pytest
from fastapi.testclient import TestClient
from template_mcp_server.src.api import app

class TestAPI:
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "template-mcp-server"

# tests/test_integration.py - End-to-end testing
import pytest
from fastmcp import Client

class TestMCPIntegration:
    @pytest.mark.asyncio
    async def test_tool_execution_via_client(self):
        """Test tool execution through MCP client."""
        async with Client("http://localhost:3000/mcp") as client:
            # Test tool execution
            result = await client.call_tool("multiply_numbers", {"params": {"a": 5, "b": 3}})

            assert result.content[0].text is not None
            assert "15" in result.content[0].text  # 5 * 3 = 15

    @pytest.mark.asyncio
    async def test_resources_via_client(self):
        """Test resource access through MCP client."""
        async with Client("http://localhost:3000/mcp") as client:
            # Test resource listing
            resources = await client.list_resources()
            assert len(resources.resources) > 0

            # Test resource reading
            resource = await client.read_resource("resource://redhat-logo")
            assert resource.contents[0].text is not None

# tests/conftest.py - Shared test configuration
import pytest
import asyncio
from template_mcp_server.src.main import main

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mcp_server():
    """Fixture providing configured MCP server."""
    from template_mcp_server.src.mcp import TemplateMCPServer
    return TemplateMCPServer()
```

## 🔧 Development Workflow

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=10000']
      - id: check-for-merge-conflicts
      - id: debug-statements
      - id: check-for-case-conflicts
      - id: check-docstring-first
      - id: check-json
      - id: check-toml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.2
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.16.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  - repo: https://github.com/PyCQA/pydocstyle
    rev: 6.3.0
    hooks:
      - id: pydocstyle
```

### Container Development Workflow
```bash
# Complete container development cycle
podman build -t template-mcp-server .                    # Build with Podman
pytest tests/test_container.py -v                        # Run container tests
podman run -d --name mcp-server -p 3000:3000 template-mcp-server  # Start container
podman logs -f mcp-server                                # View container logs
podman stop mcp-server && podman rm mcp-server          # Stop and cleanup
podman inspect template-mcp-server                       # Inspect container details

# Quality assurance
pre-commit run --all-files    # Run all quality checks
pytest tests/ -v              # Run full test suite
pytest tests/test_container.py -v  # Run container-specific tests
```

### AI Assistant Guidelines

When working with this codebase:

1. **Always use Podman** - This is a Red Hat enterprise environment, no Docker references
2. **Validate inputs** using Pydantic models before processing
3. **Use type hints extensively** - they're not optional, they're documentation
4. **Implement proper error handling** - wrap exceptions in MCPError types
5. **Write tests first** - TDD helps clarify requirements, include container tests
6. **Monitor performance** - use the monitoring decorators for new tools
7. **Document thoroughly** - include examples in docstrings
8. **Follow async patterns** - prefer async/await over sync operations
9. **Validate security** - sanitize all user inputs, follow rootless container principles
10. **Structure for maintainability** - prefer composition over inheritance
11. **Keep tools focused** - each tool should have a single responsibility
12. **Test containers thoroughly** - use comprehensive container test patterns

### Code Review Checklist

- [ ] Type hints on all functions and methods
- [ ] Comprehensive error handling with specific error types
- [ ] Input validation using Pydantic or manual validation
- [ ] Async patterns used appropriately
- [ ] Security considerations addressed (rootless containers, input sanitization)
- [ ] Tests written (unit, integration, and container tests)
- [ ] Documentation updated
- [ ] Performance monitoring added for new tools
- [ ] Logging statements for debugging
- [ ] Memory usage considered for large operations
- [ ] Container configuration follows Red Hat UBI standards
- [ ] Podman compatibility verified
- [ ] No Docker references in code or documentation

## 🎯 Success Metrics

Track these metrics to ensure quality:

- **Test Coverage**: Maintain >90% code coverage
- **Type Coverage**: Achieve 100% type hint coverage
- **Performance**: Tool execution time <100ms for simple operations
- **Memory**: Memory usage stays under configured limits
- **Error Rate**: <1% error rate in production
- **Documentation**: All public functions have comprehensive docstrings
- **Container Security**: All containers run rootless with Red Hat UBI
- **Container Build Time**: Container builds complete in <5 minutes
- **Container Tests**: 100% container test pass rate

---

*Remember: You're building enterprise-grade systems that AI agents will rely on in production Red Hat environments. Prioritize security, reliability, performance, and Red Hat ecosystem compatibility above all else.*
