# Template MCP Server

A Model Context Protocol (MCP) server template that provides a foundation for building MCP servers. This template can be customized for various data operations and management functionality.

## 1. Description

The Template MCP Server is a production-ready foundation for building Model Context Protocol (MCP) servers. It provides a complete framework with:

- **FastAPI-based HTTP server** with multiple transport protocol support
- **Modular tool system** for easy extension and customization
- **Resource management** for file and asset handling (limited client support)
- **Prompt templates** for AI interactions (limited client support)
- **Comprehensive testing** and deployment configurations
- **OpenShift deployment** ready with SSL support

The server supports multiple transport protocols (HTTP, SSE, Streamable-HTTP) and includes built-in tools for mathematical operations, resource access, and code review prompts.

**Important**: Most popular MCP clients like LangGraph and CrewAI only support MCP tools. Resources and prompts have limited client support and should only be implemented when absolutely necessary for your specific use case.

## 2. Architecture

### 2.1 Flow Diagram

```mermaid
graph TD
    A[Client Request] --> B[FastAPI App]
    B --> C{Transport Protocol}
    C -->|HTTP/Streamable-HTTP| D[HTTP Handler]
    C -->|SSE| E[SSE Handler]

    D --> G[MCP Server]
    E --> G

    G --> H{Tool Type}
    H -->|Tools| I[Tool Registry]
    H -->|Resources| J[Resource Registry]
    H -->|Prompts| K[Prompt Registry]

    I --> L[multiply_numbers]
    J --> M[redhat_logo]
    K --> N[code_review_prompt]

    L --> O[Response]
    M --> O
    N --> O

    O --> P[Client Response]

    subgraph "Configuration"
        Q[Settings]
        R[Environment Variables]
        S[SSL Configuration]
    end

    Q --> G
    R --> Q
    S --> G
```

### 2.2 Code Structure

```
template-mcp-server/
├── template_mcp_server/
│   ├── src/
│   │   ├── main.py              # Server entry point
│   │   ├── api.py               # FastAPI application setup
│   │   ├── mcp.py               # MCP server implementation
│   │   ├── settings.py          # Configuration management
│   │   ├── tools/               # MCP tools
│   │   │   └── multiply_tool.py
│   │   ├── resources/           # MCP resources
│   │   │   └── redhat_logo.py
│   │   └── prompts/             # MCP prompts
│   │       └── code_review_prompt.py
│   └── utils/
│       └── pylogger.py          # Logging utilities
├── examples/                     # Client examples
│   ├── fastmcp_client.py
│   └── langgraph_client.py
├── tests/                       # Comprehensive test suite
├── openshift/                   # OpenShift deployment configs
├── compose.yaml                 # Container compose configuration
├── Containerfile               # Container definition
└── pyproject.toml             # Project configuration
```

## 3. Installation

### Prerequisites

