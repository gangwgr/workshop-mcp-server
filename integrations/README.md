# AI Integrations for Workshop MCP Server

This directory contains integration examples for using the Workshop MCP Server with various AI systems.

## 🤖 Supported AI Systems

| AI System | Integration File | Features |
|-----------|-----------------|----------|
| **Google Gemini** | `gemini_integration.py` | Direct API, Analysis enhancement |
| **Google Gemini** | `gemini_function_calling.py` | Native function calling |
| **OpenAI GPT-4** | `openai_integration.py` | Function calling, Interactive chat |
| **LangChain** | `langchain_integration.py` | Works with ANY LLM (GPT-4, Claude, Gemini) |

## 📋 Prerequisites

### 1. Workshop MCP Server Running

The web GUI must be running:

```bash
cd ../web_gui
python app.py
# Server running at http://127.0.0.1:8080
```

### 2. API Keys

Set the appropriate environment variable for your AI system:

```bash
# For Google Gemini
export GOOGLE_API_KEY="your-google-api-key"

# For OpenAI GPT-4
export OPENAI_API_KEY="sk-..."

# For Anthropic Claude (LangChain)
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Install Dependencies

```bash
# Install integration dependencies
pip install -r requirements-integrations.txt
```

## 🚀 Quick Start

### Gemini Integration

```python
from gemini_integration import GeminiMCPClient

# Initialize
client = GeminiMCPClient()

# Review code
result = client.review_code(
    code="def test(): pass",
    language="python",
    with_gemini_analysis=True
)

print(result['gemini_analysis'])

# Debug cluster
result = client.debug_cluster(
    issue_description="API server not responding",
    with_gemini_guidance=True
)

print(result['gemini_guidance'])

# Chat interface
response = client.chat("How do I debug OpenShift issues?")
print(response)
```

### Gemini Function Calling

```python
from gemini_function_calling import GeminiFunctionCaller

# Initialize
client = GeminiFunctionCaller()

# Natural language interaction
response = client.chat(
    "Review this code for SQL injection: "
    "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')"
)

print(response)

# Interactive mode
client.multi_turn_conversation()
```

### OpenAI GPT-4 Integration

```python
from openai_integration import OpenAIMCPClient

# Initialize
client = OpenAIMCPClient()

# Chat with function calling
response = client.chat(
    "My OpenShift API server is crashing. Help me debug it."
)

print(response)

# Interactive session
client.interactive_session()
```

### LangChain Integration (Universal)

```python
from langchain_integration import create_mcp_agent
from langchain_openai import ChatOpenAI

# Works with ANY LLM!
llm = ChatOpenAI(model="gpt-4-turbo-preview")

# Create agent with MCP tools
agent = create_mcp_agent(llm)

# Use agent
response = agent.run(
    "Debug my OpenShift cluster - the API server is not responding"
)

print(response)
```

## 📚 Detailed Examples

### Example 1: Code Review with Gemini

```python
from gemini_integration import GeminiMCPClient

client = GeminiMCPClient()

code = """
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE user='{username}' AND pass='{password}'"
    return db.execute(query).fetchone()
"""

result = client.review_code(
    code=code,
    language="python",
    focus_areas=["security", "bugs"],
    with_gemini_analysis=True
)

# Get detailed analysis
print("Issues Found:", result['issues_found'])
print("\nGemini's Analysis:")
print(result['gemini_analysis'])
```

**Output:**
```
Issues Found: 2

Gemini's Analysis:
This code has critical security vulnerabilities:

1. SQL Injection: The query uses string formatting to insert user input directly,
   allowing attackers to inject malicious SQL.

2. Plain Text Password: Passwords should never be stored or compared in plain text.

Priority Recommendations:
1. Use parameterized queries: cursor.execute("SELECT * FROM users WHERE user=? AND pass=?", (username, password))
2. Implement password hashing with bcrypt or argon2
3. Add input validation and sanitization

Overall Code Quality: CRITICAL - Requires immediate security fixes
```

### Example 2: Cluster Debugging with GPT-4

```python
from openai_integration import OpenAIMCPClient

client = OpenAIMCPClient()

response = client.chat("""
My OpenShift cluster has the following issues:
- API server pods are in CrashLoopBackOff
- etcd is showing connection errors
- Nodes are reporting NotReady status

Can you help diagnose and fix this?
""")

