"""CLI demo for PawPal+. Verifies the logic layer without the Streamlit UI.

Run with: python main.py
"""

import sys

from pawpal_system import Owner, Pet, Task, Scheduler

# Windows terminals default to cp1252 and cannot print emoji; force UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_demo() -> Scheduler:
    """Create a sample owner, two pets, and several tasks for the demo."""
    owner = Owner(name="Jordan")

    mochi = owner.add_pet(Pet(name="Mochi", species="dog"))
    biscuit = owner.add_pet(Pet(name="Biscuit", species="cat"))

    # Added intentionally out of order to prove sorting works.
    mochi.add_task(Task("Evening walk", time="18:30", duration_minutes=30,
                        priority="high", frequency="daily"))
    mochi.add_task(Task("Morning walk", time="08:00", duration_minutes=30,
                        priority="high", frequency="daily"))
    biscuit.add_task(Task("Breakfast", time="08:00", duration_minutes=10,
                          priority="high", frequency="daily"))  # conflict w/ walk
    biscuit.add_task(Task("Vet appointment", time="14:00", duration_minutes=45,
                          priority="medium", frequency="once"))
    mochi.add_task(Task("Heartworm pill", time="12:00", duration_minutes=5,
                        priority="low", frequency="weekly"))

    return Scheduler(owner=owner)


def main() -> None:
    """Build the demo data and print every scheduler feature to the terminal."""
    scheduler = build_demo()

    print("=" * 52)
    print("PawPal+ — Today's Schedule (sorted by time)")
    print("=" * 52)
    for task in scheduler.todays_schedule():
        print(f"  {task}  for {task.pet_name}")

    print("\nSorted by priority:")
    for task in scheduler.sort_by_priority():
        print(f"  {task}  for {task.pet_name}")

    print("\nFiltered — Mochi's tasks only:")
    for task in scheduler.filter_by_pet("Mochi"):
        print(f"  {task}")

    print("\nConflict detection:")
    conflicts = scheduler.detect_conflicts()
    print("\n".join(f"  {w}" for w in conflicts) if conflicts else "  none")

    print("\nRecurring task demo — completing Mochi's morning walk:")
    nxt = scheduler.complete_task(
        next(t for t in scheduler.filter_by_pet("Mochi") if t.description == "Morning walk")
    )
    print(f"  completed -> next occurrence due {nxt.due_date} at {nxt.time}")

    print("\n" + scheduler.explain_plan())


if __name__ == "__main__":
    main()
