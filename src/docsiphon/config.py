# ====================
# Configuration
# ====================
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Optional, Tuple, Any

from .utils import DEFAULT_EXCLUDE_EXTS

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunConfig:
    base_url: str
    output_dir: str
    max_workers: int = 8
    request_timeout: int = 20
    rate_limit_per_sec: float = 5.0
    host_rate_limit_per_sec: float = 0.0
    host_max_concurrency: int = 0
    user_agent: str = "Mozilla/5.0 (docsiphon/0.1)"
    retry_total: int = 4
    retry_timeout: int = 2
    retry_connection: int = 2
    retry_dns: int = 1
    retry_http_429: int = 3
    retry_http_5xx: int = 2
    retry_unknown: int = 0
    retry_backoff_base: float = 0.5
    retry_backoff_max: float = 8.0
    retry_backoff_jitter: float = 0.3
    max_pages: int = 5000
    max_depth: int = 6
    scope_prefix: Optional[str] = None
    site_root: Optional[str] = None
    frontmatter: bool = False
    frontmatter_timestamp: bool = True
    html_fallback: bool = True
    exclude_exts: FrozenSet[str] = DEFAULT_EXCLUDE_EXTS
    include_regex: Optional[str] = None
    exclude_regex: Optional[str] = None
    ignore_query_params: Tuple[str, ...] = ()
    ignore_query_prefixes: Tuple[str, ...] = ("utm_",)
    content_extractor: str = "auto"
    save_html: bool = False
    save_error_html: bool = True
    ignore_robots: bool = False
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    auth: Optional[Tuple[str, str]] = None
    token: Optional[str] = None
    report_dir: Optional[str] = None
    manifest_sorted: bool = False
    error_snapshot_max_bytes: int = 200000
    error_snapshot_sample_ratio: float = 0.7
    error_snapshot_max_files: int = 0
    error_snapshot_max_total_bytes: int = 0
    max_body_bytes: int = 0
    resume: bool = False
    skip_existing: bool = False
    dry_run: bool = False
    manifest_cache_max_entries: int = 0


def _load_toml(path: str) -> Dict[str, Any]:
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            LOG.debug("No TOML parser available for %s", path)
            return {}
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        LOG.debug("Failed to load TOML profile %s: %s", path, exc)
        return {}
    return {}


def load_profile(path: str, profile_name: Optional[str] = None) -> Dict[str, Any]:
    data = _load_toml(path)
    if not data:
        return {}
    if profile_name:
        profiles = data.get("profiles")
        if isinstance(profiles, dict):
            named = profiles.get(profile_name)
            if isinstance(named, dict):
                return named
    profile = data.get("profile")
    if isinstance(profile, dict):
        return profile
    return {}
