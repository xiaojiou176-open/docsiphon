# ====================
# Storage
# ====================
from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
import threading
import heapq
import shutil
from contextlib import ExitStack
from datetime import datetime, timezone
from typing import Optional, Tuple

from .config import RunConfig
from .models import PageRecord
from .utils import safe_relative_path, safe_relative_path_from_base, sanitize_segment


LOG = logging.getLogger(__name__)
_MANIFEST_SORT_CHUNK_SIZE = 20000
_SNAPSHOT_LOCK = threading.Lock()
_SNAPSHOT_STATE: dict[str, dict[str, int]] = {}


# ====================
# Path mapping
# ====================

def _ensure_md_extension(rel_path: str) -> str:
    if rel_path.endswith(".md") or rel_path.endswith(".md.txt"):
        return rel_path
    return rel_path + ".md"


def build_output_path(url: str, config: RunConfig) -> str:
    if config.site_root:
        site_root = sanitize_segment(config.site_root)
        rel = safe_relative_path_from_base(
            url,
            config.base_url,
            site_root,
            config.ignore_query_params,
            config.ignore_query_prefixes,
        )
        return os.path.join(config.output_dir, site_root, _ensure_md_extension(rel))
    rel = safe_relative_path(url, config.ignore_query_params, config.ignore_query_prefixes)
    return os.path.join(config.output_dir, _ensure_md_extension(rel))


def build_html_output_path(url: str, config: RunConfig) -> str:
    md_path = build_output_path(url, config)
    if md_path.endswith(".md.txt"):
        return md_path[: -len(".md.txt")] + ".html"
    if md_path.endswith(".md"):
        return md_path[: -len(".md")] + ".html"
    return md_path + ".html"


def _frontmatter(url: str, fetched_url: str, include_timestamp: bool) -> str:
    lines = [
        "---",
        f"source_url: {url}",
        f"fetched_url: {fetched_url}",
        "---",
        "",
    ]
    if include_timestamp:
        ts = datetime.now(timezone.utc).isoformat()
        lines.insert(3, f"fetched_at_utc: {ts}")
    return "\n".join(lines)


def _atomic_write(path: str, content: str) -> None:
    dir_path = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=dir_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception as exc:
        try:
            os.unlink(tmp_path)
        except Exception as cleanup_exc:
            LOG.debug("temporary file cleanup failed for %s: %s", tmp_path, cleanup_exc)
        LOG.debug("atomic write failed for %s: %s", path, exc)
        raise


# ====================
# Writers
# ====================

def write_markdown(content: str, url: str, fetched_url: str, config: RunConfig) -> Tuple[Optional[str], Optional[str]]:
    path = build_output_path(url, config)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = content
        if config.frontmatter:
            payload = _frontmatter(url, fetched_url, config.frontmatter_timestamp) + content
        _atomic_write(path, payload)
        return path, None
    except Exception as exc:
        LOG.debug("write_markdown failed for %s: %s", path, exc)
        return None, str(exc)


def write_html(content: str, url: str, config: RunConfig) -> Tuple[Optional[str], Optional[str]]:
    path = build_html_output_path(url, config)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _atomic_write(path, content)
        return path, None
    except Exception as exc:
        LOG.debug("write_html failed for %s: %s", path, exc)
        return None, str(exc)


def _truncate_content(content: str, max_bytes: int, head_ratio: float) -> str:
    if max_bytes <= 0:
        return content
    raw = content.encode("utf-8", errors="ignore")
    if len(raw) <= max_bytes:
        return content
    ratio = head_ratio if 0.1 <= head_ratio <= 0.9 else 0.7
    marker = b"\n...[truncated]...\n"
    if max_bytes <= len(marker):
        return raw[:max_bytes].decode("utf-8", errors="ignore")
    budget = max_bytes - len(marker)
    head_size = int(budget * ratio)
    tail_size = budget - head_size
    head = raw[:head_size]
    tail = raw[-tail_size:] if tail_size > 0 else b""
    trimmed = head + marker + tail
    return trimmed.decode("utf-8", errors="ignore")


