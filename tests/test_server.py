"""
Basic tests for the FastMCP template server.
"""

import pytest
from unittest.mock import patch
from src.server import mcp, CalculationInput, EchoInput, FilePathInput


class TestBasicTools:
    """Test basic MCP tools."""

    @pytest.mark.asyncio
    async def test_hello_world(self):
        """Test hello world tool."""
        tools = await mcp.get_tools()
        assert "hello_world" in tools
        
        # Test execution
        tool = tools["hello_world"]
        result = tool.fn()
        assert result == "Hello from FastMCP!"

    @pytest.mark.asyncio
    async def test_calculate_sum(self):
        """Test calculation tool."""
        tools = await mcp.get_tools()
        tool = tools["calculate_sum"]
        result = tool.fn(CalculationInput(a=2, b=3))
        assert result["result"] == 5
        assert "2.0 + 3.0 = 5.0" in result["calculation"]

    @pytest.mark.asyncio
    async def test_echo_message(self):
        """Test echo tool."""
        tools = await mcp.get_tools()
        tool = tools["echo_message"]
        result = tool.fn(EchoInput(message="test"))
        assert result["original"] == "test"
        assert result["echoed"] == "Echo: test"
        assert result["length"] == "4"

    @pytest.mark.asyncio
    async def test_get_server_info(self):
        """Test server info tool."""
        with patch('src.server.settings') as mock_settings:
            mock_settings.server_name = "Test Server"
            tools = await mcp.get_tools()
            tool = tools["get_server_info"]
            result = await tool.fn()
            assert result["name"] == "Test Server"
            assert result["status"] == "running"
            assert "tools_count" in result


class TestServerConfiguration:
    """Test server configuration."""

    def test_mcp_instance(self):
        """Test MCP instance is created properly."""
        assert mcp.name == "FastMCP Template Server"
        
    @pytest.mark.asyncio
    async def test_tools_registered(self):
        """Test that tools are registered."""
        tools = await mcp.get_tools()
        expected_tools = ["hello_world", "calculate_sum", "echo_message", "get_server_info", "list_files"]
        
        for expected in expected_tools:
            assert expected in tools


@pytest.mark.asyncio
async def test_list_files():
    """Test async file listing tool."""
    tools = await mcp.get_tools()
    tool = tools["list_files"]
    
    # Test with current directory
    result = await tool.fn(FilePathInput(path="."))
    assert "files" in result
    assert "count" in result
    assert isinstance(result["files"], list)

    # Test with non-existent path
    result = await tool.fn(FilePathInput(path="/nonexistent"))
    assert "error" in result


@pytest.mark.asyncio
async def test_read_file_resource():
    """Test file reading resource."""
    templates = await mcp.get_resource_templates()
    assert "file://{path}" in templates
    
    template = templates["file://{path}"]
    
    # Test reading this test file
    content = await template.fn(__file__)
    assert "TestBasicTools" in content
    
    # Test non-existent file
    content = await template.fn("/nonexistent/file.txt")
    assert "Error reading file" in content


@pytest.mark.asyncio
async def test_code_review_prompt():
    """Test code review prompt generation."""
    prompts = await mcp.get_prompts()
    assert "code_review_prompt" in prompts
    
    prompt = prompts["code_review_prompt"]
    
    code = "def hello(): return 'world'"
    result = prompt.fn(code, "python")
    
    assert "python" in result
    assert code in result
    assert "Code quality" in result