# CLAUDE.md

## Project

ToDo-List is a personal task manager built because no existing to-do app fit my workflow. Unlike a generic checklist app, it's built around three things I actually use: priority + due dates + tags for organizing tasks, and quick capture + subtasks for getting tasks in fast and breaking down bigger ones. It's a single-user, local-first app — no accounts, no sync, no collaboration features. The scope is deliberately small: a task model, a way to add/edit/complete/delete tasks and subtasks, and views that sort/filter by priority, due date, and tag.

## Tech stack

Python (Flask) for the backend, SQLite for storage, and server-rendered HTML/vanilla JS for the frontend (Jinja templates, one small JS file for quick-capture and inline edit interactions — no frontend framework or build step). This stack was chosen for minimal moving parts: SQLite needs no separate server, Flask keeps routes and business logic easy to unit-test with pytest, and skipping a JS framework means no build tooling to maintain for a single-user app. Task data (priority, due date, tags, subtask links) maps cleanly onto SQLite tables and Flask routes.

## Conventions

- Use type hints on all function signatures.
- No global mutable state — pass the DB connection/session explicitly; don't stash data in module-level variables.
- Prefer small, focused functions (one responsibility each) over large route handlers; keep business logic (task rules, sorting, rollup of subtask completion) out of route handlers and in a separate module so it's unit-testable without spinning up Flask.
- Keep the task schema (title, priority, due date, tags, parent_id) as the single source of truth — don't duplicate task fields in multiple places.
- Write a docstring (one line is fine) for any function whose behavior isn't obvious from its name and signature.
- Match existing naming and file layout before introducing new patterns.

## Do not

- Don't add new dependencies (Python packages, JS libraries, CSS frameworks) without asking first — the point of this stack is staying minimal.
- Don't modify or weaken tests to make them pass. If a test fails, fix the code or flag that the test's expectation seems wrong — don't change the assertion just to get green.
- Don't introduce a database migration framework, ORM, or frontend build step — SQLite via the stdlib `sqlite3` module and plain SQL are enough at this scale.
- Don't add user accounts, auth, or multi-user support — this is intentionally single-user.
- Don't silently change the task schema (field names/types) — call it out explicitly since BUILD_LOG.md and tests depend on it staying stable.
