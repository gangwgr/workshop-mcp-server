"""Tests for the tools module."""

from unittest.mock import patch

import pytest

from template_mcp_server.src.tools.multiply_tool import multiply_numbers


class TestMultiplyTool:
    """Test the multiply_numbers tool."""

    def test_multiply_numbers_success(self):
        """Test successful multiplication of two numbers."""
        # Arrange
        a, b = 5.0, 3.0

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert result["status"] == "success"
        assert result["operation"] == "multiplication"
        assert result["a"] == 5.0
        assert result["b"] == 3.0
        assert result["result"] == 15.0
        assert result["message"] == "Successfully multiplied 5.0 and 3.0"

    def test_multiply_numbers_integers(self):
        """Test multiplication with integer inputs."""
        # Arrange
        a, b = 10, 7

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert result["status"] == "success"
        assert result["result"] == 70
        assert result["a"] == 10
        assert result["b"] == 7

    def test_multiply_numbers_negative_values(self):
        """Test multiplication with negative values."""
        # Arrange
        a, b = -5.0, 3.0

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert result["status"] == "success"
        assert result["result"] == -15.0

    def test_multiply_numbers_zero(self):
        """Test multiplication with zero."""
        # Arrange
        a, b = 10.0, 0.0

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert result["status"] == "success"
        assert result["result"] == 0.0

    def test_multiply_numbers_float_precision(self):
        """Test multiplication with floating point precision."""
        # Arrange
        a, b = 0.1, 0.2

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert result["status"] == "success"
        assert result["result"] == pytest.approx(0.02, rel=1e-10)

    def test_multiply_numbers_invalid_input_string(self):
        """Test multiplication with invalid string input."""
        # Arrange
        a, b = "5", 3.0

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert result["status"] == "error"
        assert "error" in result
        assert "Failed to perform multiplication" in result["message"]

    def test_multiply_numbers_invalid_input_none(self):
        """Test multiplication with None input."""
        # Arrange
        a, b = None, 3.0

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert result["status"] == "error"
        assert "error" in result
        assert "Failed to perform multiplication" in result["message"]

    def test_multiply_numbers_invalid_input_list(self):
        """Test multiplication with list input."""
        # Arrange
        a, b = [1, 2], 3.0

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert result["status"] == "error"
        assert "error" in result
        assert "Failed to perform multiplication" in result["message"]

    def test_multiply_numbers_both_invalid_inputs(self):
        """Test multiplication with both inputs invalid."""
        # Arrange
        a, b = "invalid", "also_invalid"

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert result["status"] == "error"
        assert "error" in result
        assert "Failed to perform multiplication" in result["message"]

    @patch("template_mcp_server.src.tools.multiply_tool.logger")
    def test_multiply_numbers_logging_success(self, mock_logger):
        """Test that successful multiplication is logged."""
        # Arrange
        a, b = 5.0, 3.0

        # Act
        multiply_numbers(a, b)

        # Assert
        mock_logger.info.assert_called_with("Multiply tool called: 5.0 * 3.0 = 15.0")

    @patch("template_mcp_server.src.tools.multiply_tool.logger")
    def test_multiply_numbers_logging_error(self, mock_logger):
        """Test that errors are logged."""
        # Arrange
        a, b = "invalid", 3.0

        # Act
        multiply_numbers(a, b)

        # Assert
        mock_logger.error.assert_called()

    def test_multiply_numbers_return_type(self):
        """Test that the function returns a dictionary."""
        # Arrange
        a, b = 5.0, 3.0

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert isinstance(result, dict)
        assert "status" in result
        assert "operation" in result
        assert "a" in result
        assert "b" in result
        assert "result" in result
        assert "message" in result

    def test_multiply_numbers_error_return_structure(self):
        """Test that error responses have the correct structure."""
        # Arrange
        a, b = "invalid", 3.0

        # Act
        result = multiply_numbers(a, b)

        # Assert
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "error" in result
        assert "message" in result
        assert "Failed to perform multiplication" in result["message"]

    def test_multiply_numbers_commutative_property(self):
        """Test that multiplication is commutative."""
        # Arrange
        a, b = 5.0, 3.0

        # Act
        result1 = multiply_numbers(a, b)
        result2 = multiply_numbers(b, a)

        # Assert
        assert result1["result"] == result2["result"]
        assert result1["status"] == "success"
        assert result2["status"] == "success"
