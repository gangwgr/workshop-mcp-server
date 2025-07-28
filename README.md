# Template MCP Server

A Model Context Protocol (MCP) server template that provides a foundation for building MCP servers. This template can be customized for various data operations and management functionality.


## Installation

### Prerequisites

- uv (install it from https://docs.astral.sh/uv/getting-started/installation/)

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
```

## Environment file

Create a `.env` file in the project root:

```env
MCP_HOST=0.0.0.0
MCP_PORT=4000
PYTHON_LOG_LEVEL=INFO
MCP_TRANSPORT_PROTOCOL=streamable-http
# Add your custom environment variables here
# SNOWFLAKE_ACCOUNT=your_snowflake_account
# SNOWFLAKE_USER=your_snowflake_user
# GOOGLE_APPLICATION_CREDENTIALS_CONTENT='{
#     "type": "service_account",
#     ...
#     "universe_domain": "googleapis.com"
#   }'

```

### Transport Protocols

The server supports multiple transport protocols that can be configured via the `MCP_TRANSPORT_PROTOCOL` environment variable:

- **streamable-http** (default): Uses streamable HTTP for real-time communication
- **sse**: Uses Server-Sent Events (SSE) for event-driven communication
- **http**: Uses standard HTTP for request-response communication
- **stdio**: Uses standard input/output for local communication (doesn't require a web server)

**Note**: The `stdio` protocol is different from the HTTP-based protocols:
- It doesn't use a web server (uvicorn)
- It communicates directly through standard input/output
- It's typically used for local development, testing, and CLI applications
- No port configuration is needed for stdio

## Usage

### Starting the server

#### Method 1: Using Python directly

```bash
# Run the server
python -m template_mcp_server.src.main
```

#### Method 2: Using the installed script

```bash
# After installation, you can run the server using the installed script
template-mcp-server
```


### Server Endpoints

Once the server is running, it will be available at:

- **MCP Server**: `http://0.0.0.0:4000/mcp`
- **Health Check**: `http://0.0.0.0:4000/health`

**For SSE protocol:**
- **SSE Endpoint**: `http://0.0.0.0:4000/sse`
- **Message Endpoint**: `http://0.0.0.0:4000/mcp/message`

### Testing Transport Protocols

You can test different transport protocols using the provided example script:

```bash
# Run the example script to test all transport protocols
python run_mcp_server_with_protocol.py
```

This script will start the server with each transport protocol and show the available endpoints.

## Customizing the Template

This is a template MCP server that you can customize for your specific needs:

1. **Add your own tools**: Create new tool files in `template_mcp_server/src/tools/`
2. **Update configuration**: Modify `template_mcp_server/src/settings.py` to add your environment variables
3. **Customize the server**: Update `template_mcp_server/src/server.py` to register your tools
4. **Update documentation**: Modify this README to reflect your specific use case

### Available Tools

The template includes several example tools:

1. **Multiply Tool** (`multiply_tool.py`): Demonstrates basic arithmetic operations
2. **Authorization Tool** (`authorization_tool.py`): Shows how to implement user permission checks
3. **Resource Tools** (`redhat_logo.py`): Demonstrates how to work with file resources

### Example Tool Structure

See `template_mcp_server/src/tools/multiply_tool.py` for an example of how to create MCP tools.

### Resources

The template includes a resources system for managing files and assets:

- **Assets Directory**: `template_mcp_server/assets/` - Store your resource files here
- **Resource Functions**: Access and manage resources through MCP tools
- **File Management**: Built-in functions to list and access available resources
