# ====================
# Fetch and Convert
# ====================
from __future__ import annotations

import logging
from typing import Optional, Tuple, Dict

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md_convert

from .config import RunConfig
from .models import FetchKind
from .utils import is_probable_html, is_textual_content_type


LOG = logging.getLogger(__name__)


class OversizeError(Exception):
    """Raised when a response body exceeds the configured size budget."""

# ====================
# Markdown fetch
# ====================

def _build_md_url(url: str) -> str:
    if url.endswith(".md") or url.endswith(".md.txt"):
        return url
    return url.rstrip("/") + ".md"


def fetch_markdown(
    url: str,
    session: requests.Session,
    config: RunConfig,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[
    Optional[str],
    Optional[str],
    FetchKind,
    Optional[int],
    Optional[Exception],
    Optional[str],
    Optional[str],
    Optional[str],
]:
    md_url = _build_md_url(url)
    try:
        resp = session.get(md_url, timeout=config.request_timeout, headers=headers)
        status = resp.status_code
        content_type = resp.headers.get("content-type")
        etag = resp.headers.get("etag")
        last_modified = resp.headers.get("last-modified")
        if config.max_body_bytes > 0:
            length = resp.headers.get("content-length")
            if length and length.isdigit() and int(length) > config.max_body_bytes:
                return (
                    None,
                    content_type,
                    FetchKind.MARKDOWN,
                    status,
                    OversizeError("markdown response too large"),
                    etag,
                    last_modified,
                    None,
                )
        if content_type and not is_textual_content_type(content_type) and "text/html" not in content_type.lower():
            return None, content_type, FetchKind.MARKDOWN, status, None, etag, last_modified, None
        body = resp.text
        if config.max_body_bytes > 0 and len(body.encode("utf-8")) > config.max_body_bytes:
            return (
                None,
                content_type,
                FetchKind.MARKDOWN,
                status,
                OversizeError("markdown response too large"),
                etag,
                last_modified,
                None,
            )
        if status != 200:
            return None, content_type, FetchKind.MARKDOWN, status, None, etag, last_modified, body
        if is_probable_html(resp.headers.get("content-type"), body):
            return None, content_type, FetchKind.MARKDOWN, status, None, etag, last_modified, body
        kind = FetchKind.MARKDOWN
        if md_url.endswith(".md.txt"):
            kind = FetchKind.MARKDOWN_TXT
        return body, content_type, kind, status, None, etag, last_modified, None
    except Exception as exc:
        LOG.debug("fetch_markdown failed for %s: %s", md_url, exc)
        return None, None, FetchKind.MARKDOWN, None, exc, None, None, None


# ====================
# HTML fetch
# ====================

def fetch_html(
    url: str,
    session: requests.Session,
    config: RunConfig,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[Exception], Optional[str], Optional[str]]:
    try:
        resp = session.get(url, timeout=config.request_timeout, headers=headers)
        status = resp.status_code
        content_type = resp.headers.get("content-type")
        etag = resp.headers.get("etag")
        last_modified = resp.headers.get("last-modified")
        if config.max_body_bytes > 0:
            length = resp.headers.get("content-length")
            if length and length.isdigit() and int(length) > config.max_body_bytes:
                return None, content_type, status, OversizeError("html response too large"), etag, last_modified
        body = resp.text
        if config.max_body_bytes > 0 and len(body.encode("utf-8", errors="ignore")) > config.max_body_bytes:
            return None, content_type, status, OversizeError("html response too large"), etag, last_modified
        return body, content_type, status, None, etag, last_modified
    except Exception as exc:
        LOG.debug("fetch_html failed for %s: %s", url, exc)
        return None, None, None, exc, None, None


# ====================
# HTML -> Markdown
# ====================

def _pick_main_container(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    main = soup.find("main")
    if main:
        return str(main)

    article = soup.find("article")
    if article:
        return str(article)

    body = soup.find("body")
    if body:
        return str(body)

    return html


def html_to_markdown(html: str, extractor: str = "raw") -> Optional[str]:
    try:
        if extractor == "readability":
            try:
                from readability import Document
            except Exception as exc:
                LOG.debug("readability not available: %s", exc)
                return None
            doc = Document(html)
            summary_html = doc.summary()
            return md_convert(summary_html, heading_style="ATX")
        if extractor == "trafilatura":
            try:
                from trafilatura import extract
            except Exception as exc:
                LOG.debug("trafilatura not available: %s", exc)
                return None
            text = extract(html)
            return text
        fragment = _pick_main_container(html)
        return md_convert(fragment, heading_style="ATX")
    except Exception as exc:
        LOG.debug("html_to_markdown failed: %s", exc)
        return None
