# ====================
# Discovery
# ====================
from __future__ import annotations

import gzip
import json
import logging
import re
from typing import List, Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests

from .models import DiscoveryResult, SourceKind
from .utils import candidate_base_paths, filter_same_origin, normalize_url


LOG = logging.getLogger(__name__)


# ====================
# LLMS
# ====================

def _is_response_too_large(resp: requests.Response, max_bytes: int) -> bool:
    if max_bytes <= 0:
        return False
    length = resp.headers.get("content-length")
    if length and length.isdigit() and int(length) > max_bytes:
        return True
    try:
        return len(resp.content) > max_bytes
    except Exception as exc:
        LOG.debug("content size check failed for %s: %s", resp.url, exc)
        return False


def _fetch_text(url: str, session: requests.Session, timeout: int, max_bytes: int = 0) -> Optional[str]:
    try:
        resp = session.get(url, timeout=timeout)
        if resp.status_code == 200:
            if _is_response_too_large(resp, max_bytes):
                return None
            return resp.text
    except Exception as exc:
        LOG.debug("fetch llms failed for %s: %s", url, exc)
        return None
    return None


def discover_llms_txt(
    base_url: str, session: requests.Session, timeout: int, max_bytes: int = 0
) -> Optional[DiscoveryResult]:
    candidates = []
    for base in candidate_base_paths(base_url):
        candidates.append(urljoin(base + "/", "llms.txt"))

    # Markdown link pattern: [text](url) or bare https? URLs
    _md_link_re = re.compile(r'\[([^\]]*)\]\((https?://[^)\s]+)\)|(https?://[^\s)\]]+)')

    for url in candidates:
        text = _fetch_text(url, session, timeout, max_bytes)
        if not text:
            continue
        urls = []
        seen = set()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                u = normalize_url(line)
                if u not in seen:
                    urls.append(u)
                    seen.add(u)
            for m in _md_link_re.finditer(line):
                u = normalize_url(m.group(2) or m.group(3))
                if u and u not in seen:
                    urls.append(u)
                    seen.add(u)
        urls = filter_same_origin(urls, base_url)
        if urls:
            return DiscoveryResult(source=SourceKind.LLMS_TXT, urls=urls, meta={"llms_txt": url})
    return None


def discover_llms_full(base_url: str, session: requests.Session, timeout: int, max_bytes: int = 0) -> Optional[str]:
    candidates = []
    for base in candidate_base_paths(base_url):
        candidates.append(urljoin(base + "/", "llms-full.txt"))

    for url in candidates:
        text = _fetch_text(url, session, timeout, max_bytes)
        if text:
            return url
    return None


# ====================
# Sitemap
# ====================

def _parse_sitemap(xml_bytes: bytes) -> tuple[str, List[str]]:
    root = ET.fromstring(xml_bytes)
    tag = root.tag.lower()

    if tag.endswith("sitemapindex"):
        locs: List[str] = []
        for sm in list(root):
            if not sm.tag.lower().endswith("sitemap"):
                continue
            for child in list(sm):
                if child.tag.lower().endswith("loc") and child.text:
                    locs.append(child.text.strip())
        return "index", locs

    if tag.endswith("urlset"):
        locs = []
        for u in list(root):
            if not u.tag.lower().endswith("url"):
                continue
            for child in list(u):
                if child.tag.lower().endswith("loc") and child.text:
                    locs.append(child.text.strip())
        return "urlset", locs

    return "unknown", []


def _discover_sitemap_urls(base_url: str, session: requests.Session, timeout: int, max_bytes: int = 0) -> List[str]:
    from urllib.parse import urlparse

    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    sitemap_urls: List[str] = []

    # robots.txt
    robots_url = urljoin(origin + "/", "robots.txt")
    try:
        resp = session.get(robots_url, timeout=timeout)
        if resp.status_code == 200:
            if _is_response_too_large(resp, max_bytes):
                raise ValueError("robots.txt too large")
            for line in resp.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemap_urls.append(line.split(":", 1)[1].strip())
    except Exception as exc:
        LOG.debug("robots.txt fetch failed: %s", exc)

    if not sitemap_urls:
        for path in [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap-index.xml",
            "/sitemap.xml.gz",
            "/sitemap_index.xml.gz",
            "/sitemap-index.xml.gz",
            "/sitemap.gz",
        ]:
            sitemap_urls.append(urljoin(origin + "/", path.lstrip("/")))

    return sitemap_urls


