from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date

PRIORITY_ORDER = {"high": 0, "med": 1, "low": 2}


@dataclass
class Task:
    id: int
    title: str
    priority: str
    due_date: str | None
    parent_id: int | None
    completed: bool
    created_at: str
    tags: list[str] = field(default_factory=list)
    subtasks: list["Task"] = field(default_factory=list)

    @property
    def is_overdue(self) -> bool:
        if self.completed or not self.due_date:
            return False
        return self.due_date < date.today().isoformat()


def _clean_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    cleaned: list[str] = []
    for t in tags:
        t = t.strip().lower()
        if t and t not in cleaned:
            cleaned.append(t)
    return cleaned


def create_task(
    conn: sqlite3.Connection,
    title: str,
    priority: str = "low",
    due_date: str | None = None,
    parent_id: int | None = None,
    tags: list[str] | None = None,
) -> int:
    if not title or not title.strip():
        raise ValueError("title must not be empty")
    if priority not in PRIORITY_ORDER:
        raise ValueError(f"invalid priority: {priority}")
    cur = conn.execute(
        "INSERT INTO tasks (title, priority, due_date, parent_id) VALUES (?, ?, ?, ?)",
        (title.strip(), priority, due_date, parent_id),
    )
    task_id = cur.lastrowid
    for tag in _clean_tags(tags):
        conn.execute(
            "INSERT OR IGNORE INTO task_tags (task_id, tag) VALUES (?, ?)",
            (task_id, tag),
        )
    conn.commit()
    return task_id


def _row_to_task(conn: sqlite3.Connection, row: sqlite3.Row) -> Task:
    tags = [
        r["tag"]
        for r in conn.execute(
            "SELECT tag FROM task_tags WHERE task_id = ? ORDER BY tag", (row["id"],)
        )
    ]
    return Task(
        id=row["id"],
        title=row["title"],
        priority=row["priority"],
        due_date=row["due_date"],
        parent_id=row["parent_id"],
        completed=bool(row["completed"]),
        created_at=row["created_at"],
        tags=tags,
    )


def get_task(conn: sqlite3.Connection, task_id: int) -> Task | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row_to_task(conn, row) if row else None


def get_subtasks(conn: sqlite3.Connection, parent_id: int) -> list[Task]:
    rows = conn.execute("SELECT * FROM tasks WHERE parent_id = ?", (parent_id,)).fetchall()
    subtasks = [_row_to_task(conn, r) for r in rows]
    subtasks.sort(key=_sort_key)
    return subtasks


def _sort_key(task: Task) -> tuple:
    return (PRIORITY_ORDER[task.priority], task.due_date or "9999-99-99")


def list_tasks(conn: sqlite3.Connection, tag: str | None = None) -> list[Task]:
    rows = conn.execute("SELECT * FROM tasks WHERE parent_id IS NULL").fetchall()
    tasks = [_row_to_task(conn, r) for r in rows]
    for t in tasks:
        t.subtasks = get_subtasks(conn, t.id)

    if tag:
        tag = tag.strip().lower()
        tasks = [t for t in tasks if tag in t.tags or any(tag in s.tags for s in t.subtasks)]

    tasks.sort(key=_sort_key)
    return tasks


def update_task(
    conn: sqlite3.Connection,
    task_id: int,
    title: str | None = None,
    priority: str | None = None,
    due_date: str | None | type(...) = ...,
    tags: list[str] | None = None,
) -> None:
    task = get_task(conn, task_id)
    if task is None:
        raise ValueError(f"no task with id {task_id}")

    new_title = title.strip() if title else task.title
    new_priority = priority if priority is not None else task.priority
    if new_priority not in PRIORITY_ORDER:
        raise ValueError(f"invalid priority: {new_priority}")
    new_due = task.due_date if due_date is ... else due_date

    conn.execute(
        "UPDATE tasks SET title = ?, priority = ?, due_date = ? WHERE id = ?",
        (new_title, new_priority, new_due, task_id),
    )
    if tags is not None:
        conn.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
        for t in _clean_tags(tags):
            conn.execute(
                "INSERT OR IGNORE INTO task_tags (task_id, tag) VALUES (?, ?)",
                (task_id, t),
            )
    conn.commit()


def delete_task(conn: sqlite3.Connection, task_id: int) -> None:
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()


def toggle_complete(conn: sqlite3.Connection, task_id: int) -> None:
    task = get_task(conn, task_id)
    if task is None:
        raise ValueError(f"no task with id {task_id}")
    new_state = not task.completed
    conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (int(new_state), task_id))
    conn.commit()
    if task.parent_id is not None:
        _rollup_parent(conn, task.parent_id)


def _rollup_parent(conn: sqlite3.Connection, parent_id: int) -> None:
    subtasks = get_subtasks(conn, parent_id)
    if not subtasks:
        return
    all_done = all(s.completed for s in subtasks)
    conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (int(all_done), parent_id))
    conn.commit()
