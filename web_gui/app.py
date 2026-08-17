"""Web GUI for MCP Server.

A Flask-based web interface for Must-Gather Analyzer, Cluster Debugger, and AI/LLM tools.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import sys
import os
import re
import json

# Load .env file before anything else (always overrides shell env)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _key, _val = _line.split('=', 1)
                os.environ[_key.strip()] = _val.strip()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from workshop_mcp_server.src.tools.mustgather_analyzer_tool import analyze_mustgather_bundle
    MUSTGATHER_AVAILABLE = True
    print("✅ Must-Gather analyzer loaded")
except ImportError as e:
    print(f"⚠️  Must-Gather analyzer not available: {e}")
    MUSTGATHER_AVAILABLE = False

try:
    from workshop_mcp_server.src.tools.ocp_cluster_debugger_agent_tool import debug_openshift_cluster
    CLUSTER_DEBUG_AVAILABLE = True
    print("✅ Cluster debugger loaded")
except ImportError as e:
    print(f"⚠️  Cluster debugger not available: {e}")
    CLUSTER_DEBUG_AVAILABLE = False

# RAG / Knowledge Base
try:
    from workshop_mcp_server.src.tools.rag.rag_tool import ask_docs, index_docs, index_repo, index_web, list_knowledge_bases, delete_knowledge_base
    from workshop_mcp_server.src.tools.rag.kb_context import get_kb_context
    RAG_AVAILABLE = True
    print("✅ RAG Knowledge Base loaded")
except ImportError as e:
    print(f"⚠️  RAG not available: {e}")
    RAG_AVAILABLE = False
    def get_kb_context(*args, **kwargs):
        return ""

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mcp-server-secret-key-change-in-production'

@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@app.route('/mustgather-analyzer')
def mustgather_analyzer():
    """Must-Gather analyzer page."""
    return render_template('mustgather_analyzer.html')

@app.route('/cluster-debugger')
def cluster_debugger():
    """Cluster debugger agent page."""
    return render_template('cluster_debugger.html')

@app.route('/settings')
def settings_page():
    """Settings page for credentials and configuration."""
    return render_template('settings.html')


@app.route('/cursor-setup')
def cursor_setup_page():
    """Cursor IDE + Agent integration guide and MCP config."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    from web_gui.slash_commands import get_mcp_config_snippet, list_commands, list_cursor_commands
    return render_template(
        'cursor_setup.html',
        repo_root=repo_root,
        mcp_config=get_mcp_config_snippet(repo_root),
        slash_commands=list_commands(),
        cursor_commands=list_cursor_commands(),
    )


@app.route('/api/commands', methods=['GET'])
def api_commands_list():
    """List available slash commands for the web UI."""
    from web_gui.slash_commands import list_commands
    scope = request.args.get('scope')
    return jsonify({'status': 'success', 'commands': list_commands(scope)})


@app.route('/api/commands/run', methods=['POST'])
def api_commands_run():
    """Execute a slash command (server-handled subset)."""
    from web_gui.slash_commands import parse_slash_input, format_help, get_mcp_config_snippet

    data = request.json or {}
    parsed = parse_slash_input(data.get('input', ''))
    scope = data.get('scope', 'global')
    if not parsed:
        return jsonify({'status': 'error', 'error': 'Not a slash command'}), 400

    cmd = parsed['command']
    args = parsed['args']
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    if cmd == 'help':
        return jsonify({
            'status': 'success', 'handled': True, 'command': 'help',
            'format': 'markdown', 'message': format_help(scope),
        })

    if cmd == 'status':
        try:
            from workshop_mcp_server.src.tools.llm_provider import get_config, get_availability_status
            cfg = get_config()
            avail = get_availability_status()
        except ImportError:
            return jsonify({'handled': True, 'message': 'LLM provider not available'})

        msg = (
            f"Mode: **{cfg['mode']}**\n"
            f"Model: **{cfg['model']}**\n"
            f"Available: **{avail['available']}**\n"
        )
        if not avail['available']:
            msg += f"Reason: {avail.get('reason', '')}\nHint: {avail.get('hint', '')}\n"
        msg += f"Cursor configured: {cfg.get('cursor_configured')}\n"
        msg += f"Claude configured: {cfg.get('claude_configured')}\n"
        msg += f"Cursor attach MCP: {cfg.get('cursor_attach_mcp')}"
        return jsonify({'status': 'success', 'handled': True, 'command': 'status', 'format': 'markdown', 'message': msg})

    if cmd == 'mode':
        parts = args.split(None, 1)
        new_mode = parts[0].lower() if parts else ''
        new_model = parts[1].strip() if len(parts) > 1 else ''
        if new_mode not in ('ollama', 'claude', 'cursor', 'template'):
            return jsonify({'handled': True, 'message': 'Usage: /mode <ollama|claude|cursor|template> [model]'})

        from workshop_mcp_server.src.tools.llm_provider import set_mode, set_model, get_config, get_availability_status
        set_mode(new_mode)
        if new_model:
            set_model(new_model)
        cfg = get_config()
        avail = get_availability_status()
        return jsonify({
            'status': 'success', 'handled': True, 'command': 'mode', 'action': 'switch_mode',
            'mode': cfg['mode'], 'model': cfg['model'],
            'llm_available': avail.get('available'),
            'message': f"Switched to **{cfg['mode']}** ({cfg['model']})",
        })

    if cmd == 'model':
        if not args:
            return jsonify({'handled': True, 'message': 'Usage: /model <model-name>'})
        from workshop_mcp_server.src.tools.llm_provider import set_model, get_config
        set_model(args)
        cfg = get_config()
        return jsonify({
            'status': 'success', 'handled': True, 'command': 'model', 'action': 'switch_mode',
            'mode': cfg['mode'], 'model': cfg['model'],
            'message': f"Model set to **{cfg['model']}**",
        })

    if cmd == 'cursor_config':
        msg = (
            "**Cursor Agent setup (Web UI)**\n\n"
            "1. Get API key: https://cursor.com/dashboard/integrations\n"
            "2. Settings → Cursor Agent → `CURSOR_API_KEY`\n"
            "3. Set model (default: `composer-2.5`)\n"
            "4. Top nav → **Cursor Agent** mode\n\n"
            f"CURSOR_ATTACH_MCP: {os.environ.get('CURSOR_ATTACH_MCP', 'true')}\n"
            f"CURSOR_CWD: {os.environ.get('CURSOR_CWD') or repo_root}\n"
            f"API key configured: {bool(os.environ.get('CURSOR_API_KEY'))}"
        )
        return jsonify({'status': 'success', 'handled': True, 'format': 'markdown', 'message': msg})

    if cmd == 'mcp_config':
        snippet = get_mcp_config_snippet(repo_root)
        msg = (
            "**Cursor IDE MCP config** (`.cursor/mcp.json` or `~/.cursor/mcp.json`):\n\n"
            f"```json\n{snippet}\n```\n\n"
            "Restart Cursor after saving. Tools: analyze_mustgather_bundle, debug_openshift_cluster, ask_docs, etc."
        )
        return jsonify({'status': 'success', 'handled': True, 'format': 'markdown', 'message': msg})

    if cmd == 'ask_kb':
        if not args:
            return jsonify({'handled': True, 'message': 'Usage: /ask-kb <question>'})
        try:
            from workshop_mcp_server.src.tools.rag.rag_tool import ask_docs
            result = ask_docs(args)
        except ImportError:
            return jsonify({'handled': True, 'message': 'Knowledge base (RAG) not available'})
        if result.get('status') == 'error':
            return jsonify({'handled': True, 'message': result.get('error', 'Query failed') + (f"\n{result.get('hint', '')}" if result.get('hint') else '')})
        return jsonify({
            'status': 'success', 'handled': True, 'command': 'ask_kb',
            'format': 'markdown', 'message': result.get('answer', 'No answer'),
        })

    if cmd == 'list_kb':
        try:
            from workshop_mcp_server.src.tools.rag.rag_tool import list_knowledge_bases
            result = list_knowledge_bases()
        except ImportError:
            return jsonify({'handled': True, 'message': 'Knowledge base (RAG) not available'})
        collections = result.get('collections') or []
        if not collections:
            msg = "No indexed collections yet. Use `/index-kb <folder-path>` to add documents."
        else:
            lines = ["**Knowledge base collections**", ""]
            for col in collections:
                name = col.get('name') or col.get('collection') or 'unknown'
                count = col.get('count') or col.get('document_count') or 0
                lines.append(f"- `{name}` — {count} documents")
            msg = "\n".join(lines)
        return jsonify({'status': 'success', 'handled': True, 'format': 'markdown', 'message': msg})

    if cmd == 'index_kb':
        parts = args.split(None, 1)
        folder = parts[0] if parts else ''
        collection = parts[1].strip() if len(parts) > 1 else 'default'
        if not folder:
            return jsonify({'handled': True, 'message': 'Usage: /index-kb <folder-path> [collection-name]'})
        if not os.path.isdir(folder):
            return jsonify({'handled': True, 'message': f"Folder not found: {folder}"})
        try:
            from workshop_mcp_server.src.tools.rag.rag_tool import index_docs
            result = index_docs(folder, collection)
        except ImportError:
            return jsonify({'handled': True, 'message': 'Knowledge base (RAG) not available'})
        if result.get('status') == 'error':
            return jsonify({'handled': True, 'message': result.get('error', 'Indexing failed')})
        msg = (
            f"Indexed **{result.get('chunks_indexed', result.get('documents_indexed', '?'))}** chunks "
            f"into collection `{collection}` from `{folder}`"
        )
        return jsonify({'status': 'success', 'handled': True, 'format': 'markdown', 'message': msg})

    return jsonify({
        'handled': False,
        'message': f"Unknown command `/{cmd}`. Try /help",
    })

