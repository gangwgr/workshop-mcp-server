"""Run focused oc diagnostic workflows for the cluster-debugger web GUI."""

import os
import subprocess
from typing import Any, Dict, List, Optional

WORKFLOW_CATALOG: Dict[str, Dict[str, Any]] = {
    "initial_triage": {
        "label": "Initial Triage",
        "description": "Cluster version, operators, nodes, and non-Running pods",
        "icon": "fa-stethoscope",
        "commands": [
            "oc get clusterversion",
            "oc get clusteroperators",
            "oc get nodes",
            "oc get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded",
        ],
    },
    "operators_degraded": {
        "label": "Operators Degraded",
        "description": "Describe operator, check namespace pods, events",
        "icon": "fa-cogs",
        "options": ["operator"],
        "commands": [
            "oc describe clusteroperator {operator}",
            "oc get pods -n openshift-{operator} -o wide",
            "oc get events -n openshift-{operator} --sort-by=.lastTimestamp | tail -20",
        ],
    },
    "pod_crashloop": {
        "label": "Pod CrashLoop / Not Ready",
        "description": "Describe pod, previous logs, and related events",
        "icon": "fa-cube",
        "options": ["namespace", "component"],
        "commands": [
            "oc describe pod -n {namespace} {component}",
            "oc logs -n {namespace} {component} --previous --tail=80",
            "oc get events -n {namespace} --field-selector involvedObject.name={component} --sort-by=.lastTimestamp",
        ],
    },
    "control_plane": {
        "label": "API / Control Plane",
        "description": "kube-apiserver and etcd health",
        "icon": "fa-server",
        "commands": [
            "oc get pods -n openshift-kube-apiserver -o wide",
            "oc get pods -n openshift-etcd -o wide",
            "oc get etcd cluster -o yaml",
        ],
    },
    "apiserver_health": {
        "label": "API Server Health",
        "description": "Operator status, pods, and /healthz /livez /readyz endpoints",
        "icon": "fa-heartbeat",
        "commands": [
            "oc get clusteroperator kube-apiserver",
            "oc get pods -n openshift-kube-apiserver -l app=openshift-kube-apiserver -o wide",
            "oc get --raw /healthz",
            "oc get --raw /livez?verbose",
            "oc get --raw /readyz?verbose",
        ],
    },
    "apiserver_operator": {
        "label": "API Server Operator",
        "description": "kube-apiserver cluster operator, operator pods, KubeAPIServer CR",
        "icon": "fa-cogs",
        "commands": [
            "oc describe clusteroperator kube-apiserver",
            "oc get pods -n openshift-kube-apiserver-operator -o wide",
            "oc get kubeapiserver cluster -o yaml",
            "oc get events -n openshift-kube-apiserver-operator --sort-by=.lastTimestamp | tail -20",
        ],
    },
    "apiserver_logs": {
        "label": "API Server Logs",
        "description": "Recent logs from all kube-apiserver pods",
        "icon": "fa-file-alt",
        "commands": [
            "oc logs -n openshift-kube-apiserver -l app=openshift-kube-apiserver --tail=80 --prefix=true",
        ],
    },
    "apiserver_pod_detail": {
        "label": "API Server Pod Deep Dive",
        "description": "Describe a specific kube-apiserver pod and current/previous logs",
        "icon": "fa-search",
        "options": ["component"],
        "commands": [
            "oc describe pod -n openshift-kube-apiserver {component}",
            "oc logs -n openshift-kube-apiserver {component} --tail=100",
            "oc logs -n openshift-kube-apiserver {component} --previous --tail=50",
        ],
    },
    "apiserver_events": {
        "label": "API Server Events",
        "description": "Recent events in kube-apiserver and operator namespaces",
        "icon": "fa-bell",
        "commands": [
            "oc get events -n openshift-kube-apiserver --sort-by=.lastTimestamp | tail -30",
            "oc get events -n openshift-kube-apiserver-operator --sort-by=.lastTimestamp | tail -20",
        ],
    },
    "apiserver_auth": {
        "label": "API Auth / OAuth",
        "description": "Authentication operator and OAuth when API returns 401/403",
        "icon": "fa-key",
        "commands": [
            "oc whoami",
            "oc get clusteroperator authentication",
            "oc get pods -n openshift-authentication -o wide",
            "oc get pods -n openshift-oauth-apiserver -o wide",
            "oc get oauth cluster -o yaml",
        ],
    },
    "openshift_apiserver": {
        "label": "OpenShift API Server",
        "description": "openshift-apiserver operator, pods, and APIServer CR",
        "icon": "fa-plug",
        "commands": [
            "oc get clusteroperator openshift-apiserver",
            "oc get pods -n openshift-apiserver -o wide",
            "oc get apiserver cluster -o yaml",
            "oc logs deployment/apiserver -n openshift-apiserver --tail=80 --all-containers --prefix=true",
        ],
    },
    "upgrade_stuck": {
        "label": "Upgrade Stuck",
        "description": "Cluster version and operator state during upgrade",
        "icon": "fa-arrow-up",
        "commands": [
            "oc get clusterversion -o yaml",
            "oc get clusteroperators",
            "oc adm upgrade",
        ],
    },
    "authentication": {
        "label": "Authentication / OAuth",
        "description": "OAuth and authentication operator diagnostics",
        "icon": "fa-key",
        "commands": [
            "oc get pods -n openshift-authentication -o wide",
            "oc get oauth cluster -o yaml",
            "oc get authentication cluster -o yaml",
        ],
    },
    "network_ovn": {
        "label": "Network (OVN)",
        "description": "OVN-Kubernetes pods, network config, connectivity checks",
        "icon": "fa-network-wired",
        "commands": [
            "oc get pods -n openshift-ovn-kubernetes -o wide",
            "oc get network.config cluster -o yaml",
            "oc get podnetworkconnectivitychecks -A",
        ],
    },
    "namespace_overview": {
        "label": "Namespace Overview",
        "description": "Pods, events, and workloads in a namespace",
        "icon": "fa-folder",
        "options": ["namespace"],
        "commands": [
            "oc get pods -n {namespace} -o wide",
            "oc get events -n {namespace} --sort-by=.lastTimestamp | tail -30",
            "oc get deploy,sts,ds -n {namespace}",
        ],
    },
}

