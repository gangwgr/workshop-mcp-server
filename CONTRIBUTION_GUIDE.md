# Workshop MCP Server - Contribution to ai-helpers

This guide helps you contribute the Workshop MCP Server to the shared ai-helpers repository.

## What is Workshop MCP Server?

An AI-Powered Development Assistant with comprehensive automation tools for:
- **Code Review** - Line-by-line analysis with security, performance, and quality checks
- **PR Review** - Automated GitHub PR reviews with comments
- **OpenShift Testing** - Test generation (Gherkin/YAML/Go/Shell) and execution
- **Must-Gather Analyzer** - Cluster health assessment with AI diagnostics
- **Cluster Debugger** - Intelligent issue analysis with fix recommendations

## Repository Structure for Contribution

```
workshop-mcp-server/
├── mcp-config.json              # MCP Server configuration for Claude Desktop
├── README.md                     # Main documentation
├── PREREQUISITES.md              # System requirements
├── SETUP.md                      # Installation guide
├── CONTRIBUTION_GUIDE.md         # This file
├── requirements.txt              # Python dependencies
├── workshop_mcp_server/          # Source code
│   ├── src/
│   │   └── tools/                # MCP tools (9 active tools)
│   └── utils/
└── web_gui/                      # Web interface
    ├── app.py                    # Flask application
    ├── templates/                # HTML templates
    └── static/                   # CSS/JS assets
```

## How to Contribute to ai-helpers

### Step 1: Prepare Your Contribution Package

Create a contribution folder with these files:

```bash
mkdir -p ~/ai-helpers-contribution/workshop-mcp-server
cd ~/ai-helpers-contribution/workshop-mcp-server

# Copy essential files
cp /path/to/workshop-mcp-server/mcp-config.json .
cp /path/to/workshop-mcp-server/README.md .
cp /path/to/workshop-mcp-server/PREREQUISITES.md .
cp /path/to/workshop-mcp-server/SETUP.md .
cp /path/to/workshop-mcp-server/requirements.txt .
```

### Step 2: Create MCP Server Entry

For the ai-helpers repository, create a file describing your MCP server:

**File: `workshop-mcp-server.md`**

