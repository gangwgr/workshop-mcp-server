# Workshop MCP Server - Cursor IDE Setup Guide

A focused guide to connect the Workshop MCP Server to Cursor IDE after installation.

---

## Prerequisites

Before following this guide, ensure:
- ✅ Workshop MCP Server is cloned
- ✅ Python 3.14 is installed
- ✅ Dependencies are installed: `python3.14 -m pip install --user -e .`
- ✅ MCP server works in terminal: `timeout 5 python3.14 workshop_mcp_server/src/main.py`
- ✅ Cursor IDE is installed

---

## Step 1: Locate Your MCP Configuration File

The MCP configuration file location depends on your OS:

### Linux/macOS:
```bash
~/.cursor/mcp.json
```

### Windows:
```
%APPDATA%\Cursor\mcp.json
```

**To open it easily:**
```bash
# Linux/macOS - Open in terminal
cat ~/.cursor/mcp.json

# Or open in your editor
code ~/.cursor/mcp.json
# or
nano ~/.cursor/mcp.json
```

---

## Step 2: Find Your Workspace Path

**Get your absolute path to the project:**
```bash
cd ~/Documents/workshop-mcp-server
pwd
```

Expected output:
```
/home/USERNAME/Documents/workshop-mcp-server
```

**Replace `USERNAME` with your actual username** 

---

## Step 3: Create or Update mcp.json

If `~/.cursor/mcp.json` doesn't exist, create it with this content:

```json
{
  "mcpServers": {
    "workshop-mcp-server": {
      "command": "python3.14",
      "args": [
        "/home/USERNAME/Documents/workshop-mcp-server/workshop_mcp_server/src/main.py"
      ],
      "cwd": "/home/USERNAME/Documents/workshop-mcp-server",
      "env": {
        "PYTHONPATH": "/home/USERNAME/Documents/workshop-mcp-server"
      },
      "description": "Debugging agent for live cluster and airgapped cluster with must-gather analysis, cluster health assessment, and intelligent issue diagnosis",
      "version": "1.0.0",
      "author": "Workshop MCP Team"
    }
  }
}
```

**If `mcp.json` already exists:**
- Don't delete it
- Add the `"workshop-mcp-server"` entry under `"mcpServers"`
- Keep any other MCP servers already configured

---

## Step 4: Replace USERNAME Placeholders

**Important:** Replace ALL instances of `USERNAME` with your actual username

```bash
# Find your username
whoami
# Output: xxxxx (use this for USERNAME)
```

**Example for user "xxxxx":**
```json
{
  "mcpServers": {
    "workshop-mcp-server": {
      "command": "python3.14",
      "args": [
        "/home/xxxxx/Documents/workshop-mcp-server/workshop_mcp_server/src/main.py"
      ],
      "cwd": "/home/xxxxx/Documents/workshop-mcp-server",
      "env": {
        "PYTHONPATH": "/home/xxxxx/Documents/workshop-mcp-server"
      },
      "description": "Debugging agent for live cluster and airgapped cluster with must-gather analysis, cluster health assessment, and intelligent issue diagnosis",
      "version": "1.0.0",
      "author": "Workshop MCP Team"
    }
  }
}
```

---

## Step 5: Verify JSON Syntax

Make sure the JSON is valid:

```bash
# Test JSON syntax
python3.14 -c "
import json
try:
    with open('~/.cursor/mcp.json'.replace('~', os.path.expanduser('~'))) as f:
        json.load(f)
    print('✅ JSON is valid')
except json.JSONDecodeError as e:
    print(f'❌ JSON error: {e}')
"
```

Or use an online JSON validator:
- Paste your mcp.json content at: https://jsonlint.com/

---

## Step 6: Verify Configuration Paths

Make sure all paths in mcp.json actually exist:

```bash
# Check if Python 3.14 exists
python3.14 --version
# Expected: Python 3.14.x

# Check if main.py exists
ls -la /home/USERNAME/Documents/workshop-mcp-server/workshop_mcp_server/src/main.py
# Should output the file path, not "No such file"

# Check if project directory exists
ls -la /home/USERNAME/Documents/workshop-mcp-server/
# Should show: pyproject.toml, README.md, workshop_mcp_server/, etc.
```

---

## Step 7: Restart Cursor IDE

**Important:** You must fully restart Cursor for it to load the new configuration

```bash
# Close Cursor completely (not just the window)
# Then reopen it
```

Or use the Cursor command:
- Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Linux/Windows)
- Type: `Developer: Reload Window`
- Press Enter

---

## Step 8: Verify Connection in Cursor

**Check if MCP Server is Connected:**

1. Look at the **bottom status bar** of Cursor
2. You should see: `workshop-mcp-server: Connected` (with a green dot)

**If disconnected (red dot):**