QUICK_PRESETS: Dict[str, Dict[str, Any]] = {
    "quick_health": {
        "label": "Quick Health Check",
        "workflows": ["initial_triage"],
    },
    "control_plane_issues": {
        "label": "Control Plane Issues",
        "workflows": ["initial_triage", "apiserver_health", "control_plane"],
    },
    "apiserver_not_responding": {
        "label": "API Server Not Responding",
        "workflows": ["apiserver_health", "apiserver_logs", "apiserver_events"],
    },
    "apiserver_full_debug": {
        "label": "API Server Full Debug",
        "workflows": [
            "apiserver_health",
            "apiserver_operator",
            "apiserver_logs",
            "apiserver_events",
            "control_plane",
        ],
    },
    "openshift_apiserver_debug": {
        "label": "OpenShift API Server",
        "workflows": ["openshift_apiserver"],
    },
    "auth_debug": {
        "label": "Authentication / OAuth",
        "workflows": ["apiserver_auth"],
    },
    "network_troubleshoot": {
        "label": "Network Troubleshoot",
        "workflows": ["initial_triage", "network_ovn"],
    },
    "upgrade_debug": {
        "label": "Upgrade Debug",
        "workflows": ["upgrade_stuck", "initial_triage"],
    },
}


def list_workflows() -> List[Dict[str, Any]]:
    """Return workflow catalog for the UI."""
    items = []
    for key, meta in WORKFLOW_CATALOG.items():
        items.append({
            "id": key,
            "label": meta["label"],
            "description": meta.get("description", ""),
            "icon": meta.get("icon", "fa-terminal"),
            "options": meta.get("options", []),
        })
    return items


