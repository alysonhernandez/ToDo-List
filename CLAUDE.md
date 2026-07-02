# CLAUDE.md

## Project

ToDo-List is a personal task manager built because no existing to-do app fit my workflow. Unlike a generic checklist app, it's built around three things I actually use: priority + due dates + tags for organizing tasks, and quick capture + subtasks for getting tasks in fast and breaking down bigger ones. It's a single-user, local-first app — no accounts, no sync, no collaboration features. The scope is deliberately small: a task model, a way to add/edit/complete/delete tasks and subtasks, and views that sort/filter by priority, due date, and tag.

## Tech stack

Python stdlib (`wsgiref` for the server, `sqlite3` for storage) plus Jinja2 for templates — no Flask, no JS framework, no build step. This started as a Flask plan but got revised to stdlib-only when the build environment turned out to have no network access to install packages; the upside is it's genuinely the minimal-dependency option (one third-party package, Jinja2, vs. Flask's whole stack) and every route can be unit-tested by calling the WSGI app directly with a constructed environ dict, no test client library needed. Business logic (task rules, sorting, rollup) lives in `models.py` with zero web-layer imports, so it's testable in complete isolation. Task data (priority, due date, tags, subtask links) maps directly onto SQLite tables via plain SQL.

## Conventions

- Use type hints on all function signatures.
- No global mutable state — pass the DB connection/session explicitly; don't stash data in module-level variables.
- Prefer small, focused functions (one responsibility each) over large route handlers; keep business logic (task rules, sorting, rollup of subtask completion) out of `webapp.py` and in `models.py` so it's unit-testable without spinning up a server.
- Keep the task schema (title, priority, due date, tags, parent_id) as the single source of truth — don't duplicate task fields in multiple places.
- Write a docstring (one line is fine) for any function whose behavior isn't obvious from its name and signature.
- Match existing naming and file layout before introducing new patterns.

## Do not

- Don't add new dependencies (Python packages, JS libraries, CSS frameworks) without asking first — the point of this stack is staying minimal.
- Don't modify or weaken tests to make them pass. If a test fails, fix the code or flag that the test's expectation seems wrong — don't change the assertion just to get green.
- Don't introduce a database migration framework, ORM, or frontend build step — SQLite via the stdlib `sqlite3` module and plain SQL are enough at this scale.
- Don't add user accounts, auth, or multi-user support — this is intentionally single-user.
- Don't silently change the task schema (field names/types) — call it out explicitly since BUILD_LOG.md and tests depend on it staying stable.