@app.route('/api/settings', methods=['GET'])
def api_settings_get():
    """Get current settings (masked secrets)."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
    env_path = os.path.abspath(env_path)

    settings = {
        'GITHUB_USER': os.environ.get('GITHUB_USER', ''),
        'GITHUB_TOKEN': '***' if os.environ.get('GITHUB_TOKEN') else '',
        'JIRA_URL': os.environ.get('JIRA_URL', ''),
        'JIRA_TOKEN': '***' if os.environ.get('JIRA_TOKEN') else '',
        'JIRA_USERNAME': os.environ.get('JIRA_USERNAME', ''),
        'ANTHROPIC_API_KEY': '***' if os.environ.get('ANTHROPIC_API_KEY') else '',
        'OLLAMA_BASE_URL': os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434'),
        'OLLAMA_MODEL': os.environ.get('OLLAMA_MODEL', 'llama3'),
        'CLAUDE_MODEL': os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-5@20250929'),
        'LLM_MODE': os.environ.get('LLM_MODE', 'ollama'),
        'CURSOR_API_KEY': '***' if os.environ.get('CURSOR_API_KEY') else '',
        'CURSOR_MODEL': os.environ.get('CURSOR_MODEL', 'composer-2.5'),
        'CURSOR_CWD': os.environ.get('CURSOR_CWD', ''),
        'CURSOR_ATTACH_MCP': os.environ.get('CURSOR_ATTACH_MCP', 'true'),
        'CLAUDE_CODE_USE_VERTEX': os.environ.get('CLAUDE_CODE_USE_VERTEX', ''),
        'ANTHROPIC_VERTEX_PROJECT_ID': os.environ.get('ANTHROPIC_VERTEX_PROJECT_ID', ''),
        'CLOUD_ML_REGION': os.environ.get('CLOUD_ML_REGION', ''),
        'GIT_AUTHOR_NAME': os.environ.get('GIT_AUTHOR_NAME', ''),
        'RAG_ENABLED': os.environ.get('RAG_ENABLED', 'true'),
        'env_file': env_path,
        'env_exists': os.path.isfile(env_path),
    }
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def api_settings_save():
    """Save settings to .env file and update runtime."""
    data = request.json
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
    env_path = os.path.abspath(env_path)

    # Keys we allow saving
    allowed_keys = [
        'GITHUB_USER', 'GITHUB_TOKEN',
        'JIRA_URL', 'JIRA_TOKEN', 'JIRA_USERNAME',
        'ANTHROPIC_API_KEY',
        'OLLAMA_BASE_URL', 'OLLAMA_MODEL', 'CLAUDE_MODEL', 'LLM_MODE',
        'CURSOR_API_KEY', 'CURSOR_MODEL', 'CURSOR_CWD', 'CURSOR_ATTACH_MCP',
        'CLAUDE_CODE_USE_VERTEX', 'ANTHROPIC_VERTEX_PROJECT_ID', 'CLOUD_ML_REGION',
        'GIT_AUTHOR_NAME', 'RAG_ENABLED',
    ]

    # Read existing .env
    existing_lines = []
    existing_keys = {}
    if os.path.isfile(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                existing_lines.append(line)
                if '=' in line and not line.strip().startswith('#'):
                    key = line.split('=', 1)[0].strip()
                    existing_keys[key] = len(existing_lines) - 1

    # Update values
    updated = []
    for key in allowed_keys:
        value = data.get(key, '')
        if not value or value == '***':
            continue  # Skip masked/empty values

        os.environ[key] = value
        updated.append(key)

        if key in existing_keys:
            idx = existing_keys[key]
            existing_lines[idx] = f"{key}={value}\n"
        else:
            existing_lines.append(f"{key}={value}\n")

    # Write back
    with open(env_path, 'w') as f:
        f.writelines(existing_lines)

    # Update LLM provider runtime config if applicable
    try:
        from workshop_mcp_server.src.tools.llm_provider import set_mode, set_model, _runtime_config
        if 'LLM_MODE' in data and data['LLM_MODE'] != '***':
            set_mode(data['LLM_MODE'])
        if 'OLLAMA_MODEL' in data and data['OLLAMA_MODEL'] != '***':
            _runtime_config['ollama_model'] = data['OLLAMA_MODEL']
        if 'CLAUDE_MODEL' in data and data['CLAUDE_MODEL'] != '***':
            _runtime_config['claude_model'] = data['CLAUDE_MODEL']
        if 'CURSOR_MODEL' in data and data['CURSOR_MODEL'] != '***':
            _runtime_config['cursor_model'] = data['CURSOR_MODEL']
    except Exception:
        pass

    return jsonify({'status': 'success', 'updated': updated, 'env_file': env_path})


# ============================================================
# Must-Gather Analyzer API
# ============================================================

@app.route('/api/mustgather-scripts', methods=['GET'])
def api_mustgather_scripts_list():
    """List ai-helpers must-gather analysis scripts."""
    try:
        from mustgather_scripts import list_scripts, QUICK_PRESETS
        return jsonify({
            'status': 'success',
            'scripts': list_scripts(),
            'presets': [
                {'id': k, 'label': v['label'], 'scripts': v['scripts']}
                for k, v in QUICK_PRESETS.items()
            ],
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/run-mustgather-script', methods=['POST'])
def api_run_mustgather_script():
    """Run a single must-gather analysis script (ai-helpers)."""
    try:
        from mustgather_scripts import run_script, run_preset

        data = request.json or {}
        bundle_path = (data.get('bundle_path') or '').strip()
        if not bundle_path:
            return jsonify({'status': 'error', 'error': 'bundle_path is required'}), 400

        # If it's a URL, download it first
        if bundle_path.startswith('http://') or bundle_path.startswith('https://'):
            try:
                bundle_path = _download_bundle_from_url(bundle_path)
            except Exception as dl_err:
                return jsonify({'status': 'error', 'error': f'Download failed: {str(dl_err)}'}), 400

        preset_id = data.get('preset')
        if preset_id:
            return jsonify(run_preset(preset_id, bundle_path))

        script_id = data.get('script_id')
        if not script_id:
            return jsonify({'status': 'error', 'error': 'script_id or preset is required'}), 400

        result = run_script(
            script_id=script_id,
            bundle_path=bundle_path,
            namespace=data.get('namespace') or None,
            problems_only=bool(data.get('problems_only')),
            event_type=data.get('event_type') or None,
            count=data.get('count'),
        )
        status_code = 200 if result.get('status') == 'success' else 500
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


def _download_bundle_from_url(url: str) -> str:
    """Download a must-gather bundle from URL (unique cache per URL)."""
    from workshop_mcp_server.src.tools.mustgather_download import download_bundle_from_url
    return download_bundle_from_url(url)


@app.route('/api/download-bundle', methods=['POST'])
def api_download_bundle():
    """Download a must-gather bundle from URL and return the local path."""
    try:
        data = request.json or {}
        url = (data.get('url') or '').strip()
        if not url:
            return jsonify({'status': 'error', 'error': 'url is required'}), 400
        if not url.startswith('http://') and not url.startswith('https://'):
            return jsonify({'status': 'error', 'error': 'Invalid URL'}), 400

        local_path = _download_bundle_from_url(url)
        file_size = os.path.getsize(local_path)
        return jsonify({
            'status': 'success',
            'local_path': local_path,
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 1)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/analyze-mustgather', methods=['POST'])
def api_analyze_mustgather():
    """API endpoint for must-gather analysis."""
    try:
        import asyncio
        import concurrent.futures
        data = request.json

        bundle_path = data.get('bundle_path', '')
        detailed_analysis = data.get('detailed_analysis', True)

        if not bundle_path or not bundle_path.strip():
            return jsonify({
                'status': 'error',
                'error': 'Bundle path is required'
            }), 400

        # If it's a URL, download it first
        if bundle_path.startswith('http://') or bundle_path.startswith('https://'):
            try:
                bundle_path = _download_bundle_from_url(bundle_path)
            except Exception as dl_err:
                return jsonify({
                    'status': 'error',
                    'error': f'Failed to download bundle from URL: {str(dl_err)}'
                }), 400

        # Check if path exists
        if not os.path.exists(bundle_path):
            return jsonify({
                'status': 'error',
                'error': f'Path not found: {bundle_path}'
            }), 400

        # Run analysis with timeout using subprocess
        import subprocess as _sp
        import json as _json
        import tempfile

        # Write a small script to run the analysis and output JSON
        script = f"""
