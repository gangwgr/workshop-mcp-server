"""Download and cache must-gather bundles from URLs."""

import hashlib
import json
import os
import subprocess
import tempfile
from typing import Optional
from urllib.parse import urlparse, unquote


def _cache_dir() -> str:
    path = os.path.join(tempfile.gettempdir(), "mcp_mustgather_downloads")
    os.makedirs(path, exist_ok=True)
    return path


def bundle_cache_path(url: str) -> str:
    """Stable local path for a must-gather URL (unique per URL)."""
    parsed = urlparse(url)
    basename = os.path.basename(unquote(parsed.path)) or "must-gather-bundle"
    ext = ""
    for suffix in (".tar.gz", ".tgz", ".tar", ".zip"):
        if basename.endswith(suffix):
            ext = suffix
            basename = basename[: -len(suffix)]
            break
    if not ext:
        ext = ".tar"

    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in basename)[:40]
    filename = f"{safe_name}-{url_hash}{ext}"
    return os.path.join(_cache_dir(), filename)


def _meta_path(local_path: str) -> str:
    return local_path + ".meta.json"


def _read_meta(local_path: str) -> Optional[dict]:
    meta_file = _meta_path(local_path)
    if not os.path.isfile(meta_file):
        return None
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_meta(local_path: str, url: str) -> None:
    meta = {
        "url": url,
        "size": os.path.getsize(local_path),
        "mtime": os.path.getmtime(local_path),
    }
    with open(_meta_path(local_path), "w", encoding="utf-8") as f:
        json.dump(meta, f)


def _invalidate_extraction(local_path: str) -> None:
    extract_dir = local_path + "_extracted"
    stamp_file = local_path + ".extract_stamp"
    for path in (extract_dir, stamp_file):
        if os.path.isdir(path):
            import shutil
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


def download_bundle_from_url(url: str, force: bool = False) -> str:
    """Download a must-gather bundle from URL using curl (handles redirects/GCS)."""
    local_path = bundle_cache_path(url)

    if not force and os.path.exists(local_path):
        meta = _read_meta(local_path)
        size = os.path.getsize(local_path)
        if meta and meta.get("url") == url and size > 1024:
            return local_path

    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    tmp_path = local_path + ".part"

    result = subprocess.run(
        ["curl", "-L", "-f", "-s", "-o", tmp_path, "--max-time", "600", url],
        capture_output=True,
        text=True,
        timeout=660,
    )

    if result.returncode != 0:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        error_msg = result.stderr.strip() or f"curl failed with exit code {result.returncode}"
        raise ValueError(f"Download failed: {error_msg}")

    if not os.path.exists(tmp_path):
        raise ValueError("Download produced no file")

    file_size = os.path.getsize(tmp_path)
    if file_size < 1024:
        os.remove(tmp_path)
        raise ValueError(
            f"Downloaded file is too small ({file_size} bytes) — "
            "likely not a valid must-gather bundle or URL requires authentication"
        )

    if os.path.exists(local_path):
        _invalidate_extraction(local_path)
        os.remove(local_path)

    os.replace(tmp_path, local_path)
    _write_meta(local_path, url)
    _invalidate_extraction(local_path)
    return local_path
