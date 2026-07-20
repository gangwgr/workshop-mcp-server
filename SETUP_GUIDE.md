# MCP Server — Setup & Implementation Guide

## Can it run without Cursor?

**YES.** Your MCP server has two independent interfaces:

| Interface | Port | Requires Cursor? | How to use |
|-----------|------|-------------------|------------|
| **Web GUI** (Flask) | 5001 | No — works in any browser | `python web_gui/app.py` |
| **MCP Protocol Server** (FastMCP) | 8080 | No — works with any MCP client | `python -m workshop_mcp_server.src.main` |

The Web GUI is a fully standalone web application. The MCP server can connect to Cursor, Claude Desktop, VS Code extensions, or any tool that speaks the MCP protocol.

---

## Architecture Overview

```
workshop-mcp-server/
├── .env                          # All configuration (LLM, Jira, Ollama, Claude)
├── mcp-config.json               # MCP client configuration (for Cursor/Claude Desktop)
├── web_gui/
│   ├── app.py                    # Flask web application (port 5001)
│   ├── requirements.txt          # Python dependencies
│   ├── ollama_client.py          # Ollama LLM client
│   ├── templates/                # All HTML pages
│   │   ├── base.html             # Nav layout
│   │   ├── code_review.html      # Code review tool
│   │   ├── pr_review.html        # GitHub PR review
│   │   ├── ocp_testing.html      # OpenShift test generator
│   │   ├── test_plan_generator.html  # QE test plan from docs
│   │   ├── regression_test_agent.html # Bug → regression tests
│   │   ├── jira_manager.html     # Jira integration
│   │   ├── polarion_qa.html      # Polarion test case search
│   │   ├── mustgather_analyzer.html  # Must-gather analysis
│   │   ├── cluster_debugger.html # Cluster debugging
│   │   ├── code_assistant.html   # AI code assistant
│   │   ├── knowledge_base.html   # RAG knowledge base
│   │   ├── ai_chat.html          # General AI chat
│   │   ├── work_reports.html     # Work report generator
│   │   └── settings.html         # LLM/config settings
│   └── static/css/               # Stylesheets
├── workshop_mcp_server/
│   └── src/
│       ├── main.py               # MCP protocol server (FastMCP)
│       └── tools/
│           ├── llm_provider.py           # Multi-LLM backend (Ollama/Claude)
│           ├── jira_manager_tool.py      # Jira API integration
│           ├── polarion_search_tool.py   # Polarion ALM search
│           ├── line_by_line_code_reviewer_tool.py  # Code review
│           ├── github_pr_commenter_tool.py  # GitHub PR comments
│           ├── ocp_test_case_generator_tool.py    # OCP test gen
│           ├── ocp_cluster_debugger_agent_tool.py # Cluster debug
│           ├── mustgather_analyzer_tool.py  # Must-gather analyzer
│           └── rag/                       # RAG/Knowledge Base
│               ├── rag_tool.py
│               ├── doc_ingester.py
│               └── kb_context.py
└── skills/                       # Cursor Skills (optional)
```

---

## Step-by-Step Setup

### Prerequisites

- **Python 3.10+**
- **Ollama** (for local LLMs) — https://ollama.com
- **gh CLI** (for GitHub PR features) — `brew install gh`
- **Google Cloud SDK** (only if using Claude via Vertex AI)

### Step 1: Clone & Setup Environment

```bash
cd /Users/rgangwar/hackathon/workshop-mcp-server

# Create virtual environment
python3 -m venv web_gui/venv
source web_gui/venv/bin/activate

# Install dependencies
pip install -r web_gui/requirements.txt
pip install flask requests chromadb sentence-transformers pyyaml jira anthropic google-auth
```

### Step 2: Configure `.env`

```bash
cp .env.example .env   # or edit existing .env
```

Key settings:

```env
# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.3:latest
LLM_MODE=ollama                    # Options: ollama, claude, template

# Claude (Vertex AI) — optional
CLAUDE_MODEL=claude-sonnet-4-5@20250929
CLAUDE_CODE_USE_VERTEX=1
ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project
CLOUD_ML_REGION=global

# Jira — optional (can configure via GUI)
JIRA_BASE_URL=https://your-company.atlassian.net/
JIRA_USERNAME=you@company.com
JIRA_API_TOKEN=your-token

# RAG
RAG_ENABLED=true

# Git (for work reports)
GIT_AUTHOR_NAME=Your Name
```

### Step 3: Start Ollama (Local LLMs)

```bash
# Install Ollama if not already
brew install ollama

# Start the server
ollama serve

# Pull models (in another terminal)
ollama pull llama3.3:latest
ollama pull qwen2.5-coder:32b      # optional, large model
ollama pull nomic-embed-text        # for RAG embeddings
```

### Step 4: Run the Web GUI (No Cursor needed)

```bash
cd /Users/rgangwar/hackathon/workshop-mcp-server/web_gui
source venv/bin/activate
python app.py
```

Open **http://localhost:5001** in any browser.