import sys, json, asyncio
sys.path.insert(0, '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}')
from workshop_mcp_server.src.tools.mustgather_analyzer_tool import analyze_mustgather_bundle
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(analyze_mustgather_bundle({repr(bundle_path)}, {repr(detailed_analysis)}))
    print(json.dumps(result, default=str))
except Exception as e:
    print(json.dumps({{"status": "error", "error": str(e)}}))
finally:
    loop.close()
"""
        try:
            proc_result = _sp.run(
                [sys.executable, '-c', script],
                capture_output=True, text=True, timeout=300,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            if proc_result.returncode == 0 and proc_result.stdout.strip():
                result = _json.loads(proc_result.stdout.strip().split('\n')[-1])
            else:
                error_msg = proc_result.stderr.strip()[-500:] if proc_result.stderr else 'Unknown error'
                result = {"status": "error", "error": f"Analysis failed: {error_msg}"}
        except _sp.TimeoutExpired:
            result = {"status": "error", "error": "Analysis timed out (300s). Try unchecking Deep log scanning or use a smaller bundle."}

        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/analyze-component', methods=['POST'])
def api_analyze_component():
    """LLM-powered deep analysis for a specific component from must-gather data."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate_with_fallback, get_availability_status

        data = request.json
        component = data.get('component', '')
        script_output = data.get('script_output', '')
        issues = data.get('issues', [])
        critical_logs = data.get('critical_logs', [])
        cluster_health = data.get('cluster_health', {})
        sre_report = data.get('sre_report', '')

        if not component:
            return jsonify({'status': 'error', 'error': 'component is required'}), 400

        import json
        issues_text = "\n".join([
            f"- [{i.get('severity','?').upper()}] {i.get('title','')}: {i.get('description','')}"
            for i in issues[:15]
        ])
        logs_text = "\n".join([
            f"- [{l.get('tag','log')}] {l.get('file','')}: {l.get('message','')}"
            for l in critical_logs[:20]
        ])

        # Extract SRE report text
        sre_text = ''
        if isinstance(sre_report, dict):
            sre_text = f"PRIMARY ISSUE: {sre_report.get('primary_issue', '')}\n"
            sre_text += f"ROOT CAUSE: {sre_report.get('root_cause_summary', '')}\n"
            sre_text += f"EVIDENCE: {sre_report.get('evidence', '')}\n"
            sre_text += f"IMPACT: {sre_report.get('impact', '')}"
        elif isinstance(sre_report, str):
            sre_text = sre_report[:2000]

        # Load past user corrections as context
        learnings_context = _get_relevant_learnings(component, issues_text)
        learnings_section = ""
        if learnings_context:
            learnings_section = f"""

IMPORTANT — PAST USER CORRECTIONS (learn from these):
{learnings_context}
Use these corrections to avoid repeating the same mistakes. If a user previously told you
the real issue was X, prioritize that pattern when you see similar evidence."""

        system_prompt = f"""You are an expert OpenShift/Kubernetes SRE analyzing an OFFLINE must-gather bundle.
You must provide a precise, actionable root-cause analysis based ONLY on the evidence provided.
Focus on the PRIMARY root cause — not symptoms. If the cluster has a stuck upgrade, say so directly.
Do NOT speculate about "resource exhaustion" or "etcd performance" unless logs explicitly show it.
Structure your answer as:
1. ROOT CAUSE (one sentence — the primary issue)
2. EVIDENCE (what data proves this)
3. CASCADING EFFECTS (what other symptoms are caused by the root issue)
4. REMEDIATION (specific steps using bundle paths, no live commands)
Be concise — max 400 words.{learnings_section}"""

        prompt = f"""Analyze this OpenShift cluster must-gather bundle:

CLUSTER STATUS: {cluster_health.get('status', 'unknown').upper()} — {cluster_health.get('summary', '')}
Critical issues: {cluster_health.get('critical_issues', 0)}, Warnings: {cluster_health.get('warnings', 0)}

SRE DIAGNOSTIC (already identified):
{sre_text if sre_text else 'Not available'}

SCRIPT OUTPUT (operator status, pod status, cluster version):
{script_output[:4000] if script_output else 'No script output'}

DETECTED ISSUES:
{issues_text if issues_text else 'None'}

CRITICAL LOGS:
{logs_text if logs_text else 'None'}

Provide root-cause analysis:"""

        # Inject RAG context if available (KB articles, runbooks, past solutions)
        kb_context = get_kb_context(
            f"OpenShift {component} troubleshooting root cause {issues_text[:200]}",
            collections=None, top_k=3, max_chars=1500
        )
        if kb_context:
            prompt += f"\n\nRELEVANT KNOWLEDGE BASE ARTICLES:\n{kb_context}"

        result, meta = generate_with_fallback(prompt, system=system_prompt)
        if not result:
            status = get_availability_status()
            err = meta.get("error") or status.get("reason") or "LLM not available"
            hint = meta.get("hint") or status.get("hint") or ""
            message = f"{err} {hint}".strip()
            return jsonify({'status': 'error', 'error': message, 'llm_meta': meta})

        return jsonify({
            'status': 'success',
            'analysis': result,
            'component': component,
            'llm_meta': meta,
        })
    except ImportError:
        return jsonify({'status': 'error', 'error': 'LLM provider not available'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


MUSTGATHER_FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), 'mustgather_learnings.json')


