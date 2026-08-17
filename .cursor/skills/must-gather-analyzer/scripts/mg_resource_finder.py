"""Shared must-gather resource discovery with fallbacks for partial/modern bundles."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


PARTIAL_BUNDLE_HINT = (
    "This bundle appears to be a partial/targeted must-gather — standard cluster-scoped "
    "API dumps were not collected. Re-run with a full gather:\n"
    "  oc adm must-gather\n"
    "Or at minimum:\n"
    "  oc adm must-gather -- gather_cluster_resources"
)

FALLBACK_HINT = (
    "ClusterVersion/ClusterOperator YAML not found in expected paths — "
    "using fallback sources (CVO logs or inferred pod status)."
)

_SKIP_POD_PREFIXES = ("installer-", "revision-pruner", "etcd-guard-", "kube-apiserver-guard-", "guard-")


def load_yaml_docs(file_path: Path) -> List[Dict[str, Any]]:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return [doc for doc in yaml.safe_load_all(f) if isinstance(doc, dict)]
    except Exception:
        return []


def _extract_resources(file_path: Path, kind: str) -> List[Dict[str, Any]]:
    """Extract resources of `kind` from a single doc or List (items[]) YAML file."""
    found: List[Dict[str, Any]] = []
    if not file_path.is_file():
        return found
    for doc in load_yaml_docs(file_path):
        if doc.get("kind") == kind:
            found.append(doc)
        for item in doc.get("items") or []:
            if isinstance(item, dict) and item.get("kind") == kind:
                found.append(item)
    return found


def standard_paths_exist(base_path: Path) -> Dict[str, bool]:
    csr = base_path / "cluster-scoped-resources"
    cfg = csr / "config.openshift.io"
    return {
        "clusterversion": (
            (cfg / "clusterversions" / "version.yaml").is_file()
            or (cfg / "clusterversions.yaml").is_file()
        ),
        "clusteroperators": (
            (cfg / "clusteroperators").is_dir()
            or (cfg / "clusteroperators.yaml").is_file()
        ),
        "nodes": (
            (csr / "core" / "nodes").is_dir()
            or (cfg / "nodes.yaml").is_file()
        ),
        "namespaces": (base_path / "namespaces").is_dir(),
    }


def detect_bundle_format(base_path: Path) -> str:
    paths = standard_paths_exist(base_path)
    cfg = base_path / "cluster-scoped-resources" / "config.openshift.io"
    if (cfg / "clusterversions.yaml").is_file() or (cfg / "clusteroperators.yaml").is_file():
        return "list"
    if paths["clusterversion"] and paths["clusteroperators"]:
        return "legacy"
    if paths["namespaces"] and not paths["clusterversion"]:
        return "partial"
    return "unknown"


def bundle_completeness(base_path: Path) -> Dict[str, Any]:
    paths = standard_paths_exist(base_path)
    fmt = detect_bundle_format(base_path)
    missing = [k for k, ok in paths.items() if not ok and k != "namespaces"]
    hint = PARTIAL_BUNDLE_HINT if fmt == "partial" else ""
    return {
        "format": fmt,
        "partial": fmt == "partial",
        "modern": False,
        "missing": missing,
        "paths": paths,
        "hint": hint,
    }


def find_clusterversion_doc(base_path: Path) -> Optional[Dict[str, Any]]:
    cfg = base_path / "cluster-scoped-resources" / "config.openshift.io"
    # Newer gather: aggregated List file
    list_file = cfg / "clusterversions.yaml"
    if list_file.is_file():
        items = _extract_resources(list_file, "ClusterVersion")
        if items:
            return items[0]
    # Legacy: one file per resource
    for pattern in (
        "cluster-scoped-resources/config.openshift.io/clusterversions/version.yaml",
        "cluster-scoped-resources/config.openshift.io/clusterversions/*.yaml",
    ):
        for cv_file in base_path.glob(pattern):
            for doc in _extract_resources(cv_file, "ClusterVersion"):
                return doc
    return find_clusterversion_from_cvo_logs(base_path)


def find_clusterversion_from_cvo_logs(base_path: Path) -> Optional[Dict[str, Any]]:
    """Build a synthetic ClusterVersion dict from CVO pod logs when YAML is absent."""
    log_globs = [
        "namespaces/openshift-cluster-version/pods/*/cluster-version-operator/*/logs/current.log",
    ]
    for pattern in log_globs:
        for log_file in base_path.glob(pattern):
            try:
                text = log_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for line in reversed(text.splitlines()):
                if "PayloadLoaded" in line or "RetrievePayload" in line or "Loading payload" in line:
                    vm = re.search(r'version="([^"]+)"', line)
                    im = re.search(r'image="([^"]+)"', line)
                    if vm:
                        return _synthetic_clusterversion(vm.group(1), im.group(1) if im else "", str(log_file))
    return None


def _synthetic_clusterversion(version: str, image: str, source: str) -> Dict[str, Any]:
    return {
        "kind": "ClusterVersion",
        "metadata": {"name": "version"},
        "status": {
            "desired": {"version": version, "image": image},
            "conditions": [
                {"type": "Progressing", "status": "Unknown", "message": f"Parsed from CVO logs ({source})"},
            ],
        },
        "_source": "cvo_logs",
    }


def find_clusteroperator_docs(base_path: Path) -> List[Dict[str, Any]]:
    operators: List[Dict[str, Any]] = []
    seen = set()
    cfg = base_path / "cluster-scoped-resources" / "config.openshift.io"
    list_file = cfg / "clusteroperators.yaml"
    if list_file.is_file():
        for doc in _extract_resources(list_file, "ClusterOperator"):
            name = doc.get("metadata", {}).get("name")
            if name and name not in seen:
                seen.add(name)
                operators.append(doc)
    for co_file in cfg.glob("clusteroperators/*.yaml"):
        for doc in _extract_resources(co_file, "ClusterOperator"):
            name = doc.get("metadata", {}).get("name")
            if name and name not in seen:
                seen.add(name)
                operators.append(doc)
    return operators


def find_node_docs(base_path: Path) -> List[Dict[str, Any]]:
    """Find core/v1 Node objects (not config.openshift.io Node CR)."""
    nodes: List[Dict[str, Any]] = []
    seen = set()
    for node_file in (base_path / "cluster-scoped-resources" / "core" / "nodes").glob("*.yaml"):
        if node_file.name == "nodes.yaml":
            continue
        for doc in load_yaml_docs(node_file):
            if doc.get("kind") != "Node" or doc.get("apiVersion", "").startswith("config.openshift.io"):
                continue
            name = doc.get("metadata", {}).get("name")
            if name and name not in seen:
                seen.add(name)
                nodes.append(doc)
    # Some gathers store nodes only in a List under core/
    list_file = base_path / "cluster-scoped-resources" / "core" / "nodes" / "nodes.yaml"
    if list_file.is_file():
        for doc in _extract_resources(list_file, "Node"):
            name = doc.get("metadata", {}).get("name")
            if name and name not in seen and not str(doc.get("apiVersion", "")).startswith("config.openshift.io"):
                seen.add(name)
                nodes.append(doc)
    return nodes


def _skip_pod_name(name: str) -> bool:
    return any(name.startswith(p) for p in _SKIP_POD_PREFIXES)


def infer_nodes_from_layout(base_path: Path) -> List[Dict[str, str]]:
    """Infer node list when Node YAML is missing."""
    inferred: Dict[str, Dict[str, str]] = {}

    nodes_dir = base_path / "nodes"
    if nodes_dir.is_dir():
        for entry in nodes_dir.iterdir():
            if entry.is_dir() and entry.name not in {"debug"}:
                inferred[entry.name] = {
                    "name": entry.name,
                    "status": "Present (inferred)",
                    "roles": "worker",
                    "age": "",
                    "version": "",
                    "source": "nodes/ directory",
                }

    for pod_dir in base_path.glob("namespaces/openshift-etcd/pods/etcd-*"):
        name = pod_dir.name
        if name.startswith("etcd-guard-") or name.startswith("revision-pruner"):
            continue
        host = name.replace("etcd-", "", 1)
        if host and host not in inferred:
            inferred[host] = {
                "name": host,
                "status": "Present (inferred)",
                "roles": "master,etcd",
                "age": "",
                "version": "",
                "source": "openshift-etcd static pod",
            }

    for pod_dir in base_path.glob("namespaces/openshift-kube-apiserver/pods/kube-apiserver-*"):
        name = pod_dir.name
        if name.startswith("kube-apiserver-guard-") or name.startswith("revision-pruner"):
            continue
        host = name.replace("kube-apiserver-", "", 1)
        if host and host not in inferred:
            inferred[host] = {
                "name": host,
                "status": "Present (inferred)",
                "roles": "master",
                "age": "",
                "version": "",
                "source": "kube-apiserver static pod",
            }

    return sorted(inferred.values(), key=lambda x: x["name"])


def infer_operators_from_namespaces(base_path: Path) -> List[Dict[str, str]]:
    """Summarize operator health from operator namespace pods when CO YAML is missing."""
    rows: List[Dict[str, str]] = []
    ns_dirs = sorted(base_path.glob("namespaces/openshift-*-operator"))
    static_ns = [
        base_path / "namespaces/openshift-etcd",
        base_path / "namespaces/openshift-kube-apiserver",
        base_path / "namespaces/openshift-kube-controller-manager",
        base_path / "namespaces/openshift-kube-scheduler",
    ]

    for ns_dir in list(ns_dirs) + [p for p in static_ns if p.is_dir()]:
        ns = ns_dir.name
        op_name = ns.replace("openshift-", "").replace("-operator", "")
        if ns == "openshift-etcd":
            op_name = "etcd"
        elif ns == "openshift-kube-apiserver":
            op_name = "kube-apiserver"
        elif ns == "openshift-kube-controller-manager":
            op_name = "kube-controller-manager"
        elif ns == "openshift-kube-scheduler":
            op_name = "kube-scheduler"

        pod_dirs = [p for p in ns_dir.glob("pods/*") if not _skip_pod_name(p.name)]
        total = len(pod_dirs)
        if total == 0:
            continue

        running = 0
        problems = []
        for pod_dir in pod_dirs:
            yaml_files = list(pod_dir.glob("*.yaml")) or list(pod_dir.glob("*/*.yaml"))
            if not yaml_files:
                continue
            docs = load_yaml_docs(yaml_files[0])
            if not docs or docs[0].get("kind") != "Pod":
                continue
            pod = docs[0]
            phase = pod.get("status", {}).get("phase", "Unknown")
            pod_name = pod.get("metadata", {}).get("name", pod_dir.name)
            if phase == "Running":
                running += 1
            elif phase not in ("Succeeded",):
                problems.append(f"{pod_name}={phase}")

        degraded = "True" if problems else "False"
        available = "True" if running > 0 and not problems else ("False" if problems else "True")
        message = ", ".join(problems[:3]) if problems else f"{running}/{total} pods Running (inferred)"
        rows.append({
            "name": op_name[:42],
            "version": "(inferred)",
            "available": available,
            "progressing": "Unknown",
            "degraded": degraded,
            "since": "",
            "message": message,
        })
    return rows