```markdown
# Workshop MCP Server

AI-Powered Development Assistant with code review, GitHub PR automation, OpenShift test generation & execution, must-gather analysis, and cluster debugging.

## Quick Install

\`\`\`bash
git clone https://github.com/your-username/workshop-mcp-server.git
cd workshop-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd web_gui && python app.py
\`\`\`

Access at: http://127.0.0.1:8080

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

\`\`\`json
{
  "mcpServers": {
    "workshop-mcp-server": {
      "command": "python",
      "args": ["-m", "flask", "--app", "web_gui.app", "run", "--port", "8080"],
      "cwd": "/absolute/path/to/workshop-mcp-server",
      "env": {
        "PYTHONPATH": "/absolute/path/to/workshop-mcp-server"
      }
    }
  }
}
\`\`\`

## Available Tools

| Tool | Description |
|------|-------------|
| `review_code_line_by_line` | Line-by-line code review with severity filtering |
| `post_pr_review_comments` | Post GitHub PR review comments |
| `generate_ocp_test_case` | Generate OpenShift tests (Gherkin/YAML/Go) |
| `generate_oc_cli_test` | Generate manual testing guides with oc CLI |
| `execute_ocp_test_step_by_step` | Execute tests with real-time progress |
| `debug_ocp_test_failure` | Intelligent test failure analysis |
| `validate_ocp_test_input` | Test input validation |
| `analyze_mustgather_bundle` | Analyze must-gather bundles with AI |
| `debug_openshift_cluster` | Cluster debugging with diagnostics |

## Use Cases

### 1. Code Review
\`\`\`python
# Via Web GUI: http://127.0.0.1:8080/code-review
# Paste code, select language, get detailed review
\`\`\`

### 2. GitHub PR Review
\`\`\`python
# Via Web GUI: http://127.0.0.1:8080/pr-review
# Enter PR URL, review files, post automated comments
\`\`\`

### 3. OpenShift Test Generation
\`\`\`python
# Via Web GUI: http://127.0.0.1:8080/ocp-testing
# Feature: Event TTL
# Component: kube-apiserver
# Scenario: Verify eventTTLMinutes configuration
# Format: Shell Script (oc CLI)
# → Generates comprehensive manual testing guide
\`\`\`

### 4. Must-Gather Analysis
\`\`\`python
# Via Web GUI: http://127.0.0.1:8080/mustgather-analyzer
# Path: /path/to/must-gather
# → AI-powered cluster health assessment
\`\`\`

### 5. Cluster Debugging
\`\`\`python
# Via Web GUI: http://127.0.0.1:8080/cluster-debugger
# Issue: API server pods are crashing
# → Intelligent diagnostics + fix recommendations
\`\`\`

## AI Integration

Works with multiple AI systems:

### Google Gemini
\`\`\`python
from integrations.gemini_integration import GeminiMCPClient
client = GeminiMCPClient()
result = client.review_code(code="def test(): pass", with_gemini_analysis=True)
\`\`\`

### OpenAI GPT-4
\`\`\`python
from integrations.openai_integration import OpenAIMCPClient
client = OpenAIMCPClient()
response = client.chat("Debug my OpenShift API server")
\`\`\`

### LangChain (Universal)
\`\`\`python
from integrations.langchain_integration import create_mcp_agent
from langchain_google_genai import ChatGoogleGenerativeAI
agent = create_mcp_agent(ChatGoogleGenerativeAI(model="gemini-pro"))
response = agent.run("Review this code for security issues: ...")
\`\`\`

## Prerequisites

- Python 3.8+
- pip
- Git
- (Optional) GitHub CLI (`gh`) for PR review
- (Optional) OpenShift CLI (`oc`) for cluster features

## Support

- Documentation: [README.md](README.md) | [SETUP.md](SETUP.md)
- Issues: https://github.com/your-username/workshop-mcp-server/issues

## License

MIT License

---

**Built for DevOps, SRE, and Developer Teams**
\`\`\`

### Step 3: Submit to ai-helpers Repository

1. **Fork the ai-helpers repository**
   ```bash
   # Go to https://github.com/RedHatOfficial/ai-helpers
   # Click "Fork"
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-helpers.git
   cd ai-helpers
   ```

3. **Create a new branch**
   ```bash
   git checkout -b add-workshop-mcp-server
   ```

4. **Add your contribution**
   ```bash
   # MCP servers are typically in src/mcp-servers/ or similar
   mkdir -p src/mcp-servers/workshop-mcp-server

   # Copy your files
   cp ~/ai-helpers-contribution/workshop-mcp-server/* src/mcp-servers/workshop-mcp-server/
   ```

5. **Update the main README**
   Edit the ai-helpers `README.md` to add your MCP server to the list:

   ```markdown
   ## MCP Servers

   ### Workshop MCP Server
   AI-Powered Development Assistant with code review, OpenShift testing, and cluster debugging.
   - **Tools**: 9 specialized tools for DevOps/SRE workflows
   - **Setup**: [See documentation](src/mcp-servers/workshop-mcp-server/README.md)
   - **Use Cases**: Code review, PR automation, OpenShift test generation, must-gather analysis
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add Workshop MCP Server - AI development assistant for DevOps/SRE

   - 9 specialized tools for code review, PR automation, and OpenShift testing
   - Web GUI at http://127.0.0.1:8080
   - Supports Claude Desktop, Gemini, GPT-4, and LangChain
   - Comprehensive documentation and setup guides
   "
   ```

7. **Push to your fork**
   ```bash
   git push origin add-workshop-mcp-server
   ```

8. **Create Pull Request**
   - Go to https://github.com/YOUR_USERNAME/ai-helpers
   - Click "Pull Request"
   - Select your branch: `add-workshop-mcp-server`
   - Fill in PR template:
     - **Title**: "Add Workshop MCP Server - AI Development Assistant"
     - **Description**: Explain what your MCP server does, its benefits, and use cases
     - **Testing**: Describe how you tested it
     - **Documentation**: Confirm all docs are included

### Step 4: PR Description Template

```markdown
## Summary
Adding Workshop MCP Server - a comprehensive AI-powered development assistant for DevOps and SRE teams.

## What does this add?
- **9 specialized MCP tools** for code review, GitHub PR automation, OpenShift testing, must-gather analysis, and cluster debugging
- **Web GUI** interface for easy access to all tools
- **Multi-AI support** (Claude, Gemini, GPT-4, LangChain)
- **Complete documentation** (README, SETUP, PREREQUISITES)

## Key Features
1. **Code Review** - Line-by-line analysis with security/performance checks
2. **PR Review** - Automated GitHub PR reviews with comments
3. **OpenShift Testing** - Generate and execute tests (Gherkin/YAML/Go/Shell)
4. **Must-Gather Analyzer** - AI-powered cluster health assessment
5. **Cluster Debugger** - Intelligent issue diagnosis and fix recommendations

## Use Cases
- DevOps engineers testing OpenShift features
- SREs debugging cluster issues
- Developers reviewing code before commits
- Teams automating PR reviews

## Testing Performed
- ✅ Web GUI running at http://127.0.0.1:8080
- ✅ All 9 tools tested and working
- ✅ Code review with multiple languages
- ✅ OpenShift test generation (Shell/YAML/Gherkin/Go)
- ✅ Integration with Gemini, GPT-4, and LangChain

## Documentation Included
- ✅ README.md - Main documentation
- ✅ SETUP.md - Installation guide
- ✅ PREREQUISITES.md - System requirements
- ✅ mcp-config.json - Claude Desktop configuration
- ✅ requirements.txt - Python dependencies
- ✅ Integration examples (Gemini, GPT-4, LangChain)

## Screenshots
(Optional: Add screenshots of Web GUI)

## Related Links
- Repository: https://github.com/YOUR_USERNAME/workshop-mcp-server
- Live demo: http://127.0.0.1:8080 (after setup)

## Contribution Checklist
- ✅ Code follows repository standards
- ✅ Documentation is complete and clear
- ✅ All tools tested and working
- ✅ No sensitive data or credentials included
- ✅ License information included (MIT)
- ✅ Contribution adds value to ai-helpers community
```

## Tips for Successful Contribution

1. **Clean Code**: Ensure all code is production-ready and well-documented
2. **Clear Documentation**: Provide step-by-step setup instructions
3. **Working Examples**: Include practical use cases
4. **Test Everything**: Verify all tools work before submitting
5. **Respond to Feedback**: Be ready to address PR review comments
6. **Update Regularly**: Keep your contribution maintained

## Time Estimate

- **Preparation**: 30 minutes (gathering files, testing)
- **Documentation**: 45 minutes (writing guides, examples)
- **Submission**: 30 minutes (forking, PR creation)
- **Review & Updates**: 15 minutes (responding to feedback)
- **Total**: ~2 hours ✅

## Benefits of Contributing

1. **Community Impact**: Help other DevOps/SRE teams
2. **Visibility**: Showcase your work to Red Hat community
3. **Collaboration**: Get feedback and improvements from others
4. **Recognition**: Contribution credit in ai-helpers repository

---

Ready to contribute? Follow the steps above to submit your Workshop MCP Server to ai-helpers!