def _load_learnings():
    """Load stored user corrections/learnings."""
    if os.path.exists(MUSTGATHER_FEEDBACK_FILE):
        try:
            with open(MUSTGATHER_FEEDBACK_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_learning(entry):
    """Save a new user correction."""
    learnings = _load_learnings()
    learnings.append(entry)
    # Keep last 50 learnings
    learnings = learnings[-50:]
    with open(MUSTGATHER_FEEDBACK_FILE, 'w') as f:
        json.dump(learnings, f, indent=2)


def _get_relevant_learnings(component, issues_text):
    """Get learnings relevant to the current analysis."""
    learnings = _load_learnings()
    if not learnings:
        return ''

    relevant = []
    for l in learnings[-20:]:
        # Match by component or by overlapping keywords
        if (l.get('component', '').lower() in component.lower() or
            component.lower() in l.get('component', '').lower() or
            any(kw in issues_text.lower() for kw in l.get('keywords', []))):
            relevant.append(l)

    if not relevant:
        # Show last 5 general learnings as context
        relevant = learnings[-5:]

    if relevant:
        lines = []
        for r in relevant[-5:]:
            lines.append(f"- [{r.get('component', '?')}] User correction: {r.get('correction', '')}")
        return "\n".join(lines)
    return ''


@app.route('/api/mustgather-feedback', methods=['POST'])
def api_mustgather_feedback():
    """Store user feedback/correction for must-gather analysis."""
    try:
        data = request.json
        component = data.get('component', '')
        correction = data.get('correction', '')
        timestamp = data.get('timestamp', '')

        if not correction:
            return jsonify({'status': 'error', 'error': 'correction is required'}), 400

        # Extract keywords from the correction for future matching
        keywords = [w.lower() for w in correction.split() if len(w) > 4][:10]

        entry = {
            'component': component,
            'correction': correction,
            'keywords': keywords,
            'timestamp': timestamp
        }
        _save_learning(entry)

        return jsonify({'status': 'success', 'message': 'Feedback saved'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/chat-mustgather', methods=['POST'])
def api_chat_mustgather():
    """API endpoint for chatting about must-gather analysis."""
    try:
        data = request.json
        question = data.get('question', '')
        analysis_context = data.get('analysis_context', {})

        if not question or not question.strip():
            return jsonify({
                'status': 'error',
                'error': 'Question is required'
            }), 400

        if not analysis_context:
            return jsonify({
                'status': 'error',
                'error': 'Analysis context is required. Please run an analysis first.'
            }), 400

        # Build context for the AI
        context = _build_chat_context(analysis_context)

        # Generate answer using the analysis context
        answer = _generate_answer(question, context, analysis_context)

        return jsonify({
            'status': 'success',
            'answer': answer,
            'question': question
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

def _build_chat_context(analysis):
    """Build a context summary from analysis results."""
    context_parts = []

    # Add cluster health
    if 'cluster_health' in analysis:
        health = analysis['cluster_health']
        context_parts.append(f"Cluster Status: {health.get('status', 'unknown')}")
        context_parts.append(f"Critical Issues: {health.get('critical_issues', 0)}")
        context_parts.append(f"Warnings: {health.get('warnings', 0)}")
        context_parts.append(f"Summary: {health.get('summary', 'N/A')}")

    # Add SRE report
    if 'sre_diagnostic_report' in analysis:
        sre = analysis['sre_diagnostic_report']
        context_parts.append(f"\nPrimary Issue: {sre.get('primary_issue', 'N/A')}")
        context_parts.append(f"Root Cause: {sre.get('root_cause_summary', 'N/A')}")

    # Add anomaly detection
    if 'anomaly_detection_result' in analysis:
        anomaly = analysis['anomaly_detection_result']
        context_parts.append(f"\nAnomaly Status: {anomaly.get('status', 'unknown')}")
        context_parts.append(f"Severity: {anomaly.get('severity', 'unknown')}")

    # Add focused script output (cluster version, operators, pods, nodes)
    if analysis.get('unified_report'):
        context_parts.append(f"\nComplete Diagnostic Report:\n{analysis['unified_report'][:4000]}")
    elif analysis.get('script_output'):
        context_parts.append(f"\nFocused Script Output:\n{analysis['script_output'][:3000]}")

    return "\n".join(context_parts)

def _generate_answer(question, context, analysis):
    """Generate an answer based on the question and analysis context."""
    # Try LLM-powered answer first
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available
        if is_available():
            import json
            context_str = json.dumps(analysis, indent=2, default=str)[:3000]
            system = """You are an expert OpenShift SRE analyzing an OFFLINE must-gather bundle.
The user does NOT have live cluster access. Answer only from the analysis context.
Do NOT suggest live oc, ssh, crictl, or systemctl commands.
Reference bundle paths (cluster-scoped-resources/, namespaces/, static-pods/) when helpful.
For live triage, mention cluster-debugger only if the user explicitly asks about live access."""
            prompt = f"Must-gather analysis context:\n{context_str}\n\nUser question: {question}"
            llm_answer = generate(prompt, system=system)
            if llm_answer:
                return llm_answer
    except Exception:
        pass

    question_lower = question.lower()

    # Root cause questions
    if any(word in question_lower for word in ['root cause', 'why', 'what caused', 'reason']):
        sre = analysis.get('sre_diagnostic_report', {})
        primary_issue = sre.get('primary_issue', 'Unknown issue')
        root_cause = sre.get('root_cause_summary', 'Root cause analysis not available.')
        evidence = sre.get('evidence', '')

        answer = f"ROOT CAUSE ANALYSIS:\n\n"
        answer += f"Primary Issue: {primary_issue}\n\n"
        answer += f"Explanation: {root_cause}\n\n"
        if evidence and len(evidence) < 500:
            answer += f"Evidence:\n{evidence[:500]}"

        return answer

    # Fix/solution questions
    elif any(word in question_lower for word in ['fix', 'solve', 'resolve', 'how to', 'steps']):
        sre = analysis.get('sre_diagnostic_report', {})
        immediate_actions = sre.get('immediate_actions', [])

        answer = "RECOMMENDED ACTIONS:\n\n"
        if immediate_actions:
            answer += "Immediate steps to take:\n"
            for i, action in enumerate(immediate_actions, 1):
                answer += f"{i}. {action}\n"
        else:
            answer += "No specific actions recommended. Review the full analysis report for details."

        return answer

    # Priority questions
    elif any(word in question_lower for word in ['priority', 'first', 'start', 'begin']):
        health = analysis.get('cluster_health', {})
        critical_issues = health.get('critical_issues', 0)
        sre = analysis.get('sre_diagnostic_report', {})
        primary_issue = sre.get('primary_issue', 'Unknown')

        answer = f"PRIORITIZATION RECOMMENDATION:\n\n"
        answer += f"You have {critical_issues} critical issues to address.\n\n"
        answer += f"Start with the primary issue:\n{primary_issue}\n\n"

        immediate_actions = sre.get('immediate_actions', [])
        if immediate_actions and len(immediate_actions) > 0:
            answer += f"First step: {immediate_actions[0]}"

        return answer

    # Issues/errors questions
    elif any(word in question_lower for word in ['issue', 'error', 'problem', 'wrong']):
        health = analysis.get('cluster_health', {})
        issues = analysis.get('issues', [])

        critical = [i for i in issues if i.get('severity') == 'critical']
        warnings = [i for i in issues if i.get('severity') == 'warning']

        answer = f"ISSUES SUMMARY:\n\n"
        answer += f"Total Issues: {len(issues)}\n"
        answer += f"Critical: {len(critical)}\n"
        answer += f"Warnings: {len(warnings)}\n\n"

        if critical:
            answer += "Top Critical Issues:\n"
            for i, issue in enumerate(critical[:3], 1):
                answer += f"{i}. {issue.get('title', 'Unknown')} - {issue.get('component', 'N/A')}\n"

        return answer

    # Component-specific questions
    elif any(comp in question_lower for comp in ['operator', 'pod', 'node', 'etcd', 'api', 'storage', 'network']):
        issues = analysis.get('issues', [])

        # Find component mentioned in question
        component = None
        for comp in ['operator', 'pod', 'node', 'etcd', 'api', 'storage', 'network']:
            if comp in question_lower:
                component = comp
                break

        if component:
            component_issues = [i for i in issues if component in i.get('component', '').lower() or component in i.get('category', '').lower()]

            if component_issues:
                answer = f"{component.upper()} ISSUES:\n\n"
                answer += f"Found {len(component_issues)} issues related to {component}.\n\n"

                for i, issue in enumerate(component_issues[:5], 1):
                    answer += f"{i}. [{issue.get('severity', 'unknown').upper()}] {issue.get('title', 'Unknown')}\n"
                    answer += f"   {issue.get('description', 'No description')}\n"
                    if issue.get('suggested_fix'):
                        answer += f"   Fix: {issue.get('suggested_fix')}\n"
                    answer += "\n"

                return answer
            else:
                return f"No specific issues found related to {component}. The component appears to be functioning normally."

    # Health/status questions
    elif any(word in question_lower for word in ['health', 'status', 'state', 'condition']):
        health = analysis.get('cluster_health', {})
        status = health.get('status', 'unknown')
        summary = health.get('summary', 'N/A')

        anomaly = analysis.get('anomaly_detection_result', {})
        anomaly_status = anomaly.get('status', 'unknown')
        severity = anomaly.get('severity', 'unknown')

        answer = f"CLUSTER HEALTH STATUS:\n\n"
        answer += f"Overall Status: {status.upper()}\n"
        answer += f"Health Summary: {summary}\n\n"
        answer += f"Anomaly Detection: {anomaly_status}\n"
        answer += f"Severity Level: {severity}\n"

        return answer

    # Default response
    else:
        answer = "I can help you with:\n\n"
        answer += "- Root cause analysis (ask 'What is the root cause?')\n"
        answer += "- Fix recommendations (ask 'How do I fix this?')\n"
        answer += "- Prioritization (ask 'What should I do first?')\n"
        answer += "- Component details (ask 'Tell me about [component]')\n"
        answer += "- Health status (ask 'What is the cluster health?')\n\n"
        answer += f"Current cluster status: {analysis.get('cluster_health', {}).get('status', 'unknown')}\n"
        answer += f"Critical issues: {analysis.get('cluster_health', {}).get('critical_issues', 0)}"

        return answer


# ============================================================
# Cluster Debugger API
# ============================================================

@app.route('/api/cluster-debugger-workflows', methods=['GET'])
def api_cluster_debugger_workflows():
    """List focused oc diagnostic workflows for cluster debugger."""
    try:
        from cluster_debugger_commands import list_workflows, QUICK_PRESETS
        return jsonify({
            'status': 'success',
            'workflows': list_workflows(),
            'presets': [
                {'id': k, 'label': v['label'], 'workflows': v['workflows']}
                for k, v in QUICK_PRESETS.items()
            ],
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/run-cluster-debugger-workflow', methods=['POST'])
def api_run_cluster_debugger_workflow():
    """Run a focused oc diagnostic workflow or preset."""
    try:
        from cluster_debugger_commands import run_workflow, run_preset

        data = request.json or {}
        oc_path = data.get('oc_path') or None
        kubeconfig_path = data.get('kubeconfig_path') or None
        namespace = data.get('namespace') or None
        component = data.get('component') or None
        operator = data.get('operator') or None

        preset_id = data.get('preset')
        if preset_id:
            result = run_preset(
                preset_id,
                oc_path=oc_path,
                kubeconfig_path=kubeconfig_path,
                namespace=namespace,
                component=component,
                operator=operator,
            )
            status_code = 200 if result.get('status') in ('success', 'partial') else 500
            return jsonify(result), status_code

        workflow_id = data.get('workflow_id')
        if not workflow_id:
            return jsonify({'status': 'error', 'error': 'workflow_id or preset is required'}), 400

        result = run_workflow(
            workflow_id,
            oc_path=oc_path,
            kubeconfig_path=kubeconfig_path,
            namespace=namespace,
            component=component,
            operator=operator,
        )
        status_code = 200 if result.get('status') in ('success', 'partial') else 500
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/analyze-triage-output', methods=['POST'])
def api_analyze_triage_output():
    """Analyze oc triage output using LLM."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available
        if not is_available():
            return jsonify({'status': 'error', 'error': 'LLM not available'}), 503

        data = request.json or {}
        workflow_label = data.get('workflow_label', 'oc triage')
        oc_output = data.get('oc_output', '')

        if not oc_output or len(oc_output.strip()) < 10:
            return jsonify({'status': 'error', 'error': 'No output to analyze'}), 400

        system_prompt = """You are an OpenShift SRE expert reading ACTUAL oc command output.
RULES:
- ONLY state facts you can directly see in the output. Do NOT invent or assume data not shown.
- If pods are listed as Running with all containers Ready, they ARE healthy.
- If a command shows [OK], it succeeded. If [EXIT 1] or [EXIT 2], it failed — explain the error.
- Look for: pod status, restart counts, error messages in logs, events, operator conditions.
- CRITICAL: You MUST analyze and mention EVERY pod shown in the output. The output contains multiple "========" command separators — each pod has its own describe/logs/events block. List each pod by name with its status.
- Format your response as:
  STATUS: ✅ Healthy / ⚠️ Warning / ❌ Critical
  SUMMARY: 2-4 lines covering ALL pods/components
  POD STATUS:
  - pod-name-1: status (restart count, state)
  - pod-name-2: status (restart count, state)
  - pod-name-3: status (restart count, state)
  ISSUES (if any): bullet list of specific problems with evidence"""

        # Smart truncation: strip noise, keep diagnostically important lines
        def _compress_output(text):
            """Remove verbose noise like repeated env vars, mounts, volumes for multi-pod describe output."""
            lines = text.split('\n')
            compressed = []
            skip_env = False
            skip_mounts = False
            skip_volumes = False
            for line in lines:
                stripped = line.strip()

                # Detect section boundaries for each container in oc describe
                if stripped.startswith('Environment:'):
                    skip_env = True
                    compressed.append(line.split('Environment')[0] + 'Environment: [stripped for brevity]')
                    continue
                if skip_env:
                    if stripped == '' or (not line.startswith('      ') and stripped and not stripped.startswith('NODE_') and not stripped.startswith('ETCD') and not stripped.startswith('ALL_')):
                        skip_env = False
                    else:
                        continue

                if stripped.startswith('Mounts:'):
                    skip_mounts = True
                    compressed.append(line.split('Mounts')[0] + 'Mounts: [stripped]')
                    continue
                if skip_mounts:
                    if stripped == '' or (not line.startswith('      ') and stripped and ':' in stripped):
                        skip_mounts = False
                    else:
                        continue

                if stripped.startswith('Volumes:'):
                    skip_volumes = True
                    compressed.append('  Volumes: [stripped]')
                    continue
                if skip_volumes:
                    if stripped.startswith('Conditions:') or stripped.startswith('QoS') or stripped.startswith('Events:') or (stripped.startswith('===')):
                        skip_volumes = False
                    else:
                        continue

                # Skip long image hash lines
                if 'sha256:' in stripped and len(stripped) > 80:
                    continue
                # Skip cipher/TLS config noise
                if 'CIPHER_SUITES' in stripped or 'TLS_AES' in stripped or 'TLS_ECDHE' in stripped:
                    continue
                # Skip feature-gates lines (massive list in KubeAPIServer YAML)
                if stripped.startswith('- ') and '=' in stripped and stripped.endswith(('=true', '=false')):
                    continue
                # Skip YAML config paths (cert files, key files)
                if ('certFile:' in stripped or 'keyFile:' in stripped) and '/etc/kubernetes' in stripped:
                    continue
                # Skip cipherSuites list items
                if stripped.startswith('- TLS_'):
                    continue
                compressed.append(line)
            return '\n'.join(compressed)

        processed = _compress_output(oc_output)

        if len(processed) > 8000:
            lines = processed.split('\n')
            important_keywords = ('error', 'degraded', 'not available',
                                  'failed', 'notready', 'crashloop', 'oomkilled',
                                  'running', 'pending', 'terminating', 'imagepullbackoff',
                                  'restart count', 'restarts',
                                  '1/1', '0/1', '2/2', '0/2', '3/3', '0/3', '4/4', '5/5',
                                  '========', '[ok]', '[exit',
                                  'name:', 'status:', 'ready:', 'available',
                                  'progressing', 'message:', 'conditions:',
                                  'nodename', 'nodestatuses', 'revision')
            important_lines = []
            other_lines = []
            for line in lines:
                lower = line.lower()
                if any(kw.lower() in lower for kw in important_keywords):
                    important_lines.append(line)
                else:
                    other_lines.append(line)

            important_text = '\n'.join(important_lines)
            if len(important_text) > 7500:
                truncated = important_text[:7500]
            else:
                remaining_budget = 7500 - len(important_text)
                other_text = '\n'.join(other_lines[:120])[:remaining_budget]
                truncated = important_text + "\n\n--- Additional context ---\n" + other_text
        else:
            truncated = processed

        prompt = f"""Analyze this oc output from "{workflow_label}":

{truncated}

Summarize the health status of ALL components shown. Base your answer ONLY on the data above."""

        # Inject RAG context for deeper analysis
        kb_context = get_kb_context(
            f"OpenShift {workflow_label} troubleshooting diagnosis",
            collections=None, top_k=2, max_chars=1000
        )
        if kb_context:
            prompt += f"\n\nREFERENCE (from Knowledge Base):\n{kb_context}"

        analysis = generate(prompt, system=system_prompt)
        return jsonify({'status': 'success', 'analysis': analysis})

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/debug-cluster', methods=['POST'])
def api_debug_cluster():
    """API endpoint for cluster debugging with test automation."""
    try:
        import asyncio
        data = request.json

        issue_description = data.get('issue_description', '')
        namespace = data.get('namespace')
        component = data.get('component')
        oc_path = data.get('oc_path')
        kubeconfig_path = data.get('kubeconfig_path')
        include_test_case = data.get('include_test_case', True)

        if not issue_description or not issue_description.strip():
            return jsonify({
                'status': 'error',
                'error': 'Issue description is required'
            }), 400

        # Run async debug in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                debug_openshift_cluster(
                    issue_description=issue_description,
                    namespace=namespace,
                    component=component,
                    oc_path=oc_path,
                    kubeconfig_path=kubeconfig_path,
                    include_test_case=include_test_case
                )
            )
        finally:
            loop.close()

        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/generate-cluster-test', methods=['POST'])
def api_generate_cluster_test():
    """Lightweight endpoint to generate test case without re-running full diagnostics."""
    try:
        data = request.json
        issue_description = data.get('issue_description', '')
        namespace = data.get('namespace')
        component = data.get('component')

        if not issue_description or not issue_description.strip():
            return jsonify({'status': 'error', 'error': 'Issue description is required'}), 400

        from workshop_mcp_server.src.tools.ocp_cluster_debugger_agent_tool import OCPClusterDebuggerAgent
        agent = OCPClusterDebuggerAgent()
        issue_analysis = agent._analyze_issue_description(issue_description)

        # Try LLM-powered test generation first
        test_case = None
        try:
            from workshop_mcp_server.src.tools.llm_provider import generate as llm_generate, is_available
            if is_available():
                llm_prompt = f"""Generate a Go/Ginkgo e2e test case for this OpenShift cluster scenario:

Issue: {issue_description}
Namespace: {namespace or 'openshift-*'}
Component: {component or 'general'}

Generate a complete, runnable Go test using:
- k8s.io/client-go
- github.com/onsi/ginkgo/v2
- github.com/onsi/gomega

The test should validate the issue is resolved (e.g., pod is healthy, operator not degraded).
Return ONLY the Go code, no explanation."""

                llm_code = llm_generate(llm_prompt, system="You are an expert Go/Kubernetes test writer. Return only valid Go code.")
                if llm_code and len(llm_code.strip()) > 50:
                    test_case = {
                        "test_name": f"Test_{issue_description[:50].replace(' ', '_')}",
                        "description": f"Validates: {issue_description}",
                        "go_code": llm_code.strip(),
                        "format": "go"
                    }
        except Exception:
            pass

        # Fallback to template-based generation
        if not test_case:
            test_case = agent._generate_test_case(issue_description, issue_analysis, namespace, component)
            if test_case:
                test_case["test_name"] = f"Test_{issue_analysis.get('issue_type', 'cluster')}_{(component or 'health')}"
                test_case["go_code"] = test_case.get("code", "")

        return jsonify({'status': 'success', 'test_case': test_case})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/chat-cluster-debug', methods=['POST'])
def api_chat_cluster_debug():
    """API endpoint for chatting about cluster diagnostic results."""
    try:
        data = request.json
        question = data.get('question', '')
        diagnostic_context = data.get('diagnostic_context', {})

        if not question or not question.strip():
            return jsonify({
                'status': 'error',
                'error': 'Question is required'
            }), 400

        if not diagnostic_context:
            return jsonify({
                'status': 'error',
                'error': 'Diagnostic context is required. Please run a diagnostic first.'
            }), 400

        # Generate answer using the diagnostic context
        answer = _generate_cluster_debug_answer(question, diagnostic_context)

        return jsonify({
            'status': 'success',
            'answer': answer,
            'question': question
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

def _generate_cluster_debug_answer(question, diagnostic):
    """Generate an answer based on the question and diagnostic context."""
    # Try LLM-powered answer first
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available
        if is_available():
            import json
            context_str = json.dumps(diagnostic, indent=2, default=str)[:3000]
            system = """You are an expert OpenShift/Kubernetes SRE. Answer the user's question 
based on the diagnostic context provided. Be concise, specific, and actionable.
Include relevant oc commands when appropriate."""
            prompt = f"Diagnostic context:\n{context_str}\n\nUser question: {question}"
            llm_answer = generate(prompt, system=system)
            if llm_answer:
                return llm_answer
    except Exception:
        pass

    question_lower = question.lower()

    # Issue/cause questions
    if any(word in question_lower for word in ['cause', 'causing', 'why', 'reason', 'what happened']):
        issue_analysis = diagnostic.get('issue_analysis', {})
        diagnostics = diagnostic.get('diagnostics', {})
        findings = diagnostics.get('findings', [])

        answer = "ROOT CAUSE ANALYSIS:\n\n"
        answer += f"Issue Type: {issue_analysis.get('issue_type', 'unknown')}\n"
        answer += f"Severity: {issue_analysis.get('severity', 'unknown').upper()}\n\n"

        if issue_analysis.get('affected_components'):
            answer += f"Affected Components: {', '.join(issue_analysis['affected_components'])}\n\n"

        if findings:
            answer += "Critical Findings:\n"
            critical = [f for f in findings if f.get('severity') == 'critical']
            for i, finding in enumerate(critical[:5], 1):
                answer += f"{i}. {finding['finding']}\n"

        answer += f"\n{diagnostics.get('summary', 'No detailed summary available')}"
        return answer

    # Fix/solution questions
    elif any(word in question_lower for word in ['fix', 'solve', 'resolve', 'repair', 'how to']):
        fix_recommendations = diagnostic.get('fix_recommendations', [])

        answer = "RECOMMENDED FIXES:\n\n"
        if fix_recommendations:
            answer += "Step-by-step actions to take:\n\n"
            for i, rec in enumerate(fix_recommendations, 1):
                answer += f"{i}. {rec}\n"
        else:
            answer += "No specific fix recommendations available. Check the diagnostic summary for details."

        return answer

    # Priority/what first questions
    elif any(word in question_lower for word in ['priority', 'first', 'start', 'begin', 'order']):
        findings = diagnostic.get('diagnostics', {}).get('findings', [])
        critical = [f for f in findings if f.get('severity') == 'critical']

        answer = "PRIORITIZATION:\n\n"
        answer += f"You have {len(critical)} critical issues to address.\n\n"

        if critical:
            answer += "Start with these critical issues in order:\n"
            for i, finding in enumerate(critical[:5], 1):
                answer += f"{i}. {finding['finding']}\n"

            fix_recs = diagnostic.get('fix_recommendations', [])
            if fix_recs:
                answer += f"\nFirst action: {fix_recs[0]}"
        else:
            answer += "No critical issues found. Review warnings and high-priority items."

        return answer

    # Component-specific questions (API, etcd, pod, operator, node)
    elif any(comp in question_lower for comp in ['api', 'etcd', 'pod', 'operator', 'node', 'network', 'storage']):
        component = None
        for comp in ['api', 'etcd', 'pod', 'operator', 'node', 'network', 'storage']:
            if comp in question_lower:
                component = comp
                break

        raw_output = diagnostic.get('diagnostics', {}).get('raw_output', {})

        if component == 'api' and 'api_server' in raw_output:
            api_data = raw_output['api_server']
            answer = f"API SERVER STATUS:\n\n"
            answer += f"Total Pods: {api_data.get('total_pods', 0)}\n"
            answer += f"Running Pods: {api_data.get('running_pods', 0)}\n"
            answer += f"Healthy: {api_data.get('healthy', False)}\n\n"

            if api_data.get('pod_issues'):
                answer += "Pod Issues:\n"
                for issue in api_data['pod_issues']:
                    answer += f"  • {issue}\n"

            if api_data.get('log_errors'):
                answer += "\nRecent Log Errors:\n"
                for err in api_data['log_errors'][:5]:
                    answer += f"  • {err}\n"

            return answer

        elif component == 'etcd' and 'etcd' in raw_output:
            etcd_data = raw_output['etcd']
            answer = f"ETCD STATUS:\n\n"
            answer += f"Total Pods: {etcd_data.get('total_pods', 0)}\n"
            answer += f"Running Pods: {etcd_data.get('running_pods', 0)}\n"
            answer += f"Healthy: {etcd_data.get('healthy', False)}\n\n"

            if etcd_data.get('pod_issues'):
                answer += "Pod Issues:\n"
                for issue in etcd_data['pod_issues']:
                    answer += f"  • {issue}\n"

            if etcd_data.get('log_errors'):
                answer += "\nRecent Log Errors:\n"
                for err in etcd_data['log_errors'][:5]:
                    answer += f"  • {err}\n"

            return answer

        elif component == 'operator' and 'cluster_operators' in raw_output:
            co_data = raw_output['cluster_operators']
            answer = f"CLUSTER OPERATORS STATUS:\n\n"
            answer += f"Total Operators: {co_data.get('total_operators', 0)}\n\n"

            if co_data.get('degraded_operators'):
                answer += f"Degraded ({len(co_data['degraded_operators'])}):\n"
                for op in co_data['degraded_operators']:
                    answer += f"  • {op}\n"

            if co_data.get('unavailable_operators'):
                answer += f"\nUnavailable ({len(co_data['unavailable_operators'])}):\n"
                for op in co_data['unavailable_operators']:
                    answer += f"  • {op}\n"

            return answer

        elif component == 'node' and 'nodes' in raw_output:
            node_data = raw_output['nodes']
            answer = f"NODES STATUS:\n\n"
            answer += f"Total Nodes: {node_data.get('total_nodes', 0)}\n"
            answer += f"Ready Nodes: {node_data.get('ready_nodes', 0)}\n\n"

            if node_data.get('notready_nodes'):
                answer += f"NotReady Nodes ({len(node_data['notready_nodes'])}):\n"
                for node in node_data['notready_nodes']:
                    answer += f"  • {node}\n"

            return answer

    # Log/error questions
    elif any(word in question_lower for word in ['log', 'error', 'message', 'warning']):
        findings = diagnostic.get('diagnostics', {}).get('findings', [])
        log_findings = [f for f in findings if 'log' in f.get('finding', '').lower()]

        answer = "LOG ERRORS AND WARNINGS:\n\n"
        if log_findings:
            for i, finding in enumerate(log_findings[:10], 1):
                severity = finding.get('severity', 'unknown')
                icon = '🚨' if severity == 'critical' else '⚠️'
                answer += f"{i}. {icon} {finding['finding']}\n"
        else:
            answer += "No specific log errors found in the analysis."

        return answer

    # Status/health questions
    elif any(word in question_lower for word in ['status', 'health', 'state', 'condition']):
        validation = diagnostic.get('validation_results', {})
        issue_analysis = diagnostic.get('issue_analysis', {})
        diagnostics = diagnostic.get('diagnostics', {})

        answer = "CLUSTER STATUS:\n\n"
        answer += f"OC CLI: {'✅ Available' if validation.get('oc_cli_available') else '❌ Not Found'}\n"
        answer += f"Cluster Access: {'✅ Connected' if validation.get('cluster_accessible') else '❌ No Access'}\n\n"

        answer += f"Issue Type: {issue_analysis.get('issue_type', 'unknown')}\n"
        answer += f"Severity: {issue_analysis.get('severity', 'unknown').upper()}\n\n"

        findings = diagnostics.get('findings', [])
        critical = len([f for f in findings if f.get('severity') == 'critical'])
        high = len([f for f in findings if f.get('severity') == 'high'])

        answer += f"Critical Issues: {critical}\n"
        answer += f"High Priority Issues: {high}\n"

        return answer

    # Default response
    else:
        answer = "I can help you with:\n\n"
        answer += "- Root cause analysis (ask 'What's causing the issue?')\n"
        answer += "- Fix recommendations (ask 'How do I fix this?')\n"
        answer += "- Prioritization (ask 'What should I do first?')\n"
        answer += "- Component details (ask 'Tell me about the API server')\n"
        answer += "- Log analysis (ask 'Show me the error logs')\n"
        answer += "- Status overview (ask 'What's the cluster status?')\n\n"

        issue_type = diagnostic.get('issue_analysis', {}).get('issue_type', 'unknown')
        severity = diagnostic.get('issue_analysis', {}).get('severity', 'unknown')

        answer += f"Current issue: {issue_type} (Severity: {severity})"

        return answer


# ============================================================
# AI Chat Integration (Ollama / Claude)
# ============================================================
try:
    import ollama_client
    OLLAMA_IMPORTED = True
    print("✅ Ollama/Llama3 client loaded")
except ImportError:
    OLLAMA_IMPORTED = False
    print("⚠️  Ollama client not available")


@app.route('/api/ai/status', methods=['GET'])
def api_ai_status():
    """Check backend availability, list models, and report current mode."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import get_config, get_availability_status
        config = get_config()
        llm_status = get_availability_status()
    except ImportError:
        config = {"mode": "template", "model": "llama3", "ollama_model": "llama3",
                  "claude_model": "claude-sonnet-4-5@20250929", "ollama_url": "http://localhost:11434",
                  "claude_configured": False, "cursor_configured": False}
        llm_status = {"available": False, "reason": "LLM provider not installed", "hint": ""}

    # Get Ollama models if available
    ollama_available = False
    models = []
    if OLLAMA_IMPORTED:
        ollama_available = ollama_client.is_ollama_available()
        models = ollama_client.list_models() if ollama_available else []

    return jsonify({
        'available': llm_status.get('available', False),
        'llm_available': llm_status.get('available', False),
        'llm_unavailable_reason': llm_status.get('reason', ''),
        'llm_unavailable_hint': llm_status.get('hint', ''),
        'ollama_available': ollama_available,
        'claude_configured': config.get('claude_configured', False),
        'cursor_configured': config.get('cursor_configured', False),
        'cursor_models': config.get('cursor_models', []),
        'cursor_cwd': config.get('cursor_cwd', ''),
        'cursor_attach_mcp': config.get('cursor_attach_mcp', True),
        'models': models,
        'mode': config['mode'],
        'model': config['model'],
        'ollama_model': config.get('ollama_model', 'llama3'),
        'claude_model': config.get('claude_model', 'claude-sonnet-4-5@20250929'),
        'cursor_model': config.get('cursor_model', 'composer-2.5'),
    })


@app.route('/api/ai/switch-mode', methods=['POST'])
def api_ai_switch_mode():
    """Switch between 'ollama', 'claude', 'cursor', and 'template' mode at runtime."""
    data = request.json or {}
    new_mode = data.get('mode', '').strip().lower()
    new_model = data.get('model', '').strip()

    if new_mode and new_mode not in ('ollama', 'claude', 'cursor', 'template'):
        return jsonify({'status': 'error', 'error': "mode must be 'ollama', 'claude', 'cursor', or 'template'"}), 400

    try:
        from workshop_mcp_server.src.tools.llm_provider import set_mode, set_model, get_config, get_availability_status
        if new_mode:
            set_mode(new_mode)
        if new_model:
            set_model(new_model)

        config = get_config()
        llm_status = get_availability_status()

        return jsonify({
            'status': 'success',
            'mode': config['mode'],
            'model': config['model'],
            'ollama_model': config.get('ollama_model', 'llama3'),
            'claude_model': config.get('claude_model', 'claude-sonnet-4-5@20250929'),
            'cursor_model': config.get('cursor_model', 'composer-2.5'),
            'cursor_models': config.get('cursor_models', []),
            'ollama_available': OLLAMA_IMPORTED and ollama_client.is_ollama_available() if OLLAMA_IMPORTED else False,
            'claude_configured': config.get('claude_configured', False),
            'cursor_configured': config.get('cursor_configured', False),
            'llm_available': llm_status.get('available', False),
            'llm_unavailable_reason': llm_status.get('reason', ''),
            'llm_unavailable_hint': llm_status.get('hint', ''),
            'message': (
                f"Switched to {config['mode']} mode ({config['model']})"
                + (f" — {llm_status['reason']}" if not llm_status.get('available') else "")
            ),
        })
    except ImportError:
        return jsonify({'status': 'error', 'error': 'llm_provider not available'}), 500


@app.route('/api/ai/chat', methods=['POST'])
def api_ai_chat():
    """Stream chat response - routes to active backend (Ollama or Claude)."""
    import json
    data = request.json
    messages = data.get('messages', [])

    if not messages:
        return jsonify({'error': 'No messages provided'}), 400

    # Determine current mode
    try:
        from workshop_mcp_server.src.tools.llm_provider import get_mode, get_model, _generate_claude, ANTHROPIC_API_KEY
        current_mode = get_mode()
        current_model = get_model()
    except ImportError:
        current_mode = 'ollama'
        current_model = 'llama3'

    # Enrich with Knowledge Base context
    kb_context = ""
    try:
        from workshop_mcp_server.src.tools.rag.kb_context import get_kb_context
        last_user_msg = next((m['content'] for m in reversed(messages) if m.get('role') == 'user'), "")
        if last_user_msg:
            kb_context = get_kb_context(last_user_msg, top_k=3, max_chars=1500)
    except Exception:
        pass

    # Route to Claude API (non-streaming for simplicity)
    if current_mode == 'claude':
        # Check if Claude is available via API key or Vertex
        use_vertex = os.environ.get('CLAUDE_CODE_USE_VERTEX', '')
        vertex_project = os.environ.get('ANTHROPIC_VERTEX_PROJECT_ID', '')
        if not ANTHROPIC_API_KEY and not (use_vertex and vertex_project):
            return jsonify({'error': 'Claude not configured. Go to Settings and set either ANTHROPIC_API_KEY or Vertex AI credentials.'}), 500

        system_prompt = """You are Claude, an AI assistant by Anthropic, integrated into an MCP development dashboard.
You help with OpenShift/Kubernetes operations, code review, test generation, and debugging.
When asked about your identity: you are Claude (by Anthropic), the specific model variant is """ + current_model + """.
Be concise, technical, and helpful.
If Knowledge Base context is provided, use it to give more accurate answers grounded in the team's documentation."""

        # Build prompt from messages
        user_msgs = [m for m in messages if m.get('role') != 'system']
        prompt_parts = []
        if kb_context:
            prompt_parts.append(f"{kb_context}\n\n---\n")
        prompt_parts.append("\n".join([f"{m['role']}: {m['content']}" for m in user_msgs]))
        prompt = "\n".join(prompt_parts)

        def stream_claude():
            try:
                from workshop_mcp_server.src.tools.llm_provider import generate as llm_generate
                result = llm_generate(prompt, system=system_prompt, model=current_model)
                if result:
                    chunk_size = 20
                    for i in range(0, len(result), chunk_size):
                        yield f"data: {json.dumps(result[i:i+chunk_size], ensure_ascii=False)}\n\n"
                else:
                    yield "data: [ERROR: Claude returned no response. Check Settings → Claude API Key or Vertex AI config.]\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: [ERROR: {str(e)}]\n\n"

        from flask import Response
        return Response(stream_claude(), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    # Route to Cursor Agent SDK
    if current_mode == 'cursor':
        if not os.environ.get('CURSOR_API_KEY'):
            return jsonify({'error': 'Cursor not configured. Go to Settings and set CURSOR_API_KEY.'}), 500

        system_prompt = """You are a Cursor AI agent integrated into an MCP development dashboard.
You help with OpenShift/Kubernetes operations, code review, test generation, and debugging.
When asked about your identity: you are a Cursor agent using model """ + current_model + """.
Be concise, technical, and helpful.
If Knowledge Base context is provided, use it to give more accurate answers grounded in the team's documentation.
You may use attached MCP tools (must-gather analyzer, cluster debugger, knowledge base) when helpful."""

        user_msgs = [m for m in messages if m.get('role') != 'system']
        prompt_parts = []
        if kb_context:
            prompt_parts.append(f"{kb_context}\n\n---\n")
        prompt_parts.append("\n".join([f"{m['role']}: {m['content']}" for m in user_msgs]))
        prompt = "\n".join(prompt_parts)

        def stream_cursor():
            try:
                from workshop_mcp_server.src.tools.llm_provider import generate_cursor_stream
                for chunk in generate_cursor_stream(prompt, system=system_prompt, model=current_model):
                    chunk_size = 40
                    for i in range(0, len(chunk), chunk_size):
                        yield f"data: {json.dumps(chunk[i:i+chunk_size], ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: [ERROR: {str(e)}]\n\n"

        from flask import Response
        return Response(stream_cursor(), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    # Route to Ollama (streaming)
    if not OLLAMA_IMPORTED:
        return jsonify({'error': 'Ollama client not available'}), 500

    model = data.get('model', current_model)

    # Add system prompt if not present
    if not any(m.get('role') == 'system' for m in messages):
        messages.insert(0, {
            'role': 'system',
            'content': ollama_client.get_chat_system_prompt(model),
        })

    # Inject KB context into the last user message
    if kb_context:
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get('role') == 'user':
                messages[i]['content'] = f"{kb_context}\n\n---\nUser question: {messages[i]['content']}"
                break

    def stream_ollama():
        try:
            for token in ollama_client.chat_stream(messages, model=model):
                yield f"data: {json.dumps(token, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR: {str(e)}]\n\n"

    from flask import Response
    return Response(stream_ollama(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


# ============================================================
# RAG / Knowledge Base API Endpoints
# ============================================================

@app.route('/knowledge-base')
def knowledge_base():
    """Knowledge Base management page."""
    return render_template('knowledge_base.html')


@app.route('/api/kb/list', methods=['GET'])
def api_kb_list():
    """List all indexed knowledge base collections."""
    if not RAG_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'RAG not available. Install chromadb: pip install chromadb'}), 503
    try:
        result = list_knowledge_bases()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/kb/index-folder', methods=['POST'])
def api_kb_index_folder():
    """Index a local folder into the knowledge base."""
    if not RAG_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'RAG not available'}), 503
    try:
        data = request.json
        folder_path = data.get('folder_path', '')
        collection = data.get('collection', 'default')
        include_code = data.get('include_code', True)

        if not folder_path:
            return jsonify({'status': 'error', 'error': 'folder_path is required'}), 400

        result = index_docs(folder_path, collection, include_code)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/kb/index-repo', methods=['POST'])
def api_kb_index_repo():
    """Clone and index a git repository."""
    if not RAG_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'RAG not available'}), 503
    try:
        data = request.json
        repo_url = data.get('repo_url', '')
        collection = data.get('collection', 'default')
        branch = data.get('branch', 'main')

        if not repo_url:
            return jsonify({'status': 'error', 'error': 'repo_url is required'}), 400

        result = index_repo(repo_url, collection, branch)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/kb/index-web', methods=['POST'])
def api_kb_index_web():
    """Fetch and index a web URL."""
    if not RAG_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'RAG not available'}), 503
    try:
        data = request.json
        url = data.get('url', '')
        collection = data.get('collection', 'default')
        crawl = data.get('crawl', False)

        if not url:
            return jsonify({'status': 'error', 'error': 'url is required'}), 400

        result = index_web(url, collection, crawl)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/kb/ask', methods=['POST'])
def api_kb_ask():
    """Ask a question against the knowledge base (RAG query)."""
    if not RAG_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'RAG not available'}), 503
    try:
        data = request.json
        question = data.get('question', '')
        collection = data.get('collection', 'default')
        top_k = data.get('top_k', 5)

        if not question:
            return jsonify({'status': 'error', 'error': 'question is required'}), 400

        result = ask_docs(question, collection, top_k)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/kb/delete', methods=['POST'])
def api_kb_delete():
    """Delete a knowledge base collection."""
    if not RAG_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'RAG not available'}), 503
    try:
        data = request.json
        collection = data.get('collection', '')
        if not collection:
            return jsonify({'status': 'error', 'error': 'collection name is required'}), 400

        result = delete_knowledge_base(collection)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
