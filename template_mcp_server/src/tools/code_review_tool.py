"""Code review tool for the Template MCP Server.

This tool provides functionality to generate code review prompts
for various programming languages as an MCP tool.
"""

from typing import Any, Dict

from template_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


def generate_code_review_prompt(
    code: str,
    language: str = "python",
) -> Dict[str, Any]:
    """Generate a code review prompt as a tool.

    Creates a structured prompt for code review that can be used with
    language models to analyze code quality, identify issues, and suggest
    improvements.

    Args:
        code: The source code to be reviewed.
        language: Programming language of the code (default: "python").

    Returns:
        Dict[str, Any]: A dictionary containing the formatted code review
            prompt and metadata.
    """
    try:
        # Validate inputs
        if not code or not isinstance(code, str):
            raise ValueError("Code must be a non-empty string")

        if not language or not isinstance(language, str):
            raise ValueError("Language must be a non-empty string")

        logger.info(f"Generating code review prompt for {language} code")

        prompt_content = f"""Please review the following {language} code:

```{language}
{code}
```

Focus on:
- Code quality and readability
- Potential bugs or issues
- Best practices
- Performance considerations
"""

        return {
            "status": "success",
            "operation": "code_review_prompt",
            "language": language,
            "prompt": prompt_content,
            "message": f"Successfully generated code review prompt for {language}",
        }

    except Exception as e:
        logger.error(f"Error in code review tool: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate code review prompt",
        }
