from __future__ import annotations

import os
import tempfile
import unittest

from db import get_connection
from webapp import make_app

from wsgi_client import call


class WebAppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = make_app(self.path)

    def tearDown(self) -> None:
        os.remove(self.path)

    def _first_task_id(self) -> int:
        conn = get_connection(self.path)
        row = conn.execute("SELECT id FROM tasks ORDER BY id LIMIT 1").fetchone()
        conn.close()
        return row["id"]

    def test_index_loads_empty(self):
        status, _, body = call(self.app, "GET", "/")
        self.assertEqual(status, "200 OK")
        self.assertIn(b"Nothing here yet", body)

    def test_quick_capture_creates_task(self):
        call(self.app, "POST", "/tasks", form={"title": "Buy milk"})
        _, _, body = call(self.app, "GET", "/")
        self.assertIn(b"Buy milk", body)

    def test_quick_capture_blank_title_is_noop(self):
        call(self.app, "POST", "/tasks", form={"title": "   "})
        _, _, body = call(self.app, "GET", "/")
        self.assertIn(b"Nothing here yet", body)

    def test_toggle_route_and_rollup(self):
        call(self.app, "POST", "/tasks", form={"title": "Parent"})
        parent_id = self._first_task_id()
        call(self.app, "POST", "/tasks", form={"title": "Child", "parent_id": str(parent_id)})

        conn = get_connection(self.path)
        child_id = conn.execute(
            "SELECT id FROM tasks WHERE parent_id = ?", (parent_id,)
        ).fetchone()["id"]
        conn.close()

        call(self.app, "POST", f"/tasks/{child_id}/toggle")

        conn = get_connection(self.path)
        parent_completed = conn.execute(
            "SELECT completed FROM tasks WHERE id = ?", (parent_id,)
        ).fetchone()["completed"]
        conn.close()
        self.assertEqual(parent_completed, 1)

    def test_tag_filter_query_param(self):
        call(self.app, "POST", "/tasks", form={"title": "Work thing", "tags": "work"})
        call(self.app, "POST", "/tasks", form={"title": "Home thing", "tags": "home"})
        _, _, body = call(self.app, "GET", "/", query="tag=home")
        self.assertIn(b"Home thing", body)
        self.assertNotIn(b"Work thing", body)

    def test_delete_route(self):
        call(self.app, "POST", "/tasks", form={"title": "Temp task"})
        task_id = self._first_task_id()
        call(self.app, "POST", f"/tasks/{task_id}/delete")
        _, _, body = call(self.app, "GET", "/")
        self.assertNotIn(b"Temp task", body)

    def test_edit_route_updates_fields(self):
        call(self.app, "POST", "/tasks", form={"title": "Old title"})
        task_id = self._first_task_id()
        call(self.app, "POST", f"/tasks/{task_id}/edit", form={
            "title": "New title", "priority": "high", "tags": "urgent",
        })
        _, _, body = call(self.app, "GET", "/")
        self.assertIn(b"New title", body)
        self.assertNotIn(b"Old title", body)

    def test_toggle_missing_task_is_404_not_500(self):
        status, _, _ = call(self.app, "POST", "/tasks/99999/toggle")
        self.assertEqual(status, "404 Not Found")

    def test_edit_missing_task_is_404_not_500(self):
        status, _, _ = call(self.app, "POST", "/tasks/99999/edit", form={"title": "ghost"})
        self.assertEqual(status, "404 Not Found")

    def test_delete_missing_task_is_idempotent_noop(self):
        status, _, _ = call(self.app, "POST", "/tasks/99999/delete")
        self.assertEqual(status, "302 Found")

    def test_unknown_route_is_404(self):
        status, _, _ = call(self.app, "GET", "/nope")
        self.assertEqual(status, "404 Not Found")


if __name__ == "__main__":
    unittest.main()
