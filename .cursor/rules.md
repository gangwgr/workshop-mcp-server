# Template MCP Server Development Rules

## 🎯 Rule Organization

This MCP server template follows a **three-file rule system** for optimal development guidance:

### 📋 **MCP Technical Rules** → `.cursor/mcp-rules.md`
**Technical patterns, best practices, and MCP development standards:**
- Python & FastAPI expertise patterns
- MCP Protocol mastery and tool development
- Enterprise containerization with Red Hat standards
- Testing excellence and development workflows
- AI assistant guidelines and quality practices

### 🔧 **Template Transformation Guide** → `.cursor/template-transform-rules.md`
**Complete process for transforming this template into domain-specific MCP servers:**
- Step-by-step transformation methodology
- Domain-specific development strategies
- Real-world transformation lessons learned
- Production readiness checklist
- Developer setup and verification procedures

---

## 🚨 **Critical Instructions for AI Assistants**

**ALWAYS consult the appropriate rule file:**

### For Technical Questions:
- MCP tool development → **`.cursor/mcp-rules.md`**
- FastAPI integration → **`.cursor/mcp-rules.md`**
- Container testing → **`.cursor/mcp-rules.md`**
- Code patterns → **`.cursor/mcp-rules.md`**
- Testing strategies → **`.cursor/mcp-rules.md`**

### For Transformation Questions:
- Template customization → **`.cursor/template-transform-rules.md`**
- Domain-specific development → **`.cursor/template-transform-rules.md`**
- Package renaming → **`.cursor/template-transform-rules.md`**
- Production deployment → **`.cursor/template-transform-rules.md`**
- Business logic implementation → **`.cursor/template-transform-rules.md`**

---

## ✅ **Current Template Status: Simplified Tools-First Architecture**

This template has been **optimized for maximum agent compatibility** with a simplified, tools-first design:

**🎯 Core Design Philosophy:**
- **Everything as Tools**: All functionality (math operations, code review, asset access) implemented as MCP tools
- **Universal Compatibility**: Works with ALL MCP clients (LangGraph, CrewAI, Claude Desktop, etc.)
- **Simplified Structure**: Single `src/tools/` directory contains all functionality
- **Easy Extension**: Adding capabilities is as simple as creating a new tool

**🏗️ Architecture Benefits:**
- **Maximum Compatibility**: Tools work with any MCP client
- **Consistent Interface**: All functionality accessed through the same tool protocol
- **Easy Testing**: All features can be tested using the same patterns
- **Future-Proof**: As MCP evolves, tools remain the most stable interface

**🔧 Template Structure:**
```
template_mcp_server/
├── src/
│   ├── tools/               # All MCP functionality as tools
│   │   ├── multiply_tool.py        # Mathematical operations
│   │   ├── code_review_tool.py     # Code analysis (converted from prompt)
│   │   └── redhat_logo_tool.py     # Asset access (converted from resource)
│   ├── assets/              # Static assets accessed by tools
│   │   └── redhat.png       # Logo and other static files
│   ├── main.py              # FastAPI application entry point
│   ├── api.py               # FastAPI routes and middleware
│   ├── mcp.py               # MCP server implementation
│   └── settings.py          # Pydantic settings management
├── utils/
│   └── pylogger.py          # Structured logging utilities
├── examples/                # Client integration examples
├── tests/                   # Comprehensive test suite
└── openshift/              # Enterprise deployment configs
```

**🎯 Ready-to-Use Capabilities:**
- **Mathematical Operations**: `multiply_numbers` tool for arithmetic
- **Code Analysis**: `generate_code_review_prompt` tool for code review
- **Asset Access**: `get_redhat_logo` tool for retrieving logo as base64
- **Comprehensive Testing**: Full test coverage for all tools
- **Production Deployment**: Container-ready with OpenShift configs

---

## 🚀 **Quick Start for Template Users**

1. **For Template Development**: Consult **`.cursor/mcp-rules.md`** for technical patterns
2. **For Template Transformation**: Follow **`.cursor/template-transform-rules.md`** for complete guidance
3. **For Both**: Use this file as your router to the appropriate specialized guidance

---

**📚 For detailed guidance, always reference the appropriate specialized rule file!**
