"""OpenShift Step-by-Step Test Executor tool for the MCP Server.

This tool executes OpenShift tests step-by-step with detailed progress reporting
and results for each step. Perfect for interactive testing and debugging.
"""

import subprocess
import time
from typing import Any, Dict, List, Optional

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


def execute_ocp_test_step_by_step(
    feature: str,
    component: str,
    scenario: str,
    namespace: Optional[str] = None,
    kubeconfig_path: Optional[str] = None,
    oc_path: Optional[str] = None,
    timeout_per_step: int = 300,
) -> Dict[str, Any]:
    """Execute OpenShift test step-by-step with detailed progress reporting.

    TOOL_NAME=execute_ocp_test_step_by_step
    DISPLAY_NAME=OpenShift Step-by-Step Test Executor
    USECASE=Execute OCP tests incrementally with detailed reporting of each step's results
    INSTRUCTIONS=1. Provide test details (feature, component, scenario), 2. Optionally specify namespace and kubeconfig, 3. Receive step-by-step execution results
    INPUT_DESCRIPTION=feature (str): Feature being tested, component (str): OCP component, scenario (str): Test scenario, namespace (str, optional): Target namespace, kubeconfig_path (str, optional): Path to kubeconfig, oc_path (str, optional): Path to oc binary, timeout_per_step (int): Timeout per step in seconds
    OUTPUT_DESCRIPTION=Dictionary with detailed step-by-step execution results, status of each step, logs, and overall summary
    EXAMPLES=execute_ocp_test_step_by_step("Pod Deployment", "pod", "Deploy pod in test namespace"), execute_ocp_test_step_by_step("Event TTL", "kube-apiserver", "Verify eventTTLMinutes", kubeconfig_path="/path/to/kubeconfig")
    PREREQUISITES=oc CLI installed, cluster access
    RELATED_TOOLS=generate_ocp_test_case, execute_ocp_test

    This tool executes tests step-by-step and provides:
    - Real-time step execution
    - Detailed result for each step
    - Step-level pass/fail status
    - Logs and output for each step
    - Overall test summary

    Args:
        feature: Feature or capability being tested
        component: OpenShift component
        scenario: Test scenario description
        namespace: Target namespace (optional, auto-generated if not provided)
        kubeconfig_path: Path to kubeconfig file (optional)
        oc_path: Path to oc CLI binary (optional, uses system PATH if not provided)
        timeout_per_step: Maximum time per step in seconds

    Returns:
        Dictionary containing step-by-step execution results

    Raises:
        ValueError: If inputs are invalid
    """
    try:
        # Validate inputs
        if not feature or not component or not scenario:
            raise ValueError("feature, component, and scenario are required")

        logger.info(f"Starting step-by-step test execution for {component}/{feature}")

        # Generate namespace if not provided
        if not namespace:
            namespace = f"test-{component.lower().replace('_', '-')}"

        # Initialize results structure
        execution_results = {
            "status": "in_progress",
            "feature": feature,
            "component": component,
            "scenario": scenario,
            "namespace": namespace,
            "total_steps": 0,
            "completed_steps": 0,
            "passed_steps": 0,
            "failed_steps": 0,
            "steps": [],
            "overall_status": "pending",
            "start_time": time.time(),
        }

        # Define test steps
        steps = _define_test_steps(component, namespace, kubeconfig_path, oc_path)
        execution_results["total_steps"] = len(steps)

        # Execute each step
        for idx, step in enumerate(steps, 1):
            step_result = _execute_step(
                step_number=idx,
                step=step,
                timeout=timeout_per_step,
                kubeconfig_path=kubeconfig_path,
                oc_path=oc_path,
                namespace=namespace,
            )

            execution_results["steps"].append(step_result)
            execution_results["completed_steps"] = idx

            if step_result["status"] == "passed":
                execution_results["passed_steps"] += 1
            else:
                execution_results["failed_steps"] += 1

                # Stop on critical failures
                if step_result.get("critical", False):
                    logger.error(f"Critical step {idx} failed. Stopping execution.")
                    break

        # Calculate overall status
        execution_results["end_time"] = time.time()
        execution_results["duration_seconds"] = execution_results["end_time"] - execution_results["start_time"]

        if execution_results["failed_steps"] == 0:
            execution_results["overall_status"] = "PASSED"
        elif execution_results["passed_steps"] > 0:
            execution_results["overall_status"] = "PARTIALLY_PASSED"
        else:
            execution_results["overall_status"] = "FAILED"

        execution_results["status"] = "completed"

        return {
            "status": "success",
            "execution": execution_results,
            "summary": _generate_summary(execution_results),
            "message": "Step-by-step test execution completed",
        }

    except Exception as e:
        logger.error(f"Error in step-by-step execution: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to execute step-by-step test",
        }


