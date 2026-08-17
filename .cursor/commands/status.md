# LLM status

Use the `switch_llm_mode` MCP tool with mode `""` and model `""` only if needed, or call `ask_local_llm` with prompt "report current LLM config".

Prefer: use `switch_llm_mode` after reading config — report to the user:
- Current mode (ollama / claude / cursor / template)
- Current model name
- Whether LLM is available
- Whether CURSOR_API_KEY and ANTHROPIC_API_KEY are configured

Arguments (optional context): $ARGUMENTS
