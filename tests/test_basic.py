"""Basic tests for the Template MCP Server."""

import importlib
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import template_mcp_server.src.settings as settings_mod


class TestSettings:
    """Test settings configuration."""

    def test_default_settings(self):
        """Test that default settings are correct."""
        import template_mcp_server.src.settings as settings_mod

        importlib.reload(settings_mod)
        settings = settings_mod.settings

        assert settings.MCP_HOST == "0.0.0.0"
        assert settings.MCP_PORT == 4000
        assert settings.PYTHON_LOG_LEVEL == "INFO"
        assert settings.MCP_SSL_KEYFILE is None
        assert settings.MCP_SSL_CERTFILE is None
        assert settings.MCP_TRANSPORT_PROTOCOL == "streamable-http"

    def test_port_validation(self):
        """Test that port validation works correctly."""
        import template_mcp_server.src.settings as settings_mod

        importlib.reload(settings_mod)
        settings = settings_mod.settings

        # Test valid port range
        assert 1024 <= settings.MCP_PORT <= 65535

    def test_log_level_validation(self):
        """Test that log level validation works correctly."""
        import template_mcp_server.src.settings as settings_mod

        importlib.reload(settings_mod)
        settings = settings_mod.settings

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert settings.PYTHON_LOG_LEVEL.upper() in valid_levels

    def test_transport_protocol_validation(self):
        """Test that transport protocol validation works correctly."""
        import template_mcp_server.src.settings as settings_mod

        importlib.reload(settings_mod)
        settings = settings_mod.settings

        valid_protocols = ["stdio", "streamable-http", "sse", "http"]
        assert settings.MCP_TRANSPORT_PROTOCOL in valid_protocols


class TestServer:
    """Test server functionality."""

    @pytest.fixture(autouse=True)
    def patch_snowflake_account(self, monkeypatch):
        monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "dummy_account")
        import template_mcp_server.src.settings as settings_mod

        importlib.reload(settings_mod)
        import template_mcp_server.src.mcp as server_mod

        importlib.reload(server_mod)
        self.TemplateMCPServer = server_mod.TemplateMCPServer

    def test_server_initialization(self):
        """Test that server can be initialized."""
        server = self.TemplateMCPServer()
        assert server is not None
        assert hasattr(server, "mcp")
        assert hasattr(server, "_register_mcp_tools")

    def test_server_has_mcp_tools(self):
        """Test that server has MCP tools registered."""
        server = self.TemplateMCPServer()
        assert hasattr(server, "_register_mcp_tools")

    def test_server_mcp_instance(self):
        """Test that server has a valid FastMCP instance."""
        server = self.TemplateMCPServer()
        assert server.mcp is not None
        assert hasattr(server.mcp, "tool")

    def test_transport_protocol_configuration(self):
        """Test that different transport protocols can be configured."""
        # Test with streamable-http (default)
        with patch.dict(os.environ, {"MCP_TRANSPORT_PROTOCOL": "streamable-http"}):
            importlib.reload(settings_mod)
            settings = settings_mod.settings
            assert settings.MCP_TRANSPORT_PROTOCOL == "streamable-http"

        # Test with sse
        with patch.dict(os.environ, {"MCP_TRANSPORT_PROTOCOL": "sse"}):
            importlib.reload(settings_mod)
            settings = settings_mod.settings
            assert settings.MCP_TRANSPORT_PROTOCOL == "sse"

        # Test with http
        with patch.dict(os.environ, {"MCP_TRANSPORT_PROTOCOL": "http"}):
            importlib.reload(settings_mod)
            settings = settings_mod.settings
            assert settings.MCP_TRANSPORT_PROTOCOL == "http"

        # Test with stdio
        with patch.dict(os.environ, {"MCP_TRANSPORT_PROTOCOL": "stdio"}):
            importlib.reload(settings_mod)
            settings = settings_mod.settings
            assert settings.MCP_TRANSPORT_PROTOCOL == "stdio"


class TestAPI:
    """Test API endpoints."""

    def test_health_endpoint(self):
        """Test that the health endpoint returns the expected response."""
        from template_mcp_server.src.api import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "template-mcp-server"
        assert "transport_protocol" in data
        assert data["version"] == "0.1.0"


class TestMain:
    """Test main module functionality."""

    def test_main_module_import(self):
        """Test that main module can be imported."""
        import template_mcp_server.src.main as main

        assert main is not None

    def test_main_functions_exist(self):
        """Test that main functions exist."""
        import template_mcp_server.src.main as main

        assert hasattr(main, "main")
        assert hasattr(main, "run")
        assert hasattr(main, "validate_config")
        assert hasattr(main, "handle_startup_error")


if __name__ == "__main__":
    pytest.main([__file__])
