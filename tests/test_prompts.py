"""Tests for the prompts module."""

from unittest.mock import Mock

from template_mcp_server.src.prompts.code_review_prompt import get_code_review_prompt


class TestCodeReviewPrompt:
    """Test the code review prompt functionality."""

    def test_get_code_review_prompt_basic(self):
        """Test basic code review prompt generation."""
        # Arrange
        code = "def add(a, b): return a + b"
        language = "python"

        # Act
        result = get_code_review_prompt(code, language)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "content" in result[0]
        assert code in result[0]["content"]
        assert language in result[0]["content"]

    def test_get_code_review_prompt_default_language(self):
        """Test code review prompt with default language."""
        # Arrange
        code = "function add(a, b) { return a + b; }"

        # Act
        result = get_code_review_prompt(code)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "python" in result[0]["content"]  # Default language
        assert code in result[0]["content"]

    def test_get_code_review_prompt_different_language(self):
        """Test code review prompt with different language."""
        # Arrange
        code = "function add(a, b) { return a + b; }"
        language = "javascript"

        # Act
        result = get_code_review_prompt(code, language)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert language in result[0]["content"]
        assert code in result[0]["content"]

    def test_get_code_review_prompt_with_context(self):
        """Test code review prompt with context parameter."""
        # Arrange
        code = "def multiply(x, y): return x * y"
        language = "python"
        mock_context = Mock()

        # Act
        result = get_code_review_prompt(code, language, mock_context)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        mock_context.info.assert_called_with(
            "Generating code review prompt for python code"
        )

    def test_get_code_review_prompt_without_context(self):
        """Test code review prompt without context parameter."""
        # Arrange
        code = "def divide(a, b): return a / b"
        language = "python"

        # Act
        result = get_code_review_prompt(code, language, None)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_get_code_review_prompt_content_structure(self):
        """Test that the prompt content has the expected structure."""
        # Arrange
        code = "def test_function(): pass"
        language = "python"

        # Act
        result = get_code_review_prompt(code, language)
        content = result[0]["content"]

        # Assert
        assert "Please review the following" in content
        assert f"```{language}" in content
        assert code in content
        assert "Focus on:" in content
        assert "Code quality and readability" in content
        assert "Potential bugs or issues" in content
        assert "Best practices" in content
        assert "Performance considerations" in content

    def test_get_code_review_prompt_empty_code(self):
        """Test code review prompt with empty code."""
        # Arrange
        code = ""
        language = "python"

        # Act
        result = get_code_review_prompt(code, language)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert code in result[0]["content"]

    def test_get_code_review_prompt_long_code(self):
        """Test code review prompt with long code."""
        # Arrange
        code = "def very_long_function_name_with_many_parameters(a, b, c, d, e, f, g, h, i, j):\n    return a + b + c + d + e + f + g + h + i + j"
        language = "python"

        # Act
        result = get_code_review_prompt(code, language)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert code in result[0]["content"]

    def test_get_code_review_prompt_special_characters(self):
        """Test code review prompt with special characters in code."""
        # Arrange
        code = "def special_chars(): return '!@#$%^&*()'"
        language = "python"

        # Act
        result = get_code_review_prompt(code, language)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert code in result[0]["content"]

    def test_get_code_review_prompt_multiline_code(self):
        """Test code review prompt with multiline code."""
        # Arrange
        code = """def complex_function():
    if condition:
        do_something()
    else:
        do_something_else()
    return result"""
        language = "python"

        # Act
        result = get_code_review_prompt(code, language)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert code in result[0]["content"]

    def test_get_code_review_prompt_return_type(self):
        """Test that the function returns the correct type."""
        # Arrange
        code = "def test(): pass"
        language = "python"

        # Act
        result = get_code_review_prompt(code, language)

        # Assert
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_get_code_review_prompt_message_structure(self):
        """Test that each message in the result has the correct structure."""
        # Arrange
        code = "def test(): pass"
        language = "python"

        # Act
        result = get_code_review_prompt(code, language)

        # Assert
        assert len(result) == 1
        message = result[0]
        assert "role" in message
        assert "content" in message
        assert message["role"] == "user"
        assert isinstance(message["content"], str)

    def test_get_code_review_prompt_function_signature(self):
        """Test that the function has the correct signature."""
        # Assert
        import inspect

        sig = inspect.signature(get_code_review_prompt)
        assert len(sig.parameters) == 3
        assert "code" in sig.parameters
        assert "language" in sig.parameters
        assert "context" in sig.parameters
        assert sig.parameters["language"].default == "python"
        assert sig.parameters["context"].default is None

    def test_get_code_review_prompt_various_languages(self):
        """Test code review prompt with various programming languages."""
        # Arrange
        test_cases = [
            ("python", "def test(): pass"),
            ("javascript", "function test() {}"),
            ("java", "public void test() {}"),
            ("cpp", "void test() {}"),
            ("go", "func test() {}"),
            ("rust", "fn test() {}"),
        ]

        for language, code in test_cases:
            # Act
            result = get_code_review_prompt(code, language)

            # Assert
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["role"] == "user"
            assert language in result[0]["content"]
            assert code in result[0]["content"]

    def test_get_code_review_prompt_context_logging(self):
        """Test that context logging works correctly."""
        # Arrange
        code = "def test(): pass"
        language = "python"
        mock_context = Mock()

        # Act
        get_code_review_prompt(code, language, mock_context)

        # Assert
        mock_context.info.assert_called_once_with(
            "Generating code review prompt for python code"
        )

    def test_get_code_review_prompt_no_context_logging(self):
        """Test that no logging occurs when context is None."""
        # Arrange
        code = "def test(): pass"
        language = "python"

        # Act & Assert - should not raise any exceptions
        result = get_code_review_prompt(code, language, None)
        assert result is not None