def _expand_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return os.path.abspath(os.path.expanduser(path.strip()))


def _build_oc_base(oc_path: Optional[str], kubeconfig_path: Optional[str]) -> str:
    oc = (oc_path or "oc").strip()
    kubeconfig = _expand_path(kubeconfig_path)
    if kubeconfig:
        return f"{oc} --kubeconfig {kubeconfig}"
    return oc


def _format_command(template: str, oc_base: str, params: Dict[str, str]) -> str:
    cmd = template.format(**params)
    if cmd.startswith("oc "):
        return cmd.replace("oc ", f"{oc_base} ", 1)
    return cmd


def _run_shell(cmd: str, timeout: int = 90) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return {
            "command": cmd,
            "exit_code": proc.returncode,
            "output": output.strip(),
            "status": "success" if proc.returncode == 0 else "error",
        }
    except subprocess.TimeoutExpired:
        return {"command": cmd, "exit_code": -1, "output": "", "status": "error", "error": "Command timed out"}
    except Exception as e:
        return {"command": cmd, "exit_code": -1, "output": "", "status": "error", "error": str(e)}


def _validate_oc(oc_base: str) -> Optional[str]:
    check = _run_shell(f"{oc_base} whoami", timeout=30)
    if check["exit_code"] != 0:
        return check.get("output") or check.get("error") or "oc whoami failed — check login and kubeconfig"
    return None


def _resolve_params(workflow_id: str, kwargs: Dict[str, Optional[str]], oc_base: str = "oc") -> Dict[str, str]:
    meta = WORKFLOW_CATALOG[workflow_id]
    params: Dict[str, str] = {}
    for opt in meta.get("options", []):
        value = (kwargs.get(opt) or "").strip()
        if not value:
            if opt == "component":
                # Determine the correct namespace for auto-detection
                ns = None
                # First check if namespace is in params or kwargs
                if "namespace" in params:
                    ns = params["namespace"]
                elif (kwargs.get("namespace") or "").strip():
                    ns = (kwargs["namespace"] or "").strip()

                # If no user namespace, extract from hardcoded commands (e.g., "-n openshift-kube-apiserver")
                if not ns:
                    import re
                    for cmd in meta.get("commands", []):
                        m = re.search(r'-n\s+([\w-]+)', cmd)
                        if m:
                            ns = m.group(1)
                            break

                if ns:
                    # Expand shorthand
                    if not ns.startswith("openshift-") and ns in ("etcd", "apiserver", "authentication", "monitoring", "dns", "ingress", "sdn"):
                        ns = f"openshift-{ns}"
                    detected = _auto_detect_pod(oc_base, ns)
                    if detected:
                        params[opt] = detected
                        continue
                    raise ValueError(f"No pods found in namespace '{ns}'. Please specify a pod name.")
                raise ValueError(f"Missing required option: {opt}")
            raise ValueError(f"Missing required option: {opt}")
        # Auto-expand namespace shorthand
        if opt == "namespace" and not value.startswith("openshift-") and value in ("etcd", "apiserver", "authentication", "monitoring", "dns", "ingress", "sdn"):
            value = f"openshift-{value}"
        params[opt] = value
    return params


def _auto_detect_pod(oc_base: str, namespace: str) -> Optional[str]:
    """Auto-detect pods in the namespace. Returns space-separated names for multi-pod analysis."""
    import subprocess

    # Auxiliary pod prefixes to deprioritize (guard, installer, pruner, revision jobs)
    aux_prefixes = ("guard", "installer-", "revision-pruner-", "pruner-")

    def filter_pods(pod_list):
        """Separate main pods from auxiliary pods."""
        main = [p for p in pod_list if not any(prefix in p for prefix in aux_prefixes)]
        aux = [p for p in pod_list if any(prefix in p for prefix in aux_prefixes)]
        return main if main else aux

    try:
        # First try to find non-running pods (problematic ones take priority)
        cmd = f"{oc_base} get pods -n {namespace} --field-selector=status.phase!=Running,status.phase!=Succeeded --no-headers -o custom-columns=NAME:.metadata.name"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            pods = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
            main_pods = filter_pods(pods)
            if main_pods:
                return " ".join(main_pods[:3])

        # Fall back to running pods — prioritize main workload pods
        cmd = f"{oc_base} get pods -n {namespace} --field-selector=status.phase=Running --no-headers -o custom-columns=NAME:.metadata.name"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            pods = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
            main_pods = filter_pods(pods)
            if main_pods:
                return " ".join(main_pods[:3])
    except Exception:
        pass
    return None


