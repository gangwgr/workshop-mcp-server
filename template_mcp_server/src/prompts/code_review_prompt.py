"""Code review prompt module for the Template MCP Server.

This module provides functionality to generate code review prompts
for various programming languages using the MCP prompt system.
"""

from typing import Any, Dict, List

from fastmcp import Context


def get_code_review_prompt(
    code: str, language: str = "python", context: Context = None
) -> List[Dict[str, Any]]:
    """Generate a code review prompt.

    Args:
        code: The code to review
        language: Programming language of the code
        context: MCP context for logging and capabilities

    Returns:
        List of message objects for the prompt
    """
    if context:
        context.info(f"Generating code review prompt for {language} code")

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

    return [{"role": "user", "content": prompt_content}]
