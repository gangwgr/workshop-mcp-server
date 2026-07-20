"""Shared must-gather bundle path resolution for SRE analyzer and script runner."""

import os
from typing import List, Tuple


def has_mustgather_markers(directory: str) -> bool:
    return (
        os.path.isdir(os.path.join(directory, "cluster-scoped-resources"))
        or os.path.isdir(os.path.join(directory, "namespaces"))
    )


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
