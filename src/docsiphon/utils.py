# ====================
# Utilities
# ====================
from __future__ import annotations

import hashlib
import os
import random
import re
import socket
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Pattern, Tuple
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse

import requests


_INVALID_WIN_CHARS = r"[<>:\"/\\|?*\x00-\x1f]"
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


@dataclass
class RateLimiter:
    rate_per_sec: float
    _last_ts: float = 0.0

    def wait(self) -> None:
        if self.rate_per_sec <= 0:
            return
        min_interval = 1.0 / self.rate_per_sec
        now = time.monotonic()
        delta = now - self._last_ts
        if delta < min_interval:
            time.sleep(min_interval - delta)
        self._last_ts = time.monotonic()


@dataclass
class HostRateLimiter:
    rate_per_sec: float
    _limiters: Dict[str, RateLimiter] = None
    _locks: Dict[str, "threading.Lock"] = None
    _global_lock: "threading.Lock" = None

    def __post_init__(self) -> None:
        import threading

        if self._limiters is None:
            self._limiters = {}
        if self._locks is None:
            self._locks = {}
        if self._global_lock is None:
            self._global_lock = threading.Lock()

    def wait(self, host: str) -> None:
        if self.rate_per_sec <= 0:
            return
        import threading

        with self._global_lock:
            limiter = self._limiters.get(host)
            if limiter is None:
                limiter = RateLimiter(self.rate_per_sec)
                self._limiters[host] = limiter
                self._locks[host] = threading.Lock()
            host_lock = self._locks[host]
        with host_lock:
            limiter.wait()


@dataclass
class HostConcurrencyLimiter:
    max_concurrency: int
    _semaphores: Dict[str, "threading.Semaphore"] = None
    _lock: "threading.Lock" = None

    def __post_init__(self) -> None:
        import threading

        if self._semaphores is None:
            self._semaphores = {}
        if self._lock is None:
            self._lock = threading.Lock()

    @contextmanager
    def slot(self, host: str):
        if self.max_concurrency <= 0:
            yield
            return
        import threading

        with self._lock:
            sem = self._semaphores.get(host)
            if sem is None:
                sem = threading.Semaphore(self.max_concurrency)
                self._semaphores[host] = sem
        sem.acquire()
        try:
            yield
        finally:
            sem.release()


# ====================
# Resource filtering
# ====================

DEFAULT_EXCLUDE_EXTS = frozenset(
    {
        ".css",
        ".gif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".js",
        ".map",
        ".mp4",
        ".pdf",
        ".png",
        ".svg",
        ".webp",
        ".zip",
        ".gz",
        ".tar",
        ".tgz",
    }
)


def normalize_extension(ext: str) -> str:
    cleaned = ext.strip().lower()
    if not cleaned:
        return ""
    if not cleaned.startswith("."):
        cleaned = "." + cleaned
    return cleaned


def build_exclude_exts(extra_exts: Iterable[str] | None) -> frozenset[str]:
    exts = set(DEFAULT_EXCLUDE_EXTS)
    if not extra_exts:
        return frozenset(exts)
    for raw in extra_exts:
        if not raw:
            continue
        for part in raw.split(","):
            normalized = normalize_extension(part)
            if normalized:
                exts.add(normalized)
    return frozenset(exts)


def is_excluded_by_extension(url: str, exclude_exts: Iterable[str]) -> bool:
    path = urlparse(url).path.lower()
    _, ext = os.path.splitext(path)
    if not ext:
        return False
    return ext in exclude_exts


# ====================
# URL helpers
# ====================

def normalize_query_with_ignore(
    query: str, ignore_params: Tuple[str, ...], ignore_prefixes: Tuple[str, ...]
) -> str:
    if not query:
        return ""
    pairs = parse_qsl(query, keep_blank_values=True)
    filtered = []
    for key, value in pairs:
        if ignore_params and key in ignore_params:
            continue
        if ignore_prefixes and any(key.startswith(prefix) for prefix in ignore_prefixes):
            continue
        filtered.append((key, value))
    filtered.sort()
    return urlencode(filtered, doseq=True)


