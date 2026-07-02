from __future__ import annotations

from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from jinja2 import Environment, FileSystemLoader, select_autoescape

import models
from db import get_connection, init_db

TEMPLATES = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html"]),
)


def render(name: str, **context) -> bytes:
    return TEMPLATES.get_template(name).render(**context).encode("utf-8")


def parse_form(environ: dict) -> dict[str, str]:
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    body = environ["wsgi.input"].read(length) if length else b""
    parsed = parse_qs(body.decode("utf-8"))
    return {k: v[0] for k, v in parsed.items()}


def parse_query(environ: dict) -> dict[str, str]:
    parsed = parse_qs(environ.get("QUERY_STRING", ""))
    return {k: v[0] for k, v in parsed.items()}


def parse_tags(raw: str | None) -> list[str]:
    return [t for t in raw.split(",")] if raw else []


def redirect(start_response, location: str = "/"):
    start_response("302 Found", [("Location", location)])
    return [b""]


def not_found(start_response):
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"Not found"]


def make_app(db_path: str):
    with get_connection(db_path) as conn:
        init_db(conn)

    def application(environ, start_response):
        method = environ["REQUEST_METHOD"]
        path = environ["PATH_INFO"].rstrip("/") or "/"
        conn = get_connection(db_path)
        try:
            if method == "GET" and path == "/":
                query = parse_query(environ)
                tag = query.get("tag") or None
                tasks = models.list_tasks(conn, tag=tag)
                body = render("index.html", tasks=tasks, active_tag=tag)
                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                return [body]

            if method == "GET" and path == "/static/style.css":
                with open("static/style.css", "rb") as f:
                    body = f.read()
                start_response("200 OK", [("Content-Type", "text/css")])
                return [body]

            if method == "POST" and path == "/tasks":
                form = parse_form(environ)
                try:
                    parent_id = form.get("parent_id") or None
                    models.create_task(
                        conn,
                        form.get("title", ""),
                        priority=form.get("priority", "low"),
                        due_date=form.get("due_date") or None,
                        parent_id=int(parent_id) if parent_id else None,
                        tags=parse_tags(form.get("tags")),
                    )
                except ValueError:
                    pass  # blank/invalid quick-capture input -> silent no-op
                return redirect(start_response, "/")

            if method == "POST" and path.startswith("/tasks/"):
                parts = path.split("/")  # ["", "tasks", "<id>", "<action>"]
                if len(parts) == 4 and parts[2].isdigit():
                    task_id, action = int(parts[2]), parts[3]
                    try:
                        if action == "toggle":
                            models.toggle_complete(conn, task_id)
                            return redirect(start_response, "/")
                        if action == "delete":
                            models.delete_task(conn, task_id)
                            return redirect(start_response, "/")
                        if action == "edit":
                            form = parse_form(environ)
                            tags_raw = form.get("tags")
                            models.update_task(
                                conn,
                                task_id,
                                title=form.get("title") or None,
                                priority=form.get("priority") or None,
                                due_date=(form.get("due_date") or None),
                                tags=parse_tags(tags_raw) if tags_raw is not None else None,
                            )
                            return redirect(start_response, "/")
                    except ValueError:
                        # task_id doesn't exist 
                        return not_found(start_response)

            return not_found(start_response)
        finally:
            conn.close()

    return application


if __name__ == "__main__":
    app = make_app("todo.db")
    with make_server("", 5000, app) as httpd:
        print("Serving on http://localhost:5000")
        httpd.serve_forever()