def write_error_snapshot(
    report_dir: str,
    url: str,
    content: str,
    suffix: str,
    run_id: str = "",
    max_bytes: int = 200000,
    head_ratio: float = 0.7,
    max_files: int = 0,
    max_total_bytes: int = 0,
) -> Tuple[Optional[str], Optional[str]]:
    safe_dir = os.path.join(report_dir, "_errors")
    digest = hashlib.sha1(url.encode("utf-8", errors="ignore")).hexdigest()[:10]
    name_parts = [sanitize_segment(digest), suffix]
    if run_id:
        name_parts.insert(0, sanitize_segment(run_id))
    name = "_".join(name_parts) + ".txt"
    path = os.path.join(safe_dir, name)
    try:
        os.makedirs(safe_dir, exist_ok=True)
        payload = _truncate_content(content, max_bytes, head_ratio)
        payload_size = len(payload.encode("utf-8", errors="ignore"))
        reserved = False
        if max_files > 0 or max_total_bytes > 0:
            with _SNAPSHOT_LOCK:
                state = _SNAPSHOT_STATE.setdefault(report_dir, {"files": 0, "bytes": 0})
                if max_files > 0 and state["files"] >= max_files:
                    return None, "snapshot quota exceeded (files)"
                if max_total_bytes > 0 and state["bytes"] + payload_size > max_total_bytes:
                    return None, "snapshot quota exceeded (bytes)"
                state["files"] += 1
                state["bytes"] += payload_size
                reserved = True
        _atomic_write(path, payload)
        return path, None
    except Exception as exc:
        if reserved and (max_files > 0 or max_total_bytes > 0):
            with _SNAPSHOT_LOCK:
                state = _SNAPSHOT_STATE.get(report_dir)
                if state:
                    state["files"] = max(state["files"] - 1, 0)
                    state["bytes"] = max(state["bytes"] - payload_size, 0)
        LOG.debug("write_error_snapshot failed for %s: %s", path, exc)
        return None, str(exc)


def load_manifest_ok_urls(output_dir: str) -> set[str]:
    path = os.path.join(output_dir, "manifest.jsonl")
    ok_urls: set[str] = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    LOG.debug("manifest row decode failed in %s: %s", path, exc)
                    continue
                if payload.get("status") == "ok" and isinstance(payload.get("url"), str):
                    ok_urls.add(payload["url"])
    except FileNotFoundError:
        return ok_urls
    except Exception as exc:
        LOG.debug("manifest read failed: %s", exc)
        return ok_urls
    return ok_urls


def load_manifest_cache(
    output_dir: str,
    allowed_urls: Optional[set[str]] = None,
    max_entries: int = 0,
) -> dict[str, dict[str, str]]:
    path = os.path.join(output_dir, "manifest.jsonl")
    cache: dict[str, dict[str, str]] = {}
    remaining = set(allowed_urls) if allowed_urls else None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    LOG.debug("manifest cache row decode failed in %s: %s", path, exc)
                    continue
                url = payload.get("url")
                if not isinstance(url, str):
                    continue
                if remaining is not None and url not in remaining:
                    continue
                entry: dict[str, str] = {}
                for key in ("etag", "last_modified", "content_hash"):
                    value = payload.get(key)
                    if isinstance(value, str):
                        entry[key] = value
                if entry:
                    cache[url] = entry
                    if remaining is not None:
                        remaining.discard(url)
                        if not remaining:
                            break
                    if max_entries > 0 and len(cache) >= max_entries:
                        break
    except FileNotFoundError:
        return cache
    except Exception as exc:
        LOG.debug("manifest cache read failed: %s", exc)
        return cache
    return cache


