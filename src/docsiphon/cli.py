# ====================
# CLI
# ====================
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
import threading
import time
import urllib.parse
import urllib.robotparser
import uuid
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from typing import Dict, Optional, Iterable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import RunConfig, load_profile
from .crawl import crawl_site
from .discovery import discover_llms_full, discover_llms_txt, discover_search_index, discover_sitemap
from .fetch import OversizeError, fetch_html, fetch_markdown, html_to_markdown
from .models import ContentExtractor, ErrorKind, FetchKind, FetchStatus, NoteKind, PageRecord
from .report import (
    write_report,
    write_report_html_from_manifest,
    write_toc_from_manifest,
    write_url_list,
    write_index_from_manifest,
)
from .storage import (
    ManifestWriter,
    build_output_path,
    load_manifest_cache,
    write_error_snapshot,
    write_html,
    write_markdown,
)
from .utils import (
    RateLimiter,
    HostRateLimiter,
    HostConcurrencyLimiter,
    build_exclude_exts,
    classify_exception,
    classify_http_error,
    compile_regex,
    compute_backoff,
    is_excluded_by_extension,
    is_probable_html,
    is_textual_content_type,
    matches_filters,
    min_nonzero,
    normalize_content_type,
    normalize_url,
    parse_cookie_args,
    parse_header_args,
    sanitize_segment,
)


LOG = logging.getLogger(__name__)
_SESSION_LOCAL = threading.local()


# ====================
# Session
# ====================

def build_session(user_agent: str, config: Optional[RunConfig] = None) -> requests.Session:
    session = requests.Session()
    retries = Retry(total=0, connect=0, read=0, redirect=0, status=0)
    pool_size = 10
    if config:
        pool_size = max(pool_size, int(config.max_workers))
    adapter = HTTPAdapter(max_retries=retries, pool_connections=pool_size, pool_maxsize=pool_size)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": user_agent, "Accept": "text/markdown,text/plain;q=0.9,text/html;q=0.8"})
    if config:
        if config.headers:
            session.headers.update(config.headers)
        if config.token:
            session.headers.update({"Authorization": f"Bearer {config.token}"})
        if config.cookies:
            session.cookies.update(config.cookies)
        if config.auth:
            session.auth = config.auth
    return session


def _get_thread_session(user_agent: str, config: RunConfig) -> requests.Session:
    session = getattr(_SESSION_LOCAL, "session", None)
    session_agent = getattr(_SESSION_LOCAL, "user_agent", None)
    if session is None:
        session = build_session(user_agent, config)
        _SESSION_LOCAL.session = session
        _SESSION_LOCAL.user_agent = user_agent
    elif session_agent != user_agent:
        session = build_session(user_agent, config)
        _SESSION_LOCAL.session = session
        _SESSION_LOCAL.user_agent = user_agent
    return session


# ====================
# Runner
# ====================

def _markdown_url(url: str) -> str:
    if url.endswith(".md") or url.endswith(".md.txt"):
        return url
    return url.rstrip("/") + ".md"


def _derive_site_root(base_url: str) -> str | None:
    parsed = urlparse(base_url)
    path = parsed.path.strip("/")
    if not path:
        return None
    return path.split("/")[-1]


def _report_dir(config: RunConfig) -> str:
    if config.site_root:
        return os.path.join(config.output_dir, sanitize_segment(config.site_root))
    return config.output_dir


