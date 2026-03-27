# ====================
# BFS Crawler
# ====================
from __future__ import annotations

from collections import deque
import logging
import os
import urllib.robotparser
from typing import Deque, List, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import RunConfig
from .models import DiscoveryResult, SourceKind
from .utils import (
    HostRateLimiter,
    RateLimiter,
    compile_regex,
    is_excluded_by_extension,
    is_probable_html,
    is_textual_content_type,
    matches_filters,
    min_nonzero,
    normalize_url,
    same_origin,
)


LOG = logging.getLogger(__name__)


# ====================
# Link extraction
# ====================

def _extract_links(
    html: str,
    base_url: str,
    exclude_exts: Set[str],
    include_re,
    exclude_re,
    ignore_query_params: Tuple[str, ...],
    ignore_query_prefixes: Tuple[str, ...],
) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        abs_url = urljoin(base_url, href)
        if is_excluded_by_extension(abs_url, exclude_exts):
            continue
        normalized = normalize_url(abs_url, ignore_query_params, ignore_query_prefixes)
        if not matches_filters(normalized, include_re, exclude_re):
            continue
        links.append(normalized)
    return links


def _scope_prefix(config: RunConfig) -> str:
    if config.scope_prefix:
        return config.scope_prefix
    parsed = urlparse(config.base_url)
    path = parsed.path or "/"
    if not path or path == "/":
        return "/"
    if path.endswith("/"):
        scope = path.rstrip("/")
    else:
        segments = [seg for seg in path.split("/") if seg]
        _, ext = os.path.splitext(path)
        if len(segments) == 1 and not ext:
            scope = path
        else:
            scope = os.path.dirname(path)
    if not scope:
        return "/"
    if not scope.startswith("/"):
        scope = "/" + scope
    return scope


def _in_scope(url: str, scope_prefix: str, base_url: str) -> bool:
    if not same_origin(url, base_url):
        return False
    parsed = urlparse(url)
    if scope_prefix == "/":
        return True
    return parsed.path.startswith(scope_prefix)


# ====================
# Crawl
# ====================

def crawl_site(config: RunConfig, session: requests.Session) -> DiscoveryResult:
    limiter = RateLimiter(config.rate_limit_per_sec)
    host_limiter = HostRateLimiter(config.host_rate_limit_per_sec)
    scope = _scope_prefix(config)
    include_re = compile_regex(config.include_regex)
    exclude_re = compile_regex(config.exclude_regex)

    robots = None
    robots_delay = None
    if not config.ignore_robots:
        try:
            parsed = urlparse(config.base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            resp = session.get(robots_url, timeout=config.request_timeout)
            if resp.status_code == 200:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(resp.text.splitlines())
                robots = rp
                robots_delay = rp.crawl_delay(config.user_agent)
        except Exception:
            robots = None

    visited: Set[str] = set()
    if robots_delay:
        limiter = RateLimiter(min_nonzero(config.rate_limit_per_sec, 1.0 / float(robots_delay)))
        host_limiter = HostRateLimiter(min_nonzero(config.host_rate_limit_per_sec, 1.0 / float(robots_delay)))

    queue: Deque[Tuple[str, int]] = deque(
        [(normalize_url(config.base_url, config.ignore_query_params, config.ignore_query_prefixes), 0)]
    )

    results: List[str] = []

    while queue and len(visited) < config.max_pages:
        url, depth = queue.popleft()
        if url in visited:
            continue
        if depth > config.max_depth:
            continue

        visited.add(url)

        if is_excluded_by_extension(url, set(config.exclude_exts)):
            continue
        if not matches_filters(url, include_re, exclude_re):
            continue
        limiter.wait()
        host_limiter.wait(urlparse(url).netloc)

        if robots and not robots.can_fetch(config.user_agent, url):
            continue

        try:
            resp = session.get(url, timeout=config.request_timeout)
            if resp.status_code != 200:
                continue
            if config.max_body_bytes > 0:
                length = resp.headers.get("content-length")
                if length and length.isdigit() and int(length) > config.max_body_bytes:
                    continue
            content_type = resp.headers.get("content-type")
            if not is_textual_content_type(content_type):
                continue
            html = resp.text
            if config.max_body_bytes > 0 and len(html.encode("utf-8", errors="ignore")) > config.max_body_bytes:
                continue
            if not is_probable_html(content_type, html):
                continue
        except Exception as exc:
            LOG.debug("crawl fetch failed for %s: %s", url, exc)
            continue

        results.append(url)

        try:
            links = _extract_links(
                html,
                url,
                set(config.exclude_exts),
                include_re,
                exclude_re,
                config.ignore_query_params,
                config.ignore_query_prefixes,
            )
        except Exception as exc:
            LOG.debug("crawl link parse failed for %s: %s", url, exc)
            continue

        for link in links:
            if link in visited:
                continue
            if not _in_scope(link, scope, config.base_url):
                continue
            queue.append((link, depth + 1))

    return DiscoveryResult(source=SourceKind.BFS, urls=sorted(set(results)), meta={"scope": scope})
