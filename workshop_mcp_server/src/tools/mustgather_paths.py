"""Shared must-gather bundle path resolution for SRE analyzer and script runner."""

import os
import tarfile
import zipfile
from typing import List, Tuple


def has_mustgather_markers(directory: str) -> bool:
    """True when directory looks like a must-gather root with actual resource YAML."""
    csr = os.path.join(directory, "cluster-scoped-resources")
    ns = os.path.join(directory, "namespaces")
    if not os.path.isdir(csr) and not os.path.isdir(ns):
        return False

    yaml_count = 0
    for root in (csr, ns):
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for name in files:
                if name.endswith((".yaml", ".yml")):
                    yaml_count += 1
                    if yaml_count >= 1:
                        return True
    return False


def has_core_cluster_resources(directory: str) -> bool:
    """True when standard ClusterVersion / ClusterOperator YAML is present."""
    cfg = os.path.join(directory, "cluster-scoped-resources", "config.openshift.io")
    if not os.path.isdir(cfg):
        return False

    co_list = os.path.join(cfg, "clusteroperators.yaml")
    co_dir = os.path.join(cfg, "clusteroperators")
    cv_list = os.path.join(cfg, "clusterversions.yaml")
    cv_file = os.path.join(cfg, "clusterversions", "version.yaml")

    return (
        os.path.isfile(co_list)
        or os.path.isdir(co_dir)
        or os.path.isfile(cv_list)
        or os.path.isfile(cv_file)
    )


def score_data_root(directory: str) -> int:
    """Higher score = better must-gather data root candidate."""
    score = 0
    if has_mustgather_markers(directory):
        score += 1
    if has_core_cluster_resources(directory):
        score += 100
    if os.path.isdir(os.path.join(directory, "namespaces")):
        score += 10
    if os.path.isdir(os.path.join(directory, "cluster-scoped-resources", "core", "nodes")):
        score += 5
    return score


def resolve_mustgather_data_root(path: str) -> str:
    """Find the best subdirectory that contains must-gather resource YAML."""
    best_path = path
    best_score = score_data_root(path)

    queue: List[Tuple[str, int]] = [(path, 0)]
    max_depth = 8

    while queue:
        current, depth = queue.pop(0)
        if depth > max_depth:
            continue
        try:
            entries = sorted(os.listdir(current))
        except OSError:
            continue
        for name in entries:
            candidate = os.path.join(current, name)
            if not os.path.isdir(candidate):
                continue
            candidate_score = score_data_root(candidate)
            if candidate_score > best_score:
                best_score = candidate_score
                best_path = candidate
            if depth < max_depth:
                queue.append((candidate, depth + 1))

    return best_path


def _archive_member_paths(archive_path: str) -> List[str]:
    if archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            return [info.filename for info in zf.infolist() if not info.is_dir()]
    with tarfile.open(archive_path, "r:*") as tar:
        return [member.name for member in tar.getmembers() if member.isfile()]


def extraction_is_complete(extract_dir: str, archive_path: str) -> bool:
    """Return False when a cached extraction is missing expected cluster-scoped YAML."""
    root = resolve_mustgather_data_root(extract_dir)
    if not has_mustgather_markers(root):
        return False

    try:
        member_paths = _archive_member_paths(archive_path)
    except Exception:
        return has_core_cluster_resources(root)

    archive_has_core = any(
        "config.openshift.io/clusteroperators" in path or "config.openshift.io/clusterversions" in path
        for path in member_paths
    )
    if archive_has_core and not has_core_cluster_resources(root):
        return False

    archive_file_count = len(member_paths)
    extracted_file_count = sum(len(files) for _, _, files in os.walk(extract_dir))
    if archive_file_count > 100 and extracted_file_count < archive_file_count * 0.85:
        return False

    return True