- Python 3.12 or higher
- uv (install from https://docs.astral.sh/uv/getting-started/installation/)

### Install from source

```bash
# Clone the repository
git clone https://gitlab.cee.redhat.com/dataverse/ai/mcp-servers/template-mcp-server.git
cd template-mcp-server

# Create venv and activate
uv venv --python 3.12
source .venv/bin/activate

# Install the package
uv pip install -e ".[dev]"

# Install RH certificates
wget https://certs.corp.redhat.com/certs/Current-IT-Root-CAs.pem \
    && cat Current-IT-Root-CAs.pem >> `python -m certifi`
```

## 4. Run the pytests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=template_mcp_server

# Run specific test file
pytest tests/test_tools.py

# Run tests with verbose output
pytest -v
```

## 5. Environment File

Copy the contents of `.env.template` to `.env`:

```env
# MCP Server Configuration
MCP_HOST=0.0.0.0
MCP_PORT=3000
MCP_TRANSPORT_PROTOCOL=http
# MCP_SSL_KEYFILE=/path/to/ssl_key.pem
# MCP_SSL_CERTFILE=/path/to/ssl_cert.pem

# Python Logging
PYTHON_LOG_LEVEL=INFO
```

### 5.1 Transport Protocol

The server supports multiple transport protocols that can be configured via the `MCP_TRANSPORT_PROTOCOL` environment variable:

- **http/streamable-http**: Standard HTTP for request-response communication (both use the same implementation)
- **sse**: Server-Sent Events (SSE) for event-driven communication (deprecated)

**Note**: Both **http** and **streamable-http** protocols use the same HTTP implementation and are functionally identical. We recommend using **http** or **streamable-http** for most use cases as they provide the best compatibility and performance. The **SSE protocol** is deprecated and should only be used if specifically required for legacy clients like Goose users on Linux desktop environments.

## 6. Usage (Run locally)

### Method 1: Using Python directly

```bash
# Run the server
python -m template_mcp_server.src.main
```

### Method 2: Using the installed script

```bash
# After installation, you can run the server using the installed script
template-mcp-server
```

### Method 3: Using Podman Container

```bash
# Build the container
podman build -t template-mcp-server .

# Run the container
podman run -d --name mcp-server -p 3000:3000 template-mcp-server

# View logs
podman logs -f mcp-server

# Stop the container
podman stop mcp-server && podman rm mcp-server
```

## 7. Server Endpoints

Once the server is running, it will be available at:

### 7.1 HTTP Protocol (http/streamable-http)

- **MCP Server**: `http://0.0.0.0:3000/mcp`
- **Health Check**: `http://0.0.0.0:3000/health`

### 7.2 SSE Protocol

- **SSE Endpoint**: `http://0.0.0.0:3000/sse`
- **Health Check**: `http://0.0.0.0:3000/health`

## 8. Deploy on OpenShift

The project includes complete OpenShift deployment configurations in the `openshift/` directory:

```bash
# Create the namespace
oc apply -f openshift/tenant.yaml

# Apply the deployment
oc apply -k openshift/

# Check deployment status
oc get pods -n ddis-asteroid--template

# View logs
oc logs -f deployment/template-mcp-server
```

### Server Endpoints

Once the server is running, it will be available at:

#### HTTP Protocol (http/streamable-http)

- **MCP Server**: `https://template-mcp-server.apps.int.spoke.preprod.us-west-2.aws.paas.redhat.com/mcp`
- **Health Check**: `https://template-mcp-server.apps.int.spoke.preprod.us-west-2.aws.paas.redhat.com/health`

#### SSE Protocol

- **SSE Endpoint**: `https://template-mcp-server.apps.int.spoke.preprod.us-west-2.aws.paas.redhat.com/sse`
- **Health Check**: `https://template-mcp-server.apps.int.spoke.preprod.us-west-2.aws.paas.redhat.com/health`

### OpenShift Configuration

- **Namespace**: `ddis-asteroid--template`
- **Port**: 8443 (HTTPS)
- **SSL**: Configured with TLS certificates
- **Resources**: 1 CPU, 1Gi memory
- **Health Checks**: Liveness and readiness probes configured

## 9. Examples

### FastMCP Client Example

```bash
# Run the FastMCP client example
python examples/fastmcp_client.py
```

This example demonstrates:
- Connecting to the MCP server
- Using available tools (multiply_numbers)
- Accessing resources (Red Hat logo)
- Using prompts (code review)

### LangGraph Client Example

```bash
# Run the LangGraph client example
python examples/langgraph_client.py
```

This example shows:
- LangGraph agent integration
- Google Gemini model usage
- Tool calls for mathematical operations
- Conversational AI workflows

## 10. How to Customize the Template

### Adding New Tools

1. Create a new tool file in `template_mcp_server/src/tools/`:

```python
# template_mcp_server/src/tools/my_tool.py
from typing import Any, Dict

def my_custom_tool(param1: str, param2: int) -> Dict[str, Any]:
    """My custom tool description."""
    # Your tool logic here
    return {
        "status": "success",
        "result": "your_result"
    }
```

2. Register the tool in `template_mcp_server/src/mcp.py`:

```python
from template_mcp_server.src.tools.my_tool import my_custom_tool

def _register_mcp_tools(self) -> None:
    self.mcp.tool()(multiply_numbers)
    self.mcp.tool()(my_custom_tool)  # Add your tool here
```

### Adding New Resources

**Note**: Resources have limited client support. Most popular MCP clients like LangGraph and CrewAI do not support MCP resources. Only implement resources if absolutely necessary for your specific use case.

1. Create a resource file in `template_mcp_server/src/resources/`:

```python
# template_mcp_server/src/resources/my_resource.py
def read_my_resource_content() -> str:
    """Read content from my resource."""
    return "Your resource content"
```

2. Register the resource in `template_mcp_server/src/mcp.py`:

```python
from template_mcp_server.src.resources.my_resource import read_my_resource_content

def _register_mcp_resources(self) -> None:
    self.mcp.resource("resource://my-resource")(read_my_resource_content)
```

### Adding New Prompts

**Note**: Prompts have limited client support. Most popular MCP clients like LangGraph and CrewAI do not support MCP prompts. Only implement prompts if absolutely necessary for your specific use case.

1. Create a prompt file in `template_mcp_server/src/prompts/`:

```python
# template_mcp_server/src/prompts/my_prompt.py
def get_my_prompt(code: str, language: str) -> str:
    """Generate a custom prompt."""
    return f"Review this {language} code: {code}"
```

2. Register the prompt in `template_mcp_server/src/mcp.py`:

```python
from template_mcp_server.src.prompts.my_prompt import get_my_prompt

def _register_mcp_prompts(self) -> None:
    self.mcp.prompt()(get_my_prompt)
```

### Updating Configuration

1. Add new environment variables to `template_mcp_server/src/settings.py`:

```python
class Settings(BaseSettings):
    # Existing settings...

    MY_CUSTOM_VAR: str = Field(
        default="default_value",
        json_schema_extra={
            "env": "MY_CUSTOM_VAR",
            "description": "Description of your custom variable"
        }
    )
```

2. Update `.env.template` with your new variables:

```env
# Existing variables...
MY_CUSTOM_VAR=your_value
```

### Customizing the Server

1. **Update server behavior**: Modify `template_mcp_server/src/mcp.py`
2. **Add middleware**: Update `template_mcp_server/src/api.py`
3. **Customize logging**: Modify `template_mcp_server/utils/pylogger.py`
4. **Add authentication**: Extend the FastAPI app in `template_mcp_server/src/api.py`

### Testing Your Changes

```bash
# Run tests for your new components
pytest tests/test_tools.py -k "test_my_tool"
pytest tests/test_resources.py -k "test_my_resource"
pytest tests/test_prompts.py -k "test_my_prompt"

# Run all tests to ensure nothing is broken
pytest
```

### Container Testing

The project includes comprehensive container tests in `tests/test_container.py` that verify:

- **Rootless container build** with Red Hat UBI Python 3.12
- **Container execution** and health verification
- **SSL/HTTPS configuration** capability
- **Production deployment** readiness

```bash
# Run all container tests (requires podman)
pytest tests/test_container.py -v

# Test specific functionality
pytest tests/test_container.py::TestContainerBuild -v          # Build verification
pytest tests/test_container.py::TestContainerExecution -v     # Runtime testing
pytest tests/test_container.py::TestContainerConfiguration -v # Config validation
pytest tests/test_container.py::TestProductionDeployment -v   # Production readiness
```

**Container Features Tested:**
- ✅ Red Hat UBI base image compliance
- ✅ Rootless operation (no root user required)
- ✅ Virtual environment isolation
- ✅ Red Hat certificate integration
- ✅ HTTP/HTTPS server startup
- ✅ Source code structure validation
- ✅ Podman build and execution validation

**Requirements:**
- `podman` must be available (Red Hat's container engine)
- Network access for base image download
- ~2-3 minutes for initial build

### Client Compatibility Considerations

When designing your MCP server, consider the following client compatibility:

- **✅ Tools**: Supported by most MCP clients including LangGraph, CrewAI, and others
- **⚠️ Resources**: Limited support - only implement if absolutely necessary
- **⚠️ Prompts**: Limited support - only implement if absolutely necessary

**Recommendation**: Focus on implementing MCP tools as they have the broadest client support and are the most reliable way to extend MCP server functionality.

## 11. AI Development Assistant

This template includes `.cursor/rules.md` - a comprehensive development guide specifically designed to help AI coding assistants understand and work effectively with this MCP server template.

### What's Included

The `.cursor/rules.md` file provides:
- **Enterprise containerization patterns** (Podman, Red Hat UBI, rootless containers)
- **MCP development best practices** (tool design, error handling, testing patterns)
- **FastAPI + MCP integration examples** with real code snippets
- **Container testing strategies** matching our `test_container.py` implementation
- **AI assistant guidelines** for working with this specific template architecture

### Usage Options

You have several options for the `.cursor/rules.md` file:

1. **Keep it**: Use as-is to help AI assistants understand your project structure
2. **Customize it**: Modify the file to reflect your specific deployment needs and patterns
3. **Remove it**: Delete the file if you don't need AI development assistance
4. **Contribute improvements**: Submit merge requests with enhancements or fixes

### Contributing

We welcome contributions to improve the AI development assistance:
- **Bug fixes** for incorrect patterns or outdated information
- **New patterns** for common MCP server development scenarios
- **Documentation improvements** for better AI assistant guidance
- **Tool integration examples** for additional development workflows

Submit your improvements via merge request - we value innovations in this area!

### Deployment Considerations

1. **Update container configuration**: Modify `Containerfile` (optimized for Podman/Buildah)
2. **Update OpenShift configs**: Modify files in `openshift/` directory
3. **Update dependencies**: Add new requirements to `pyproject.toml`
4. **Test container changes**: Run `pytest tests/test_container.py -v`
5. **Update documentation**: Modify this README to reflect your changes
