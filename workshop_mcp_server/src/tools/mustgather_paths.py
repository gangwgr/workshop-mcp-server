"""Shared must-gather bundle path resolution for SRE analyzer and script runner."""

import os
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


def resolve_mustgather_data_root(path: str) -> str:
    """Find the subdirectory that contains cluster-scoped-resources/ or namespaces/."""
    if has_mustgather_markers(path):
        return path

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
            if has_mustgather_markers(candidate):
                return candidate
            queue.append((candidate, depth + 1))

    return path