### Step 5 (Optional): Run as MCP Protocol Server

This mode exposes tools via the MCP protocol for AI clients:

```bash
cd /Users/rgangwar/hackathon/workshop-mcp-server
PYTHONPATH=. python -m workshop_mcp_server.src.main
```

---

## Connecting to Different Clients

### A) Browser Only (No AI client needed)

Just run `python web_gui/app.py` and open http://localhost:5001. All features work standalone.

### B) Cursor IDE

Add to your Cursor MCP settings (`~/.cursor/mcp.json` or workspace `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "workshop-mcp-server": {
      "command": "python",
      "args": ["-m", "workshop_mcp_server.src.main"],
      "cwd": "/Users/rgangwar/hackathon/workshop-mcp-server",
      "env": {
        "PYTHONPATH": "/Users/rgangwar/hackathon/workshop-mcp-server"
      }
    }
  }
}
```

### C) Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "workshop-mcp-server": {
      "command": "python",
      "args": ["-m", "workshop_mcp_server.src.main"],
      "cwd": "/Users/rgangwar/hackathon/workshop-mcp-server",
      "env": {
        "PYTHONPATH": "/Users/rgangwar/hackathon/workshop-mcp-server"
      }
    }
  }
}
```

### D) VS Code (with MCP extension)

Use the same `mcp-config.json` included in the project root.

---

## Available Tools (via MCP Protocol)

| Tool | Description |
|------|-------------|
| `search_test_cases` | Search Polarion for test cases |
| `get_test_case_details` | Get detailed Polarion test case |
| `query_polarion_api` | Raw Polarion API query |
| `test_jira_connection` | Test Jira connectivity |
| `get_issue` | Fetch Jira issue details |
| `search_issues` | JQL search on Jira |
| `get_high_priority_bugs` | Find high-priority bugs |
| `get_team_issues` | Get team's issues |
| `generate_test_cases_from_jira` | AI test gen from Jira issue |
| `generate_test_plan_from_jira` | AI test plan from Jira issue |
| `review_code_line_by_line` | AI code review |
| `post_pr_review_comments` | Post review comments on GitHub PR |
| `generate_ocp_test_case` | Generate OpenShift test cases |
| `generate_oc_cli_test` | Generate oc CLI test scripts |
| `execute_ocp_test_step_by_step` | Execute OCP tests step by step |
| `debug_ocp_test_failure` | Debug test failures |
| `validate_ocp_test_input` | Validate test inputs |
| `analyze_mustgather_bundle` | Analyze must-gather bundles |
| `debug_openshift_cluster` | AI cluster debugging |
| `ask_local_llm` | Ask the configured LLM directly |
| `switch_llm_mode` | Switch between Ollama/Claude/Template |
| `ask_docs` | RAG query over indexed docs |
| `index_docs` / `index_repo` / `index_web` | Index documents for RAG |
| `list_knowledge_bases` / `delete_knowledge_base` | Manage KB |

---

## Web GUI Pages

| URL | Feature |
|-----|---------|
| `/` | Dashboard home |
| `/code-review` | AI code review |
| `/pr-review` | GitHub PR review |
| `/ocp-testing` | OpenShift test generation |
| `/test-plan-generator` | Test plan from enhancement docs |
| `/regression-test-agent` | Regression tests from bugs |
| `/jira-manager` | Jira issue management |
| `/polarion-qa` | Polarion test case search |
| `/mustgather-analyzer` | Must-gather analysis |
| `/cluster-debugger` | Cluster debugging |
| `/code-assistant` | AI code assistant (write/edit/browse) |
| `/knowledge-base` | RAG knowledge base management |
| `/ai-chat` | General AI chat |
| `/work-reports` | Daily work report generator |
| `/settings` | LLM configuration |

---

## Running on Another Machine

```bash
# 1. Copy the project
scp -r workshop-mcp-server/ user@remote:/opt/mcp-server/

# 2. On remote machine
cd /opt/mcp-server
python3 -m venv web_gui/venv
source web_gui/venv/bin/activate
pip install -r web_gui/requirements.txt

# 3. Edit .env for that machine
vi .env

# 4. Start
python web_gui/app.py
# Access at http://remote-ip:5001
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `LLM not available` | Start Ollama: `ollama serve` |
| `404 on model` | Pull the model: `ollama pull llama3.3:latest` |
| `Jira credentials error` | Configure in Settings or add to `.env` |
| `Port 5001 in use` | `lsof -ti:5001 \| xargs kill -9` |
| `Claude not responding` | Check `ANTHROPIC_VERTEX_PROJECT_ID` and `gcloud auth` |
| `RAG empty collection` | Index documents via Knowledge Base page first |
| `Import errors` | Ensure `PYTHONPATH` includes the project root |

---

## Quick Start (TL;DR)

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Web GUI
cd /Users/rgangwar/hackathon/workshop-mcp-server/web_gui
source venv/bin/activate
python app.py

# Open browser: http://localhost:5001
```

No Cursor required. All AI features work via the browser UI with local Ollama models.
