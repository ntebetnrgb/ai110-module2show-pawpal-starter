# AI Interactions Log

> Stretch features only. Documents the agent workflow and the data-persistence stretch.

---

## Agent Workflow (SF7)

**What task did you give the agent?**

"Build the whole PawPal+ project from the starter repo": design the UML, implement
the four-class logic layer with sorting/filtering/conflict/recurrence algorithms,
write a CLI demo, a pytest suite, wire the Streamlit UI to the logic, and finish
the docs (README, reflection, UML diagrams).

**What did the agent do?**

- Cloned the starter repo and moved its files into the project root.
- Created `pawpal_system.py` (`Task`, `Pet`, `Owner`, `Scheduler` dataclasses).
- Created `main.py` CLI demo and ran it (`python main.py`).
- Created `tests/test_pawpal.py` (17 tests) and ran `python -m pytest` — all pass.
- Rewrote `app.py` to import the logic layer and persist the `Owner` in `st.session_state`.
- Authored `diagrams/uml_draft.mmd`, `diagrams/uml_final.mmd`, the README, and the reflection.

**What did you have to verify or fix manually?**

- **Windows console encoding.** `python main.py` crashed with a `UnicodeEncodeError`
  (cp1252) when printing the ⚠️ emoji. Fixed by reconfiguring stdout to UTF-8 in `main.py`.
- **Conflict double-counting.** After a recurring task was completed, both the
  completed copy and the new occurrence shared a time slot and were both reported.
  Fixed `detect_conflicts()` to skip completed tasks.

---

## Data Persistence (Stretch)

`Scheduler.save_to_json(path)` serializes the owner, pets, and every task to a JSON
file using `dataclasses.asdict`. `Scheduler.load_from_json(path)` rebuilds the full
object graph, dropping the volatile `id`/`pet_name` fields so `Pet.add_task()` can
re-stamp them. A round-trip test (`test_save_and_load_roundtrip`) confirms task data
survives a save→load cycle. Files modified: `pawpal_system.py` (methods),
`tests/test_pawpal.py` (test).
