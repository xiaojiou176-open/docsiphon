# ====================
# Local test server
# ====================
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Tuple, Callable, Union


ResponseTuple = Tuple[int, Dict[str, str], bytes | str]
RouteValue = Union[ResponseTuple, Callable[[], ResponseTuple]]


class TestServer:
    __test__ = False

    def __init__(self, routes: Dict[str, RouteValue]) -> None:
        self.routes = routes
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.base_url: str = ""

    def __enter__(self) -> "TestServer":
        routes = self.routes

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                path = self.path.split("?", 1)[0]
                if path in routes:
                    value = routes[path]
                    if callable(value):
                        status, headers, body = value()
                    else:
                        status, headers, body = value
                else:
                    status, headers, body = 404, {"Content-Type": "text/plain"}, "not found"
                payload = body.encode("utf-8") if isinstance(body, str) else body
                self.send_response(status)
                for header_name, header_value in headers.items():
                    self.send_header(header_name, header_value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, fmt: str, *args) -> None:
                """Suppress HTTP server log noise during tests."""
                pass

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        host, port = self._httpd.server_address
        self.base_url = f"http://{host}:{port}"
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
