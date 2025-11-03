"""OpenShift Test Debugger tool for the MCP Server.

This tool provides intelligent debugging for failed OpenShift tests, analyzing
failures and providing actionable recommendations to fix issues.
"""

import re
from typing import Any, Dict, List, Optional

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


def debug_ocp_test_failure(
    test_results: Dict[str, Any],
    feature: Optional[str] = None,
    component: Optional[str] = None,
    collect_cluster_info: bool = True,
) -> Dict[str, Any]:
    """Debug OpenShift test failures with intelligent analysis and recommendations.

    TOOL_NAME=debug_ocp_test_failure
    DISPLAY_NAME=OpenShift Test Failure Debugger
    USECASE=Analyze failed OCP tests and provide detailed debugging information with actionable fixes
    INSTRUCTIONS=1. Provide test results from execute_ocp_test_step_by_step, 2. Receive detailed failure analysis with root cause and solutions
    INPUT_DESCRIPTION=test_results (dict): Results from step-by-step execution, feature (str, optional): Feature being tested, component (str, optional): Component name, collect_cluster_info (bool): Collect additional cluster diagnostics
    OUTPUT_DESCRIPTION=Dictionary with failure analysis, root cause, recommended solutions, and debugging commands
    EXAMPLES=debug_ocp_test_failure(test_results), debug_ocp_test_failure(test_results, feature="Pod Deployment", component="pod")
    PREREQUISITES=Test execution results
    RELATED_TOOLS=execute_ocp_test_step_by_step, analyze_ocp_test_results

    This tool provides:
    - Root cause analysis
    - Step-by-step failure breakdown
    - Common error pattern detection
    - Actionable fix recommendations
    - Debugging commands to run
    - Related issues and solutions

    Args:
        test_results: Test execution results (from execute_ocp_test_step_by_step)
        feature: Feature being tested (optional)
        component: Component being tested (optional)
        collect_cluster_info: Whether to collect additional cluster diagnostics

    Returns:
        Dictionary containing detailed debugging information and recommendations

    Raises:
        ValueError: If test_results is invalid
    """
    try:
        # Validate input
        if not test_results or not isinstance(test_results, dict):
            raise ValueError("test_results must be a valid dictionary")

        logger.info("Starting intelligent test failure debugging")

        # Extract execution data
        execution = test_results.get("execution", {})
        if not execution:
            return {
                "status": "error",
                "error": "No execution data found in test results",
                "message": "Cannot debug without execution results",
            }

        # Initialize debugging results
        debug_info = {
            "status": "success",
            "test_status": execution.get("overall_status", "unknown"),
            "feature": feature or execution.get("feature", "unknown"),
            "component": component or execution.get("component", "unknown"),
            "namespace": execution.get("namespace", "unknown"),
            "failure_analysis": {},
            "root_causes": [],
            "recommendations": [],
            "debugging_commands": [],
            "quick_fixes": [],
            "related_issues": [],
        }

        # Analyze failures
        failed_steps = [step for step in execution.get("steps", []) if step.get("status") == "failed"]

        if not failed_steps:
            debug_info["message"] = "No failures detected. Test passed or no execution data available."
            debug_info["recommendations"] = ["Test appears to have passed. No debugging needed."]
            return debug_info

        # Analyze each failed step
        for step in failed_steps:
            step_analysis = _analyze_failed_step(step, execution.get("namespace"))

            debug_info["failure_analysis"][f"Step {step['step_number']}"] = step_analysis
            debug_info["root_causes"].extend(step_analysis.get("root_causes", []))
            debug_info["recommendations"].extend(step_analysis.get("recommendations", []))
            debug_info["debugging_commands"].extend(step_analysis.get("debugging_commands", []))
            debug_info["quick_fixes"].extend(step_analysis.get("quick_fixes", []))

        # Detect common patterns across all failures
        common_patterns = _detect_common_patterns(failed_steps)
        debug_info["common_patterns"] = common_patterns
        debug_info["root_causes"].extend(common_patterns.get("root_causes", []))
        debug_info["recommendations"].extend(common_patterns.get("recommendations", []))

        # Add component-specific debugging
        component_debug = _get_component_specific_debug(
            component or execution.get("component", ""),
            failed_steps,
            execution.get("namespace")
        )
        debug_info["component_specific_debugging"] = component_debug
        debug_info["debugging_commands"].extend(component_debug.get("commands", []))

        # Generate summary
        debug_info["summary"] = _generate_debug_summary(debug_info, failed_steps, execution)

        logger.info("Test failure debugging completed")
        return debug_info

    except Exception as e:
        logger.error(f"Error debugging test failure: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to debug test failure",
        }


