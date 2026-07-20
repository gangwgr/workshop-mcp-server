"""Web GUI for MCP Server.

A Flask-based web interface for interacting with all MCP server tools.
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

# Try to import Polarion tools
try:
    from workshop_mcp_server.src.tools.polarion_search_tool import search_test_cases, get_test_case_details, query_polarion_api, format_search_results
    POLARION_AVAILABLE = True
    print("✅ Polarion QA Assistant tools loaded")
except ImportError as e:
    print(f"⚠️  Polarion tools not available: {e}")
    POLARION_AVAILABLE = False

# Try to import Jira Manager tools
try:
    from workshop_mcp_server.src.tools.jira_manager_tool import (
        test_jira_connection, get_jira_projects, fetch_all_jira_issues, get_issue, search_issues, get_high_priority_bugs, get_team_issues,
        generate_test_cases_from_jira, generate_test_plan_from_jira, format_jira_results, _get_jira_client
    )
    JIRA_AVAILABLE = True
    print("✅ Jira Manager tools loaded")
except ImportError as e:
    print(f"⚠️  Jira Manager tools not available: {e}")
    JIRA_AVAILABLE = False

# Try to import other tools - make them optional
try:
    from workshop_mcp_server.src.tools.line_by_line_code_reviewer_tool import review_code_line_by_line
    CODE_REVIEW_AVAILABLE = True
    print("✅ Code review tools loaded")
except ImportError as e:
    print(f"⚠️  Code review tools not available: {e}")
    CODE_REVIEW_AVAILABLE = False

try:
    from workshop_mcp_server.src.tools.github_pr_commenter_tool import post_pr_review_comments
    PR_TOOLS_AVAILABLE = True
    print("✅ GitHub PR tools loaded")
except ImportError as e:
    print(f"⚠️  GitHub PR tools not available: {e}")
    PR_TOOLS_AVAILABLE = False

try:
    from workshop_mcp_server.src.tools.ocp_test_case_generator_tool import generate_ocp_test_case
    from workshop_mcp_server.src.tools.ocp_oc_cli_test_generator_tool import generate_oc_cli_test
    from workshop_mcp_server.src.tools.ocp_step_by_step_executor_tool import execute_ocp_test_step_by_step
    from workshop_mcp_server.src.tools.ocp_test_debugger_tool import debug_ocp_test_failure
    from workshop_mcp_server.src.tools.ocp_test_validator_tool import validate_ocp_test_input
    OCP_TOOLS_AVAILABLE = True
    print("✅ OpenShift testing tools loaded")
except ImportError as e:
    print(f"⚠️  OpenShift testing tools not available: {e}")
    OCP_TOOLS_AVAILABLE = False

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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mcp-server-secret-key-change-in-production'

# Track PR review counts to prevent infinite review loops
# Key: PR URL, Value: {'count': N, 'last_reviewed': timestamp}
_pr_review_tracker = {}
PR_REVIEW_MAX = 2  # Maximum reviews per PR before warning

@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@app.route('/code-review')
def code_review():
    """Code review page."""
    return render_template('code_review.html')

@app.route('/pr-review')
def pr_review():
    """PR review page."""
    return render_template('pr_review.html')

@app.route('/ocp-testing')
def ocp_testing():
    """OpenShift testing page."""
    return render_template('ocp_testing.html')

@app.route('/mustgather-analyzer')
def mustgather_analyzer():
    """Must-Gather analyzer page."""
    return render_template('mustgather_analyzer.html')

@app.route('/cluster-debugger')
def cluster_debugger():
    """Cluster debugger agent page."""
    return render_template('cluster_debugger.html')

@app.route('/knowledge-base')
def knowledge_base():
    """Knowledge Base / RAG page."""
    return render_template('knowledge_base.html')

@app.route('/api/rag/collections', methods=['GET'])
def api_rag_collections():
    """List all RAG collections."""
    try:
        from workshop_mcp_server.src.tools.rag.rag_tool import list_knowledge_bases
        return jsonify(list_knowledge_bases())
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/rag/index', methods=['POST'])
def api_rag_index():
    """Index a folder into RAG."""
    try:
        from workshop_mcp_server.src.tools.rag.rag_tool import index_docs
        data = request.json
        folder_path = data.get('folder_path', '')
        collection = data.get('collection', 'default')
        include_code = data.get('include_code', True)
        if not folder_path:
            return jsonify({'status': 'error', 'error': 'folder_path required'}), 400
        result = index_docs(folder_path, collection, include_code)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/rag/index-repo', methods=['POST'])
def api_rag_index_repo():
    """Clone and index a git repo into RAG."""
    try:
        from workshop_mcp_server.src.tools.rag.rag_tool import index_repo
        data = request.json
        repo_url = data.get('repo_url', '')
        collection = data.get('collection', 'default')
        branch = data.get('branch', 'main')
        if not repo_url:
            return jsonify({'status': 'error', 'error': 'repo_url required'}), 400
        result = index_repo(repo_url, collection, branch)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/rag/index-web', methods=['POST'])
def api_rag_index_web():
    """Fetch and index a web URL into RAG."""
    try:
        from workshop_mcp_server.src.tools.rag.rag_tool import index_web
        data = request.json
        web_url = data.get('web_url', '')
        collection = data.get('collection', 'default')
        crawl = data.get('crawl', False)
        if not web_url:
            return jsonify({'status': 'error', 'error': 'web_url required'}), 400
        result = index_web(web_url, collection, crawl)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/rag/ask', methods=['POST'])
def api_rag_ask():
    """Ask a question against indexed docs."""
    try:
        from workshop_mcp_server.src.tools.rag.rag_tool import ask_docs
        data = request.json
        question = data.get('question', '')
        collection = data.get('collection', 'default')
        if not question:
            return jsonify({'status': 'error', 'error': 'question required'}), 400
        result = ask_docs(question, collection)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/rag/delete', methods=['POST'])
def api_rag_delete():
    """Delete a RAG collection."""
    try:
        from workshop_mcp_server.src.tools.rag.rag_tool import delete_knowledge_base
        data = request.json
        collection = data.get('collection', '')
        if not collection:
            return jsonify({'status': 'error', 'error': 'collection name required'}), 400
        result = delete_knowledge_base(collection)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/code-assistant')
def code_assistant():
    """AI Code Assistant - writes code using KB context."""
    return render_template('code_assistant.html')

# ============================================================
# Git Operations API
# ============================================================

@app.route('/api/git/status', methods=['POST'])
def api_git_status():
    """Get git status for a repo."""
    import subprocess
    data = request.json
    repo_path = data.get('repo_path', '').strip()
    repo_path = os.path.expanduser(repo_path)
    if not repo_path or not os.path.isdir(repo_path):
        return jsonify({'status': 'error', 'error': f'Repository path does not exist: {repo_path}'}), 400
    git_dir = os.path.join(repo_path, '.git')
    if not os.path.isdir(git_dir):
        return jsonify({'status': 'error', 'error': f'Not a git repository (no .git directory): {repo_path}'}), 400
    try:
        result = subprocess.run(['git', 'status', '--porcelain', '-b'], cwd=repo_path, capture_output=True, text=True, timeout=10)
        branch_result = subprocess.run(['git', 'branch', '--show-current'], cwd=repo_path, capture_output=True, text=True, timeout=5)
        log_result = subprocess.run(['git', 'log', '--oneline', '-10'], cwd=repo_path, capture_output=True, text=True, timeout=5)
        remote_result = subprocess.run(['git', 'remote', '-v'], cwd=repo_path, capture_output=True, text=True, timeout=5)
        return jsonify({
            'status': 'success',
            'branch': branch_result.stdout.strip(),
            'git_status': result.stdout,
            'recent_commits': log_result.stdout,
            'remotes': remote_result.stdout,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

def _normalize_repo_path(data):
    """Normalize and validate a repo path from request data."""
    path = data.get('repo_path', '').strip()
    return os.path.expanduser(path) if path else ''

@app.route('/api/git/branches', methods=['POST'])
def api_git_branches():
    """List all branches."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    try:
        result = subprocess.run(['git', 'branch', '-a', '--format=%(refname:short) %(upstream:short) %(subject)'],
                                cwd=repo_path, capture_output=True, text=True, timeout=10)
        current = subprocess.run(['git', 'branch', '--show-current'], cwd=repo_path, capture_output=True, text=True, timeout=5)
        branches = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.strip().split(' ', 2)
                branches.append({'name': parts[0], 'tracking': parts[1] if len(parts) > 1 else '', 'subject': parts[2] if len(parts) > 2 else ''})
        return jsonify({'status': 'success', 'branches': branches, 'current': current.stdout.strip()})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/git/create-branch', methods=['POST'])
def api_git_create_branch():
    """Create and checkout a new branch."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    branch_name = data.get('branch_name', '')
    base = data.get('base', 'HEAD')
    if not branch_name:
        return jsonify({'status': 'error', 'error': 'branch_name required'}), 400
    try:
        result = subprocess.run(['git', 'checkout', '-b', branch_name, base], cwd=repo_path, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return jsonify({'status': 'error', 'error': result.stderr}), 400
        return jsonify({'status': 'success', 'message': f'Created and switched to branch: {branch_name}', 'output': result.stdout + result.stderr})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/git/checkout', methods=['POST'])
def api_git_checkout():
    """Switch to a branch."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    branch = data.get('branch', '')
    try:
        result = subprocess.run(['git', 'checkout', branch], cwd=repo_path, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return jsonify({'status': 'error', 'error': result.stderr}), 400
        return jsonify({'status': 'success', 'message': f'Switched to: {branch}', 'output': result.stdout + result.stderr})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/git/commit', methods=['POST'])
def api_git_commit():
    """Stage and commit changes."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    message = data.get('message', '')
    files = data.get('files', [])  # empty = all
    if not message:
        return jsonify({'status': 'error', 'error': 'commit message required'}), 400
    try:
        if files:
            subprocess.run(['git', 'add'] + files, cwd=repo_path, capture_output=True, text=True, timeout=10)
        else:
            subprocess.run(['git', 'add', '-A'], cwd=repo_path, capture_output=True, text=True, timeout=10)
        result = subprocess.run(['git', 'commit', '-m', message], cwd=repo_path, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return jsonify({'status': 'error', 'error': result.stderr or result.stdout}), 400
        return jsonify({'status': 'success', 'message': 'Committed', 'output': result.stdout})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/git/push', methods=['POST'])
def api_git_push():
    """Push current branch to remote."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    force = data.get('force', False)
    try:
        cmd = ['git', 'push', '-u', 'origin', 'HEAD']
        if force:
            cmd.insert(2, '--force-with-lease')
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return jsonify({'status': 'error', 'error': result.stderr}), 400
        return jsonify({'status': 'success', 'message': 'Pushed', 'output': result.stdout + result.stderr})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/git/rebase', methods=['POST'])
def api_git_rebase():
    """Rebase current branch onto another."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    onto = data.get('onto', 'main')
    action = data.get('action', 'start')  # start, continue, abort
    try:
        if action == 'continue':
            result = subprocess.run(['git', 'rebase', '--continue'], cwd=repo_path, capture_output=True, text=True, timeout=30, env={**os.environ, 'GIT_EDITOR': 'true'})
        elif action == 'abort':
            result = subprocess.run(['git', 'rebase', '--abort'], cwd=repo_path, capture_output=True, text=True, timeout=10)
        else:
            subprocess.run(['git', 'fetch', 'origin'], cwd=repo_path, capture_output=True, text=True, timeout=30)
            result = subprocess.run(['git', 'rebase', f'origin/{onto}'], cwd=repo_path, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            conflict_result = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=U'], cwd=repo_path, capture_output=True, text=True, timeout=5)
            return jsonify({
                'status': 'conflict',
                'message': 'Rebase has conflicts that need resolution',
                'output': result.stdout + result.stderr,
                'conflicted_files': conflict_result.stdout.strip().split('\n') if conflict_result.stdout.strip() else [],
            })
        return jsonify({'status': 'success', 'message': f'Rebase onto {onto} completed', 'output': result.stdout + result.stderr})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/git/resolve-conflicts', methods=['POST'])
def api_git_resolve_conflicts():
    """AI-powered conflict resolution."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    file_path = data.get('file_path', '')
    strategy = data.get('strategy', 'ai')  # ai, ours, theirs

    if not file_path:
        return jsonify({'status': 'error', 'error': 'file_path required'}), 400

    full_path = os.path.join(repo_path, file_path) if not file_path.startswith('/') else file_path
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if '<<<<<<< ' not in content:
            return jsonify({'status': 'error', 'error': 'No conflict markers found in file'}), 400

        if strategy == 'ours':
            import re
            resolved = re.sub(r'<<<<<<< .*?\n(.*?)=======\n.*?>>>>>>> .*?\n', r'\1', content, flags=re.DOTALL)
        elif strategy == 'theirs':
            import re
            resolved = re.sub(r'<<<<<<< .*?\n.*?=======\n(.*?)>>>>>>> .*?\n', r'\1', content, flags=re.DOTALL)
        elif strategy == 'ai':
            from workshop_mcp_server.src.tools.llm_provider import generate, is_available
            from workshop_mcp_server.src.tools.rag.kb_context import get_kb_context

            if not is_available():
                return jsonify({'status': 'error', 'error': 'LLM not available for AI resolution'}), 500

            kb_context = get_kb_context(f"merge conflict resolution {file_path}", top_k=2, max_chars=1000)

            system = """You are an expert at resolving git merge conflicts.
Output ONLY the resolved file content - no explanations, no markdown fences.
Merge both sides intelligently: keep all functionality from both versions.
Follow the codebase patterns from the Knowledge Base context if provided."""

            prompt_parts = []
            if kb_context:
                prompt_parts.append(f"Codebase context:\n{kb_context}\n---\n")
            prompt_parts.append(f"Resolve the conflicts in this file ({file_path}):\n\n{content}")
            prompt = "\n".join(prompt_parts)

            resolved = generate(prompt, system=system, max_tokens=4096)
            if not resolved:
                return jsonify({'status': 'error', 'error': 'AI could not resolve conflicts'}), 500
            if resolved.startswith('```'):
                lines = resolved.split('\n')[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                resolved = '\n'.join(lines)
        else:
            return jsonify({'status': 'error', 'error': 'Invalid strategy'}), 400

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(resolved)

        subprocess.run(['git', 'add', file_path], cwd=repo_path, capture_output=True, text=True, timeout=5)
        return jsonify({'status': 'success', 'message': f'Conflict resolved in {file_path} ({strategy})', 'resolved_content': resolved[:500]})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/git/cherry-pick', methods=['POST'])
def api_git_cherry_pick():
    """Cherry-pick a commit (bump changes from another PR/branch)."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    commit = data.get('commit', '')
    if not commit:
        return jsonify({'status': 'error', 'error': 'commit hash required'}), 400
    try:
        subprocess.run(['git', 'fetch', '--all'], cwd=repo_path, capture_output=True, text=True, timeout=30)
        result = subprocess.run(['git', 'cherry-pick', commit], cwd=repo_path, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            conflict_result = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=U'], cwd=repo_path, capture_output=True, text=True, timeout=5)
            return jsonify({
                'status': 'conflict',
                'message': 'Cherry-pick has conflicts',
                'output': result.stderr,
                'conflicted_files': conflict_result.stdout.strip().split('\n') if conflict_result.stdout.strip() else [],
            })
        return jsonify({'status': 'success', 'message': f'Cherry-picked {commit}', 'output': result.stdout + result.stderr})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/git/log', methods=['POST'])
def api_git_log():
    """Get commit log (optionally for a branch or PR)."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    branch = data.get('branch', '')
    count = data.get('count', 20)
    try:
        cmd = ['git', 'log', f'-{count}', '--oneline', '--decorate']
        if branch:
            cmd.append(branch)
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=10)
        return jsonify({'status': 'success', 'log': result.stdout})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/git/diff', methods=['POST'])
def api_git_diff():
    """Get diff (staged, unstaged, or between branches)."""
    import subprocess
    data = request.json
    repo_path = _normalize_repo_path(data)
    target = data.get('target', '')  # branch or commit to diff against
    try:
        cmd = ['git', 'diff']
        if target:
            cmd.append(target)
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=10)
        return jsonify({'status': 'success', 'diff': result.stdout})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/code-assist/browse', methods=['POST'])
