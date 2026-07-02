from __future__ import annotations

from io import BytesIO
from urllib.parse import urlencode


def call(app, method: str, path: str, form: dict | None = None, query: str = ""):
    body = urlencode(form).encode("utf-8") if form else b""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "wsgi.input": BytesIO(body),
        "wsgi.errors": BytesIO(),
    }
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    result = b"".join(app(environ, start_response))
    return captured["status"], dict(captured["headers"]), result