def _analyze_failed_step(step: Dict[str, Any], namespace: str) -> Dict[str, Any]:
    """Analyze a single failed step."""
    analysis = {
        "step_name": step.get("name", "unknown"),
        "step_number": step.get("step_number", 0),
        "root_causes": [],
        "recommendations": [],
        "debugging_commands": [],
        "quick_fixes": [],
        "failed_commands": [],
    }

    # Analyze each failed command in the step
    for cmd in step.get("commands", []):
        if cmd.get("status") != "success":
            cmd_analysis = _analyze_failed_command(cmd, step, namespace)

            analysis["failed_commands"].append({
                "description": cmd.get("description", ""),
                "command": cmd.get("command", ""),
                "error": cmd.get("stderr", ""),
                "analysis": cmd_analysis,
            })

            analysis["root_causes"].extend(cmd_analysis.get("root_causes", []))
            analysis["recommendations"].extend(cmd_analysis.get("recommendations", []))
            analysis["debugging_commands"].extend(cmd_analysis.get("debugging_commands", []))
            analysis["quick_fixes"].extend(cmd_analysis.get("quick_fixes", []))

    return analysis


def _analyze_failed_command(cmd: Dict[str, Any], step: Dict[str, Any], namespace: str) -> Dict[str, Any]:
    """Analyze a single failed command."""
    analysis = {
        "root_causes": [],
        "recommendations": [],
        "debugging_commands": [],
        "quick_fixes": [],
    }

    stderr = cmd.get("stderr", "").lower()
    stdout = cmd.get("stdout", "").lower()
    combined_output = stderr + " " + stdout
    command = cmd.get("command", "")

    # Pattern: oc command not found
    if "oc: command not found" in stderr or "oc: not found" in stderr:
        analysis["root_causes"].append("OpenShift CLI (oc) is not installed or not in PATH")
        analysis["recommendations"].append("Install OpenShift CLI: https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/")
        analysis["quick_fixes"].append({
            "description": "Install oc CLI on Linux",
            "commands": [
                "wget https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/openshift-client-linux.tar.gz",
                "tar xvf openshift-client-linux.tar.gz",
                "sudo mv oc /usr/local/bin/",
                "oc version --client"
            ]
        })
        analysis["quick_fixes"].append({
            "description": "Install oc CLI on Mac",
            "commands": [
                "brew install openshift-cli",
                "oc version --client"
            ]
        })

    # Pattern: Not logged in / auth issues
    if any(pattern in combined_output for pattern in ["not logged in", "unauthorized", "authentication required", "login required"]):
        analysis["root_causes"].append("Not logged into OpenShift cluster or authentication failed")
        analysis["recommendations"].append("Login to your OpenShift cluster using: oc login --token=<token> --server=<server>")
        analysis["debugging_commands"].append("oc whoami  # Check current user")
        analysis["debugging_commands"].append("oc cluster-info  # Verify cluster connectivity")
        analysis["quick_fixes"].append({
            "description": "Login to cluster",
            "commands": [
                "oc login --token=<YOUR_TOKEN> --server=<YOUR_SERVER>",
                "oc whoami"
            ]
        })

    # Pattern: Permission denied
    if any(pattern in combined_output for pattern in ["forbidden", "permission denied", "unauthorized", "you must be logged in"]):
        analysis["root_causes"].append("Insufficient permissions to perform the operation")
        analysis["recommendations"].append("Check your user permissions and role bindings")
        analysis["debugging_commands"].append(f"oc auth can-i create namespace  # Check namespace creation permission")
        analysis["debugging_commands"].append(f"oc auth can-i create pods -n {namespace}  # Check pod creation permission")
        analysis["debugging_commands"].append("oc whoami -v  # Show current user and context")
        analysis["quick_fixes"].append({
            "description": "Request cluster-admin access",
            "commands": [
                "oc adm policy add-cluster-role-to-user cluster-admin $(oc whoami)",
            ]
        })

    # Pattern: Namespace already exists
    if "already exists" in combined_output and "namespace" in combined_output:
        analysis["root_causes"].append(f"Namespace '{namespace}' already exists")
        analysis["recommendations"].append(f"Use existing namespace or delete it first: oc delete namespace {namespace}")
        analysis["debugging_commands"].append(f"oc get namespace {namespace}")
        analysis["debugging_commands"].append(f"oc get all -n {namespace}")
        analysis["quick_fixes"].append({
            "description": "Delete existing namespace",
            "commands": [
                f"oc delete namespace {namespace}",
                f"oc wait --for=delete namespace/{namespace} --timeout=60s"
            ]
        })

    # Pattern: Pod creation failed
    if any(pattern in combined_output for pattern in ["error creating", "failed to create pod", "pod creation failed"]):
        analysis["root_causes"].append("Pod creation failed")
        analysis["recommendations"].append("Check pod specification and resource quotas")
        analysis["debugging_commands"].append(f"oc get events -n {namespace} --sort-by='.lastTimestamp'")
        analysis["debugging_commands"].append(f"oc get resourcequotas -n {namespace}")
        analysis["debugging_commands"].append(f"oc get limitranges -n {namespace}")

    # Pattern: ImagePullBackOff
    if "imagepullbackoff" in combined_output or "image pull" in combined_output:
        analysis["root_causes"].append("Failed to pull container image")
        analysis["recommendations"].append("Verify image name and registry accessibility")
        analysis["debugging_commands"].append(f"oc describe pod <pod-name> -n {namespace}")
        analysis["debugging_commands"].append(f"oc get events -n {namespace} | grep -i pull")
        analysis["quick_fixes"].append({
            "description": "Check image and registry",
            "commands": [
                f"oc describe pod <pod-name> -n {namespace} | grep -A5 Events",
                "# Verify image exists in registry",
                "# Check image pull secrets if using private registry"
            ]
        })

    # Pattern: Timeout waiting for pod
    if "timeout" in combined_output or "timed out" in combined_output:
        if "waiting for" in combined_output or "condition" in combined_output:
            analysis["root_causes"].append("Pod did not become ready within timeout period")
            analysis["recommendations"].append("Increase timeout or check pod status and events")
            analysis["debugging_commands"].append(f"oc get pod <pod-name> -n {namespace} -o wide")
            analysis["debugging_commands"].append(f"oc describe pod <pod-name> -n {namespace}")
            analysis["debugging_commands"].append(f"oc logs <pod-name> -n {namespace}")
            analysis["debugging_commands"].append(f"oc get events -n {namespace} --sort-by='.lastTimestamp'")

    # Pattern: CrashLoopBackOff
    if "crashloopbackoff" in combined_output:
        analysis["root_causes"].append("Pod is crashing repeatedly")
        analysis["recommendations"].append("Check pod logs for crash reason")
        analysis["debugging_commands"].append(f"oc logs <pod-name> -n {namespace} --previous")
        analysis["debugging_commands"].append(f"oc describe pod <pod-name> -n {namespace}")
        analysis["quick_fixes"].append({
            "description": "Debug crashing pod",
            "commands": [
                f"oc logs <pod-name> -n {namespace} --previous",
                f"oc describe pod <pod-name> -n {namespace}",
                "# Check for missing dependencies, configuration errors, or resource limits"
            ]
        })

    # Pattern: Resource constraints
    if any(pattern in combined_output for pattern in ["insufficient", "exceeded quota", "resource quota", "limit"]):
        analysis["root_causes"].append("Resource constraints or quota exceeded")
        analysis["recommendations"].append("Check resource quotas and limits")
        analysis["debugging_commands"].append(f"oc describe quota -n {namespace}")
        analysis["debugging_commands"].append(f"oc describe limitrange -n {namespace}")
        analysis["debugging_commands"].append(f"oc get pods -n {namespace} -o yaml | grep -A5 resources")

    # Pattern: Network issues
    if any(pattern in combined_output for pattern in ["connection refused", "timeout", "network", "dns", "unreachable"]):
        analysis["root_causes"].append("Network connectivity issue")
        analysis["recommendations"].append("Check cluster network connectivity and DNS resolution")
        analysis["debugging_commands"].append("oc get nodes")
        analysis["debugging_commands"].append(f"oc get pods -n {namespace} -o wide")
        analysis["debugging_commands"].append("oc get network-diagnostics")

    # Pattern: Invalid/malformed spec
    if any(pattern in combined_output for pattern in ["invalid", "malformed", "syntax error", "parse error"]):
        analysis["root_causes"].append("Invalid or malformed resource specification")
        analysis["recommendations"].append("Validate YAML syntax and resource specification")
        analysis["debugging_commands"].append("# Check YAML syntax")
        analysis["debugging_commands"].append("# Validate against Kubernetes API schema")

    return analysis