def api_code_browse():
    """Browse local directory tree."""
    data = request.json
    path = data.get('path', os.path.expanduser('~/office-work'))
    try:
        if not os.path.exists(path):
            return jsonify({'status': 'error', 'error': f'Path not found: {path}'}), 404

        items = []
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return jsonify({'status': 'success', 'type': 'file', 'path': path, 'content': content, 'lines': len(content.splitlines())})

        for item in sorted(os.listdir(path)):
            if item.startswith('.') or item in ('node_modules', '__pycache__', 'vendor', '.git', 'venv'):
                continue
            full = os.path.join(path, item)
            items.append({
                'name': item,
                'path': full,
                'is_dir': os.path.isdir(full),
                'size': os.path.getsize(full) if os.path.isfile(full) else None,
            })
        return jsonify({'status': 'success', 'type': 'directory', 'path': path, 'items': items})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/code-assist/tree', methods=['POST'])
def api_code_tree():
    """Get recursive directory tree for a repo (up to 3 levels deep)."""
    data = request.json
    path = data.get('path', os.path.expanduser('~/office-work'))
    max_depth = data.get('depth', 3)
    SKIP = {'.git', 'node_modules', '__pycache__', 'vendor', 'venv', '.venv', '.tox', 'dist', 'build', '.eggs', '*.egg-info'}

    def build_tree(dir_path, depth=0):
        if depth >= max_depth:
            return []
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return []
        tree = []
        for name in entries:
            if name.startswith('.') or name in SKIP or name.endswith('.egg-info'):
                continue
            full = os.path.join(dir_path, name)
            is_dir = os.path.isdir(full)
            node = {'name': name, 'path': full, 'is_dir': is_dir}
            if is_dir:
                node['children'] = build_tree(full, depth + 1)
            else:
                try:
                    node['size'] = os.path.getsize(full)
                except OSError:
                    node['size'] = 0
            tree.append(node)
        return tree

    try:
        if not os.path.exists(path):
            return jsonify({'status': 'error', 'error': f'Path not found: {path}'}), 404
        tree = build_tree(path)
        return jsonify({'status': 'success', 'path': path, 'tree': tree})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/code-assist/read-file', methods=['POST'])
def api_code_read_file():
    """Read a local file."""
    data = request.json
    file_path = data.get('path', '')
    if not file_path or not os.path.isfile(file_path):
        return jsonify({'status': 'error', 'error': 'File not found'}), 404
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return jsonify({'status': 'success', 'path': file_path, 'content': content, 'lines': len(content.splitlines())})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/code-assist/write-file', methods=['POST'])
def api_code_write_file():
    """Write/create a file on disk."""
    data = request.json
    file_path = data.get('path', '')
    content = data.get('content', '')
    if not file_path:
        return jsonify({'status': 'error', 'error': 'path required'}), 400
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'status': 'success', 'path': file_path, 'bytes_written': len(content), 'message': f'File saved: {file_path}'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/code-assist/edit-file', methods=['POST'])
def api_code_edit_file():
    """Edit an existing file - find and replace, or insert at line."""
    data = request.json
    file_path = data.get('path', '')
    action = data.get('action', 'replace')  # replace, insert, append
    old_text = data.get('old_text', '')
    new_text = data.get('new_text', '')
    line_number = data.get('line_number', None)

    if not file_path or not os.path.isfile(file_path):
        return jsonify({'status': 'error', 'error': 'File not found'}), 404
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if action == 'replace' and old_text:
            if old_text not in content:
                return jsonify({'status': 'error', 'error': 'old_text not found in file'}), 400
            content = content.replace(old_text, new_text, 1)
        elif action == 'insert' and line_number is not None:
            lines = content.splitlines(True)
            idx = max(0, min(line_number - 1, len(lines)))
            lines.insert(idx, new_text + '\n')
            content = ''.join(lines)
        elif action == 'append':
            content += '\n' + new_text
        else:
            return jsonify({'status': 'error', 'error': 'Invalid action or missing parameters'}), 400

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'status': 'success', 'path': file_path, 'action': action, 'message': f'File edited: {file_path}'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/code-assist/generate-and-save', methods=['POST'])
def api_code_generate_and_save():
    """Generate code with AI and save directly to a file."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config
        from workshop_mcp_server.src.tools.rag.kb_context import get_kb_context

        data = request.json
        task = data.get('task', '')
        language = data.get('language', 'go')
        file_path = data.get('file_path', '')
        collection = data.get('collection', '')
        context_hint = data.get('context', '')
        mode = data.get('mode', 'create')  # create, edit_append, edit_insert

        if not task or not file_path:
            return jsonify({'status': 'error', 'error': 'task and file_path required'}), 400
        if not is_available():
            return jsonify({'status': 'error', 'error': 'LLM not available'}), 500

        # Read existing file content if editing
        existing_content = ""
        if os.path.isfile(file_path) and mode != 'create':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                existing_content = f.read()

        # Get KB context
        kb_query = f"{language} {task}"
        if context_hint:
            kb_query += f" {context_hint}"
        collections_filter = [collection] if collection else None
        kb_context = get_kb_context(kb_query, collections=collections_filter, top_k=5, max_chars=3000)

        system = f"""You are an expert {language} developer.
