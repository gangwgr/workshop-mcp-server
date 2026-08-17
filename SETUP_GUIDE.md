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
├── .env                          # All configuration (LLM, Ollama, Claude)
├── .gitignore
├── mcp-config.json               # MCP client configuration (for Cursor/Claude Desktop)
├── SETUP_GUIDE.md                # This file
├── web_gui/
│   ├── app.py                    # Flask web application (port 5001)
│   ├── requirements.txt          # Python dependencies
│   ├── ollama_client.py          # Ollama LLM client
│   ├── cluster_debugger_commands.py  # oc triage workflow definitions
│   ├── mustgather_learnings.json # Stored user feedback for Must-Gather
│   ├── templates/
│   │   ├── base.html             # Nav layout (shared header)
│   │   ├── index.html            # Dashboard home
│   │   ├── cluster_debugger.html # Live cluster debugging
│   │   ├── mustgather_analyzer.html  # Must-gather bundle analysis
│   │   ├── knowledge_base.html   # RAG Knowledge Base management
│   │   └── settings.html         # LLM/config settings
│   └── static/css/               # Stylesheets
├── workshop_mcp_server/
│   ├── utils/
│   │   └── pylogger.py           # Structured logging utility
│   └── src/
│       ├── main.py               # MCP protocol server (FastMCP)
│       └── tools/
│           ├── llm_provider.py           # Multi-LLM backend (Ollama/Claude)
│           ├── ocp_cluster_debugger_agent_tool.py # Live cluster debugging
│           ├── mustgather_analyzer_tool.py  # Must-gather analysis
│           └── rag/                       # RAG/Knowledge Base
│               ├── rag_tool.py            # RAG query & indexing functions
│               ├── doc_ingester.py        # ChromaDB ingestion engine
│               └── kb_context.py          # KB context injection helper
└── vector_store/                  # ChromaDB data (auto-created, gitignored)
```

---

## Step-by-Step Setup

### Prerequisites

- **Python 3.10+**
- **Ollama** (for local LLMs) — https://ollama.com
- **Google Cloud SDK** (only if using Claude via Vertex AI)

### Step 1: Clone & Setup Environment

```bash
cd /Users/rgangwar/hackathon/workshop-mcp-server

# Create virtual environment
python3 -m venv web_gui/venv
source web_gui/venv/bin/activate

# Install dependencies
pip install -r web_gui/requirements.txt
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

# RAG
RAG_ENABLED=true
```

### Step 3: Start Ollama (Local LLMs)

```bash
# Install Ollama if not already
brew install ollama

# Start the server
ollama serve

