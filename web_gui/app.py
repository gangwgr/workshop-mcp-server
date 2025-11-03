"""Web GUI for MCP Server.

A Flask-based web interface for interacting with all MCP server tools.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workshop_mcp_server.src.tools.line_by_line_code_reviewer_tool import review_code_line_by_line
from workshop_mcp_server.src.tools.github_pr_commenter_tool import post_pr_review_comments
from workshop_mcp_server.src.tools.ocp_test_case_generator_tool import generate_ocp_test_case
from workshop_mcp_server.src.tools.ocp_oc_cli_test_generator_tool import generate_oc_cli_test
from workshop_mcp_server.src.tools.ocp_step_by_step_executor_tool import execute_ocp_test_step_by_step
from workshop_mcp_server.src.tools.ocp_test_debugger_tool import debug_ocp_test_failure
from workshop_mcp_server.src.tools.ocp_test_validator_tool import validate_ocp_test_input
from workshop_mcp_server.src.tools.mustgather_analyzer_tool import analyze_mustgather_bundle
from workshop_mcp_server.src.tools.ocp_cluster_debugger_agent_tool import debug_openshift_cluster

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mcp-server-secret-key-change-in-production'

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

        # Try to fetch the actual file content from the PR
        try:
            # Get list of changed files
            files_result = subprocess.run(
                ['gh', 'pr', 'view', pr_number, '-R', f'{owner}/{repo}', '--json', 'files'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if files_result.returncode == 0:
                import json
                pr_data = json.loads(files_result.stdout)
                if pr_data.get('files'):
                    # Get the first changed file
                    first_file = pr_data['files'][0]
                    file_path = first_file['path']

                    # Fetch file content from the PR branch
                    content_result = subprocess.run(
                        ['gh', 'api', f'repos/{owner}/{repo}/pulls/{pr_number}/files'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if content_result.returncode == 0:
                        file_data = json.loads(content_result.stdout)
                        if file_data:
                            # Get patch (changes) from first file
                            files = [{
                                'filename': file_data[0].get('filename', 'unknown'),
                                'content': file_data[0].get('patch', ''),
                                'language': 'auto'
                            }]
        except Exception:
            pass  # Fall back to diff

        return jsonify({'status': 'success', 'files': files})

    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'error': 'Request timed out'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/review-pr', methods=['POST'])
def api_review_pr():
    """API endpoint for PR review."""
    try:
        data = request.json
        pr_url = data.get('pr_url', '')

        # Check if code is provided
        if not data.get('code') or not data['code'].strip():
            return jsonify({
                'status': 'error',
                'error': 'No code provided. Please use the "Fetch PR Files" button or paste code manually.'
            }), 400

        # Review the code
        review_result = review_code_line_by_line(
            code_content=data['code'],
            file_path=data.get('file_path', 'unknown'),
            language=data.get('language', 'go'),
            review_focus=['security', 'performance', 'bugs', 'best-practices', 'maintainability', 'style'],
            severity_threshold='info'
        )

        # Post to GitHub if requested
        if data.get('post_to_github', False) and pr_url:
            post_result = post_pr_review_comments(
                pr_url=pr_url,
                review_results=review_result,
                post_summary=True,
                post_inline_comments=data.get('post_inline', False),
                approve_if_clean=data.get('approve', False)
            )

            return jsonify({
                'status': 'success',
                'review': review_result,
                'post_result': post_result
            })

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

    return "\n".join(context_parts)

def _generate_answer(question, context, analysis):
    """Generate an answer based on the question and analysis context."""
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
