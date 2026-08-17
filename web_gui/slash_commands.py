"""Unified slash command registry — web UI chat + Cursor IDE (.cursor/commands/)."""

import os
from typing import Any, Dict, List, Optional

# Each command: name, usage, description, scope, cursor_file (optional)
SLASH_COMMANDS: List[Dict[str, Any]] = [
    # --- Global ---
    {"name": "help", "usage": "/help", "description": "List all slash commands", "scope": "global", "cursor_file": "help.md"},
    {"name": "status", "usage": "/status", "description": "Show active LLM mode, model, and availability", "scope": "global", "cursor_file": "status.md"},
    {"name": "mode", "usage": "/mode <ollama|claude|cursor|template> [model]", "description": "Switch LLM provider (optionally set model)", "scope": "global", "cursor_file": "mode.md"},
    {"name": "model", "usage": "/model <name>", "description": "Switch model for the current LLM provider", "scope": "global", "cursor_file": "model.md"},
    {"name": "cursor-config", "usage": "/cursor-config", "description": "Show Cursor Agent setup (API key, MCP attach)", "scope": "global"},
    {"name": "mcp-config", "usage": "/mcp-config", "description": "Show MCP server config for Cursor IDE", "scope": "global"},
    {"name": "debug", "usage": "/debug <issue description>", "description": "Open Cluster Debugger with issue prefilled", "scope": "global", "cursor_file": "debug-cluster.md"},
    {"name": "mustgather", "usage": "/mustgather <path-or-url>", "description": "Open Must-Gather Analyzer with bundle path prefilled", "scope": "global", "cursor_file": "analyze-mustgather.md"},
    {"name": "ask-kb", "usage": "/ask-kb <question>", "description": "Ask the knowledge base (RAG)", "scope": "global", "cursor_file": "ask-knowledge-base.md"},
    {"name": "list-kb", "usage": "/list-kb", "description": "List indexed knowledge base collections", "scope": "global", "cursor_file": "list-knowledge-base.md"},
    {"name": "index-kb", "usage": "/index-kb <folder-path> [collection-name]", "description": "Index a local folder into the knowledge base", "scope": "global", "cursor_file": "index-knowledge-base.md"},
    # --- Must-Gather ---
    {"name": "analyze", "usage": "/analyze", "description": "Run analysis on the current page", "scope": "page", "cursor_file": "analyze-mustgather.md"},
    {"name": "preset", "usage": "/preset <health_check|degraded_cluster|network_issues>", "description": "Select a Must-Gather quick preset", "scope": "mustgather", "cursor_file": "preset-health-check.md"},
    {"name": "script", "usage": "/script <clusterversion|clusteroperators|pods|nodes|etcd|network|events>", "description": "Run a single Must-Gather script (needs bundle path set)", "scope": "mustgather"},
    # --- Cluster Debugger ---
    {"name": "triage", "usage": "/triage <workflow_id>", "description": "Run oc triage workflow (e.g. pod_crashloop, apiserver_health)", "scope": "cluster_debugger", "cursor_file": "triage-initial.md"},
    # --- Chat ---
    {"name": "clear", "usage": "/clear", "description": "Clear chat messages", "scope": "chat"},
]

CURSOR_EXTRA_COMMANDS: List[Dict[str, str]] = [
    {"file": "preset-degraded-cluster.md", "usage": "/preset-degraded-cluster", "description": "Must-Gather preset: degraded cluster"},
    {"file": "preset-network-issues.md", "usage": "/preset-network-issues", "description": "Must-Gather preset: network issues"},
    {"file": "analyze-etcd.md", "usage": "/analyze-etcd", "description": "Must-Gather: etcd health analysis"},
    {"file": "triage-apiserver.md", "usage": "/triage-apiserver", "description": "Live oc triage: API server health"},
    {"file": "triage-pod-crashloop.md", "usage": "/triage-pod-crashloop", "description": "Live oc triage: CrashLoop pods"},
    {"file": "switch-llm.md", "usage": "/switch-llm", "description": "Alias for /mode — switch LLM backend"},
]

MUSTGATHER_SCRIPTS = [
    "clusterversion", "clusteroperators", "pods", "nodes", "etcd",
    "network", "ovn_dbs", "events", "pvs", "prometheus", "windows_logs",
]

TRIAGE_WORKFLOWS = [
    "initial_triage", "operators_degraded", "pod_crashloop", "control_plane",
    "apiserver_health", "apiserver_operator", "apiserver_logs", "apiserver_events",
    "apiserver_auth", "openshift_apiserver", "etcd_health", "node_notready", "network_ovs",
]


def list_commands(scope: Optional[str] = None) -> List[Dict[str, Any]]:
    if not scope:
        return SLASH_COMMANDS
    return [c for c in SLASH_COMMANDS if c.get("scope") in ("global", scope)]


def list_cursor_commands() -> List[Dict[str, str]]:
    """All Cursor IDE commands (.cursor/commands/*.md)."""
    seen = set()
    items: List[Dict[str, str]] = []
    for cmd in SLASH_COMMANDS:
        cf = cmd.get("cursor_file")
        if cf and cf not in seen:
            seen.add(cf)
            slug = cf.replace(".md", "")
            items.append({"file": cf, "usage": f"/{slug}", "description": cmd["description"]})
    for extra in CURSOR_EXTRA_COMMANDS:
        if extra["file"] not in seen:
            seen.add(extra["file"])
            items.append(extra)
    return items


def parse_slash_input(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if not text.startswith("/"):
        return None
    parts = text[1:].split(None, 1)
    if not parts:
        return None
    return {
        "command": parts[0].lower().replace("-", "_"),
        "args": parts[1].strip() if len(parts) > 1 else "",
        "raw": text,
    }


def format_help(scope: Optional[str] = None) -> str:
    lines = ["**Web UI slash commands**", ""]
    for cmd in list_commands(scope):
        lines.append(f"- `{cmd['usage']}` — {cmd['description']}")
    lines.append("")
    lines.append("**Cursor IDE** — type `/` in Cursor chat (`.cursor/commands/`):")
    for c in list_cursor_commands():
        name = c["file"].replace(".md", "")
        lines.append(f"- `/{name}` — {c['description']}")
    return "\n".join(lines)


def get_mcp_config_snippet(repo_root: str) -> str:
    return f'''{{
  "mcpServers": {{
    "workshop-mcp-server": {{
      "command": "python",
      "args": ["-m", "workshop_mcp_server.src.main"],
      "cwd": "{repo_root}",
      "env": {{
        "PYTHONPATH": "{repo_root}"
      }}
    }}
  }}
}}'''