# Pull models (in another terminal)
ollama pull llama3.3:latest         # Chat/analysis model
ollama pull nomic-embed-text        # Required for RAG embeddings
ollama pull qwen2.5-coder:32b      # Optional — larger coding model
```

### Step 4: Run the Web GUI

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

## Tools & Features

### 1. Cluster Debugger (`/cluster-debugger`)

AI-powered live cluster diagnostics with test automation.

- **AI Debug & Analyze** — Describe issue in natural language, AI runs `oc` commands and analyzes output
- **Focused oc Triage** — Predefined workflows (Pod CrashLoop, API Server, etcd, Nodes, Network, Storage, etc.)
- **Test Case Generation** — Go/Ginkgo test cases generated from diagnostic context
- **Fix Recommendations** — Specific remediation commands
- **RAG-Enhanced** — KB articles injected into LLM prompts for better diagnosis

### 2. Must-Gather Analyzer (`/mustgather-analyzer`)

Deep analysis of OpenShift must-gather bundles.

- Upload `.tar.gz`, `.tar`, `.zip` or extracted directories
- Component-focused analysis (etcd, nodes, network, storage, etc.)
- Anomaly detection with scoring
- AI root-cause analysis with evidence and remediation
- Feedback learning — correct the AI, it remembers
- **RAG-Enhanced** — KB solutions injected into root-cause analysis

### 3. Knowledge Base / RAG (`/knowledge-base`)

Index documents to enhance AI analysis across all tools.

- **Index local folders** — Point to docs, runbooks, code repos on disk
- **Index Git repos** — Clone and index any git repository
- **Index web docs** — Fetch and index documentation URLs (with crawl option)
- **Ask KB** — Query the knowledge base with natural language
- **Auto-injection** — Relevant KB context is automatically added to Cluster Debugger and Must-Gather LLM prompts
- Supports: `.go`, `.py`, `.md`, `.yaml`, `.json`, `.sh`, `.pdf`, and more

### 4. AI Chat (in navigation bar)

- LLM chat with KB context injection
- Switch between Ollama / Claude / **Cursor Agent** from the UI
- Available on all pages via the mode selector

### 5. Cursor Agent (in Web UI)

Use Cursor models and agents directly from the dashboard for analysis:

1. Get a API key from [cursor.com/dashboard/integrations](https://cursor.com/dashboard/integrations)
2. Go to **Settings** → set `CURSOR_API_KEY` and model (default: `composer-2.5`)
3. Select **Cursor Agent** in the top navigation mode dropdown
4. Run Cluster Debugger or Must-Gather analysis — LLM calls route through the Cursor SDK

Optional settings:
- `CURSOR_CWD` — local repo path for agent context
- `CURSOR_ATTACH_MCP=true` — attach workshop MCP tools (must-gather, cluster debugger, RAG) to the agent

**Web UI slash commands** — in Must-Gather / Cluster Debugger chat:
- `/help` — list commands
- `/status` — LLM mode and availability
- `/mode cursor` or `/mode ollama` — switch provider
- `/preset health_check` — Must-Gather preset
- `/analyze` — run analysis on current page
- `/debug apiserver pods crashing` — open Cluster Debugger
- `/mustgather /path/to/bundle.tar` — open Must-Gather with path
- `/mcp-config` — show MCP JSON for Cursor IDE

See full list at `/cursor-setup` in the web UI.

---

## Connecting to Different Clients

### A) Browser Only (No AI client needed)

Just run `python web_gui/app.py` and open http://localhost:5001. All features work standalone.

### B) Cursor IDE (MCP + slash commands)

**MCP config** — already in `.cursor/mcp.json` in this repo. Or copy from the **Cursor** page in the web UI (`/cursor-setup`).

Restart Cursor after saving. Available MCP tools:
- `analyze_mustgather_bundle` — offline bundle analysis
- `debug_openshift_cluster` — live cluster debug
- `ask_docs` / `index_docs` — knowledge base
- `switch_llm_mode` — change LLM backend

**Cursor slash commands** — type `/` in Cursor chat (from `.cursor/commands/`). Full list at `/cursor-setup` in the web UI. Examples:

- `/help` — list all commands
- `/debug-cluster` — investigate a live cluster issue
- `/analyze-mustgather` — analyze an offline bundle path/URL
- `/preset-health-check` / `/preset-degraded-cluster` / `/preset-network-issues`
- `/analyze-etcd` — etcd-focused bundle analysis
- `/triage-initial` / `/triage-apiserver` / `/triage-pod-crashloop`
- `/ask-knowledge-base` / `/list-knowledge-base` / `/index-knowledge-base`
- `/mode` / `/model` / `/status` / `/switch-llm`

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

## Web GUI Pages

| URL | Feature |
|-----|---------|
| `/` | Dashboard home — status overview |
| `/cluster-debugger` | Live cluster debugging with AI |
| `/mustgather-analyzer` | Must-gather bundle analysis |
| `/knowledge-base` | RAG knowledge base management |
| `/settings` | LLM configuration |

---

## How RAG Works

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Index Sources   │────▶│  ChromaDB    │────▶│  LLM Analysis   │
│  (docs/code/web) │     │  (vectors)   │     │  (enriched)     │
└─────────────────┘     └──────────────┘     └─────────────────┘
        │                       │                       │
   Index Folder            nomic-embed-text         get_kb_context()
   Index Git Repo          embeddings              auto-injected into
   Index Web URL           cosine similarity       every LLM prompt
```

1. **Indexing**: Documents are chunked (800 chars, 100 overlap), embedded with `nomic-embed-text`, stored in ChromaDB
2. **Retrieval**: When a tool calls the LLM, `get_kb_context()` searches for relevant chunks (relevance > 40%)
3. **Generation**: Retrieved context is appended to the LLM prompt, grounding responses in your indexed knowledge

### Example: Enhancing Cluster Debugger with KB

```bash
# Index OpenShift troubleshooting docs
# (via Knowledge Base page or API)
POST /api/kb/index-web
{
  "url": "https://docs.openshift.com/container-platform/4.17/support/troubleshooting/troubleshooting-installations.html",
  "collection": "ocp-docs",
  "crawl": true
}

# Index internal runbooks
POST /api/kb/index-folder
{
  "folder_path": "/path/to/team-runbooks",
  "collection": "runbooks"
}

# Now when Cluster Debugger runs, it automatically retrieves
# relevant KB articles and includes them in the LLM prompt
```

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

# 4. Start Ollama and pull models
ollama serve &
ollama pull llama3.3:latest
ollama pull nomic-embed-text

# 5. Start the app
python web_gui/app.py
# Access at http://remote-ip:5001
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `LLM not available` | Start Ollama: `ollama serve` |
| `404 on model` | Pull the model: `ollama pull llama3.3:latest` |
| `Port 5001 in use` | `lsof -ti:5001 \| xargs kill -9` |
| `Claude not responding` | Check `ANTHROPIC_VERTEX_PROJECT_ID` and `gcloud auth` |
| `RAG empty collection` | Index documents via Knowledge Base page first |
| `nomic-embed-text error` | Pull embedding model: `ollama pull nomic-embed-text` |
| `Import errors` | Ensure `PYTHONPATH` includes the project root |
| `chromadb not found` | `pip install chromadb` |
| `oc commands fail` | Check OC CLI Path and Kubeconfig in Cluster Debugger config |

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
