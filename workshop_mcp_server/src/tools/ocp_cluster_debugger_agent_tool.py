"""OpenShift Cluster Debugger + Test Automation Agent.

Advanced AI agent for debugging OpenShift/Kubernetes clusters and generating test automation.
"""

import subprocess
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


class OCPClusterDebuggerAgent:
    """OpenShift Cluster Debugger and Test Automation AI Agent."""

    def __init__(self):
        self.oc_path = "oc"
        self.kubeconfig_path = None
        self.validation_results = {}
        self.diagnostic_data = {}

    def debug_cluster_issue(
        self,
        issue_description: str,
        namespace: Optional[str] = None,
        component: Optional[str] = None,
        oc_path: Optional[str] = None,
        kubeconfig_path: Optional[str] = None,
        include_test_case: bool = True,
    ) -> Dict[str, Any]:
        """Debug OpenShift cluster issue and optionally generate test case.

        TOOL_NAME=debug_cluster_issue
        DISPLAY_NAME=OpenShift Cluster Debugger Agent
        USECASE=Debug cluster issues and generate test automation cases
        INSTRUCTIONS=1. Describe the issue, 2. Optionally specify namespace/component, 3. Get diagnosis, fix recommendations, and test cases
        INPUT_DESCRIPTION=issue_description (str): Description of the cluster issue, namespace (str, optional): Target namespace, component (str, optional): Component name (pod/operator/node), oc_path (str, optional): Path to oc binary, kubeconfig_path (str, optional): Path to kubeconfig, include_test_case (bool): Generate test automation code
        OUTPUT_DESCRIPTION=Dictionary with diagnostic summary, test case code, fix recommendations, and validation results
        EXAMPLES=debug_cluster_issue("API server not responding"), debug_cluster_issue("Pod crash loop", namespace="openshift-etcd", component="etcd-master-0")
        PREREQUISITES=oc CLI access to cluster
        RELATED_TOOLS=analyze_mustgather_bundle, execute_ocp_test_step_by_step

        Args:
            issue_description: Description of the cluster issue
            namespace: Target namespace (optional)
            component: Component name - pod, operator, node, etc. (optional)
            oc_path: Path to oc binary (optional)
            kubeconfig_path: Path to kubeconfig file (optional)
            include_test_case: Whether to generate test automation code

        Returns:
            Dictionary with diagnostic summary, test case, and recommendations
        """
        try:
            logger.info(f"Starting cluster debug for issue: {issue_description}")

            if oc_path:
                self.oc_path = oc_path
            if kubeconfig_path:
                self.kubeconfig_path = kubeconfig_path

            # Try LLM-powered debugging first for enhanced analysis
            try:
                from workshop_mcp_server.src.tools.llm_provider import debug_cluster_issue as llm_debug, is_available
                if is_available():
                    llm_result = llm_debug(
                        issue=issue_description,
                        namespace=namespace or "",
                        component=component or "",
                    )
                    if llm_result:
                        logger.info("LLM-enhanced cluster debug completed")
                        return {
                            "status": "success",
                            "mode": "llm",
                            "issue_description": issue_description,
                            "llm_analysis": llm_result,
                            "message": "AI-powered cluster debugging (llama3)",
                            "timestamp": datetime.now().isoformat(),
                        }
            except Exception as llm_err:
                logger.warning(f"LLM debug unavailable, using built-in analysis: {llm_err}")

            # Validate inputs
            validation = self._validate_inputs(namespace, component)

            # Analyze the issue description
            issue_analysis = self._analyze_issue_description(issue_description)

            # Run diagnostics based on issue type
            diagnostics = self._run_diagnostics(
                issue_analysis, namespace, component
            )

            # Generate fix recommendations
            fix_recommendations = self._generate_fix_recommendations(
                issue_analysis, diagnostics
            )

            # Generate test case if requested
            test_case = None
            if include_test_case:
                test_case = self._generate_test_case(
                    issue_description, issue_analysis, namespace, component
                )

            # Build comprehensive response
            result = {
                "status": "success",
                "issue_description": issue_description,
                "diagnostic_summary": diagnostics.get("summary", ""),
                "issue_analysis": issue_analysis,
                "validation_results": validation,
                "diagnostics": diagnostics,
                "fix_recommendations": fix_recommendations,
                "test_case": test_case,
                "suggested_commands": self._get_suggested_commands(
                    issue_analysis, namespace, component
                ),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info("Cluster debug completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error debugging cluster issue: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issue_description": issue_description,
                "timestamp": datetime.now().isoformat(),
            }

    def _validate_inputs(
        self, namespace: Optional[str], component: Optional[str]
    ) -> Dict[str, Any]:
        """Validate user inputs before running diagnostics."""
        validation = {
            "oc_cli_available": False,
            "cluster_accessible": False,
            "namespace_exists": None,
            "component_exists": None,
        }

        try:
            # Check oc CLI availability
            result = self._run_command(f"{self.oc_path} version --client")
            validation["oc_cli_available"] = result["exit_code"] == 0

            if not validation["oc_cli_available"]:
                return validation

            # Check cluster access
            result = self._run_command(f"{self.oc_path} whoami")
            validation["cluster_accessible"] = result["exit_code"] == 0

            if not validation["cluster_accessible"]:
                return validation

            # Validate namespace if provided
            if namespace:
                result = self._run_command(f"{self.oc_path} get namespace {namespace}")
                validation["namespace_exists"] = result["exit_code"] == 0

            # Validate component if provided
            if component and namespace:
                # Try to find component as pod, deployment, or other resource
                result = self._run_command(
                    f"{self.oc_path} get pod {component} -n {namespace}"
                )
                if result["exit_code"] == 0:
                    validation["component_exists"] = True
                    validation["component_type"] = "pod"
                else:
                    # Try as deployment
                    result = self._run_command(
                        f"{self.oc_path} get deployment {component} -n {namespace}"
                    )
                    if result["exit_code"] == 0:
                        validation["component_exists"] = True
                        validation["component_type"] = "deployment"
                    else:
                        validation["component_exists"] = False

        except Exception as e:
            logger.error(f"Error validating inputs: {e}")
            validation["validation_error"] = str(e)

        return validation

    def _analyze_issue_description(self, issue_description: str) -> Dict[str, Any]:
        """Analyze issue description to identify issue type and affected components."""
        issue_lower = issue_description.lower()

        analysis = {
            "issue_type": "unknown",
            "affected_components": [],
            "severity": "medium",
            "keywords": [],
        }

        # Identify issue type
        if any(
            word in issue_lower
            for word in ["not responding", "unavailable", "down", "timeout"]
        ):
            analysis["issue_type"] = "availability"
            analysis["severity"] = "critical"

        elif any(
            word in issue_lower
            for word in ["crash", "crashloop", "restarting", "oomkilled"]
        ):
            analysis["issue_type"] = "pod_crash"
            analysis["severity"] = "critical"

        elif any(
            word in issue_lower for word in ["degraded", "progressing", "unavailable"]
        ):
            analysis["issue_type"] = "operator_degraded"
            analysis["severity"] = "high"

        elif any(word in issue_lower for word in ["notready", "not ready", "offline"]):
            analysis["issue_type"] = "node_issue"
            analysis["severity"] = "critical"

        elif any(
            word in issue_lower
            for word in ["network", "connection", "dns", "route", "ingress"]
        ):
            analysis["issue_type"] = "networking"
            analysis["severity"] = "high"

        elif any(
            word in issue_lower
            for word in ["storage", "volume", "pvc", "pv", "disk"]
        ):
            analysis["issue_type"] = "storage"
            analysis["severity"] = "high"

        elif any(word in issue_lower for word in ["upgrade", "update", "version"]):
            analysis["issue_type"] = "upgrade"
            analysis["severity"] = "medium"

        elif any(
            word in issue_lower for word in ["performance", "slow", "latency", "memory"]
        ):
            analysis["issue_type"] = "performance"
            analysis["severity"] = "medium"

        # Identify affected components
        components = {
            "api": ["api", "apiserver", "kube-apiserver"],
            "etcd": ["etcd"],
            "operator": ["operator", "cvo", "cluster-version"],
            "node": ["node", "worker", "master", "control plane"],
            "network": ["sdn", "ovn", "network", "dns", "route"],
            "storage": ["storage", "csi", "volume", "pvc"],
            "authentication": ["auth", "oauth", "authentication"],
            "monitoring": ["monitoring", "prometheus", "alertmanager"],
            "registry": ["registry", "image"],
        }

        for comp_name, keywords in components.items():
            if any(keyword in issue_lower for keyword in keywords):
                analysis["affected_components"].append(comp_name)
                analysis["keywords"].extend(
                    [kw for kw in keywords if kw in issue_lower]
                )

        return analysis

    def _run_diagnostics(
        self,
        issue_analysis: Dict[str, Any],
        namespace: Optional[str],
        component: Optional[str],
    ) -> Dict[str, Any]:
        """Run diagnostics based on issue analysis."""
        diagnostics = {
            "checks_performed": [],
            "findings": [],
            "summary": "",
            "raw_output": {},
        }

        issue_type = issue_analysis["issue_type"]
        affected_components = issue_analysis["affected_components"]

        try:
            # Always check cluster operators
            co_check = self._check_cluster_operators()
            diagnostics["checks_performed"].append("cluster_operators")
            diagnostics["raw_output"]["cluster_operators"] = co_check
            if co_check.get("degraded_operators"):
                diagnostics["findings"].append(
                    {
                        "severity": "critical",
                        "finding": f"Degraded operators: {', '.join(co_check['degraded_operators'])}",
                    }
                )

            # Check nodes
            if issue_type in ["node_issue", "availability"] or "node" in affected_components:
                node_check = self._check_nodes()
                diagnostics["checks_performed"].append("nodes")
                diagnostics["raw_output"]["nodes"] = node_check
                if node_check.get("notready_nodes"):
                    diagnostics["findings"].append(
                        {
                            "severity": "critical",
                            "finding": f"NotReady nodes: {', '.join(node_check['notready_nodes'])}",
                        }
                    )

            # Check specific component if provided
            if component and namespace:
                comp_check = self._check_component_detailed(namespace, component)
                diagnostics["checks_performed"].append(f"component_{component}")
                diagnostics["raw_output"][f"component_{component}"] = comp_check

                if comp_check.get("status") != "Running":
                    diagnostics["findings"].append({
                        "severity": "critical",
                        "finding": f"Component {component} status: {comp_check.get('status', 'Unknown')}",
                    })

                # Add log findings
                if comp_check.get("log_errors"):
                    for log_error in comp_check["log_errors"][:5]:
                        diagnostics["findings"].append({
                            "severity": "critical",
                            "finding": f"{component} Log: {log_error}"
                        })

                if comp_check.get("restart_count", 0) > 5:
                    diagnostics["findings"].append({
                        "severity": "high",
                        "finding": f"{component} has restarted {comp_check['restart_count']} times"
                    })

            # Check API server if relevant
            if "api" in affected_components or issue_type == "availability":
                api_check = self._check_api_server()
                diagnostics["checks_performed"].append("api_server")
                diagnostics["raw_output"]["api_server"] = api_check

                # Add findings from API server analysis
                if api_check.get("pod_issues"):
                    for issue in api_check["pod_issues"]:
                        diagnostics["findings"].append({
                            "severity": "critical",
                            "finding": f"API Server: {issue}"
                        })

                if api_check.get("log_errors"):
                    for log_error in api_check["log_errors"][:5]:  # Top 5
                        diagnostics["findings"].append({
                            "severity": "critical",
                            "finding": f"API Server Log: {log_error}"
                        })

            # Check etcd if relevant
            if "etcd" in affected_components or "api" in affected_components:
                etcd_check = self._check_etcd()
                diagnostics["checks_performed"].append("etcd")
                diagnostics["raw_output"]["etcd"] = etcd_check

                # Add findings from etcd analysis
                if etcd_check.get("pod_issues"):
                    for issue in etcd_check["pod_issues"]:
                        diagnostics["findings"].append({
                            "severity": "critical",
                            "finding": f"etcd: {issue}"
                        })

                if etcd_check.get("log_errors"):
                    for log_error in etcd_check["log_errors"][:5]:  # Top 5
                        diagnostics["findings"].append({
                            "severity": "high",
                            "finding": f"etcd Log: {log_error}"
                        })

            # Check events
            events_check = self._check_recent_events(namespace)
            diagnostics["checks_performed"].append("events")
            diagnostics["raw_output"]["events"] = events_check

            # Generate summary
            diagnostics["summary"] = self._generate_diagnostic_summary(diagnostics)

        except Exception as e:
            logger.error(f"Error running diagnostics: {e}")
            diagnostics["error"] = str(e)

        return diagnostics

    def _check_cluster_operators(self) -> Dict[str, Any]:
        """Check cluster operator status."""
        result = self._run_command(f"{self.oc_path} get co -o json")

        if result["exit_code"] != 0:
            return {"error": "Failed to get cluster operators"}

        try:
            co_data = json.loads(result["stdout"])
            operators = co_data.get("items", [])

            degraded_operators = []
            unavailable_operators = []
            progressing_operators = []

            for op in operators:
                name = op.get("metadata", {}).get("name", "unknown")
                conditions = op.get("status", {}).get("conditions", [])

                for condition in conditions:
                    if condition.get("type") == "Degraded" and condition.get("status") == "True":
                        degraded_operators.append(name)
                    elif condition.get("type") == "Available" and condition.get("status") == "False":
                        unavailable_operators.append(name)
                    elif condition.get("type") == "Progressing" and condition.get("status") == "True":
                        progressing_operators.append(name)

            return {
                "total_operators": len(operators),
                "degraded_operators": degraded_operators,
                "unavailable_operators": unavailable_operators,
                "progressing_operators": progressing_operators,
            }

        except Exception as e:
            return {"error": f"Failed to parse cluster operators: {e}"}

    def _check_nodes(self) -> Dict[str, Any]:
        """Check node status."""
        result = self._run_command(f"{self.oc_path} get nodes -o json")

        if result["exit_code"] != 0:
            return {"error": "Failed to get nodes"}

        try:
            nodes_data = json.loads(result["stdout"])
            nodes = nodes_data.get("items", [])

            notready_nodes = []
            total_nodes = len(nodes)

            for node in nodes:
                name = node.get("metadata", {}).get("name", "unknown")
                conditions = node.get("status", {}).get("conditions", [])

                for condition in conditions:
                    if condition.get("type") == "Ready":
                        if condition.get("status") != "True":
                            notready_nodes.append(name)

            return {
                "total_nodes": total_nodes,
                "ready_nodes": total_nodes - len(notready_nodes),
                "notready_nodes": notready_nodes,
            }

        except Exception as e:
            return {"error": f"Failed to parse nodes: {e}"}

    def _check_component(self, namespace: str, component: str) -> Dict[str, Any]:
        """Check specific component (pod, deployment, etc.) - basic check."""
        # Try as pod first
        result = self._run_command(f"{self.oc_path} get pod {component} -n {namespace} -o json")

        if result["exit_code"] == 0:
            try:
                pod_data = json.loads(result["stdout"])
                status = pod_data.get("status", {}).get("phase", "Unknown")
                container_statuses = pod_data.get("status", {}).get("containerStatuses", [])

                restarts = sum(cs.get("restartCount", 0) for cs in container_statuses)

                return {
                    "type": "pod",
                    "name": component,
                    "namespace": namespace,
                    "status": status,
                    "restart_count": restarts,
                }
            except Exception as e:
                return {"error": f"Failed to parse pod: {e}"}

        # Try as deployment
        result = self._run_command(
            f"{self.oc_path} get deployment {component} -n {namespace} -o json"
        )

        if result["exit_code"] == 0:
            try:
                deploy_data = json.loads(result["stdout"])
                replicas = deploy_data.get("status", {}).get("replicas", 0)
                ready_replicas = deploy_data.get("status", {}).get("readyReplicas", 0)

                return {
                    "type": "deployment",
                    "name": component,
                    "namespace": namespace,
                    "replicas": replicas,
                    "ready_replicas": ready_replicas,
                }
            except Exception as e:
                return {"error": f"Failed to parse deployment: {e}"}

        return {"error": f"Component {component} not found"}

    def _check_component_detailed(self, namespace: str, component: str) -> Dict[str, Any]:
        """Check component with detailed log analysis."""
        # Get basic component info
        basic_check = self._check_component(namespace, component)

        if "error" in basic_check:
            return basic_check

        # If it's a pod, get logs and analyze
        if basic_check.get("type") == "pod":
            log_errors = []
            status = basic_check.get("status")

            # Get pod logs (last 100 lines)
            log_result = self._run_command(
                f"{self.oc_path} logs {component} -n {namespace} --tail=100 2>&1"
            )

            if log_result["exit_code"] == 0:
                log_lines = log_result["stdout"].split('\n')

                # Analyze logs for errors, warnings, panics, etc.
                for line in log_lines[-50:]:  # Last 50 lines
                    lower_line = line.lower()
                    if any(err in lower_line for err in ['error', 'fatal', 'panic', 'failed', 'exception', 'crash']):
                        log_errors.append(line.strip()[:200])  # First 200 chars
                    elif any(warn in lower_line for warn in ['warn', 'warning']) and len(log_errors) < 10:
                        log_errors.append(line.strip()[:200])

            # Get pod events
            events_result = self._run_command(
                f"{self.oc_path} get events -n {namespace} --field-selector involvedObject.name={component} --sort-by='.lastTimestamp' | tail -10"
            )

            pod_events = []
            if events_result["exit_code"] == 0:
                event_lines = events_result["stdout"].split('\n')
                for line in event_lines:
                    if any(word in line.lower() for word in ['error', 'failed', 'warning', 'backoff', 'killed']):
                        pod_events.append(line.strip()[:150])

            # Describe pod to get more details
            describe_result = self._run_command(
                f"{self.oc_path} describe pod {component} -n {namespace}"
            )

            container_issues = []
            if describe_result["exit_code"] == 0:
                desc_lines = describe_result["stdout"].split('\n')
                for line in desc_lines:
                    lower_line = line.lower()
                    if any(word in lower_line for word in ['backoff', 'oomkilled', 'imagepullbackoff', 'crashloop']):
                        container_issues.append(line.strip()[:150])

            basic_check["log_errors"] = log_errors[:10]  # Top 10
            basic_check["pod_events"] = pod_events
            basic_check["container_issues"] = container_issues

        return basic_check

    def _check_api_server(self) -> Dict[str, Any]:
        """Check API server health with detailed log analysis."""
        result = self._run_command(
            f"{self.oc_path} get pods -n openshift-kube-apiserver -l app=openshift-kube-apiserver -o json"
        )

        if result["exit_code"] != 0:
            return {"error": "Failed to get API server pods"}

        try:
            pods_data = json.loads(result["stdout"])
            pods = pods_data.get("items", [])

            running_pods = 0
            total_pods = len(pods)
            pod_issues = []
            log_errors = []

            for pod in pods:
                pod_name = pod.get("metadata", {}).get("name", "unknown")
                phase = pod.get("status", {}).get("phase")

                if phase == "Running":
                    running_pods += 1
                else:
                    pod_issues.append(f"{pod_name}: {phase}")

                # Check container statuses
                container_statuses = pod.get("status", {}).get("containerStatuses", [])
                for cs in container_statuses:
                    if cs.get("state", {}).get("waiting"):
                        reason = cs["state"]["waiting"].get("reason", "Unknown")
                        pod_issues.append(f"{pod_name}/{cs.get('name')}: Waiting - {reason}")

                    restart_count = cs.get("restartCount", 0)
                    if restart_count > 5:
                        pod_issues.append(f"{pod_name}/{cs.get('name')}: High restart count ({restart_count})")

                # Get pod logs if not running
                if phase != "Running":
                    log_result = self._run_command(
                        f"{self.oc_path} logs {pod_name} -n openshift-kube-apiserver --tail=50 2>&1"
                    )
                    if log_result["exit_code"] == 0:
                        # Analyze logs for errors
                        log_lines = log_result["stdout"].split('\n')
                        for line in log_lines[-20:]:  # Last 20 lines
                            if any(err in line.lower() for err in ['error', 'fatal', 'panic', 'failed']):
                                log_errors.append(f"{pod_name}: {line.strip()[:150]}")

            return {
                "total_pods": total_pods,
                "running_pods": running_pods,
                "healthy": running_pods == total_pods and total_pods > 0,
                "pod_issues": pod_issues,
                "log_errors": log_errors[:10],  # Limit to 10 most recent
            }

        except Exception as e:
            return {"error": f"Failed to parse API server pods: {e}"}

    def _check_etcd(self) -> Dict[str, Any]:
        """Check etcd health with log analysis."""
        result = self._run_command(
            f"{self.oc_path} get pods -n openshift-etcd -l app=etcd -o json"
        )

        if result["exit_code"] != 0:
            return {"error": "Failed to get etcd pods"}

        try:
            pods_data = json.loads(result["stdout"])
            pods = pods_data.get("items", [])

            running_pods = 0
            total_pods = len(pods)
            pod_issues = []
            log_errors = []

            for pod in pods:
                pod_name = pod.get("metadata", {}).get("name", "unknown")
                phase = pod.get("status", {}).get("phase")

                if phase == "Running":
                    running_pods += 1

                    # Get logs from running etcd pods to check for warnings/errors
                    log_result = self._run_command(
                        f"{self.oc_path} logs {pod_name} -n openshift-etcd -c etcd --tail=100 2>&1"
                    )
                    if log_result["exit_code"] == 0:
                        log_lines = log_result["stdout"].split('\n')
                        for line in log_lines[-50:]:
                            if any(err in line.lower() for err in ['error', 'warn', 'failed', 'timeout']):
                                log_errors.append(f"{pod_name}: {line.strip()[:150]}")
                else:
                    pod_issues.append(f"{pod_name}: {phase}")

                # Check container statuses
                container_statuses = pod.get("status", {}).get("containerStatuses", [])
                for cs in container_statuses:
                    restart_count = cs.get("restartCount", 0)
                    if restart_count > 3:
                        pod_issues.append(f"{pod_name}/etcd: High restart count ({restart_count})")

            return {
                "total_pods": total_pods,
                "running_pods": running_pods,
                "healthy": running_pods == total_pods and total_pods > 0 and len(log_errors) == 0,
                "pod_issues": pod_issues,
                "log_errors": log_errors[:15],  # Limit to 15
            }

        except Exception as e:
            return {"error": f"Failed to parse etcd pods: {e}"}

    def _check_recent_events(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Check recent cluster events."""
        if namespace:
            cmd = f"{self.oc_path} get events -n {namespace} --sort-by='.lastTimestamp' | tail -20"
        else:
            cmd = f"{self.oc_path} get events --all-namespaces --sort-by='.lastTimestamp' | tail -20"

        result = self._run_command(cmd)

        if result["exit_code"] != 0:
            return {"error": "Failed to get events"}

        return {
            "recent_events": result["stdout"],
            "warning_count": result["stdout"].lower().count("warning"),
            "error_count": result["stdout"].lower().count("error"),
        }

    def _generate_diagnostic_summary(self, diagnostics: Dict[str, Any]) -> str:
        """Generate human-readable diagnostic summary with intelligent analysis."""
        findings = diagnostics.get("findings", [])
        raw_output = diagnostics.get("raw_output", {})

        if not findings:
            return "✅ No critical issues detected. All checked components appear healthy.\n\nThe cluster is functioning normally based on the diagnostic checks performed."

        summary_parts = ["DIAGNOSTIC SUMMARY:\n", "=" * 60, "\n"]

        # Analyze the actual issue
        critical_findings = [f for f in findings if f.get("severity") == "critical"]
        high_findings = [f for f in findings if f.get("severity") == "high"]

        # Smart analysis section
        summary_parts.append("ROOT CAUSE ANALYSIS:\n")

        # Check API server issues
        if 'api_server' in raw_output:
            api_data = raw_output['api_server']
            if not api_data.get('healthy', True):
                summary_parts.append(f"🚨 API Server is UNHEALTHY:")
                summary_parts.append(f"   - Running pods: {api_data.get('running_pods', 0)}/{api_data.get('total_pods', 0)}")
                if api_data.get('pod_issues'):
                    summary_parts.append(f"   - Pod issues found: {len(api_data['pod_issues'])}")
                    for issue in api_data['pod_issues'][:3]:
                        summary_parts.append(f"     • {issue}")
                summary_parts.append("")

        # Check etcd issues
        if 'etcd' in raw_output:
            etcd_data = raw_output['etcd']
            if not etcd_data.get('healthy', True):
                summary_parts.append(f"🚨 etcd is UNHEALTHY:")
                summary_parts.append(f"   - Running pods: {etcd_data.get('running_pods', 0)}/{etcd_data.get('total_pods', 0)}")
                if etcd_data.get('pod_issues'):
                    summary_parts.append(f"   - Pod issues found: {len(etcd_data['pod_issues'])}")
                    for issue in etcd_data['pod_issues'][:3]:
                        summary_parts.append(f"     • {issue}")
                summary_parts.append("")
            elif etcd_data.get('log_errors'):
                # etcd is running but has warnings
                summary_parts.append(f"⚠️ etcd is running but showing warnings:")
                summary_parts.append(f"   - etcd connection rejections detected")
                summary_parts.append(f"   - This is usually normal client connection behavior")
                summary_parts.append(f"   - Not the root cause of API server issues")
                summary_parts.append("")

        # Check cluster operators
        if 'cluster_operators' in raw_output:
            co_data = raw_output['cluster_operators']
            if co_data.get('degraded_operators'):
                summary_parts.append(f"🚨 DEGRADED OPERATORS ({len(co_data['degraded_operators'])}):")
                for op in co_data['degraded_operators'][:5]:
                    summary_parts.append(f"   • {op}")
                summary_parts.append("")

            if co_data.get('unavailable_operators'):
                summary_parts.append(f"🚨 UNAVAILABLE OPERATORS ({len(co_data['unavailable_operators'])}):")
                for op in co_data['unavailable_operators'][:5]:
                    summary_parts.append(f"   • {op}")
                summary_parts.append("")

        # Check nodes
        if 'nodes' in raw_output:
            node_data = raw_output['nodes']
            if node_data.get('notready_nodes'):
                summary_parts.append(f"🚨 NOTREADY NODES ({len(node_data['notready_nodes'])}):")
                for node in node_data['notready_nodes']:
                    summary_parts.append(f"   • {node}")
                summary_parts.append("")

        # Display actual critical issues (not just logs)
        if critical_findings:
            critical_non_log = [f for f in critical_findings if 'log' not in f['finding'].lower()]
            if critical_non_log:
                summary_parts.append(f"\n🚨 CRITICAL ISSUES ({len(critical_non_log)}):")
                for finding in critical_non_log[:5]:
                    summary_parts.append(f"  • {finding['finding']}")

        # Display high priority issues (excluding repetitive log warnings)
        if high_findings:
            high_non_repetitive = []
            seen = set()
            for f in high_findings:
                # Deduplicate similar etcd warnings
                if 'rejected connection' in f['finding']:
                    if 'etcd_connection_warning' not in seen:
                        high_non_repetitive.append({'finding': 'etcd: Client connection rejections (normal behavior, not an error)'})
                        seen.add('etcd_connection_warning')
                elif f['finding'] not in seen:
                    high_non_repetitive.append(f)
                    seen.add(f['finding'])

            if high_non_repetitive and len(high_non_repetitive) <= 5:
                summary_parts.append(f"\n⚠️ WARNINGS ({len(high_non_repetitive)}):")
                for finding in high_non_repetitive:
                    summary_parts.append(f"  • {finding['finding']}")

        summary_parts.append(f"\n✅ Diagnostics completed: {', '.join(diagnostics.get('checks_performed', []))}")
        summary_parts.append("=" * 60)

        return "\n".join(summary_parts)

    def _generate_fix_recommendations(
        self, issue_analysis: Dict[str, Any], diagnostics: Dict[str, Any]
    ) -> List[str]:
        """Generate fix recommendations based on diagnostics."""
        recommendations = []

        issue_type = issue_analysis.get("issue_type")
        findings = diagnostics.get("findings", [])

        # Check for degraded operators
        co_data = diagnostics.get("raw_output", {}).get("cluster_operators", {})
        if co_data.get("degraded_operators"):
            for op in co_data["degraded_operators"]:
                recommendations.append(
                    f"oc describe co {op} - Check why operator is degraded"
                )
                recommendations.append(
                    f"oc get pods -n openshift-{op} - Check operator pods"
                )

        # Check for NotReady nodes
        nodes_data = diagnostics.get("raw_output", {}).get("nodes", {})
        if nodes_data.get("notready_nodes"):
            for node in nodes_data["notready_nodes"]:
                recommendations.append(f"oc describe node {node} - Check node conditions")
                recommendations.append(
                    f"oc debug node/{node} -- chroot /host journalctl -u kubelet -n 100"
                )

        # Issue type specific recommendations
        if issue_type == "pod_crash":
            recommendations.extend(
                [
                    "Check pod logs for error messages",
                    "Review pod resource limits and requests",
                    "Check for OOMKilled events",
                    "Verify image pull secrets",
                ]
            )
        elif issue_type == "networking":
            recommendations.extend(
                [
                    "oc get co network - Check SDN/OVN operator",
                    "oc get pods -n openshift-sdn -o wide - Check SDN pods",
                    "oc get pods -n openshift-dns - Check DNS pods",
                ]
            )
        elif issue_type == "storage":
            recommendations.extend(
                [
                    "oc get pv,pvc --all-namespaces - Check volumes",
                    "oc get storageclass - Verify storage classes",
                    "Check CSI driver logs",
                ]
            )

        # Default recommendations
        if not recommendations:
            recommendations = [
                "oc get co - Check all cluster operators",
                "oc get nodes - Verify node status",
                "oc get events --all-namespaces --sort-by='.lastTimestamp' | tail -50",
                "oc adm top nodes - Check resource usage",
            ]

        return recommendations

    def _generate_test_case(
        self,
        issue_description: str,
        issue_analysis: Dict[str, Any],
        namespace: Optional[str],
        component: Optional[str],
    ) -> Dict[str, str]:
        """Generate test automation code based on issue."""
        issue_type = issue_analysis.get("issue_type")

        test_case = {
            "format": "go",
            "description": f"Test case to validate: {issue_description}",
            "code": "",
        }

        if issue_type == "pod_crash":
            test_case["code"] = self._generate_pod_crash_test(namespace, component)
        elif issue_type == "operator_degraded":
            test_case["code"] = self._generate_operator_health_test(component)
        elif issue_type == "node_issue":
            test_case["code"] = self._generate_node_health_test()
        elif issue_type == "networking":
            test_case["code"] = self._generate_network_test(namespace)
        elif issue_type == "storage":
            test_case["code"] = self._generate_storage_test(namespace)
        else:
            test_case["code"] = self._generate_generic_test(issue_description, namespace, component)

        # Also provide shell script version
        test_case["shell_script"] = self._generate_shell_test_script(
            issue_type, namespace, component
        )

        return test_case

    def _generate_pod_crash_test(
        self, namespace: Optional[str], component: Optional[str]
    ) -> str:
        """Generate Go test for pod crash scenario."""
        ns = namespace or "test"
        pod_name = component or "test-pod"

        return f'''package e2e

import (
    "context"
    "testing"
    "time"

    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/kubernetes"
)

// TestPodStability validates that pod does not crash repeatedly
func TestPodStability(t *testing.T) {{
    clientset := getClientset(t)

    namespace := "{ns}"
    podName := "{pod_name}"

    // Get initial restart count
    pod, err := clientset.CoreV1().Pods(namespace).Get(context.TODO(), podName, metav1.GetOptions{{}})
    if err != nil {{
        t.Fatalf("Failed to get pod: %v", err)
    }}

    initialRestarts := getRestartCount(pod)

    // Wait 5 minutes and check again
    time.Sleep(5 * time.Minute)

    pod, err = clientset.CoreV1().Pods(namespace).Get(context.TODO(), podName, metav1.GetOptions{{}})
    if err != nil {{
        t.Fatalf("Failed to get pod after wait: %v", err)
    }}

    finalRestarts := getRestartCount(pod)

    if finalRestarts > initialRestarts {{
        t.Fatalf("Pod restarted %d times during test period", finalRestarts-initialRestarts)
    }}

    if pod.Status.Phase != "Running" {{
        t.Fatalf("Pod is not running: %s", pod.Status.Phase)
    }}

    t.Logf("Pod is stable with %d total restarts", finalRestarts)
}}

func getRestartCount(pod *v1.Pod) int {{
    count := 0
    for _, cs := range pod.Status.ContainerStatuses {{
        count += int(cs.RestartCount)
    }}
    return count
}}
'''

    def _generate_operator_health_test(self, operator: Optional[str]) -> str:
        """Generate Go test for operator health."""
        op = operator or "cluster-version-operator"

        return f'''package e2e

import (
    "context"
    "testing"

    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    configv1 "github.com/openshift/api/config/v1"
)

// TestOperatorHealth validates operator is available and not degraded
func TestOperatorHealth(t *testing.T) {{
    configClient := getConfigClient(t)

    operatorName := "{op}"

    co, err := configClient.ConfigV1().ClusterOperators().Get(context.TODO(), operatorName, metav1.GetOptions{{}})
    if err != nil {{
        t.Fatalf("Failed to get cluster operator: %v", err)
    }}

    isAvailable := false
    isDegraded := false
    isProgressing := false

    for _, condition := range co.Status.Conditions {{
        switch condition.Type {{
        case configv1.OperatorAvailable:
            isAvailable = condition.Status == configv1.ConditionTrue
        case configv1.OperatorDegraded:
            isDegraded = condition.Status == configv1.ConditionTrue
        case configv1.OperatorProgressing:
            isProgressing = condition.Status == configv1.ConditionTrue
        }}
    }}

    if !isAvailable {{
        t.Fatalf("Operator %s is not available", operatorName)
    }}

    if isDegraded {{
        t.Fatalf("Operator %s is degraded", operatorName)
    }}

    t.Logf("Operator %s is healthy (Available: %v, Degraded: %v, Progressing: %v)",
        operatorName, isAvailable, isDegraded, isProgressing)
}}
'''

    def _generate_node_health_test(self) -> str:
        """Generate Go test for node health."""
        return '''package e2e

import (
    "context"
    "testing"

    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    corev1 "k8s.io/api/core/v1"
)

// TestNodeHealth validates all nodes are ready
func TestNodeHealth(t *testing.T) {
    clientset := getClientset(t)

    nodes, err := clientset.CoreV1().Nodes().List(context.TODO(), metav1.ListOptions{})
    if err != nil {
        t.Fatalf("Failed to list nodes: %v", err)
    }

    if len(nodes.Items) == 0 {
        t.Fatal("No nodes found in cluster")
    }

    notReadyNodes := []string{}

    for _, node := range nodes.Items {
        isReady := false

        for _, condition := range node.Status.Conditions {
            if condition.Type == corev1.NodeReady {
                isReady = condition.Status == corev1.ConditionTrue
                break
            }
        }

        if !isReady {
            notReadyNodes = append(notReadyNodes, node.Name)
        }
    }

    if len(notReadyNodes) > 0 {
        t.Fatalf("Found %d NotReady nodes: %v", len(notReadyNodes), notReadyNodes)
    }

    t.Logf("All %d nodes are Ready", len(nodes.Items))
}
'''

    def _generate_network_test(self, namespace: Optional[str]) -> str:
        """Generate network connectivity test."""
        ns = namespace or "test"

        return f'''package e2e

import (
    "context"
    "testing"
    "time"

    corev1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// TestNetworkConnectivity validates pod-to-pod network connectivity
func TestNetworkConnectivity(t *testing.T) {{
    clientset := getClientset(t)

    namespace := "{ns}"

    // Create test pod
    pod := &corev1.Pod{{
        ObjectMeta: metav1.ObjectMeta{{
            Name: "network-test-pod",
            Namespace: namespace,
        }},
        Spec: corev1.PodSpec{{
            Containers: []corev1.Container{{
                {{
                    Name: "test",
                    Image: "registry.access.redhat.com/ubi8/ubi-minimal",
                    Command: []string{{"sh", "-c", "sleep 3600"}},
                }},
            }},
        }},
    }}

    _, err := clientset.CoreV1().Pods(namespace).Create(context.TODO(), pod, metav1.CreateOptions{{}})
    if err != nil {{
        t.Fatalf("Failed to create test pod: %v", err)
    }}

    defer clientset.CoreV1().Pods(namespace).Delete(context.TODO(), pod.Name, metav1.DeleteOptions{{}})

    // Wait for pod to be ready
    time.Sleep(30 * time.Second)

    // Test DNS resolution
    output, err := execInPod(clientset, namespace, pod.Name, []string{{"nslookup", "kubernetes.default"}})
    if err != nil {{
        t.Fatalf("DNS resolution failed: %v", err)
    }}

    t.Logf("DNS resolution successful: %s", output)
}}
'''

    def _generate_storage_test(self, namespace: Optional[str]) -> str:
        """Generate storage/PVC test."""
        ns = namespace or "test"

        return f'''package e2e

import (
    "context"
    "testing"
    "time"

    corev1 "k8s.io/api/core/v1"
    "k8s.io/apimachinery/pkg/api/resource"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// TestStorageProvisioning validates PVC can be created and bound
func TestStorageProvisioning(t *testing.T) {{
    clientset := getClientset(t)

    namespace := "{ns}"

    // Create PVC
    pvc := &corev1.PersistentVolumeClaim{{
        ObjectMeta: metav1.ObjectMeta{{
            Name: "test-pvc",
            Namespace: namespace,
        }},
        Spec: corev1.PersistentVolumeClaimSpec{{
            AccessModes: []corev1.PersistentVolumeAccessMode{{corev1.ReadWriteOnce}},
            Resources: corev1.ResourceRequirements{{
                Requests: corev1.ResourceList{{
                    corev1.ResourceStorage: resource.MustParse("1Gi"),
                }},
            }},
        }},
    }}

    _, err := clientset.CoreV1().PersistentVolumeClaims(namespace).Create(context.TODO(), pvc, metav1.CreateOptions{{}})
    if err != nil {{
        t.Fatalf("Failed to create PVC: %v", err)
    }}

    defer clientset.CoreV1().PersistentVolumeClaims(namespace).Delete(context.TODO(), pvc.Name, metav1.DeleteOptions{{}})

    // Wait for PVC to be bound
    timeout := time.After(2 * time.Minute)
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()

    for {{
        select {{
        case <-timeout:
            t.Fatal("PVC did not bind within timeout")
        case <-ticker.C:
            pvc, err := clientset.CoreV1().PersistentVolumeClaims(namespace).Get(context.TODO(), pvc.Name, metav1.GetOptions{{}})
            if err != nil {{
                t.Fatalf("Failed to get PVC: %v", err)
            }}

            if pvc.Status.Phase == corev1.ClaimBound {{
                t.Logf("PVC successfully bound to PV: %s", pvc.Spec.VolumeName)
                return
            }}
        }}
    }}
}}
'''

    def _generate_generic_test(
        self, issue_description: str, namespace: Optional[str], component: Optional[str]
    ) -> str:
        """Generate generic test template."""
        ns = namespace or "test"
        comp = component or "test-component"

        return f'''package e2e

import (
    "context"
    "testing"

    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// TestClusterIssue validates: {issue_description}
func TestClusterIssue(t *testing.T) {{
    clientset := getClientset(t)

    namespace := "{ns}"
    componentName := "{comp}"

    // TODO: Implement test logic for: {issue_description}

    // Example: Get cluster operators
    configClient := getConfigClient(t)
    operators, err := configClient.ConfigV1().ClusterOperators().List(context.TODO(), metav1.ListOptions{{}})
    if err != nil {{
        t.Fatalf("Failed to list cluster operators: %v", err)
    }}

    t.Logf("Found %d cluster operators", len(operators.Items))

    // Add your test validation logic here
}}
'''

    def _generate_shell_test_script(
        self, issue_type: str, namespace: Optional[str], component: Optional[str]
    ) -> str:
        """Generate shell script for testing."""
        ns = namespace or "test"
        comp = component or "test-component"

        script = f'''#!/bin/bash
# OpenShift Test Automation Script
# Issue Type: {issue_type}

set -e

OC="${{OC:-oc}}"
NAMESPACE="{ns}"
COMPONENT="{comp}"

echo "=== Starting OpenShift Test ==="
echo "Namespace: $NAMESPACE"
echo "Component: $COMPONENT"
echo ""

# Check cluster access
echo "Checking cluster access..."
$OC whoami
$OC cluster-info
echo ""

# Check cluster operators
echo "Checking cluster operators..."
$OC get co
echo ""

# Check nodes
echo "Checking node status..."
$OC get nodes
echo ""
'''

        if issue_type == "pod_crash":
            script += f'''
# Monitor pod for crashes
echo "Monitoring pod: $COMPONENT"
INITIAL_RESTARTS=$($OC get pod $COMPONENT -n $NAMESPACE -o jsonpath='{{.status.containerStatuses[0].restartCount}}')
echo "Initial restart count: $INITIAL_RESTARTS"

sleep 300  # Wait 5 minutes

FINAL_RESTARTS=$($OC get pod $COMPONENT -n $NAMESPACE -o jsonpath='{{.status.containerStatuses[0].restartCount}}')
echo "Final restart count: $FINAL_RESTARTS"

if [ "$FINAL_RESTARTS" -gt "$INITIAL_RESTARTS" ]; then
    echo "ERROR: Pod restarted during test!"
    exit 1
fi

echo "✓ Pod is stable"
'''
        elif issue_type == "operator_degraded":
            script += f'''
# Check operator health
echo "Checking operator: $COMPONENT"
$OC get co $COMPONENT -o yaml

AVAILABLE=$($OC get co $COMPONENT -o jsonpath='{{.status.conditions[?(@.type=="Available")].status}}')
DEGRADED=$($OC get co $COMPONENT -o jsonpath='{{.status.conditions[?(@.type=="Degraded")].status}}')

if [ "$AVAILABLE" != "True" ] || [ "$DEGRADED" != "False" ]; then
    echo "ERROR: Operator is not healthy!"
    exit 1
fi

echo "✓ Operator is healthy"
'''
        else:
            script += f'''
# Generic checks
echo "Running generic cluster health checks..."

# Check namespace
$OC get namespace $NAMESPACE || $OC create namespace $NAMESPACE

# Check recent events
echo "Recent events:"
$OC get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -20

echo "✓ Basic checks completed"
'''

        script += '''
echo ""
echo "=== Test Completed Successfully ==="
'''

        return script

    def _get_suggested_commands(
        self, issue_analysis: Dict[str, Any], namespace: Optional[str], component: Optional[str]
    ) -> List[str]:
        """Get suggested oc/kubectl commands for further investigation."""
        commands = []

        issue_type = issue_analysis.get("issue_type")
        affected_components = issue_analysis.get("affected_components", [])

        # Always suggest these
        commands.append("oc get co")
        commands.append("oc get nodes")

        if namespace:
            commands.append(f"oc get pods -n {namespace}")
            commands.append(f"oc get events -n {namespace} --sort-by='.lastTimestamp'")

            if component:
                commands.append(f"oc describe pod {component} -n {namespace}")
                commands.append(f"oc logs {component} -n {namespace}")

        # Issue-specific commands
        if "api" in affected_components:
            commands.append("oc get pods -n openshift-kube-apiserver")

        if "etcd" in affected_components:
            commands.append("oc get pods -n openshift-etcd")
            commands.append(
                "oc logs -n openshift-etcd -l app=etcd -c etcd | tail -100"
            )

        if "network" in affected_components:
            commands.append("oc get co network")
            commands.append("oc get pods -n openshift-sdn")

        return commands

    def _run_command(self, cmd: str) -> Dict[str, Any]:
        """Run shell command and return result."""
        try:
            # Add kubeconfig if specified
            if self.kubeconfig_path and "oc " in cmd:
                cmd = cmd.replace("oc ", f"oc --kubeconfig {self.kubeconfig_path} ")

            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=60
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }

        except subprocess.TimeoutExpired:
            return {"exit_code": -1, "stdout": "", "stderr": "Command timed out"}
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}


# MCP Tool Function
async def debug_openshift_cluster(
    issue_description: str,
    namespace: Optional[str] = None,
    component: Optional[str] = None,
    oc_path: Optional[str] = None,
    kubeconfig_path: Optional[str] = None,
    include_test_case: bool = True,
) -> Dict[str, Any]:
    """Debug OpenShift cluster issue and generate test automation.

    TOOL_NAME=debug_openshift_cluster
    DISPLAY_NAME=OpenShift Cluster Debugger + Test Automation Agent
    USECASE=Debug cluster issues with AI-powered diagnostics and generate test automation code
    INSTRUCTIONS=1. Describe the cluster issue, 2. Optionally specify namespace/component, 3. Get comprehensive diagnostics, fix recommendations, and test code
    INPUT_DESCRIPTION=issue_description (str): Description of the cluster issue, namespace (str, optional): Target namespace, component (str, optional): Component name, oc_path (str, optional): Path to oc binary, kubeconfig_path (str, optional): Path to kubeconfig, include_test_case (bool): Generate test automation
    OUTPUT_DESCRIPTION=Dictionary with diagnostic summary, validation results, fix recommendations, test cases in Go and shell formats
    EXAMPLES=debug_openshift_cluster("API server not responding"), debug_openshift_cluster("Pod crash loop", namespace="openshift-etcd", component="etcd-master-0")
    PREREQUISITES=oc CLI with cluster access
    RELATED_TOOLS=analyze_mustgather_bundle, execute_ocp_test_step_by_step

    Args:
        issue_description: Description of the cluster issue
        namespace: Target namespace (optional)
        component: Component name (optional)
        oc_path: Path to oc binary (optional)
        kubeconfig_path: Path to kubeconfig (optional)
        include_test_case: Whether to generate test automation code

    Returns:
        Comprehensive diagnostic results with test cases
    """
    try:
        logger.info(f"Starting OpenShift cluster debug: {issue_description}")

        agent = OCPClusterDebuggerAgent()

        result = agent.debug_cluster_issue(
            issue_description=issue_description,
            namespace=namespace,
            component=component,
            oc_path=oc_path,
            kubeconfig_path=kubeconfig_path,
            include_test_case=include_test_case,
        )

        logger.info("OpenShift cluster debug completed")
        return result

    except Exception as e:
        logger.error(f"Error in OpenShift cluster debug: {e}")
        return {
            "status": "error",
            "error": str(e),
            "issue_description": issue_description,
            "timestamp": datetime.now().isoformat(),
        }