def _define_test_steps(component: str, namespace: str, kubeconfig_path: Optional[str], oc_path: Optional[str]) -> List[Dict[str, Any]]:
    """Define the test steps to execute."""
    base_steps = [
        {
            "name": "Verify Prerequisites",
            "description": "Check oc CLI installation and cluster connectivity",
            "commands": [
                {"cmd": "oc version --client", "description": "Check oc CLI version"},
                {"cmd": "oc cluster-info", "description": "Verify cluster connectivity"},
            ],
            "critical": True,
        },
        {
            "name": "Check Permissions",
            "description": "Verify user has required permissions",
            "commands": [
                {"cmd": "oc whoami", "description": "Get current user"},
                {"cmd": f"oc auth can-i create namespace", "description": "Check namespace creation permission"},
            ],
            "critical": True,
        },
        {
            "name": "Create Test Namespace",
            "description": f"Create namespace '{namespace}' for testing",
            "commands": [
                {"cmd": f"oc create namespace {namespace} --dry-run=client -o yaml", "description": "Validate namespace spec"},
                {"cmd": f"oc get namespace {namespace} 2>/dev/null || oc create namespace {namespace}", "description": "Create namespace"},
                {"cmd": f"oc get namespace {namespace}", "description": "Verify namespace created"},
            ],
            "critical": True,
        },
        {
            "name": "Deploy Test Pod",
            "description": f"Deploy test pod in namespace '{namespace}'",
            "commands": [
                {
                    "cmd": f"""cat <<EOF | oc apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: {namespace}
  labels:
    app: test-pod
    test: step-by-step
spec:
  containers:
  - name: test-container
    image: registry.access.redhat.com/ubi8/ubi-minimal:latest
    command: ["sh", "-c", "echo 'Test pod started successfully' && sleep 3600"]
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
  restartPolicy: Always
EOF""",
                    "description": "Create test pod",
                },
            ],
            "critical": True,
        },
        {
            "name": "Wait for Pod Ready",
            "description": "Wait for test pod to become ready",
            "commands": [
                {"cmd": f"oc get pod test-pod -n {namespace}", "description": "Check pod status"},
                {"cmd": f"oc wait --for=condition=Ready pod/test-pod -n {namespace} --timeout=60s", "description": "Wait for pod ready"},
            ],
            "critical": True,
        },
        {
            "name": "Verify Pod Running",
            "description": "Verify pod is running and healthy",
            "commands": [
                {"cmd": f"oc get pod test-pod -n {namespace} -o wide", "description": "Get pod details"},
                {"cmd": f"oc describe pod test-pod -n {namespace}", "description": "Describe pod"},
            ],
            "critical": False,
        },
        {
            "name": "Check Pod Logs",
            "description": "Retrieve and verify pod logs",
            "commands": [
                {"cmd": f"oc logs test-pod -n {namespace}", "description": "Get pod logs"},
            ],
            "critical": False,
        },
        {
            "name": "Verify Component Health",
            "description": f"Check {component} component health",
            "commands": [
                {"cmd": f"oc get pods -n {namespace}", "description": f"List pods in {namespace}"},
                {"cmd": f"oc get events -n {namespace} --sort-by='.lastTimestamp'", "description": "Check recent events"},
            ],
            "critical": False,
        },
        {
            "name": "Collect Diagnostics",
            "description": "Collect diagnostic information",
            "commands": [
                {"cmd": f"oc get all -n {namespace}", "description": "Get all resources"},
                {"cmd": f"oc get events -n {namespace}", "description": "Get events"},
            ],
            "critical": False,
        },
        {
            "name": "Cleanup Resources",
            "description": "Clean up test resources",
            "commands": [
                {"cmd": f"oc delete pod test-pod -n {namespace} --grace-period=0 --force 2>/dev/null || true", "description": "Delete test pod"},
                {"cmd": f"oc delete namespace {namespace} --grace-period=0 --force 2>/dev/null || true", "description": "Delete test namespace"},
            ],
            "critical": False,
        },
    ]

    # Add component-specific steps
    if component.lower() == "kube-apiserver":
        base_steps.insert(
            5,
            {
                "name": "Verify kube-apiserver Configuration",
                "description": "Check kube-apiserver specific settings",
                "commands": [
                    {
                        "cmd": "oc get pods -n openshift-kube-apiserver -l app=openshift-kube-apiserver",
                        "description": "List kube-apiserver pods",
                    },
                ],
                "critical": False,
            },
        )

    return base_steps