print(response)
```

**Output:**
```
I'll help you debug this OpenShift cluster issue. Let me run diagnostics...

🔧 Calling function: debug_cluster
   Arguments: {'issue_description': 'API server pods crashing, etcd errors, nodes NotReady'}
   ✅ Status: success

Based on the diagnostics, here's what I found:

ROOT CAUSE:
The primary issue is etcd cluster instability causing API server failures,
which cascades to node NotReady status.

IMMEDIATE ACTIONS:
1. Check etcd quorum: oc get pods -n openshift-etcd
2. Verify etcd member health: oc rsh -n openshift-etcd etcd-master-0 etcdctl member list
3. Review etcd logs: oc logs -n openshift-etcd etcd-master-0 -c etcd

STEP-BY-STEP FIX:
1. First, verify etcd cluster has quorum (at least 2/3 members healthy)
2. If etcd is healthy, check API server logs for specific errors
3. Verify master nodes have sufficient resources (CPU, memory, disk)
4. Check network connectivity between master nodes

Would you like me to generate a test case to validate the fix?
```

### Example 3: Test Generation and Execution with LangChain

```python
from langchain_integration import create_mcp_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# Use Gemini via LangChain
llm = ChatGoogleGenerativeAI(model="gemini-pro")
agent = create_mcp_agent(llm)

response = agent.run("""
Create a test to verify that:
1. An nginx pod can be deployed in the 'production' namespace
2. The pod becomes Running within 60 seconds
3. The pod responds to HTTP requests on port 80

Then execute the test and tell me if it passes.
""")

print(response)
```

**Output:**
```
> Entering new AgentExecutor chain...

I'll help you create and execute that test. Let me break this down:

🔧 Using tool: generate_ocp_test
Arguments: {
  "feature": "nginx deployment",
  "component": "nginx",
  "scenario": "Deploy pod and verify HTTP response",
  "test_format": "shell"
}

Generated test case successfully! Now executing it...

🔧 Using tool: execute_ocp_test
Arguments: {
  "feature": "nginx deployment",
  "component": "nginx",
  "scenario": "Deploy pod and verify HTTP response",
  "namespace": "production"
}

Test Results:
✅ All 5 steps passed!

1. ✅ Created namespace 'production'
2. ✅ Deployed nginx pod
3. ✅ Pod reached Running state in 23 seconds
4. ✅ Pod is healthy (1/1 Ready)
5. ✅ HTTP request to port 80 successful (200 OK)

The test PASSED! Your nginx pod is deployed and working correctly in the production namespace.
```

### Example 4: Must-Gather Analysis with Gemini

```python
from gemini_integration import GeminiMCPClient

client = GeminiMCPClient()

result = client.analyze_mustgather(
    bundle_path="/path/to/must-gather.local.123456",
    with_gemini_insights=True
)

print(result['gemini_insights'])
```

**Output:**
```
EXECUTIVE SUMMARY:
Your OpenShift cluster is experiencing critical availability issues caused by
etcd database corruption, resulting in API server instability and cascade failures.

IMMEDIATE ACTIONS (Priority Order):
1. [CRITICAL] Restore etcd from backup (ETA: 30 minutes)
   Command: oc -n openshift-etcd exec etcd-master-0 -- etcdctl snapshot restore

2. [CRITICAL] Verify etcd cluster health after restore (ETA: 5 minutes)
   Command: oc rsh -n openshift-etcd etcd-master-0 etcdctl endpoint health

3. [HIGH] Restart API server pods to reconnect to healthy etcd (ETA: 10 minutes)
   Command: oc delete pods -n openshift-kube-apiserver -l app=openshift-kube-apiserver

LONG-TERM RECOMMENDATIONS:
- Implement automated etcd backup schedule (daily snapshots)
- Add monitoring alerts for etcd disk I/O latency
- Review and increase etcd disk IOPS if on cloud infrastructure
- Document etcd recovery procedures for on-call engineers

ESTIMATED TIME TO RESOLUTION: 45-60 minutes

STATUS: CRITICAL - Cluster requires immediate intervention
```

## 🔧 Configuration

### Changing MCP Server URL

If your MCP Server runs on a different URL:

```python
# Gemini
client = GeminiMCPClient(mcp_base_url="http://your-server:8080")

