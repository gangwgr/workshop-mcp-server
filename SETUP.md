# Setup Guide

## Quick Setup (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/your-username/workshop-mcp-server.git
cd workshop-mcp-server

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure GitHub
gh auth login

# 5. (Optional) Configure OpenShift
oc login https://api.your-cluster.example.com:6443

# 6. Run web GUI
cd web_gui
python app.py

# 7. Open browser
# Visit: http://127.0.0.1:8080
```

---

## Installation Options

### Option 1: Web GUI Mode (Recommended)

Best for: General use, testing, development

```bash
cd workshop-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd web_gui
python app.py
```

Access at: **http://127.0.0.1:8080**

### Option 2: MCP Server Mode

Best for: Claude Desktop integration

```bash
cd workshop-mcp-server
pip install -e .
python -m workshop_mcp_server.server
```

Then configure Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "workshop-mcp-server": {
      "command": "python",
      "args": ["-m", "workshop_mcp_server.server"]
    }
  }
}
```

### Option 3: AI Integration Mode

Best for: Using with Gemini, GPT-4, or other AI systems

```bash
cd workshop-mcp-server/integrations
pip install -r requirements-integrations.txt

# Set API key
export GOOGLE_API_KEY="your-key"  # For Gemini
export OPENAI_API_KEY="your-key"  # For GPT-4

# Run examples
python example_all_integrations.py
```

See [integrations/README.md](integrations/README.md) for details.

---

## Configuration

### Environment Variables (Optional)

Create `.env` file:

```bash
# Optional overrides
KUBECONFIG=/path/to/kubeconfig
OC_PATH=/usr/local/bin/oc
GITHUB_TOKEN=your_github_token
WEB_GUI_PORT=8080
FLASK_DEBUG=True
```

### GitHub Authentication

```bash
gh auth login
gh auth status  # Verify
```

### OpenShift Access

```bash
oc login https://api.cluster.com:6443
oc whoami  # Verify
oc get nodes  # Test access
```

---

## Verification

Test each feature:

**1. Code Review**
```bash
curl -X POST http://127.0.0.1:8080/api/review-code \
  -H "Content-Type: application/json" \
  -d '{"code": "def test(): pass", "language": "python"}'
```

**2. Cluster Debug (requires oc login)**
```bash
curl -X POST http://127.0.0.1:8080/api/debug-cluster \
  -H "Content-Type: application/json" \
  -d '{"issue_description": "Test debug"}'
```

**3. Web GUI**
- Open http://127.0.0.1:8080
- Navigate to Code Review
- Paste sample code
- Click "Review Code"

---

## Troubleshooting

### Port 8080 Already in Use

```bash
lsof -i :8080
kill -9 <PID>

# Or change port in web_gui/app.py
```

### Module Not Found Error

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall
pip install -r requirements.txt

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### GitHub CLI Not Authenticated

```bash
gh auth logout
gh auth login
gh auth status
```

### OpenShift Connection Failed

```bash
# Check cluster access
oc login https://api.cluster.com:6443
oc whoami
oc get nodes

# Check kubeconfig
echo $KUBECONFIG
export KUBECONFIG=/path/to/kubeconfig
```

### Dependencies Installation Failed

```bash
# Upgrade pip
pip install --upgrade pip

# Install one by one
cat requirements.txt | xargs -n 1 pip install

# Use Python 3.9 if 3.8 has issues
python3.9 -m venv venv
```

---

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
cd web_gui
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### Using Docker

```bash
docker build -t workshop-mcp-server .
docker run -p 8080:8080 \
  -v ~/.kube/config:/root/.kube/config \
  -e KUBECONFIG=/root/.kube/config \
  workshop-mcp-server
```

### On OpenShift

```bash
oc new-project mcp-server
oc new-app python:3.9~https://github.com/your-username/workshop-mcp-server.git \
  --context-dir=web_gui --name=mcp-server
oc expose svc/mcp-server
oc get route mcp-server
```

---

## Next Steps

1. **Explore Web GUI**: http://127.0.0.1:8080
2. **Try AI Integrations**: See [integrations/README.md](integrations/README.md)
3. **Read Main README**: [README.md](README.md)
4. **Report Issues**: https://github.com/your-username/workshop-mcp-server/issues

---

**Setup Complete!** Start using the MCP Server.