def normalize_url(
    url: str,
    ignore_query_params: Tuple[str, ...] | None = None,
    ignore_query_prefixes: Tuple[str, ...] | None = None,
) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    netloc = parsed.netloc.lower()
    if parsed.scheme.lower() == "http" and netloc.endswith(":80"):
        netloc = netloc[: -len(":80")]
    if parsed.scheme.lower() == "https" and netloc.endswith(":443"):
        netloc = netloc[: -len(":443")]
    ignore_params = ignore_query_params or ()
    ignore_prefixes = ignore_query_prefixes or ()
    cleaned = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=netloc,
        path=path,
        fragment="",
        query=normalize_query_with_ignore(parsed.query, ignore_params, ignore_prefixes),
    )
    return urlunparse(cleaned)


def min_nonzero(a: float, b: float) -> float:
    if a <= 0:
        return b
    if b <= 0:
        return a
    return min(a, b)


def compute_backoff(attempt: int, base: float, max_delay: float, jitter: float) -> float:
    if attempt <= 0:
        return 0.0
    delay = base * (2 ** (attempt - 1))
    if max_delay > 0:
        delay = min(delay, max_delay)
    if jitter > 0:
        delay += random.uniform(0.0, jitter)
    return max(delay, 0.0)


def same_origin(url_a: str, url_b: str) -> bool:
    pa = urlparse(url_a)
    pb = urlparse(url_b)
    return pa.scheme == pb.scheme and pa.netloc == pb.netloc


def candidate_base_paths(base_url: str) -> List[str]:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path.strip("/")
    segments = [seg for seg in path.split("/") if seg]

    candidates = [origin]
    if segments:
        candidates.append(origin + "/" + segments[0])
    if len(segments) >= 2:
        candidates.append(origin + "/" + "/".join(segments[:2]))

    # Deduplicate; try most specific path first (avoids root llms.txt redirecting
    # to a different page, e.g. code.claude.com/llms.txt -> product page)
    seen = set()
    result = []
    for c in reversed(candidates):
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


# ====================
# Path mapping
# ====================

def _sanitize_segment(segment: str) -> str:
    segment = unquote(segment)
    segment = segment.strip()
    if segment in {".", "..", ""}:
        return "_"
    segment = re.sub(_INVALID_WIN_CHARS, "_", segment)
    if segment.upper() in _WINDOWS_RESERVED:
        segment = f"_{segment}_"
    if len(segment) > 120:
        digest = hashlib.sha1(segment.encode("utf-8", errors="ignore")).hexdigest()[:8]
        segment = segment[:80] + "_" + digest
    return segment


def sanitize_segment(segment: str) -> str:
    return _sanitize_segment(segment)


def _normalize_path(path: str) -> str:
    if not path or path == "/":
        return "/"
    return "/" + path.strip("/")


def _normalize_query(query: str) -> str:
    if not query:
        return ""
    pairs = parse_qsl(query, keep_blank_values=True)
    pairs.sort()
    return urlencode(pairs, doseq=True)


def _query_suffix(
    url: str,
    ignore_query_params: Tuple[str, ...] | None = None,
    ignore_query_prefixes: Tuple[str, ...] | None = None,
) -> str:
    parsed = urlparse(url)
    if not parsed.query:
        return ""
    ignore_params = ignore_query_params or ()
    ignore_prefixes = ignore_query_prefixes or ()
    normalized = normalize_query_with_ignore(parsed.query, ignore_params, ignore_prefixes)
    digest = hashlib.sha1(normalized.encode("utf-8", errors="ignore")).hexdigest()[:8]
    return f"__q_{digest}"