def _maybe_decompress_sitemap(content: bytes, content_type: str | None, sitemap_url: str) -> bytes:
    if sitemap_url.endswith(".gz"):
        try:
            return gzip.decompress(content)
        except Exception as exc:
            LOG.debug("sitemap gzip decompress failed for %s: %s", sitemap_url, exc)
            return content
    if content_type and "gzip" in content_type.lower():
        try:
            return gzip.decompress(content)
        except Exception as exc:
            LOG.debug("sitemap gzip decompress failed for %s: %s", sitemap_url, exc)
            return content
    return content


def _resolve_sitemap_locs(locs: List[str], sitemap_url: str) -> List[str]:
    resolved: List[str] = []
    for loc in locs:
        loc = (loc or "").strip()
        if not loc:
            continue
        if loc.startswith("http://") or loc.startswith("https://"):
            resolved.append(loc)
        else:
            resolved.append(urljoin(sitemap_url, loc))
    return resolved


def discover_sitemap(
    base_url: str, session: requests.Session, timeout: int, max_bytes: int = 0
) -> Optional[DiscoveryResult]:
    urls: List[str] = []
    queue = _discover_sitemap_urls(base_url, session, timeout, max_bytes)
    seen: set[str] = set()

    while queue:
        sitemap = queue.pop(0)
        if sitemap in seen:
            continue
        seen.add(sitemap)
        try:
            resp = session.get(sitemap, timeout=timeout)
            if resp.status_code != 200:
                continue
            if _is_response_too_large(resp, max_bytes):
                continue
            content = _maybe_decompress_sitemap(resp.content, resp.headers.get("content-type"), sitemap)
            if max_bytes > 0 and len(content) > max_bytes:
                continue
            kind, locs = _parse_sitemap(content)
            locs = _resolve_sitemap_locs(locs, sitemap)
            if kind == "index":
                queue.extend([loc for loc in locs if loc not in seen])
            elif kind == "urlset":
                urls.extend(locs)
        except Exception as exc:
            LOG.debug("sitemap fetch/parse failed for %s: %s", sitemap, exc)
            continue

    urls = [normalize_url(u) for u in urls]
    urls = filter_same_origin(urls, base_url)
    if urls:
        return DiscoveryResult(source=SourceKind.SITEMAP, urls=sorted(set(urls)), meta={"sitemap": "auto"})
    return None


# ====================
# Search index
# ====================

def _extract_urls_from_json(data, base_url: str) -> List[str]:
    urls: List[str] = []

    def _push(value: str) -> None:
        if value.startswith("http://") or value.startswith("https://"):
            urls.append(value)
        else:
            urls.append(urljoin(base_url, value))

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for key in ("url", "path", "location"):
                    if key in item and isinstance(item[key], str):
                        _push(item[key])
    elif isinstance(data, dict):
        for key in ("docs", "documents", "entries", "pages", "index"):
            if key in data:
                urls.extend(_extract_urls_from_json(data[key], base_url))
        for key in ("url", "path", "location"):
            if key in data and isinstance(data[key], str):
                _push(data[key])

    return urls


def discover_search_index(
    base_url: str, session: requests.Session, timeout: int, max_bytes: int = 0
) -> Optional[DiscoveryResult]:
    candidates: List[str] = []
    for base in candidate_base_paths(base_url):
        for path in [
            "search/search_index.json",
            "search_index.json",
            "search-index.json",
            "search.json",
            "index.json",
            "assets/search.json",
            "search/search-index.json",
        ]:
            candidates.append(urljoin(base + "/", path))

    for url in candidates:
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code != 200:
                continue
            if _is_response_too_large(resp, max_bytes):
                continue
            data = json.loads(resp.text)
            urls = _extract_urls_from_json(data, base_url)
            urls = [normalize_url(u) for u in urls]
            urls = filter_same_origin(urls, base_url)
            if urls:
                return DiscoveryResult(source=SourceKind.SEARCH_INDEX, urls=sorted(set(urls)), meta={"search_index": url})
        except Exception as exc:
            LOG.debug("search index fetch/parse failed for %s: %s", url, exc)
            continue

    return None
