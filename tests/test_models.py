from __future__ import annotations

import os
import tempfile
import unittest

import models
from db import get_connection, init_db


class ModelsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = get_connection(self.path)
        init_db(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        os.remove(self.path)

    def test_subtask_rollup_only_when_all_subtasks_complete(self):
        parent_id = models.create_task(self.conn, "Plan trip", priority="high")
        sub1 = models.create_task(self.conn, "Book flight", parent_id=parent_id)
        sub2 = models.create_task(self.conn, "Book hotel", parent_id=parent_id)

        models.toggle_complete(self.conn, sub1)
        self.assertFalse(models.get_task(self.conn, parent_id).completed)

        models.toggle_complete(self.conn, sub2)
        self.assertTrue(models.get_task(self.conn, parent_id).completed)

        models.toggle_complete(self.conn, sub1)
        self.assertFalse(models.get_task(self.conn, parent_id).completed)

    def test_priority_then_due_date_sort_order(self):
        models.create_task(self.conn, "low task", priority="low", due_date="2026-01-01")
        models.create_task(self.conn, "high task, later due", priority="high", due_date="2026-06-01")
        models.create_task(self.conn, "high task, sooner due", priority="high", due_date="2026-02-01")
        titles = [t.title for t in models.list_tasks(self.conn)]
        self.assertEqual(
            titles,
            ["high task, sooner due", "high task, later due", "low task"],
        )

    def test_tag_filter_matches_task_or_its_subtasks(self):
        home_id = models.create_task(self.conn, "Groceries", tags=["home"])
        work_id = models.create_task(self.conn, "Fix bug", tags=["work"])
        models.create_task(self.conn, "Buy milk", parent_id=home_id, tags=["home"])
        result_ids = [t.id for t in models.list_tasks(self.conn, tag="home")]
        self.assertEqual(result_ids, [home_id])
        self.assertNotIn(work_id, result_ids)

    def test_delete_cascades_to_subtasks(self):
        parent_id = models.create_task(self.conn, "Parent")
        child_id = models.create_task(self.conn, "Child", parent_id=parent_id)
        models.delete_task(self.conn, parent_id)
        self.assertIsNone(models.get_task(self.conn, parent_id))
        self.assertIsNone(models.get_task(self.conn, child_id))

    def test_create_task_rejects_empty_title(self):
        with self.assertRaises(ValueError):
            models.create_task(self.conn, "   ")

    def test_overdue_flag(self):
        task_id = models.create_task(self.conn, "Past due", due_date="2000-01-01")
        self.assertTrue(models.get_task(self.conn, task_id).is_overdue)
        models.toggle_complete(self.conn, task_id)
        self.assertFalse(models.get_task(self.conn, task_id).is_overdue)


class PersistenceTestCase(unittest.TestCase):
    def test_persistence_round_trip(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            conn = get_connection(path)
            init_db(conn)
            parent_id = models.create_task(
                conn, "Ship capstone", priority="high", due_date="2026-07-15",
                tags=["school", "urgent"],
            )
            models.create_task(conn, "Write tests", parent_id=parent_id, priority="med")
            conn.close()

            reopened = get_connection(path)
            tasks = models.list_tasks(reopened)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].title, "Ship capstone")
            self.assertEqual(tasks[0].priority, "high")
            self.assertEqual(tasks[0].due_date, "2026-07-15")
            self.assertEqual(set(tasks[0].tags), {"school", "urgent"})
            self.assertEqual(len(tasks[0].subtasks), 1)
            self.assertEqual(tasks[0].subtasks[0].title, "Write tests")
            reopened.close()
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
