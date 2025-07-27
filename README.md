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
# Add your custom environment variables here
# SNOWFLAKE_ACCOUNT=your_snowflake_account
# SNOWFLAKE_USER=your_snowflake_user
# GOOGLE_APPLICATION_CREDENTIALS_CONTENT='{
#     "type": "service_account",
#     ...
#     "universe_domain": "googleapis.com"
#   }'

```


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

## Customizing the Template

This is a template MCP server that you can customize for your specific needs:

1. **Add your own tools**: Create new tool files in `template_mcp_server/src/tools/`
2. **Update configuration**: Modify `template_mcp_server/src/settings.py` to add your environment variables
3. **Customize the server**: Update `template_mcp_server/src/server.py` to register your tools
4. **Update documentation**: Modify this README to reflect your specific use case

### Example Tool Structure

See `template_mcp_server/src/tools/example_tool.py` for an example of how to create MCP tools.
