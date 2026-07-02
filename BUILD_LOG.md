# Build Log

## Task 1 — Task model
- Brief: Define a task schema with title, priority (low/med/high), due date, tags, and parent/subtask links. Verify: create a task with all fields and confirm it saves and loads correctly.
- What Claude proposed: SQLite schema (`tasks` + `task_tags` tables, `ON DELETE CASCADE` for subtasks) in `db.py`, and a `Task` dataclass + `create_task`/`get_task` in `models.py`.
- What I changed before approving: The PRIORITY_ORDER because it made more sense
- Verification: `test_persistence_round_trip` (tests/test_models.py) creates a task with all fields, closes the connection, reopens the same db file, asserts every field round-trips. Ran via `python3 -m unittest`.
- One thing I learned: How to incorporate SQL into the ToDo List to keep everything organize in a db 

## Task 2 — Quick capture
- Brief: Add a single-keystroke or one-field entry point that creates a task with just a title, defaulting the rest. Verify: type a title and hit enter, confirm a new task appears with default priority/no due date.
- What Claude proposed: A single `<input name="title">` form at the top of `index.html` posting to `/tasks`; blank/whitespace-only titles silently no-op instead of erroring.
- What I changed before approving: What would be the default priority
- Verification: `test_quick_capture_creates_task` and `test_quick_capture_blank_title_is_noop` (tests/test_webapp.py), plus manual curl: `POST /tasks -d "title=Buy groceries"` then confirmed it appeared on `GET /`.
- One thing I learned: How to default otherwise user input fields

## Task 3 — Subtasks
- Brief: Allow any task to have nested subtasks that roll up to a parent's completion status. Verify: complete all subtasks and confirm the parent auto-marks (or prompts to mark) complete.
- What Claude proposed: `parent_id` self-reference on `tasks`; `toggle_complete()` recomputes the parent's completed flag via `_rollup_parent()` after every subtask toggle (all-done -> parent complete; any incomplete -> parent incomplete).
- What I changed before approving: Nothing, Claude's changes looked fine
- Verification: `test_subtask_rollup_only_when_all_subtasks_complete` — completes one of two subtasks (parent stays incomplete), completes both (parent auto-completes), un-completes one (parent un-completes). Also exercised live: created "Plan trip" -> "Book flight" via curl, toggled it, confirmed `completed=1` on the parent row in the db.
- One thing I learned: How to make nested db's

## Task 4 — Priority sorting
- Brief: Sort/group the task list by priority, with high-priority items always visible at the top. Verify: add tasks of mixed priority and confirm high-priority ones render first.
- What Claude proposed: `_sort_key()` in models.py sorts by `(priority_rank, due_date)`, applied in `list_tasks()`.
- What I changed before approving: Nothing, Claude's changes looked fine
- Verification: `test_priority_then_due_date_sort_order` — three tasks across priorities/dates, asserts exact render order.
- One thing I learned: How to sort by priority

## Task 5 — Due date handling
- Brief: Show overdue tasks distinctly (e.g., highlighted) and sort upcoming tasks by nearest due date. Verify: set a due date in the past and confirm it's visually flagged as overdue.
- What Claude proposed: `Task.is_overdue` property (past due date + not completed); template adds an `overdue` CSS class and "(overdue)" label when true.
- What I changed before approving: What would show when task is overdue
- Verification: `test_overdue_flag` (flags a 2000-01-01 task as overdue, un-flags it once completed). Manual: created a task due 2020-01-01, confirmed "overdue" text rendered in the HTML response.
- One thing I learned: How to handle tasks that are overdue

## Task 6 — Tagging + filtering
- Brief: Let tasks carry multiple tags and filter the list by one or more tags. Verify: tag several tasks the same way and confirm the filter returns exactly that set.
- What Claude proposed: `task_tags` join table; `list_tasks(tag=...)` filters top-level tasks by whether the task or any of its subtasks carries the tag; `?tag=` query param on `/` drives it from the URL.
- What I changed before approving: How the tags would appear
- Verification: `test_tag_filter_matches_task_or_its_subtasks`. Manual: tagged one task `home`, another `work`, hit `GET /?tag=home`, confirmed only the `home` task rendered.
- One thing I learned: How to sort certain tasks by tags

## Task 7 — Edit/delete flow
- Brief: Support inline editing and deletion of any task or subtask without losing sibling data. Verify: edit a task's title and delete a sibling subtask, confirm the rest of the list is unaffected.
- What Claude proposed: `/tasks/<id>/edit` and `/tasks/<id>/delete` routes; edit only overwrites fields present in the form.
- What I changed before approving: found via manual testing (not by me — flagging so the record is accurate): hitting `/tasks/<id>/toggle` or `/tasks/<id>/edit` with a nonexistent id crashed with a 500 instead of failing gracefully. Fixed by catching the `ValueError` from models.py and returning 404. Real bug, real fix — worth you re-reading that `try/except` block in `webapp.py` to make sure the fix makes sense to you.
- Verification: `test_toggle_missing_task_is_404_not_500`, `test_edit_missing_task_is_404_not_500`, `test_delete_missing_task_is_idempotent_noop`. Manual: edited a task's title/priority/due date via curl, confirmed the new title rendered and the old one didn't; deleted a task, confirmed it disappeared and siblings stayed intact.
- One thing I learned: How you can miss system crashes if you only test happy paths

## Task 8 — Persistence
- Brief: Save all tasks (with tags, priority, due dates, subtasks) so they survive a restart/reload. Verify: add tasks, reload the app, confirm everything is still there.
- What Claude proposed: SQLite file (`todo.db`) as the single source of truth; nothing held in memory between requests.
- What I changed before approving: Nothing, Claude's changes looked fine
- Verification: `test_persistence_round_trip`. Manual: started the server, added 3 tasks, killed the process, started a fresh server process pointed at the same `todo.db`, confirmed all 3 tasks (and the earlier rollup/overdue state) were still there.
- One thing I learned: How persistence works

# AI Workflow
- I used ChatGPT for helping me come up with different ideas of what to put on my ToDo List app, Claude for helping me plan and write the code, and Copilot for explaining any sort of errors that I came across.
- Claude outperformed in planning and writing code compared to the other two tools I used.
- I tried to use Claude for helping explain an error, but I switched over to Copilot because it wasn't explaining what the error actually meant, which is what I wanted.

# Reflection
- Using an agent within my workflow definitely made the process more efficient. Instead of me having to Google any error that I came across, I could easily ask my agent, who already knows the context, what problem I was facing, and could even fix it for me.
- The times when I had to step in were whenever Claude was planning. I realized that I needed to be more detailed and specific, or else Claude was just going to add a bunch of random features that wouldn't be useful to me. The whole point of this ToDo List is that it's catered to what I'll find useful, so this step was crucial to the project to make sure I had everything right.
- This project taught me a lot about expanding into different resources. Whenever I make a project, I tend to just use whatever I already know, and this limits the capabilities of my project because I'm never approaching a project differently. And so whenever the agents would recommend I use something else, I would do my research, then make my own judgement to see if it would be better or not. Most of the time, it was, and that's what I really liked about using agents.
- I would mostly use this workflow within my internship whenever I need some explaining. I like to use agents when I want to learn, so if I'm ever confused about something, I can just ask the agent, and they'll give me the answer I'm looking for since they already have the context needed.