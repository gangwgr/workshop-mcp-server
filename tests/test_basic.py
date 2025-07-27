"""Basic tests for the Template MCP Server."""

import importlib

import pytest


class TestConfig:
    """Test configuration settings."""

    @pytest.fixture(autouse=True)
    def patch_snowflake_account(self, monkeypatch):
        monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "dummy_account")
        import importlib

        import template_mcp_server.src.settings as settings_mod

        importlib.reload(settings_mod)
        self.settings = settings_mod.settings

    def test_config_defaults(self):
        settings = self.settings
        """Test that config has expected default values."""
        assert settings.MCP_HOST == "0.0.0.0"
        assert settings.MCP_PORT == 4000
        assert settings.PYTHON_LOG_LEVEL == "INFO"
        assert settings.MCP_SSL_KEYFILE is None
        assert settings.MCP_SSL_CERTFILE is None

    def test_config_port_range(self):
        settings = self.settings
        """Test that port is within valid range."""
        assert 1024 <= settings.MCP_PORT <= 65535

    def test_config_log_level(self):
        settings = self.settings
        """Test that log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert settings.PYTHON_LOG_LEVEL.upper() in valid_levels


class TestServer:
    """Test server functionality."""

    @pytest.fixture(autouse=True)
    def patch_snowflake_account(self, monkeypatch):
        monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "dummy_account")
        import template_mcp_server.src.settings as settings_mod

        importlib.reload(settings_mod)
        import template_mcp_server.src.server as server_mod

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


class TestMain:
    """Test main module functionality."""

    def test_import_main(self):
        """Test that main module can be imported."""
        from template_mcp_server.src import main

        assert main is not None

    def test_main_has_required_functions(self):
        """Test that main module has required functions."""
        from template_mcp_server.src import main

        assert hasattr(main, "main")
        assert hasattr(main, "run")
        assert hasattr(main, "validate_config")
        assert hasattr(main, "handle_startup_error")


if __name__ == "__main__":
    pytest.main([__file__])
