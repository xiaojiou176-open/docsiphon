# ====================
# Reporting
# ====================
from __future__ import annotations

import html as html_lib
import json
import logging
import os
from typing import Dict, Any, Iterable, Iterator

from .models import PageRecord, FetchStatus

LOG = logging.getLogger(__name__)


def write_report(output_dir: str, data: Dict[str, Any]) -> None:
    path = os.path.join(output_dir, "report.json")
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        LOG.debug("write_report failed for %s: %s", path, exc)
        return


def write_url_list(output_dir: str, urls: list[str]) -> None:
    path = os.path.join(output_dir, "urls.txt")
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
    except Exception as exc:
        LOG.debug("write_url_list failed for %s: %s", path, exc)
        return


def _safe_rel(path: str, base: str) -> str:
    try:
        return os.path.relpath(path, base)
    except Exception as exc:
        LOG.debug("relpath fallback for %s against %s: %s", path, base, exc)
        return path


def _iter_manifest(path: str) -> Iterator[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as exc:
                    LOG.debug("manifest row decode failed in %s: %s", path, exc)
                    continue
                if isinstance(payload, dict):
                    yield payload
    except Exception as exc:
        LOG.debug("iter_manifest failed for %s: %s", path, exc)
        return


def write_index(output_dir: str, records: Iterable[PageRecord]) -> None:
    path = os.path.join(output_dir, "index.json")
    try:
        os.makedirs(output_dir, exist_ok=True)
        payload = []
        ordered = sorted(records, key=lambda item: item.url)
        for record in ordered:
            payload.append(
                {
                    "url": record.url,
                    "status": record.status.value,
                    "fetch_kind": record.fetch_kind.value,
                    "http_status": record.http_status,
                    "content_type": record.content_type,
                    "bytes_written": record.bytes_written,
                    "out_path": _safe_rel(record.out_path, output_dir) if record.out_path else None,
                    "note": record.note.value if record.note else None,
                    "error": record.error,
                    "error_kind": record.error_kind.value if record.error_kind else None,
                    "error_snapshot": _safe_rel(record.error_snapshot, output_dir) if record.error_snapshot else None,
                    "etag": record.etag,
                    "last_modified": record.last_modified,
                    "content_hash": record.content_hash,
                    "run_id": record.run_id,
                    "extractor": record.extractor.value if record.extractor else None,
                    "title": record.title,
                    "h1": record.h1,
                }
            )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        LOG.debug("write_index failed for %s: %s", path, exc)
        return


def write_index_from_manifest(manifest_path: str, output_dir: str) -> None:
    path = os.path.join(output_dir, "index.json")
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("[")
            first = True
            for record in _iter_manifest(manifest_path):
                item = {
                    "url": record.get("url"),
                    "status": record.get("status"),
                    "fetch_kind": record.get("fetch_kind"),
                    "http_status": record.get("http_status"),
                    "content_type": record.get("content_type"),
                    "bytes_written": record.get("bytes_written", 0),
                    "out_path": _safe_rel(record.get("out_path"), output_dir) if record.get("out_path") else None,
                    "note": record.get("note"),
                    "error": record.get("error"),
                    "error_kind": record.get("error_kind"),
                    "error_snapshot": _safe_rel(record.get("error_snapshot"), output_dir)
                    if record.get("error_snapshot")
                    else None,
                    "etag": record.get("etag"),
                    "last_modified": record.get("last_modified"),
                    "content_hash": record.get("content_hash"),
                    "run_id": record.get("run_id"),
                    "extractor": record.get("extractor"),
                    "title": record.get("title"),
                    "h1": record.get("h1"),
                }
                if not first:
                    f.write(",")
                f.write(json.dumps(item, ensure_ascii=False))
                first = False
            f.write("]")
    except Exception as exc:
        LOG.debug("write_index_from_manifest failed for %s: %s", path, exc)
        return


def _build_tree(paths: Iterable[str]) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    for path in paths:
        parts = [p for p in path.split(os.sep) if p]
        node = root
        for part in parts:
            node = node.setdefault(part, {})
    return root


def _render_tree(node: Dict[str, Any], depth: int = 0) -> list[str]:
    lines: list[str] = []
    for name in sorted(node.keys()):
        indent = "  " * depth
        lines.append(f"{indent}- {name}")
        child = node[name]
        if isinstance(child, dict) and child:
            lines.extend(_render_tree(child, depth + 1))
    return lines


def write_toc(output_dir: str, records: Iterable[PageRecord]) -> None:
    path = os.path.join(output_dir, "toc.md")
    try:
        os.makedirs(output_dir, exist_ok=True)
        paths = []
        for record in records:
            if record.status != FetchStatus.OK or not record.out_path:
                continue
            paths.append(_safe_rel(record.out_path, output_dir))
        tree = _build_tree(paths)
        lines = ["# TOC", ""]
        lines.extend(_render_tree(tree))
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as exc:
        LOG.debug("write_toc failed for %s: %s", path, exc)
        return


def write_toc_from_manifest(manifest_path: str, output_dir: str) -> None:
    path = os.path.join(output_dir, "toc.md")
    try:
        os.makedirs(output_dir, exist_ok=True)
        tree: Dict[str, Any] = {}
        for record in _iter_manifest(manifest_path):
            if record.get("status") != FetchStatus.OK.value:
                continue
            out_path = record.get("out_path")
            if not out_path:
                continue
            rel = _safe_rel(out_path, output_dir)
            parts = [p for p in rel.split(os.sep) if p]
            node = tree
            for part in parts:
                node = node.setdefault(part, {})
        lines = ["# TOC", ""]
        lines.extend(_render_tree(tree))
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as exc:
        LOG.debug("write_toc_from_manifest failed for %s: %s", path, exc)
        return


def write_report_html(output_dir: str, summary: Dict[str, Any], records: Iterable[PageRecord]) -> None:
    path = os.path.join(output_dir, "report.html")
    try:
        os.makedirs(output_dir, exist_ok=True)
        def _esc(value: object) -> str:
            return html_lib.escape(str(value)) if value is not None else ""

        error_rows = []
        for record in records:
            if record.status == FetchStatus.OK:
                continue
            snapshot = _safe_rel(record.error_snapshot, output_dir) if record.error_snapshot else ""
            error_rows.append(
                {
                    "url_raw": record.url,
                    "url": _esc(record.url),
                    "status": _esc(record.status.value),
                    "note": _esc(record.note.value if record.note else ""),
                    "error_kind": _esc(record.error_kind.value if record.error_kind else ""),
                    "http_status": _esc(record.http_status if record.http_status is not None else ""),
                    "snapshot": snapshot,
                }
            )
        error_rows.sort(key=lambda row: row["url_raw"])
        status_counts = summary.get("status_counts", {})
        http_counts = summary.get("http_status_counts", {})
        note_counts = summary.get("note_counts", {})
        error_kind_counts = summary.get("error_kind_counts", {})

        def _top_n(counter, n=5):
            items = sorted(counter.items(), key=lambda item: item[1], reverse=True)
            return items[:n]

        def _bar(label, value, max_value):
            width = 0 if max_value <= 0 else int((value / max_value) * 240)
            return (
                f"<div><span>{_esc(label)}</span>"
                f"<div style='display:inline-block;margin-left:6px;height:8px;width:{width}px;background:#4a90e2'></div>"
                f" <span>{_esc(value)}</span></div>"
            )

        html = [
            "<!doctype html>",
            "<html lang='en'>",
            "<head>",
            "  <meta charset='utf-8' />",
            "  <meta name='viewport' content='width=device-width, initial-scale=1' />",
            "  <title>Docsiphon report</title>",
            "  <style>",
            "    body{font-family:Arial,Helvetica,sans-serif;margin:24px;color:#222}",
            "    h1{font-size:20px;margin-bottom:8px}",
            "    table{border-collapse:collapse;width:100%;margin-top:16px}",
            "    th,td{border:1px solid #ddd;padding:6px 8px;font-size:12px;vertical-align:top}",
            "    th{background:#f5f5f5;text-align:left}",
            "    .badge{display:inline-block;padding:2px 6px;border-radius:4px;background:#eee}",
            "    .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:12px}",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>Export Report</h1>",
            "  <div>",
        ]
        for key in sorted(summary.keys()):
            html.append(f"    <div><span class='badge'>{_esc(key)}</span> {_esc(summary[key])}</div>")
        html.extend(["  </div>", "  <div class='grid'>"])
        max_status = max(status_counts.values()) if status_counts else 0
        max_http = max(http_counts.values()) if http_counts else 0
        html.append("    <div><h3>Status Distribution</h3>")
        for key, value in sorted(status_counts.items()):
            html.append(_bar(key, value, max_status))
        html.append("    </div>")
        html.append("    <div><h3>HTTP Status Distribution</h3>")
        for key, value in sorted(http_counts.items()):
            html.append(_bar(key, value, max_http))
        html.append("    </div>")
        html.append("  </div>")

        html.append("  <div class='grid'>")
        html.append("    <div><h3>Failure Reasons TopN</h3>")
        for key, value in _top_n(note_counts):
            html.append(_bar(key, value, max(note_counts.values()) if note_counts else 0))
        html.append("    </div>")
        html.append("    <div><h3>Error Kind TopN</h3>")
        for key, value in _top_n(error_kind_counts):
            html.append(_bar(key, value, max(error_kind_counts.values()) if error_kind_counts else 0))
        html.append("    </div>")
        html.append("    <div><h3>Extractor Distribution</h3>")
        extractor_counts = summary.get("extractor_counts", {})
        for key, value in _top_n(extractor_counts, 6):
            html.append(_bar(key, value, max(extractor_counts.values()) if extractor_counts else 0))
        html.append("    </div>")
        html.append("  </div>")

        html.extend(
            [
                "  <h2>Failures & Skips</h2>",
                "  <table>",
                "    <thead><tr><th>URL</th><th>Status</th><th>Note</th><th>Error Kind</th><th>HTTP</th><th>Snapshot</th></tr></thead>",
                "    <tbody>",
            ]
        )
        for row in error_rows:
            snapshot = row["snapshot"]
            snap_cell = ""
            if snapshot:
                snap_esc = _esc(snapshot)
                snap_cell = f"<a href='{snap_esc}' target='_blank' rel='noopener'>{snap_esc}</a>"
            html.append(
                "    <tr>"
                f"<td>{row['url']}</td>"
                f"<td>{row['status']}</td>"
                f"<td>{row['note']}</td>"
                f"<td>{row['error_kind']}</td>"
                f"<td>{row['http_status']}</td>"
                f"<td>{snap_cell}</td>"
                "</tr>"
            )
        html.extend(["    </tbody>", "  </table>", "</body>", "</html>"])
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(html))
    except Exception as exc:
        LOG.debug("write_report_html failed for %s: %s", path, exc)
        return


