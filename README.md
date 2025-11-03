# Workshop MCP Server

AI-Powered Development Assistant with code review, GitHub PR automation, OpenShift test generation & execution, must-gather analysis, and cluster debugging capabilities.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

---

## Features

1. **Code Review** - Line-by-line analysis with security, performance, and quality checks
2. **PR Review** - Automated GitHub PR reviews with comments
3. **OpenShift Testing** - Test generation (Gherkin/YAML/Go/Shell) and execution
4. **Must-Gather Analyzer** - Cluster health assessment with AI-powered diagnostics
5. **Cluster Debugger** - Intelligent issue analysis with fix recommendations
6. **Web GUI** - Beautiful interface for all tools

---

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/your-username/workshop-mcp-server.git
cd workshop-mcp-server
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Authenticate for GitHub/OpenShift features
gh auth login
oc login https://api.your-cluster.example.com:6443

# 4. Run web GUI
cd web_gui
python app.py

# 5. Open browser: http://127.0.0.1:8080
```

For detailed setup, see [SETUP.md](SETUP.md) | Prerequisites: [PREREQUISITES.md](PREREQUISITES.md)

---

## Usage

### Web GUI (Recommended)

Access at **http://127.0.0.1:8080** for an intuitive interface to all tools.

### MCP Server (Claude Desktop)

```bash
pip install -e .
python -m workshop_mcp_server.server
```

Configure Claude Desktop to use this server (see [SETUP.md](SETUP.md)).

### AI System Integrations

Works with **Google Gemini, OpenAI GPT-4, Anthropic Claude, and any LLM via LangChain**.

```python
# Gemini Example
from integrations.gemini_integration import GeminiMCPClient
client = GeminiMCPClient()
result = client.review_code(code="def test(): pass", with_gemini_analysis=True)

# GPT-4 Example
from integrations.openai_integration import OpenAIMCPClient
client = OpenAIMCPClient()
response = client.chat("Debug my OpenShift API server")

# LangChain (Universal - works with ANY LLM)
from integrations.langchain_integration import create_mcp_agent
from langchain_google_genai import ChatGoogleGenerativeAI
agent = create_mcp_agent(ChatGoogleGenerativeAI(model="gemini-pro"))
response = agent.run("Review this code for security issues: ...")
```

See [integrations/README.md](integrations/README.md) for complete guide.

---

## Available Tools

| Tool | Description |
|------|-------------|
| `review_code_line_by_line` | Line-by-line code review with severity filtering |
| `post_pr_review_comments` | Post GitHub PR review comments |
| `generate_ocp_test_case` | Generate OpenShift tests (Gherkin/YAML/Go/Shell) |
| `execute_ocp_test_step_by_step` | Execute tests with real-time progress |
| `debug_ocp_test_failure` | Intelligent test failure analysis |
| `analyze_mustgather_bundle` | Analyze must-gather bundles with AI |
| `debug_openshift_cluster` | Cluster debugging with diagnostics |

---

## Architecture

```
Users (Web Browser / Claude Desktop)
           ↓
Web GUI / MCP Server / CLI Tools
           ↓
Tool Layer (Python Functions)
           ↓
GitHub API / OpenShift Cluster / Must-Gather Files
```

**Tech Stack:** Python 3.8+, Flask, MCP Protocol, GitHub CLI, OpenShift CLI

---

## Deployment

### Production (Gunicorn)

```bash
pip install gunicorn
cd web_gui
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### Docker

```bash
docker build -t workshop-mcp-server .
docker run -p 8080:8080 -v ~/.kube/config:/root/.kube/config workshop-mcp-server
```

### OpenShift

```bash
oc new-app python:3.9~https://github.com/your-username/workshop-mcp-server.git \
  --context-dir=web_gui --name=mcp-server
oc expose svc/mcp-server
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8080 in use | `lsof -i :8080` then `kill -9 <PID>` |
| Module not found | Activate venv: `source venv/bin/activate` |
| GitHub auth failed | `gh auth logout && gh auth login` |
| OC cluster failed | `oc login https://api.cluster.com:6443` |

See [SETUP.md](SETUP.md) for more help.

---

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Support

- **Documentation**: [PREREQUISITES.md](PREREQUISITES.md) | [SETUP.md](SETUP.md) | [integrations/README.md](integrations/README.md)
- **Issues**: https://github.com/your-username/workshop-mcp-server/issues

---

**Built for DevOps, SRE, and Developer Teams**