def safe_relative_path_from_base(
    url: str,
    base_url: str,
    base_slug: str | None,
    ignore_query_params: Tuple[str, ...] | None = None,
    ignore_query_prefixes: Tuple[str, ...] | None = None,
) -> str:
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)

    base_path = _normalize_path(parsed_base.path)
    url_path = _normalize_path(parsed_url.path)
    suffix = _query_suffix(url, ignore_query_params, ignore_query_prefixes)

    if base_path != "/" and (url_path == base_path or url_path.startswith(base_path + "/")):
        rel = url_path[len(base_path):].lstrip("/")
        if not rel:
            if base_slug:
                return _sanitize_segment(base_slug) + suffix
            return "index" + suffix
        segments = [seg for seg in rel.split("/") if seg]
        safe_segments = [_sanitize_segment(seg) for seg in segments]
        if safe_segments:
            safe_segments[-1] = safe_segments[-1] + suffix
        return "/".join(safe_segments)

    return safe_relative_path(url)


def safe_relative_path(
    url: str,
    ignore_query_params: Tuple[str, ...] | None = None,
    ignore_query_prefixes: Tuple[str, ...] | None = None,
) -> str:
    parsed = urlparse(url)
    raw = parsed.path.strip("/")
    suffix = _query_suffix(url, ignore_query_params, ignore_query_prefixes)
    if not raw:
        return "index" + suffix
    segments = [seg for seg in raw.split("/") if seg]
    safe_segments = [_sanitize_segment(seg) for seg in segments]
    if safe_segments:
        safe_segments[-1] = safe_segments[-1] + suffix
    return "/".join(safe_segments)


# ====================
# Content detection
# ====================

def is_probable_html(content_type: str | None, text: str) -> bool:
    if content_type and "text/html" in content_type.lower():
        return True
    head = text.lstrip().lower()[:200]
    return head.startswith("<!doctype") or head.startswith("<html")


def is_textual_content_type(content_type: str | None) -> bool:
    if not content_type:
        return True
    normalized = content_type.split(";", 1)[0].strip().lower()
    if normalized.startswith("text/"):
        return True
    if normalized in {"application/xhtml+xml", "application/xml"}:
        return True
    if normalized.endswith("+xml"):
        return True
    return False


def normalize_content_type(content_type: str | None) -> str:
    if not content_type:
        return "unknown"
    return content_type.split(";", 1)[0].strip().lower()


def compile_regex(pattern: Optional[str]) -> Optional[Pattern[str]]:
    if not pattern:
        return None
    try:
        return re.compile(pattern)
    except re.error:
        return None


def matches_filters(url: str, include: Optional[Pattern[str]], exclude: Optional[Pattern[str]]) -> bool:
    if include and not include.search(url):
        return False
    if exclude and exclude.search(url):
        return False
    return True


def classify_http_error(status: Optional[int]) -> Optional[str]:
    if status is None:
        return None
    if status == 429:
        return "http_429"
    if 400 <= status < 500:
        return "http_4xx"
    if 500 <= status < 600:
        return "http_5xx"
    return None


def classify_exception(exc: Exception) -> str:
    if isinstance(exc, requests.exceptions.Timeout):
        return "timeout"
    if isinstance(exc, requests.exceptions.ConnectionError):
        return "connection"
    if isinstance(exc, socket.gaierror):
        return "dns"
    return "unknown"


def parse_header_args(values: Iterable[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for raw in values:
        if not raw:
            continue
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key:
            headers[key] = value
    return headers


def parse_cookie_args(values: Iterable[str]) -> Dict[str, str]:
    cookies: Dict[str, str] = {}
    for raw in values:
        if not raw or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            cookies[key] = value
    return cookies


def filter_same_origin(urls: Iterable[str], base_url: str) -> List[str]:
    base = urlparse(base_url)
    filtered = []
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme == base.scheme and parsed.netloc == base.netloc:
            filtered.append(url)
    return filtered