Generate ONLY the code - no explanations, no markdown fences, no commentary.
Output raw code that can be directly saved to a file.
Follow the patterns from the Knowledge Base context if provided.
The code should be production-ready with proper imports, error handling, and structure."""

        prompt_parts = []
        if kb_context:
            prompt_parts.append(f"Reference patterns:\n{kb_context}\n\n---\n")
        if existing_content:
            prompt_parts.append(f"Existing file content:\n```\n{existing_content}\n```\n")
            if mode == 'edit_append':
                prompt_parts.append(f"ADD the following to the end of this file:")
            else:
                prompt_parts.append(f"MODIFY this file to:")
        prompt_parts.append(f"Task: {task}")
        prompt_parts.append(f"Language: {language}")
        prompt_parts.append(f"Target file: {file_path}")
        prompt = "\n".join(prompt_parts)

        result = generate(prompt, system=system, max_tokens=4096)
        if not result:
            return jsonify({'status': 'error', 'error': 'LLM returned no response'}), 500

        # Clean markdown fences if LLM included them
        code = result.strip()
        if code.startswith('```'):
            lines = code.split('\n')
            lines = lines[1:]  # remove opening fence
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            code = '\n'.join(lines)

        # Write to file
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
        if mode == 'edit_append' and existing_content:
            code = existing_content + '\n\n' + code

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        config = get_config()
        return jsonify({
            'status': 'success',
            'path': file_path,
            'bytes_written': len(code),
            'lines_written': len(code.splitlines()),
            'model': config['model'],
            'kb_used': bool(kb_context),
            'message': f'Code generated and saved to {file_path}',
            'preview': code[:500],
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/ai/quick-chat', methods=['POST'])
def api_ai_quick_chat():
    """General-purpose AI chat endpoint - answers questions, explains code, helps with tasks."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config

        data = request.json
        message = data.get('message', '')
        context = data.get('context', '')
        file_path = data.get('file_path', '')

        if not message:
            return jsonify({'status': 'error', 'error': 'message required'}), 400

        if not is_available():
            return jsonify({'status': 'error', 'error': 'LLM not available'}), 500

        # If a file path is provided, read it and include as context
        file_content = ""
        if file_path:
            try:
                import os
                if os.path.isfile(file_path):
                    with open(file_path, 'r', errors='ignore') as f:
                        file_content = f.read()[:8000]
            except Exception:
                pass

        # Try to get KB context
        kb_context = ""
        try:
            from workshop_mcp_server.src.tools.rag.kb_context import get_kb_context
            kb_context = get_kb_context(message, top_k=3, max_chars=2000)
        except Exception:
            pass

        system = """You are a helpful AI assistant for software engineers. You answer questions clearly and concisely.
When explaining code or files, describe what they do in plain language.
When asked to write code, provide clean, working code.
When asked about concepts, give clear explanations with examples if helpful.
Keep responses focused and practical. Use markdown formatting."""

        prompt_parts = []
        if file_content:
            prompt_parts.append(f"File: {file_path}\n```\n{file_content}\n```\n")
        if kb_context:
            prompt_parts.append(f"Knowledge Base context:\n{kb_context}\n---\n")
        if context:
            prompt_parts.append(f"Context: {context}\n")
        prompt_parts.append(f"Question: {message}")
        prompt = "\n".join(prompt_parts)

        result = generate(prompt, system=system, max_tokens=4096)
        config = get_config()

        if result:
            return jsonify({
                'status': 'success',
                'response': result,
                'model': config.get('model', ''),
                'mode': config.get('mode', '')
            })
        else:
            return jsonify({'status': 'error', 'error': 'No response from LLM'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/code-assist', methods=['POST'])
def api_code_assist():
    """AI Code Assistant endpoint - generates code using KB context from local repos."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config

        data = request.json
        task = data.get('task', '')
        language = data.get('language', 'go')
        context_hint = data.get('context', '')
        collection = data.get('collection', '')
        file_path = data.get('file_path', '')

        if not task:
            return jsonify({'status': 'error', 'error': 'task description required'}), 400

        if not is_available():
            return jsonify({'status': 'error', 'error': 'LLM not available'}), 500

        kb_query = f"{language} {task}"
        if context_hint:
            kb_query += f" {context_hint}"

        kb_context = ""
        try:
            from workshop_mcp_server.src.tools.rag.kb_context import get_kb_context
            collections_filter = [collection] if collection else None
            kb_context = get_kb_context(kb_query, collections=collections_filter, top_k=5, max_chars=3000)
        except Exception:
            pass

        system = f"""You are an expert {language} developer embedded in a team's development environment.
You have access to the team's existing codebase via the Knowledge Base context below.
Your job is to write production-quality code that:
1. Follows the SAME patterns, naming conventions, and style as the existing codebase
2. Reuses existing functions/types/imports from the indexed repos when applicable
3. Includes proper error handling, logging, and comments where needed
4. Is complete and ready to use (not pseudo-code)

If Knowledge Base context is provided, reference those patterns directly.
Always output complete, runnable code in markdown code blocks."""

        prompt_parts = []
        if kb_context:
            prompt_parts.append(f"Existing codebase reference:\n{kb_context}\n\n---\n")
        if file_path:
            prompt_parts.append(f"Target file: {file_path}")
        prompt_parts.append(f"Language: {language}")
        prompt_parts.append(f"Task: {task}")
        if context_hint:
            prompt_parts.append(f"Additional context: {context_hint}")
        prompt_parts.append("\nWrite the complete code:")
        prompt = "\n".join(prompt_parts)

        result = generate(prompt, system=system, max_tokens=4096)
        config = get_config()

        if result:
            return jsonify({
                'status': 'success',
                'code': result,
                'model': config['model'],
                'mode': config['mode'],
                'kb_used': bool(kb_context),
                'collection_searched': collection or 'all',
            })
        else:
            return jsonify({'status': 'error', 'error': 'LLM returned no response'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/code-assist/explain', methods=['POST'])
def api_code_explain():
    """Explain code using KB context."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config

        data = request.json
        code = data.get('code', '')
        if not code:
            return jsonify({'status': 'error', 'error': 'code required'}), 400

        kb_context = ""
        try:
            from workshop_mcp_server.src.tools.rag.kb_context import get_kb_context
            kb_context = get_kb_context(code[:500], top_k=3, max_chars=1500)
        except Exception:
            pass

        system = """You are an expert code explainer. Explain what the code does in clear, concise terms.
Reference the team's codebase context when available to explain how this code fits in the larger system.
Use bullet points and be specific about function calls, types, and patterns used."""

        prompt_parts = []
        if kb_context:
            prompt_parts.append(f"Team codebase context:\n{kb_context}\n\n---\n")
        prompt_parts.append(f"Explain this code:\n```\n{code}\n```")
        prompt = "\n".join(prompt_parts)

        result = generate(prompt, system=system)
        config = get_config()
        if result:
            return jsonify({'status': 'success', 'explanation': result, 'kb_used': bool(kb_context),
                            'model': config['model'], 'mode': config['mode']})
        return jsonify({'status': 'error', 'error': 'LLM returned no response'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/code-assist/refactor', methods=['POST'])
def api_code_refactor():
    """Refactor code using KB context for team patterns."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config

        data = request.json
        code = data.get('code', '')
        instructions = data.get('instructions', 'improve code quality')
        if not code:
            return jsonify({'status': 'error', 'error': 'code required'}), 400

        kb_context = ""
        try:
            from workshop_mcp_server.src.tools.rag.kb_context import get_kb_context
            kb_context = get_kb_context(f"refactor {code[:300]}", top_k=3, max_chars=2000)
        except Exception:
            pass

        system = """You are an expert code refactoring assistant.
Refactor the given code following the team's existing patterns from the Knowledge Base.
Maintain the same functionality but improve quality, readability, and consistency.
Output the complete refactored code in a code block."""

        prompt_parts = []
        if kb_context:
            prompt_parts.append(f"Team codebase patterns:\n{kb_context}\n\n---\n")
        prompt_parts.append(f"Refactor instructions: {instructions}")
        prompt_parts.append(f"\nCode to refactor:\n```\n{code}\n```\n\nRefactored code:")
        prompt = "\n".join(prompt_parts)

        result = generate(prompt, system=system, max_tokens=4096)
        config = get_config()
        if result:
            return jsonify({'status': 'success', 'refactored': result, 'kb_used': bool(kb_context),
                            'model': config['model'], 'mode': config['mode']})
        return jsonify({'status': 'error', 'error': 'LLM returned no response'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/work-reports')
def work_reports():
    """Work Report Generator page."""
    return render_template('work_reports.html')

@app.route('/api/work-report/generate', methods=['POST'])
def api_work_report_generate():
    """Generate a daily work report from Jira/GitHub data."""
    import subprocess
    data = request.json
    date = data.get('date', '')
    report_format = data.get('format', 'brief')
    user_name = data.get('user_name', os.environ.get('GIT_AUTHOR_NAME', 'User'))

    if not date:
        from datetime import datetime
        date = datetime.now().strftime('%Y-%m-%d')

    try:
        jira_data = {"issues": data.get('jira_issues', [])}
        github_data = {"prs": data.get('github_prs', [])}

        # Try to use the work-report-generator
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'work-report-generator', 'src'))
        from report_manager import ReportManager
        from server import _build_brief_report, _build_full_report

        from datetime import datetime as dt
        report_date = dt.strptime(date, "%Y-%m-%d")

        brief_content = _build_brief_report(report_date, jira_data, github_data)
        full_content = _build_full_report(report_date, jira_data, github_data, user_name)

        if report_format == 'brief':
            return jsonify({'status': 'success', 'report': brief_content, 'format': 'brief', 'date': date})
        elif report_format == 'full':
            return jsonify({'status': 'success', 'report': full_content, 'format': 'full', 'date': date})
        else:
            return jsonify({'status': 'success', 'report': brief_content, 'full_report': full_content, 'format': 'all', 'date': date})

    except ImportError as e:
        return jsonify({'status': 'error', 'error': f'Work report generator not available: {e}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/work-report/fetch-jira', methods=['POST'])
def api_work_report_fetch_jira():
    """Fetch Jira issues for today via Jira API or CLI."""
    import subprocess
    data = request.json
    date = data.get('date', '')
    jql = data.get('jql', '')

    if not date:
        from datetime import datetime
        date = datetime.now().strftime('%Y-%m-%d')

    if not jql:
        jql = f'(assignee = currentUser() OR reporter = currentUser()) AND updated >= "{date}" AND updated < "{date}" + 1d'

    # Try environment-based Jira access
    jira_url = os.environ.get('JIRA_URL', '')
    jira_token = os.environ.get('JIRA_TOKEN', '')

    if jira_url and jira_token:
        import requests as http_req
        try:
            headers = {'Authorization': f'Bearer {jira_token}', 'Content-Type': 'application/json'}
            resp = http_req.get(
                f'{jira_url}/rest/api/2/search',
                params={'jql': jql, 'maxResults': 50, 'fields': 'summary,status,labels,assignee'},
                headers=headers, timeout=15
            )
            resp.raise_for_status()
            issues = []
            for item in resp.json().get('issues', []):
                issues.append({
                    'key': item['key'],
                    'summary': item['fields']['summary'],
                    'status': item['fields']['status']['name'],
                    'url': f"{jira_url}/browse/{item['key']}",
                    'labels': item['fields'].get('labels', []),
                    'has_my_activity': True,
                })
            return jsonify({'status': 'success', 'issues': issues, 'count': len(issues)})
        except Exception as e:
            return jsonify({'status': 'error', 'error': f'Jira fetch failed: {e}'}), 500
    else:
        return jsonify({'status': 'info', 'issues': [], 'message': 'Set JIRA_URL and JIRA_TOKEN env vars for auto-fetch. Or enter issues manually.'})

@app.route('/api/work-report/fetch-github', methods=['POST'])
def api_work_report_fetch_github():
    """Fetch GitHub PRs using gh CLI."""
    import subprocess
    data = request.json
    date = data.get('date', '')

    if not date:
        from datetime import datetime
        date = datetime.now().strftime('%Y-%m-%d')

    try:
        result = subprocess.run(
            ['gh', 'search', 'prs', '--author=@me', f'--updated={date}',
             '--json', 'number,title,state,repository,url,closedAt,isDraft'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return jsonify({'status': 'error', 'error': result.stderr or 'gh CLI failed'}), 500

        import json as json_mod
        prs_raw = json_mod.loads(result.stdout) if result.stdout.strip() else []
        prs = []
        for pr in prs_raw:
            prs.append({
                'repo': pr.get('repository', {}).get('name', ''),
                'number': pr.get('number', 0),
                'title': pr.get('title', ''),
                'url': pr.get('url', ''),
                'state': pr.get('state', 'open'),
                'draft': pr.get('isDraft', False),
                'section': 'working_on',
            })
        return jsonify({'status': 'success', 'prs': prs, 'count': len(prs)})
    except FileNotFoundError:
        return jsonify({'status': 'error', 'error': 'gh CLI not installed. Install it: brew install gh'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/settings')
def settings_page():
    """Settings page for credentials and configuration."""
    return render_template('settings.html')

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
    except Exception:
        pass

    return jsonify({'status': 'success', 'updated': updated, 'env_file': env_path})

@app.route('/polarion-qa')
def polarion_qa():
    """Polarion QA Assistant page."""
    return render_template('polarion_qa.html')

@app.route('/jira-manager')
def jira_manager():
    """Jira Manager page."""
    return render_template('jira_manager.html')

@app.route('/jira-manager-improved')
def jira_manager_improved():
    """Improved Jira Manager dashboard with better UX and no JQL required."""
    return render_template('jira_manager.html')

@app.route('/api/review-code', methods=['POST'])
def api_review_code():
    """API endpoint for code review."""
    try:
        data = request.json

        result = review_code_line_by_line(
            code_content=data['code'],
            language=data.get('language', 'python'),
            review_focus=data.get('review_focus', ['security', 'bugs', 'best-practices']),
            severity_threshold=data.get('severity', 'info')
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/fetch-pr-files', methods=['POST'])
def api_fetch_pr_files():
    """API endpoint to fetch PR files from GitHub."""
    try:
        import subprocess
        data = request.json
        pr_url = data['pr_url']

        # Parse PR URL to get owner, repo, and PR number
        # Format: https://github.com/owner/repo/pull/123
        parts = pr_url.replace('https://github.com/', '').split('/')
        if len(parts) < 4:
            return jsonify({'status': 'error', 'error': 'Invalid PR URL format'}), 400

        owner, repo, _, pr_number = parts[0], parts[1], parts[2], parts[3]

        # Use gh CLI to get PR diff
        result = subprocess.run(
            ['gh', 'pr', 'diff', pr_number, '-R', f'{owner}/{repo}'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return jsonify({'status': 'error', 'error': f'Failed to fetch PR: {result.stderr}'}), 500

        # Parse the diff to extract file content
        # For now, return the full diff
        files = [{
            'filename': f'PR-{pr_number}-changes.diff',
            'content': result.stdout,
            'language': 'diff'
        }]

        # Fetch all changed files with their patches (includes @@ line numbers)
        try:
            import json

            content_result = subprocess.run(
                ['gh', 'api', f'repos/{owner}/{repo}/pulls/{pr_number}/files', '--paginate'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if content_result.returncode == 0:
                file_data = json.loads(content_result.stdout)
                if file_data and len(file_data) > 0:
                    files = []
                    for f in file_data:
                        filename = f.get('filename', 'unknown')
                        status = f.get('status', '')
                        patch = f.get('patch', '')

                        if status == 'removed' or not patch:
                            continue

                        # Extract changed lines with their real line numbers from @@ headers
                        annotated_lines = []
                        current_line = 0
                        for patch_line in patch.split('\n'):
                            hunk_match = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', patch_line)
                            if hunk_match:
                                current_line = int(hunk_match.group(1))
                                annotated_lines.append(patch_line)
                                continue
                            if patch_line.startswith('-'):
                                continue
                            if patch_line.startswith('+'):
                                annotated_lines.append(f"{current_line}: {patch_line[1:]}")
                                current_line += 1
                            else:
                                annotated_lines.append(f"{current_line}: {patch_line}")
                                current_line += 1

                        file_content = '\n'.join(annotated_lines)
                        if file_content.strip():
                            files.append({
                                'filename': filename,
                                'content': file_content,
                                'language': 'auto'
                            })

                    if not files:
                        files = [{
                            'filename': f'PR-{pr_number}-changes.diff',
                            'content': result.stdout,
                            'language': 'diff'
                        }]
        except Exception:
            pass  # Fall back to diff

        return jsonify({'status': 'success', 'files': files})

    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'error': 'Request timed out'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


def _extract_issues_checklist(llm_review_text):
    """Extract issues from LLM review as a numbered checklist for re-review verification.

    This ensures re-reviews only check these specific items regardless of which model is used.
    """
    issues = []
    issue_num = 0

    # Match the standard issue format from the LLM
    pattern = re.compile(
        r'-\s*\*\*Line (\d+(?:-\d+)?)\*\*\s*(?:\(`?([^`\)]*)`?\)\s*)?\[SEVERITY:\s*(\w+)\]\s*\[CATEGORY:\s*(\w+)\]\s*\n'
        r'\s*-\s*Issue:\s*(.*?)\n'
        r'\s*-\s*Suggestion:\s*(.*?)(?=\n\s*-\s*\*\*Line|\n##|\Z)',
        re.DOTALL
    )

    for match in pattern.finditer(llm_review_text):
        issue_num += 1
        line = match.group(1)
        filename = match.group(2) or 'unknown'
        severity = match.group(3)
        category = match.group(4)
        issue_desc = match.group(5).strip()
        suggestion = match.group(6).strip()

        issues.append(
            f"{issue_num}. [Line {line}] [{filename}] [{severity}/{category}]: {issue_desc} "
            f"(Suggested fix: {suggestion})"
        )

    if issues:
        return "ISSUES TO VERIFY (do not add new ones):\n" + "\n".join(issues)

    # Fallback: extract the "Issues Found" section raw
    issues_section = re.search(r'## Issues Found(.*?)(?=\n## |\Z)', llm_review_text, re.DOTALL)
    if issues_section:
        return "ISSUES TO VERIFY (do not add new ones):\n" + issues_section.group(1).strip()

    return llm_review_text


def _post_llm_inline_comments(gh_repo, gh_pr_number, file_path, llm_text):
    """Parse LLM review text and post inline comments with code suggestions.

    Returns dict with count and comment_ids mapped to issue numbers for later resolution.
    Posts GitHub-native suggestion blocks when code suggestions are available.
    """
    import subprocess
    import json
    inline_posted = 0
    comment_map = {}  # {issue_key: comment_id}

    # Parse issues with optional code suggestion blocks
    issue_pattern = re.compile(
        r'\*\*Line (\d+)(?:-(\d+))?\*\*\s*(?:\(`?([^`\)]+)`?\)\s*)?\[SEVERITY:\s*(\w+)\]\s*\[CATEGORY:\s*(\w+)\]\s*\n'
        r'\s*-\s*Issue:\s*(.*?)\n'
        r'\s*-\s*Suggestion:\s*(.*?)(?=\n\s*-\s*Code suggestion:|\n\s*-\s*\*\*Line|\n##|\Z)',
        re.DOTALL
    )

    # Also find code suggestions associated with each issue
    suggestion_code_pattern = re.compile(
        r'```suggestion\n([\s\S]*?)```'
    )

    # Determine actual file name (skip "all-pr-files" placeholder)
    actual_file = file_path if file_path and file_path != 'all-pr-files' else None
    issue_num = 0

    # Split by issues and extract code suggestions for each
    issues_with_suggestions = []
    issue_matches = list(issue_pattern.finditer(llm_text))

    for i, match in enumerate(issue_matches):
        issue_num += 1
        line_start = match.group(1)
        line_end = match.group(2)
        issue_file = match.group(3)
        severity = match.group(4)
        category = match.group(5)
        issue = match.group(6).strip()
        suggestion = match.group(7).strip()

        # Find code suggestion between this issue and the next one
        start_pos = match.end()
        end_pos = issue_matches[i + 1].start() if i + 1 < len(issue_matches) else len(llm_text)
        section = llm_text[start_pos:end_pos]

        code_match = suggestion_code_pattern.search(section)
        code_suggestion = code_match.group(1).strip() if code_match else None

        issues_with_suggestions.append({
            'issue_num': issue_num,
            'line_start': line_start,
            'line_end': line_end,
            'issue_file': issue_file,
            'severity': severity,
            'category': category,
            'issue': issue,
            'suggestion': suggestion,
            'code_suggestion': code_suggestion,
        })

    for item in issues_with_suggestions:
        line_ref = f"Line {item['line_start']}" + (f"-{item['line_end']}" if item['line_end'] else "")
        display_file = item['issue_file'] or actual_file
        file_ref = f" in `{display_file}`" if display_file else ""

        severity_icons = {
            'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'
        }
        icon = severity_icons.get(item['severity'].lower(), '⚪')

        comment_body = (
            f"{icon} **{item['severity'].upper()}** | {item['category']}\n\n"
            f"**Issue:** {item['issue']}\n\n"
            f"**Suggestion:** {item['suggestion']}\n\n"
        )

        # Add GitHub-native suggestion block if code suggestion is available
        if item['code_suggestion']:
            comment_body += (
                f"```suggestion\n"
                f"{item['code_suggestion']}\n"
                f"```\n\n"
            )

        comment_body += f"---\n*🤖 MCP Code Review — Issue #{item['issue_num']}*"

        # Try to post as PR review comment on specific line (enables "Apply suggestion" button)
        posted = False
        if display_file and display_file != 'all-pr-files':
            try:
                review_comment = {
                    "body": comment_body,
                    "path": display_file,
                    "line": int(item['line_start']),
                    "side": "RIGHT",
                }
                # For multi-line suggestions
                if item['line_end']:
                    review_comment["start_line"] = int(item['line_start'])
                    review_comment["line"] = int(item['line_end'])
                    review_comment["start_side"] = "RIGHT"

                # Post as a single-comment review using GitHub API
                review_payload = json.dumps({
                    "body": f"MCP Review — Issue #{item['issue_num']}",
                    "event": "COMMENT",
                    "comments": [review_comment]
                })

                result = subprocess.run(
                    ['gh', 'api', f'repos/{gh_repo}/pulls/{gh_pr_number}/reviews',
                     '--method', 'POST', '--input', '-'],
                    input=review_payload,
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    inline_posted += 1
                    posted = True
                    # Extract review comment ID from response
                    try:
                        review_data = json.loads(result.stdout)
                        review_id = review_data.get('id')
                        if review_id:
                            comment_map[str(item['issue_num'])] = str(review_id)
                    except Exception:
                        pass
            except Exception:
                pass

        # Fallback: post as regular PR comment if review comment failed
        if not posted:
            try:
                result = subprocess.run(
                    ['gh', 'pr', 'comment', gh_pr_number,
                     '--repo', gh_repo, '--body', comment_body],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    inline_posted += 1
                    comment_url = result.stdout.strip()
                    if comment_url:
                        id_match = re.search(r'issuecomment-(\d+)', comment_url)
                        if id_match:
                            comment_map[str(item['issue_num'])] = id_match.group(1)
            except Exception:
                pass

    return {'count': inline_posted, 'comment_map': comment_map}


def _resolve_inline_comments(gh_repo, pr_url, re_review_text, tracker):
    """Mark inline comments as resolved when re-review confirms they're fixed.

    Edits original GitHub comments to show ✅ RESOLVED status.
    """
    import subprocess

    comment_map = tracker.get('comment_map', {})
    if not comment_map:
        return 0

    resolved_count = 0

    # Parse re-review to find FIXED items (match table rows or status lines)
    # Match: | 1 | ... | ✅ FIXED |  or  "1. ... ✅ FIXED"
    fixed_pattern = re.compile(r'\|\s*(\d+)\s*\|.*?\|\s*✅\s*FIXED', re.IGNORECASE)
    fixed_items = set()
    for match in fixed_pattern.finditer(re_review_text):
        fixed_items.add(match.group(1))

    # Also try alternate format: "- Issue #N: ✅ FIXED"
    alt_pattern = re.compile(r'#(\d+).*?✅\s*FIXED', re.IGNORECASE)
    for match in alt_pattern.finditer(re_review_text):
        fixed_items.add(match.group(1))

    owner_repo_parts = gh_repo.split('/')
    if len(owner_repo_parts) != 2:
        return 0

    for issue_num in fixed_items:
        comment_id = comment_map.get(issue_num)
        if not comment_id:
            continue

        try:
            # Fetch current comment body
            fetch_result = subprocess.run(
                ['gh', 'api', f'repos/{gh_repo}/issues/comments/{comment_id}', '--jq', '.body'],
                capture_output=True, text=True, timeout=10
            )
            if fetch_result.returncode != 0:
                continue

            original_body = fetch_result.stdout.strip()

            # Update comment with RESOLVED banner
            resolved_body = (
                f"## ✅ RESOLVED\n\n"
                f"~~{original_body}~~\n\n"
                f"---\n*✅ This issue has been fixed and verified.*"
            )

            # Edit the comment
            edit_result = subprocess.run(
                ['gh', 'api', f'repos/{gh_repo}/issues/comments/{comment_id}',
                 '-X', 'PATCH', '-f', f'body={resolved_body}'],
                capture_output=True, text=True, timeout=10
            )
            if edit_result.returncode == 0:
                resolved_count += 1
        except Exception:
            pass

    return resolved_count


@app.route('/api/check-pr-replies', methods=['POST'])
def api_check_pr_replies():
    """Check PR author's replies to review comments and resolve if explanation is satisfactory."""
    try:
        import subprocess
        import json
        data = request.json
        pr_url = data.get('pr_url', '')

        if not pr_url:
            return jsonify({'status': 'error', 'error': 'PR URL is required'}), 400

        pr_info = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
        if not pr_info:
            return jsonify({'status': 'error', 'error': 'Invalid PR URL'}), 400

        gh_repo = f"{pr_info.group(1)}/{pr_info.group(2)}"
        gh_pr_number = pr_info.group(3)

        tracker = _pr_review_tracker.get(pr_url, {})
        comment_map = tracker.get('comment_map', {})

        if not comment_map:
            return jsonify({
                'status': 'info',
                'message': 'No inline comments tracked for this PR. Post inline comments first.',
                'resolved': 0
            })

        # Fetch all comments on the PR to find replies
        comments_result = subprocess.run(
            ['gh', 'api', f'repos/{gh_repo}/issues/{gh_pr_number}/comments', '--paginate'],
            capture_output=True, text=True, timeout=30
        )
        if comments_result.returncode != 0:
            return jsonify({'status': 'error', 'error': 'Failed to fetch PR comments'}), 500

        all_comments = json.loads(comments_result.stdout)

        # Find our bot comments and any replies that came after them
        bot_comments = {}
        for issue_num, comment_id in comment_map.items():
            bot_comments[comment_id] = {
                'issue_num': issue_num,
                'replies': [],
                'timestamp': None
            }

        # Get timestamps for our bot comments and find replies
        for comment in all_comments:
            cid = str(comment.get('id', ''))
            if cid in bot_comments:
                bot_comments[cid]['timestamp'] = comment.get('created_at', '')
                bot_comments[cid]['body'] = comment.get('body', '')

        # Find author replies (comments after our bot comment that aren't from us)
        for comment in all_comments:
            cid = str(comment.get('id', ''))
            if cid in bot_comments:
                continue

            comment_time = comment.get('created_at', '')
            comment_body = comment.get('body', '')
            comment_author = comment.get('user', {}).get('login', '')

            # Check if this comment is a reply to one of our comments
            # (posted after our comment and references it or is by the PR author)
            for bot_cid, bot_data in bot_comments.items():
                if bot_data['timestamp'] and comment_time > bot_data['timestamp']:
                    # Check if reply references the issue or is a general reply
                    issue_num = bot_data.get('issue_num', '')
                    if (f"#{issue_num}" in comment_body or
                            'resolve' in comment_body.lower() or
                            'fixed' in comment_body.lower() or
                            'addressed' in comment_body.lower() or
                            'intentional' in comment_body.lower() or
                            'by design' in comment_body.lower() or
                            len(bot_data['replies']) == 0):
                        bot_data['replies'].append({
                            'author': comment_author,
                            'body': comment_body,
                        })

        # Use LLM to evaluate replies
        resolved_count = 0
        evaluation_results = []

        from workshop_mcp_server.src.tools.llm_provider import generate, is_available
        if not is_available():
            return jsonify({
                'status': 'error',
                'error': 'LLM not available. Cannot evaluate replies.'
            }), 500

        for bot_cid, bot_data in bot_comments.items():
            if not bot_data['replies']:
                continue

            issue_num = bot_data['issue_num']
            original_comment = bot_data.get('body', '')
            replies_text = "\n".join([
                f"- {r['author']}: {r['body']}" for r in bot_data['replies']
            ])

            # Ask LLM if the reply is satisfactory
            eval_prompt = (
                f"A code reviewer posted this issue on a PR:\n\n"
                f"---\n{original_comment}\n---\n\n"
                f"The PR author replied:\n\n"
                f"---\n{replies_text}\n---\n\n"
                f"Is the author's reply a satisfactory explanation or acknowledgment? "
                f"Consider: Did they explain why the code is correct as-is? Did they acknowledge and fix it? "
                f"Did they provide a valid technical justification?\n\n"
                f"Reply with ONLY one word: SATISFIED or UNSATISFIED"
            )

            eval_result = generate(eval_prompt, system="You evaluate PR review discussions. Reply with only SATISFIED or UNSATISFIED.", temperature=0.1, max_tokens=20)

            is_satisfied = eval_result and 'SATISFIED' in eval_result.upper() and 'UNSATISFIED' not in eval_result.upper()

            evaluation_results.append({
                'issue_num': issue_num,
                'author_reply': bot_data['replies'][0]['body'][:100] if bot_data['replies'] else '',
                'satisfied': is_satisfied,
            })

            # If satisfied, mark the comment as resolved
            if is_satisfied:
                try:
                    reply_summary = bot_data['replies'][0]['body'][:80] if bot_data['replies'] else ''
                    resolved_body = (
                        f"## ✅ RESOLVED — Author's explanation accepted\n\n"
                        f"~~{original_comment}~~\n\n"
                        f"**Author's response:** {reply_summary}...\n\n"
                        f"---\n*✅ Resolved — explanation verified by AI reviewer*"
                    )

                    edit_result = subprocess.run(
                        ['gh', 'api', f'repos/{gh_repo}/issues/comments/{bot_cid}',
                         '-X', 'PATCH', '-f', f'body={resolved_body}'],
                        capture_output=True, text=True, timeout=10
                    )
                    if edit_result.returncode == 0:
                        resolved_count += 1

                        # Store feedback for future learning
                        try:
                            from workshop_mcp_server.src.tools.rag.doc_ingester import store_review_feedback
                            store_review_feedback(
                                issue_description=original_comment,
                                author_explanation=bot_data['replies'][0]['body'],
                                category='pr_review',
                                file_context=f"PR: {pr_url}",
                                pr_url=pr_url,
                            )
                        except Exception:
                            pass
                except Exception:
                    pass

        return jsonify({
            'status': 'success',
            'resolved': resolved_count,
            'total_with_replies': len(evaluation_results),
            'evaluations': evaluation_results,
            'message': f"Checked {len(evaluation_results)} replies. Resolved {resolved_count} comment(s)."
        })

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/review-pr', methods=['POST'])
def api_review_pr():
    """API endpoint for PR review."""
    try:
        import subprocess
        from datetime import datetime
        data = request.json
        pr_url = data.get('pr_url', '')

        # Check if code is provided
        if not data.get('code') or not data['code'].strip():
            return jsonify({
                'status': 'error',
                'error': 'No code provided. Please use the "Fetch PR Files" button or paste code manually.'
            }), 400

        # Track review count per PR to prevent infinite review loops
        force_review = data.get('force_review', False)
        previous_issues = None
        if pr_url:
            if pr_url not in _pr_review_tracker:
                _pr_review_tracker[pr_url] = {'count': 0, 'last_reviewed': None, 'issues': None}

            tracker = _pr_review_tracker[pr_url]
            tracker['count'] += 1
            tracker['last_reviewed'] = datetime.now().isoformat()

            if tracker['count'] > PR_REVIEW_MAX and not force_review:
                return jsonify({
                    'status': 'warning',
                    'warning': 'review_limit_reached',
                    'review_count': tracker['count'],
                    'max_reviews': PR_REVIEW_MAX,
                    'message': (
                        f"This PR has already been reviewed {tracker['count'] - 1} time(s). "
                        f"AI reviewers may give different suggestions each time, creating an infinite loop. "
                        f"Consider applying the existing suggestions first."
                    ),
                }), 200

            # On re-review, use the stored issues from the first review
            if tracker['count'] > 1 and tracker.get('issues'):
                previous_issues = tracker['issues']

        # Review the code (detect if it's a PR diff with annotated line numbers)
        code = data['code']
        is_pr_diff = bool(re.search(r'^@@ -\d+', code, re.MULTILINE) or re.search(r'^\d+: ', code, re.MULTILINE))

        review_result = review_code_line_by_line(
            code_content=code,
            file_path=data.get('file_path', 'unknown'),
            language=data.get('language', 'go'),
            review_focus=['security', 'performance', 'bugs', 'best-practices', 'maintainability', 'style'],
            severity_threshold='info',
            is_pr_diff=is_pr_diff,
            previous_issues=previous_issues
        )

        # Store the issues from the first review for future re-reviews
        if pr_url and pr_url in _pr_review_tracker:
            if _pr_review_tracker[pr_url]['count'] == 1:
                if review_result.get('mode') == 'llm' and review_result.get('llm_review'):
                    # Extract only the Issues Found section as a checklist
                    llm_text = review_result['llm_review']
                    _pr_review_tracker[pr_url]['issues'] = _extract_issues_checklist(llm_text)
                    _pr_review_tracker[pr_url]['model_used'] = review_result.get('llm_model', 'unknown')
                elif review_result.get('line_reviews'):
                    _pr_review_tracker[pr_url]['issues'] = review_result.get('summary', '')

        # Post to GitHub if requested
        if data.get('post_to_github', False) and pr_url:
            # If LLM mode, post the LLM review text directly to GitHub
            if review_result.get('mode') == 'llm' and review_result.get('llm_review'):
                pr_info = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
                if pr_info:
                    gh_repo = f"{pr_info.group(1)}/{pr_info.group(2)}"
                    gh_pr_number = pr_info.group(3)
                    file_path = data.get('file_path', 'unknown')

                    llm_text = review_result['llm_review']
                    model_info = f"{review_result.get('llm_provider', 'LLM')} ({review_result.get('llm_model', 'unknown')})"

                    # Build the summary comment with file name info
                    comment_body = f"## 🤖 AI Code Review ({model_info})\n\n"
                    comment_body += f"**Reviewed file(s):** `{file_path}`\n\n"
                    comment_body += f"{llm_text}\n\n---\n*🤖 Automated review by MCP Code Reviewer*"

                    gh_result = subprocess.run(
                        ['gh', 'pr', 'comment', gh_pr_number,
                         '--repo', gh_repo, '--body', comment_body],
                        capture_output=True, text=True, timeout=30
                    )

                    inline_posted = 0
                    resolved_count = 0
                    tracker = _pr_review_tracker.get(pr_url, {})

                    # On re-review: resolve fixed inline comments from previous review
                    if tracker.get('count', 0) > 1 and tracker.get('comment_map'):
                        resolved_count = _resolve_inline_comments(
                            gh_repo, pr_url, llm_text, tracker
                        )

                    # On first review: post inline comments and store their IDs
                    if data.get('post_inline', False) and tracker.get('count', 1) == 1:
                        inline_result = _post_llm_inline_comments(
                            gh_repo, gh_pr_number, file_path, llm_text
                        )
                        inline_posted = inline_result['count']
                        # Store comment IDs for future resolution
                        if pr_url and pr_url in _pr_review_tracker:
                            _pr_review_tracker[pr_url]['comment_map'] = inline_result['comment_map']
                    elif data.get('post_inline', False):
                        inline_result = _post_llm_inline_comments(
                            gh_repo, gh_pr_number, file_path, llm_text
                        )
                        inline_posted = inline_result['count']

                    post_result = {
                        'status': 'success' if gh_result.returncode == 0 else 'error',
                        'summary_posted': gh_result.returncode == 0,
                        'review_action': 'comment',
                        'inline_comments_posted': inline_posted,
                        'comments_resolved': resolved_count,
                        'error': gh_result.stderr if gh_result.returncode != 0 else None,
                    }
                else:
                    post_result = {'status': 'error', 'error': 'Invalid PR URL'}
            else:
                post_result = post_pr_review_comments(
                    pr_url=pr_url,
                    review_results=review_result,
                    post_summary=True,
                    post_inline_comments=data.get('post_inline', False),
                    approve_if_clean=data.get('approve', False)
                )

            review_count = _pr_review_tracker.get(pr_url, {}).get('count', 1) if pr_url else 1
            review_result['review_count'] = review_count
            return jsonify({
                'status': 'success',
                'review': review_result,
                'post_result': post_result
            })

        # Add review count to response
        review_count = _pr_review_tracker.get(pr_url, {}).get('count', 1) if pr_url else 1
        review_result['review_count'] = review_count
        return jsonify(review_result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/generate-ocp-test', methods=['POST'])
def api_generate_ocp_test():
    """API endpoint for OCP test generation."""
    try:
        data = request.json

        # Validate input first
        validation = validate_ocp_test_input(
            feature=data['feature'],
            component=data['component'],
            scenario=data['scenario']
        )

        # Check if validation found errors
        if validation.get('status') == 'success':
            validation_data = validation.get('validation', {})
            if not validation_data.get('valid', True):
                # Return validation errors if any
                return jsonify({
                    'status': 'error',
                    'error': 'Validation failed',
                    'validation_errors': validation_data.get('errors', []),
                    'warnings': validation_data.get('warnings', [])
                }), 400

        # Generate test
        if data.get('format') == 'shell':
            result = generate_oc_cli_test(
                feature=data['feature'],
                component=data['component'],
                scenario=data['scenario'],
                namespace=data.get('namespace')
            )
        else:
            result = generate_ocp_test_case(
                feature=data['feature'],
                component=data['component'],
                scenario=data['scenario'],
                test_format=data.get('format', 'yaml'),
                namespace=data.get('namespace')
            )

        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/execute-ocp-test', methods=['POST'])
def api_execute_ocp_test():
    """API endpoint for OCP test execution."""
    try:
        data = request.json

        result = execute_ocp_test_step_by_step(
            feature=data['feature'],
            component=data['component'],
            scenario=data['scenario'],
            namespace=data.get('namespace'),
            kubeconfig_path=data.get('kubeconfig_path'),
            oc_path=data.get('oc_path'),
            timeout_per_step=data.get('timeout', 300)
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/debug-ocp-test', methods=['POST'])
def api_debug_ocp_test():
    """API endpoint for OCP test debugging."""
    try:
        data = request.json

        result = debug_ocp_test_failure(
            test_results=data['test_results'],
            feature=data.get('feature'),
            component=data.get('component')
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

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


@app.route('/api/analyze-mustgather', methods=['POST'])
def api_analyze_mustgather():
    """API endpoint for must-gather analysis."""
    try:
        import asyncio
        data = request.json

        bundle_path = data.get('bundle_path', '')
        detailed_analysis = data.get('detailed_analysis', True)

        if not bundle_path or not bundle_path.strip():
            return jsonify({
                'status': 'error',
                'error': 'Bundle path is required'
            }), 400

        # Check if path exists
        if not os.path.exists(bundle_path):
            return jsonify({
                'status': 'error',
                'error': f'Path not found: {bundle_path}'
            }), 400

        # Run async analysis in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                analyze_mustgather_bundle(bundle_path, detailed_analysis)
            )
        finally:
            loop.close()

        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/analyze-component', methods=['POST'])
def api_analyze_component():
    """LLM-powered deep analysis for a specific component from must-gather data."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available
        if not is_available():
            return jsonify({'status': 'error', 'error': 'LLM not available'}), 500

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

        result = generate(prompt, system=system_prompt)
        if not result:
            return jsonify({'status': 'error', 'error': 'LLM returned empty response'}), 500

        return jsonify({
            'status': 'success',
            'analysis': result,
            'component': component
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
                    # End env section on next non-indented or known field
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
                    if stripped.startswith('Conditions:') or stripped.startswith('QoS') or stripped.startswith('Events:') or (stripped.startswith('===') ):
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
        except Exception as llm_err:
            logger.warning(f"LLM test generation failed: {llm_err}")

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

@app.route('/api/search-polarion-testcases', methods=['POST'])
def api_search_polarion_testcases():
    """API endpoint for Polarion test case search."""
    if not POLARION_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Polarion tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        
        keywords = data.get('keywords', '')
        component = data.get('component')
        version = data.get('version')
        status = data.get('status')
        test_type = data.get('test_type')
        limit = data.get('limit', 10)

        if not keywords or not keywords.strip():
            return jsonify({
                'status': 'error',
                'error': 'Keywords are required for search'
            }), 400

        # Call the Polarion search function
        result = search_test_cases(
            keywords=keywords,
            component=component,
            version=version,
            status=status,
            test_type=test_type,
            limit=limit
        )

        # Format results for display
        if result.get('status') == 'success':
            formatted_results = format_search_results(result)
            result['formatted_results'] = formatted_results

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/get-polarion-testcase-details', methods=['POST'])
def api_get_polarion_testcase_details():
    """API endpoint for getting Polarion test case details."""
    if not POLARION_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Polarion tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        test_case_id = data.get('test_case_id', '').strip()

        if not test_case_id:
            return jsonify({
                'status': 'error',
                'error': 'Test case ID is required'
            }), 400

        # Call the Polarion details function
        result = get_test_case_details(test_case_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/query-polarion-custom', methods=['POST'])
def api_query_polarion_custom():
    """API endpoint for custom Polarion WIQL queries."""
    if not POLARION_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Polarion tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        
        wiql_query = data.get('wiql_query', '').strip()
        fields = data.get('fields')
        limit = data.get('limit', 20)

        if not wiql_query:
            return jsonify({
                'status': 'error',
                'error': 'WIQL query is required'
            }), 400

        # Call the custom query function
        result = query_polarion_api(
            wiql_query=wiql_query,
            fields=fields,
            limit=limit
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# Jira Manager API Endpoints
@app.route('/api/jira-test-connection', methods=['POST'])
def api_jira_test_connection():
    """API endpoint for testing Jira connection."""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        base_url = data.get('base_url', '').strip()
        username = data.get('username', '').strip()
        api_token = data.get('api_token', '').strip()
        password = data.get('password', '').strip()

        if not base_url or not username:
            return jsonify({
                'status': 'error',
                'error': 'Base URL and Username are required'
            }), 400
        
        if not api_token and not password:
            return jsonify({
                'status': 'error',
                'error': 'Either API Token or Password is required'
            }), 400

        result = test_jira_connection(base_url, username, api_token, password)

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-get-projects', methods=['POST'])
def api_jira_get_projects():
    """API endpoint to fetch all accessible Jira projects."""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        base_url = data.get('base_url', '').strip()
        username = data.get('username', '').strip()
        api_token = data.get('api_token', '').strip()
        password = data.get('password', '').strip()

        if not base_url or not username:
            return jsonify({
                'status': 'error',
                'error': 'Base URL and Username are required'
            }), 400
        
        if not api_token and not password:
            return jsonify({
                'status': 'error',
                'error': 'Either API Token or Password is required'
            }), 400

        result = get_jira_projects(base_url, username, api_token, password)
        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-fetch-all-issues', methods=['POST'])
def api_jira_fetch_all_issues():
    """API endpoint to fetch all accessible Jira issues for client-side filtering."""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        base_url = data.get('base_url', '').strip()
        username = data.get('username', '').strip()
        api_token = data.get('api_token', '').strip()
        password = data.get('password', '').strip()
        max_results = data.get('max_results', 500)  # Default to 500 for performance

        if not base_url or not username:
            return jsonify({
                'status': 'error',
                'error': 'Base URL and Username are required'
            }), 400
        
        if not api_token and not password:
            return jsonify({
                'status': 'error',
                'error': 'Either API Token or Password is required'
            }), 400

        result = fetch_all_jira_issues(base_url, username, api_token, password, max_results)
        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-demo-data', methods=['POST'])
def api_jira_demo_data():
    """Provide demo data for testing when real Jira is not accessible"""
    try:
        # Generate sample issues for testing
        demo_issues = []
        projects = ['OCPQE', 'USHIFT', 'OCPBUGS', 'WRKLDS', 'BUILD']
        statuses = ['Open', 'In Progress', 'To Do', 'Done', 'Closed']
        priorities = ['Critical', 'High', 'Major', 'Medium', 'Normal', 'Low']
        issue_types = ['Bug', 'Task', 'Story', 'Epic', 'Improvement']
        assignees = ['Rahul Gangwar', 'John Doe', 'Jane Smith', 'Bob Wilson', None]
        
        import random
        from datetime import datetime, timedelta
        
        for i in range(100):
            project = random.choice(projects)
            issue = {
                'key': f'{project}-{1000 + i}',
                'summary': f'Sample issue {i+1} - {random.choice(["API test", "Bug fix", "Feature request", "Performance improvement"])}',
                'status': random.choice(statuses),
                'priority': random.choice(priorities),
                'issue_type': random.choice(issue_types),
                'project': project,
                'project_name': f'{project} Project',
                'assignee': random.choice(assignees),
                'assignee_email': f'{random.choice(assignees).lower().replace(" ", ".")}@redhat.com' if random.choice(assignees) else None,
                'reporter': 'Rahul Gangwar',
                'created': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                'updated': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                'description': f'This is a demo issue for testing the client-side filtering functionality. Issue {i+1}.',
                'labels': random.sample(['api', 'frontend', 'backend', 'testing', 'urgent'], k=random.randint(0, 3)),
                'components': random.sample(['Authentication', 'UI', 'Database', 'API'], k=random.randint(0, 2))
            }
            demo_issues.append(issue)
        
        # Calculate filter counts
        filter_counts = {
            'projects': {},
            'assignees': {},
            'statuses': {},
            'priorities': {},
            'issue_types': {},
            'total': len(demo_issues)
        }
        
        for issue in demo_issues:
            # Project counts
            project = issue.get('project', 'Unknown')
            filter_counts['projects'][project] = filter_counts['projects'].get(project, 0) + 1
            
            # Assignee counts
            assignee = issue.get('assignee', 'Unassigned') or 'Unassigned'
            filter_counts['assignees'][assignee] = filter_counts['assignees'].get(assignee, 0) + 1
            
            # Status counts
            status = issue.get('status', 'Unknown')
            filter_counts['statuses'][status] = filter_counts['statuses'].get(status, 0) + 1
            
            # Priority counts
            priority = issue.get('priority', 'Undefined')
            filter_counts['priorities'][priority] = filter_counts['priorities'].get(priority, 0) + 1
            
            # Issue type counts
            issue_type = issue.get('issue_type', 'Unknown')
            filter_counts['issue_types'][issue_type] = filter_counts['issue_types'].get(issue_type, 0) + 1
        
        return jsonify({
            'status': 'success',
            'issues': demo_issues,
            'total': len(demo_issues),
            'filter_counts': filter_counts,
            'message': f'Loaded {len(demo_issues)} demo issues for testing',
            'demo': True
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-debug-auth', methods=['POST'])
def api_jira_debug_auth():
    """Debug API authentication with detailed testing"""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        base_url = data.get('base_url', '').strip()
        username = data.get('username', '').strip()
        api_token = data.get('api_token', '').strip()
        password = data.get('password', '').strip()

        debug_results = []
        
        # Test 1: Basic URL accessibility
        debug_results.append({
            'test': 'URL Format',
            'result': 'Valid' if base_url.startswith('https://') else 'Invalid - must start with https://',
            'value': base_url
        })
        
        # Test 2: Authentication format
        auth_type = 'API Token' if api_token else ('Password' if password else 'None')
        debug_results.append({
            'test': 'Authentication Type',
            'result': auth_type,
            'value': f"Username: {username}, Auth: {auth_type}"
        })
        
        # Test 3: Try different API endpoints
        from workshop_mcp_server.src.tools.jira_manager_tool import JiraClient
        client = JiraClient(base_url, username, api_token, password)
        
        endpoints = [
            ('/rest/api/2/serverInfo', 'Server Info v2'),
            ('/rest/api/3/serverInfo', 'Server Info v3'),
            ('/rest/api/2/myself', 'User Info v2'),
            ('/rest/api/3/myself', 'User Info v3'),
            ('/rest/api/2/permissions', 'Permissions v2'),
            ('/rest/api/3/permissions', 'Permissions v3')
        ]
        
        import requests
        
        for endpoint_path, description in endpoints:
            try:
                full_url = f"{base_url.rstrip('/')}{endpoint_path}"
                
                # Configure proxy settings for corporate environments
                proxies = {}
                
                # Try to use system proxy settings
                import os
                http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
                https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
                
                if http_proxy:
                    proxies['http'] = http_proxy
                if https_proxy:
                    proxies['https'] = https_proxy
                
                # Make direct request to see exact error
                response = requests.get(
                    full_url,
                    auth=(username, api_token or password),
                    headers={'Accept': 'application/json'},
                    timeout=10,
                    proxies=proxies if proxies else None,
                    verify=True
                )
                
                if response.status_code == 200:
                    debug_results.append({
                        'test': description,
                        'result': '✅ Success',
                        'value': f"Status: {response.status_code}"
                    })
                else:
                    debug_results.append({
                        'test': description, 
                        'result': f'❌ Failed',
                        'value': f"Status: {response.status_code} - {response.reason}"
                    })
                    
            except requests.exceptions.ProxyError as e:
                debug_results.append({
                    'test': description,
                    'result': '🌐 Proxy Error',
                    'value': str(e)[:100]
                })
            except requests.exceptions.ConnectionError as e:
                debug_results.append({
                    'test': description,
                    'result': '🔌 Connection Error', 
                    'value': str(e)[:100]
                })
            except Exception as e:
                debug_results.append({
                    'test': description,
                    'result': '⚠️ Error',
                    'value': str(e)[:100]
                })
        
        return jsonify({
            'status': 'success',
            'debug_results': debug_results,
            'recommendations': [
                "✅ If any test shows 'Success', your credentials work!",
                "❌ If all tests fail with 'Proxy Error', check VPN connection",
                "🔑 If tests show '401 Unauthorized', check your API token",
                "🚫 If tests show '403 Forbidden', contact admin for API permissions",
                "📍 If Server Info works but User Info fails, token has limited permissions"
            ]
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/set-proxy', methods=['POST'])
def api_set_proxy():
    """Set proxy configuration for corporate environments"""
    try:
        data = request.json
        http_proxy = data.get('http_proxy', '').strip()
        https_proxy = data.get('https_proxy', '').strip()
        
        # Set environment variables for proxy
        import os
        if http_proxy:
            os.environ['HTTP_PROXY'] = http_proxy
            os.environ['http_proxy'] = http_proxy
        
        if https_proxy:
            os.environ['HTTPS_PROXY'] = https_proxy
            os.environ['https_proxy'] = https_proxy
            
        return jsonify({
            'status': 'success',
            'message': 'Proxy settings updated',
            'http_proxy': http_proxy or 'Not set',
            'https_proxy': https_proxy or 'Not set'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/test-network-comparison', methods=['POST'])
def api_test_network_comparison():
    """Compare network access between working MCP service and Jira"""
    try:
        data = request.json
        jira_url = data.get('jira_url', 'https://redhat.atlassian.net')
        
        import requests
        import time
        
        test_results = []
        
        # Test 1: Basic connectivity to Jira domain
        try:
            start_time = time.time()
            response = requests.head(f"{jira_url.rstrip('/')}/", timeout=10, verify=True)
            elapsed = round((time.time() - start_time) * 1000)
            
            test_results.append({
                'test': 'Jira Domain Access',
                'status': f'✅ Success ({response.status_code})',
                'timing': f'{elapsed}ms',
                'details': f'Basic domain connectivity works'
            })
            
        except Exception as e:
            test_results.append({
                'test': 'Jira Domain Access',
                'status': '❌ Failed',
                'timing': 'N/A',
                'details': str(e)[:150]
            })
        
        # Test 2: Compare with working endpoint (httpbin for testing)
        try:
            start_time = time.time()
            response = requests.get('https://httpbin.org/status/200', timeout=10, verify=True)
            elapsed = round((time.time() - start_time) * 1000)
            
            test_results.append({
                'test': 'Reference API (httpbin)',
                'status': f'✅ Success ({response.status_code})',
                'timing': f'{elapsed}ms',
                'details': 'External API access works fine'
            })
            
        except Exception as e:
            test_results.append({
                'test': 'Reference API (httpbin)',
                'status': '❌ Failed',
                'timing': 'N/A',
                'details': str(e)[:150]
            })
        
        # Test 3: Specific Jira API endpoint
        try:
            start_time = time.time()
            jira_api_url = f"{jira_url.rstrip('/')}/rest/api/2/serverInfo"
            response = requests.get(jira_api_url, timeout=10, verify=True)
            elapsed = round((time.time() - start_time) * 1000)
            
            test_results.append({
                'test': 'Jira API Endpoint (no auth)',
                'status': f'✅ Success ({response.status_code})',
                'timing': f'{elapsed}ms',  
                'details': 'Jira API endpoint is reachable'
            })
            
        except Exception as e:
            test_results.append({
                'test': 'Jira API Endpoint (no auth)',
                'status': '❌ Failed',
                'timing': 'N/A',
                'details': str(e)[:150]
            })
        
        # Test 4: DNS resolution
        try:
            import socket
            start_time = time.time()
            ip = socket.gethostbyname('redhat.atlassian.net')
            elapsed = round((time.time() - start_time) * 1000)
            
            test_results.append({
                'test': 'DNS Resolution',
                'status': '✅ Success',
                'timing': f'{elapsed}ms',
                'details': f'redhat.atlassian.net resolves to {ip}'
            })
            
        except Exception as e:
            test_results.append({
                'test': 'DNS Resolution',
                'status': '❌ Failed',
                'timing': 'N/A',
                'details': str(e)[:150]
            })
        
        return jsonify({
            'status': 'success',
            'test_results': test_results,
            'summary': f"Completed {len(test_results)} network tests",
            'recommendations': [
                "🔍 If Reference API works but Jira fails → Jira-specific blocking",
                "🌐 If DNS fails → Network connectivity issue", 
                "⏱️ Compare timings → Slow responses may indicate proxy",
                "✅ If Jira domain works but API fails → Authentication/endpoint issue"
            ]
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-get-issue', methods=['POST'])
def api_jira_get_issue():
    """API endpoint for getting a specific Jira issue."""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        issue_id = data.get('issue_id', '').strip()

        if not issue_id:
            return jsonify({
                'status': 'error',
                'error': 'Issue ID is required'
            }), 400

        # Extract credentials from request
        base_url = data.get('base_url')
        username = data.get('username') 
        api_token = data.get('api_token')
        password = data.get('password')

        result = get_issue(issue_id, base_url, username, api_token, password)
        
        # Format results for display
        if result.get('status') == 'success':
            formatted_results = format_jira_results(result)
            result['formatted_results'] = formatted_results

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-my-issues', methods=['POST'])
def api_jira_my_issues():
    """API endpoint for getting user's own issues."""
    if not JIRA_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Jira not available'}), 500
    try:
        data = request.json
        issue_type = data.get('issue_type', 'assigned')
        status_filter = data.get('status_filter', '')
        max_results = data.get('max_results', 50)
        base_url = data.get('base_url')
        username = data.get('username')
        api_token = data.get('api_token')
        password = data.get('password', '')
        client = _get_jira_client(base_url, username, api_token, password)
        if not client.auth_configured:
            return jsonify({'status': 'error', 'error': 'No Jira credentials configured'}), 400
        result = client.get_my_issues(issue_type, status_filter, max_results)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-add-comment', methods=['POST'])
def api_jira_add_comment():
    """API endpoint for adding a comment to a Jira issue."""
    if not JIRA_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Jira not available'}), 500
    try:
        data = request.json
        issue_key = data.get('issue_key', '').strip()
        comment = data.get('comment', '').strip()
        if not issue_key or not comment:
            return jsonify({'status': 'error', 'error': 'Issue key and comment are required'}), 400
        base_url = data.get('base_url')
        username = data.get('username')
        api_token = data.get('api_token')
        password = data.get('password', '')
        client = _get_jira_client(base_url, username, api_token, password)
        result = client.add_comment(issue_key, comment)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-get-comments', methods=['POST'])
def api_jira_get_comments():
    """API endpoint for getting comments on a Jira issue."""
    if not JIRA_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Jira not available'}), 500
    try:
        data = request.json
        issue_key = data.get('issue_key', '').strip()
        if not issue_key:
            return jsonify({'status': 'error', 'error': 'Issue key required'}), 400
        base_url = data.get('base_url')
        username = data.get('username')
        api_token = data.get('api_token')
        password = data.get('password', '')
        client = _get_jira_client(base_url, username, api_token, password)
        result = client.get_comments(issue_key)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-get-transitions', methods=['POST'])
def api_jira_get_transitions():
    """API endpoint for getting available transitions."""
    if not JIRA_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Jira not available'}), 500
    try:
        data = request.json
        issue_key = data.get('issue_key', '').strip()
        if not issue_key:
            return jsonify({'status': 'error', 'error': 'Issue key required'}), 400
        base_url = data.get('base_url')
        username = data.get('username')
        api_token = data.get('api_token')
        password = data.get('password', '')
        client = _get_jira_client(base_url, username, api_token, password)
        result = client.get_transitions(issue_key)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-transition-issue', methods=['POST'])
def api_jira_transition_issue():
    """API endpoint for transitioning an issue."""
    if not JIRA_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Jira not available'}), 500
    try:
        data = request.json
        issue_key = data.get('issue_key', '').strip()
        transition_id = data.get('transition_id', '').strip()
        comment = data.get('comment', '')
        if not issue_key or not transition_id:
            return jsonify({'status': 'error', 'error': 'Issue key and transition_id required'}), 400
        base_url = data.get('base_url')
        username = data.get('username')
        api_token = data.get('api_token')
        password = data.get('password', '')
        client = _get_jira_client(base_url, username, api_token, password)
        result = client.transition_issue(issue_key, transition_id, comment)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-assign-issue', methods=['POST'])
def api_jira_assign_issue():
    """API endpoint for assigning a Jira issue."""
    if not JIRA_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Jira not available'}), 500
    try:
        data = request.json
        issue_key = data.get('issue_key', '').strip()
        assignee = data.get('assignee', '').strip()
        if not issue_key or not assignee:
            return jsonify({'status': 'error', 'error': 'Issue key and assignee required'}), 400
        base_url = data.get('base_url')
        username = data.get('username')
        api_token = data.get('api_token')
        password = data.get('password', '')
        client = _get_jira_client(base_url, username, api_token, password)
        result = client.assign_issue(issue_key, assignee)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-search-issues', methods=['POST'])
def api_jira_search_issues():
    """API endpoint for searching Jira issues."""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        query = data.get('query', '').strip()
        max_results = data.get('max_results', 20)

        if not query:
            return jsonify({
                'status': 'error',
                'error': 'JQL query is required'
            }), 400

        # Extract credentials from request
        base_url = data.get('base_url')
        username = data.get('username')
        api_token = data.get('api_token')
        password = data.get('password')

        result = search_issues(query, max_results, base_url, username, api_token, password)
        
        # Format results for display
        if result.get('status') == 'success':
            formatted_results = format_jira_results(result)
            result['formatted_results'] = formatted_results

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-high-priority-bugs', methods=['POST'])
def api_jira_high_priority_bugs():
    """API endpoint for getting high priority bugs."""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        team = data.get('team', '').strip()
        days = data.get('days', 30)

        # Extract credentials from request
        base_url = data.get('base_url')
        username = data.get('username')
        api_token = data.get('api_token')
        password = data.get('password')

        result = get_high_priority_bugs(team if team else None, days, base_url, username, api_token, password)
        
        # Format results for display
        if result.get('status') == 'success':
            formatted_results = format_jira_results(result)
            result['formatted_results'] = formatted_results

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-team-issues', methods=['POST'])
def api_jira_team_issues():
    """API endpoint for getting team issues."""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        team_name = data.get('team_name', '').strip()
        status = data.get('status', '').strip()
        days = data.get('days', 14)

        if not team_name:
            return jsonify({
                'status': 'error',
                'error': 'Team name is required'
            }), 400

        # Extract credentials from request
        base_url = data.get('base_url')
        username = data.get('username')
        api_token = data.get('api_token')
        password = data.get('password')

        result = get_team_issues(team_name, status if status else None, days, base_url, username, api_token, password)
        
        # Format results for display
        if result.get('status') == 'success':
            formatted_results = format_jira_results(result)
            result['formatted_results'] = formatted_results

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-generate-test-cases', methods=['POST'])
def api_jira_generate_test_cases():
    """API endpoint for generating test cases from Jira issue."""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        issue_id = data.get('issue_id', '').strip()
        test_types = data.get('test_types', ['functional', 'edge', 'negative', 'regression'])
        base_url = data.get('base_url', '').strip() or None
        username = data.get('username', '').strip() or None
        api_token = data.get('api_token', '').strip() or None
        password = data.get('password', '').strip() or None

        if not issue_id:
            return jsonify({
                'status': 'error',
                'error': 'Issue ID is required'
            }), 400

        result = generate_test_cases_from_jira(issue_id, test_types, base_url=base_url, username=username, api_token=api_token, password=password)

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/jira-generate-test-plan', methods=['POST'])
def api_jira_generate_test_plan():
    """API endpoint for generating test plan from Jira issue."""
    if not JIRA_AVAILABLE:
        return jsonify({
            'status': 'error',
            'error': 'Jira Manager tools are not available. Please check your setup.'
        }), 500
    
    try:
        data = request.json
        issue_id = data.get('issue_id', '').strip()
        base_url = data.get('base_url', '').strip() or None
        username = data.get('username', '').strip() or None
        api_token = data.get('api_token', '').strip() or None
        password = data.get('password', '').strip() or None

        if not issue_id:
            return jsonify({
                'status': 'error',
                'error': 'Issue ID is required'
            }), 400

        result = generate_test_plan_from_jira(issue_id, base_url=base_url, username=username, api_token=api_token, password=password)

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ============================================================
# AI Chat Integration (Ollama / Llama3)
# ============================================================
try:
    import ollama_client
    OLLAMA_IMPORTED = True
    print("✅ Ollama/Llama3 client loaded")
except ImportError:
    OLLAMA_IMPORTED = False
    print("⚠️  Ollama client not available")


@app.route('/ai-chat')
def ai_chat():
    """AI Chat page powered by local Llama3."""
    return render_template('ai_chat.html')


@app.route('/api/ai/status', methods=['GET'])
def api_ai_status():
    """Check backend availability, list models, and report current mode."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import get_config, is_available as llm_is_available
        config = get_config()
    except ImportError:
        config = {"mode": "template", "model": "llama3", "ollama_model": "llama3",
                  "claude_model": "claude-sonnet-4-5@20250929", "ollama_url": "http://localhost:11434",
                  "claude_configured": False}

    # Get Ollama models if available
    ollama_available = False
    models = []
    if OLLAMA_IMPORTED:
        ollama_available = ollama_client.is_ollama_available()
        models = ollama_client.list_models() if ollama_available else []

    return jsonify({
        'available': ollama_available,
        'ollama_available': ollama_available,
        'claude_configured': config.get('claude_configured', False),
        'models': models,
        'mode': config['mode'],
        'model': config['model'],
        'ollama_model': config.get('ollama_model', 'llama3'),
        'claude_model': config.get('claude_model', 'claude-sonnet-4-5@20250929'),
    })


@app.route('/api/ai/switch-mode', methods=['POST'])
def api_ai_switch_mode():
    """Switch between 'ollama', 'claude', and 'template' mode at runtime."""
    data = request.json or {}
    new_mode = data.get('mode', '').strip().lower()
    new_model = data.get('model', '').strip()

    if new_mode and new_mode not in ('ollama', 'claude', 'template'):
        return jsonify({'status': 'error', 'error': "mode must be 'ollama', 'claude', or 'template'"}), 400

    try:
        from workshop_mcp_server.src.tools.llm_provider import set_mode, set_model, get_config, is_available as llm_is_available
        if new_mode:
            set_mode(new_mode)
        if new_model:
            set_model(new_model)

        config = get_config()
        ollama_online = False
        if config['mode'] == 'ollama':
            ollama_online = llm_is_available()

        return jsonify({
            'status': 'success',
            'mode': config['mode'],
            'model': config['model'],
            'ollama_model': config.get('ollama_model', 'llama3'),
            'claude_model': config.get('claude_model', 'claude-sonnet-4-5@20250929'),
            'ollama_available': ollama_online,
            'claude_configured': config.get('claude_configured', False),
            'message': f"Switched to {config['mode']} mode ({config['model']})",
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


@app.route('/api/ai/generate', methods=['POST'])
def api_ai_generate():
    """Non-streaming generation using active LLM (Claude or Ollama)."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config
        if not is_available():
            return jsonify({'error': 'LLM not available. Check Settings.'}), 500

        data = request.json
        prompt = data.get('prompt', '')
        system = data.get('system', '')

        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        response = generate(prompt, system=system)
        config = get_config()
        if response:
            return jsonify({'status': 'success', 'response': response, 'model': config['model'], 'mode': config['mode']})
        return jsonify({'status': 'error', 'error': 'LLM returned no response'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/ai/review-code', methods=['POST'])
def api_ai_review_code():
    """AI-powered code review using active LLM (Claude or Ollama)."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import review_code, is_available, get_config
        if not is_available():
            return jsonify({'error': 'LLM not available. Check Settings.'}), 500

        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'go')

        if not code:
            return jsonify({'error': 'No code provided'}), 400

        result = review_code(code, language=language)
        config = get_config()
        if result:
            return jsonify({'status': 'success', 'review': result, 'model': config['model'], 'mode': config['mode']})
        return jsonify({'status': 'error', 'error': 'LLM returned no response'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/ai/generate-tests', methods=['POST'])
def api_ai_generate_tests():
    """AI-powered test case generation using active LLM (Claude or Ollama)."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate_test_case, is_available, get_config
        if not is_available():
            return jsonify({'error': 'LLM not available. Check Settings.'}), 500

        data = request.json
        description = data.get('description', '')
        context = data.get('context', '')

        if not description:
            return jsonify({'error': 'No description provided'}), 400

        result = generate_test_case(
            feature=description,
            component=context or 'general',
            scenario=description,
            test_format='go'
        )
        config = get_config()
        if result:
            return jsonify({'status': 'success', 'tests': result, 'model': config['model'], 'mode': config['mode']})
        return jsonify({'status': 'error', 'error': 'LLM returned no response'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/ai/debug-cluster', methods=['POST'])
def api_ai_debug_cluster():
    """AI-powered cluster debugging using active LLM (Claude or Ollama)."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import debug_cluster_issue, is_available, get_config
        if not is_available():
            return jsonify({'error': 'LLM not available. Check Settings.'}), 500

        data = request.json
        state = data.get('state', '')

        if not state:
            return jsonify({'error': 'No cluster state provided'}), 400

        result = debug_cluster_issue(issue=state)
        config = get_config()
        if result:
            return jsonify({'status': 'success', 'analysis': result, 'model': config['model'], 'mode': config['mode']})
        return jsonify({'status': 'error', 'error': 'LLM returned no response'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/test-plan-generator')
def test_plan_generator():
    """Control Plane Test Plan Generator page."""
    return render_template('test_plan_generator.html')


@app.route('/api/generate-test-plan-from-doc', methods=['POST'])
def api_generate_test_plan_from_doc():
    """Generate structured test plan from enhancement/design document using LLM."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config

        if not is_available():
            return jsonify({'status': 'error', 'error': 'LLM not available. Check Settings.'}), 500

        data = request.json
        doc_content = data.get('doc_content', '').strip()
        pr_url = data.get('pr_url', '').strip()
        feature_name = data.get('feature_name', '').strip()
        target_components = data.get('target_components', '').strip()
        focus_areas = data.get('focus_areas', [])

        if not doc_content and not pr_url:
            return jsonify({'status': 'error', 'error': 'Provide either document content or PR URL'}), 400

        # If PR URL provided, fetch the diff
        input_context = doc_content
        if pr_url and not doc_content:
            import subprocess
            try:
                # Try to fetch PR diff via gh CLI
                parts = pr_url.rstrip('/').split('/')
                pr_num = parts[-1]
                repo = f"{parts[-4]}/{parts[-3]}"
                result = subprocess.run(
                    ['gh', 'pr', 'diff', pr_num, '--repo', repo],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    input_context = f"PR: {pr_url}\n\nDiff:\n{result.stdout[:15000]}"
                else:
                    return jsonify({'status': 'error', 'error': f'Could not fetch PR diff: {result.stderr}'}), 400
            except Exception as e:
                return jsonify({'status': 'error', 'error': f'Failed to fetch PR: {str(e)}'}), 400

        focus_str = ", ".join(focus_areas) if focus_areas else "all areas"

        system_prompt = """ROLE: Senior Control Plane Quality Engineer & Principal ASDL Testing Architect.

You are an autonomous testing agent integrated into the OpenShift/Kubernetes Control Plane QE engineering pipeline. Your objective is to eliminate manual test-planning overhead by analyzing architectural enhancements and auto-generating structured, highly technical test plans.

AGENT TASK FLOW:
1. Parse the input document to identify structural API changes, state-machine transitions, configuration variables, and behavioral side-effects.
2. Cross-reference changes against Control Plane reliability criteria (Upgrade paths, cluster-operator availability, regression risks).
3. Brainstorm at least 15 edge cases, including:
   - Network partitions or API server timeouts during operations.
   - Corrupted/Invalid configuration states (e.g., bad container images, wrong fields).
   - Race conditions or resource contention between parallel controller loops.

OUTPUT FORMAT (strict Markdown):

# Test Plan: [Feature Name / PR Title]

## 1. Executive Summary & Feature Scope
- **Core Functionality Analyzed:** [Brief description of what changes]
- **Target Components:** [e.g., cluster-kube-apiserver-operator, library-go utilities]

## 2. Test Matrix & Coverage Targets (Aiming for ≥80% baseline scenario map)
### A. Functional Scenarios
- [Scenario Name] -> [Pre-conditions] -> [Action] -> [Expected Result]
### B. Negative & Edge-Case Scenarios (Minimum 15 detailed bullets)
- [Edge Case ID] -> [Fault Injection Strategy] -> [Expected Operator Remediation]
### C. Regression & Upgrade Compatibility Targets
- [Scenario] -> [Impact on existing API fields and runtime workloads]

## 3. Acceptance & Verification Criteria
- Explicit validation statements for cluster operator `Available=True`, `Progressing=False`, and `Degraded=False` states.

CRITICAL CONSTRAINT: Do not generate vague or high-level goals. All test scenarios must be immediately actionable by a technical QE engineer."""

        prompt = f"""Generate a comprehensive test plan for the following enhancement:

Feature Name: {feature_name or 'Extracted from document'}
Target Components: {target_components or 'Auto-detect from document'}
Focus Areas: {focus_str}

--- INPUT DOCUMENT ---
{input_context[:12000]}
--- END DOCUMENT ---

Generate the full test plan following the exact markdown template structure."""

        config = get_config()
        result = generate(prompt, system=system_prompt, max_tokens=8192, temperature=0.3)

        if result:
            return jsonify({
                'status': 'success',
                'test_plan': result,
                'model': config['model'],
                'mode': config['mode']
            })
        return jsonify({'status': 'error', 'error': 'LLM returned no response. Try switching model.'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/regression-test-agent')
def regression_test_agent():
    """Regression Test Agent - generates regression tests from Jira bugs."""
    return render_template('regression_test_agent.html')


@app.route('/api/generate-regression-tests', methods=['POST'])
def api_generate_regression_tests():
    """Generate regression test cases from Jira bug data using LLM."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config

        if not is_available():
            return jsonify({'status': 'error', 'error': 'LLM not available. Check Settings.'}), 500

        data = request.json
        jira_id = data.get('jira_id', '').strip()
        bug_title = data.get('bug_title', '').strip()
        description = data.get('description', '').strip()
        reproduce_steps = data.get('reproduce_steps', '').strip()
        root_cause = data.get('root_cause', '').strip()
        fix_details = data.get('fix_details', '').strip()
        component = data.get('component', '').strip()
        linked_test_plan = data.get('linked_test_plan', '').strip()
        output_format = data.get('output_format', 'yaml')

        if not description and not bug_title:
            return jsonify({'status': 'error', 'error': 'Provide at least bug title or description'}), 400

        system_prompt = """ROLE: Automated Regression Test Engineer & Jira-to-Test Integration Agent.

CONTEXT: You are a specialized quality assurance agent tasked with ensuring closed bugs never manifest again. You ingest root-cause analyses from issue trackers and map them directly into granular, reproducible regression test cases.

AGENT TASK FLOW:
1. Analyze how the system broke. Extract exact preconditions, environmental constraints, and user payloads that triggered the bug.
2. Look for gaps: Identify exactly why the original test plan missed this path, and synthesize 3 adjacent scenarios likely to suffer from similar regressions.
3. Map the bug steps into standard BDD format.

OUTPUT FORMAT (YAML for test management systems):

---
test_case_meta:
  jira_ticket: "[JIRA_BUG_ID]"
  priority: "P0/P1 Regression"
  component: "[Component Name]"
  created_by: "Regression Test Agent"

test_case_definition:
  title: "Regression: Verify [Summary of Bug Fix]"
  preconditions:
    - [State of cluster operators, CRDs, or nodes required]
  
  steps:
    - step_number: 1
      action: "Setup initial conditions matching bug report: [Details]"
      expected_result: "Environment matches exact pre-failure state smoothly."
    - step_number: 2
      action: "Execute the triggering action / fault injection: [Steps]"
      expected_result: "System blocks error or handles gracefully. Fix validation succeeds."
    - step_number: 3
      action: "Verify post-fix behavior and operator health"
      expected_result: "Cluster operators report Available=True, Degraded=False"
      
  boundary_and_adjacent_scenarios:
    - "Adjacent Check 1: [Scenario mapping nearby code branches]"
    - "Adjacent Check 2: [Negative input limits]"
    - "Adjacent Check 3: [Scale/Stress version of identical action]"

  gap_analysis:
    why_missed: "[Explain why the original test plan missed this path]"
    coverage_improvement: "[What new test coverage this adds]"
---

Generate MULTIPLE test cases (at least 3) covering:
1. The exact regression scenario from the bug
2. Adjacent boundary scenarios that could fail similarly
3. A stress/scale variant of the same failure path

CRITICAL: All steps must be immediately executable by a QE engineer. No vague instructions."""

        bug_context = f"""Jira Bug ID: {jira_id or 'N/A'}
Title: {bug_title or 'N/A'}
Component: {component or 'Control Plane Operator'}

Description:
{description or 'Not provided'}

Steps to Reproduce:
{reproduce_steps or 'Not provided'}

Root Cause Analysis:
{root_cause or 'Not provided'}

Fix Details:
{fix_details or 'Not provided'}"""

        if linked_test_plan:
            bug_context += f"\n\nLinked Test Plan Context:\n{linked_test_plan[:3000]}"

        prompt = f"""Generate comprehensive regression test cases for the following bug:

{bug_context}

Generate the regression test cases in YAML format following the exact template structure. Include at least 3 test cases covering the exact regression, adjacent scenarios, and stress variants."""

        config = get_config()
        result = generate(prompt, system=system_prompt, max_tokens=8192, temperature=0.2)

        if result:
            return jsonify({
                'status': 'success',
                'regression_tests': result,
                'model': config['model'],
                'mode': config['mode'],
                'jira_id': jira_id
            })
        return jsonify({'status': 'error', 'error': 'LLM returned no response. Try switching model.'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/generate-regression-from-jira', methods=['POST'])
def api_generate_regression_from_jira():
    """Fetch Jira bug and auto-generate regression tests."""
    try:
        from workshop_mcp_server.src.tools.llm_provider import generate, is_available, get_config

        if not JIRA_AVAILABLE:
            return jsonify({'status': 'error', 'error': 'Jira tools not available'}), 500
        if not is_available():
            return jsonify({'status': 'error', 'error': 'LLM not available. Check Settings.'}), 500

        data = request.json
        jira_id = data.get('jira_id', '').strip()
        base_url = data.get('base_url', '').strip() or None
        username = data.get('username', '').strip() or None
        api_token = data.get('api_token', '').strip() or None
        password = data.get('password', '').strip() or None

        if not jira_id:
            return jsonify({'status': 'error', 'error': 'Jira Issue ID is required'}), 400

        # Fetch the bug from Jira
        issue_result = get_issue(jira_id, base_url=base_url, username=username, api_token=api_token, password=password)
        if issue_result.get('status') == 'error':
            return jsonify(issue_result), 400

        issue = issue_result['issue']

        # Forward to the regression test generator
        regression_data = {
            'jira_id': jira_id,
            'bug_title': issue.get('summary', ''),
            'description': issue.get('description', ''),
            'reproduce_steps': issue.get('description', ''),
            'root_cause': '',
            'fix_details': '',
            'component': issue.get('components', ['Control Plane'])[0] if issue.get('components') else 'Control Plane',
        }

        # Call the generation logic directly
        from workshop_mcp_server.src.tools.llm_provider import generate as llm_generate, get_config

        system_prompt = """ROLE: Automated Regression Test Engineer & Jira-to-Test Integration Agent.

You are a specialized quality assurance agent. Analyze the Jira bug and generate regression test cases in YAML format.

Generate at least 3 test cases:
1. Exact regression scenario from the bug
2. Adjacent boundary scenarios
3. Stress/scale variant

Output YAML format with test_case_meta, test_case_definition (title, preconditions, steps, boundary_and_adjacent_scenarios, gap_analysis)."""

        prompt = f"""Generate regression test cases for:

Jira: {jira_id}
Title: {issue.get('summary', '')}
Type: {issue.get('issue_type', '')}
Status: {issue.get('status', '')}
Priority: {issue.get('priority', '')}
Component: {regression_data['component']}

Description:
{issue.get('description', 'No description')[:5000]}

Generate comprehensive regression tests in YAML format."""

        config = get_config()
        result = llm_generate(prompt, system=system_prompt, max_tokens=8192, temperature=0.2)

        if result:
            return jsonify({
                'status': 'success',
                'regression_tests': result,
                'model': config['model'],
                'mode': config['mode'],
                'jira_id': jira_id,
                'issue_summary': issue.get('summary', '')
            })
        return jsonify({'status': 'error', 'error': 'LLM returned no response'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