def _hash_content(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def _error_kind_from_status(status: Optional[int], error: Optional[Exception]) -> Optional[ErrorKind]:
    if status is not None:
        kind = classify_http_error(status)
        if kind:
            try:
                return ErrorKind(kind)
            except ValueError as exc:
                LOG.debug("unknown HTTP error kind %s: %s", kind, exc)
                return ErrorKind.UNKNOWN
    if error is not None:
        try:
            return ErrorKind(classify_exception(error))
        except ValueError as exc:
            LOG.debug("unknown exception classification for %s: %s", error, exc)
            return ErrorKind.UNKNOWN
    return None


def _resolve_extractor(config: RunConfig) -> ContentExtractor:
    raw = (config.content_extractor or "auto").lower()
    try:
        return ContentExtractor(raw)
    except ValueError as exc:
        LOG.debug("unknown content extractor %s: %s", raw, exc)
        return ContentExtractor.AUTO


def _convert_html(html: str, config: RunConfig) -> Tuple[Optional[str], ContentExtractor]:
    extractor = _resolve_extractor(config)
    if extractor == ContentExtractor.AUTO:
        for candidate in (ContentExtractor.READABILITY, ContentExtractor.TRAFILATURA, ContentExtractor.RAW):
            md = html_to_markdown(html, candidate.value)
            if md:
                return md, candidate
        return None, ContentExtractor.RAW
    return html_to_markdown(html, extractor.value), extractor


def _extract_title_h1(html: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        soup = BeautifulSoup(html, "html.parser")
        title = None
        h1 = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        h1_tag = soup.find("h1")
        if h1_tag:
            h1_text = h1_tag.get_text(strip=True)
            if h1_text:
                h1 = h1_text
        return title, h1
    except Exception as exc:
        LOG.debug("title/h1 extraction failed: %s", exc)
        return None, None


def _extract_markdown_h1(text: str) -> Optional[str]:
    lines = text.splitlines()
    idx = 0
    if lines and lines[0].strip() == "---":
        idx = 1
        while idx < len(lines):
            if lines[idx].strip() == "---":
                idx += 1
                break
            idx += 1
    while idx < len(lines):
        cleaned = lines[idx].strip()
        if cleaned.startswith("# "):
            return cleaned[2:].strip()
        idx += 1
    return None


def _is_oversize_error(error: Optional[Exception]) -> bool:
    return isinstance(error, OversizeError)


def _retry_limits(config: RunConfig) -> Dict[ErrorKind, int]:
    return {
        ErrorKind.TIMEOUT: config.retry_timeout,
        ErrorKind.CONNECTION: config.retry_connection,
        ErrorKind.DNS: config.retry_dns,
        ErrorKind.HTTP_429: config.retry_http_429,
        ErrorKind.HTTP_5XX: config.retry_http_5xx,
        ErrorKind.UNKNOWN: config.retry_unknown,
    }


def _classify_retry_kind(status: Optional[int], error: Optional[Exception]) -> Optional[ErrorKind]:
    if status is not None:
        kind = classify_http_error(status)
        if kind:
            try:
                return ErrorKind(kind)
            except ValueError as exc:
                LOG.debug("unknown retry HTTP kind %s: %s", kind, exc)
                return ErrorKind.UNKNOWN
    if error is not None:
        try:
            return ErrorKind(classify_exception(error))
        except ValueError as exc:
            LOG.debug("unknown retry exception classification for %s: %s", error, exc)
            return ErrorKind.UNKNOWN
    return None


def _call_with_retry(
    fetch_fn,
    limiter: RateLimiter,
    host_limiter: HostRateLimiter,
    host_concurrency: HostConcurrencyLimiter,
    limiter_lock: threading.Lock,
    host: str,
    config: RunConfig,
    status_index: int,
    error_index: int,
):
    limits = _retry_limits(config)
    attempt = 0
    while True:
        with host_concurrency.slot(host):
            with limiter_lock:
                limiter.wait()
            host_limiter.wait(host)
            result = fetch_fn()
        status = result[status_index] if len(result) > status_index else None
        error = result[error_index] if len(result) > error_index else None
        kind = _classify_retry_kind(status, error)
        if kind is None:
            return result
        limit = limits.get(kind, 0)
        if attempt >= limit:
            return result
        attempt += 1
        delay = compute_backoff(attempt, config.retry_backoff_base, config.retry_backoff_max, config.retry_backoff_jitter)
        if delay > 0:
            time.sleep(delay)


def _load_robots(base_url: str, session: requests.Session, timeout: int) -> Optional[urllib.robotparser.RobotFileParser]:
    try:
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        resp = session.get(robots_url, timeout=timeout)
        if resp.status_code != 200:
            return None
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(resp.text.splitlines())
        return rp
    except Exception as exc:
        LOG.debug("robots fetch failed for %s: %s", base_url, exc)
        return None


def _apply_filters(urls: Iterable[str], config: RunConfig, source_kind) -> Tuple[list[str], list[PageRecord]]:
    include_re = compile_regex(config.include_regex)
    exclude_re = compile_regex(config.exclude_regex)
    kept: list[str] = []
    filtered: list[PageRecord] = []
    for raw in urls:
        url = normalize_url(raw, config.ignore_query_params, config.ignore_query_prefixes)
        if is_excluded_by_extension(url, config.exclude_exts):
            filtered.append(
                PageRecord(
                    url=url,
                    fetched_url=url,
                    source=source_kind,
                    fetch_kind=FetchKind.NONE,
                    status=FetchStatus.SKIPPED,
                    note=NoteKind.EXCLUDED_EXTENSION,
                )
            )
            continue
        if not matches_filters(url, include_re, exclude_re):
            filtered.append(
                PageRecord(
                    url=url,
                    fetched_url=url,
                    source=source_kind,
                    fetch_kind=FetchKind.NONE,
                    status=FetchStatus.SKIPPED,
                    note=NoteKind.FILTERED_OUT,
                )
            )
            continue
        kept.append(url)
    return kept, filtered


def _apply_robots(
    urls: Iterable[str],
    config: RunConfig,
    robots: Optional[urllib.robotparser.RobotFileParser],
    source_kind,
) -> Tuple[list[str], list[PageRecord]]:
    if not robots:
        return list(urls), []
    kept: list[str] = []
    filtered: list[PageRecord] = []
    for url in urls:
        try:
            if robots.can_fetch(config.user_agent, url):
                kept.append(url)
                continue
        except Exception:
            kept.append(url)
            continue
        filtered.append(
            PageRecord(
                url=url,
                fetched_url=url,
                source=source_kind,
                fetch_kind=FetchKind.NONE,
                status=FetchStatus.SKIPPED,
                note=NoteKind.ROBOTS_DISALLOW,
            )
        )
    return kept, filtered


def _flatten_csv(values: Optional[Iterable[str]]) -> list[str]:
    if not values:
        return []
    items: list[str] = []
    for raw in values:
        if not raw:
            continue
        parts = [part.strip() for part in str(raw).split(",") if part.strip()]
        items.extend(parts)
    return items


def _coerce_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _parse_auth(value: object) -> Optional[Tuple[str, str]]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return str(value[0]), str(value[1])
    if isinstance(value, dict):
        user = value.get("username") or value.get("user")
        pwd = value.get("password") or value.get("pass")
        if user is not None and pwd is not None:
            return str(user), str(pwd)
    if isinstance(value, str) and ":" in value:
        user, pwd = value.split(":", 1)
        if user and pwd:
            return user, pwd
    return None


def _merge_headers(cli_values: Optional[list[str]], profile_value: object) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if isinstance(profile_value, dict):
        headers.update({str(k): str(v) for k, v in profile_value.items()})
    elif isinstance(profile_value, list):
        headers.update(parse_header_args([str(v) for v in profile_value]))
    if cli_values:
        headers.update(parse_header_args(cli_values))
    return headers


def _merge_cookies(cli_values: Optional[list[str]], profile_value: object) -> Dict[str, str]:
    cookies: Dict[str, str] = {}
    if isinstance(profile_value, dict):
        cookies.update({str(k): str(v) for k, v in profile_value.items()})
    elif isinstance(profile_value, list):
        cookies.update(parse_cookie_args([str(v) for v in profile_value]))
    if cli_values:
        cookies.update(parse_cookie_args(cli_values))
    return cookies


def _fetch_one(
    url: str,
    config: RunConfig,
    limiter: RateLimiter,
    host_limiter: HostRateLimiter,
    host_concurrency: HostConcurrencyLimiter,
    limiter_lock: threading.Lock,
    manifest: ManifestWriter,
    source_kind,
    cache: Optional[Dict[str, Dict[str, str]]],
    run_id: str = "",
) -> PageRecord:
    session = _get_thread_session(config.user_agent, config)
    host = urlparse(url).netloc

    conditional_headers: Dict[str, str] = {}
    cached = (cache or {}).get(url, {})
    if cached.get("etag"):
        conditional_headers["If-None-Match"] = cached["etag"]
    if cached.get("last_modified"):
        conditional_headers["If-Modified-Since"] = cached["last_modified"]

    text, content_type, fetch_kind, http_status, error, etag, last_modified, error_body = _call_with_retry(
        lambda: fetch_markdown(url, session, config, conditional_headers or None),
        limiter,
        host_limiter,
        host_concurrency,
        limiter_lock,
        host,
        config,
        3,
        4,
    )
    if http_status == 304:
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=FetchKind.NONE,
            status=FetchStatus.SKIPPED,
            http_status=http_status,
            content_type=content_type,
            note=NoteKind.NOT_MODIFIED,
            etag=etag or cached.get("etag"),
            last_modified=last_modified or cached.get("last_modified"),
            content_hash=cached.get("content_hash"),
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    if _is_oversize_error(error):
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=fetch_kind,
            status=FetchStatus.SKIPPED,
            http_status=http_status,
            content_type=content_type,
            note=NoteKind.OVERSIZE,
            error=str(error),
            error_kind=ErrorKind.UNKNOWN,
            etag=etag,
            last_modified=last_modified,
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    if text is not None:
        md_url = _markdown_url(url)
        path, write_error = write_markdown(text, url, md_url, config)
        status = FetchStatus.OK if path else FetchStatus.FAILED
        content_hash = _hash_content(text) if path else None
        error_kind = _error_kind_from_status(http_status, error)
        if write_error and error_kind is None:
            error_kind = ErrorKind.UNKNOWN
        h1 = _extract_markdown_h1(text)
        record = PageRecord(
            url=url,
            fetched_url=md_url,
            source=source_kind,
            fetch_kind=fetch_kind,
            status=status,
            http_status=http_status,
            content_type=content_type,
            bytes_written=len(text.encode("utf-8")) if path else 0,
            out_path=path,
            error=str(error) if error else write_error,
            etag=etag,
            last_modified=last_modified,
            content_hash=content_hash,
            error_kind=error_kind,
            extractor=ContentExtractor.MARKDOWN,
            title=h1,
            h1=h1,
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    if not config.html_fallback:
        note = NoteKind.MARKDOWN_NOT_AVAILABLE
        if error:
            note = NoteKind.MARKDOWN_FETCH_ERROR
        elif content_type and not is_textual_content_type(content_type):
            note = NoteKind.MARKDOWN_NON_TEXT
        elif content_type and "text/html" in content_type.lower():
            note = NoteKind.MARKDOWN_IS_HTML
        snapshot_path = None
        if config.save_error_html:
            snapshot_content = error_body if error_body else (str(error) if error else "")
            if snapshot_content:
                snapshot_path, _ = write_error_snapshot(
                    config.report_dir or config.output_dir,
                    url,
                    snapshot_content,
                    "markdown",
                    run_id,
                    config.error_snapshot_max_bytes,
                    config.error_snapshot_sample_ratio,
                    config.error_snapshot_max_files,
                    config.error_snapshot_max_total_bytes,
                )
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=fetch_kind,
            status=FetchStatus.SKIPPED,
            http_status=http_status,
            content_type=content_type,
            note=note,
            error=str(error) if error else None,
            error_kind=_error_kind_from_status(http_status, error),
            error_snapshot=snapshot_path,
            etag=etag,
            last_modified=last_modified,
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    markdown_snapshot_content = None
    if config.save_error_html:
        if error_body:
            markdown_snapshot_content = error_body
        elif error:
            markdown_snapshot_content = str(error)

    if is_excluded_by_extension(url, config.exclude_exts):
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=FetchKind.NONE,
            status=FetchStatus.SKIPPED,
            http_status=http_status,
            content_type=content_type,
            note=NoteKind.EXCLUDED_EXTENSION,
            error=str(error) if error else None,
            error_kind=_error_kind_from_status(http_status, error),
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    html, html_type, html_status, html_error, html_etag, html_last_modified = _call_with_retry(
        lambda: fetch_html(url, session, config, conditional_headers or None),
        limiter,
        host_limiter,
        host_concurrency,
        limiter_lock,
        host,
        config,
        2,
        3,
    )
    if html is None:
        if _is_oversize_error(html_error):
            record = PageRecord(
                url=url,
                fetched_url=url,
                source=source_kind,
                fetch_kind=FetchKind.HTML,
                status=FetchStatus.SKIPPED,
                http_status=html_status,
                content_type=html_type,
                note=NoteKind.OVERSIZE,
                error=str(html_error),
                error_kind=ErrorKind.UNKNOWN,
                etag=html_etag,
                last_modified=html_last_modified,
            )
            _stamp_record(record, run_id)
            manifest.write(record)
            return record
        snapshot_path = None
        if config.save_error_html and html_error:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                str(html_error),
                "html_exception",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        if snapshot_path is None and markdown_snapshot_content:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                markdown_snapshot_content,
                "markdown_fallback",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=FetchKind.HTML,
            status=FetchStatus.FAILED,
            http_status=html_status,
            content_type=html_type,
            note=NoteKind.HTML_FETCH_FAILED,
            error=str(html_error) if html_error else None,
            error_kind=_error_kind_from_status(html_status, html_error),
            error_snapshot=snapshot_path,
            etag=html_etag,
            last_modified=html_last_modified,
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    if html_status == 304:
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=FetchKind.NONE,
            status=FetchStatus.SKIPPED,
            http_status=html_status,
            content_type=html_type,
            note=NoteKind.NOT_MODIFIED,
            etag=html_etag or cached.get("etag"),
            last_modified=html_last_modified or cached.get("last_modified"),
            content_hash=cached.get("content_hash"),
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    if not is_textual_content_type(html_type):
        snapshot_path = None
        if config.save_error_html:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                html,
                "non_text",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        if snapshot_path is None and markdown_snapshot_content:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                markdown_snapshot_content,
                "markdown_fallback",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=FetchKind.HTML,
            status=FetchStatus.SKIPPED,
            http_status=html_status,
            content_type=html_type,
            note=NoteKind.NON_TEXT_CONTENT_TYPE,
            error_snapshot=snapshot_path,
            etag=html_etag,
            last_modified=html_last_modified,
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    if html_status and html_status != 200:
        snapshot_path = None
        if config.save_error_html:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                html,
                "html_http",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        if snapshot_path is None and markdown_snapshot_content:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                markdown_snapshot_content,
                "markdown_fallback",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=FetchKind.HTML,
            status=FetchStatus.FAILED,
            http_status=html_status,
            content_type=html_type,
            note=NoteKind.HTML_FETCH_FAILED,
            error_kind=_error_kind_from_status(html_status, None),
            error_snapshot=snapshot_path,
            etag=html_etag,
            last_modified=html_last_modified,
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    if html is not None and not is_probable_html(html_type, html):
        snapshot_path = None
        if config.save_error_html:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                html,
                "non_html_text",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        if snapshot_path is None and markdown_snapshot_content:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                markdown_snapshot_content,
                "markdown_fallback",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=FetchKind.HTML,
            status=FetchStatus.SKIPPED,
            http_status=html_status,
            content_type=html_type,
            note=NoteKind.NON_HTML_TEXT,
            error_snapshot=snapshot_path,
            etag=html_etag,
            last_modified=html_last_modified,
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    title, h1 = _extract_title_h1(html)
    md, extractor = _convert_html(html, config)
    if md is None:
        snapshot_path = None
        if config.save_error_html:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                html,
                "html_to_md",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        if snapshot_path is None and markdown_snapshot_content:
            snapshot_path, _ = write_error_snapshot(
                config.report_dir or config.output_dir,
                url,
                markdown_snapshot_content,
                "markdown_fallback",
                run_id,
                config.error_snapshot_max_bytes,
                config.error_snapshot_sample_ratio,
                config.error_snapshot_max_files,
                config.error_snapshot_max_total_bytes,
            )
        record = PageRecord(
            url=url,
            fetched_url=url,
            source=source_kind,
            fetch_kind=FetchKind.HTML,
            status=FetchStatus.FAILED,
            http_status=html_status,
            content_type=html_type,
            note=NoteKind.HTML_TO_MARKDOWN_FAILED,
            error_snapshot=snapshot_path,
            etag=html_etag,
            last_modified=html_last_modified,
            error_kind=_error_kind_from_status(html_status, None),
            extractor=extractor,
            title=title,
            h1=h1,
        )
        _stamp_record(record, run_id)
        manifest.write(record)
        return record

    if config.save_html:
        write_html(html, url, config)

    path, write_error = write_markdown(md, url, url, config)
    status = FetchStatus.OK if path else FetchStatus.FAILED
    content_hash = _hash_content(md) if path else None
    error_kind = _error_kind_from_status(html_status, None)
    if write_error and error_kind is None:
        error_kind = ErrorKind.UNKNOWN
    record = PageRecord(
        url=url,
        fetched_url=url,
        source=source_kind,
        fetch_kind=FetchKind.HTML,
        status=status,
        http_status=html_status,
        content_type=html_type,
        bytes_written=len(md.encode("utf-8")) if path else 0,
        out_path=path,
        error=write_error,
        etag=html_etag,
        last_modified=html_last_modified,
        content_hash=content_hash,
        error_kind=error_kind,
        extractor=extractor,
        title=title,
        h1=h1,
    )
    _stamp_record(record, run_id)
    manifest.write(record)
    return record


def _filter_by_scope(urls: list[str], scope_prefix: str | None) -> list[str]:
    if not scope_prefix:
        return urls
    prefix = scope_prefix
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    filtered = []
    for url in urls:
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception as exc:
            LOG.debug("scope parsing failed for %s: %s", url, exc)
            continue
        if parsed.path.startswith(prefix):
            filtered.append(url)
    return filtered


def _dedupe_by_output_path(urls: list[str], config: RunConfig) -> tuple[list[str], list[tuple[str, str]]]:
    seen: dict[str, str] = {}
    deduped: list[str] = []
    collisions: list[tuple[str, str]] = []
    for url in urls:
        try:
            path = os.path.normpath(build_output_path(url, config))
        except Exception as exc:
            LOG.debug("output path dedupe fallback for %s: %s", url, exc)
            deduped.append(url)
            continue
        if path in seen:
            collisions.append((url, seen[path]))
            continue
        seen[path] = url
        deduped.append(url)
    return deduped, collisions


def _summarize_results(results: list[PageRecord]) -> dict[str, object]:
    status_counts = Counter(r.status.value for r in results)
    http_status_counts = Counter(str(r.http_status) if r.http_status is not None else "none" for r in results)
    content_type_counts = Counter(normalize_content_type(r.content_type) for r in results)
    note_counts = Counter(r.note.value for r in results if r.note)
    error_kind_counts = Counter(r.error_kind.value for r in results if r.error_kind)
    extractor_counts = Counter(r.extractor.value if r.extractor else "none" for r in results)
    error_count = sum(1 for r in results if r.error)
    return {
        "status_counts": dict(status_counts),
        "http_status_counts": dict(http_status_counts),
        "content_type_counts": dict(content_type_counts),
        "note_counts": dict(note_counts),
        "error_kind_counts": dict(error_kind_counts),
        "extractor_counts": dict(extractor_counts),
        "error_count": error_count,
    }


def _init_summary() -> dict[str, Counter]:
    return {
        "status_counts": Counter(),
        "http_status_counts": Counter(),
        "content_type_counts": Counter(),
        "note_counts": Counter(),
        "error_kind_counts": Counter(),
        "extractor_counts": Counter(),
        "error_count": Counter(),
    }


def _accumulate_summary(summary: dict[str, Counter], record: PageRecord) -> None:
    summary["status_counts"][record.status.value] += 1
    summary["http_status_counts"][str(record.http_status) if record.http_status is not None else "none"] += 1
    summary["content_type_counts"][normalize_content_type(record.content_type)] += 1
    if record.note:
        summary["note_counts"][record.note.value] += 1
    if record.error_kind:
        summary["error_kind_counts"][record.error_kind.value] += 1
    summary["extractor_counts"][record.extractor.value if record.extractor else "none"] += 1
    if record.error:
        summary["error_count"]["error_count"] += 1


def _stamp_record(record: PageRecord, run_id: str) -> PageRecord:
    record.run_id = run_id
    return record


def run(config: RunConfig) -> int:
    os.makedirs(config.output_dir, exist_ok=True)
    run_id = uuid.uuid4().hex[:12]
    started_at_utc = datetime.now(timezone.utc).isoformat()
    discovery_session = build_session(config.user_agent, config)

    llms_full = discover_llms_full(config.base_url, discovery_session, config.request_timeout, config.max_body_bytes)

    discovery = discover_llms_txt(config.base_url, discovery_session, config.request_timeout, config.max_body_bytes)
    if discovery is None:
        discovery = discover_sitemap(config.base_url, discovery_session, config.request_timeout, config.max_body_bytes)
    if discovery is None:
        discovery = discover_search_index(
            config.base_url, discovery_session, config.request_timeout, config.max_body_bytes
        )
    if discovery is None:
        discovery = crawl_site(config, discovery_session)

    urls = [
        normalize_url(u, config.ignore_query_params, config.ignore_query_prefixes) for u in discovery.urls
    ]
    if config.scope_prefix:
        urls = _filter_by_scope(urls, config.scope_prefix)

    if not urls:
        print("No URLs discovered.")
        return 2

    report_dir = config.report_dir or _report_dir(config)
    os.makedirs(report_dir, exist_ok=True)
    if config.report_dir is None:
        config = replace(config, report_dir=report_dir)

    urls, filtered_records = _apply_filters(urls, config, discovery.source)
    urls = sorted(set(urls))
    urls, collisions = _dedupe_by_output_path(urls, config)
    if collisions:
        print(f"Detected {len(collisions)} path collisions; skipping duplicates.")

    limited_records: list[PageRecord] = []
    if config.max_pages > 0 and len(urls) > config.max_pages:
        limited_urls = urls[config.max_pages :]
        urls = urls[: config.max_pages]
        for url in limited_urls:
            limited_records.append(
                PageRecord(
                    url=url,
                    fetched_url=url,
                    source=discovery.source,
                    fetch_kind=FetchKind.NONE,
                    status=FetchStatus.SKIPPED,
                    note=NoteKind.MAX_PAGES_LIMIT,
                )
            )

    write_url_list(report_dir, urls)

    if config.dry_run:
        print(f"Discovered {len(urls)} URLs via {discovery.source.value}.")
        if llms_full:
            print(f"Found llms-full.txt at {llms_full} (not used for per-page export).")
        return 0

    robots = None
    if not config.ignore_robots:
        robots = _load_robots(config.base_url, discovery_session, config.request_timeout)

    urls, robot_filtered = _apply_robots(urls, config, robots, discovery.source)

    robots_delay = None
    if robots:
        try:
            robots_delay = robots.crawl_delay(config.user_agent)
        except Exception:
            robots_delay = None

    effective_rate = config.rate_limit_per_sec
    if robots_delay:
        effective_rate = min_nonzero(effective_rate, 1.0 / float(robots_delay))
    limiter = RateLimiter(effective_rate)
    effective_host_rate = config.host_rate_limit_per_sec
    if robots_delay:
        effective_host_rate = min_nonzero(effective_host_rate, 1.0 / float(robots_delay))
    host_limiter = HostRateLimiter(effective_host_rate)
    host_concurrency = HostConcurrencyLimiter(config.host_max_concurrency)
    limiter_lock = threading.Lock()
    manifest = ManifestWriter(report_dir, sorted_mode=config.manifest_sorted)

    summary = _init_summary()
    total_records = 0
    try:
        for record in filtered_records:
            _stamp_record(record, run_id)
            manifest.write(record)
            _accumulate_summary(summary, record)
            total_records += 1
        for record in robot_filtered:
            _stamp_record(record, run_id)
            manifest.write(record)
            _accumulate_summary(summary, record)
            total_records += 1
        for record in limited_records:
            _stamp_record(record, run_id)
            manifest.write(record)
            _accumulate_summary(summary, record)
            total_records += 1

        for url, kept in collisions:
            record = PageRecord(
                url=url,
                fetched_url=kept,
                source=discovery.source,
                fetch_kind=FetchKind.NONE,
                status=FetchStatus.SKIPPED,
                note=NoteKind.PATH_COLLISION,
            )
            _stamp_record(record, run_id)
            manifest.write(record)
            _accumulate_summary(summary, record)
            total_records += 1

        skip_urls: set[str] = set()
        cache: Optional[Dict[str, Dict[str, str]]] = None
        if config.resume:
            cache = load_manifest_cache(
                report_dir,
                allowed_urls=set(urls),
                max_entries=config.manifest_cache_max_entries,
            )

        for url in urls:
            if config.skip_existing:
                path = build_output_path(url, config)
                if os.path.exists(path):
                    skip_urls.add(url)
                    record = PageRecord(
                        url=url,
                        fetched_url=url,
                        source=discovery.source,
                        fetch_kind=FetchKind.NONE,
                        status=FetchStatus.SKIPPED,
                        note=NoteKind.SKIP_EXISTING,
                    )
                    _stamp_record(record, run_id)
                    manifest.write(record)
                    _accumulate_summary(summary, record)
                    total_records += 1

        urls_to_fetch = [url for url in urls if url not in skip_urls]

        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            futures = [
                executor.submit(
                    _fetch_one,
                    url,
                    config,
                    limiter,
                    host_limiter,
                    host_concurrency,
                    limiter_lock,
                    manifest,
                    discovery.source,
                    cache,
                    run_id,
                )
                for url in urls_to_fetch
            ]
            for f in as_completed(futures):
                try:
                    record = f.result()
                    _accumulate_summary(summary, record)
                    total_records += 1
                except Exception as exc:
                    LOG.debug("worker failed: %s", exc)
                    continue

        counts = {
            "run_id": run_id,
            "started_at_utc": started_at_utc,
            "total": total_records,
            "filtered_urls": len(urls),
            "scheduled_urls": len(urls_to_fetch),
            "ok": summary["status_counts"].get(FetchStatus.OK.value, 0),
            "failed": summary["status_counts"].get(FetchStatus.FAILED.value, 0),
            "skipped": summary["status_counts"].get(FetchStatus.SKIPPED.value, 0),
            "discovery_source": discovery.source.value,
            "scope_prefix": config.scope_prefix or "",
            "path_collisions": len(collisions),
            "limited_urls": len(limited_records),
        }
        counts.update(
            {
                "status_counts": dict(summary["status_counts"]),
                "http_status_counts": dict(summary["http_status_counts"]),
                "content_type_counts": dict(summary["content_type_counts"]),
                "note_counts": dict(summary["note_counts"]),
                "error_kind_counts": dict(summary["error_kind_counts"]),
                "extractor_counts": dict(summary["extractor_counts"]),
                "error_count": summary["error_count"].get("error_count", 0),
            }
        )
        manifest.finalize()
        write_report(report_dir, counts)
        manifest_path = os.path.join(report_dir, "manifest.jsonl")
        write_index_from_manifest(manifest_path, report_dir)
        write_toc_from_manifest(manifest_path, report_dir)
        write_report_html_from_manifest(manifest_path, report_dir, counts)
        return 0
    finally:
        manifest.finalize()


# ====================
# CLI entry
# ====================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docsiphon",
        description="Docsiphon: export documentation sites to Markdown with preserved paths."
    )
    parser.add_argument("base_url", help="Any docs page URL as a starting point.")
    parser.add_argument("--out", default=None, help="Output directory.")
    parser.add_argument(
        "--site-root",
        default=None,
        help="Group output under a site root folder. Use 'auto' to derive from base_url.",
    )
    parser.add_argument("--workers", type=int, default=None, help="Concurrent workers.")
    parser.add_argument("--timeout", type=int, default=None, help="Request timeout in seconds.")
    parser.add_argument("--rate", type=float, default=None, help="Global rate limit (req/sec).")
    parser.add_argument("--host-rate", type=float, default=None, help="Per-host rate limit (req/sec).")
    parser.add_argument("--host-concurrency", type=int, default=None, help="Per-host max concurrency.")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages for BFS discovery.")
    parser.add_argument("--max-depth", type=int, default=None, help="Max depth for BFS discovery.")
    parser.add_argument("--scope-prefix", default=None, help="Path prefix scope, e.g. /docs.")
    parser.add_argument("--frontmatter", action="store_true", default=None, help="Write YAML frontmatter with source metadata.")
    parser.add_argument(
        "--frontmatter-no-timestamp", action="store_true", default=None, help="Disable timestamp in frontmatter."
    )
    parser.add_argument("--no-html", action="store_true", default=None, help="Disable HTML fallback conversion.")
    parser.add_argument(
        "--exclude-ext",
        action="append",
        default=None,
        help="Comma-separated or repeatable extensions to skip during HTML fallback, e.g. .pdf,.png",
    )
    parser.add_argument("--include-regex", default=None, help="Only include URLs matching regex.")
    parser.add_argument("--exclude-regex", default=None, help="Exclude URLs matching regex.")
    parser.add_argument("--ignore-query", action="append", default=None, help="Query params to ignore (repeatable).")
    parser.add_argument(
        "--ignore-query-prefix", action="append", default=None, help="Query param prefixes to ignore (repeatable)."
    )
    parser.add_argument(
        "--content-extractor",
        default=None,
        choices=[e.value for e in ContentExtractor],
        help="HTML content extractor.",
    )
    parser.add_argument("--save-html", action=argparse.BooleanOptionalAction, default=None, help="Save raw HTML.")
    parser.add_argument(
        "--save-error-html",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Save error HTML/text snapshots.",
    )
    parser.add_argument("--ignore-robots", action=argparse.BooleanOptionalAction, default=None, help="Ignore robots.txt.")
    parser.add_argument("--retry", type=int, default=None, help="Total retry attempts for transient errors.")
    parser.add_argument("--retry-timeout", type=int, default=None, help="Retries for timeout errors.")
    parser.add_argument("--retry-connection", type=int, default=None, help="Retries for connection errors.")
    parser.add_argument("--retry-dns", type=int, default=None, help="Retries for DNS errors.")
    parser.add_argument("--retry-429", type=int, default=None, help="Retries for HTTP 429.")
    parser.add_argument("--retry-5xx", type=int, default=None, help="Retries for HTTP 5xx.")
    parser.add_argument("--retry-unknown", type=int, default=None, help="Retries for unknown errors.")
    parser.add_argument("--retry-backoff", type=float, default=None, help="Backoff base seconds.")
    parser.add_argument("--retry-backoff-max", type=float, default=None, help="Backoff max seconds.")
    parser.add_argument("--retry-jitter", type=float, default=None, help="Backoff jitter seconds.")
    parser.add_argument("--header", action="append", default=None, help="Extra header (Key: Value). Repeatable.")
    parser.add_argument("--cookie", action="append", default=None, help="Cookie (key=value). Repeatable.")
    parser.add_argument("--auth", default=None, help="Basic auth user:pass.")
    parser.add_argument("--token", default=None, help="Bearer token.")
    parser.add_argument("--report-dir", default=None, help="Directory for reports/manifest.")
    parser.add_argument("--profile", default=None, help="Path to config.toml profile.")
    parser.add_argument("--profile-name", default=None, help="Profile name under profiles.<name>.")
    parser.add_argument("--user-agent", default=None, help="Override User-Agent header.")
    parser.add_argument(
        "--manifest-sorted",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Write manifest.jsonl in sorted order.",
    )
    parser.add_argument(
        "--error-snapshot-max-bytes",
        type=int,
        default=None,
        help="Max bytes per error snapshot.",
    )
    parser.add_argument(
        "--error-snapshot-sample-ratio",
        type=float,
        default=None,
        help="Head ratio for truncation sampling.",
    )
    parser.add_argument(
        "--error-snapshot-max-files",
        type=int,
        default=None,
        help="Max number of error snapshots to write.",
    )
    parser.add_argument(
        "--error-snapshot-max-total-bytes",
        type=int,
        default=None,
        help="Max total bytes for error snapshots.",
    )
    parser.add_argument("--max-body-bytes", type=int, default=None, help="Max bytes for response body.")
    parser.add_argument("--dry-run", action="store_true", default=None, help="Discovery only, no downloads.")
    parser.add_argument("--resume", action="store_true", default=None, help="Use manifest cache for incremental run.")
    parser.add_argument("--skip-existing", action="store_true", default=None, help="Skip URLs when output file exists.")
    parser.add_argument("--verbose", action="store_true", default=None, help="Verbose logging for debugging.")
    parser.add_argument(
        "--manifest-cache-max-entries",
        type=int,
        default=None,
        help="Max entries to keep in manifest cache.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    profile = load_profile(args.profile, args.profile_name) if args.profile else {}

    def pick(key: str, arg_value, default):
        if arg_value is not None:
            return arg_value
        if key in profile:
            return profile[key]
        return default

    logging.basicConfig(
        level=logging.DEBUG if _coerce_bool(pick("verbose", args.verbose, False), False) else logging.WARNING,
        format="%(levelname)s:%(name)s:%(message)s",
    )

    site_root = None
    raw_site_root = pick("site_root", args.site_root, None)
    if raw_site_root:
        if raw_site_root == "auto":
            site_root = _derive_site_root(args.base_url)
        else:
            cleaned = str(raw_site_root).strip()
            if cleaned:
                site_root = cleaned

    output_dir = pick("output_dir", args.out, "./_outputs")

    exclude_raw = args.exclude_ext if args.exclude_ext is not None else profile.get("exclude_exts") or profile.get(
        "exclude_ext"
    )
    exclude_exts = build_exclude_exts(_flatten_csv(exclude_raw))

    ignore_query = (
        args.ignore_query
        if args.ignore_query is not None
        else profile.get("ignore_query_params") if "ignore_query_params" in profile else profile.get("ignore_query")
    )
    if args.ignore_query_prefix is not None:
        ignore_query_prefix = args.ignore_query_prefix
    elif "ignore_query_prefixes" in profile:
        ignore_query_prefix = profile.get("ignore_query_prefixes")
    elif "ignore_query_prefix" in profile:
        ignore_query_prefix = profile.get("ignore_query_prefix")
    else:
        ignore_query_prefix = ["utm_"]

    include_regex = pick("include_regex", args.include_regex, None)
    exclude_regex = pick("exclude_regex", args.exclude_regex, None)

    content_extractor = pick("content_extractor", args.content_extractor, "auto")

    save_html = _coerce_bool(pick("save_html", args.save_html, False), False)
    save_error_html = _coerce_bool(pick("save_error_html", args.save_error_html, True), True)
    ignore_robots = _coerce_bool(pick("ignore_robots", args.ignore_robots, False), False)
    dry_run = _coerce_bool(pick("dry_run", args.dry_run, False), False)
    resume = _coerce_bool(pick("resume", args.resume, False), False)
    skip_existing = _coerce_bool(pick("skip_existing", args.skip_existing, False), False)

    frontmatter = _coerce_bool(pick("frontmatter", args.frontmatter, False), False)
    frontmatter_timestamp = True
    fm_ts_value = pick("frontmatter_timestamp", None, None)
    if fm_ts_value is not None:
        frontmatter_timestamp = _coerce_bool(fm_ts_value, True)
    no_ts_value = pick("frontmatter_no_timestamp", args.frontmatter_no_timestamp, None)
    if no_ts_value is not None:
        frontmatter_timestamp = not _coerce_bool(no_ts_value, False)

    html_fallback = True
    html_fallback_value = pick("html_fallback", None, None)
    if html_fallback_value is not None:
        html_fallback = _coerce_bool(html_fallback_value, True)
    no_html_value = pick("no_html", args.no_html, None)
    if no_html_value is not None:
        html_fallback = not _coerce_bool(no_html_value, False)

    headers = _merge_headers(args.header, profile.get("headers") if profile else {})
    cookies = _merge_cookies(args.cookie, profile.get("cookies") if profile else {})
    auth = _parse_auth(args.auth) or _parse_auth(profile.get("auth") if profile else None)
    token = pick("token", args.token, None)
    report_dir = pick("report_dir", args.report_dir, None)
    user_agent = str(pick("user_agent", args.user_agent, "Mozilla/5.0 (docsiphon/0.1)"))

    retry_total = int(pick("retry_total", args.retry, 4))
    retry_timeout = int(pick("retry_timeout", args.retry_timeout, retry_total))
    retry_connection = int(pick("retry_connection", args.retry_connection, retry_total))
    retry_dns = int(pick("retry_dns", args.retry_dns, retry_total))
    retry_http_429 = int(pick("retry_http_429", args.retry_429, retry_total))
    retry_http_5xx = int(pick("retry_http_5xx", args.retry_5xx, retry_total))
    retry_unknown = int(pick("retry_unknown", args.retry_unknown, 0))
    retry_backoff_base = float(pick("retry_backoff_base", args.retry_backoff, 0.5))
    retry_backoff_max = float(pick("retry_backoff_max", args.retry_backoff_max, 8.0))
    retry_backoff_jitter = float(pick("retry_backoff_jitter", args.retry_jitter, 0.3))

    manifest_sorted = _coerce_bool(pick("manifest_sorted", args.manifest_sorted, False), False)
    error_snapshot_max_bytes = int(pick("error_snapshot_max_bytes", args.error_snapshot_max_bytes, 200000))
    error_snapshot_sample_ratio = float(
        pick("error_snapshot_sample_ratio", args.error_snapshot_sample_ratio, 0.7)
    )
    error_snapshot_max_files = int(pick("error_snapshot_max_files", args.error_snapshot_max_files, 0))
    error_snapshot_max_total_bytes = int(
        pick("error_snapshot_max_total_bytes", args.error_snapshot_max_total_bytes, 0)
    )
    max_body_bytes = int(pick("max_body_bytes", args.max_body_bytes, 0))
    manifest_cache_max_entries = int(pick("manifest_cache_max_entries", args.manifest_cache_max_entries, 0))

    config = RunConfig(
        base_url=args.base_url,
        output_dir=output_dir,
        site_root=site_root,
        max_workers=int(pick("max_workers", args.workers, 8)),
        request_timeout=int(pick("request_timeout", args.timeout, 20)),
        rate_limit_per_sec=float(pick("rate_limit_per_sec", args.rate, 5.0)),
        host_rate_limit_per_sec=float(pick("host_rate_limit_per_sec", args.host_rate, 0.0)),
        host_max_concurrency=int(pick("host_max_concurrency", args.host_concurrency, 0)),
        user_agent=user_agent,
        retry_total=retry_total,
        retry_timeout=retry_timeout,
        retry_connection=retry_connection,
        retry_dns=retry_dns,
        retry_http_429=retry_http_429,
        retry_http_5xx=retry_http_5xx,
        retry_unknown=retry_unknown,
        retry_backoff_base=retry_backoff_base,
        retry_backoff_max=retry_backoff_max,
        retry_backoff_jitter=retry_backoff_jitter,
        max_pages=int(pick("max_pages", args.max_pages, 5000)),
        max_depth=int(pick("max_depth", args.max_depth, 6)),
        scope_prefix=pick("scope_prefix", args.scope_prefix, None),
        frontmatter=frontmatter,
        frontmatter_timestamp=frontmatter_timestamp,
        html_fallback=html_fallback,
        exclude_exts=exclude_exts,
        include_regex=include_regex,
        exclude_regex=exclude_regex,
        ignore_query_params=tuple(_flatten_csv(ignore_query)),
        ignore_query_prefixes=tuple(_flatten_csv(ignore_query_prefix)),
        content_extractor=str(content_extractor),
        save_html=save_html,
        save_error_html=save_error_html,
        ignore_robots=ignore_robots,
        headers=headers,
        cookies=cookies,
        auth=auth,
        token=token,
        report_dir=report_dir,
        manifest_sorted=manifest_sorted,
        error_snapshot_max_bytes=error_snapshot_max_bytes,
        error_snapshot_sample_ratio=error_snapshot_sample_ratio,
        error_snapshot_max_files=error_snapshot_max_files,
        error_snapshot_max_total_bytes=error_snapshot_max_total_bytes,
        max_body_bytes=max_body_bytes,
        resume=resume,
        skip_existing=skip_existing,
        dry_run=dry_run,
        manifest_cache_max_entries=manifest_cache_max_entries,
    )

    try:
        code = run(config)
    except KeyboardInterrupt:
        print("Interrupted.")
        code = 130
    except Exception as exc:
        print(f"Fatal error: {exc}")
        code = 1

    sys.exit(code)


if __name__ == "__main__":
    main()
