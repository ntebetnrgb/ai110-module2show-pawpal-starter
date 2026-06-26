# PawPal+ Project Reflection

## System Design (core actions)

A user of PawPal+ should be able to:
1. Add a pet (and its basic info) under an owner.
2. Schedule a care task (walk, feeding, meds, appointment) with a time, duration, priority, and frequency.
3. See "today's schedule" — a sorted daily plan with conflict warnings.

## 1. System Design

**a. Initial design**

I chose four classes mirroring the real world:
- `Owner` — the top-level account; holds a list of `Pet`s and aggregates their tasks via `all_tasks()`.
- `Pet` — name/species plus its own list of `Task`s; responsible only for owning tasks.
- `Task` — a dataclass for a single activity (description, time, duration, priority, frequency, completion). It owns its own recurrence logic.
- `Scheduler` — the "brain." It reads from the `Owner` and provides sorting, filtering, conflict detection, and recurrence orchestration. It holds no data itself.

The key relationships: `Owner` has many `Pet`s, each `Pet` has many `Task`s, and `Scheduler` reads from one `Owner`.

**b. Design changes**

Two changes during implementation:
- **`Task` stamps its own `pet_name`.** Originally the `Scheduler` had to map a task back to its pet, which meant scanning every pet on every report. I moved a `pet_name` field onto `Task`, set by `Pet.add_task()`, so filtering and conflict reports are O(n) instead of nested loops.
- **Recurrence split between `Task` and `Scheduler`.** `Task.mark_complete()` returns the *next* occurrence (pure, easy to test), but it can't re-attach itself to a pet. So `Scheduler.complete_task()` wraps it and adds the new task back to the owning pet. This kept the data/orchestration boundary clean.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers **time** (`HH:MM`), **priority** (high/medium/low), **frequency** (once/daily/weekly), and **completion status**. Time mattered most because the core deliverable is a chronological daily plan; priority is the tiebreaker and the alternate sort mode. Duration is stored and displayed but not yet used to pack a fixed time budget.

**b. Tradeoffs**

`detect_conflicts()` only flags tasks that share an **exact** start time — it does not account for overlapping durations (a 30-minute 08:00 walk overlapping an 08:15 feeding is not flagged). This is reasonable for a v1 pet-care planner: exact-match detection is trivial to reason about, never produces false positives, and most household routines are scheduled on the hour/half-hour anyway. Interval-overlap detection would be the next iteration.

---

## 3. AI Collaboration

**a. How you used AI**

I used the AI assistant in agent mode to scaffold the four classes from my UML, then to flesh out the `Scheduler` algorithms (sorting key via `lambda`, `timedelta`-based recurrence, the conflict-grouping dict). I also had it draft the pytest suite and explain the `tmp_path` fixture. The most helpful prompts were specific and verifiable, e.g. "sort `Task` objects whose `time` is an `HH:MM` string" and "given my skeletons, how should the `Scheduler` retrieve all tasks from the `Owner`'s pets?"

**b. Judgment and verification**

I rejected an early suggestion to store `time` as a raw `datetime` on every task. For a daily planner that only cares about clock time, full datetimes added timezone/date noise and made the demo data verbose. I kept a plain `HH:MM` string plus a `minutes_since_midnight` property for sorting. I verified everything through `python main.py` and `python -m pytest` rather than trusting the generated code — which is how I caught that conflict detection was double-counting completed-then-recurred tasks, and fixed it to skip completed tasks.

---

## 4. Testing and Verification

**a. What you tested**

17 tests covering sorting correctness (chronological + priority order), recurrence (daily → +1 day, weekly → +7 days, once → none, and scheduler re-attachment), conflict detection (positive and negative), filtering by pet and status, input validation (bad time/priority raise `ValueError`), and the empty-pet edge case. These are the behaviors a user actually depends on — a wrong sort or a dropped recurring task would silently break someone's pet-care routine.

**b. Confidence**

Confidence: 4/5. The logic layer is well covered. With more time I'd test interval-overlap conflicts, tasks spanning midnight, and the Streamlit `session_state` flow with an automated harness instead of manual clicks.

---

## 5. Reflection

**a. What went well**

The CLI-first workflow. Building and verifying `pawpal_system.py` through `main.py` before touching Streamlit meant the UI wiring in Phase 3 was almost trivial — the logic was already proven.

**b. What you would improve**

Conflict detection should consider durations, and the app should persist data between sessions by default (the `save_to_json`/`load_from_json` methods exist but aren't wired into the UI yet).

**c. Key takeaway**

Acting as "lead architect" means owning the boundaries. The AI was fastest when I gave it a clear class contract and a single, testable responsibility per method; it drifted when asked open-ended "make it smart" questions. Keeping data (`Owner`/`Pet`/`Task`) separate from orchestration (`Scheduler`) made both the AI's job and the testing far easier.
