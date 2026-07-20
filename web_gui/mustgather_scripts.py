"""Run openshift-eng/ai-helpers must-gather analysis scripts from the web GUI."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Repo root: web_gui/ -> workshop-mcp-server/
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / ".cursor" / "skills" / "must-gather-analyzer" / "scripts"
if not _SCRIPTS_DIR.is_dir():
    _SCRIPTS_DIR = _REPO_ROOT / "skills" / "must-gather-analyzer" / "scripts"

SCRIPT_CATALOG: Dict[str, Dict[str, Any]] = {
    "clusterversion": {
        "script": "analyze_clusterversion.py",
        "label": "Cluster Version",
        "description": "Version, upgrade status, capabilities (oc get clusterversion)",
        "icon": "fa-code-branch",
    },
    "clusteroperators": {
        "script": "analyze_clusteroperators.py",
        "label": "Cluster Operators",
        "description": "Operator health, degraded/available conditions",
        "icon": "fa-cogs",
    },
    "pods": {
        "script": "analyze_pods.py",
        "label": "Pods",
        "description": "Pod status across namespaces; filter by namespace or problems only",
        "icon": "fa-cube",
        "options": ["namespace", "problems_only"],
    },
    "nodes": {
        "script": "analyze_nodes.py",
        "label": "Nodes",
        "description": "Node readiness, conditions, capacity",
        "icon": "fa-server",
        "options": ["problems_only"],
    },
    "etcd": {
        "script": "analyze_etcd.py",
        "label": "etcd",
        "description": "Member health, quorum, endpoint status",
        "icon": "fa-database",
    },
    "network": {
        "script": "analyze_network.py",
        "label": "Network",
        "description": "OVN/SDN health and connectivity checks",
        "icon": "fa-network-wired",
    },
    "ovn_dbs": {
        "script": "analyze_ovn_dbs.py",
        "label": "OVN Databases",
        "description": "OVN-Kubernetes database diagnostics",
        "icon": "fa-project-diagram",
    },
    "events": {
        "script": "analyze_events.py",
        "label": "Events",
        "description": "Warning/error events by namespace",
        "icon": "fa-bell",
        "options": ["namespace", "event_type", "count"],
    },
    "pvs": {
        "script": "analyze_pvs.py",
        "label": "Storage (PV/PVC)",
        "description": "PersistentVolumes and claims",
        "icon": "fa-hdd",
        "options": ["namespace"],
    },
    "prometheus": {
        "script": "analyze_prometheus.py",
        "label": "Prometheus Alerts",
        "description": "Firing/pending alerts from monitoring",
        "icon": "fa-chart-line",
        "options": ["namespace"],
    },
    "windows_logs": {
        "script": "analyze_windows_logs.py",
        "label": "Windows Node Logs",
        "description": "Windows worker node log analysis",
        "icon": "fa-windows",
    },
}

QUICK_PRESETS = {
    "health_check": {
        "label": "Quick Health Check",
        "scripts": ["clusterversion", "clusteroperators", "pods", "nodes"],
        "pods_problems_only": True,
        "nodes_problems_only": False,
    },
    "degraded_cluster": {
        "label": "Degraded Cluster",
        "scripts": ["clusteroperators", "pods", "events", "etcd"],
        "pods_problems_only": True,
        "events_type": "Warning",
    },
    "network_issues": {
        "label": "Network Issues",
        "scripts": ["network", "ovn_dbs", "pods"],
        "pods_namespace": "openshift-ovn-kubernetes",
    },
}


def list_scripts() -> List[Dict[str, Any]]:
    """Return script catalog for the UI."""
    items = []
    for key, meta in SCRIPT_CATALOG.items():
        script_path = _SCRIPTS_DIR / meta["script"]
        items.append({
            "id": key,
            "label": meta["label"],
            "description": meta.get("description", ""),
            "icon": meta.get("icon", "fa-terminal"),
            "options": meta.get("options", []),
            "available": script_path.is_file(),
        })
    return items


def resolve_mustgather_path(bundle_path: str) -> str:
    """Resolve user path to the must-gather data root (hash subdirectory if needed)."""
    path = os.path.abspath(os.path.expanduser(bundle_path.strip()))
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path not found: {path}")

    if os.path.isfile(path):
        from workshop_mcp_server.src.tools.mustgather_analyzer_tool import MustGatherAnalyzer
        path = MustGatherAnalyzer()._extract_bundle(path)

    return _resolve_data_root(path)


def _has_mg_markers(directory: str) -> bool:
    from workshop_mcp_server.src.tools.mustgather_paths import has_mustgather_markers
    return has_mustgather_markers(directory)


def _resolve_data_root(path: str) -> str:
    from workshop_mcp_server.src.tools.mustgather_paths import resolve_mustgather_data_root
    return resolve_mustgather_data_root(path)


def run_script(
    script_id: str,
    bundle_path: str,
    namespace: Optional[str] = None,
    problems_only: bool = False,
    event_type: Optional[str] = None,
    count: Optional[int] = None,
    timeout: int = 180,
) -> Dict[str, Any]:
    """Run a single must-gather analysis script."""
    if script_id not in SCRIPT_CATALOG:
        return {"status": "error", "error": f"Unknown script: {script_id}"}

    meta = SCRIPT_CATALOG[script_id]
    script_file = _SCRIPTS_DIR / meta["script"]
    if not script_file.is_file():
        return {"status": "error", "error": f"Script not found: {script_file}"}

    try:
        mg_path = resolve_mustgather_path(bundle_path)
    except Exception as e:
        return {"status": "error", "error": str(e)}

    if not _has_mg_markers(mg_path):
        return {
            "status": "error",
            "error": (
                "Could not find must-gather data (cluster-scoped-resources/ or namespaces/). "
                f"Resolved path: {mg_path}"
            ),
        }

    cmd = [sys.executable, str(script_file), mg_path]
    opts = meta.get("options", [])

    if "namespace" in opts and namespace:
        cmd.extend(["--namespace", namespace])
    if "problems_only" in opts and problems_only:
        cmd.append("--problems-only")
    if "event_type" in opts and event_type:
        cmd.extend(["--type", event_type])
    if "count" in opts and count:
        cmd.extend(["--count", str(count)])

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(_SCRIPTS_DIR),
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "script_id": script_id,
            "script_label": meta["label"],
            "resolved_path": mg_path,
            "command": " ".join(cmd),
            "exit_code": proc.returncode,
            "output": output.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": f"Script timed out after {timeout}s"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_preset(preset_id: str, bundle_path: str) -> Dict[str, Any]:
    """Run a preset bundle of scripts."""
    if preset_id not in QUICK_PRESETS:
        return {"status": "error", "error": f"Unknown preset: {preset_id}"}

    preset = QUICK_PRESETS[preset_id]
    results = []
    for script_id in preset["scripts"]:
        kwargs = {}
        if script_id == "pods":
            if preset.get("pods_namespace"):
                kwargs["namespace"] = preset["pods_namespace"]
            if preset.get("pods_problems_only"):
                kwargs["problems_only"] = True
        if script_id == "nodes" and preset.get("nodes_problems_only"):
            kwargs["problems_only"] = True
        if script_id == "events" and preset.get("events_type"):
            kwargs["event_type"] = preset["events_type"]
        results.append(run_script(script_id, bundle_path, **kwargs))

    return {
        "status": "success",
        "preset": preset_id,
        "preset_label": preset["label"],
        "results": results,
    }