def _detect_common_patterns(failed_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect common patterns across multiple failed steps."""
    patterns = {
        "root_causes": [],
        "recommendations": [],
    }

    # If first step (prerequisites) failed
    first_step = failed_steps[0] if failed_steps else None
    if first_step and first_step.get("step_number") == 1:
        patterns["root_causes"].append("Test failed at prerequisites check - environment setup issue")
        patterns["recommendations"].append("Ensure oc CLI is installed and you are logged into the cluster")
        patterns["recommendations"].append("Verify cluster connectivity: oc cluster-info")

    # If multiple consecutive steps failed
    if len(failed_steps) > 3:
        patterns["root_causes"].append("Multiple consecutive failures detected - likely systemic issue")
        patterns["recommendations"].append("Check overall cluster health and connectivity")
        patterns["recommendations"].append("Review cluster operator status: oc get co")

    # Check for authentication/permission patterns
    auth_failures = sum(1 for step in failed_steps
                       for cmd in step.get("commands", [])
                       if any(p in cmd.get("stderr", "").lower()
                             for p in ["forbidden", "unauthorized", "permission"]))

    if auth_failures > 0:
        patterns["root_causes"].append("Authentication or permission issues detected")
        patterns["recommendations"].append("Verify your user has sufficient cluster permissions")
        patterns["recommendations"].append("Check RBAC policies and role bindings")

    return patterns


def _get_component_specific_debug(component: str, failed_steps: List[Dict[str, Any]], namespace: str) -> Dict[str, Any]:
    """Get component-specific debugging information."""
    debug_info = {"commands": []}

    component_lower = component.lower() if component else ""

    if "kube-apiserver" in component_lower:
        debug_info["commands"].extend([
            "oc get pods -n openshift-kube-apiserver",
            "oc logs -n openshift-kube-apiserver -l app=openshift-kube-apiserver --tail=50",
            "oc get kubeapiserver cluster -o yaml",
        ])
        debug_info["description"] = "kube-apiserver specific debugging"

    elif "pod" in component_lower:
        debug_info["commands"].extend([
            f"oc get pods -n {namespace} -o wide",
            f"oc describe pod <pod-name> -n {namespace}",
            f"oc logs <pod-name> -n {namespace}",
            f"oc get events -n {namespace}",
        ])
        debug_info["description"] = "Pod debugging commands"

    elif "oauth" in component_lower:
        debug_info["commands"].extend([
            "oc get oauth cluster -o yaml",
            "oc get clusteroperator authentication",
            "oc logs -n openshift-authentication --tail=50",
        ])
        debug_info["description"] = "OAuth/Authentication debugging"

    elif "registry" in component_lower:
        debug_info["commands"].extend([
            "oc get clusteroperator image-registry",
            "oc get configs.imageregistry.operator.openshift.io cluster -o yaml",
            "oc get pods -n openshift-image-registry",
        ])
        debug_info["description"] = "Image registry debugging"

    return debug_info


def _generate_debug_summary(debug_info: Dict[str, Any], failed_steps: List[Dict[str, Any]], execution: Dict[str, Any]) -> str:
    """Generate human-readable debugging summary."""

    total_steps = execution.get("total_steps", 0)
    failed_count = len(failed_steps)
    first_failure = failed_steps[0].get("step_number") if failed_steps else 0

    # Deduplicate root causes and recommendations
    unique_causes = list(dict.fromkeys(debug_info.get("root_causes", [])))
    unique_recommendations = list(dict.fromkeys(debug_info.get("recommendations", [])))

    summary = f"""
Test Failure Debugging Summary
{'=' * 70}
Feature:    {debug_info.get('feature', 'unknown')}
Component:  {debug_info.get('component', 'unknown')}
Namespace:  {debug_info.get('namespace', 'unknown')}
Status:     {debug_info.get('test_status', 'FAILED')}

Failure Statistics:
  Total Steps:        {total_steps}
  Failed Steps:       {failed_count}
  First Failure:      Step {first_failure}

Root Causes Identified ({len(unique_causes)}):
"""

    for i, cause in enumerate(unique_causes[:5], 1):  # Show top 5
        summary += f"  {i}. {cause}\n"

    summary += f"\nRecommended Actions ({len(unique_recommendations)}):\n"

    for i, rec in enumerate(unique_recommendations[:5], 1):  # Show top 5
        summary += f"  {i}. {rec}\n"

    summary += f"\nDebugging Commands Available: {len(debug_info.get('debugging_commands', []))}\n"
    summary += f"Quick Fixes Available: {len(debug_info.get('quick_fixes', []))}\n"

    summary += f"\n{'=' * 70}\n"

    return summary.strip()
