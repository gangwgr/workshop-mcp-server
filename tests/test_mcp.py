"""Tests for the MCP server module."""

from unittest.mock import Mock, patch

import pytest

from template_mcp_server.src.mcp import TemplateMCPServer


class TestTemplateMCPServer:
    """Test the TemplateMCPServer class."""

    @patch("template_mcp_server.src.mcp.FastMCP")
    @patch("template_mcp_server.src.mcp.logger")
    def test_init_success(self, mock_logger, mock_fastmcp):
        """Test successful initialization of TemplateMCPServer."""
        # Arrange
        mock_mcp = Mock()
        mock_fastmcp.return_value = mock_mcp

        # Act
        server = TemplateMCPServer()

        # Assert
        assert server.mcp == mock_mcp
        mock_logger.info.assert_called_with(
            "Template MCP Server initialized successfully"
        )
        mock_mcp.tool.assert_called()
        mock_mcp.resource.assert_called()
        mock_mcp.prompt.assert_called()

    @patch("template_mcp_server.src.mcp.FastMCP")
    @patch("template_mcp_server.src.mcp.logger")
    def test_init_failure(self, mock_logger, mock_fastmcp):
        """Test initialization failure handling."""
        # Arrange
        mock_fastmcp.side_effect = Exception("Test error")

        # Act & Assert
        with pytest.raises(Exception, match="Test error"):
            TemplateMCPServer()

        mock_logger.error.assert_called_with(
            "Failed to initialize Template MCP Server: Test error"
        )

    @patch("template_mcp_server.src.mcp.FastMCP")
    def test_register_mcp_tools(self, mock_fastmcp):
        """Test MCP tools registration."""
        # Arrange
        mock_mcp = Mock()
        mock_fastmcp.return_value = mock_mcp
        server = TemplateMCPServer()

        # Act
        server._register_mcp_tools()

        # Assert
        mock_mcp.tool.assert_called()

    @patch("template_mcp_server.src.mcp.FastMCP")
    def test_register_mcp_resources(self, mock_fastmcp):
        """Test MCP resources registration."""
        # Arrange
        mock_mcp = Mock()
        mock_fastmcp.return_value = mock_mcp
        server = TemplateMCPServer()

        # Act
        server._register_mcp_resources()

        # Assert
        mock_mcp.resource.assert_called_with("resource://redhat-logo")

    @patch("template_mcp_server.src.mcp.FastMCP")
    def test_register_mcp_prompts(self, mock_fastmcp):
        """Test MCP prompts registration."""
        # Arrange
        mock_mcp = Mock()
        mock_fastmcp.return_value = mock_mcp
        server = TemplateMCPServer()

        # Act
        server._register_mcp_prompts()

        # Assert
        mock_mcp.prompt.assert_called()

    def test_server_attributes(self):
        """Test that server has required attributes."""
        # Arrange & Act
        with patch("template_mcp_server.src.mcp.FastMCP"):
            server = TemplateMCPServer()

        # Assert
        assert hasattr(server, "mcp")
        assert hasattr(server, "_register_mcp_tools")
        assert hasattr(server, "_register_mcp_resources")
        assert hasattr(server, "_register_mcp_prompts")