1. Click on the MCP status indicator
2. Check the error message
3. Review the [Troubleshooting](#troubleshooting) section below

---

## Step 9: Test MCP Tools

Once connected, test the tools:

### Method 1: Command Palette
```
Cmd+Shift+P (macOS)
Ctrl+Shift+P (Linux/Windows)

Then type and select:
- "MCP: List Tools" - See available tools
- "MCP: Ask Local LLM" - Test the LLM tool
```

### Method 2: Use @ Symbol
In the Cursor chat, type `@` and you should see:
```
@workshop-mcp-server
  - debug_openshift_cluster
  - ask_local_llm
  - switch_llm_mode
  - ask_docs
  - list_knowledge_bases
  ... (other tools)
```

---

## Troubleshooting

### Issue: MCP Server Shows "Disconnected"

**Check 1: Verify mcp.json exists and is valid**
```bash
cat ~/.cursor/mcp.json
# Should output valid JSON, not "No such file"
```

**Check 2: Verify Python 3.14 works**
```bash
python3.14 -c "print('✅ Python works')"
```

**Check 3: Test MCP server directly**
```bash
cd ~/Documents/techgenie/workshop-mcp-server
timeout 5 python3.14 workshop_mcp_server/src/main.py
# Should show FastMCP banner and "Starting MCP server"
```

**Check 4: Verify paths in mcp.json are correct**
```bash
# Check each path
ls /home/USERNAME/Documents/techgenie/workshop-mcp-server/workshop_mcp_server/src/main.py
ls /home/USERNAME/Documents/techgenie/workshop-mcp-server/

# If paths don't exist, update mcp.json with correct paths
```

**Check 5: Restart Cursor completely**
- Close all Cursor windows
- Wait 5 seconds
- Reopen Cursor
- Wait for status bar to update

---

### Issue: JSON Syntax Error in mcp.json

**Look for common mistakes:**
- Missing commas between properties
- Trailing commas after last property
- Unescaped backslashes in paths
- Missing quotes around values

**Fix:**
```bash
# View mcp.json
cat ~/.cursor/mcp.json

# Validate with Python
python3.14 -c "import json; json.load(open(open('~/.cursor/mcp.json')))"
```

---

### Issue: "python3.14: command not found"

**Solution:**
```bash
# Check if Python 3.14 is installed
python3.14 --version

# If not found, install it:
# Ubuntu/Debian:
sudo apt install python3.14

# Fedora:
sudo dnf install python3.14

# macOS:
brew install python@3.14
```

---

### Issue: "No module named 'workshop_mcp_server'"

**Solution:**
```bash
# Reinstall the project
cd ~/Documents/workshop-mcp-server
python3.14 -m pip install --user -e .

# Verify installation
python3.14 -c "import workshop_mcp_server; print('✅ Installed')"
```

---

### Issue: "Permission denied" errors

**Solution:**
```bash
# Fix ~/.local permissions
chmod -R u+w ~/.local/lib/python3.14
chmod -R u+w ~/.local/bin

# Reinstall
python3.14 -m pip install --user --force-reinstall -e .
```

---

### Issue: Cursor Output Panel Shows MCP Errors

**View detailed error logs:**

1. In Cursor, open the **Output** panel:
   - View > Output (or Ctrl+Shift+U)

2. In the dropdown on the right, select **"MCP"** or **"workshop-mcp-server"**

3. Look for error messages that tell you what's wrong

4. Common errors:
   - `ModuleNotFoundError` → Reinstall with `python3.14 -m pip install --user -e .`
   - `FileNotFoundError` → Check paths in mcp.json
   - `ConnectionError` → Restart Cursor and check Python version

---

## Advanced: Manual MCP Configuration (Alternative)

If using Cursor Settings GUI (instead of editing mcp.json manually):

1. Open Cursor Settings: `Cmd+,` (macOS) or `Ctrl+,` (Linux/Windows)
2. Search for "MCP"
3. Find "MCP Servers" section
4. Click "Add Server"
5. Fill in:
   - **Name:** `workshop-mcp-server`
   - **Command:** `python3.14`
   - **Args:** `/home/USERNAME/Documents/workshop-mcp-server/workshop_mcp_server/src/main.py`
   - **CWD:** `/home/USERNAME/Documents/workshop-mcp-server`
   - **Environment:** `PYTHONPATH=/home/USERNAME/Documents/workshop-mcp-server`

---

## Quick Reference

| Item | Value |
|------|-------|
| **Config File** | `~/.cursor/mcp.json` |
| **Python Command** | `python3.14` |
| **Main Script** | `workshop_mcp_server/src/main.py` |
| **Project Path** | `/home/USERNAME/Documents/workshop-mcp-server` |
| **Status Check** | Bottom status bar of Cursor |
| **Restart Command** | `Cmd+Shift+P` → "Developer: Reload Window" |

---

## Verification Checklist

Before considering setup complete, verify all of these:

- [ ] `~/.cursor/mcp.json` exists and is valid JSON
- [ ] All paths in mcp.json exist on your system
- [ ] `python3.14 --version` works in terminal
- [ ] `timeout 5 python3.14 workshop_mcp_server/src/main.py` shows FastMCP banner
- [ ] Cursor status bar shows `workshop-mcp-server: Connected` (green dot)
- [ ] `@workshop-mcp-server` appears in Cursor chat with @ symbol
- [ ] You can see tool names when clicking on workshop-mcp-server

Once all checks pass, you're ready to use the MCP Server! 🎉

---

## Next Steps

After connection is verified:
1. Read the main [README.md](./README.md) for tool descriptions
2. Try asking the LLM a question using `@workshop-mcp-server`
3. Explore different tools through the command palette
4. Check the [SETUP_GUIDE.md](./SETUP_GUIDE.md) for troubleshooting

For issues, refer to the [Troubleshooting](#troubleshooting) section above.