# OpenAI
client = OpenAIMCPClient(mcp_base_url="http://your-server:8080")

# LangChain
from langchain_integration import CodeReviewTool
tool = CodeReviewTool(mcp_base_url="http://your-server:8080")
```

### Using Different Models

```python
# Gemini - Different model
client = GeminiMCPClient(model_name="gemini-1.5-pro")

# OpenAI - Different model
client = OpenAIMCPClient(model="gpt-4o")

# LangChain - Any LLM
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3-opus-20240229")
agent = create_mcp_agent(llm)
```

## 📊 Comparison Matrix

| Feature | Gemini Direct | Gemini Function | OpenAI | LangChain |
|---------|---------------|----------------|--------|-----------|
| Code Review | ✅ | ✅ | ✅ | ✅ |
| Cluster Debug | ✅ | ✅ | ✅ | ✅ |
| Test Generation | ✅ | ✅ | ✅ | ✅ |
| Test Execution | ✅ | ✅ | ✅ | ✅ |
| Must-Gather | ✅ | ✅ | ✅ | ✅ |
| AI Analysis | ✅ | ✅ | ✅ | ✅ |
| Function Calling | ❌ | ✅ | ✅ | ✅ |
| Interactive Chat | ✅ | ✅ | ✅ | ✅ |
| Multi-LLM Support | ❌ | ❌ | ❌ | ✅ |
| Best For | Simple integration | Natural conversation | GPT-4 users | Maximum flexibility |

## 🎯 Use Cases

### Use Case 1: Code Review Pipeline

```python
# Integrate into CI/CD
from gemini_integration import GeminiMCPClient

def review_pull_request(pr_files):
    client = GeminiMCPClient()

    for file in pr_files:
        if file.endswith('.py'):
            result = client.review_code(
                code=file.content,
                language="python",
                with_gemini_analysis=True
            )

            if result['issues_found'] > 0:
                post_comment_to_pr(result['gemini_analysis'])
```

### Use Case 2: Automated Cluster Monitoring

```python
# Run periodic cluster health checks
from openai_integration import OpenAIMCPClient
import schedule

def check_cluster_health():
    client = OpenAIMCPClient()

    response = client.chat(
        "Check my OpenShift cluster health and alert if there are critical issues"
    )

    if "CRITICAL" in response:
        send_alert_to_slack(response)

schedule.every(5).minutes.do(check_cluster_health)
```

### Use Case 3: Interactive DevOps Assistant

```python
# Slack bot for cluster operations
from langchain_integration import create_mcp_agent
from langchain_openai import ChatOpenAI

class DevOpsBot:
    def __init__(self):
        llm = ChatOpenAI(model="gpt-4-turbo-preview")
        self.agent = create_mcp_agent(llm)

    def handle_message(self, user_message):
        response = self.agent.run(user_message)
        return response

bot = DevOpsBot()
# Connect to Slack, Teams, etc.
```

## 🐛 Troubleshooting

### Issue: API Key Not Found

**Error:** `ValueError: GOOGLE_API_KEY environment variable required`

**Solution:**
```bash
export GOOGLE_API_KEY="your-api-key"
export OPENAI_API_KEY="sk-..."
```

### Issue: MCP Server Connection Failed

**Error:** `requests.exceptions.ConnectionError`

**Solution:**
```bash
# Ensure MCP Server is running
cd ../web_gui
python app.py

# Check server is accessible
curl http://127.0.0.1:8080/health
```

### Issue: Function Calling Not Working

**Error:** Function calls not being made

**Solution:**
- Use models that support function calling:
  - Gemini: `gemini-1.5-pro` or later
  - OpenAI: `gpt-4-turbo-preview` or later
  - Claude: `claude-3-opus` or later

## 📖 Additional Resources

- **Gemini API Docs**: https://ai.google.dev/docs
- **OpenAI API Docs**: https://platform.openai.com/docs
- **LangChain Docs**: https://python.langchain.com/docs/
- **MCP Server Docs**: See main README.md

## 🤝 Contributing

Add new integrations:

1. Create new file: `{ai_system}_integration.py`
2. Implement client class
3. Add examples to this README
4. Update requirements-integrations.txt

## 📄 License

Same as Workshop MCP Server - MIT License
