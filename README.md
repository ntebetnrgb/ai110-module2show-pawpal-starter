# PawPal+ 🐾 (Module 2 Project)

**PawPal+** is a smart pet-care management system. It helps a busy owner stay
consistent with daily routines — walks, feedings, medications, and appointments —
by sorting tasks, flagging scheduling conflicts, and auto-rescheduling recurring
tasks. The backend logic lives in `pawpal_system.py` and is exercised both by a
CLI demo (`main.py`) and a Streamlit UI (`app.py`).

## Architecture

Four classes, built with Python dataclasses:

| Class | Responsibility |
|-------|----------------|
| `Task` | A single activity: description, time, duration, priority, frequency, completion. Knows how to recur. |
| `Pet` | Holds pet details and a list of `Task`s. |
| `Owner` | Manages multiple `Pet`s and aggregates all their tasks. |
| `Scheduler` | The "brain": sorts, filters, detects conflicts, and rebuilds recurring tasks. |

See [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) for the class diagram
(`diagrams/uml_draft.mmd` is the Phase 1 draft).

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

Run the CLI demo:

```bash
python main.py
```

Run the Streamlit app:

```bash
streamlit run app.py
```

## 🖥️ Sample Output

Output from `python main.py`:

```
====================================================
PawPal+ — Today's Schedule (sorted by time)
====================================================
  [ ] 08:00  Morning walk (30 min) [high]  for Mochi
  [ ] 08:00  Breakfast (10 min) [high]  for Biscuit
  [ ] 12:00  Heartworm pill (5 min) [low]  for Mochi
  [ ] 14:00  Vet appointment (45 min) [medium]  for Biscuit
  [ ] 18:30  Evening walk (30 min) [high]  for Mochi

Sorted by priority:
  [ ] 08:00  Morning walk (30 min) [high]  for Mochi
  [ ] 08:00  Breakfast (10 min) [high]  for Biscuit
  [ ] 18:30  Evening walk (30 min) [high]  for Mochi
  [ ] 14:00  Vet appointment (45 min) [medium]  for Biscuit
  [ ] 12:00  Heartworm pill (5 min) [low]  for Mochi

Filtered — Mochi's tasks only:
  [ ] 18:30  Evening walk (30 min) [high]
  [ ] 08:00  Morning walk (30 min) [high]
  [ ] 12:00  Heartworm pill (5 min) [low]

Conflict detection:
  ⚠️ Conflict at 08:00: Morning walk (Mochi), Breakfast (Biscuit)

Recurring task demo — completing Mochi's morning walk:
  completed -> next occurrence due 2026-06-26 at 08:00

Daily plan for Jordan's pets:
  08:00 — Breakfast (10 min) [priority: high] for Biscuit
  12:00 — Heartworm pill (5 min) [priority: low] for Mochi
  14:00 — Vet appointment (45 min) [priority: medium] for Biscuit
  18:30 — Evening walk (30 min) [priority: high] for Mochi
  ⚠️ Conflict at 08:00: Morning walk (Mochi), Breakfast (Biscuit)
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting (time) | `Scheduler.sort_by_time()` | `sorted()` keyed on `Task.minutes_since_midnight` (parses `HH:MM`). |
| Task sorting (priority) | `Scheduler.sort_by_priority()` | Sorts by `priority_rank` (high→low), then time as tiebreaker. |
| Filtering | `Scheduler.filter_by_pet()`, `Scheduler.filter_by_status()` | By pet name (case-insensitive) or completion status. |
| Conflict handling | `Scheduler.detect_conflicts()` | Groups pending tasks by exact time; warns on any shared slot. |
| Recurring tasks | `Task.mark_complete()` → `Task._spawn_next()`, `Scheduler.complete_task()` | Completing a `daily`/`weekly` task spawns the next via `timedelta` and re-attaches it to the pet. |
| Daily plan + explanation | `Scheduler.todays_schedule()`, `Scheduler.explain_plan()` | Today's pending tasks, time-sorted, with conflict warnings. |
| Persistence (stretch) | `Scheduler.save_to_json()`, `Scheduler.load_from_json()` | Dataclass → dict via `asdict`, round-trips through a JSON file. |

## 🧪 Testing PawPal+

```bash
python -m pytest
```

The suite (`tests/test_pawpal.py`) covers: task completion and status, task
addition counts, owner task aggregation, time/priority sorting, pet/status
filtering, daily and weekly recurrence (and scheduler re-attachment), conflict
detection (positive and negative), input validation (bad time/priority), the
empty-pet edge case, and JSON save/load round-trip.

Sample run:

```
tests\test_pawpal.py .................                                   [100%]
============================= 17 passed in 0.05s ==============================
```

**Confidence Level: ★★★★☆ (4/5)** — core scheduling, recurrence, and conflict
logic are all covered by passing tests. Held back one star because conflict
detection only catches exact time matches (not overlapping durations) and the
Streamlit layer is verified manually rather than by tests.

## 📸 Demo Walkthrough

1. **Set up the owner.** Edit the owner name in the sidebar.
2. **Add pets.** Use the sidebar "Add a pet" form (name + species). The pet list
   updates immediately; the `Owner` object is held in `st.session_state` so it
   survives Streamlit's reruns.
3. **Add tasks.** Pick a pet, enter a description, time, duration, priority, and
   frequency (`once`/`daily`/`weekly`). Each submit calls `Pet.add_task()`.
4. **View today's plan.** The table re-sorts live by **time** or **priority**
   using `Scheduler.sort_by_time()` / `sort_by_priority()`. Any two pending tasks
   at the same time raise a yellow `st.warning` from `Scheduler.detect_conflicts()`.
5. **Complete a task.** Marking a `daily`/`weekly` task done calls
   `Scheduler.complete_task()`, which auto-schedules the next occurrence and
   confirms the new due date.

Example workflow: *add pet "Mochi" → schedule "Morning walk" at 08:00 (daily) →
schedule "Breakfast" at 08:00 → see the 08:00 conflict warning → complete the
walk and watch tomorrow's walk appear.*
