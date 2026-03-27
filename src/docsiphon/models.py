# ====================
# Models and Enums
# ====================
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SourceKind(str, Enum):
    LLMS_TXT = "llms_txt"
    LLMS_FULL = "llms_full"
    SITEMAP = "sitemap"
    SEARCH_INDEX = "search_index"
    BFS = "bfs"


class FetchKind(str, Enum):
    NONE = "none"
    MARKDOWN = "markdown"
    MARKDOWN_TXT = "markdown_txt"
    HTML = "html"


class FetchStatus(str, Enum):
    OK = "ok"
    SKIPPED = "skipped"
    FAILED = "failed"


class ContentExtractor(str, Enum):
    AUTO = "auto"
    READABILITY = "readability"
    TRAFILATURA = "trafilatura"
    RAW = "raw"
    MARKDOWN = "markdown"


class ErrorKind(str, Enum):
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    DNS = "dns"
    HTTP_4XX = "http_4xx"
    HTTP_5XX = "http_5xx"
    HTTP_429 = "http_429"
    UNKNOWN = "unknown"


class NoteKind(str, Enum):
    MARKDOWN_NOT_AVAILABLE = "markdown_not_available"
    MARKDOWN_FETCH_ERROR = "markdown_fetch_error"
    MARKDOWN_IS_HTML = "markdown_is_html"
    MARKDOWN_NON_TEXT = "markdown_non_text"
    OVERSIZE = "oversize"
    EXCLUDED_EXTENSION = "excluded_extension"
    NON_HTML_TEXT = "non_html_text"
    MAX_PAGES_LIMIT = "max_pages_limit"
    HTML_FETCH_FAILED = "html_fetch_failed"
    HTML_TO_MARKDOWN_FAILED = "html_to_markdown_failed"
    NON_TEXT_CONTENT_TYPE = "non_text_content_type"
    PATH_COLLISION = "path_collision"
    RESUME_SKIP = "resume_skip"
    SKIP_EXISTING = "skip_existing"
    NOT_MODIFIED = "not_modified"
    FILTERED_OUT = "filtered_out"
    ROBOTS_DISALLOW = "robots_disallow"
    ERROR_SNAPSHOT = "error_snapshot"


@dataclass
class DiscoveryResult:
    source: SourceKind
    urls: List[str]
    meta: Dict[str, str] = field(default_factory=dict)


@dataclass
class PageRecord:
    url: str
    fetched_url: str
    source: SourceKind
    fetch_kind: FetchKind
    status: FetchStatus
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    bytes_written: int = 0
    out_path: Optional[str] = None
    note: Optional[NoteKind] = None
    error: Optional[str] = None
    error_kind: Optional[ErrorKind] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    content_hash: Optional[str] = None
    error_snapshot: Optional[str] = None
    extractor: Optional[ContentExtractor] = None
    title: Optional[str] = None
    h1: Optional[str] = None
    run_id: Optional[str] = None
    manifest_version: str = "1.1"