def write_report_html_from_manifest(manifest_path: str, output_dir: str, summary: Dict[str, Any]) -> None:
    path = os.path.join(output_dir, "report.html")
    try:
        os.makedirs(output_dir, exist_ok=True)
        def _esc(value: object) -> str:
            return html_lib.escape(str(value)) if value is not None else ""

        status_counts = summary.get("status_counts", {})
        http_counts = summary.get("http_status_counts", {})
        note_counts = summary.get("note_counts", {})
        error_kind_counts = summary.get("error_kind_counts", {})

        def _top_n(counter, n=5):
            items = sorted(counter.items(), key=lambda item: item[1], reverse=True)
            return items[:n]

        def _bar(label, value, max_value):
            width = 0 if max_value <= 0 else int((value / max_value) * 240)
            return (
                f"<div><span>{_esc(label)}</span>"
                f"<div style='display:inline-block;margin-left:6px;height:8px;width:{width}px;background:#4a90e2'></div>"
                f" <span>{_esc(value)}</span></div>"
            )

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join([
                "<!doctype html>",
                "<html lang='en'>",
                "<head>",
                "  <meta charset='utf-8' />",
                "  <meta name='viewport' content='width=device-width, initial-scale=1' />",
                "  <title>Docsiphon report</title>",
                "  <style>",
                "    body{font-family:Arial,Helvetica,sans-serif;margin:24px;color:#222}",
                "    h1{font-size:20px;margin-bottom:8px}",
                "    table{border-collapse:collapse;width:100%;margin-top:16px}",
                "    th,td{border:1px solid #ddd;padding:6px 8px;font-size:12px;vertical-align:top}",
                "    th{background:#f5f5f5;text-align:left}",
                "    .badge{display:inline-block;padding:2px 6px;border-radius:4px;background:#eee}",
                "    .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:12px}",
                "  </style>",
                "</head>",
                "<body>",
                "  <h1>Export Report</h1>",
                "  <div>",
            ]))
            for key in sorted(summary.keys()):
                f.write(f"\n    <div><span class='badge'>{_esc(key)}</span> {_esc(summary[key])}</div>")
            f.write("\n  </div>\n  <div class='grid'>")
            max_status = max(status_counts.values()) if status_counts else 0
            max_http = max(http_counts.values()) if http_counts else 0
            f.write("\n    <div><h3>Status Distribution</h3>")
            for key, value in sorted(status_counts.items()):
                f.write("\n" + _bar(key, value, max_status))
            f.write("\n    </div>\n    <div><h3>HTTP Status Distribution</h3>")
            for key, value in sorted(http_counts.items()):
                f.write("\n" + _bar(key, value, max_http))
            f.write("\n    </div>\n  </div>")

            f.write("\n  <div class='grid'>")
            f.write("\n    <div><h3>Failure Reasons TopN</h3>")
            for key, value in _top_n(note_counts):
                f.write("\n" + _bar(key, value, max(note_counts.values()) if note_counts else 0))
            f.write("\n    </div>")
            f.write("\n    <div><h3>Error Kind TopN</h3>")
            for key, value in _top_n(error_kind_counts):
                f.write("\n" + _bar(key, value, max(error_kind_counts.values()) if error_kind_counts else 0))
            f.write("\n    </div>")
            f.write("\n    <div><h3>Extractor Distribution</h3>")
            extractor_counts = summary.get("extractor_counts", {})
            for key, value in _top_n(extractor_counts, 6):
                f.write("\n" + _bar(key, value, max(extractor_counts.values()) if extractor_counts else 0))
            f.write("\n    </div>")
            f.write("\n  </div>")

            f.write(
                "\n  <h2>Failures & Skips</h2>"
                "\n  <table>"
                "\n    <thead><tr><th>URL</th><th>Status</th><th>Note</th><th>Error Kind</th><th>HTTP</th><th>Snapshot</th></tr></thead>"
                "\n    <tbody>"
            )
            for record in _iter_manifest(manifest_path):
                status = record.get("status")
                if status == FetchStatus.OK.value:
                    continue
                snapshot = _safe_rel(record.get("error_snapshot"), output_dir) if record.get("error_snapshot") else ""
                snap_cell = ""
                if snapshot:
                    snap_esc = _esc(snapshot)
                    snap_cell = f"<a href='{snap_esc}' target='_blank' rel='noopener'>{snap_esc}</a>"
                f.write(
                    "\n    <tr>"
                    f"<td>{_esc(record.get('url'))}</td>"
                    f"<td>{_esc(status)}</td>"
                    f"<td>{_esc(record.get('note'))}</td>"
                    f"<td>{_esc(record.get('error_kind'))}</td>"
                    f"<td>{_esc(record.get('http_status'))}</td>"
                    f"<td>{snap_cell}</td>"
                    "</tr>"
                )
            f.write("\n    </tbody>\n  </table>\n</body>\n</html>")
    except Exception as exc:
        LOG.debug("write_report_html_from_manifest failed for %s: %s", path, exc)
        return
