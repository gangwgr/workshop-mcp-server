"""Tests for the resources module."""

import base64
from unittest.mock import Mock, mock_open, patch

import pytest

from template_mcp_server.src.resources.redhat_logo import read_redhat_logo_content


class TestRedHatLogo:
    """Test the Red Hat logo resource."""

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_png_data")
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_success(self, mock_path, mock_file):
        """Test successful reading of Red Hat logo."""
        # Arrange
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        # Act
        result = await read_redhat_logo_content()

        # Assert
        assert result["name"] == "Red Hat Logo"
        assert result["description"] == "Red Hat logo as base64 encoded PNG"
        assert result["mimeType"] == "image/png"
        assert isinstance(result["text"], str)
        assert len(result["text"]) > 0

    @pytest.mark.asyncio
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_file_not_found(self, mock_path):
        """Test handling when logo file is not found."""
        # Arrange
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            # Act
            result = await read_redhat_logo_content()

            # Assert
            assert result["name"] == "Red Hat Logo Error"
            assert result["description"] == "Could not find Red Hat logo file"
            assert result["mimeType"] == "text/plain"
            assert "Error: Could not find logo file" in result["text"]

    @pytest.mark.asyncio
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_permission_error(self, mock_path):
        """Test handling when logo file cannot be read due to permissions."""
        # Arrange
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Act
            result = await read_redhat_logo_content()

            # Assert
            assert result["name"] == "Red Hat Logo Error"
            assert result["description"] == "Error reading Red Hat logo file"
            assert result["mimeType"] == "text/plain"
            assert "Error: Permission denied" in result["text"]

    @pytest.mark.asyncio
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_generic_error(self, mock_path):
        """Test handling of generic errors when reading logo file."""
        # Arrange
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        with patch("builtins.open", side_effect=Exception("Generic error")):
            # Act
            result = await read_redhat_logo_content()

            # Assert
            assert result["name"] == "Red Hat Logo Error"
            assert result["description"] == "Error reading Red Hat logo file"
            assert result["mimeType"] == "text/plain"
            assert "Error: Generic error" in result["text"]

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_png_data")
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_base64_encoding(self, mock_path, mock_file):
        """Test that the logo data is properly base64 encoded."""
        # Arrange
        test_data = b"fake_png_data"
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        # Act
        result = await read_redhat_logo_content()

        # Assert
        expected_base64 = base64.b64encode(test_data).decode("utf-8")
        assert result["text"] == expected_base64

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_png_data")
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_return_structure(
        self, mock_path, mock_file
    ):
        """Test that the function returns the correct structure."""
        # Arrange
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        # Act
        result = await read_redhat_logo_content()

        # Assert
        required_keys = ["name", "description", "mimeType", "text"]
        for key in required_keys:
            assert key in result
            assert result[key] is not None

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_png_data")
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_async_function(self, mock_path, mock_file):
        """Test that the function is properly defined as async."""
        # Arrange
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        # Act
        result = await read_redhat_logo_content()

        # Assert
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_path_construction(self, mock_path):
        """Test that the file path is constructed correctly."""
        # Arrange
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        # Act
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            await read_redhat_logo_content()

        # Assert
        # Verify that the path construction was called
        mock_path_instance.parent.__truediv__.assert_called()

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_png_data")
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_empty_file(self, mock_path, mock_file):
        """Test handling of empty logo file."""
        # Arrange
        mock_file.return_value.read.return_value = b""
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        # Act
        result = await read_redhat_logo_content()

        # Assert
        assert result["name"] == "Red Hat Logo"
        assert result["text"] == ""  # Empty base64 string

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_png_data")
    @patch("template_mcp_server.src.resources.redhat_logo.Path")
    async def test_read_redhat_logo_content_large_file(self, mock_path, mock_file):
        """Test handling of large logo file."""
        # Arrange
        large_data = b"x" * 1000000  # 1MB of data
        mock_file.return_value.read.return_value = large_data
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Configure the mock to support path operations
        assets_dir = Mock()
        assets_dir.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value = assets_dir

        # Act
        result = await read_redhat_logo_content()

        # Assert
        assert result["name"] == "Red Hat Logo"
        assert len(result["text"]) > 0
        # Verify it's valid base64
        try:
            base64.b64decode(result["text"])
        except Exception:
            pytest.fail("Result is not valid base64")

    def test_read_redhat_logo_content_function_signature(self):
        """Test that the function has the correct signature."""
        # Assert
        import inspect

        sig = inspect.signature(read_redhat_logo_content)
        assert sig.return_annotation is dict
        assert len(sig.parameters) == 0  # No parameters
