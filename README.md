# Template MCP Server

A modern, production-ready template for building [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers using [FastMCP](https://github.com/jlowin/fastmcp).

## ✨ Features

- 🐍 **Python 3.12** - Modern Python with latest features
- ⚡ **UV Package Manager** - Ultra-fast dependency management
- 🔧 **Multiple Entry Points** - Module, script, and development execution
- 🐨 **Container Ready** - Buildah/Podman support with Red Hat UBI
- 🚀 **CI/CD Pipeline** - GitLab CI with automated testing
- 📝 **Code Quality** - Pre-commit hooks with ruff, mypy, and pydocstyle
- 🔒 **Security First** - Non-root containers and dependency scanning
- 📚 **Well Documented** - Comprehensive documentation and examples

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) package manager

### Installation

1. **Clone this template:**
   ```bash
   git clone <this-repo>
   cd template-mcp-server
   ```

2. **Install with UV:**
   ```bash
   uv pip install -e .
   ```

3. **Set up development environment:**
   ```bash
   # Copy environment template
   cp .env.template .env
   # Edit .env with your settings
   
   # Install pre-commit hooks
   pre-commit install
   ```

## 🎯 Usage

### Multiple Ways to Run

```bash
# 1. As an installed module (recommended)
python -m src

# 2. Using script entry points
mcp-server
# or
template-mcp-server

# 3. Direct execution (development)
python src/main.py

# 4. With custom arguments
python -m src --transport http --port 8001 --host 0.0.0.0
```

### Transport Modes

**STDIO Mode** (default - for MCP clients):
```bash
python -m src --transport stdio
```

**HTTP Mode** (for testing/web integration):
```bash
python -m src --transport http --port 8000
```

## 📁 Project Structure

```
template-mcp-server/
├── src/                        # Main application package
│   ├── __init__.py            # Package version and metadata
│   ├── __main__.py            # Module entry point
│   ├── main.py                # Development entry point
│   ├── server.py              # FastMCP server with tools
│   └── config/                # Configuration modules
├── tests/                      # Test suite
├── .env.template              # Environment variables template
├── .pre-commit-config.yaml    # Code quality hooks
├── .gitlab-ci.yml             # CI/CD pipeline
├── Containerfile              # Container build instructions
├── .containerignore           # Container build exclusions
├── .gitignore                 # Git exclusions
└── pyproject.toml             # Project configuration
```

## 🛠️ Example Tools Included

This template provides **5 example tools** demonstrating different patterns:

- **`hello_world()`** - Simple greeting tool
- **`calculate_sum()`** - Math operations with Pydantic validation
- **`echo_message()`** - Message processing with metadata
- **`get_server_info()`** - Server introspection and health
- **`list_files()`** - Async file system operations

Plus **resources** and **prompts** examples for complete MCP functionality.

## ⚙️ Configuration

### Environment Variables

Copy `.env.template` to `.env` and customize:

```bash
# Server Configuration
SERVER_NAME="FastMCP Template Server"
SERVER_HOST="localhost"
SERVER_PORT="8000"

# Transport Mode (stdio, http)
TRANSPORT_MODE="stdio"

# Logging Configuration
LOG_LEVEL="INFO"

# Development Settings
DEBUG="false"

# Add your custom variables here
CUSTOM_API_KEY="your_api_key_here"
```

### Development Configuration

All tools support environment variable configuration with automatic loading.

## 🏗️ Development

### Code Quality

This template includes comprehensive code quality tools:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Format and lint
ruff check --fix src/ tests/
ruff format src/ tests/

# Type checking
mypy src/

# Run tests
pytest tests/ -v
```

### Adding New Tools

1. **Create your tool in `src/server.py`:**

```python
from pydantic import BaseModel

class MyToolInput(BaseModel):
    name: str
    count: int = 1

@mcp.tool()
def my_custom_tool(params: MyToolInput) -> Dict[str, Any]:
    """Description of what this tool does."""
    return {
        "result": f"Processed {params.name} {params.count} times",
        "success": True
    }
```

2. **Add tests in `tests/`:**

```python
def test_my_custom_tool():
    result = my_custom_tool(MyToolInput(name="test", count=3))
    assert result["success"] is True
```

3. **Run quality checks:**

```bash
pre-commit run --all-files
pytest
```

## 🐨 Container Deployment

### Building with Buildah/Podman

```bash
# Build the container
buildah build -t template-mcp-server .

# Or with Podman
podman build -t template-mcp-server .
```

### Running Containers

**STDIO mode** (for MCP clients):
```bash
podman run -it template-mcp-server
```

**HTTP mode** (for web services):
```bash
podman run -p 8000:8000 template-mcp-server \
  python -m src --transport http --host 0.0.0.0
```

**Production deployment:**
```bash
podman run -d --name mcp-server \
  --restart=unless-stopped \
  -p 8000:8000 \
  -e LOG_LEVEL="DEBUG" \
  template-mcp-server
```

### Container Features

- ✅ **Red Hat UBI Python 3.12** base image
- ✅ **Non-root user** for security
- ✅ **Health checks** built-in
- ✅ **Environment variable** configuration
- ✅ **Optimized layers** for fast builds

## 🚀 CI/CD Pipeline

Automated GitLab CI pipeline includes:

- **Code Quality**: Pre-commit hooks, linting, formatting
- **Testing**: Comprehensive test suite with pytest
- **Security**: Dependency scanning and validation
- **Performance**: Optimized builds with UV and caching

Pipeline runs on:
- Merge requests
- Main branch pushes
- Manual triggers

## 📚 API Reference

### Tool Categories

**Core Tools:**
- `hello_world()` - Basic greeting
- `get_server_info()` - Server metadata and health

**Data Processing:**
- `calculate_sum(a, b)` - Mathematical operations
- `echo_message(message)` - Message processing

**File Operations:**
- `list_files(path)` - Directory listing with metadata

### Resources

- `file://{path}` - Read file contents

### Prompts

- `code_review_prompt(code, language)` - Generate code review prompts

## 🔧 Customization

### 1. Replace Example Tools

Update `src/server.py` with your specific tools and business logic.

### 2. Configure Settings

Modify `src/config/` for your application-specific configuration.

### 3. Update Metadata

Edit `pyproject.toml` and `src/__init__.py` with your project details.

### 4. Customize Container

Update `Containerfile` for your deployment requirements.

## 📖 Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io/)
- [UV Package Manager](https://docs.astral.sh/uv/)
- [Red Hat UBI Images](https://catalog.redhat.com/software/containers/ubi9/python-312/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run quality checks: `pre-commit run --all-files`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using FastMCP, Python 3.12, and modern development practices.**