def run_workflow(
    workflow_id: str,
    oc_path: Optional[str] = None,
    kubeconfig_path: Optional[str] = None,
    namespace: Optional[str] = None,
    component: Optional[str] = None,
    operator: Optional[str] = None,
    timeout: int = 90,
) -> Dict[str, Any]:
    """Run a single diagnostic workflow."""
    if workflow_id not in WORKFLOW_CATALOG:
        return {"status": "error", "error": f"Unknown workflow: {workflow_id}"}

    meta = WORKFLOW_CATALOG[workflow_id]
    oc_base = _build_oc_base(oc_path, kubeconfig_path)

    auth_err = _validate_oc(oc_base)
    if auth_err:
        return {"status": "error", "error": auth_err}

    try:
        params = _resolve_params(
            workflow_id,
            {"namespace": namespace, "component": component, "operator": operator},
            oc_base=oc_base,
        )
    except ValueError as e:
        return {"status": "error", "error": str(e)}

    results = []

    # If component has multiple pods (space-separated), run commands for each pod
    component_value = params.get("component", "")
    if " " in component_value and "{component}" in " ".join(meta.get("commands", [])):
        pods = component_value.split()
        for pod in pods:
            pod_params = dict(params)
            pod_params["component"] = pod
            for template in meta["commands"]:
                cmd = _format_command(template, oc_base, pod_params)
                results.append(_run_shell(cmd, timeout=timeout))
    else:
        for template in meta["commands"]:
            cmd = _format_command(template, oc_base, params)
            results.append(_run_shell(cmd, timeout=timeout))

    combined = _format_combined_output(meta["label"], results)
    any_error = any(r["exit_code"] != 0 for r in results)

    return {
        "status": "success" if not any_error else "partial",
        "workflow_id": workflow_id,
        "workflow_label": meta["label"],
        "results": results,
        "output": combined,
    }


def run_preset(
    preset_id: str,
    oc_path: Optional[str] = None,
    kubeconfig_path: Optional[str] = None,
    namespace: Optional[str] = None,
    component: Optional[str] = None,
    operator: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a preset bundle of workflows."""
    if preset_id not in QUICK_PRESETS:
        return {"status": "error", "error": f"Unknown preset: {preset_id}"}

    preset = QUICK_PRESETS[preset_id]
    results = []
    for workflow_id in preset["workflows"]:
        results.append(
            run_workflow(
                workflow_id,
                oc_path=oc_path,
                kubeconfig_path=kubeconfig_path,
                namespace=namespace,
                component=component,
                operator=operator,
            )
        )

    combined_parts = []
    for r in results:
        combined_parts.append(r.get("output", r.get("error", "")))

    return {
        "status": "success",
        "preset": preset_id,
        "preset_label": preset["label"],
        "results": results,
        "output": "\n\n".join(p for p in combined_parts if p),
    }


def _format_combined_output(label: str, results: List[Dict[str, Any]]) -> str:
    parts = []
    for r in results:
        parts.append("\n" + "=" * 72)
        parts.append(r["command"])
        parts.append("=" * 72)
        status = "OK" if r["exit_code"] == 0 else f"EXIT {r['exit_code']}"
        parts.append(f"[{status}]")
        parts.append(r.get("output") or r.get("error") or "(no output)")
    header = f"Workflow: {label}\n"
    return header + "\n".join(parts)