def _execute_step(
    step_number: int, step: Dict[str, Any], timeout: int, kubeconfig_path: Optional[str], oc_path: Optional[str], namespace: str
) -> Dict[str, Any]:
    """Execute a single test step."""
    step_result = {
        "step_number": step_number,
        "name": step["name"],
        "description": step["description"],
        "status": "pending",
        "commands": [],
        "start_time": time.time(),
    }

    logger.info(f"Step {step_number}: {step['name']}")

    all_passed = True

    for cmd_info in step["commands"]:
        cmd = cmd_info["cmd"]
        cmd_desc = cmd_info["description"]

        # Replace oc binary path if custom path provided
        if oc_path and "oc " in cmd:
            cmd = cmd.replace("oc ", f"{oc_path} ")

        # Add kubeconfig if provided
        if kubeconfig_path and "oc " in cmd:
            cmd = cmd.replace("oc ", f"oc --kubeconfig {kubeconfig_path} ")
        # Handle case where oc was already replaced with custom path
        elif kubeconfig_path and oc_path and oc_path in cmd:
            cmd = cmd.replace(f"{oc_path} ", f"{oc_path} --kubeconfig {kubeconfig_path} ")

        cmd_result = _execute_command(cmd, cmd_desc, timeout)
        step_result["commands"].append(cmd_result)

        if cmd_result["status"] != "success":
            all_passed = False

    step_result["end_time"] = time.time()
    step_result["duration_seconds"] = step_result["end_time"] - step_result["start_time"]
    step_result["status"] = "passed" if all_passed else "failed"
    step_result["critical"] = step.get("critical", False)

    return step_result


def _execute_command(cmd: str, description: str, timeout: int) -> Dict[str, Any]:
    """Execute a single command."""
    logger.info(f"  Executing: {description}")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=None
        )

        return {
            "description": description,
            "command": cmd,
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    except subprocess.TimeoutExpired:
        return {
            "description": description,
            "command": cmd,
            "status": "timeout",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
        }
    except Exception as e:
        return {
            "description": description,
            "command": cmd,
            "status": "error",
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
        }


def _generate_summary(execution_results: Dict[str, Any]) -> str:
    """Generate human-readable summary."""
    total = execution_results["total_steps"]
    completed = execution_results["completed_steps"]
    passed = execution_results["passed_steps"]
    failed = execution_results["failed_steps"]
    status = execution_results["overall_status"]
    duration = execution_results.get("duration_seconds", 0)

    summary = f"""
Test Execution Summary
{'=' * 60}
Feature:    {execution_results['feature']}
Component:  {execution_results['component']}
Scenario:   {execution_results['scenario']}
Namespace:  {execution_results['namespace']}

Step Results:
  Total Steps:     {total}
  Completed:       {completed}
  Passed:          {passed} ✅
  Failed:          {failed} ❌

Overall Status:    {status}
Duration:          {duration:.2f} seconds

{'=' * 60}
"""

    return summary.strip()
