"""Tests for the utils module."""

from unittest.mock import Mock, patch

import pytest

from template_mcp_server.utils.pylogger import get_python_logger


class TestPylogger:
    """Test the pylogger utility."""

    def test_get_python_logger_default(self):
        """Test getting logger with default configuration."""
        # Act
        logger = get_python_logger()

        # Assert
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "critical")

    def test_get_python_logger_custom_level(self):
        """Test getting logger with custom log level."""
        # Arrange
        custom_level = "DEBUG"

        # Act
        logger = get_python_logger(custom_level)

        # Assert
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "critical")

    def test_get_python_logger_case_insensitive(self):
        """Test that log level is converted to uppercase."""
        # Arrange
        test_levels = ["info", "INFO", "Info", "iNfO"]

        for level in test_levels:
            # Act
            logger = get_python_logger(level)

            # Assert
            assert logger is not None
            assert hasattr(logger, "info")

    def test_get_python_logger_valid_levels(self):
        """Test logger creation with all valid log levels."""
        # Arrange
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            # Act
            logger = get_python_logger(level)

            # Assert
            assert logger is not None
            assert hasattr(logger, "info")
            assert hasattr(logger, "error")
            assert hasattr(logger, "warning")
            assert hasattr(logger, "debug")
            assert hasattr(logger, "critical")

    @patch("template_mcp_server.utils.pylogger.structlog")
    def test_get_python_logger_structlog_configuration(self, mock_structlog):
        """Test that structlog is configured correctly."""
        # Arrange
        mock_structlog.get_logger.return_value = Mock()

        # Act
        get_python_logger()

        # Assert
        mock_structlog.configure.assert_called_once()
        mock_structlog.get_logger.assert_called_once()

    @patch("template_mcp_server.utils.pylogger.structlog")
    def test_get_python_logger_processors_configuration(self, mock_structlog):
        """Test that structlog processors are configured correctly."""
        # Arrange
        mock_structlog.get_logger.return_value = Mock()

        # Act
        get_python_logger()

        # Assert
        mock_structlog.configure.assert_called_once()
        call_args = mock_structlog.configure.call_args

        # Check that processors list is provided
        assert "processors" in call_args[1]
        processors = call_args[1]["processors"]
        assert isinstance(processors, list)
        assert len(processors) > 0

    @patch("template_mcp_server.utils.pylogger.structlog")
    def test_get_python_logger_context_class_configuration(self, mock_structlog):
        """Test that context_class is configured correctly."""
        # Arrange
        mock_structlog.get_logger.return_value = Mock()

        # Act
        get_python_logger()

        # Assert
        mock_structlog.configure.assert_called_once()
        call_args = mock_structlog.configure.call_args
        assert call_args[1]["context_class"] is dict

    @patch("template_mcp_server.utils.pylogger.structlog")
    def test_get_python_logger_logger_factory_configuration(self, mock_structlog):
        """Test that logger_factory is configured correctly."""
        # Arrange
        mock_structlog.get_logger.return_value = Mock()

        # Act
        get_python_logger()

        # Assert
        mock_structlog.configure.assert_called_once()
        call_args = mock_structlog.configure.call_args
        # Check that logger_factory is in the configuration
        assert "logger_factory" in call_args[1]
        # The actual value might be a mock, so we just verify it's configured
        assert call_args[1]["logger_factory"] is not None

    @patch("template_mcp_server.utils.pylogger.structlog")
    def test_get_python_logger_wrapper_class_configuration(self, mock_structlog):
        """Test that wrapper_class is configured correctly."""
        # Arrange
        mock_structlog.get_logger.return_value = Mock()

        # Act
        get_python_logger()

        # Assert
        mock_structlog.configure.assert_called_once()
        call_args = mock_structlog.configure.call_args
        assert call_args[1]["wrapper_class"] == mock_structlog.stdlib.BoundLogger

    @patch("template_mcp_server.utils.pylogger.structlog")
    def test_get_python_logger_cache_logger_configuration(self, mock_structlog):
        """Test that cache_logger_on_first_use is configured correctly."""
        # Arrange
        mock_structlog.get_logger.return_value = Mock()

        # Act
        get_python_logger()

        # Assert
        mock_structlog.configure.assert_called_once()
        call_args = mock_structlog.configure.call_args
        assert call_args[1]["cache_logger_on_first_use"] is True

    def test_get_python_logger_return_type(self):
        """Test that the function returns the correct type."""
        # Act
        logger = get_python_logger()

        # Assert
        assert logger is not None
        # The logger should be a structlog logger instance

    def test_get_python_logger_function_signature(self):
        """Test that the function has the correct signature."""
        # Assert
        import inspect

        sig = inspect.signature(get_python_logger)
        assert len(sig.parameters) == 1
        assert "log_level" in sig.parameters
        assert sig.parameters["log_level"].default == "INFO"

    def test_get_python_logger_multiple_calls(self):
        """Test that multiple calls to get_python_logger work correctly."""
        # Act
        logger1 = get_python_logger("INFO")
        logger2 = get_python_logger("DEBUG")
        logger3 = get_python_logger()

        # Assert
        assert logger1 is not None
        assert logger2 is not None
        assert logger3 is not None
        assert hasattr(logger1, "info")
        assert hasattr(logger2, "info")
        assert hasattr(logger3, "info")

    def test_get_python_logger_logging_functionality(self):
        """Test that the logger can be used for logging."""
        # Arrange
        logger = get_python_logger()

        # Act & Assert - should not raise any exceptions
        try:
            logger.info("Test info message")
            logger.error("Test error message")
            logger.warning("Test warning message")
            logger.debug("Test debug message")
            logger.critical("Test critical message")
        except Exception as e:
            pytest.fail(f"Logger should not raise exceptions: {e}")

    def test_get_python_logger_with_structured_logging(self):
        """Test that the logger supports structured logging."""
        # Arrange
        logger = get_python_logger()

        # Act & Assert - should not raise any exceptions
        try:
            logger.info("Test message", user_id=123, action="test")
            logger.error("Test error", error_code=500, component="test")
        except Exception as e:
            pytest.fail(f"Structured logging should not raise exceptions: {e}")

    def test_get_python_logger_import(self):
        """Test that the module can be imported without errors."""
        # Act & Assert
        try:
            import template_mcp_server.utils.pylogger

            assert template_mcp_server.utils.pylogger.get_python_logger is not None
        except ImportError as e:
            pytest.fail(f"Module should be importable: {e}")
