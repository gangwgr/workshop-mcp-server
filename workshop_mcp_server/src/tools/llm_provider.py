"""LLM Provider for MCP Server tools.

Supports multiple backends:
- ollama: Local Ollama (llama3, codellama, mistral, etc.)
- claude: Anthropic Claude API (sonnet, opus, haiku)
- template: No LLM, use pattern-based rules

Supports runtime mode switching without restart.
"""

import os
import requests
import json
from typing import Optional, Generator

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# Vertex AI settings (alternative to direct Anthropic API)
USE_VERTEX = os.environ.get("CLAUDE_CODE_USE_VERTEX", "").strip()
VERTEX_PROJECT_ID = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID", "")
VERTEX_REGION = os.environ.get("CLOUD_ML_REGION", "global")

# Vertex AI model name mapping
VERTEX_MODEL_MAP = {
    "sonnet": "claude-sonnet-4-5@20250929",
    "haiku": "claude-haiku-4-5@20251001",
    "opus": "claude-sonnet-4-5@20250929",
}

VALID_MODES = ("ollama", "claude", "template")

_runtime_config = {
    "mode": os.environ.get("LLM_MODE", "ollama"),
    "ollama_model": os.environ.get("OLLAMA_MODEL", "llama3"),
    "claude_model": os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5@20250929"),
}


def get_mode() -> str:
    return _runtime_config["mode"]


def set_mode(mode: str) -> None:
    if mode in VALID_MODES:
        _runtime_config["mode"] = mode


def get_model() -> str:
    mode = _runtime_config["mode"]
    if mode == "ollama":
        return _runtime_config["ollama_model"]
    elif mode == "claude":
        return _runtime_config["claude_model"]
    return "template"


def set_model(model: str) -> None:
    if not model:
        return
    mode = _runtime_config["mode"]
    if mode == "ollama":
        _runtime_config["ollama_model"] = model
    elif mode == "claude":
        _runtime_config["claude_model"] = model


def get_config() -> dict:
    return {
        "mode": _runtime_config["mode"],
        "model": get_model(),
        "ollama_model": _runtime_config["ollama_model"],
        "claude_model": _runtime_config["claude_model"],
        "ollama_url": OLLAMA_BASE_URL,
        "claude_configured": bool(ANTHROPIC_API_KEY),
    }