class ManifestWriter:
    def __init__(self, output_dir: str, sorted_mode: bool = False) -> None:
        self._path = os.path.join(output_dir, "manifest.jsonl")
        self._lock = threading.Lock()
        self._sorted_mode = sorted_mode
        self._buffer: list[dict] | None = [] if sorted_mode else None
        self._chunk_paths: list[str] = []
        self._chunk_dir: Optional[str] = None
        self._finalized: bool = False

    def write(self, record: PageRecord) -> None:
        data = {}
        for key, value in record.__dict__.items():
            if hasattr(value, "value"):
                data[key] = value.value
            else:
                data[key] = value
        if "manifest_version" not in data:
            data["manifest_version"] = "1.1"
        if not _validate_manifest_payload(data):
            return
        try:
            payload = json.dumps(data, ensure_ascii=False)
        except Exception as exc:
            LOG.debug("manifest json serialization failed: %s", exc)
            return
        with self._lock:
            if self._sorted_mode and self._buffer is not None:
                self._buffer.append(data)
                if len(self._buffer) >= _MANIFEST_SORT_CHUNK_SIZE:
                    self._write_sorted_chunk(self._buffer)
                    self._buffer.clear()
                return
            try:
                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(payload + "\n")
            except Exception as exc:
                LOG.debug("manifest write failed: %s", exc)
                return

    def finalize(self) -> None:
        if not self._sorted_mode or self._buffer is None:
            return
        if self._finalized:
            return
        with self._lock:
            records = list(self._buffer)
            self._buffer.clear()
        if records:
            self._write_sorted_chunk(records)
        if not self._chunk_paths:
            try:
                with open(self._path, "w", encoding="utf-8") as f:
                    for record in sorted(records, key=lambda item: item.get("url") or ""):
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
            except Exception as exc:
                LOG.debug("manifest finalize failed: %s", exc)
            self._finalized = True
            return
        try:
            self._merge_sorted_chunks()
        finally:
            self._cleanup_chunks()
            self._finalized = True

    def _write_sorted_chunk(self, records: list[dict]) -> None:
        records.sort(key=lambda item: item.get("url") or "")
        if self._chunk_dir is None:
            self._chunk_dir = tempfile.mkdtemp(prefix="manifest_chunks_")
        fd, path = tempfile.mkstemp(prefix="chunk_", dir=self._chunk_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._chunk_paths.append(path)
        except Exception as exc:
            LOG.debug("manifest chunk write failed: %s", exc)
            try:
                os.unlink(path)
            except Exception as cleanup_exc:
                LOG.debug("manifest chunk cleanup failed for %s: %s", path, cleanup_exc)

    def _merge_sorted_chunks(self) -> None:
        heap: list[tuple[str, int, str]] = []
        try:
            with ExitStack() as stack:
                files = []
                for idx, path in enumerate(self._chunk_paths):
                    chunk_file = stack.enter_context(open(path, "r", encoding="utf-8"))
                    files.append(chunk_file)
                    line = chunk_file.readline()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError as decode_exc:
                        LOG.debug("manifest chunk decode failed for %s: %s", path, decode_exc)
                        payload = {}
                    url = payload.get("url") if isinstance(payload, dict) else ""
                    heapq.heappush(heap, (str(url or ""), idx, line))
                with open(self._path, "w", encoding="utf-8") as out:
                    while heap:
                        _, idx, line = heapq.heappop(heap)
                        out.write(line.rstrip("\n") + "\n")
                        next_line = files[idx].readline()
                        if not next_line:
                            continue
                        try:
                            payload = json.loads(next_line)
                        except json.JSONDecodeError as decode_exc:
                            LOG.debug(
                                "manifest chunk decode failed while merging %s: %s",
                                self._chunk_paths[idx],
                                decode_exc,
                            )
                            payload = {}
                        url = payload.get("url") if isinstance(payload, dict) else ""
                        heapq.heappush(heap, (str(url or ""), idx, next_line))
        except Exception as exc:
            LOG.debug("manifest merge failed: %s", exc)

    def _cleanup_chunks(self) -> None:
        for path in self._chunk_paths:
            try:
                os.unlink(path)
            except Exception as exc:
                LOG.debug("manifest chunk unlink failed for %s: %s", path, exc)
        self._chunk_paths.clear()
        if self._chunk_dir:
            try:
                shutil.rmtree(self._chunk_dir, ignore_errors=True)
            except Exception as exc:
                LOG.debug("manifest chunk dir cleanup failed for %s: %s", self._chunk_dir, exc)
            self._chunk_dir = None


def _validate_manifest_payload(data: dict) -> bool:
    required = {
        "manifest_version": str,
        "url": str,
        "status": str,
        "fetch_kind": str,
        "source": str,
    }
    for key, expected in required.items():
        value = data.get(key)
        if not isinstance(value, expected) or not value:
            LOG.debug("manifest schema invalid for %s", key)
            return False
    return True