def is_available() -> bool:
    mode = _runtime_config["mode"]
    if mode == "template":
        return False
    if mode == "ollama":
        try:
            resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False
    if mode == "claude":
        api_key = os.environ.get("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY)
        use_vertex = os.environ.get("CLAUDE_CODE_USE_VERTEX", USE_VERTEX)
        vertex_project = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID", VERTEX_PROJECT_ID)
        return bool(api_key) or (bool(use_vertex) and bool(vertex_project))
    return False


def _generate_ollama(prompt: str, system: str, model: str,
                     temperature: float, max_tokens: int) -> Optional[str]:
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system:
            payload["system"] = system
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception:
        return None


def _generate_claude(prompt: str, system: str, model: str,
                     temperature: float, max_tokens: int) -> Optional[str]:
    # Check for Vertex AI path
    use_vertex = os.environ.get("CLAUDE_CODE_USE_VERTEX", USE_VERTEX)
    vertex_project = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID", VERTEX_PROJECT_ID)
    vertex_region = os.environ.get("CLOUD_ML_REGION", VERTEX_REGION)
    api_key = os.environ.get("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY)

    if use_vertex and vertex_project:
        return _generate_claude_vertex(prompt, system, model, temperature, max_tokens, vertex_project, vertex_region)

    if not api_key:
        return None
    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0]["text"]
        return None
    except Exception:
        return None


def _generate_claude_vertex(prompt: str, system: str, model: str,
                            temperature: float, max_tokens: int,
                            project_id: str, region: str) -> Optional[str]:
    """Call Claude via Google Cloud Vertex AI using the AnthropicVertex SDK."""
    try:
        from anthropic import AnthropicVertex

        # Map model name to Vertex-compatible model ID
        vertex_model = model
        if "@" not in model:
            for key, mapped in VERTEX_MODEL_MAP.items():
                if key in model.lower():
                    vertex_model = mapped
                    break

        client = AnthropicVertex(project_id=project_id, region=region)
        kwargs = {
            "model": vertex_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        msg = client.messages.create(**kwargs)
        if msg.content and msg.content[0].type == "text":
            return msg.content[0].text
        return None
    except Exception:
        return None


def generate(prompt: str, system: str = "", model: str = None,
             temperature: float = 0.7, max_tokens: int = 4096) -> Optional[str]:
    mode = _runtime_config["mode"]
    if mode == "template":
        return None

    if mode == "ollama":
        active_model = model or _runtime_config["ollama_model"]
        return _generate_ollama(prompt, system, active_model, temperature, max_tokens)

    if mode == "claude":
        active_model = model or _runtime_config["claude_model"]
        return _generate_claude(prompt, system, active_model, temperature, max_tokens)

    return None


# ============================================================
# Knowledge Base context helper
# ============================================================

def _get_kb_context(query: str, collections: list = None) -> str:
    """Fetch relevant KB context to enrich LLM prompts."""
    try:
        from workshop_mcp_server.src.tools.rag.kb_context import get_kb_context
        return get_kb_context(query, collections=collections, top_k=3, max_chars=2000)
    except Exception:
        return ""


def _get_review_feedback(code_snippet: str) -> str:
    """Fetch past review feedback to avoid repeating false positives."""
    try:
        from workshop_mcp_server.src.tools.rag.doc_ingester import get_review_feedback
        return get_review_feedback(code_snippet, top_k=3)
    except Exception:
        return ""


# ============================================================
# Specialized tool prompts (KB-enhanced)
# ============================================================

def review_code(code: str, language: str = "go", focus: list = None, is_pr_diff: bool = False, previous_issues: str = None) -> Optional[str]:
    focus_str = ", ".join(focus) if focus else "security, performance, bugs, style, best-practices"

    kb_context = _get_kb_context(f"{language} code review best practices OpenShift {focus_str}")

    # Re-review mode: only verify if previous issues were fixed
    if previous_issues:
        system = f"""You are verifying whether previously identified code issues have been fixed.

STRICT RULES — YOU MUST FOLLOW THESE:
1. You are given a NUMBERED LIST of specific issues found in a prior review.
2. Your ONLY job is to check each numbered issue and report: FIXED or NOT FIXED.
3. Do NOT add new issues, suggestions, style opinions, or recommendations.
4. Do NOT comment on code quality beyond the listed issues.
5. Do NOT suggest alternative approaches or improvements.
6. If all issues are fixed, simply confirm it — do not invent new concerns.
7. These rules apply regardless of which AI model performed the original review.

Format your response EXACTLY as:
## Re-Review: Issue Verification

| # | Issue | Status |
|---|-------|--------|
| 1 | <brief issue description> | ✅ FIXED / ❌ NOT FIXED |
| 2 | ... | ... |

## Verdict
- Fixed: <N>/<total>
- <If all fixed: "✅ All issues resolved — PR is ready to merge!">
- <If not all fixed: "❌ <N> issue(s) still need attention.">"""

        prompt_parts = []
        if kb_context:
            prompt_parts.append(f"Reference documentation from Knowledge Base:\n{kb_context}\n\n---\n")
        prompt_parts.append(f"## CHECKLIST — Verify ONLY these issues:\n\n{previous_issues}\n\n---\n")
        prompt_parts.append("## UPDATED CODE TO CHECK AGAINST:\n")
        if is_pr_diff:
            prompt_parts.append(f"{code}")
        else:
            prompt_parts.append(f"```{language}\n{code}\n```")
        prompt_parts.append("\n\nCheck EACH numbered issue above against the updated code. Report only FIXED or NOT FIXED for each one.")
        prompt = "\n".join(prompt_parts)
        return generate(prompt, system=system)

    if is_pr_diff:
        system = f"""You are an expert code reviewer for {language} specializing in OpenShift/Kubernetes, similar to CodeRabbit.
You are reviewing a Pull Request diff. Each line is prefixed with its real line number in the file (format: "LINE_NUM: code").
Lines starting with @@ are diff hunk headers showing context.
File boundaries are marked with "// ===== File: filename =====" headers.

IMPORTANT:
- Use the EXACT line numbers shown in the prefix when reporting issues.
- Only review the changed/added lines.
- Include the file name for each issue.
- For EACH issue, provide an actual CODE SUGGESTION showing the corrected code.

Provide a structured review focusing on: {focus_str}.

Format your response as:
## Summary
<overall assessment of the PR changes>

## Issues Found
For each issue:
- **Line <N>** (`filename`) [SEVERITY: critical/high/medium/low] [CATEGORY: security/performance/bug/style]
  - Issue: <description>
  - Suggestion: <text explanation of the fix>
  - Code suggestion:
    ```suggestion
    <the corrected code that should replace the problematic line(s)>
    ```

## Recommendations
<numbered list of improvements>

IMPORTANT for code suggestions:
- Use triple backticks with the word "suggestion" (like GitHub's suggestion format)
- Show ONLY the replacement code (what the line should become), not the original
- Keep the same indentation as the original code
- If the fix spans multiple lines, include all replacement lines"""
    else:
        system = f"""You are an expert code reviewer for {language} specializing in OpenShift/Kubernetes, similar to CodeRabbit.
Provide a structured line-by-line review focusing on: {focus_str}.
For EACH issue, provide an actual CODE SUGGESTION showing the corrected code.

Format your response as:
## Summary
<overall assessment>

## Issues Found
For each issue:
- **Line <N>** [SEVERITY: critical/high/medium/low] [CATEGORY: security/performance/bug/style]
  - Issue: <description>
  - Suggestion: <text explanation of the fix>
  - Code suggestion:
    ```suggestion
    <the corrected code that should replace the problematic line(s)>
    ```

## Recommendations
<numbered list of improvements>

IMPORTANT for code suggestions:
- Use triple backticks with the word "suggestion"
- Show ONLY the replacement code, not the original
- Keep the same indentation as the original code"""

    prompt_parts = []
    if kb_context:
        prompt_parts.append(f"Reference documentation from Knowledge Base:\n{kb_context}\n\n---\n")

    # Include past review feedback to avoid repeating false positives
    feedback_context = _get_review_feedback(code[:500])
    if feedback_context:
        prompt_parts.append(
            f"## PAST FEEDBACK — Do NOT flag these patterns (previously accepted by PR authors):\n"
            f"{feedback_context}\n\n---\n"
        )

    if is_pr_diff:
        prompt_parts.append(f"Review these PR changes ({language}):\n\n{code}")
    else:
        prompt_parts.append(f"Review this {language} code:\n\n```{language}\n{code}\n```")
    prompt = "\n".join(prompt_parts)
    return generate(prompt, system=system)


def generate_test_case(feature: str, component: str, scenario: str,
                       test_format: str = "go", description: str = "") -> Optional[str]:
    kb_context = _get_kb_context(f"OpenShift {component} {feature} test {test_format} {scenario}")

    system = f"""You are an expert OpenShift QA engineer generating {test_format} test cases.
Follow Red Hat OpenShift testing conventions and standards.
For Go tests, use Ginkgo/Gomega framework with proper Describe/It blocks.
For Gherkin, use proper Given/When/Then syntax.
For YAML, generate complete test manifests.
Always include proper cleanup/teardown steps."""

    parts = []
    if kb_context:
        parts.append(f"Reference from Knowledge Base:\n{kb_context}\n\n---\n")
    parts.append(f"Generate a {test_format} test case for:")
    parts.append(f"- Feature: {feature}")
    parts.append(f"- Component: {component}")
    parts.append(f"- Scenario: {scenario}")
    if description:
        parts.append(f"- Description: {description}")
    parts.append("\nGenerate production-ready, complete test code.")
    prompt = "\n".join(parts)
    return generate(prompt, system=system)


def debug_cluster_issue(issue: str, namespace: str = "", component: str = "",
                        diagnostic_data: str = "") -> Optional[str]:
    kb_query = f"OpenShift debug {issue}"
    if component:
        kb_query += f" {component}"
    if namespace:
        kb_query += f" {namespace}"
    kb_context = _get_kb_context(kb_query)

    system = """You are an expert OpenShift/Kubernetes cluster administrator and SRE.
Analyze cluster issues and provide:
1. Root cause analysis
2. Specific oc commands for further diagnosis
3. Step-by-step remediation
4. Prevention recommendations
5. A Go/Ginkgo test case to validate the fix

Format clearly with markdown headers and code blocks for commands."""

    parts = []
    if kb_context:
        parts.append(f"Relevant documentation from Knowledge Base:\n{kb_context}\n\n---\n")
    parts.append(f"Debug this OpenShift cluster issue:")
    parts.append(f"- Issue: {issue}")
    if namespace:
        parts.append(f"- Namespace: {namespace}")
    if component:
        parts.append(f"- Component: {component}")
    if diagnostic_data:
        parts.append(f"- Diagnostic data:\n{diagnostic_data}")
    parts.append("\nProvide root cause analysis, oc commands for diagnosis, fix steps, and a test case.")
    prompt = "\n".join(parts)
    return generate(prompt, system=system)


def analyze_mustgather(summary: str) -> Optional[str]:
    """LLM enhancement disabled — must-gather is offline-only; live runbooks are not appropriate."""
    return None


def generate_pr_review(diff: str, title: str = "", description: str = "") -> Optional[str]:
    kb_query = f"code review PR {title or 'OpenShift'}"
    kb_context = _get_kb_context(kb_query)

    system = """You are a senior OpenShift developer reviewing pull requests.
Provide constructive, specific feedback focusing on:
- Correctness and logic errors
- Security implications
- Performance impact
- Test coverage gaps
- API compatibility
Format as actionable review comments."""

    parts = []
    if kb_context:
        parts.append(f"Reference from Knowledge Base:\n{kb_context}\n\n---\n")
    parts.append("Review this PR:")
    if title:
        parts.append(f"Title: {title}")
    if description:
        parts.append(f"Description: {description}")
    parts.append(f"\nDiff:\n```\n{diff}\n```")
    prompt = "\n".join(parts)
    return generate(prompt, system=system)
